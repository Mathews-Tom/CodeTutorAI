"""
EnlightenAI - LLM Client

This module provides a unified interface for calling different LLM providers.
"""

import os
import json
import requests
from typing import Dict, Any, Optional


def call_openai(prompt: str, api_key: Optional[str] = None, max_tokens: int = 1000, temperature: float = 0.7) -> str:
    """Call the OpenAI API.
    
    Args:
        prompt (str): The prompt to send to the API
        api_key (str, optional): OpenAI API key (defaults to OPENAI_API_KEY env var)
        max_tokens (int, optional): Maximum number of tokens to generate
        temperature (float, optional): Sampling temperature
        
    Returns:
        str: The generated text
    """
    api_key = api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key not provided")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    data = {
        "model": "gpt-4",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        data=json.dumps(data)
    )
    
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def call_anthropic(prompt: str, api_key: Optional[str] = None, max_tokens: int = 1000, temperature: float = 0.7) -> str:
    """Call the Anthropic Claude API.
    
    Args:
        prompt (str): The prompt to send to the API
        api_key (str, optional): Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
        max_tokens (int, optional): Maximum number of tokens to generate
        temperature (float, optional): Sampling temperature
        
    Returns:
        str: The generated text
    """
    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("Anthropic API key not provided")
    
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key
    }
    
    data = {
        "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
        "model": "claude-2",
        "max_tokens_to_sample": max_tokens,
        "temperature": temperature
    }
    
    response = requests.post(
        "https://api.anthropic.com/v1/complete",
        headers=headers,
        data=json.dumps(data)
    )
    
    response.raise_for_status()
    return response.json()["completion"]


def call_palm(prompt: str, api_key: Optional[str] = None, max_tokens: int = 1000, temperature: float = 0.7) -> str:
    """Call the Google PaLM API.
    
    Args:
        prompt (str): The prompt to send to the API
        api_key (str, optional): Google API key (defaults to GOOGLE_API_KEY env var)
        max_tokens (int, optional): Maximum number of tokens to generate
        temperature (float, optional): Sampling temperature
        
    Returns:
        str: The generated text
    """
    api_key = api_key or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("Google API key not provided")
    
    headers = {
        "Content-Type": "application/json"
    }
    
    data = {
        "prompt": {"text": prompt},
        "temperature": temperature,
        "maxOutputTokens": max_tokens
    }
    
    response = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta2/models/text-bison-001:generateText?key={api_key}",
        headers=headers,
        data=json.dumps(data)
    )
    
    response.raise_for_status()
    return response.json()["candidates"][0]["output"]


def call_llm(prompt: str, provider: str = "openai", api_key: Optional[str] = None, 
             max_tokens: int = 1000, temperature: float = 0.7) -> str:
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
    providers = {
        "openai": call_openai,
        "anthropic": call_anthropic,
        "palm": call_palm
    }
    
    if provider not in providers:
        raise ValueError(f"Unsupported LLM provider: {provider}")
    
    try:
        return providers[provider](prompt, api_key, max_tokens, temperature)
    except Exception as e:
        raise Exception(f"Error calling {provider} LLM: {str(e)}")
