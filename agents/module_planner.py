"""
Module Planner Agent
Takes a high-level module from a learning path and breaks it down into atomic micro-lessons
following the URAC (Understand, Retain, Apply, Connect) framework.

Supports two models:
- Gemini Flash Latest
- Groq GPT-OSS 120B
"""

import time
import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types
from groq import Groq
import json_repair

load_dotenv()


class ModulePlannerAgent:
    """
    Module planner that breaks down high-level modules into atomic micro-lessons.
    """

    def __init__(self, model_provider: str = "gemini"):
        """
        Initialize the agent with specified model provider.

        Args:
            model_provider: Either "gemini" or "groq"
        """
        self.model_provider = model_provider.lower()

        if self.model_provider == "gemini":
            self.model_name = "gemini-flash-latest"
            self.client = self._setup_gemini()
        elif self.model_provider == "groq":
            self.model_name = "openai/gpt-oss-120b"
            self.client = self._setup_groq()
        else:
            raise ValueError(f"Unknown model provider: {model_provider}. Use 'gemini' or 'groq'")

    def _setup_gemini(self):
        """Setup Google GenAI client."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in .env")
        return genai.Client(api_key=api_key)

    def _setup_groq(self):
        """Setup Groq client."""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in .env")
        return Groq(api_key=api_key)

    def plan_module(
        self,
        user_baseline: str,
        user_objective: str,
        current_module: dict,
        acquired_knowledge_history: list = None
    ):
        """
        Break down a high-level module into atomic micro-lessons.

        Args:
            user_baseline: The user's current knowledge and skills
            user_objective: The specific goal the user wants to achieve
            current_module: The module to break down (from learning path)
            acquired_knowledge_history: List of competencies from previous modules

        Returns:
            Dictionary with lesson plan following URAC framework
        """
        if acquired_knowledge_history is None:
            acquired_knowledge_history = []

        print(f"\n{'='*80}")
        print(f"MODULE PLANNER AGENT ({self.model_provider.upper()})")
        print(f"{'='*80}")
        print(f"Module: {current_module.get('title', 'N/A')}")
        print(f"Provider: {self.model_name}\n")

        system_prompt = """**Role**
You are an Expert Curriculum Architect. Your role is to design lesson blueprints for a "Mastery Engine" that will execute them.

**Design Principle:**
Create tasks that build mastery through HIGH COGNITIVE EFFORT rather than LOW COGNITIVE EFFORT.

HIGH cognitive effort = Requires decisions, analysis, reasoning, understanding relationships, choosing approaches, solving problems.
LOW cognitive effort = Repetitive, mechanical, following known patterns, formatting, structuring without thinking.

The Mastery Engine will provide scaffolding for low-cognitive but time-consuming parts during execution.

**Input Data**
You will receive:

1.  **User Baseline:** The user's initial existing knowledge, skills, and mental models.
2.  **User Objective:** The specific goal the user wants to achieve.
3.  **Current Module:** The high-level topic that needs to be broken down now.
4.  **Acquired Knowledge History:** A list of summaries from previously completed modules (if any). Use this to avoid redundancy and to anchor new concepts to recently learned ones.

**The Architectural Framework (URAC)**
You must break the Module into a linear sequence of atomic "Micro-Lessons." For each lesson, you must define a **URAC Blueprint** that guides the downstream Mastery Engine on *what* to execute:

  * **Understand:** Define the scope of the new mental model to be taught.
  * **Retain:** Design an analytical question that requires HIGH COGNITIVE EFFORT rather than simple recall. The question should make the user process and synthesize what they learned, not just repeat it.
  * **Apply:** Design a GENERATIVE task requiring HIGH COGNITIVE EFFORT (create, analyze, construct, etc). Assume the Mastery Engine will provide scaffolding for low-cognitive but time-consuming parts.
  * **Connect:** Specify how to link this concept back to the user's baseline, objective, or previously acquired knowledge.

**Strict Constraints**

  * **User-Directed Language:** Write directly to the user using second person ("you will", "you can"), NOT third person ("the learner will"). The user reads this content themselves.
  * **No Lecture Content:** Do not generate paragraphs of explanation or dialogue. Only generate directives.
  * **Atomic Concepts:** One single concept per lesson beat.
  * **Agnostic Design:** Your blueprints must work regardless of whether the topic is technical, scientific, or soft skills.
  * **Stateful Planning:** Do not include concepts in the lesson plan that appear in the "Acquired Knowledge History."
  * **Text or Code-Based Evaluation:** Assume NO external environment or tools. A good AI must be able to evaluate the user's success solely based on their text/code input

**Output Format**
You must output a single valid JSON object following this schema:

```json
{
  "module_id": module_order
  "module_context_bridge": "<Instruction: For the first module, connect to the User's Baseline. For subsequent modules, connect to recently Acquired Knowledge (and optionally baseline). Write directly to the user explaining what they already know that will help them with this module.>",
  "lesson_plan": [
    {
      "sequence": 1,
      "topic": "<Title of the specific micro-topic>",
      "urac_blueprint": {
        "understand": "Define the specific concept/mental model to be taught (the boundary of what to learn).",
        "retain": "Write an analytical question requiring HIGH COGNITIVE EFFORT - NOT simple recall.",
        "apply": "Write a GENERATIVE task requiring HIGH COGNITIVE EFFORT. The user must create/analyze/construct something concrete. The Mastery Engine will provide scaffolding for low-cognitive parts.",
        "connect": "Specify how to link this lesson to the user's objective or prior knowledge."
      }
    }
  ],
  "acquired_competencies": [
    "<List 2-3 concise phrases describing what the user learned and can effectively apply after this module.>"
  ]
}
```
"""

        acquired_knowledge_str = "\n".join([f"- {comp}" for comp in acquired_knowledge_history]) if acquired_knowledge_history else "None (this is the first module)"

        user_prompt = f"""<user_input>
User Baseline: {user_baseline}

User Objective: {user_objective}

Current Module:
Title: {current_module.get('title', 'N/A')}
Competency Goal: {current_module.get('competency_goal', 'N/A')}
Mental Map: {json.dumps(current_module.get('mental_map', []), indent=2)}
Application: {json.dumps(current_module.get('application', []), indent=2)}
Relevance to Goal: {current_module.get('relevance_to_goal', 'N/A')}

Acquired Knowledge History:
{acquired_knowledge_str}
</user_input>"""

        if self.model_provider == "gemini":
            return self._generate_with_gemini(system_prompt, user_prompt)
        else:
            return self._generate_with_groq(system_prompt, user_prompt)

    def _generate_with_gemini(self, system_prompt: str, user_prompt: str):
        """Generate lesson plan using Gemini."""
        try:
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=f"{system_prompt}\n\n{user_prompt}"),
                    ],
                ),
            ]

            generate_content_config = types.GenerateContentConfig(
                temperature=0.0,
                top_p=1.0,
                max_output_tokens=16000,
            )

            print("📝 Generating lesson plan with Gemini...\n")
            print("─" * 80)

            start_time = time.time()
            usage_metadata = None
            finish_reason = None

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
                if hasattr(chunk, 'candidates') and chunk.candidates:
                    if hasattr(chunk.candidates[0], 'finish_reason'):
                        finish_reason = chunk.candidates[0].finish_reason

            end_time = time.time()
            duration = end_time - start_time

            print("\n" + "─" * 80 + "\n")

            response_length = len(full_response)
            print(f"📊 Stats:")
            print(f"   ⏱️  Time: {duration:.2f}s")
            if usage_metadata:
                input_tokens = usage_metadata.prompt_token_count
                output_tokens = usage_metadata.candidates_token_count
                total_tokens = usage_metadata.total_token_count
                print(f"   🔢 Tokens: {total_tokens:,} (In: {input_tokens:,}, Out: {output_tokens:,})")
            else:
                print(f"   🔢 Tokens: Unknown")
            print(f"   📝 Response length: {response_length:,} chars")
            if finish_reason:
                print(f"   🏁 Finish reason: {finish_reason}")
            print()

            lesson_plan = self._extract_json(full_response)
            return lesson_plan

        except Exception as e:
            print(f"\n❌ Error: {e}")
            raise e

    def _generate_with_groq(self, system_prompt: str, user_prompt: str):
        """Generate lesson plan using Groq."""
        try:
            print(f"📝 Generating lesson plan with Groq ({self.model_name})...\n")

            start_time = time.time()

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.0,
                max_tokens=8000,
                top_p=1,
                stream=False,
                reasoning_effort="medium"
            )

            end_time = time.time()
            duration = end_time - start_time

            content = response.choices[0].message.content

            print("─" * 80 + "\n")

            if hasattr(response, 'usage'):
                usage = response.usage
                print(f"📊 Stats:")
                print(f"   ⏱️  Time: {duration:.2f}s")
                print(f"   🔢 Tokens: {usage.total_tokens:,} (In: {usage.prompt_tokens:,}, Out: {usage.completion_tokens:,})\n")

            lesson_plan = self._extract_json(content)
            return lesson_plan

        except Exception as e:
            print(f"\n❌ Error: {e}")
            raise e

    def _extract_json(self, text: str):
        """Extract JSON from LLM response wrapped in markdown."""
        text = text.strip()

        start_marker = "```json"
        end_marker = "```"

        start_idx = text.find(start_marker)
        if start_idx == -1:
            start_marker = "```"
            start_idx = text.find(start_marker)
            if start_idx == -1:
                try:
                    return json_repair.loads(text)
                except Exception as e:
                    print(f"❌ JSON parsing error: {e}")
                    print(f"Response (first 800 chars): {text[:800]}")
                    raise ValueError(f"Invalid JSON response: {str(e)}")

        end_idx = text.find(end_marker, start_idx + len(start_marker))

        if end_idx == -1:
            print(f"⚠️  No closing '```' found, attempting to extract JSON anyway...")
            json_str = text[start_idx + len(start_marker):].strip()
        else:
            json_str = text[start_idx + len(start_marker):end_idx].strip()

        try:
            result = json_repair.loads(json_str)
            if end_idx == -1:
                print(f"  ✅ JSON extracted successfully despite missing closing marker")
            return result
        except Exception as e:
            print(f"❌ JSON parsing error: {e}")
            print(f"  JSON string (first 800 chars): {json_str[:800]}")
            print(f"  JSON string (last 200 chars): {json_str[-200:]}")
            raise ValueError(f"Invalid JSON in code block: {str(e)}")


def process_learning_path(
    learning_path_file: str,
    model_provider: str = "gemini",
    output_file: str = "module_plans.json"
):
    """
    Process all modules in a learning path file.

    Args:
        learning_path_file: Path to LPgemini.json file
        model_provider: "gemini" or "groq"
        output_file: Where to save the results
    """
    with open(learning_path_file, 'r') as f:
        data = json.load(f)

    user_baseline = data['input']['user_baseline']
    user_objective = data['input']['user_objective']
    curriculum = data['learning_path']['curriculum']

    print(f"\n{'='*80}")
    print(f"PROCESSING LEARNING PATH")
    print(f"{'='*80}")
    print(f"Total modules: {len(curriculum)}")
    print(f"Model provider: {model_provider}\n")

    agent = ModulePlannerAgent(model_provider=model_provider)

    acquired_knowledge_history = []
    module_plans = []

    for idx, module in enumerate(curriculum, 1):
        print(f"\n{'#'*80}")
        print(f"PROCESSING MODULE {idx}/{len(curriculum)}")
        print(f"{'#'*80}\n")

        lesson_plan = agent.plan_module(
            user_baseline=user_baseline,
            user_objective=user_objective,
            current_module=module,
            acquired_knowledge_history=acquired_knowledge_history
        )

        print_lesson_plan(lesson_plan, module['title'])

        new_competencies = lesson_plan.get('acquired_competencies', [])
        acquired_knowledge_history.extend(new_competencies)

        module_plans.append({
            "module_order": idx,
            "original_module": module,
            "lesson_plan": lesson_plan,
            "acquired_knowledge_at_this_point": acquired_knowledge_history.copy()
        })

    output = {
        "input": {
            "user_baseline": user_baseline,
            "user_objective": user_objective,
            "learning_path_file": learning_path_file,
            "model_provider": model_provider
        },
        "module_plans": module_plans
    }

    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n{'='*80}")
    print(f"✅ All modules processed!")
    print(f"✅ Results saved to: {output_file}")
    print(f"{'='*80}\n")


def print_lesson_plan(lesson_plan: dict, module_title: str):
    """Pretty print a lesson plan."""
    print(f"\n{'='*80}")
    print(f"LESSON PLAN: {module_title}")
    print(f"{'='*80}\n")

    print(f"🆔 Module ID: {lesson_plan.get('module_id', 'N/A')}")
    print(f"🌉 Context Bridge: {lesson_plan.get('module_context_bridge', 'N/A')}\n")

    print(f"{'─'*80}")
    print(f"MICRO-LESSONS ({len(lesson_plan.get('lesson_plan', []))} lessons):")
    print(f"{'─'*80}")

    for lesson in lesson_plan.get('lesson_plan', []):
        blueprint = lesson.get('urac_blueprint', {})
        print(f"\n[Lesson {lesson['sequence']}] {lesson['topic']}")
        print(f"  🧠 Understand: {blueprint.get('understand', 'N/A')}")
        print(f"  💾 Retain: {blueprint.get('retain', 'N/A')}")
        print(f"  🔧 Apply: {blueprint.get('apply', 'N/A')}")
        print(f"  🔗 Connect: {blueprint.get('connect', 'N/A')}")

    print(f"\n{'─'*80}")
    print(f"📚 ACQUIRED COMPETENCIES:")
    print(f"{'─'*80}")
    for comp in lesson_plan.get('acquired_competencies', []):
        print(f"  ✓ {comp}")

    print(f"\n{'='*80}\n")


def main():
    """Main function for testing."""
    print("\n" + "="*80)
    print("MODULE PLANNER AGENT")
    print("="*80)
    print("\nBreaks down high-level modules into atomic micro-lessons")
    print("following the URAC framework.\n")

    learning_path_file = "LPgemini.json"
    model_provider = "gemini" # or groq

    if not os.path.exists(learning_path_file):
        print(f"❌ Error: {learning_path_file} not found!")
        print(f"Please ensure the learning path file exists in the current directory.")
        return

    try:
        process_learning_path(
            learning_path_file=learning_path_file,
            model_provider=model_provider,
            output_file="module_plans.json"
        )
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if not os.path.exists(".env"):
        print("\n⚠️  No .env file found!")
        print("Create .env with:")
        print("  GEMINI_API_KEY=your_key")
        print("  GROQ_API_KEY=your_key")
        exit(1)

    main()
