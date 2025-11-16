"""
LLM Service - Multi-Provider LLM Management

Coordinates multiple LLM providers (OpenAI, Ollama, HuggingFace) with:
- Provider routing
- Streaming support
- Cost tracking
- Fallback handling
"""

import os
import logging
from typing import AsyncGenerator, Dict, List, Optional, Any, Union
from datetime import datetime

from ..providers.base_provider import (
    BaseProvider,
    Message,
    GenerationConfig,
    GenerationResult
)
from ..providers.openai_provider import OpenAIProvider
from ..providers.ollama_provider import OllamaProvider
from ..providers.huggingface_provider import HuggingFaceProvider

logger = logging.getLogger(__name__)


class LLMService:
    """
    Multi-provider LLM service with routing, streaming, and cost tracking
    """

    # Model to provider mapping
    MODEL_PROVIDER_MAP = {
        "gpt-4": "openai",
        "gpt-4-turbo": "openai",
        "gpt-3.5-turbo": "openai",
        "llama3": "ollama",
        "llama2": "ollama",
        "mistral": "ollama",
        "codellama": "ollama",
        "gemma": "ollama",
        "phi": "ollama",
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize LLM service with providers

        Args:
            config: Service configuration
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Initialize providers
        self.providers: Dict[str, BaseProvider] = {}
        self._initialize_providers()

        # Cost tracking
        self.total_cost = 0.0
        self.total_tokens = 0
        self.usage_history: List[Dict[str, Any]] = []

        # Fallback configuration
        self.fallback_enabled = self.config.get("fallback_enabled", True)
        self.fallback_order = self.config.get("fallback_order", ["openai", "ollama", "huggingface"])

        self.logger.info(f"LLM service initialized with providers: {list(self.providers.keys())}")

    def _initialize_providers(self):
        """Initialize all available providers"""
        # OpenAI
        try:
            if os.getenv("OPENAI_API_KEY"):
                self.providers["openai"] = OpenAIProvider(
                    config=self.config.get("openai", {})
                )
                self.logger.info("OpenAI provider initialized")
        except Exception as e:
            self.logger.warning(f"Failed to initialize OpenAI provider: {e}")

        # Ollama
        try:
            self.providers["ollama"] = OllamaProvider(
                config=self.config.get("ollama", {})
            )
            self.logger.info("Ollama provider initialized")
        except Exception as e:
            self.logger.warning(f"Failed to initialize Ollama provider: {e}")

        # HuggingFace
        try:
            self.providers["huggingface"] = HuggingFaceProvider(
                config=self.config.get("huggingface", {})
            )
            self.logger.info("HuggingFace provider initialized")
        except Exception as e:
            self.logger.warning(f"Failed to initialize HuggingFace provider: {e}")

    def _get_provider(self, model: str) -> Optional[str]:
        """
        Determine which provider to use for a given model

        Args:
            model: Model name

        Returns:
            Provider name or None if not found
        """
        # Check exact match first
        for model_key, provider in self.MODEL_PROVIDER_MAP.items():
            if model.startswith(model_key):
                return provider

        # Default to first available provider
        if self.providers:
            return list(self.providers.keys())[0]

        return None

    async def generate(
        self,
        prompt: str,
        model: str = "gpt-3.5-turbo",
        generation_config: Optional[GenerationConfig] = None,
        provider: Optional[str] = None,
        **kwargs
    ) -> GenerationResult:
        """
        Generate text from a prompt (non-streaming)

        Args:
            prompt: Input text prompt
            model: Model name
            generation_config: Generation parameters
            provider: Specific provider to use (optional)
            **kwargs: Additional provider-specific arguments

        Returns:
            GenerationResult with text and metadata

        Raises:
            Exception: If generation fails on all providers
        """
        # Determine provider
        if not provider:
            provider = self._get_provider(model)

        if not provider or provider not in self.providers:
            raise ValueError(f"No provider available for model: {model}")

        # Attempt generation with primary provider
        try:
            result = await self.providers[provider].generate(
                prompt=prompt,
                model=model,
                generation_config=generation_config,
                **kwargs
            )

            # Track usage
            self._track_usage(result)

            return result

        except Exception as e:
            self.logger.error(f"Generation failed with {provider}: {e}")

            # Try fallback if enabled
            if self.fallback_enabled:
                return await self._generate_with_fallback(
                    prompt, model, generation_config, provider, **kwargs
                )
            else:
                raise

    async def generate_stream(
        self,
        prompt: str,
        model: str = "gpt-3.5-turbo",
        generation_config: Optional[GenerationConfig] = None,
        provider: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Generate text from a prompt (streaming)

        Args:
            prompt: Input text prompt
            model: Model name
            generation_config: Generation parameters
            provider: Specific provider to use (optional)
            **kwargs: Additional provider-specific arguments

        Yields:
            Text chunks as they are generated
        """
        # Determine provider
        if not provider:
            provider = self._get_provider(model)

        if not provider or provider not in self.providers:
            raise ValueError(f"No provider available for model: {model}")

        # Stream generation
        try:
            async for chunk in self.providers[provider].generate_stream(
                prompt=prompt,
                model=model,
                generation_config=generation_config,
                **kwargs
            ):
                yield chunk

        except Exception as e:
            self.logger.error(f"Streaming generation failed with {provider}: {e}")
            raise

    async def chat(
        self,
        messages: List[Message],
        model: str = "gpt-3.5-turbo",
        generation_config: Optional[GenerationConfig] = None,
        provider: Optional[str] = None,
        **kwargs
    ) -> GenerationResult:
        """
        Chat completion (non-streaming)

        Args:
            messages: List of chat messages
            model: Model name
            generation_config: Generation parameters
            provider: Specific provider to use (optional)
            **kwargs: Additional provider-specific arguments

        Returns:
            GenerationResult with response and metadata
        """
        # Determine provider
        if not provider:
            provider = self._get_provider(model)

        if not provider or provider not in self.providers:
            raise ValueError(f"No provider available for model: {model}")

        # Attempt chat completion
        try:
            result = await self.providers[provider].chat(
                messages=messages,
                model=model,
                generation_config=generation_config,
                **kwargs
            )

            # Track usage
            self._track_usage(result)

            return result

        except Exception as e:
            self.logger.error(f"Chat completion failed with {provider}: {e}")

            # Try fallback if enabled
            if self.fallback_enabled:
                return await self._chat_with_fallback(
                    messages, model, generation_config, provider, **kwargs
                )
            else:
                raise

    async def chat_stream(
        self,
        messages: List[Message],
        model: str = "gpt-3.5-turbo",
        generation_config: Optional[GenerationConfig] = None,
        provider: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Chat completion (streaming)

        Args:
            messages: List of chat messages
            model: Model name
            generation_config: Generation parameters
            provider: Specific provider to use (optional)
            **kwargs: Additional provider-specific arguments

        Yields:
            Text chunks as they are generated
        """
        # Determine provider
        if not provider:
            provider = self._get_provider(model)

        if not provider or provider not in self.providers:
            raise ValueError(f"No provider available for model: {model}")

        # Stream chat completion
        try:
            async for chunk in self.providers[provider].chat_stream(
                messages=messages,
                model=model,
                generation_config=generation_config,
                **kwargs
            ):
                yield chunk

        except Exception as e:
            self.logger.error(f"Streaming chat failed with {provider}: {e}")
            raise

    async def _generate_with_fallback(
        self,
        prompt: str,
        model: str,
        generation_config: Optional[GenerationConfig],
        failed_provider: str,
        **kwargs
    ) -> GenerationResult:
        """
        Try generation with fallback providers

        Args:
            prompt: Input text prompt
            model: Model name
            generation_config: Generation parameters
            failed_provider: Provider that failed
            **kwargs: Additional arguments

        Returns:
            GenerationResult from successful provider

        Raises:
            Exception: If all providers fail
        """
        self.logger.info(f"Attempting fallback after {failed_provider} failure")

        # Try other providers in fallback order
        for fallback_provider in self.fallback_order:
            if fallback_provider == failed_provider or fallback_provider not in self.providers:
                continue

            try:
                self.logger.info(f"Trying fallback provider: {fallback_provider}")

                # Use a compatible model for the fallback provider
                fallback_model = self._get_fallback_model(fallback_provider)

                result = await self.providers[fallback_provider].generate(
                    prompt=prompt,
                    model=fallback_model,
                    generation_config=generation_config,
                    **kwargs
                )

                self._track_usage(result)
                self.logger.info(f"Fallback successful with {fallback_provider}")
                return result

            except Exception as e:
                self.logger.warning(f"Fallback provider {fallback_provider} also failed: {e}")
                continue

        raise Exception(f"All providers failed for model: {model}")

    async def _chat_with_fallback(
        self,
        messages: List[Message],
        model: str,
        generation_config: Optional[GenerationConfig],
        failed_provider: str,
        **kwargs
    ) -> GenerationResult:
        """
        Try chat with fallback providers

        Args:
            messages: List of chat messages
            model: Model name
            generation_config: Generation parameters
            failed_provider: Provider that failed
            **kwargs: Additional arguments

        Returns:
            GenerationResult from successful provider

        Raises:
            Exception: If all providers fail
        """
        self.logger.info(f"Attempting fallback after {failed_provider} failure")

        # Try other providers in fallback order
        for fallback_provider in self.fallback_order:
            if fallback_provider == failed_provider or fallback_provider not in self.providers:
                continue

            try:
                self.logger.info(f"Trying fallback provider: {fallback_provider}")

                # Use a compatible model for the fallback provider
                fallback_model = self._get_fallback_model(fallback_provider)

                result = await self.providers[fallback_provider].chat(
                    messages=messages,
                    model=fallback_model,
                    generation_config=generation_config,
                    **kwargs
                )

                self._track_usage(result)
                self.logger.info(f"Fallback successful with {fallback_provider}")
                return result

            except Exception as e:
                self.logger.warning(f"Fallback provider {fallback_provider} also failed: {e}")
                continue

        raise Exception(f"All providers failed for model: {model}")

    def _get_fallback_model(self, provider: str) -> str:
        """
        Get a default model for a fallback provider

        Args:
            provider: Provider name

        Returns:
            Default model name for the provider
        """
        defaults = {
            "openai": "gpt-3.5-turbo",
            "ollama": "llama3",
            "huggingface": "gpt2"
        }
        return defaults.get(provider, "gpt2")

    def _track_usage(self, result: GenerationResult):
        """
        Track usage and costs

        Args:
            result: Generation result to track
        """
        self.total_cost += result.cost
        self.total_tokens += result.tokens_used

        self.usage_history.append({
            "timestamp": datetime.now().isoformat(),
            "model": result.model,
            "tokens": result.tokens_used,
            "cost": result.cost,
            "latency_ms": result.latency_ms
        })

    async def list_available_models(self) -> Dict[str, List[str]]:
        """
        List all available models from all providers

        Returns:
            Dictionary mapping provider names to list of models
        """
        available_models = {}

        for provider_name, provider in self.providers.items():
            try:
                models = await provider.list_models()
                available_models[provider_name] = models
            except Exception as e:
                self.logger.warning(f"Failed to list models for {provider_name}: {e}")
                available_models[provider_name] = []

        return available_models

    async def check_provider_availability(self) -> Dict[str, bool]:
        """
        Check availability of all providers

        Returns:
            Dictionary mapping provider names to availability status
        """
        availability = {}

        for provider_name, provider in self.providers.items():
            try:
                is_available = await provider.check_availability()
                availability[provider_name] = is_available
            except Exception as e:
                self.logger.warning(f"Failed to check availability for {provider_name}: {e}")
                availability[provider_name] = False

        return availability

    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get usage statistics

        Returns:
            Dictionary with usage stats
        """
        return {
            "total_cost": self.total_cost,
            "total_tokens": self.total_tokens,
            "total_requests": len(self.usage_history),
            "history": self.usage_history[-10:]  # Last 10 requests
        }

    def reset_usage_stats(self):
        """Reset usage tracking"""
        self.total_cost = 0.0
        self.total_tokens = 0
        self.usage_history = []
        self.logger.info("Usage statistics reset")
