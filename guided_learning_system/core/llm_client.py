"""LLM client wrapper for Groq API."""

import json
import logging
from typing import Dict, Any, Optional
from groq import Groq

from config import model_config


logger = logging.getLogger(__name__)


class LLMClient:
    """Wrapper for Groq LLM API calls."""

    def __init__(self):
        """Initialize the Groq client."""
        api_key = model_config.get_api_key()  # Lazy check for API key
        self.client = Groq(api_key=api_key)
        self.default_model = model_config.default_model
        logger.info(f"LLM Client initialized with model: {self.default_model}")

    def call(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        response_format: Optional[Dict[str, str]] = None,
        model: Optional[str] = None
    ) -> str:
        """
        Make a call to the LLM.

        Args:
            system_prompt: System-level instructions
            user_prompt: User message/query
            temperature: Sampling temperature (0.0-1.0)
            response_format: Optional format specification (e.g., {"type": "json_object"})
            model: Optional model override

        Returns:
            The LLM's response content
        """
        model = model or self.default_model

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        logger.debug(f"LLM Call - Model: {model}, Temp: {temperature}")
        logger.debug(f"System: {system_prompt[:100]}...")
        logger.debug(f"User: {user_prompt[:100]}...")

        try:
            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": model_config.max_tokens,
            }

            if response_format:
                kwargs["response_format"] = response_format

            response = self.client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content

            logger.debug(f"LLM Response: {content[:100]}...")
            return content

        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            raise

    def call_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Make a call expecting JSON response.

        Returns:
            Parsed JSON dictionary
        """
        response = self.call(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            response_format={"type": "json_object"},
            model=model
        )

        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Raw response: {response}")
            raise


# Global LLM client instance (lazy-loaded)
_llm_client_instance = None


def get_llm_client() -> LLMClient:
    """Get or create the global LLM client instance."""
    global _llm_client_instance
    if _llm_client_instance is None:
        _llm_client_instance = LLMClient()
    return _llm_client_instance


# For backward compatibility
class _LLMClientProxy:
    """Proxy that lazily creates the LLM client."""
    def __getattr__(self, name):
        return getattr(get_llm_client(), name)


llm_client = _LLMClientProxy()
