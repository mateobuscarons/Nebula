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
        self.model_name = "gemini-3-flash-preview"
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

        system_prompt = """You are an expert instructional designer. Generate a learning journey that bridges the gap between a learner's baseline and their objective.

## INPUTS
1. **User's Baseline**: Current knowledge, skills, and experience.
2. **User's Objective**: The specific outcome they want to achieve.

## YOUR TASK
Create a lean curriculum of **Minimum Viable Knowledge (MVK)**—only what's essential to achieve the objective.

## DESIGN PRINCIPLES

1. **Gap-Focused**: Only include what closes the baseline→objective gap. Exclude what they already know.
2. **Narrative Flow**: Design chapters like episodes in a series—each one ends with a cliffhanger that the next chapter resolves. The learner should feel momentum, not isolated modules.
3. **Progressive**: Each chapter builds on the previous. The artifact/skill from Chapter N becomes the foundation for Chapter N+1.
4. **Outcome-Oriented**: Focus on what user CAN DO after each chapter, not abstract knowledge.
5. **Lean**: 2-8 chapters. Prefer fewer, deeper chapters over many shallow ones.

## STRICT EXCLUSION
Only include a chapter if the learner CANNOT achieve the objective without it. Exclude:
- Best practices (unless essential for basic functionality)
- Scope creep beyond the stated objective
- Topics requiring external resources outside learner's control
- Historical context or "why it was created" unless directly relevant

## OUTPUT FORMAT
Return a single valid JSON object:

{
  "journey": {
    "title": "Transformation arc (e.g., 'From X to Y' or 'Becoming a Z')",
    "destination": "One sentence: what they'll be able to do/create/understand at the end"
  },
  "chapters": [
    {
      "chapter": 1,
      "title": "Achievement-focused title (what you'll accomplish)",
      "outcome": "The concrete capability gained—what you can now build, do, or solve. Vary phrasing naturally.",
      "unlocks": "The natural next question or limitation this creates—the hook into the next chapter (null for final)",
      "concepts": ["Core concept with brief context", "Another essential concept"],
      "practice": ["Specific hands-on task with clear deliverable", "Another practical exercise"]
    }
  ]
}

## WRITING STYLE
- Write directly to user (second person: "you", not "the learner")
- Vary sentence structure and vocabulary—avoid repetitive patterns across chapters
- Use action verbs: build, create, configure, deploy, debug, integrate, etc.
- Be specific: name technologies, patterns, or artifacts the learner will work with
- Outcomes should feel like achievements, not checkboxes

## RULES
- Output ONLY JSON. No markdown fences, no explanation.
- Every chapter must have clear, non-redundant purpose.
- Concepts: 2-4 essential ideas per chapter (quality over quantity)
- Practice: 1-3 concrete activities that produce tangible results"""

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

            # Return token usage for logging
            token_usage = None
            if usage_metadata:
                token_usage = {
                    "prompt_tokens": usage_metadata.prompt_token_count,
                    "completion_tokens": usage_metadata.candidates_token_count,
                    "total_tokens": usage_metadata.total_token_count,
                    "model_name": self.model_name
                }

            return {
                "learning_path": learning_path,
                "token_usage": token_usage
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

        system_prompt = """You are a curriculum refinement specialist. ADJUST the learning path based on user feedback.

## RULES
1. The original path is HIGH QUALITY—make MINIMAL changes
2. Only adjust what the feedback specifically requests
3. Preserve the narrative flow and chapter dependencies
4. Do NOT add/remove chapters unless explicitly requested

## OUTPUT FORMAT
Return ONLY valid JSON:

{
  "journey": {
    "title": "Transformation arc",
    "destination": "What they'll be able to do at the end"
  },
  "chapters": [
    {
      "chapter": 1,
      "title": "Achievement-focused title",
      "outcome": "Concrete capability gained—vary phrasing naturally across chapters",
      "unlocks": "The hook into the next chapter—what question or limitation this creates (null for final)",
      "concepts": ["Core concept", "Another concept"],
      "practice": ["Hands-on task with deliverable", "Another exercise"]
    }
  ]
}

## WRITING STYLE
- Write directly to user (second person: "you")
- Vary sentence structure—avoid repetitive patterns
- Outcomes should feel like achievements, not checkboxes

## RULES
- Output ONLY JSON. No markdown fences, no explanation.
- Maintain sequential chapter ordering (1, 2, 3, ...)"""

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

            print(f"✅ Learning path adjusted: {len(adjusted_path.get('chapters', []))} chapters\n")

            # Return token usage for logging
            token_usage = None
            if hasattr(response, 'usage'):
                usage = response.usage
                token_usage = {
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens,
                    "model_name": "llama-3.3-70b-versatile"
                }

            return {
                "learning_path": adjusted_path,
                "token_usage": token_usage
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
    print(f"LEARNING JOURNEY")
    print(f"{'='*80}\n")

    journey = path.get('journey', {})
    print(f"🎯 {journey.get('title', 'N/A')}")
    print(f"   {journey.get('destination', 'N/A')}\n")

    print(f"{'─'*80}")
    print(f"CHAPTERS ({len(path.get('chapters', []))} total):")
    print(f"{'─'*80}")

    for chapter in path.get('chapters', []):
        print(f"\n[Chapter {chapter['chapter']}] {chapter['title']}")
        print(f"  ✓ Outcome: {chapter['outcome']}")
        print(f"  🧠 Concepts: {chapter.get('concepts', [])}")
        print(f"  🔧 Practice: {chapter.get('practice', [])}")
        print(f"  → Unlocks: {chapter.get('unlocks', 'N/A')}")

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
