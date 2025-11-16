"""
OpenAI Provider Implementation

Integrates with OpenAI's GPT models (GPT-4, GPT-3.5, etc.)
"""

import os
import time
from typing import AsyncGenerator, Dict, List, Optional, Any
import logging
import tiktoken

from openai import AsyncOpenAI, OpenAIError
from .base_provider import (
    BaseProvider,
    Message,
    GenerationConfig,
    GenerationResult
)

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseProvider):
    """OpenAI LLM provider using official Python SDK"""

    # Pricing per 1K tokens (as of 2024)
    PRICING = {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-4-turbo-preview": {"input": 0.01, "output": 0.03},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        "gpt-3.5-turbo-16k": {"input": 0.003, "output": 0.004},
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize OpenAI provider

        Args:
            config: Configuration dict with optional 'api_key' and 'organization'
        """
        super().__init__(config)

        api_key = self.config.get("api_key") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not found in config or environment")

        organization = self.config.get("organization") or os.getenv("OPENAI_ORG_ID")

        self.client = AsyncOpenAI(
            api_key=api_key,
            organization=organization
        )

        self.logger.info("OpenAI provider initialized")

    async def generate(
        self,
        prompt: str,
        model: str = "gpt-3.5-turbo",
        generation_config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> GenerationResult:
        """
        Generate text from a prompt using OpenAI

        Args:
            prompt: Input text prompt
            model: OpenAI model name
            generation_config: Generation parameters
            **kwargs: Additional OpenAI-specific arguments

        Returns:
            GenerationResult with generated text and metadata
        """
        start_time = time.time()
        config = generation_config or GenerationConfig()

        try:
            # Convert prompt to messages format
            messages = [Message(role="user", content=prompt)]

            # Use chat endpoint
            response = await self.client.chat.completions.create(
                model=model,
                messages=[msg.to_dict() for msg in messages],
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                top_p=config.top_p,
                frequency_penalty=config.frequency_penalty,
                presence_penalty=config.presence_penalty,
                stop=config.stop_sequences,
                **kwargs
            )

            # Extract response
            text = response.choices[0].message.content
            tokens_input = response.usage.prompt_tokens
            tokens_output = response.usage.completion_tokens

            # Calculate cost
            cost = self.calculate_cost(tokens_input, tokens_output, model)

            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)

            return GenerationResult(
                text=text,
                model=model,
                tokens_used=tokens_input + tokens_output,
                cost=cost,
                latency_ms=latency_ms,
                metadata={
                    "tokens_input": tokens_input,
                    "tokens_output": tokens_output,
                    "finish_reason": response.choices[0].finish_reason
                }
            )

        except OpenAIError as e:
            self._handle_error(e, "generate")
            raise
        except Exception as e:
            self._handle_error(e, "generate")
            raise

    async def generate_stream(
        self,
        prompt: str,
        model: str = "gpt-3.5-turbo",
        generation_config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Generate text from a prompt (streaming)

        Args:
            prompt: Input text prompt
            model: OpenAI model name
            generation_config: Generation parameters
            **kwargs: Additional OpenAI-specific arguments

        Yields:
            Text chunks as they are generated
        """
        config = generation_config or GenerationConfig()

        try:
            # Convert prompt to messages format
            messages = [Message(role="user", content=prompt)]

            # Stream chat completion
            stream = await self.client.chat.completions.create(
                model=model,
                messages=[msg.to_dict() for msg in messages],
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                top_p=config.top_p,
                frequency_penalty=config.frequency_penalty,
                presence_penalty=config.presence_penalty,
                stop=config.stop_sequences,
                stream=True,
                **kwargs
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except OpenAIError as e:
            self._handle_error(e, "generate_stream")
            raise
        except Exception as e:
            self._handle_error(e, "generate_stream")
            raise

    async def chat(
        self,
        messages: List[Message],
        model: str = "gpt-3.5-turbo",
        generation_config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> GenerationResult:
        """
        Chat completion using OpenAI

        Args:
            messages: List of chat messages
            model: OpenAI model name
            generation_config: Generation parameters
            **kwargs: Additional OpenAI-specific arguments

        Returns:
            GenerationResult with response and metadata
        """
        start_time = time.time()
        config = generation_config or GenerationConfig()

        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=[msg.to_dict() for msg in messages],
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                top_p=config.top_p,
                frequency_penalty=config.frequency_penalty,
                presence_penalty=config.presence_penalty,
                stop=config.stop_sequences,
                **kwargs
            )

            # Extract response
            text = response.choices[0].message.content
            tokens_input = response.usage.prompt_tokens
            tokens_output = response.usage.completion_tokens

            # Calculate cost
            cost = self.calculate_cost(tokens_input, tokens_output, model)

            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)

            return GenerationResult(
                text=text,
                model=model,
                tokens_used=tokens_input + tokens_output,
                cost=cost,
                latency_ms=latency_ms,
                metadata={
                    "tokens_input": tokens_input,
                    "tokens_output": tokens_output,
                    "finish_reason": response.choices[0].finish_reason
                }
            )

        except OpenAIError as e:
            self._handle_error(e, "chat")
            raise
        except Exception as e:
            self._handle_error(e, "chat")
            raise

    async def chat_stream(
        self,
        messages: List[Message],
        model: str = "gpt-3.5-turbo",
        generation_config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Chat completion (streaming)

        Args:
            messages: List of chat messages
            model: OpenAI model name
            generation_config: Generation parameters
            **kwargs: Additional OpenAI-specific arguments

        Yields:
            Text chunks as they are generated
        """
        config = generation_config or GenerationConfig()

        try:
            stream = await self.client.chat.completions.create(
                model=model,
                messages=[msg.to_dict() for msg in messages],
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                top_p=config.top_p,
                frequency_penalty=config.frequency_penalty,
                presence_penalty=config.presence_penalty,
                stop=config.stop_sequences,
                stream=True,
                **kwargs
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except OpenAIError as e:
            self._handle_error(e, "chat_stream")
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
        Calculate cost for OpenAI API usage

        Args:
            tokens_input: Number of input tokens
            tokens_output: Number of output tokens
            model: Model name

        Returns:
            Cost in USD
        """
        # Find matching pricing (handle model variants)
        pricing = None
        for model_key in self.PRICING:
            if model.startswith(model_key):
                pricing = self.PRICING[model_key]
                break

        if not pricing:
            # Default to GPT-3.5 pricing if model not found
            self.logger.warning(f"Pricing not found for model {model}, using GPT-3.5 pricing")
            pricing = self.PRICING["gpt-3.5-turbo"]

        # Calculate cost (pricing is per 1K tokens)
        input_cost = (tokens_input / 1000) * pricing["input"]
        output_cost = (tokens_output / 1000) * pricing["output"]

        return input_cost + output_cost

    async def list_models(self) -> List[str]:
        """
        List available OpenAI models

        Returns:
            List of model names
        """
        try:
            models = await self.client.models.list()
            # Filter to chat models only
            chat_models = [
                model.id for model in models.data
                if "gpt" in model.id.lower()
            ]
            return sorted(chat_models)

        except OpenAIError as e:
            self._handle_error(e, "list_models")
            return list(self.PRICING.keys())
        except Exception as e:
            self._handle_error(e, "list_models")
            return list(self.PRICING.keys())

    async def check_availability(self) -> bool:
        """
        Check if OpenAI API is accessible

        Returns:
            True if API is accessible, False otherwise
        """
        try:
            # Try to list models as a health check
            await self.client.models.list()
            return True
        except Exception as e:
            self.logger.warning(f"OpenAI API not accessible: {str(e)}")
            return False

    def count_tokens(self, text: str, model: str = "gpt-3.5-turbo") -> int:
        """
        Count tokens in text using tiktoken

        Args:
            text: Input text
            model: Model name (for correct tokenizer)

        Returns:
            Number of tokens
        """
        try:
            encoding = tiktoken.encoding_for_model(model)
            return len(encoding.encode(text))
        except Exception as e:
            self.logger.warning(f"Error counting tokens: {str(e)}")
            # Rough estimate: ~4 characters per token
            return len(text) // 4
