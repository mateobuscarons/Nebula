"""Session state management for the Guided Learning System."""

import uuid
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum


logger = logging.getLogger(__name__)


class MessageRole(str, Enum):
    """Message roles in conversation history."""
    TUTOR = "tutor"
    USER = "user"


@dataclass
class Message:
    """A single message in the conversation history."""
    role: MessageRole
    content: str

    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role.value, "content": self.content}


@dataclass
class TeachingNode:
    """A single node in the teaching path."""
    id: str
    concept: str
    goal: str

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'TeachingNode':
        return TeachingNode(
            id=data["id"],
            concept=data["concept"],
            goal=data["goal"]
        )

    def to_dict(self) -> Dict[str, str]:
        return {"id": self.id, "concept": self.concept, "goal": self.goal}


@dataclass
class TeachingPath:
    """A complete teaching path with sequence of nodes."""
    id: str
    name: str
    description: str
    teaching_sequence: List[TeachingNode]

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'TeachingPath':
        return TeachingPath(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            teaching_sequence=[
                TeachingNode.from_dict(node) for node in data["teaching_sequence"]
            ]
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "teaching_sequence": [node.to_dict() for node in self.teaching_sequence]
        }


@dataclass
class LessonContext:
    """Context information about the lesson."""
    title: str
    objectives: List[str]
    topics_covered: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "objectives": self.objectives,
            "topics_covered": self.topics_covered
        }


@dataclass
class FeedbackLoop:
    """Temporary state for Reviewer feedback loops."""
    retry_count: int = 0
    reviewer_notes: Optional[str] = None

    def reset(self):
        """Reset the feedback loop state."""
        self.retry_count = 0
        self.reviewer_notes = None

    def increment(self, notes: str):
        """Increment retry count and store notes."""
        self.retry_count += 1
        self.reviewer_notes = notes

    def to_dict(self) -> Dict[str, Any]:
        return {
            "retry_count": self.retry_count,
            "reviewer_notes": self.reviewer_notes
        }


@dataclass
class SessionState:
    """
    The central state object passed between agents.
    Maintains all context to prevent hallucinations.
    """
    session_id: str
    lesson_context: LessonContext
    teaching_path: Optional[TeachingPath] = None
    current_index: int = 0
    history: List[Message] = field(default_factory=list)
    last_feedback_loop: FeedbackLoop = field(default_factory=FeedbackLoop)

    @staticmethod
    def create_new(lesson_context: LessonContext) -> 'SessionState':
        """Create a new session with a unique ID."""
        session_id = str(uuid.uuid4())
        logger.info(f"Created new session: {session_id}")
        return SessionState(
            session_id=session_id,
            lesson_context=lesson_context
        )

    def set_teaching_path(self, path: TeachingPath):
        """Set the selected teaching path."""
        self.teaching_path = path
        self.current_index = 0
        logger.info(f"Teaching path set: {path.name} ({len(path.teaching_sequence)} nodes)")

    def get_current_node(self) -> Optional[TeachingNode]:
        """Get the current teaching node."""
        if not self.teaching_path or self.current_index >= len(self.teaching_path.teaching_sequence):
            return None
        return self.teaching_path.teaching_sequence[self.current_index]

    def advance_to_next_node(self) -> bool:
        """
        Advance to the next node in the teaching path.
        Returns True if advanced, False if at the end.
        """
        if not self.teaching_path:
            return False

        if self.current_index < len(self.teaching_path.teaching_sequence) - 1:
            self.current_index += 1
            logger.info(f"Advanced to node {self.current_index}: {self.get_current_node().concept}")
            return True
        else:
            logger.info("Reached end of teaching path")
            return False

    def add_message(self, role: MessageRole, content: str, max_window: int = 10):
        """Add a message to history with rolling window."""
        self.history.append(Message(role=role, content=content))

        # Keep only the last max_window messages
        if len(self.history) > max_window:
            self.history = self.history[-max_window:]
            logger.debug(f"Trimmed history to {max_window} messages")

    def get_recent_history(self, num_turns: int) -> List[Message]:
        """Get the last N turns from history."""
        return self.history[-num_turns:] if self.history else []

    def is_complete(self) -> bool:
        """Check if the lesson is complete."""
        if not self.teaching_path:
            return False
        return self.current_index >= len(self.teaching_path.teaching_sequence) - 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "lesson_context": self.lesson_context.to_dict(),
            "teaching_path": self.teaching_path.to_dict() if self.teaching_path else None,
            "current_index": self.current_index,
            "history": [msg.to_dict() for msg in self.history],
            "last_feedback_loop": self.last_feedback_loop.to_dict()
        }

    def __str__(self) -> str:
        """String representation for logging."""
        current_node = self.get_current_node()
        return (
            f"Session({self.session_id[:8]}...): "
            f"Node {self.current_index}/{len(self.teaching_path.teaching_sequence) - 1 if self.teaching_path else 0} - "
            f"{current_node.concept if current_node else 'No path selected'}"
        )
