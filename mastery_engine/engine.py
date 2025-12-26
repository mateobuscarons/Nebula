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

load_dotenv()


class MasteryEngine:
    """
    Interactive teaching engine that executes micro-lessons following the URAC framework.

    The engine manages:
    - Conversation state for current lesson
    - Acquired knowledge across lessons
    - Phase transitions (TEACHING → APPLICATION → CONNECT → COMPLETED)
    - Structured JSON output from LLM
    """

    def __init__(self):
        """Initialize the Mastery Engine with Gemini client."""
        self.model_name = "gemini-3-flash-preview" # gemini-flash-latest
        self.client = self._setup_gemini()

        # Data loaded from module_plans.json
        self.module_plans = None
        self.user_baseline = ""
        self.user_objective = ""

        # State management (resets for each lesson)
        self.current_module_idx = 0
        self.current_lesson_idx = 0
        self.conversation_history = []  # Resets for each new lesson

        # Directly loaded acquired knowledge (for API integration)
        self._direct_acquired_knowledge = None

        # Metrics
        self.last_response_time = 0
        self.last_token_usage = {}

        # Resource cache for grounded references (per lesson)
        self._lesson_resources_cache = {}  # Key: (module_idx, lesson_idx)

    def _setup_gemini(self):
        """Setup Google GenAI client."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in .env")
        return genai.Client(api_key=api_key)

    def load_lesson_plans(self, file_path: str):
        """
        Load module plans from JSON file.

        Args:
            file_path: Path to module_plans.json
        """
        with open(file_path, 'r') as f:
            data = json.load(f)

        self.module_plans = data.get("module_plans", [])
        self.user_baseline = data.get("input", {}).get("user_baseline", "")
        self.user_objective = data.get("input", {}).get("user_objective", "")

        print(f"✅ Loaded {len(self.module_plans)} modules")

        # Calculate total lessons
        total_lessons = sum(
            len(module["lesson_plan"]["lesson_plan"])
            for module in self.module_plans
        )
        print(f"✅ Total lessons: {total_lessons}\n")

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

        This method allows the engine to be initialized with lesson data
        directly from the database, without loading from a file.

        Args:
            user_baseline: What the user already knows
            user_objective: What the user wants to achieve
            module_data: Module challenges data from DB (includes lesson_plan, module, etc.)
            lesson_index: 0-indexed lesson number within the module
            acquired_knowledge: List of competencies already acquired
        """
        self.user_baseline = user_baseline
        self.user_objective = user_objective

        # Build a module_plans structure compatible with existing methods
        # The module_data from DB has: module, lesson_plan, acquired_competencies, etc.
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

        # Set the current lesson index
        self.current_module_idx = 0
        self.current_lesson_idx = lesson_index

        # Store directly loaded acquired knowledge
        self._direct_acquired_knowledge = acquired_knowledge

        # Reset conversation history
        self.conversation_history = []

        lesson = self.get_current_lesson()
        if lesson:
            print(f"✅ Loaded lesson: {lesson.get('topic', 'Unknown')}")
        else:
            print(f"⚠️ Could not find lesson at index {lesson_index}")

    def get_current_lesson(self) -> Optional[Dict]:
        """Get the current lesson data."""
        if not self.module_plans:
            return None

        if self.current_module_idx >= len(self.module_plans):
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
        """
        Get the list of acquired knowledge up to the current lesson.

        This includes:
        1. All knowledge from previous modules
        2. Knowledge from lessons completed before the current one in the current module

        When using load_lesson_from_data(), the acquired knowledge is directly provided.

        Returns:
            List of acquired knowledge strings
        """
        # If directly loaded via API, use the provided acquired knowledge
        if self._direct_acquired_knowledge is not None:
            return self._direct_acquired_knowledge

        if not self.module_plans:
            return []

        acquired_knowledge_list = []

        # 1. Add all knowledge from previous modules
        if self.current_module_idx > 0:
            prev_module = self.module_plans[self.current_module_idx - 1]
            acquired_knowledge_list.extend(prev_module.get("acquired_knowledge_at_this_point", []))

        # 2. Add knowledge from current module's lessons completed before this one
        module = self.get_current_module()
        if module:
            current_competencies = module["lesson_plan"].get("acquired_competencies", [])
            for i in range(self.current_lesson_idx):
                if i < len(current_competencies):
                    acquired_knowledge_list.append(current_competencies[i])

        return acquired_knowledge_list

    def start_lesson(self) -> Dict[str, Any]:
        """
        Start a new lesson and get the initial LLM response.

        Returns:
            Structured JSON response from LLM
        """
        lesson = self.get_current_lesson()
        if not lesson:
            return None

        # Reset conversation history for new lesson
        self.conversation_history = []

        # Get initial response from LLM (no user input yet)
        return self._generate_response(user_input=None)

    def get_source_attributions(self, use_cache: bool = True) -> Dict[str, Any]:
        """
        Find source attributions for the methodologies/frameworks used in this lesson.

        Identifies named frameworks, their industry origins, and authoritative
        documentation. Adds credibility by showing the lesson teaches established
        industry practices.

        Example output:
            "Kubernetes Pods — Official container orchestration concept from kubernetes.io"
            + link to documentation

        Args:
            use_cache: Return cached attributions if available

        Returns:
            {
                "attributions": [
                    {
                        "concept": "Kubernetes Pods",
                        "description": "Official documentation for the smallest deployable unit",
                        "url": "https://..."
                    }
                ],
                "lesson_topic": str,
                "cached": bool,
                "error": None or str
            }
        """
        lesson = self.get_current_lesson()
        if not lesson:
            return {"attributions": [], "lesson_topic": "", "cached": False, "error": "No lesson"}

        cache_key = (self.current_module_idx, self.current_lesson_idx)

        if use_cache and cache_key in self._lesson_resources_cache:
            cached = self._lesson_resources_cache[cache_key].copy()
            cached["cached"] = True
            return cached

        topic = lesson.get("topic", "")
        urac = lesson.get("urac_blueprint", {})
        core_concept = urac.get("understand", "")
        application = urac.get("apply", "")

        # Prompt designed to get grounded, verifiable sources
        prompt = f"""Lesson: "{topic}"
Concept: {core_concept}

Find 2-3 authoritative sources. For each, write a SHORT phrase (under 15 words) saying how it supports the lesson."""

        try:
            start_time = time.time()

            # Use gemini-2.0-flash for grounding (stable support)
            grounding_tool = types.Tool(google_search=types.GoogleSearch())
            config = types.GenerateContentConfig(
                tools=[grounding_tool],
                temperature=0.0,
                max_output_tokens=800,
            )

            response = self.client.models.generate_content(
                model="gemini-2.0-flash",  # Stable model with grounding support
                contents=prompt,
                config=config,
            )

            duration = time.time() - start_time
            attributions = []

            if response.candidates and response.candidates[0].grounding_metadata:
                metadata = response.candidates[0].grounding_metadata
                chunks = getattr(metadata, 'grounding_chunks', None) or []
                response_text = response.text or ""

                # Parse numbered items from LLM response
                # Match by position: item 1 → first unique domain, item 2 → second, etc.
                numbered_items = []
                lines = response_text.split('\n')
                current_item = None

                for i, line in enumerate(lines):
                    line_stripped = line.strip()
                    if not line_stripped:
                        continue

                    # Check if this is a numbered item start (1., 2., etc.)
                    if line_stripped and line_stripped[0].isdigit() and '.' in line_stripped[:3]:
                        if current_item:
                            numbered_items.append(current_item)
                        current_item = line_stripped
                    elif current_item and line_stripped.startswith('*'):
                        # Continuation line with description
                        current_item += ' ' + line_stripped.lstrip('*').strip()

                if current_item:
                    numbered_items.append(current_item)

                # Extract descriptions from numbered items
                item_descriptions = []
                for item in numbered_items:
                    desc = None
                    # Format: "1. **Title**: Description" or "1. **Title** - Description"
                    if '**:' in item:
                        desc = item.split('**:', 1)[-1].strip()
                    elif '** -' in item:
                        desc = item.split('** -', 1)[-1].strip()
                    elif '** –' in item:
                        desc = item.split('** –', 1)[-1].strip()
                    elif '**.' in item:
                        desc = item.split('**.', 1)[-1].strip()
                    # Fallback: everything after the closing **
                    elif '**' in item:
                        parts = item.split('**')
                        if len(parts) >= 3:
                            desc = parts[-1].strip().lstrip(':').lstrip('-').strip()

                    if desc and len(desc) > 20:
                        item_descriptions.append(desc)
                    else:
                        item_descriptions.append(None)

                # Build attributions from unique domains, matching by position
                seen_domains = set()
                desc_index = 0
                for chunk in chunks:
                    if len(attributions) >= 3:
                        break

                    if not hasattr(chunk, 'web') or not chunk.web:
                        continue

                    url = getattr(chunk.web, 'uri', None)
                    title = getattr(chunk.web, 'title', None) or "Source"

                    if not url:
                        continue

                    domain_full = title.lower().replace('www.', '')
                    if domain_full in seen_domains:
                        continue
                    seen_domains.add(domain_full)

                    # Get description by position (first unique domain → first item, etc.)
                    description = f"Reference for {topic}"
                    if desc_index < len(item_descriptions) and item_descriptions[desc_index]:
                        description = item_descriptions[desc_index]
                    desc_index += 1

                    attributions.append({
                        "concept": title,
                        "description": description,
                        "url": url
                    })

            result = {
                "attributions": attributions,
                "lesson_topic": topic,
                "cached": False,
                "fetch_time_seconds": round(duration, 2),
                "error": None
            }

            self._lesson_resources_cache[cache_key] = result

            print(f"\n💡 Source Attributions for '{topic}': {len(attributions)} found ({duration:.1f}s)")
            for a in attributions:
                print(f"   • {a['concept']}: {a['description'][:50]}...")

            return result

        except Exception as e:
            print(f"\n⚠️ Attribution error: {e}")
            return {
                "attributions": [],
                "lesson_topic": topic,
                "cached": False,
                "error": str(e)
            }

    def clear_attributions_cache(self):
        """Clear cached source attributions."""
        self._lesson_resources_cache = {}

    def process_user_input(self, user_input: str) -> Dict[str, Any]:
        """
        Process user input and get LLM response.

        Args:
            user_input: The user's response (text, code, answer, etc.)

        Returns:
            Structured JSON response from LLM
        """
        return self._generate_response(user_input=user_input)

    def advance_to_next_lesson(self) -> bool:
        """
        Advance to the next lesson.

        Returns:
            True if advanced successfully, False if no more lessons
        """
        module = self.get_current_module()
        if not module:
            return False

        lessons = module["lesson_plan"]["lesson_plan"]

        # Try next lesson in current module
        if self.current_lesson_idx + 1 < len(lessons):
            self.current_lesson_idx += 1
            return True

        # Try next module
        if self.current_module_idx + 1 < len(self.module_plans):
            self.current_module_idx += 1
            self.current_lesson_idx = 0
            return True

        # No more lessons
        return False

    def _generate_response(self, user_input: Optional[str]) -> Dict[str, Any]:
        """
        Generate LLM response with structured JSON output.

        Args:
            user_input: User's input (None for initial lesson start)

        Returns:
            Structured JSON response
        """
        lesson = self.get_current_lesson()
        module = self.get_current_module()

        if not lesson or not module:
            raise ValueError("No current lesson available")

        # Build system prompt
        system_prompt = self._build_system_prompt(lesson, module)

        # Build user message
        if user_input is None:
            user_message = "[SYSTEM] Start the lesson. This is your first message to the learner."
        else:
            user_message = user_input

        # Add to conversation history
        if user_input is not None:
            self.conversation_history.append({
                "role": "user",
                "content": user_input
            })

        # Prepare contents for Gemini
        contents = []

        # Add conversation history
        for msg in self.conversation_history:
            contents.append(
                types.Content(
                    role=msg["role"],
                    parts=[types.Part.from_text(text=msg["content"])],
                )
            )

        # Add current user message if this is the initial message
        if user_input is None:
            contents.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=user_message)],
                )
            )

        # Use system_instruction parameter instead of prepending as user message
        generate_content_config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.0,
            top_p=0.95,
            max_output_tokens=4000,
            response_mime_type="application/json",  # Force JSON output
        )

        try:
            start_time = time.time()
            usage_metadata = None

            full_response = ""
            for chunk in self.client.models.generate_content_stream(
                model=self.model_name,
                contents=contents,
                config=generate_content_config,
            ):
                if chunk.text:
                    full_response += chunk.text
                if chunk.usage_metadata:
                    usage_metadata = chunk.usage_metadata

            end_time = time.time()
            self.last_response_time = end_time - start_time

            if usage_metadata:
                self.last_token_usage = {
                    "input_tokens": usage_metadata.prompt_token_count,
                    "output_tokens": usage_metadata.candidates_token_count,
                    "total_tokens": usage_metadata.total_token_count
                }
            else:
                self.last_token_usage = {}

            # Parse JSON response
            response_json = self._extract_json(full_response)

            # Validate that we got a dict, not a string
            if not isinstance(response_json, dict):
                print(f"   ❌ Invalid response type: {type(response_json).__name__}")
                raise ValueError(f"JSON extraction returned {type(response_json).__name__} instead of dict. Content: {str(response_json)[:200]}")

            # Print clean, formatted response
            print(f"\n{'='*80}")
            print(f"🤖 GEMINI RESPONSE")
            print(f"{'='*80}")

            print(f"\n💭 THOUGHT PROCESS:")
            print(f"{response_json.get('thought_process', 'N/A')}")

            print(f"\n💬 CONVERSATION CONTENT:")
            print(f"{response_json.get('conversation_content', 'N/A')}")

            print(f"\n📝 EDITOR CONTENT:")
            editor = response_json.get('editor_content')
            if editor:
                print(f"   Type: {editor.get('type', 'N/A')}")
                print(f"   Language: {editor.get('language', 'N/A')}")
                print(f"   Content:")
                print(f"{editor.get('content', 'N/A')}")
            else:
                print(f"   (None)")

            print(f"\n📊 LESSON STATUS:")
            lesson_status = response_json.get('lesson_status', {})
            print(f"   Phase: {lesson_status.get('current_phase', 'N/A')}")
            print(f"   Waiting for user: {lesson_status.get('is_waiting_for_user_action', 'N/A')}")

            print(f"\n{'='*80}\n")

            # Add assistant response to conversation history
            self.conversation_history.append({
                "role": "model",
                "content": full_response
            })

            return response_json

        except Exception as e:
            print(f"❌ Error generating response: {e}")
            import traceback
            traceback.print_exc()
            raise e

    def _build_system_prompt(self, lesson: Dict, module: Dict) -> str:
        """
        Build comprehensive system prompt for the LLM.

        Includes:
        - Role and behavior instructions
        - User baseline and objective
        - Acquired knowledge
        - Current lesson's URAC blueprint
        - JSON output schema enforcement
        """
        urac = lesson.get("urac_blueprint", {})
        module_context_bridge = module["lesson_plan"].get("module_context_bridge", "")

        acquired_knowledge_list = self.get_acquired_knowledge()
        acquired_knowledge_str = "\n".join([f"  • {k}" for k in acquired_knowledge_list]) if acquired_knowledge_list else "  (None - this is the first lesson)"

        print(f"\n📚 Acquired Knowledge being sent to Gemini:")
        print(f"   Count: {len(acquired_knowledge_list)} items")
        if acquired_knowledge_list:
            for i, knowledge in enumerate(acquired_knowledge_list[:3], 1):
                preview = knowledge[:80] + "..." if len(knowledge) > 80 else knowledge
                print(f"   {i}. {preview}")
            if len(acquired_knowledge_list) > 3:
                print(f"   ... and {len(acquired_knowledge_list) - 3} more")
        else:
            print(f"   ℹ️  No acquired knowledge (first lesson)")

        system_prompt = f"""You are an Expert Mentor executing an interactive micro-lesson.

# LEARNER CONTEXT

**Baseline:** {self.user_baseline}
**Objective:** {self.user_objective}
**Prior Knowledge:** {acquired_knowledge_str}

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
3. Include a key insight using blockquote: > **Key:** [the critical point]
4. Then ask the Analytical Question based on: "{urac.get("retain", "")}"

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
    A[Data] --> B{{Decision}}
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

ENGAGE → DEEPEN: When learner answers the easy question correctly
DEEPEN → APPLY: When learner answers the analytical question correctly
APPLY → COMPLETED: When learner completes the task successfully

**On incorrect answers:** Stay in current phase, give hints/guidance, let them retry."""

        return system_prompt

    def _extract_json(self, text: str) -> Dict:
        """
        Smart JSON extraction with multiple fallback strategies.

        Tries:
        1. Standard JSON parsing on raw text (since we force JSON output)
        2. Markdown code fence extraction
        3. Finding first { to last } (with proper brace counting)
        4. json_repair for malformed JSON
        5. Constructing valid JSON from key-value patterns
        """
        original_text = text
        text = text.strip()

        # Strategy 1: Try standard JSON parsing on raw text first
        # Since we use response_mime_type="application/json", the LLM should output valid JSON
        try:
            result = json.loads(text)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass

        # Strategy 2: Try markdown code fences
        start_marker = "```json"
        end_marker = "```"
        start_idx = text.find(start_marker)

        if start_idx == -1:
            start_marker = "```"
            start_idx = text.find(start_marker)

        if start_idx != -1:
            end_idx = text.find(end_marker, start_idx + len(start_marker))
            if end_idx != -1:
                json_str = text[start_idx + len(start_marker):end_idx].strip()
            else:
                json_str = text[start_idx + len(start_marker):].strip()
        else:
            json_str = text

        # Strategy 3: Try standard JSON parsing after fence extraction
        try:
            result = json.loads(json_str)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass

        # Strategy 4: Try to find JSON object boundaries with proper brace counting
        first_brace = json_str.find('{')
        if first_brace != -1:
            # Count braces to find the matching closing brace
            brace_count = 0
            in_string = False
            escape_next = False
            last_brace = -1

            for i in range(first_brace, len(json_str)):
                char = json_str[i]

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
                            last_brace = i
                            break

            if last_brace != -1:
                json_str = json_str[first_brace:last_brace + 1]

        # Strategy 5: Try standard JSON parsing after boundary extraction
        try:
            result = json.loads(json_str)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass

        # Strategy 6: Try json_repair
        try:
            repaired = json_repair.loads(json_str)
            if isinstance(repaired, dict):
                print("  ⚠️  JSON was malformed but successfully repaired")
                return repaired
            else:
                print(f"  ⚠️  json_repair returned {type(repaired).__name__} instead of dict, skipping")
        except Exception:
            pass

        # Strategy 7: Last resort - try to extract from raw text
        # If the LLM output looks like "thought_process\nThe user is..." without JSON structure
        if '{' not in original_text and '"thought_process"' not in original_text:
            # Try to construct a minimal valid response
            print("  ⚠️  No JSON structure found, attempting reconstruction...")
            try:
                # Extract content sections using pattern matching
                thought_match = re.search(r'thought_process[:\s]*(.*?)(?=conversation_content|$)', original_text, re.DOTALL)
                conv_match = re.search(r'conversation_content[:\s]*(.*?)(?=editor_content|lesson_status|$)', original_text, re.DOTALL)

                thought = thought_match.group(1).strip() if thought_match else "Processing lesson"
                conv = conv_match.group(1).strip() if conv_match else original_text[:500]

                reconstructed = {
                    "thought_process": thought,
                    "conversation_content": conv,
                    "editor_content": {"type": "text", "language": "markdown", "content": None},
                    "lesson_status": {"current_phase": "TEACHING", "is_waiting_for_user_action": True}
                }
                print(f"  ✓ Reconstructed JSON from unstructured response")
                return reconstructed
            except Exception:
                pass

        # All strategies failed
        print(f"\n❌ JSON Extraction Failed - All strategies exhausted")
        print(f"Response length: {len(original_text)} chars")
        print(f"First 300 chars: {original_text[:300]}")
        print(f"Last 200 chars: {original_text[-200:]}")
        raise ValueError(f"Could not extract valid JSON from LLM response after trying all strategies")

    def get_progress_info(self) -> Dict[str, Any]:
        """Get current progress information."""
        if not self.module_plans:
            return {
                "total_modules": 0,
                "total_lessons": 0,
                "current_module": 0,
                "current_lesson": 0,
                "module_title": "",
                "lesson_topic": ""
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
