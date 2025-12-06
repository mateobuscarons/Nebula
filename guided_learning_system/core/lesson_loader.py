"""Utility to load and parse lesson plans from JSON files."""

import json
import logging
from pathlib import Path
from typing import Dict, Any

from core import LessonContext


logger = logging.getLogger(__name__)


class LessonLoader:
    """Loads lesson plans from JSON files."""

    @staticmethod
    def load_lesson(file_path: str, lesson_number: int = 1) -> LessonContext:
        """
        Load a specific lesson from a lesson plan JSON file.

        Args:
            file_path: Path to the lesson plan JSON file
            lesson_number: Which lesson to load (1-indexed)

        Returns:
            LessonContext with the lesson details
        """
        logger.info(f"Loading lesson {lesson_number} from {file_path}")

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Lesson plan file not found: {file_path}")

        with open(path, 'r') as f:
            data = json.load(f)

        # Extract lesson
        lessons = data.get("lesson_plan", {}).get("lessons", [])
        if not lessons:
            raise ValueError("No lessons found in lesson plan")

        # Find the requested lesson (1-indexed)
        lesson_data = None
        for lesson in lessons:
            if lesson.get("lesson_number") == lesson_number:
                lesson_data = lesson
                break

        if not lesson_data:
            raise ValueError(f"Lesson {lesson_number} not found in plan")

        # Create LessonContext
        context = LessonContext(
            title=lesson_data.get("title", ""),
            objectives=lesson_data.get("learning_objectives", []),
            topics_covered=lesson_data.get("topics_covered", [])
        )

        logger.info(f"Loaded lesson: {context.title}")
        logger.debug(f"Objectives: {len(context.objectives)}")

        return context

    @staticmethod
    def list_lessons(file_path: str) -> list:
        """
        List all lessons in a lesson plan file.

        Args:
            file_path: Path to the lesson plan JSON file

        Returns:
            List of lesson summaries
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Lesson plan file not found: {file_path}")

        with open(path, 'r') as f:
            data = json.load(f)

        lessons = data.get("lesson_plan", {}).get("lessons", [])
        module_title = data.get("lesson_plan", {}).get("module_title", "Unknown Module")

        summaries = []
        for lesson in lessons:
            summaries.append({
                "number": lesson.get("lesson_number"),
                "title": lesson.get("title"),
                "topics": lesson.get("topics_covered", [])
            })

        logger.info(f"Found {len(summaries)} lessons in module: {module_title}")
        return summaries
