"""Pedagogical Reviewer Agent - Quality control for teaching outputs."""

import logging
from typing import Dict, Any
from dataclasses import dataclass

from core import TeachingNode, llm_client
from config import model_config


logger = logging.getLogger(__name__)


@dataclass
class ReviewResult:
    """Result from the Pedagogical Reviewer."""
    approved: bool
    feedback: str

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'ReviewResult':
        return ReviewResult(
            approved=data["approved"],
            feedback=data.get("feedback", "")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "approved": self.approved,
            "feedback": self.feedback
        }


class PedagogicalReviewerAgent:
    """
    The Quality Control: Ensures teaching quality and adherence to
    learning principles.
    """

    # The 7 Learning Principles
    LEARNING_PRINCIPLES = [
        "Active Learning (Generation Effect)",
        "Cognitive Load Management (One concept per turn)",
        "Adaptive Scaffolding & Fading (ZPD)",
        "Misconception Diagnosis - Treat errors as signals",
        "Curiosity & Relevance - Connect to concrete problems",
        "Emotional Awareness - Acknowledge and support",
        "Interleaving & Transfer - Build transferable skills"
    ]

    def __init__(self):
        self.temperature = model_config.reviewer_temp  # 0.3
        logger.info("PedagogicalReviewerAgent initialized")

    def review(
        self,
        tutor_output: Dict[str, str],
        current_node: TeachingNode
    ) -> ReviewResult:
        """
        Review tutor's output against learning principles.

        Args:
            tutor_output: The tutor's proposed teaching and question
            current_node: The current teaching node context

        Returns:
            ReviewResult indicating approval and feedback
        """
        logger.info(f"Reviewing tutor output for: {current_node.concept}")
        logger.debug(f"Teaching: {tutor_output['teaching'][:100]}...")
        logger.debug(f"Question: {tutor_output['question'][:100]}...")

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(tutor_output, current_node)

        try:
            response = llm_client.call_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=self.temperature
            )

            result = ReviewResult.from_dict(response)

            logger.info(f"Review result: approved={result.approved}")
            if not result.approved:
                logger.debug(f"Feedback: {result.feedback}")

            return result

        except Exception as e:
            logger.error(f"Review failed: {e}")
            raise

    def _build_system_prompt(self) -> str:
        """Build the system prompt for reviewing."""
        principles_text = "\n".join(f"{i}. {p}" for i, p in enumerate(self.LEARNING_PRINCIPLES, 1))

        return f"""You are a Pedagogical Reviewer Agent, an expert in learning science.

Your role is to ensure teaching quality and adherence to learning principles.

THE 7 LEARNING PRINCIPLES:
{principles_text}

YOUR EVALUATION CRITERIA:
1. Does the teaching promote ACTIVE LEARNING?
   - Encourages generation, not just recognition
   - Asks for thinking, not just recall

2. Is COGNITIVE LOAD managed?
   - Focuses on ONE concept at a time
   - Avoids overwhelming with too much information

3. Is there ADAPTIVE SCAFFOLDING?
   - Appropriate challenge level (Zone of Proximal Development)
   - Not too easy, not too hard

4. Does it treat MISCONCEPTIONS well?
   - If addressing an error, does it diagnose thoughtfully?
   - Treats errors as learning opportunities

5. Does it spark CURIOSITY?
   - Connects abstract concepts to concrete problems
   - Uses relevant examples or scenarios

6. Is there EMOTIONAL AWARENESS?
   - Supportive and encouraging tone
   - Acknowledges struggle when appropriate

7. Does it support TRANSFER?
   - Builds skills that apply beyond this specific case
   - Connects related concepts when relevant

APPROVAL CRITERIA:
- APPROVE if the output meets most principles well
- REJECT if there are significant issues with clarity, cognitive load, or engagement

When rejecting, provide SPECIFIC, ACTIONABLE feedback:
- Point to exact issues
- Suggest concrete improvements
- Focus on the most important fixes

Return ONLY valid JSON in this exact format:
{{
  "approved": true|false,
  "feedback": "Specific feedback if rejected, empty string if approved"
}}"""

    def _build_user_prompt(
        self,
        tutor_output: Dict[str, str],
        current_node: TeachingNode
    ) -> str:
        """Build the user prompt for review."""
        return f"""Review this teaching output against the 7 Learning Principles:

TEACHING NODE:
Concept: {current_node.concept}
Goal: {current_node.goal}

TUTOR'S OUTPUT:

TEACHING:
{tutor_output['teaching']}

QUESTION:
{tutor_output['question']}

Evaluate whether this output:
1. Promotes active learning
2. Manages cognitive load
3. Provides appropriate scaffolding (ZPD)
4. Handles misconceptions well (if applicable)
5. Sparks curiosity and relevance
6. Shows emotional awareness
7. Supports transfer

Approve or reject with specific, actionable feedback.

Return ONLY the JSON object, nothing else."""

    def __str__(self) -> str:
        return f"PedagogicalReviewerAgent(temp={self.temperature})"
