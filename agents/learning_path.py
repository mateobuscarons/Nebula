"""
Learning Path Agent
Uses Gemini Flash Latest for generating learning paths.
"""

import time
import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()


class LearningPathAgent:
    """
    Learning path generator using Gemini.
    Single-step process: path generation only.
    """

    def __init__(self):
        """Initialize the agent with Google GenAI client."""
        self.model_name = "gemini-flash-latest"
        self.client = self._setup_llm()

    def _setup_llm(self):
        """Setup Google GenAI client."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in .env")
        return genai.Client(api_key=api_key)

    def generate(self, user_context: str, user_goal: str):
        """
        Generate learning path based on user baseline and objective.
        Single-step process: path generation only.

        Args:
            user_context: The user's current baseline (expertise, experience, knowledge)
            user_goal: The practical objective the user wants to achieve

        Returns:
            Dictionary with learning path
        """
        print(f"\n{'='*80}")
        print(f"LEARNING PATH AGENT (GEMINI)")
        print(f"{'='*80}")
        print(f"Baseline: {user_context}")
        print(f"Objective: {user_goal}\n")

        print(f"🤖 Generating learning path with Gemini Flash...\n")

        system_prompt = """You are an expert instructional designer and curriculum architect. Your task is to generate a personalized, goal-driven learning path that efficiently bridges the gap between a learner's current expertise and their target objective.

## INPUTS
You will receive:
1. **User's Baseline**: Their current knowledge, skills, experience, and what they can already accomplish related to the objective.
2. **User's Objective**: The specific, practical outcome they want to achieve. This is the north star—every module must serve this goal.

## YOUR TASK
Analyze the gap between baseline and objective, then construct a lean, progressive curriculum of **Minimum Viable Knowledge (MVK)**—the essential theory and practice required to achieve the objective, nothing more.

## CURRICULUM DESIGN PRINCIPLES

### 1. Gap-Focused
- Include ONLY what closes the gap between current state and objective
- Exclude any topic the user already knows or that doesn't directly enable the goal
- If the user has strong foundations, the path should be short; if foundations are missing, build them

### 2. Theory-Practice Balance
- Each module must blend conceptual understanding ("why" and "how it works") with hands-on application ("do it")
- Theory exists to enable confident application, not for its own sake
- Application must be realistic and tied to the stated objective
- Applications must be achievable independently or via AI-assisted simulation (no dependency on external partners or teams).

### 3. Pedagogical Scaffolding & Isolation
- **Separation of Concerns**: Ensure each module targets a single "failure domain" or conceptual leap. Do not bundle distinct complex topics.
- **Linear Progression**: Sequence modules so the output of Module N becomes the input for Module N+1.
- Build mental models progressively—connect new concepts to prior ones.

### 4. Pragmatic Scope & Density
- **Cognitive Load Management**: Better to have 5 focused modules than 3 dense ones. If an Application step requires the user to juggle more than 3 distinct new concepts, split the module.
- Design for busy professionals: Modules must be substantial but finishable in one sitting.
- Total curriculum: minimum 2 modules, maximum 8 modules.

### 5. Strict Scope & Exclusion Criteria
Apply these filters rigorously. Only include a topic/module if it meets **ALL** of these conditions:
1. The learner **CANNOT** achieve the stated objective without this knowledge.
2. Skipping it would cause immediate failure or broken functionality.
3. It is not already covered by another module (even partially).

**Explicitly EXCLUDE:**
- Best practices or optimizations (unless essential for basic functionality).
- Topics the user didn't ask for (Scope Creep).
- Enhancements beyond what the objective explicitly or implicitly requires.
- Learnings that depend on resources, access, or approvals outside the learner's direct control (e.g., paid services, cloud accounts, proprietary tools).

## OUTPUT FORMAT
Return a single valid JSON object with this exact structure:

{
  "pedagogical_strategy": "Brief analysis of: (1) the key gaps identified, (2) the sequencing logic, and (3) any baseline strengths you're leveraging.",
  "curriculum": [
    {
      "module_order": 1,
      "title": "Concise, descriptive module title",
      "competency_goal": "What you will understand and be able to do after completing this module. Write directly to the user using second person ('you will', 'you can'), NOT third person ('the learner will').",
      "mental_map": [
        "First core concept, framework, or theory point",
        "Second core concept, framework, or theory point",
        ...
      ],
      "application": [
        "First specific hands-on exercise or practice activity",
        "Second specific hands-on exercise or practice activity",
        ..."
      ],
      "relevance_to_goal": "Explicitly state WHY this module is necessary and HOW it connects to achieving the user's objective."
    }
  ]
}

## RULES
- Output ONLY the JSON object. No preamble, no markdown code fences, no explanation outside the JSON.
- Every module must have a clear, non-redundant purpose.
- Write for clarity and actionability. Avoid vague descriptions."""

        user_prompt = f"""<user_input>
User Baseline: {user_context}
User Objective: {user_goal}
</user_input>"""

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
                max_output_tokens=8000,
            )

            
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
            duration = end_time - start_time
            
            print("\n" + "─" * 80 + "\n")
            
            if usage_metadata:
                input_tokens = usage_metadata.prompt_token_count
                output_tokens = usage_metadata.candidates_token_count
                total_tokens = usage_metadata.total_token_count
                print(f"📊 Stats:")
                print(f"   ⏱️  Time: {duration:.2f}s")
                print(f"   🔢 Tokens: {total_tokens:,} (In: {input_tokens:,}, Out: {output_tokens:,})\n")
            else:
                print(f"📊 Stats:")
                print(f"   ⏱️  Time: {duration:.2f}s")
                print(f"   🔢 Tokens: Unknown\n")

            learning_path = self._extract_json(full_response)

            return {
                "learning_path": learning_path
            }

        except Exception as e:
            print(f"\n❌ Error: {e}")
            raise e

    def regenerate_with_feedback(self, original_path: dict, user_feedback: str, learning_goal: str):
        """
        Regenerate learning path based on user feedback using Groq llama-3.3-70b-versatile.
        The original path is treated as the ideal baseline - only adjust based on feedback.

        Args:
            original_path: The original learning path (the ideal starting point)
            user_feedback: User's feedback on what to adjust
            learning_goal: The user's learning goal

        Returns:
            Dictionary with adjusted learning path (same format as original)
        """
        from groq import Groq
        
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY not found in .env")
        
        groq_client = Groq(api_key=groq_api_key)
        
        print(f"\n{'='*80}")
        print(f"LEARNING PATH ADJUSTMENT (GROQ LLAMA 3.3 70B)")
        print(f"{'='*80}")
        print(f"Feedback: {user_feedback}\n")

        original_path_json = json.dumps(original_path, indent=2)

        system_prompt = """You are a curriculum refinement specialist. Your task is to ADJUST an existing learning path based on user feedback.

## CRITICAL RULES
1. The original learning path is HIGH QUALITY and should be treated as the ideal baseline
2. Make MINIMAL changes - only what the feedback specifically requests
3. Preserve the pedagogical structure and sequencing logic
4. Do NOT add modules unless explicitly requested
5. Do NOT remove modules unless explicitly requested
6. Adjust content within modules when possible instead of restructuring

## ADJUSTMENT PRINCIPLES
- If feedback asks to add a topic: integrate it into the most relevant existing module, or add a new module only if it's truly distinct
- If feedback asks to remove something: remove it cleanly without breaking dependencies
- If feedback asks for more/less depth: adjust the content accordingly
- If feedback is about pacing: consider splitting or merging modules

## OUTPUT FORMAT
Return ONLY a valid JSON object with this exact structure (same as input):

{
  "pedagogical_strategy": "Updated strategy reflecting the adjustments made",
  "curriculum": [
    {
      "module_order": 1,
      "title": "Module title",
      "competency_goal": "What the learner will understand and be able to do",
      "mental_map": [
        "First core concept, framework, or theory point",
        "Second core concept, framework, or theory point",
        ...
      ],
      "application": [
        "First specific hands-on exercise or practice activity",
        "Second specific hands-on exercise or practice activity",
        ...
      ],
      "relevance_to_goal": "WHY this module is necessary and HOW it connects to achieving the objective"
    }
  ]
}

RULES:
- Output ONLY the JSON object. No preamble, no markdown code fences, no explanation
- Maintain module_order sequential ordering (1, 2, 3, ...)
- Preserve the exact JSON structure of the original"""

        user_prompt = f"""## ORIGINAL LEARNING PATH (treat as ideal baseline):
```json
{original_path_json}
```

## LEARNING GOAL:
{learning_goal}

## USER FEEDBACK (apply these adjustments):
{user_feedback}

Adjust the learning path based on the feedback while preserving as much of the original structure as possible."""

        try:
            print(f"🔄 Adjusting learning path with Llama 3.3 70B...\n")
            
            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=8000,
                top_p=1,
                stream=False
            )

            content = response.choices[0].message.content
            
            if hasattr(response, 'usage'):
                usage = response.usage
                print(f"📊 Stats:")
                print(f"   🔢 Tokens: {usage.total_tokens:,} (In: {usage.prompt_tokens:,}, Out: {usage.completion_tokens:,})\n")

            adjusted_path = self._extract_json(content)
            
            print(f"✅ Learning path adjusted: {len(adjusted_path.get('curriculum', []))} modules\n")
            
            return {
                "learning_path": adjusted_path
            }

        except Exception as e:
            print(f"\n❌ Adjustment Error: {e}")
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
                    return json.loads(text)
                except json.JSONDecodeError as e:
                    print(f"❌ JSON parsing error: {e}")
                    print(f"Response (first 500 chars): {text[:500]}")
                    raise ValueError(f"Invalid JSON response: {str(e)}")

        end_idx = text.find(end_marker, start_idx + len(start_marker))

        if end_idx == -1:
            raise ValueError(f"No closing '```' found for JSON block")

        json_str = text[start_idx + len(start_marker) : end_idx].strip()

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            print(f"  Attempting to repair JSON...")

            try:
                import re
                repaired = re.sub(r',\s*}', '}', json_str)
                repaired = re.sub(r',\s*]', ']', repaired)

                result = json.loads(repaired)
                print(f"  ✅ JSON repaired successfully")
                return result
            except:
                print(f"  ❌ Repair failed")
                raise ValueError(f"Invalid JSON in code block: {str(e)}")


def print_learning_path(path: dict):
    """Pretty print learning path."""
    print(f"\n{'='*80}")
    print(f"LEARNING PATH GENERATED")
    print(f"{'='*80}\n")

    print(f"📋 PEDAGOGICAL STRATEGY:")
    print(f"   {path.get('pedagogical_strategy', 'N/A')}\n")

    print(f"{'─'*80}")
    print(f"CURRICULUM ({len(path.get('curriculum', []))} modules):")
    print(f"{'─'*80}")

    for module in path.get('curriculum', []):
        print(f"\n[Module {module['module_order']}] {module['title']}")
        print(f"  🎯 Competency Goal: {module['competency_goal']}")
        print(f"  🧠 Mental Map: {module.get('mental_map', 'N/A')}")
        print(f"  🔧 Application: {module.get('application', 'N/A')}")
        print(f"  💡 Relevance: {module['relevance_to_goal']}")

    print(f"\n{'='*80}\n")


def main():
    """Main function with test inputs."""
    print("\n" + "="*80)
    print("LEARNING PATH GENERATOR (GEMINI)")
    print("="*80)
    print("\nDesign your personalized learning pathway!\n")
    print("This agent will create a curriculum that bridges the gap between")
    print("where you are now and where you want to be.\n")

    # Test inputs
    user_context = "I am a Senior Backend Developer (Node.js/Go) comfortable with Linux command line. I use Docker daily: I can write multi-stage Dockerfiles, optimize image sizes, and use docker-compose for local development. However, I have zero experience with orchestration. Concepts like 'Pods,' 'Ingress,' or 'Helm charts' are abstract to me. I understand basic networking (ports, DNS) but find Kubernetes manifests verbose and confusing."

    user_goal = "My company is migrating our monolithic app to microservices on a cloud provider. My specific goal is to take three of our existing dockerized microservices (Frontend, API, Database) and deploy them into a live Kubernetes cluster. I need to be able to configure them so they can communicate securely (Service Discovery/Secrets), expose the frontend to the public internet (Ingress), and perform a 'Rolling Update' without downtime. I need to be able to debug if a Pod gets stuck in CrashLoopBackOff."

    print(f"\n📋 Single-step process:")
    print(f"   Learning Path Design: Gemini Flash Latest")

    try:
        agent = LearningPathAgent()
        result = agent.generate(user_context, user_goal)

        learning_path = result.get("learning_path", {})

        print_learning_path(learning_path)

        output_file = "LPgemini.json"

        with open(output_file, "w") as f:
            json.dump({
                "input": {
                    "user_baseline": user_context,
                    "user_objective": user_goal
                },
                "learning_path": learning_path
            }, f, indent=2)

        print(f"✅ Results saved to: {output_file}\n")

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
