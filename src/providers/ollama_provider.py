"""
Ollama Provider Implementation

Integrates with Ollama for local LLM inference (Llama, Mistral, CodeLlama, etc.)
"""

import os
import time
import json
from typing import AsyncGenerator, Dict, List, Optional, Any
import logging
import httpx

from .base_provider import (
    BaseProvider,
    Message,
    GenerationConfig,
    GenerationResult
)

logger = logging.getLogger(__name__)


class OllamaProvider(BaseProvider):
    """Ollama local LLM provider using HTTP API"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Ollama provider

        Args:
            config: Configuration dict with optional 'base_url' and 'timeout'
        """
        super().__init__(config)

        self.base_url = self.config.get("base_url") or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.timeout = self.config.get("timeout", 120)

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout
        )

        self.logger.info(f"Ollama provider initialized with base_url: {self.base_url}")

    async def generate(
        self,
        prompt: str,
        model: str = "llama3",
        generation_config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> GenerationResult:
        """
        Generate text from a prompt using Ollama

        Args:
            prompt: Input text prompt
            model: Ollama model name (e.g., 'llama3', 'mistral', 'codellama')
            generation_config: Generation parameters
            **kwargs: Additional Ollama-specific arguments

        Returns:
            GenerationResult with generated text and metadata
        """
        start_time = time.time()
        config = generation_config or GenerationConfig()

        try:
            # Build request payload
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": config.temperature,
                    "num_predict": config.max_tokens,
                    "top_p": config.top_p,
                    "top_k": config.top_k,
                }
            }

            if config.stop_sequences:
                payload["options"]["stop"] = config.stop_sequences

            # Merge additional kwargs
            payload.update(kwargs)

            # Make API request
            response = await self.client.post("/api/generate", json=payload)
            response.raise_for_status()

            # Parse response
            result = response.json()
            text = result.get("response", "")

            # Extract metadata
            eval_count = result.get("eval_count", 0)
            prompt_eval_count = result.get("prompt_eval_count", 0)
            total_tokens = eval_count + prompt_eval_count

            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)

            # Ollama is free (local), so cost is 0
            cost = 0.0

            return GenerationResult(
                text=text,
                model=model,
                tokens_used=total_tokens,
                cost=cost,
                latency_ms=latency_ms,
                metadata={
                    "tokens_input": prompt_eval_count,
                    "tokens_output": eval_count,
                    "eval_duration": result.get("eval_duration", 0),
                    "total_duration": result.get("total_duration", 0),
                }
            )

        except httpx.HTTPStatusError as e:
            self._handle_error(e, f"generate (status {e.response.status_code})")
            raise
        except Exception as e:
            self._handle_error(e, "generate")
            raise

    async def generate_stream(
        self,
        prompt: str,
        model: str = "llama3",
        generation_config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Generate text from a prompt (streaming)

        Args:
            prompt: Input text prompt
            model: Ollama model name
            generation_config: Generation parameters
            **kwargs: Additional Ollama-specific arguments

        Yields:
            Text chunks as they are generated
        """
        config = generation_config or GenerationConfig()

        try:
            # Build request payload
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": True,
                "options": {
                    "temperature": config.temperature,
                    "num_predict": config.max_tokens,
                    "top_p": config.top_p,
                    "top_k": config.top_k,
                }
            }

            if config.stop_sequences:
                payload["options"]["stop"] = config.stop_sequences

            # Merge additional kwargs
            payload.update(kwargs)

            # Stream API request
            async with self.client.stream("POST", "/api/generate", json=payload) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            chunk = json.loads(line)
                            if "response" in chunk:
                                yield chunk["response"]
                        except json.JSONDecodeError:
                            self.logger.warning(f"Failed to parse JSON: {line}")
                            continue

        except httpx.HTTPStatusError as e:
            self._handle_error(e, f"generate_stream (status {e.response.status_code})")
            raise
        except Exception as e:
            self._handle_error(e, "generate_stream")
            raise

    async def chat(
        self,
        messages: List[Message],
        model: str = "llama3",
        generation_config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> GenerationResult:
        """
        Chat completion using Ollama

        Args:
            messages: List of chat messages
            model: Ollama model name
            generation_config: Generation parameters
            **kwargs: Additional Ollama-specific arguments

        Returns:
            GenerationResult with response and metadata
        """
        start_time = time.time()
        config = generation_config or GenerationConfig()

        try:
            # Build request payload
            payload = {
                "model": model,
                "messages": [msg.to_dict() for msg in messages],
                "stream": False,
                "options": {
                    "temperature": config.temperature,
                    "num_predict": config.max_tokens,
                    "top_p": config.top_p,
                    "top_k": config.top_k,
                }
            }

            if config.stop_sequences:
                payload["options"]["stop"] = config.stop_sequences

            # Merge additional kwargs
            payload.update(kwargs)

            # Make API request
            response = await self.client.post("/api/chat", json=payload)
            response.raise_for_status()

            # Parse response
            result = response.json()
            text = result.get("message", {}).get("content", "")

            # Extract metadata
            eval_count = result.get("eval_count", 0)
            prompt_eval_count = result.get("prompt_eval_count", 0)
            total_tokens = eval_count + prompt_eval_count

            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)

            # Ollama is free (local), so cost is 0
            cost = 0.0

            return GenerationResult(
                text=text,
                model=model,
                tokens_used=total_tokens,
                cost=cost,
                latency_ms=latency_ms,
                metadata={
                    "tokens_input": prompt_eval_count,
                    "tokens_output": eval_count,
                    "eval_duration": result.get("eval_duration", 0),
                    "total_duration": result.get("total_duration", 0),
                }
            )

        except httpx.HTTPStatusError as e:
            self._handle_error(e, f"chat (status {e.response.status_code})")
            raise
        except Exception as e:
            self._handle_error(e, "chat")
            raise

    async def chat_stream(
        self,
        messages: List[Message],
        model: str = "llama3",
        generation_config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Chat completion (streaming)

        Args:
            messages: List of chat messages
            model: Ollama model name
            generation_config: Generation parameters
            **kwargs: Additional Ollama-specific arguments

        Yields:
            Text chunks as they are generated
        """
        config = generation_config or GenerationConfig()

        try:
            # Build request payload
            payload = {
                "model": model,
                "messages": [msg.to_dict() for msg in messages],
                "stream": True,
                "options": {
                    "temperature": config.temperature,
                    "num_predict": config.max_tokens,
                    "top_p": config.top_p,
                    "top_k": config.top_k,
                }
            }

            if config.stop_sequences:
                payload["options"]["stop"] = config.stop_sequences

            # Merge additional kwargs
            payload.update(kwargs)

            # Stream API request
            async with self.client.stream("POST", "/api/chat", json=payload) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            chunk = json.loads(line)
                            if "message" in chunk and "content" in chunk["message"]:
                                yield chunk["message"]["content"]
                        except json.JSONDecodeError:
                            self.logger.warning(f"Failed to parse JSON: {line}")
                            continue

        except httpx.HTTPStatusError as e:
            self._handle_error(e, f"chat_stream (status {e.response.status_code})")
            raise
        except Exception as e:
            self._handle_error(e, "chat_stream")
            raise

    def calculate_cost(
        self,
        tokens_input: int,
        tokens_output: int,
        model: str
    ) -> float:
        """
        Calculate cost for Ollama usage (always free)

        Args:
            tokens_input: Number of input tokens
            tokens_output: Number of output tokens
            model: Model name

        Returns:
            Cost in USD (always 0.0 for local Ollama)
        """
        return 0.0

    async def list_models(self) -> List[str]:
        """
        List available Ollama models

        Returns:
            List of model names
        """
        try:
            response = await self.client.get("/api/tags")
            response.raise_for_status()

            result = response.json()
            models = [model["name"] for model in result.get("models", [])]
            return sorted(models)

        except httpx.HTTPStatusError as e:
            self._handle_error(e, f"list_models (status {e.response.status_code})")
            return []
        except Exception as e:
            self._handle_error(e, "list_models")
            return []

    async def check_availability(self) -> bool:
        """
        Check if Ollama is running and accessible

        Returns:
            True if Ollama is accessible, False otherwise
        """
        try:
            response = await self.client.get("/api/tags")
            return response.status_code == 200
        except Exception as e:
            self.logger.warning(f"Ollama not accessible: {str(e)}")
            return False

    async def pull_model(self, model: str) -> bool:
        """
        Pull/download a model from Ollama library

        Args:
            model: Model name to pull

        Returns:
            True if successful, False otherwise
        """
        try:
            payload = {"name": model, "stream": False}
            response = await self.client.post("/api/pull", json=payload)
            response.raise_for_status()
            return True

        except httpx.HTTPStatusError as e:
            self._handle_error(e, f"pull_model (status {e.response.status_code})")
            return False
        except Exception as e:
            self._handle_error(e, "pull_model")
            return False

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

    def __del__(self):
        """Cleanup on deletion"""
        try:
            import asyncio
            asyncio.create_task(self.close())
        except Exception:
            pass
