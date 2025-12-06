"""Evaluator Agent - Assesses user understanding and provides guidance."""

import logging
from typing import Dict, Any, List
from dataclasses import dataclass

from core import SessionState, TeachingNode, Message, llm_client
from config import model_config, system_config


logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """Result from the Evaluator Agent."""
    user_intent: str  # "attempt_answer" | "ask_question" | "stuck"
    evaluation: str   # "correct" | "partial" | "wrong" | "n/a"
    reasoning: str
    guidance_for_tutor: str
    should_advance: bool

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'EvaluationResult':
        return EvaluationResult(
            user_intent=data["user_intent"],
            evaluation=data["evaluation"],
            reasoning=data["reasoning"],
            guidance_for_tutor=data["guidance_for_tutor"],
            should_advance=data["should_advance"]
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_intent": self.user_intent,
            "evaluation": self.evaluation,
            "reasoning": self.reasoning,
            "guidance_for_tutor": self.guidance_for_tutor,
            "should_advance": self.should_advance
        }


class EvaluatorAgent:
    """
    The Diagnostician: Assesses user input to determine intent and understanding.
    Uses deterministic temperature for consistent evaluation.
    """

    def __init__(self):
        self.temperature = model_config.evaluator_temp  # 0.1 - deterministic
        self.history_window = system_config.evaluator_history_window  # Last 2 turns
        logger.info("EvaluatorAgent initialized (deterministic mode)")

    def evaluate(
        self,
        state: SessionState,
        user_message: str,
        tutor_previous_content: str
    ) -> EvaluationResult:
        """
        Evaluate user's response to determine understanding and next steps.

        Args:
            state: Current session state
            user_message: The user's latest message
            tutor_previous_content: What the tutor previously asked/taught

        Returns:
            EvaluationResult with guidance for the tutor
        """
        current_node = state.get_current_node()
        logger.info(f"Evaluating user response for node: {current_node.concept}")
        logger.debug(f"User message: {user_message[:100]}...")

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(
            user_message=user_message,
            current_node=current_node,
            tutor_previous=tutor_previous_content,
            recent_history=state.get_recent_history(self.history_window)
        )

        try:
            response = llm_client.call_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=self.temperature
            )

            result = EvaluationResult.from_dict(response)

            logger.info(f"Evaluation: intent={result.user_intent}, "
                       f"eval={result.evaluation}, advance={result.should_advance}")
            logger.debug(f"Guidance: {result.guidance_for_tutor[:100]}...")

            return result

        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            raise

    def _build_system_prompt(self) -> str:
        """Build the system prompt for evaluation."""
        return """You are an Evaluator Agent, a diagnostic expert in learning assessment.

Your role is to assess user responses and provide strategic guidance to the tutor.

CORE PRINCIPLES:
1. Determine user INTENT (answering, asking, stuck)
2. Evaluate UNDERSTANDING (correct, partial, wrong, n/a)
3. Be GENEROUS and LENIENT - basic understanding is enough
4. Provide SPECIFIC guidance (what the tutor should do next)
5. Decide if user should ADVANCE (ready for next concept)

GENEROSITY MANDATE:
- You are TOO STRICT if you expect perfect answers
- Basic grasp of the main idea = ADVANCE
- Small gaps = Tutor should praise, briefly clarify, then ADVANCE
- Only remediate if fundamentally confused or wrong

EVALUATION CRITERIA - BE GENEROUS:
- Primary question: "Did they grasp the BASIC idea of the core concept?"
- Look for BASIC UNDERSTANDING, not excellence or perfect wording
- If they show minimal comprehension, that's often enough to advance
- Don't expect mastery - basic grasp is sufficient
- Partial understanding is valuable and often enough to move forward

GUIDANCE SHOULD BE:
- Strategic: Tell tutor HOW to respond
- Specific: Point to exact gaps or strengths
- Actionable: Clear next steps (praise, address gap, advance, etc.)
- For minimal gaps: Suggest tutor PRAISE the answer, briefly ADDRESS the small gap, then ADVANCE

ADVANCING CRITERIA - BE LENIENT:
- User shows BASIC understanding of core concept (even if incomplete)
- Demonstrates they got the main idea, even if details are fuzzy
- Small gaps or incomplete answers should still result in advancement
- Only stay on node if user is truly confused or misunderstands fundamentally
- When in doubt, ADVANCE with guidance to address small gaps

Return ONLY valid JSON in this exact format:
{
  "user_intent": "attempt_answer|ask_question|stuck",
  "evaluation": "correct|partial|wrong|n/a",
  "reasoning": "Detailed analysis of user's understanding",
  "guidance_for_tutor": "Strategic direction for tutor's next response",
  "should_advance": true|false
}"""

    def _build_user_prompt(
        self,
        user_message: str,
        current_node: TeachingNode,
        tutor_previous: str,
        recent_history: List[Message]
    ) -> str:
        """Build the user prompt with context."""
        # Format recent history
        history_text = ""
        if recent_history:
            history_text = "RECENT CONVERSATION:\n"
            for msg in recent_history:
                history_text += f"{msg.role.value.upper()}: {msg.content}\n"

        return f"""Evaluate this user response:

CURRENT TEACHING NODE:
Concept: {current_node.concept}
Goal: {current_node.goal}

TUTOR'S PREVIOUS MESSAGE:
{tutor_previous}

{history_text}

USER'S RESPONSE:
{user_message}

Assess the user's intent, understanding, and readiness to advance.
Provide specific guidance for the tutor's next move.

Return ONLY the JSON object, nothing else."""

    def __str__(self) -> str:
        return f"EvaluatorAgent(temp={self.temperature}, window={self.history_window})"
