"""Orchestration Engine - The central state machine managing the teaching loop."""

import logging
from typing import Optional, List

from core import SessionState, MessageRole
from agents import (
    PathGeneratorAgent,
    EvaluatorAgent,
    TutorAgent,
    PedagogicalReviewerAgent,
    TutorOutput,
    EvaluationResult
)
from config import system_config


logger = logging.getLogger(__name__)


class OrchestrationEngine:
    """
    The central state machine that manages the loop:
    Assessment → Strategy → Execution → Review
    """

    def __init__(self):
        """Initialize all agents."""
        self.path_generator = PathGeneratorAgent()
        self.evaluator = EvaluatorAgent()
        self.tutor = TutorAgent()
        self.reviewer = PedagogicalReviewerAgent()

        self.max_reviewer_retries = system_config.max_reviewer_retries

        logger.info("OrchestrationEngine initialized with all agents")

    def initialize_session(self, state: SessionState) -> List[dict]:
        """
        Initialize a new session by generating teaching paths.

        Args:
            state: The session state

        Returns:
            List of path options for user selection
        """
        logger.info(f"Initializing session: {state.session_id}")

        paths = self.path_generator.generate_paths(state.lesson_context)

        # Format paths for user selection with full sequences
        path_options = [
            {
                "id": path.id,
                "name": path.name,
                "description": path.description,
                "node_count": len(path.teaching_sequence),
                "sequence": [
                    {
                        "concept": node.concept,
                        "goal": node.goal
                    }
                    for node in path.teaching_sequence
                ]
            }
            for path in paths
        ]

        # Store paths temporarily (in real system, would store in state)
        self._temp_paths = {path.id: path for path in paths}

        logger.info(f"Generated {len(paths)} path options")
        return path_options

    def select_path(self, state: SessionState, path_id: str):
        """
        Select a teaching path and set it in the state.

        Args:
            state: The session state
            path_id: The ID of the selected path
        """
        if not hasattr(self, '_temp_paths') or path_id not in self._temp_paths:
            raise ValueError(f"Invalid path ID: {path_id}")

        selected_path = self._temp_paths[path_id]
        state.set_teaching_path(selected_path)

        logger.info(f"Path selected: {selected_path.name}")

    def start_teaching(self, state: SessionState) -> str:
        """
        Start teaching the first node (no evaluation feedback).

        Args:
            state: The session state

        Returns:
            Formatted tutor output for display
        """
        logger.info("Starting teaching with first node")

        tutor_output = self._generate_reviewed_tutor_output(
            state=state,
            strategy_directive=None  # First iteration has no evaluator feedback
        )

        # Add to history
        formatted_output = tutor_output.format_for_display()
        state.add_message(MessageRole.TUTOR, formatted_output, system_config.max_history_window)

        return formatted_output

    def process_user_response(self, state: SessionState, user_message: str) -> Optional[str]:
        """
        Process user response through the full teaching loop.

        Flow:
        1. Add user message to history
        2. Evaluate user response
        3. Decide: Advance or Remediate
        4. Generate tutor response with evaluator guidance
        5. Review tutor output
        6. Add tutor response to history
        7. Return formatted output (or None if complete)

        Args:
            state: The session state
            user_message: The user's response

        Returns:
            Next tutor output, or None if lesson is complete
        """
        logger.info("Processing user response")

        # Step 1: Add user message to history
        state.add_message(MessageRole.USER, user_message, system_config.max_history_window)

        # Get the last tutor message for context
        tutor_history = [msg for msg in state.history if msg.role == MessageRole.TUTOR]
        last_tutor_content = tutor_history[-1].content if tutor_history else ""

        # Step 2: Evaluate user response
        evaluation = self.evaluator.evaluate(
            state=state,
            user_message=user_message,
            tutor_previous_content=last_tutor_content
        )

        logger.info(f"Evaluation complete: should_advance={evaluation.should_advance}")

        # Step 3: Decide to advance or remediate
        if evaluation.should_advance:
            logger.info("User ready to advance")
            advanced = state.advance_to_next_node()

            if not advanced:
                # Reached the end
                logger.info("Lesson complete!")
                return None

            # Reset feedback loop for new node
            state.last_feedback_loop.reset()

        else:
            logger.info("User needs remediation on current node")

        # Step 4 & 5: Generate and review tutor response
        tutor_output = self._generate_reviewed_tutor_output(
            state=state,
            strategy_directive=evaluation.guidance_for_tutor
        )

        # Step 6: Add to history
        formatted_output = tutor_output.format_for_display()
        state.add_message(MessageRole.TUTOR, formatted_output, system_config.max_history_window)

        return formatted_output

    def _generate_reviewed_tutor_output(
        self,
        state: SessionState,
        strategy_directive: Optional[str]
    ) -> TutorOutput:
        """
        Generate tutor output with reviewer feedback loop.

        Implements the safety mechanism: max 3 retries, then bypass.

        Args:
            state: The session state
            strategy_directive: Guidance from evaluator (None for first node)

        Returns:
            Approved TutorOutput (or last attempt if max retries reached)
        """
        current_node = state.get_current_node()
        pedagogical_feedback = None
        last_output = None

        # Reset retry count at start
        state.last_feedback_loop.reset()

        while state.last_feedback_loop.retry_count <= self.max_reviewer_retries:
            logger.debug(f"Tutor generation attempt {state.last_feedback_loop.retry_count + 1}")

            # Generate tutor output
            tutor_output = self.tutor.teach_node(
                state=state,
                strategy_directive=strategy_directive,
                pedagogical_feedback=pedagogical_feedback
            )

            last_output = tutor_output

            # Review the output
            review_result = self.reviewer.review(
                tutor_output=tutor_output.to_dict(),
                current_node=current_node
            )

            if review_result.approved:
                logger.info("Tutor output approved by reviewer")
                return tutor_output

            # Not approved - check retry limit
            state.last_feedback_loop.increment(review_result.feedback)

            if state.last_feedback_loop.retry_count >= self.max_reviewer_retries:
                logger.warning(
                    f"Max reviewer retries ({self.max_reviewer_retries}) reached. "
                    "Bypassing reviewer and using last output."
                )
                return last_output

            # Retry with feedback
            logger.info(f"Retrying tutor generation with feedback (attempt {state.last_feedback_loop.retry_count + 1})")
            pedagogical_feedback = review_result.feedback

        # Should not reach here, but return last output as fallback
        return last_output

    def is_lesson_complete(self, state: SessionState) -> bool:
        """Check if the lesson is complete."""
        if not state.teaching_path:
            return False

        # Lesson is complete when we've finished the last node
        return state.current_index >= len(state.teaching_path.teaching_sequence) - 1

    def __str__(self) -> str:
        return (
            f"OrchestrationEngine("
            f"path_gen={self.path_generator}, "
            f"evaluator={self.evaluator}, "
            f"tutor={self.tutor}, "
            f"reviewer={self.reviewer})"
        )
