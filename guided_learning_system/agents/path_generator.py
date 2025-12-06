"""Path Generator Agent - Creates diverse, atomic learning paths."""

import logging
from typing import List, Dict, Any

from core import LessonContext, TeachingPath, TeachingNode, llm_client
from config import model_config


logger = logging.getLogger(__name__)


class PathGeneratorAgent:
    """
    The Architect: Analyzes lesson objectives and creates structured,
    atomic learning paths.
    """

    def __init__(self):
        self.temperature = model_config.path_generator_temp
        logger.info("PathGeneratorAgent initialized")

    def generate_paths(self, lesson_context: LessonContext) -> List[TeachingPath]:
        """
        Generate diverse teaching paths from lesson objectives.

        Args:
            lesson_context: The lesson's title, objectives, and topics

        Returns:
            List of TeachingPath objects (diverse approaches)
        """
        logger.info(f"Generating paths for: {lesson_context.title}")
        logger.debug(f"Objectives: {lesson_context.objectives}")

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(lesson_context)

        try:
            response = llm_client.call_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=self.temperature
            )

            paths = self._parse_paths(response)
            logger.info(f"Generated {len(paths)} diverse teaching paths")

            for i, path in enumerate(paths, 1):
                logger.debug(f"Path {i}: {path.name} ({len(path.teaching_sequence)} nodes)")

            return paths

        except Exception as e:
            logger.error(f"Path generation failed: {e}")
            raise

    def _build_system_prompt(self) -> str:
        """Build the system prompt for path generation."""
        return """You are a Path Generator Agent, an expert instructional designer.

Your role is to analyze learning objectives and create structured, atomic learning paths.

CORE PRINCIPLES:
1. Break objectives into ATOMIC CONCEPTS (one concept per node)
2. Keep paths SHORT and LEAN (focused on the essentials): 3-5 nodes total (including intro/closing)
3. Prevent cognitive overload - small, digestible chunks
4. Always include an INTRODUCTORY NODE (overview/context)
5. Always include a CLOSING NODE (summary/verification)
6. Create DIVERSE approaches - different angles to the same material

OUTPUT REQUIREMENTS:
- Generate 2-3 diverse paths (different teaching approaches)
- Each path must be CONCISE: 3-5 nodes maximum
- Nodes must be atomic and focused on essentials

Return ONLY valid JSON in this exact format:
{
  "paths": [
    {
      "id": "1",
      "name": "Path Name",
      "description": "Brief description of this approach",
      "teaching_sequence": [
        {
          "id": "node_1",
          "concept": "Concept name",
          "goal": "What the learner should achieve"
        }
      ]
    }
  ]
}"""

    def _build_user_prompt(self, lesson_context: LessonContext) -> str:
        """Build the user prompt with lesson details."""
        objectives_text = "\n".join(f"- {obj}" for obj in lesson_context.objectives)

        return f"""Create diverse teaching paths for this lesson:

LESSON TITLE: {lesson_context.title}

LEARNING OBJECTIVES:
{objectives_text}

Generate 2-3 diverse teaching paths that approach these objectives from different angles.

CRITICAL REQUIREMENTS:
- Focus on the most essential concepts only
- Each node should be atomic and teach ONE clear concept
- Different paths should take different approaches to the same objectives

Remember: Return ONLY the JSON object, nothing else."""

    def _parse_paths(self, response: Dict[str, Any]) -> List[TeachingPath]:
        """Parse the JSON response into TeachingPath objects."""
        if "paths" not in response:
            raise ValueError("Response missing 'paths' key")

        paths = []
        for path_data in response["paths"]:
            try:
                path = TeachingPath.from_dict(path_data)
                paths.append(path)
            except Exception as e:
                logger.warning(f"Failed to parse path: {e}")
                continue

        if not paths:
            raise ValueError("No valid paths generated")

        return paths
