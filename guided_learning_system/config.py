"""Configuration for the Guided Learning System."""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load .env file if it exists
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path)


@dataclass
class ModelConfig:
    """Configuration for LLM models."""

    provider: str = "groq"
    default_model: str = "meta-llama/llama-4-maverick-17b-128e-instruct"

    # Agent-specific temperatures
    path_generator_temp: float = 0.7
    evaluator_temp: float = 0.1  # Deterministic
    tutor_temp: float = 0.5      # Creative
    reviewer_temp: float = 0.3

    # Model-specific settings
    max_tokens: int = 3000

    # API configuration
    api_key: Optional[str] = None

    def __post_init__(self):
        """Load API key from environment if not provided."""
        if self.api_key is None:
            self.api_key = os.getenv("GROQ_API_KEY")

    def get_api_key(self) -> str:
        """Get API key, raising error if not set."""
        if not self.api_key:
            raise ValueError(
                "GROQ_API_KEY environment variable not set. "
                "Please set it with: export GROQ_API_KEY='your-key-here'"
            )
        return self.api_key


@dataclass
class SystemConfig:
    """System-wide configuration."""

    # Reviewer retry limit
    max_reviewer_retries: int = 3

    # History window sizes (in turns)
    evaluator_history_window: int = 2  # Last 2 turns
    tutor_history_window: int = 6      # Last 6 turns
    max_history_window: int = 10       # Maximum stored

    # Logging
    log_level: str = "DEBUG"
    log_file: Optional[str] = "guided_learning.log"


# Global configuration instances
model_config = ModelConfig()
system_config = SystemConfig()
