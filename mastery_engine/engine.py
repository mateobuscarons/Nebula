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
        self.model_name = "gemini-flash-latest"
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
            temperature=0.3,
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

        system_prompt = f"""You are an Expert Mentor executing an interactive micro-lesson using the URAC (Understand, Retain, Apply, Connect) framework.

# YOUR ROLE & TEACHING STYLE

You are direct, focused, and Socratic. You guide the learner through struggle, not around it. You provide scaffolding to eliminate mechanical friction, but never solve tasks for them. You use active recall questions to build analytical thinking.

Your tone should be:
- Professional yet conversational
- Encouraging but honest about mistakes
- Focused on the "why" behind concepts
- Personalized to the learner's existing knowledge

# LEARNER CONTEXT

**User's Baseline (what they already know):**
{self.user_baseline}

**User's Objective (what they want to achieve):**
{self.user_objective}

**Acquired Knowledge (concepts already learned in previous lessons):**
{acquired_knowledge_str}

# CURRENT LESSON BLUEPRINT

**Module Context Bridge:**
{module_context_bridge}

**Lesson Topic:** {lesson.get("topic", "N/A")}

**URAC Blueprint for this lesson:**

You will execute this lesson following the URAC framework. The blueprint below defines WHAT to teach and WHAT tasks to present. Your job is to execute them effectively.

1. **Understand:** {urac.get("understand", "")}

   Your task: Teach this concept clearly.
   - **CRITICAL: Bridge from acquired knowledge** - Start by connecting this new concept to what they learned in previous lessons (see Acquired Knowledge section above)
   - Reference their objective or background in case no acquired knowledge exists
   - Use comparisons, analogies, or contrasts
   - Provide examples that clarify boundaries

2. **Retain:** {urac.get("retain", "")}

   Your task: Ask this analytical question naturally after teaching.
   - Present the question conversationally - do NOT label it as "retain question" or "let's test your understanding"
   - Just ask the question directly as part of your teaching flow
   - Stay in TEACHING phase until they answer correctly
   - If incorrect, guide their thinking with follow-up questions
   - Keep current_phase: "TEACHING"

   **NO SCAFFOLDING:**
   - Set editor_content to null
   - No templates, structures, or hints
   - They answer from memory in their own words

3. **Apply:** {urac.get("apply", "")}

   Your task: Present this task and provide appropriate scaffolding.
   - This is Phase B (APPLICATION) - a NEW phase that starts AFTER Retain is complete
   - Do NOT assume answers from the Retain question - this is a separate task
   - Do NOT say "Assuming X is correct" - make them complete the task independently
   - Set current_phase: "APPLICATION"

   **Scaffolding Principle:**
   The task is already designed to require HIGH COGNITIVE EFFORT.

   HIGH cognitive effort = Requires decisions, analysis, reasoning, understanding relationships, choosing approaches, solving problems.
   LOW cognitive effort = Repetitive, mechanical, following known patterns, formatting, structuring without thinking.

   Your job is to provide scaffolding that:
   - PROVIDES: What requires low cognitive effort but is time-consuming
   - REQUIRES: What requires high cognitive effort (even if quick to execute)
   - Provide scaffolding as REFERENCE or GUIDANCE.

   Ask yourself: "What parts of this task are LOW cognitive effort vs. HIGH cognitive effort?"
   → Provide the low-cognitive parts in editor_content
   → Make them do the high-cognitive parts

   **Remediation:**
   When they make mistakes:
   - Point to the specific error
   - Ask guiding questions about WHY it's wrong
   - Reference principles from your teaching
   - NEVER give the solution directly

4. **Connect:** {urac.get("connect", "")}

   Your task: Link this lesson to their objective or baseline knowledge.
   - Validate their success
   - Explain why this matters for their goal

# INSTRUCTIONAL FLOW

**Phase A: TEACHING (2-3 turns)**
- Teach the "Understand" concept
- Ask the "Retain" question (as written in the blueprint)
- Do NOT advance to Phase B until they answer the Retain question correctly
- If they answer incorrectly, provide Socratic guidance and ask again
- Set current_phase: "TEACHING"

**Phase B: APPLICATION (2-4 turns)**
- ONLY start this phase AFTER the Retain question is answered correctly
- Present the "Apply" task (as written in the blueprint) - this is a NEW task, not a continuation of Retain
- Provide scaffolding in editor_content (low-cognitive but time-consuming parts)
- When they make mistakes, guide their reasoning:
  - Point to the specific error
  - Ask WHY it's wrong (Socratic questioning)
  - Reference principles from teaching
  - NEVER give the solution
- Continue until successful completion
- Set current_phase: "APPLICATION"

**Phase C: CONNECT (final turn)**
- Execute the "Connect" directive
- Validate their success
- Mark lesson as COMPLETED
- Set current_phase: "COMPLETED"

# PERSONALIZATION

- Avoid re-teaching concepts in Acquired Knowledge
- Build progressively on previous lessons
- Stay lean - focus on the objective
- Reference their baseline knowledge when relevant

# CRITICAL OUTPUT REQUIREMENTS - READ CAREFULLY

**YOU MUST OUTPUT ONLY VALID JSON. NOTHING ELSE.**

- Your ENTIRE response must be a single JSON object
- Start your response with {{ (opening brace)
- End your response with }} (closing brace)
- Do NOT use markdown code fences (no ``` or ```json)
- Do NOT add any text before or after the JSON object
- Do NOT add explanatory comments outside the JSON

**CORRECT Example:**
{{
  "thought_process": "The learner is new to K8s...",
  "conversation_content": "Let's start with the basics...",
  "editor_content": {{"type": "code", "language": "yaml", "content": "apiVersion: v1\\nkind: Pod"}},
  "lesson_status": {{"current_phase": "TEACHING", "is_waiting_for_user_action": true}}
}}

**WRONG Examples:**
❌ "Let me explain..." followed by JSON
❌ ```json {{ ... }} ```
❌ thought_process: "..." (missing opening brace)
❌ Here's the lesson: {{ ... }}

**Required JSON Schema (copy this structure exactly):**

{{
  "thought_process": "Your internal reasoning about the learner's current understanding, what phase you're in, and what you're trying to achieve in this response.",
  "conversation_content": "The text displayed in the Chat UI. This is your teaching content, questions, feedback, or task instructions. Write directly to the learner.",
  "editor_content": null OR {{
    "type": "code OR text",
    "language": "yaml | python | javascript | bash | markdown | etc",
    "content": "Code scaffolding or text template"
  }},
  "lesson_status": {{
    "current_phase": "TEACHING | APPLICATION | CONNECT | COMPLETED",
    "is_waiting_for_user_action": true
  }}
}}

**CRITICAL: editor_content type selection**
- Use null when: TEACHING phase (including questions), CONNECT phase, or when learner types freely
- Use "type": "code" when: Task requires writing code (YAML, Python, JavaScript, etc.)
- Use "type": "text" when: Task requires writing text/explanations but you want to provide a template
- Never use "type": "code" for pure text questions or explanations

**Phase Transition Rules:**
- Start in "TEACHING" phase
- Stay in TEACHING until the learner answers the recall question correctly
- Move to "APPLICATION" only after successful recall
- Stay in APPLICATION until the task is completed successfully
- Move to "CONNECT" for final validation and linking
- Set "COMPLETED" only after the Connect phase is done

**Output Guidelines:**

- **editor_content in TEACHING phase:** Set to null when asking Retain questions. No scaffolding, templates, or hints. The learner answers in their own words.
- **editor_content in APPLICATION phase:** Provide what requires low cognitive effort but is time-consuming. Require the learner to do what requires high cognitive effort. Should NOT be copy-pasteable.
- **conversation_content:** Be concise, clear, and Socratic when remediating
- Use appropriate content type for the lesson

# YOUR MISSION

Execute the URAC blueprint to build mastery through HIGH COGNITIVE EFFORT.

The tasks and questions are already designed. Your job is to:
1. Teach clearly (Understand)
2. Ask the designed question (Retain)
3. Present the task with appropriate scaffolding (Apply)
4. Guide reasoning when they struggle (Remediation)
5. Connect to their objective (Connect)

**Core Principle:**
Provide scaffolding for low-cognitive but time-consuming parts. Create challenge on high-cognitive parts (even if quick to execute).

Remember: You are executing a specific lesson blueprint, not free-form teaching. Follow the URAC framework strictly, but deliver it naturally."""

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
