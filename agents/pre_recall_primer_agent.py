"""
Pre-Recall Primer Agent - Cognitive Activation Before Learning

Generates a brief, engaging primer before each lesson to:
1. Activate prior knowledge and intuitive thinking
2. Create curiosity and motivation
3. Explain the concept of Active Recall
4. Provide context for downstream agents

Uses llama-3.3-70b-versatile for pedagogically sound activation prompts.
"""

import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# LLM Configuration
PRE_RECALL_LLM_CONFIG = ("groq", "meta-llama/llama-4-maverick-17b-128e-instruct")


class PreRecallPrimerAgent:
    """Generates cognitive activation primers before lessons."""

    def __init__(self):
        """Initialize the agent with configured Groq client."""
        self.provider = PRE_RECALL_LLM_CONFIG[0]
        self.model_name = PRE_RECALL_LLM_CONFIG[1]
        self.client = self._setup_llm()
        self.total_tokens = 0

    def _setup_llm(self):
        """Setup Groq client."""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in .env")
        return Groq(api_key=api_key)

    def _log_token_usage(self, response, call_type: str):
        """Log token usage from Groq response and accumulate total."""
        try:
            if hasattr(response, 'usage'):
                usage = response.usage
                input_tokens = usage.prompt_tokens
                output_tokens = usage.completion_tokens
                total_tokens = usage.total_tokens

                if total_tokens > 0:
                    print(f"  📊 [{call_type}] {self.model_name}: {total_tokens:,} tokens (in: {input_tokens:,}, out: {output_tokens:,})")
                    self.total_tokens += total_tokens
        except Exception:
            pass

    def run(self, lesson_title: str, topics_covered: list, experience_level: str, learning_objectives: list) -> dict:
        """
        Generate a pre-recall primer for a lesson.
        
        Args:
            lesson_title: Title of the upcoming lesson
            topics_covered: List of topics that will be covered
            experience_level: User's experience level (Beginner/Intermediate/Advanced)
            learning_objectives: Specific learning objectives for the lesson
            
        Returns:
            Dictionary with primer text and metadata
            Note: User's ANSWERS to the primer questions should be captured and passed to Tutor Agent
        """
        print(f"\n{'='*80}")
        print(f"PRE-RECALL PRIMER AGENT - {self.provider.upper()}")
        print(f"{'='*80}")
        print(f"Lesson: {lesson_title}")
        print(f"Level: {experience_level}\n")

        print(f"  🧠 Generating cognitive activation primer...\n")

        system_prompt = """You are the Pre-Recall Primer Agent, a learning science expert specializing in cognitive activation and diagnostic assessment.

Your purpose:
Generate a short, engaging diagnostic assessment that activates prior knowledge, triggers thinking, and reveals the learner's actual level.

=====================================================
PRIMER FUNCTION
=====================================================
This is a MICRO cognitive diagnostic that:
1. Activates prior knowledge through engaging questions
2. Demonstrates the value of the lesson content
3. Calibrates the learner's confidence level
4. Triggers curiosity and critical thinking

The entire primer must take the learner **20–30 seconds** to complete.

=====================================================
WHAT TO GENERATE
=====================================================
Produce ONLY the following elements:

1. **Three Diagnostic Multiple-Choice Questions (CRITICAL STRUCTURE)**

   **Question 1 - Intuitive Paradox (The "Mental Model"):**
   - Challenge the user to identify the *necessity* or *purpose* of the concept.
   - Focus on the "Why" behind the "What".
   - Correct answer = the logical reason for its existence.

   **Question 2 - Logical Dilemma:**
   - Present a scenario that requires a logical choice, not just tool knowledge.
   - The answer should be the only sensible move based on the context.

   **Question 3 - Hidden Consequence (The "Why"):**
   - Test the ability to connect cause and effect.
   - Reveal a relationship or trade-off that isn't immediately obvious.

   **General Question Guidelines:**
   - **Simple but Deep:** Use plain language, but demand reasoning. No "trivia".
   - **Domain Agnostic:** Adapt tone and style to the subject.
   - **Anti-Guessing:** Wrong answers must sound plausible to a layperson.

2. **Confidence Slider Prompt**
   - A simple question asking about their confidence level regarding the specific topic.

3. **Curiosity Hook (1 sentence)**
   - Create a magnetic "Open Loop" that teases a hidden connection or counter-intuitive truth.
   - **Assume the user is new:** Use accessible language; avoid jargon.
   - **Focus on the Power/Why:** Highlight the superpower or critical insight this topic unlocks.
   - Make the user feel they *must* take the lesson to find the answer.
   - Dont phrase it as a question. Must be a statement.

=====================================================
OUTPUT FORMAT (STRICT JSON)
=====================================================
{
  "mcq_questions": [
    {
      "question": "Question 1 text",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer_index": 0
    },
    {
      "question": "Question 2 text",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer_index": 1
    },
    {
      "question": "Question 3 text",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer_index": 2
    }
  ],
  "confidence_prompt": "How confident do you feel about [Topic] right now?",
  "curiosity_hook": "1 sentence hook"
}

Output ONLY valid JSON. No prose before or after."""

        user_prompt = f"""Create a Pre-Recall Primer for this lesson:

Lesson Title: {lesson_title}
Topics Covered: {json.dumps(topics_covered)}
Experience Level: {experience_level}
Learning Objectives: {json.dumps(learning_objectives)}

Generate the engaging diagnostic primer now."""

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.4,  # Slightly higher for more engaging questions
                max_completion_tokens=2000,
                top_p=1,
                stream=False,
                stop=None
            )

            content = response.choices[0].message.content
            self._log_token_usage(response, "Pre-Recall Primer Generation")

            primer_data = self._extract_json(content)

            return primer_data

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
            raise ValueError(f"No closing '```' found for JSON block: {text[:200]}...")

        json_str = text[start_idx + len(start_marker) : end_idx].strip()

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            print(f"Response around error: {json_str[max(0, e.pos-100):min(len(json_str), e.pos+100)]}")
            raise ValueError(f"Invalid JSON in code block: {str(e)}")


def print_primer(primer_data: dict, challenge_title: str):
    """Pretty-print primer data to terminal."""
    print(f"\n{'='*80}")
    print(f"PRIMER FOR: {challenge_title}")
    print(f"{'='*80}\n")
    print("❓ MCQ Questions:")
    for i, mcq in enumerate(primer_data['mcq_questions'], 1):
        print(f"\n  {i}. {mcq['question']}")
        for j, opt in enumerate(mcq['options']):
            marker = "✓" if j == mcq.get('correct_answer_index', -1) else " "
            print(f"     {chr(65+j)}. {opt} {'[CORRECT]' if marker == '✓' else ''}")
    print(f"\n🎚️  Confidence: {primer_data['confidence_prompt']}")
    print(f"\n✨ Hook: {primer_data['curiosity_hook']}")


def get_available_lesson_plans():
    """Find all lesson plan files in current directory."""
    import glob
    files = glob.glob("LessonPlan_M*.json")
    return sorted(files)


def main():
    """Test the Pre-Recall Primer Agent using outputs from module_planner_agent.py."""
    import glob
    
    print("\n" + "="*80)
    print("PRE-RECALL PRIMER AGENT - LOCAL TEST")
    print("="*80)
    
    # Find available lesson plan files
    lesson_plans = get_available_lesson_plans()
    
    if not lesson_plans:
        print("\n❌ No lesson plan files found.")
        print("   Run module_planner_agent.py first to generate lesson plans.")
        print("   Expected files: LessonPlan_M1.json, LessonPlan_M2.json, etc.")
        return
    
    print(f"\n📚 Found {len(lesson_plans)} lesson plan file(s):")
    for i, lp in enumerate(lesson_plans, 1):
        print(f"  {i}. {lp}")
    
    # Let user choose module
    print("\nSelect a lesson plan:")
    for i, lp in enumerate(lesson_plans, 1):
        print(f"  {i}. {lp}")
    
    module_choice = input("\nYour choice: ").strip()
    
    try:
        idx = int(module_choice) - 1
        if not (0 <= idx < len(lesson_plans)):
            print("❌ Invalid choice")
            return
        lesson_file = lesson_plans[idx]
    except ValueError:
        print("❌ Invalid input")
        return
    
    # Load the selected lesson plan
    try:
        with open(lesson_file, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading {lesson_file}: {e}")
        return
    
    # Extract metadata
    metadata = data.get('metadata', {})
    lesson_plan = data.get('lesson_plan', data)  # Handle both formats
    
    learning_goal = metadata.get('learning_goal', 'Unknown goal')
    experience_level = metadata.get('experience_level', 'Intermediate')
    module_number = metadata.get('module_number', '?')
    
    print(f"\n{'='*80}")
    print(f"MODULE: {lesson_plan.get('module_title', 'Unknown')}")
    print(f"{'='*80}")
    print(f"📘 Module {module_number}")
    print(f"🎯 Goal: {learning_goal}")
    print(f"📊 Level: {experience_level}")
    
    # Show available challenges
    lessons = lesson_plan.get('lessons', [])
    print(f"\n📋 Available Challenges ({len(lessons)}):")
    for i, lesson in enumerate(lessons, 1):
        print(f"  {i}. {lesson.get('title', 'Unknown Challenge')}")
    
    # Let user choose challenge
    challenge_choice = input("\nSelect a challenge (or 'A' for all): ").strip().upper()
    
    # Determine which challenges to process
    if challenge_choice == 'A':
        challenges_to_process = list(enumerate(lessons))
    else:
        try:
            idx = int(challenge_choice) - 1
            if not (0 <= idx < len(lessons)):
                print("❌ Invalid choice")
                return
            challenges_to_process = [(idx, lessons[idx])]
        except ValueError:
            print("❌ Invalid input")
            return
    
    agent = PreRecallPrimerAgent()
    all_primers = []
    
    # Process selected challenge(s)
    for idx, lesson in challenges_to_process:
        challenge_number = lesson.get('lesson_number', idx + 1)
        challenge_title = lesson.get('title', 'Unknown Challenge')
        topics = lesson.get('topics_covered', [])
        learning_objectives = lesson.get('learning_objectives', [])
        
        print(f"\n{'='*80}")
        print(f"GENERATING PRIMER FOR CHALLENGE {challenge_number}")
        print(f"{'='*80}")
        
        # Generate primer
        primer = agent.run(
            lesson_title=challenge_title,
            topics_covered=topics,
            experience_level=experience_level,
            learning_objectives=learning_objectives
        )
        
        # Display primer
        print_primer(primer, challenge_title)
        
        # Store for saving
        all_primers.append({
            'challenge_number': challenge_number,
            'challenge_title': challenge_title,
            'topics_covered': topics,
            'learning_objectives': learning_objectives,
            'primer': primer
        })
    
    # Save primers to file
    if challenge_choice == 'A':
        output_file = lesson_file.replace('LessonPlan', 'Primers')
        output_data = {
            'metadata': metadata,
            'module_title': lesson_plan.get('module_title'),
            'primers': all_primers
        }
    else:
        # Save single primer with challenge number
        output_file = lesson_file.replace('LessonPlan', f'Primer_M{module_number}_C{challenge_number}')
        output_data = all_primers[0] if all_primers else {}
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n\n✅ Saved primer(s) to: {output_file}")
    
    print(f"\n{'='*80}")
    print(f"TOTAL TOKEN USAGE: {agent.total_tokens:,} tokens")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()

