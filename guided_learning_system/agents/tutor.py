"""Tutor Agent - Delivers teaching content and generates active recall questions."""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from core import SessionState, TeachingNode, Message, llm_client
from config import model_config, system_config


logger = logging.getLogger(__name__)


@dataclass
class TutorOutput:
    """Output from the Tutor Agent."""
    teaching: str
    question: str

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'TutorOutput':
        return TutorOutput(
            teaching=data["teaching"],
            question=data["question"]
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "teaching": self.teaching,
            "question": self.question
        }

    def format_for_display(self) -> str:
        """Format the output for CLI display."""
        return f"{self.teaching}\n\n{self.question}"


class TutorAgent:
    """
    The Guide: Delivers focused teaching segments and generates responses
    based on Evaluator guidance.
    """

    def __init__(self):
        self.temperature = model_config.tutor_temp  # 0.5 - creative
        self.history_window = system_config.tutor_history_window  # Last 6 turns
        logger.info("TutorAgent initialized (creative mode)")

    def teach_node(
        self,
        state: SessionState,
        strategy_directive: Optional[str] = None,
        pedagogical_feedback: Optional[str] = None
    ) -> TutorOutput:
        """
        Generate teaching content for the current node.

        Args:
            state: Current session state
            strategy_directive: Guidance from Evaluator (None for first iteration)
            pedagogical_feedback: Feedback from Reviewer (if retrying)

        Returns:
            TutorOutput with teaching explanation and question
        """
        current_node = state.get_current_node()
        logger.info(f"Teaching node: {current_node.concept}")

        if strategy_directive:
            logger.debug(f"Strategy directive: {strategy_directive[:100]}...")
        if pedagogical_feedback:
            logger.debug(f"Pedagogical feedback: {pedagogical_feedback[:100]}...")

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(
            current_node=current_node,
            lesson_context=state.lesson_context,
            strategy_directive=strategy_directive,
            pedagogical_feedback=pedagogical_feedback,
            recent_history=state.get_recent_history(self.history_window)
        )

        try:
            response = llm_client.call_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=self.temperature
            )

            output = TutorOutput.from_dict(response)

            logger.info("Tutor output generated successfully")
            logger.debug(f"Teaching: {output.teaching[:100]}...")
            logger.debug(f"Question: {output.question[:100]}...")

            return output

        except Exception as e:
            logger.error(f"Tutor generation failed: {e}")
            raise

    def _build_system_prompt(self) -> str:
        """Build the system prompt for teaching."""
        return """You are a Tutor Agent, an expert educator and guide.

Your role is to deliver focused, engaging teaching segments with active recall questions.

CORE PRINCIPLES:
1. CLARITY: Explain concepts clearly and concisely
2. BRIDGING: Connect to previous concepts when possible
3. ENGAGEMENT: Make learning interactive and relevant
4. ACTIVE RECALL: Ask questions that require thinking, not just remembering
5. APPROPRIATE CHALLENGE: Stay in the zone of proximal development

TEACHING APPROACH:
- Start with the big picture, then dive into details
- Use analogies, examples, and scenarios
- Keep explanations focused on the current concept
- Build on what the learner already knows
- Adjust difficulty based on learner's responses

QUESTION TYPES (vary these):
- Scenario-based: "If X happens, what would Y do?"
- Prediction: "What do you think will happen when...?"
- Contrast: "How is A different from B?"
- Cause-effect: "Why does X lead to Y?"
- Application: "How would you use X to solve Y?"

CHAIN-OF-THOUGHT PROCESS:
Before generating your final output, think through:
1. What's the core concept to teach?
2. How does it connect to what they've learned?
3. What's an engaging way to present this?
4. What question will deepen understanding?

Use STRATEGY DIRECTIVE if provided (from evaluator's guidance).
Use PEDAGOGICAL FEEDBACK if provided (from reviewer's suggestions).

Return ONLY valid JSON in this exact format:
{
  "teaching": "Clear explanation with bridge from previous concepts...",
  "question": "Engaging question leveraging active recall that tests understanding of the concept..."
}"""

    def _build_user_prompt(
        self,
        current_node: TeachingNode,
        lesson_context,
        strategy_directive: Optional[str],
        pedagogical_feedback: Optional[str],
        recent_history: List[Message]
    ) -> str:
        """Build the user prompt with full context."""
        # Format recent history
        history_text = ""
        if recent_history:
            history_text = "CONVERSATION HISTORY:\n"
            for msg in recent_history:
                history_text += f"{msg.role.value.upper()}: {msg.content}\n"
            history_text += "\n"

        # Strategy directive section
        strategy_text = ""
        if strategy_directive:
            strategy_text = f"""EVALUATOR GUIDANCE:
{strategy_directive}

Follow this guidance in your response.

"""

        # Pedagogical feedback section
        feedback_text = ""
        if pedagogical_feedback:
            feedback_text = f"""REVIEWER FEEDBACK:
{pedagogical_feedback}

Revise your output based on this feedback.

"""

        return f"""Generate teaching content for this learning node:

LESSON CONTEXT:
Title: {lesson_context.title}
Objectives: {', '.join(lesson_context.objectives)}

CURRENT NODE TO TEACH:
Concept: {current_node.concept}
Goal: {current_node.goal}

{history_text}{strategy_text}{feedback_text}Create an engaging teaching segment with an active recall question.
Make it conversational, clear, and appropriately challenging.

Return ONLY the JSON object, nothing else."""

    def __str__(self) -> str:
        return f"TutorAgent(temp={self.temperature}, window={self.history_window})"
