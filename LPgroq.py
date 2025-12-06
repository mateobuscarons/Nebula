"""
Learning Path Agent - Claude Version
Uses Groq's GPT OSS 120B with high reasoning for generating learning paths.
Includes post-validation quality audit using Llama 3.3 70B.
"""

import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()


class LearningPathAgent:
    """
    Learning path generator with quality validation.
    Step 1: GPT OSS 120B generates learning path curriculum.
    Step 2: Llama 3.3 70B validates curriculum quality and identifies gaps.
    """

    def __init__(self):
        """Initialize the agent with Groq client."""
        self.model_name = "openai/gpt-oss-120b"
        self.client = self._setup_llm()
        self.total_tokens = 0

    def _setup_llm(self):
        """Setup Groq client."""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in .env")
        return Groq(api_key=api_key)

    def _log_token_usage(self, response, step_name=""):
        """Log token usage from Groq response."""
        try:
            if hasattr(response, 'usage'):
                usage = response.usage
                input_tokens = usage.prompt_tokens
                output_tokens = usage.completion_tokens
                total_tokens = usage.total_tokens

                if total_tokens > 0:
                    step_info = f" ({step_name})" if step_name else ""
                    print(f"\n📊 Token Usage{step_info}: {total_tokens:,} tokens (in: {input_tokens:,}, out: {output_tokens:,})")
                    self.total_tokens += total_tokens
        except Exception:
            pass

    def _validate_curriculum(self, user_context: str, user_goal: str, learning_path: dict):
        """
        Validate curriculum quality using Llama 3.3 70B.

        Args:
            user_context: The user's baseline
            user_goal: The user's objective
            learning_path: The generated learning path

        Returns:
            Dictionary with validation status and gaps (if any)
        """
        print(f"🔍 Validating curriculum quality with Llama 3.3 70B...\n")

        # Build curriculum summary
        curriculum_summary = ""
        for module in learning_path.get('curriculum', []):
            curriculum_summary += f"Module {module['module_order']}: {module['title']}\n"
            curriculum_summary += f"  - Goal: {module['competency_goal']}\n"
            curriculum_summary += f"  - Mental Map: {module.get('mental_map', 'N/A')}\n"
            curriculum_summary += f"  - Application: {module.get('application', 'N/A')}\n\n"

        system_prompt = """You are a curriculum quality auditor. Your job is to find gaps in learning paths.

## TASK
Audit the curriculum below. Identify anything missing that would cause the learner to fail or produce incomplete/incorrect results when executing their objective in the real world.

## AUDIT CRITERIA
Only flag gaps that meet ALL of these conditions:
1. The learner CANNOT achieve the stated objective without this knowledge
2. Skipping it would cause failure or broken functionality
3. It is not already covered by another module (even partially)


Do NOT flag:
- Best practices or optimizations
- Topics the user didn't ask for
- Enhancements beyond what the objective explicitly or implicitly requires
- Learnings that depend on resources, access, or approvals outside the learner's direct control (e.g., paid services, cloud accounts, etc.)

## OUTPUT
Return a single valid JSON object with this exact structure:
{
    "status": "fail" OR "pass", 
    "gaps": ["gap 1", "gap 2"] or []
}

CRITICAL: Output ONLY the JSON object. No preamble, no markdown code fences, no explanation outside the JSON.

"""
        user_prompt = f"""## INPUTS
**Baseline:** {user_context}

**Objective:** {user_goal}

**Curriculum:**
{curriculum_summary}"""

        try:
            response = self.client.chat.completions.create(
                model="meta-llama/llama-4-maverick-17b-128e-instruct",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.0,
                max_completion_tokens=8000,
                top_p=1,
                stream=False,
                #reasoning_effort="high"
            )

            content = response.choices[0].message.content
            self._log_token_usage(response, "Curriculum Validation")

            validation_result = self._extract_json(content)
            return validation_result

        except Exception as e:
            print(f"\n⚠️  Validation failed: {e}")
            print(f"   Continuing without validation...\n")
            return {"status": "error", "gaps": [], "error": str(e)}

    def generate(self, user_context: str, user_goal: str):
        """
        Generate learning path based on user baseline and objective.
        Two-step process: path generation, then validation.

        Args:
            user_context: The user's current baseline (expertise, experience, knowledge)
            user_goal: The practical objective the user wants to achieve

        Returns:
            Dictionary with 'learning_path' (dict) and 'validation' (dict)
        """
        print(f"\n{'='*80}")
        print(f"LEARNING PATH AGENT")
        print(f"{'='*80}")
        print(f"Baseline: {user_context}")
        print(f"Objective: {user_goal}\n")

        # Step 1: Generate learning path
        print(f"🤖 Generating learning path with high reasoning...\n")

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

### 3. Pedagogical Scaffolding
- Sequence modules so each one enables the next
- Build mental models progressively—connect new concepts to prior ones
- Continuously reinforce how each piece fits the overall goal

### 4. Pragmatic Scope
- Design for busy professionals and students who need to learn and apply efficiently
- Modules should be substantial enough to build real competency, but focused enough to complete
- Total curriculum: minimum 2 modules, maximum 8 modules

### 5. Professional Integrity & Validity
- **No "Toy" Solutions**: Do not simplify concepts to the point of creating "bad habits" or technical/professional debt. The solution must be viable in a real-world professional context (e.g., do not teach deploying a database without persistence to an engineer; do not teach "buying followers" to a marketer).

## OUTPUT FORMAT
Return a single valid JSON object with this exact structure:

{
  "pedagogical_strategy": "Brief analysis of: (1) the key gaps identified, (2) the sequencing logic, and (3) any baseline strengths you're leveraging.",
  "curriculum": [
    {
      "module_order": 1,
      "title": "Concise, descriptive module title",
      "competency_goal": "What the learner will understand and be able to do after completing this module.",
      "mental_map": "The core concepts, frameworks, or theory covered. Explain what the learner needs to internalize.",
      "application": "Specific hands-on exercises, projects, or practice activities that apply the concepts to real scenarios aligned with the objective.",
      "relevance_to_goal": "Explicitly state WHY this module is necessary and HOW it connects to achieving the user's objective."
    }
  ]
}

## RULES
- Output ONLY the JSON object. No preamble, no markdown code fences, no explanation outside the JSON.
- Every module must have a clear, non-redundant purpose.
- Do not pad the curriculum—if 3 modules suffice, use 3.
- Write for clarity and actionability. Avoid vague descriptions."""

        user_prompt = f"""<user_input>
User Baseline: {user_context}
User Objective: {user_goal}
</user_input>"""

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.0,
                max_completion_tokens=8000,
                top_p=1,
                stream=False,
                stop=None,
                reasoning_effort="high"
            )

            content = response.choices[0].message.content
            self._log_token_usage(response, "Learning Path Generation")

            learning_path = self._extract_json(content)

            # Step 2: Validate curriculum
            validation_result = self._validate_curriculum(user_context, user_goal, learning_path)

            # Return learning path and validation
            return {
                "learning_path": learning_path,
                "validation": validation_result
            }

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


def print_learning_path(path: dict, validation: dict = None):
    """Pretty print learning path with optional validation results."""
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

    print(f"\n{'='*80}")

    # Print validation results if available
    if validation:
        print(f"QUALITY VALIDATION")
        print(f"{'='*80}\n")

        status = validation.get('status', 'unknown')
        gaps = validation.get('gaps', [])

        if status == 'pass':
            print(f"✅ VALIDATION PASSED")
            print(f"   The curriculum is complete and ready to use.\n")
        elif status == 'fail':
            print(f"⚠️  VALIDATION FAILED")
            print(f"   {len(gaps)} gap(s) identified:\n")
            for i, gap in enumerate(gaps, 1):
                print(f"   {i}. {gap}")
            print()
        elif status == 'error':
            print(f"❌ VALIDATION ERROR")
            print(f"   {validation.get('error', 'Unknown error')}\n")
        else:
            print(f"❓ VALIDATION STATUS: {status}\n")

        print(f"{'='*80}\n")
    else:
        print(f"\n")


def main():
    """Main function with test inputs."""
    print("\n" + "="*80)
    print("LEARNING PATH GENERATOR (CLAUDE)")
    print("="*80)
    print("\nDesign your personalized learning pathway!\n")
    print("This agent will create a curriculum that bridges the gap between")
    print("where you are now and where you want to be.\n")

    # Test inputs
    user_context = "I am a Senior Backend Developer (Node.js/Go) comfortable with Linux command line. I use Docker daily: I can write multi-stage Dockerfiles, optimize image sizes, and use docker-compose for local development. However, I have zero experience with orchestration. Concepts like 'Pods,' 'Ingress,' or 'Helm charts' are abstract to me. I understand basic networking (ports, DNS) but find Kubernetes manifests verbose and confusing."

    user_goal = "My company is migrating our monolithic app to microservices on a cloud provider. My specific goal is to take three of our existing dockerized microservices (Frontend, API, Database) and deploy them into a live Kubernetes cluster. I need to be able to configure them so they can communicate securely (Service Discovery/Secrets), expose the frontend to the public internet (Ingress), and perform a 'Rolling Update' without downtime. I need to be able to debug if a Pod gets stuck in CrashLoopBackOff."

    print("📝 Using test inputs:")
    print(f"\nBaseline: {user_context[:100]}...")
    print(f"\nObjective: {user_goal[:100]}...\n")

    print(f"\n📋 Two-step process:")
    print(f"   1. Learning Path Design: Groq GPT OSS 120B (reasoning: high)")
    print(f"   2. Quality Validation: Llama 3.3 70B Versatile")

    try:
        agent = LearningPathAgent()
        result = agent.generate(user_context, user_goal)

        # Extract components
        learning_path = result.get("learning_path", {})
        validation = result.get("validation", {})

        print_learning_path(learning_path, validation)

        # Save to file
        output_file = f"Claude_LP.json"

        with open(output_file, "w") as f:
            json.dump({
                "input": {
                    "user_baseline": user_context,
                    "user_objective": user_goal
                },
                "learning_path": learning_path,
                "validation": validation
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
        print("  GROQ_API_KEY=your_key")
        exit(1)

    main()
