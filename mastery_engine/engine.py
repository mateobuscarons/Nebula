"""
Mastery Engine - Core Teaching Engine

Executes interactive lessons using the URAC framework (Understand, Retain, Apply, Connect)
with Gemini Flash as the LLM backend.
"""

import os
import json
import time
import re
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types
import json_repair

from concurrent.futures import ThreadPoolExecutor

from mastery_engine.grounding import ground_lesson
from mastery_engine.further_reading import get_further_reading

load_dotenv()


class MasteryEngine:
    """
    Interactive teaching engine that executes micro-lessons following the URAC framework.

    The engine manages:
    - Conversation state for current lesson
    - Acquired knowledge across lessons
    - Phase transitions (TEACHING -> APPLICATION -> CONNECT -> COMPLETED)
    - Structured JSON output from LLM
    """

    def __init__(self):
        """Initialize the Mastery Engine with Gemini client."""
        self.model_name = "gemini-3-flash-preview"
        self.client = self._setup_gemini()

        # Data loaded from module_plans.json
        self.module_plans = None
        self.user_baseline = ""
        self.user_objective = ""

        # State management (resets for each lesson)
        self.current_module_idx = 0
        self.current_lesson_idx = 0
        self.conversation_history = []

        # Directly loaded acquired knowledge (for API integration)
        self._direct_acquired_knowledge = None

        # Metrics
        self.last_response_time = 0
        self.last_token_usage = {}

        # Grounding context for current lesson
        self._lesson_grounding = None
        self._further_reading = None

    def _setup_gemini(self):
        """Setup Google GenAI client."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in .env")
        return genai.Client(api_key=api_key)

    # =========================================================================
    # Lesson Loading
    # =========================================================================

    def load_lesson_plans(self, file_path: str):
        """Load module plans from JSON file."""
        with open(file_path, 'r') as f:
            data = json.load(f)

        self.module_plans = data.get("module_plans", [])
        self.user_baseline = data.get("input", {}).get("user_baseline", "")
        self.user_objective = data.get("input", {}).get("user_objective", "")

        total_lessons = sum(
            len(module["lesson_plan"]["lesson_plan"])
            for module in self.module_plans
        )
        print(f"Loaded {len(self.module_plans)} modules, {total_lessons} lessons")

    def load_lesson_from_data(
        self,
        user_baseline: str,
        user_objective: str,
        module_data: Dict[str, Any],
        lesson_index: int,
        acquired_knowledge: List[str]
    ):
        """
        Load a single lesson from database data (for API integration).

        Args:
            user_baseline: What the user already knows
            user_objective: What the user wants to achieve
            module_data: Module challenges data from DB
            lesson_index: 0-indexed lesson number within the module
            acquired_knowledge: List of competencies already acquired
        """
        self.user_baseline = user_baseline
        self.user_objective = user_objective

        module_info = module_data.get("module", {})

        self.module_plans = [{
            "module_order": 1,
            "original_module": module_info,
            "lesson_plan": {
                "module_id": module_data.get("module_id", 1),
                "module_context_bridge": module_data.get("module_context_bridge", ""),
                "lesson_plan": module_data.get("lesson_plan", []),
                "acquired_competencies": module_data.get("acquired_competencies", [])
            },
            "acquired_knowledge_at_this_point": acquired_knowledge
        }]

        self.current_module_idx = 0
        self.current_lesson_idx = lesson_index
        self._direct_acquired_knowledge = acquired_knowledge
        self.conversation_history = []

        lesson = self.get_current_lesson()
        if lesson:
            print(f"Loaded lesson: {lesson.get('topic', 'Unknown')}")
        else:
            print(f"Could not find lesson at index {lesson_index}")

    # =========================================================================
    # Lesson State Accessors
    # =========================================================================

    def get_current_lesson(self) -> Optional[Dict]:
        """Get the current lesson data."""
        if not self.module_plans or self.current_module_idx >= len(self.module_plans):
            return None

        module = self.module_plans[self.current_module_idx]
        lessons = module["lesson_plan"]["lesson_plan"]

        if self.current_lesson_idx >= len(lessons):
            return None

        return lessons[self.current_lesson_idx]

    def get_current_module(self) -> Optional[Dict]:
        """Get the current module data."""
        if not self.module_plans or self.current_module_idx >= len(self.module_plans):
            return None
        return self.module_plans[self.current_module_idx]

    def get_acquired_knowledge(self) -> List[str]:
        """Get the list of acquired knowledge up to the current lesson."""
        if self._direct_acquired_knowledge is not None:
            return self._direct_acquired_knowledge

        if not self.module_plans:
            return []

        acquired = []

        # Add knowledge from previous modules
        if self.current_module_idx > 0:
            prev_module = self.module_plans[self.current_module_idx - 1]
            acquired.extend(prev_module.get("acquired_knowledge_at_this_point", []))

        # Add knowledge from previous lessons in current module
        module = self.get_current_module()
        if module:
            competencies = module["lesson_plan"].get("acquired_competencies", [])
            for i in range(self.current_lesson_idx):
                if i < len(competencies):
                    acquired.append(competencies[i])

        return acquired

    def get_grounding_context(self) -> Dict[str, Any]:
        """Get cached grounding context for current lesson."""
        grounding = self._lesson_grounding or {}
        reading = self._further_reading or {}

        return {
            "insights": grounding.get("insights", []),
            "further_reading": reading.get("sources", []),
            "grounded": grounding.get("grounded", False) or len(reading.get("sources", [])) > 0,
        }

    def get_progress_info(self) -> Dict[str, Any]:
        """Get current progress information."""
        if not self.module_plans:
            return {
                "total_modules": 0, "total_lessons": 0,
                "current_module": 0, "current_lesson": 0,
                "module_title": "", "lesson_topic": ""
            }

        total_modules = len(self.module_plans)
        total_lessons = sum(
            len(module["lesson_plan"]["lesson_plan"])
            for module in self.module_plans
        )

        module = self.get_current_module()
        lesson = self.get_current_lesson()

        return {
            "total_modules": total_modules,
            "total_lessons": total_lessons,
            "current_module": self.current_module_idx + 1,
            "current_lesson": self.current_lesson_idx + 1,
            "module_title": module["original_module"]["title"] if module else "",
            "lesson_topic": lesson.get("topic", "") if lesson else ""
        }

    # =========================================================================
    # Lesson Flow
    # =========================================================================

    def ground_lesson(self) -> Dict[str, Any]:
        """Ground the lesson with insights AND further reading in parallel."""
        lesson = self.get_current_lesson()
        if not lesson:
            return {"insights": [], "further_reading": [], "grounded": False}

        topic = lesson.get("topic", "")
        core_concept = lesson.get("urac_blueprint", {}).get("understand", "")

        # Run both in parallel
        with ThreadPoolExecutor(max_workers=2) as executor:
            insights_future = executor.submit(ground_lesson, self.client, topic, core_concept)
            reading_future = executor.submit(get_further_reading, self.client, topic)

            grounding_result = insights_future.result()
            reading_result = reading_future.result()

        self._lesson_grounding = grounding_result
        self._further_reading = reading_result

        return {
            "insights": grounding_result.get("insights", []),
            "further_reading": reading_result.get("sources", []),
            "grounded": grounding_result.get("grounded", False) or len(reading_result.get("sources", [])) > 0,
            "token_usage": {
                "grounding": grounding_result.get("token_usage"),
                "further_reading": reading_result.get("token_usage"),
            }
        }

    def start_lesson(self) -> Dict[str, Any]:
        """Start a new lesson and get the initial LLM response."""
        lesson = self.get_current_lesson()
        if not lesson:
            return None

        self.conversation_history = []
        return self._generate_response(user_input=None)

    def process_user_input(self, user_input: str) -> Dict[str, Any]:
        """Process user input and get LLM response."""
        return self._generate_response(user_input=user_input)

    def advance_to_next_lesson(self) -> bool:
        """Advance to the next lesson. Returns True if successful."""
        module = self.get_current_module()
        if not module:
            return False

        lessons = module["lesson_plan"]["lesson_plan"]

        if self.current_lesson_idx + 1 < len(lessons):
            self.current_lesson_idx += 1
            return True

        if self.current_module_idx + 1 < len(self.module_plans):
            self.current_module_idx += 1
            self.current_lesson_idx = 0
            return True

        return False

    # =========================================================================
    # LLM Response Generation
    # =========================================================================

    def _generate_response(self, user_input: Optional[str]) -> Dict[str, Any]:
        """Generate LLM response with structured JSON output."""
        lesson = self.get_current_lesson()
        module = self.get_current_module()

        if not lesson or not module:
            raise ValueError("No current lesson available")

        system_prompt = self._build_system_prompt(lesson, module)

        if user_input is None:
            user_message = "[SYSTEM] Start the lesson. This is your first message to the learner."
        else:
            user_message = user_input
            self.conversation_history.append({"role": "user", "content": user_input})

        # Build contents for Gemini
        contents = []
        for msg in self.conversation_history:
            contents.append(
                types.Content(
                    role=msg["role"],
                    parts=[types.Part.from_text(text=msg["content"])],
                )
            )

        if user_input is None:
            contents.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=user_message)],
                )
            )

        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.0,
            top_p=0.95,
            max_output_tokens=4000,
            response_mime_type="application/json",
        )

        try:
            start_time = time.time()
            usage_metadata = None
            full_response = ""

            for chunk in self.client.models.generate_content_stream(
                model=self.model_name,
                contents=contents,
                config=config,
            ):
                if chunk.text:
                    full_response += chunk.text
                if chunk.usage_metadata:
                    usage_metadata = chunk.usage_metadata

            self.last_response_time = time.time() - start_time

            if usage_metadata:
                self.last_token_usage = {
                    "input_tokens": usage_metadata.prompt_token_count,
                    "output_tokens": usage_metadata.candidates_token_count,
                    "total_tokens": usage_metadata.total_token_count
                }
            else:
                self.last_token_usage = {}

            response_json = self._extract_json(full_response)

            if not isinstance(response_json, dict):
                raise ValueError(f"JSON extraction returned {type(response_json).__name__}")

            self._log_response(response_json)

            self.conversation_history.append({"role": "model", "content": full_response})
            return response_json

        except Exception as e:
            print(f"Error generating response: {e}")
            import traceback
            traceback.print_exc()
            raise e

    def _log_response(self, response: Dict[str, Any]):
        """Log formatted response for debugging."""
        print(f"\n{'='*60}")
        print(f"GEMINI RESPONSE")
        print(f"{'='*60}")
        print(f"\nThought: {response.get('thought_process', 'N/A')}")
        print(f"\nContent: {response.get('conversation_content', 'N/A')[:200]}...")

        editor = response.get('editor_content')
        if editor:
            print(f"\nEditor: {editor.get('type', 'N/A')} / {editor.get('language', 'N/A')}")

        status = response.get('lesson_status', {})
        print(f"\nPhase: {status.get('current_phase', 'N/A')}")
        print(f"{'='*60}\n")

    # =========================================================================
    # System Prompt
    # =========================================================================

    def _build_system_prompt(self, lesson: Dict, module: Dict) -> str:
        """Build comprehensive system prompt for the LLM."""
        urac = lesson.get("urac_blueprint", {})
        module_context_bridge = module["lesson_plan"].get("module_context_bridge", "")

        acquired = self.get_acquired_knowledge()
        acquired_str = "\n".join([f"  - {k}" for k in acquired]) if acquired else "  (None - first lesson)"

        return f"""You are an Expert Mentor executing an interactive micro-lesson.

# LEARNER CONTEXT

**Baseline:** {self.user_baseline}
**Objective:** {self.user_objective}
**Prior Knowledge:** {acquired_str}

# LESSON CONTENT

**Topic:** {lesson.get("topic", "N/A")}
**Context:** {module_context_bridge}

**Core Concept:** {urac.get("understand", "")}
**Analytical Question:** {urac.get("retain", "")}
**Application Task:** {urac.get("apply", "")}
**Connection:** {urac.get("connect", "")}

# THE 4-PHASE LESSON STRUCTURE

## Phase 1: ENGAGE (1-2 turns)
**Purpose:** Warm up with a quick win. Build confidence.

Your FIRST message must:
1. Hook (1 sentence connecting to their knowledge)
2. Visual (diagram or table)
3. Brief decode (one bullet per element)
4. Simple question with a mini-scenario

**Question rule:** Frame as a quick scenario, not a lookup.
- BAD: "What does the Readiness probe do?" (just reading)
- GOOD: "Your app started but the database isn't connected yet—which probe handles this?"

Keep it easy but require applying the visual to a situation.

**If correct:** Brief acknowledgment, transition to DEEPEN
**If incorrect:** Hint pointing to the visual, let them retry

Set `current_phase: "ENGAGE"`

## Phase 2: DEEPEN (1-2 turns)
**Purpose:** Build deeper understanding with guided reasoning.

When transitioning from ENGAGE:
1. Acknowledge their answer briefly (1 sentence)
2. Expand with MORE detail - add a visual, formula, or table
3. Ask the Analytical Question based on: "{urac.get("retain", "")}"

**How to frame the analytical question (IMPORTANT):**
- DON'T ask abstract "why" questions that feel like a test
- DO frame it as a concrete scenario or "what if"
- Give them something to reason FROM (a situation, example, or the visual)

Examples of good framing:
- "Looking at the formula, if Company A has a higher P/E than the target, what happens to EPS?"
- "Imagine you're using 100% debt financing. Based on what we covered, how would that affect...?"
- "In the diagram, if step 2 fails, what would the outcome be?"

**If correct:** Validate their reasoning specifically, transition to APPLY
**If incorrect:** Give a hint or simpler sub-question, guide them to the answer

Set `current_phase: "DEEPEN"`

## Phase 3: APPLY (2-3 turns)
**Purpose:** Transfer knowledge to a practical task.

Present the Application Task: "{urac.get("apply", "")}"

**Scaffolding:**
- PROVIDE in editor_content: Structure, templates, boilerplate (low-cognitive effort)
- REQUIRE from learner: Decisions, analysis, reasoning (high-cognitive effort)

**If incorrect:** Point to specific error, ask WHY it's wrong, never give solution

Set `current_phase: "APPLY"`

## Phase 4: CONNECT (1 turn)
**Purpose:** Consolidate and motivate.

When APPLY is complete:
1. Validate their success specifically
2. Connect to their objective: "{self.user_objective}"
3. Brief forward hook (what this enables next)

Keep under 80 words. Set `current_phase: "COMPLETED"`

# CRITICAL: SELF-CONTAINED MESSAGES

**The learner CANNOT see previous messages.** Every message must be self-contained.

- If you reference a diagram, RE-INCLUDE it in your message
- If you reference a concept, briefly restate it
- Never say "as shown above" or "in the previous diagram" without showing it again
- Each message should make sense on its own

# VISUAL FORMATTING RULES

## Mermaid Diagrams

IMPORTANT: Keep diagrams clean and minimal. Do NOT use:
- Colors (no `style`, no `fill:`, no `stroke:`)
- Classdefs or custom styling
- Subgraphs with colored backgrounds

Just use plain nodes and edges. The UI will apply consistent theming.

**ALWAYS use `graph LR` (horizontal/left-to-right).** Never use `graph TD` (vertical).

```mermaid
graph LR
    A[Input] --> B[Process] --> C[Output]
```

```mermaid
graph LR
    A[Data] --> B{{{{Decision}}}}
    B -->|Yes| C[Save]
    B -->|No| D[Error]
```

Keep diagrams compact and horizontal.

## Tables

| Aspect | A | B |
|--------|---|---|
| Speed | Fast | Slow |
| Cost | High | Low |

## LaTeX Formulas - FOR MATH & FINANCE

Inline math (within text): $EPS = \\frac{{Net Income}}{{Shares}}$
Display math (centered block): $$P/E = \\frac{{Price}}{{EPS}}$$

Use LaTeX for:
- Financial ratios and formulas
- Mathematical relationships
- Equations with fractions, subscripts, exponents

Examples:
- "The formula $ROE = \\frac{{NI}}{{Equity}}$ measures..."
- "Accretion is calculated as: $$\\Delta EPS = EPS_{{pro forma}} - EPS_{{standalone}}$$"

## Other Formatting

**Blockquotes** for insights:
> **Key:** The critical point.

**Horizontal rule** before questions:
---
**Your turn:** [Question]

## HARD RULES

- MAX 3 sentences per paragraph
- EVERY process = compact diagram
- EVERY comparison = focused table
- NO walls of text
- NO meta-commentary ("Let me test you...", "Now, let's...")
- RE-INCLUDE visuals when referencing them

# CRITICAL OUTPUT REQUIREMENTS - READ CAREFULLY

**YOU MUST OUTPUT ONLY VALID JSON. NOTHING ELSE.**

- Your ENTIRE response must be a single JSON object
- Start your response with {{ (opening brace)
- End your response with }} (closing brace)
- Do NOT use markdown code fences (no ``` or ```json)
- Do NOT add any text before or after the JSON object
- Do NOT add explanatory comments outside the JSON

**Required JSON Schema:**

{{
  "thought_process": "Brief: current phase, what you're doing, expected response.",
  "conversation_content": "Markdown shown to learner. Self-contained. Follow visual rules.",
  "editor_content": null OR {{"type": "code|text", "language": "yaml|python|etc", "content": "..."}},
  "lesson_status": {{"current_phase": "ENGAGE|DEEPEN|APPLY|COMPLETED", "is_waiting_for_user_action": true}}
}}

**editor_content by phase:**
- ENGAGE: null (simple text answer)
- DEEPEN: null (reasoning in their words)
- APPLY: Provide scaffolding (templates, structure)
- COMPLETED: null

# PHASE TRANSITIONS

ENGAGE -> DEEPEN: When learner answers the easy question correctly
DEEPEN -> APPLY: When learner answers the analytical question correctly
APPLY -> COMPLETED: When learner completes the task successfully

**On incorrect answers:** Stay in current phase, give hints/guidance, let them retry."""

    # =========================================================================
    # JSON Extraction
    # =========================================================================

    def _extract_json(self, text: str) -> Dict:
        """Smart JSON extraction with multiple fallback strategies."""
        original_text = text
        text = text.strip()

        # Strategy 1: Direct parse (response_mime_type should return valid JSON)
        try:
            result = json.loads(text)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass

        # Strategy 2: Markdown code fence extraction
        json_str = self._extract_from_code_fence(text)

        try:
            result = json.loads(json_str)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass

        # Strategy 3: Find JSON boundaries with brace counting
        json_str = self._extract_by_brace_matching(json_str)

        try:
            result = json.loads(json_str)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass

        # Strategy 4: json_repair library
        try:
            repaired = json_repair.loads(json_str)
            if isinstance(repaired, dict):
                print("  JSON was malformed but repaired")
                return repaired
        except Exception:
            pass

        # Strategy 5: Reconstruct from patterns
        if '{' not in original_text:
            return self._reconstruct_from_patterns(original_text)

        print(f"\nJSON Extraction Failed")
        print(f"Response length: {len(original_text)}")
        print(f"First 300 chars: {original_text[:300]}")
        raise ValueError("Could not extract valid JSON from LLM response")

    def _extract_from_code_fence(self, text: str) -> str:
        """Extract JSON from markdown code fences."""
        for marker in ["```json", "```"]:
            start_idx = text.find(marker)
            if start_idx != -1:
                end_idx = text.find("```", start_idx + len(marker))
                if end_idx != -1:
                    return text[start_idx + len(marker):end_idx].strip()
                return text[start_idx + len(marker):].strip()
        return text

    def _extract_by_brace_matching(self, text: str) -> str:
        """Extract JSON by matching braces."""
        first_brace = text.find('{')
        if first_brace == -1:
            return text

        brace_count = 0
        in_string = False
        escape_next = False

        for i in range(first_brace, len(text)):
            char = text[i]

            if escape_next:
                escape_next = False
                continue

            if char == '\\':
                escape_next = True
                continue

            if char == '"' and not escape_next:
                in_string = not in_string
                continue

            if not in_string:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        return text[first_brace:i + 1]

        return text

    def _reconstruct_from_patterns(self, text: str) -> Dict:
        """Attempt to reconstruct JSON from unstructured text."""
        print("  No JSON structure found, attempting reconstruction...")

        thought_match = re.search(r'thought_process[:\s]*(.*?)(?=conversation_content|$)', text, re.DOTALL)
        conv_match = re.search(r'conversation_content[:\s]*(.*?)(?=editor_content|lesson_status|$)', text, re.DOTALL)

        return {
            "thought_process": thought_match.group(1).strip() if thought_match else "Processing",
            "conversation_content": conv_match.group(1).strip() if conv_match else text[:500],
            "editor_content": None,
            "lesson_status": {"current_phase": "ENGAGE", "is_waiting_for_user_action": True}
        }
