"""
EnlightenAI - LLM Client

This module provides a unified interface for calling different LLM providers.
This is a compatibility layer that imports from the new llm_client module.
"""

from typing import Optional

from utils.llm_client import call_llm as new_call_llm


def call_llm(
    prompt: str,
    provider: str = "openai",
    api_key: Optional[str] = None,
    max_tokens: int = 1000,
    temperature: float = 0.7,
) -> str:
    """Call an LLM provider with the given prompt.

    Args:
        prompt (str): The prompt to send to the LLM
        provider (str, optional): The LLM provider to use (openai, anthropic, palm)
        api_key (str, optional): API key for the provider
        max_tokens (int, optional): Maximum number of tokens to generate
        temperature (float, optional): Sampling temperature

    Returns:
        str: The generated text
    """
    return new_call_llm(prompt, provider, api_key, max_tokens, temperature)
