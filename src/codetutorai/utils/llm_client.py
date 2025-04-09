"""
CodeTutorAI - LLM Client

This module provides a unified interface for calling different LLM providers
with enhanced features like retries, error handling, and token management.
"""

import hashlib
import json
import logging
import os
import time
from typing import Optional

import diskcache
import google.generativeai as genai  # Import Google AI library
import requests
import tiktoken
from google.api_core import \
    exceptions as google_api_exceptions  # Import Google API exceptions
from tenacity import (retry, retry_if_exception_type, stop_after_attempt,
                      wait_exponential)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("llm_client")


class TokenCounter:
    """Utility class for counting tokens in prompts."""

    def __init__(self, model: str = "gpt-4"):
        """Initialize the token counter.

        Args:
            model (str): The model to use for token counting
        """
        try:
            self.encoder = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fall back to cl100k_base for models not directly supported
            self.encoder = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text.

        Args:
            text (str): The text to count tokens for

        Returns:
            int: The number of tokens
        """
        return len(self.encoder.encode(text))


class LLMClient:
    """Client for interacting with various LLM providers."""

    def __init__(
        self,
        provider: str = "openai",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_retries: int = 3,
        timeout: int = 60,
        verbose: bool = False,
        cache_enabled: bool = False,
        cache_dir: str = ".llm_cache",
    ):
        """Initialize the LLM client.

        Args:
            provider (str): The LLM provider to use (openai, anthropic, palm)
            api_key (str, optional): API key for the provider
            model (str, optional): The model to use (defaults to provider's default)
            max_retries (int): Maximum number of retries for failed requests
            timeout (int): Timeout for requests in seconds
            verbose (bool): Whether to print verbose output
            cache_enabled (bool): Whether to enable caching for LLM calls
            cache_dir (str): Directory to store the cache
        """
        self.provider = provider.lower()
        self.api_key = api_key or self._get_api_key(provider)
        self.model = model or self._get_default_model(provider)
        self.max_retries = max_retries
        self.timeout = timeout
        self.verbose = verbose
        self.cache_enabled = cache_enabled
        self.cache = None
        if self.cache_enabled:
            os.makedirs(cache_dir, exist_ok=True)
            self.cache = diskcache.Cache(cache_dir)
            logger.info(f"LLM caching enabled. Cache directory: {cache_dir}")

        # Initialize token counter
        self.token_counter = TokenCounter(
            self.model if provider == "openai" else "gpt-4"
        )

        if self.verbose:
            logger.setLevel(logging.DEBUG)

        logger.debug(
            f"Initialized LLM client with provider: {provider}, model: {self.model}"
        )

    def _get_api_key(self, provider: str) -> str:
        """Get the API key for the specified provider from environment variables.

        Args:
            provider (str): The LLM provider

        Returns:
            str: The API key

        Raises:
            ValueError: If the API key is not found
        """
        env_var_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "palm": "GOOGLE_API_KEY",
            "google": "GOOGLE_API_KEY",
        }

        if provider.lower() not in env_var_map:
            raise ValueError(f"Unsupported LLM provider: {provider}")

        env_var = env_var_map[provider.lower()]
        api_key = os.environ.get(env_var)

        if not api_key:
            raise ValueError(f"{env_var} not found in environment variables")

        return api_key

    def _get_default_model(self, provider: str) -> str:
        """Get the default model for the specified provider.

        Args:
            provider (str): The LLM provider

        Returns:
            str: The default model
        """
        default_models = {
            "openai": "gpt-4",
            "anthropic": "claude-2",
            "palm": "text-bison-001",
            "google": "text-bison-001",
        }

        return default_models.get(provider.lower(), "gpt-4")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(
            (requests.exceptions.RequestException, json.JSONDecodeError)
        ),
        reraise=True,
    )
    def call_openai(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_message: Optional[str] = None,
    ) -> str:
        """Call the OpenAI API.

        Args:
            prompt (str): The prompt to send to the API
            max_tokens (int): Maximum number of tokens to generate
            temperature (float): Sampling temperature
            system_message (str, optional): System message to prepend

        Returns:
            str: The generated text
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        logger.debug(f"Calling OpenAI API with model: {self.model}")

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            data=json.dumps(data),
            timeout=self.timeout,
        )

        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(
            (requests.exceptions.RequestException, json.JSONDecodeError)
        ),
        reraise=True,
    )
    def call_anthropic(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_message: Optional[str] = None,
    ) -> str:
        """Call the Anthropic Claude API.

        Args:
            prompt (str): The prompt to send to the API
            max_tokens (int): Maximum number of tokens to generate
            temperature (float): Sampling temperature
            system_message (str, optional): System message to prepend

        Returns:
            str: The generated text
        """
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }

        # Format the prompt according to Anthropic's requirements
        formatted_prompt = prompt
        if system_message:
            formatted_prompt = f"{system_message}\n\n{prompt}"

        data = {
            "model": self.model,
            "prompt": f"\n\nHuman: {formatted_prompt}\n\nAssistant:",
            "max_tokens_to_sample": max_tokens,
            "temperature": temperature,
        }

        logger.debug(f"Calling Anthropic API with model: {self.model}")

        response = requests.post(
            "https://api.anthropic.com/v1/complete",
            headers=headers,
            data=json.dumps(data),
            timeout=self.timeout,
        )

        response.raise_for_status()
        return response.json()["completion"]

    # --- Google Gemini Call ---
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        # Add specific Google API exceptions if available, otherwise use general ones
        retry=retry_if_exception_type((google_api_exceptions.GoogleAPIError, requests.exceptions.RequestException)), # Use correct Google API error
        reraise=True,
    )
    def call_google_gemini(
        self,
        prompt: str,
        max_tokens: int = 2048, # Gemini often supports larger outputs
        temperature: float = 0.7,
        system_message: Optional[str] = None,
    ) -> str:
        """Calls the Google Gemini API using the google-generativeai library.

        Args:
            prompt (str): The user prompt.
            max_tokens (int): Maximum number of tokens to generate.
            temperature (float): Sampling temperature.
            system_message (str, optional): System message/instruction.

        Returns:
            str: The generated text content.

        Raises:
            ValueError: If the API key is missing.
            genai.APIError: If the Google API call fails.
            Exception: For other unexpected errors.
        """
        if not self.api_key:
            raise ValueError("Google API Key (GOOGLE_API_KEY) is required.")

        try:
            genai.configure(api_key=self.api_key)

            # --- Model Name Mapping (Conceptual - needs proper implementation) ---
            # This mapping should be more robustly handled, maybe in __init__
            # Map UI display names to actual API model IDs
            # NOTE: This mapping should ideally be centralized or loaded from config
            MODEL_NAME_TO_API_ID = {
                # Google
                "Gemini 1.5 Flash": "gemini-1.5-flash-latest", # Assuming latest for flash
                "Gemini 1.5 Pro": "gemini-1.5-pro-latest",
                "Gemini 2.0 Flash": "gemini-2.0-flash", # Placeholder - Verify actual ID
                "Gemini 2.5 Pro Preview": "gemini-2.5-pro-preview-03-25", # Placeholder - Verify actual ID

                # OpenAI (Assuming UI names match common API IDs)
                "GPT-4O": "gpt-4o",
                "GPT-4 Turbo": "gpt-4-turbo",
                "GPT-4": "gpt-4",
                "GPT-3.5 Turbo": "gpt-3.5-turbo",

                # Anthropic (Using provided IDs, assuming 'latest' maps correctly)
                "Claude 3.5 Haiku": "claude-3-5-haiku-latest", # Placeholder - Verify actual ID
                "Claude 3.5 Sonnet": "claude-3-5-sonnet-20240620",
                "Claude 3.7 Sonnet": "claude-3-7-sonnet-latest", # Placeholder - Verify actual ID
                "Claude 3 Opus": "claude-3-opus-20240229", # Assuming latest maps to this date version
            }
            # Use the selected model from self.model (which comes from Streamlit state)
            # Default to a known working model if the mapping is missing
            api_model_id = MODEL_NAME_TO_API_ID.get(self.model, "gemini-1.5-flash-latest")
            api_model_id = MODEL_NAME_TO_API_ID.get(self.model, "gemini-1.5-pro-latest") # Default if name not found
            logger.debug(f"Mapping UI model '{self.model}' to API ID '{api_model_id}'")
            # --- End Mapping ---


            model = genai.GenerativeModel(
                model_name=api_model_id,
                # Pass system instruction if provided and supported by the model version
                system_instruction=system_message if system_message else None
            )

            generation_config = genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature
            )

            logger.debug(f"Calling Google Gemini API with model: {api_model_id}")

            # Construct content (handle system message if not directly supported)
            # For some models, system message is part of the model init,
            # for others, it might need to be part of the first 'user' turn.
            # Assuming model init handles it for now.
            contents = [prompt] # Simple case, just the user prompt

            response = model.generate_content(
                contents=contents,
                generation_config=generation_config,
                # Add safety settings if needed
                # safety_settings=...
            )

            # Handle potential blocks or lack of content
            if not response.candidates:
                raise google_api_exceptions.GoogleAPIError("No candidates returned from Gemini API.") # Use correct exception
            # Check finish reason by comparing its name attribute (more robust if enum path is unclear)
            if hasattr(response.candidates[0].finish_reason, 'name') and response.candidates[0].finish_reason.name != 'STOP':
                logger.warning(f"Gemini generation finished with reason: {response.candidates[0].finish_reason}")
                # Optionally raise an error or just return potentially partial text

            # Extract text, handling potential multipart responses if necessary
            if response.candidates[0].content.parts:
                return "".join(part.text for part in response.candidates[0].content.parts)
            else:
                # Should not happen with text models, but handle defensively
                return ""


        except ValueError as ve: # Catch missing API key specifically
            logger.error(f"Configuration error for Google Gemini: {ve}")
            raise
        except google_api_exceptions.GoogleAPIError as e: # Use correct exception
            logger.error(f"Google Gemini API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling Google Gemini: {e}")
            # Consider logging traceback here
            raise # Re-raise the exception

    def call(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_message: Optional[str] = None,
        force_regeneration: bool = False, # Added parameter to force regeneration
    ) -> str:
        """Call the LLM provider with the given prompt.

        Args:
            prompt (str): The prompt to send to the LLM
            max_tokens (int): Maximum number of tokens to generate
            temperature (float): Sampling temperature
            system_message (str, optional): System message to prepend

        Returns:
            str: The generated text
        """
        providers = {
            "openai": self.call_openai,
            "anthropic": self.call_anthropic,
            # "palm": self.call_palm, # Remove palm
            "google": self.call_google_gemini, # Map google to the new method
        }

        if self.provider not in providers:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
        cache_key = None
        # --- Caching Logic ---
        cache_key = None
        # Calculate cache key if caching is enabled (needed for both lookup and storage)
        if self.cache_enabled and self.cache is not None:
            key_data = {
                "provider": self.provider,
                "model": self.model,
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "system_message": system_message,
            }
            key_string = json.dumps(key_data, sort_keys=True)
            cache_key = hashlib.sha256(key_string.encode('utf-8')).hexdigest()

            # Attempt cache lookup only if NOT forcing regeneration
            if not force_regeneration:
                cached_result = self.cache.get(cache_key)
                if cached_result is not None:
                    if self.verbose:
                        logger.debug(f"Cache hit for key: {cache_key[:8]}...")
                    # Indicate cache was used (modify if a more direct way is found later)
                    # Note: This might need refinement if flow passes cache status back
                    # context["cache_hit"] = True # Example if context is mutable
                    return cached_result # Return cached result
                elif self.verbose:
                    logger.debug(f"Cache miss for key: {cache_key[:8]}...")
            elif self.verbose: # force_regeneration is True
                 logger.debug(f"Forcing regeneration for key: {cache_key[:8]}..., skipping cache check.")
        # --- End Caching Logic ---

        # Check token count if using OpenAI
        if self.provider == "openai":
            token_count = self.token_counter.count_tokens(prompt)
            if system_message:
                token_count += self.token_counter.count_tokens(system_message)

            logger.debug(f"Prompt token count: {token_count}")

            # Check if we're approaching token limits
            if token_count + max_tokens > 8192 and "gpt-4" in self.model:
                logger.warning(
                    f"Token count ({token_count} + {max_tokens}) approaching GPT-4 limit (8192)"
                )
            elif token_count + max_tokens > 4096 and "gpt-3.5" in self.model:
                logger.warning(
                    f"Token count ({token_count} + {max_tokens}) approaching GPT-3.5 limit (4096)"
                )

        try:
            start_time = time.time()
            response = providers[self.provider](
                prompt, max_tokens, temperature, system_message
            )
            elapsed_time = time.time() - start_time

            logger.debug(f"LLM call completed in {elapsed_time:.2f} seconds")
            # Store in cache if enabled and successful
            # Store in cache if caching is enabled (cache_key will be non-None if enabled)
            if self.cache_enabled and self.cache is not None:
                self.cache.set(cache_key, response)
                if self.verbose:
                    logger.debug(f"Stored result in cache for key: {cache_key[:8]}...")
            return response
        except Exception as e:
            logger.error(f"Error calling {self.provider} LLM: {str(e)}")
            raise


# For backward compatibility with existing code
def call_llm(
    prompt: str,
    provider: str = "openai",
    api_key: Optional[str] = None,
    max_tokens: int = 1000,
    temperature: float = 0.7,
    system_message: Optional[str] = None,
    cache_enabled: bool = False,
    cache_dir: str = ".llm_cache",
    force_regeneration: bool = False, # Added parameter
) -> str:
    """Call an LLM provider with the given prompt (compatibility function).

    Args:
        prompt (str): The prompt to send to the LLM
        provider (str): The LLM provider to use (openai, anthropic, palm)
        api_key (str, optional): API key for the provider
        max_tokens (int): Maximum number of tokens to generate
        temperature (float): Sampling temperature
        system_message (str, optional): System message to prepend
        cache_enabled (bool): Whether to enable caching
        cache_dir (str): Directory for the cache

    Returns:
        str: The generated text
    """
    client = LLMClient(
        provider=provider,
        api_key=api_key,
        cache_enabled=cache_enabled,
        cache_dir=cache_dir
    )
    return client.call(prompt, max_tokens, temperature, system_message, force_regeneration=force_regeneration)
