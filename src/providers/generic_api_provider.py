"""
Generic API Provider for any LLM API endpoint.

Supports multiple API formats:
- OpenAI-compatible APIs (OpenAI, OpenRouter, Together AI, Groq, Anyscale, etc.)
- Google Gemini
- Anthropic Claude
- Custom APIs with adapters
"""

import asyncio
import json
from typing import AsyncGenerator, Dict, List, Optional, Any
from dataclasses import dataclass
import aiohttp
from abc import ABC, abstractmethod

from .base_provider import (
    BaseProvider,
    Message,
    GenerationConfig,
    GenerationResult
)


@dataclass
class APIConfig:
    """Configuration for an API provider."""
    name: str  # Display name (e.g., "OpenAI GPT-4", "Gemini Pro")
    api_key: str
    base_url: str
    model: str
    api_format: str = "openai"  # openai, gemini, claude, custom
    headers: Optional[Dict[str, str]] = None
    default_params: Optional[Dict[str, Any]] = None
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0


class APIAdapter(ABC):
    """Abstract adapter for converting requests/responses between formats."""

    @abstractmethod
    def format_request(
        self,
        messages: List[Message],
        config: GenerationConfig,
        model: str
    ) -> Dict[str, Any]:
        """Format request payload for the API."""
        pass

    @abstractmethod
    def parse_response(self, response: Dict[str, Any]) -> str:
        """Parse response from the API."""
        pass

    @abstractmethod
    def parse_stream_chunk(self, chunk: str) -> Optional[str]:
        """Parse a streaming response chunk."""
        pass


class OpenAIAdapter(APIAdapter):
    """Adapter for OpenAI-compatible APIs."""

    def format_request(
        self,
        messages: List[Message],
        config: GenerationConfig,
        model: str
    ) -> Dict[str, Any]:
        return {
            "model": model,
            "messages": [{"role": msg.role, "content": msg.content} for msg in messages],
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "top_p": config.top_p,
            "stream": config.stream
        }

    def parse_response(self, response: Dict[str, Any]) -> str:
        return response["choices"][0]["message"]["content"]

    def parse_stream_chunk(self, chunk: str) -> Optional[str]:
        if chunk.startswith("data: "):
            chunk = chunk[6:]
        if chunk.strip() == "[DONE]":
            return None

        try:
            data = json.loads(chunk)
            delta = data["choices"][0]["delta"]
            return delta.get("content", "")
        except:
            return None


class GeminiAdapter(APIAdapter):
    """Adapter for Google Gemini API."""

    def format_request(
        self,
        messages: List[Message],
        config: GenerationConfig,
        model: str
    ) -> Dict[str, Any]:
        # Convert messages to Gemini format
        contents = []
        for msg in messages:
            role = "user" if msg.role in ["user", "system"] else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg.content}]
            })

        return {
            "contents": contents,
            "generationConfig": {
                "temperature": config.temperature,
                "maxOutputTokens": config.max_tokens,
                "topP": config.top_p
            }
        }

    def parse_response(self, response: Dict[str, Any]) -> str:
        return response["candidates"][0]["content"]["parts"][0]["text"]

    def parse_stream_chunk(self, chunk: str) -> Optional[str]:
        try:
            data = json.loads(chunk)
            if "candidates" in data:
                return data["candidates"][0]["content"]["parts"][0]["text"]
        except:
            pass
        return None


class ClaudeAdapter(APIAdapter):
    """Adapter for Anthropic Claude API."""

    def format_request(
        self,
        messages: List[Message],
        config: GenerationConfig,
        model: str
    ) -> Dict[str, Any]:
        # Extract system message if present
        system = ""
        formatted_messages = []

        for msg in messages:
            if msg.role == "system":
                system = msg.content
            else:
                formatted_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

        payload = {
            "model": model,
            "messages": formatted_messages,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "stream": config.stream
        }

        if system:
            payload["system"] = system

        return payload

    def parse_response(self, response: Dict[str, Any]) -> str:
        return response["content"][0]["text"]

    def parse_stream_chunk(self, chunk: str) -> Optional[str]:
        if chunk.startswith("data: "):
            chunk = chunk[6:]

        try:
            data = json.loads(chunk)
            if data.get("type") == "content_block_delta":
                return data["delta"].get("text", "")
        except:
            pass
        return None


class GenericAPIProvider(BaseProvider):
    """Generic provider that works with any configured API endpoint."""

    ADAPTERS = {
        "openai": OpenAIAdapter(),
        "gemini": GeminiAdapter(),
        "claude": ClaudeAdapter()
    }

    def __init__(self, api_configs: Optional[List[APIConfig]] = None):
        """
        Initialize with API configurations.

        Args:
            api_configs: List of API configurations
        """
        self.api_configs: Dict[str, APIConfig] = {}
        if api_configs:
            for config in api_configs:
                self.add_api(config)

        self.session: Optional[aiohttp.ClientSession] = None

    def add_api(self, config: APIConfig):
        """Add a new API configuration."""
        self.api_configs[config.name] = config

    def remove_api(self, name: str):
        """Remove an API configuration."""
        if name in self.api_configs:
            del self.api_configs[name]

    def get_adapter(self, api_format: str) -> APIAdapter:
        """Get the appropriate adapter for the API format."""
        return self.ADAPTERS.get(api_format, OpenAIAdapter())

    async def _ensure_session(self):
        """Ensure aiohttp session exists."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def _get_headers(self, config: APIConfig) -> Dict[str, str]:
        """Build headers for the API request."""
        headers = {
            "Content-Type": "application/json"
        }

        # API-specific headers
        if config.api_format == "openai":
            headers["Authorization"] = f"Bearer {config.api_key}"
        elif config.api_format == "gemini":
            # Gemini uses API key in URL
            pass
        elif config.api_format == "claude":
            headers["x-api-key"] = config.api_key
            headers["anthropic-version"] = "2023-06-01"

        # Custom headers
        if config.headers:
            headers.update(config.headers)

        return headers

    def _get_endpoint(self, config: APIConfig, stream: bool = False) -> str:
        """Build the API endpoint URL."""
        base_url = config.base_url.rstrip("/")

        if config.api_format == "openai":
            return f"{base_url}/chat/completions"
        elif config.api_format == "gemini":
            action = "streamGenerateContent" if stream else "generateContent"
            return f"{base_url}/v1/models/{config.model}:{action}?key={config.api_key}"
        elif config.api_format == "claude":
            return f"{base_url}/v1/messages"
        else:
            return base_url

    async def generate(
        self,
        prompt: str,
        model: str,
        **kwargs
    ) -> str:
        """Generate response from the API."""
        messages = [Message(role="user", content=prompt)]
        result = await self.chat(messages, model, **kwargs)
        return result.content

    async def generate_stream(
        self,
        prompt: str,
        model: str,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response from the API."""
        messages = [Message(role="user", content=prompt)]
        async for chunk in self.chat_stream(messages, model, **kwargs):
            yield chunk

    async def chat(
        self,
        messages: List[Message],
        model: str,
        **kwargs
    ) -> GenerationResult:
        """Chat completion from the API."""
        # Find API config
        config = self._get_config_for_model(model)
        if not config:
            raise ValueError(f"No API configuration found for model: {model}")

        # Build generation config
        gen_config = GenerationConfig(
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 1000),
            top_p=kwargs.get("top_p", 1.0),
            stream=False
        )

        # Get adapter and format request
        adapter = self.get_adapter(config.api_format)
        payload = adapter.format_request(messages, gen_config, config.model)

        # Make request
        await self._ensure_session()
        headers = await self._get_headers(config)
        endpoint = self._get_endpoint(config, stream=False)

        async with self.session.post(endpoint, json=payload, headers=headers) as response:
            response.raise_for_status()
            data = await response.json()

        # Parse response
        content = adapter.parse_response(data)

        # Estimate tokens and cost
        input_tokens = sum(len(msg.content.split()) for msg in messages)
        output_tokens = len(content.split())

        return GenerationResult(
            content=content,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            cost=self.calculate_cost(input_tokens + output_tokens, model)
        )

    async def chat_stream(
        self,
        messages: List[Message],
        model: str,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Streaming chat completion from the API."""
        # Find API config
        config = self._get_config_for_model(model)
        if not config:
            raise ValueError(f"No API configuration found for model: {model}")

        # Build generation config
        gen_config = GenerationConfig(
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 1000),
            top_p=kwargs.get("top_p", 1.0),
            stream=True
        )

        # Get adapter and format request
        adapter = self.get_adapter(config.api_format)
        payload = adapter.format_request(messages, gen_config, config.model)

        # Make streaming request
        await self._ensure_session()
        headers = await self._get_headers(config)
        endpoint = self._get_endpoint(config, stream=True)

        async with self.session.post(endpoint, json=payload, headers=headers) as response:
            response.raise_for_status()

            async for line in response.content:
                line = line.decode('utf-8').strip()
                if line:
                    chunk = adapter.parse_stream_chunk(line)
                    if chunk:
                        yield chunk

    def _get_config_for_model(self, model: str) -> Optional[APIConfig]:
        """Find the API configuration for a model name."""
        # Try exact match first
        if model in self.api_configs:
            return self.api_configs[model]

        # Try to find by model field
        for config in self.api_configs.values():
            if config.model == model or config.name == model:
                return config

        return None

    def calculate_cost(self, tokens: int, model: str) -> float:
        """Calculate cost for the given tokens and model."""
        config = self._get_config_for_model(model)
        if not config:
            return 0.0

        # Rough estimate (would need to track input/output separately)
        cost_per_token = (config.cost_per_1k_input + config.cost_per_1k_output) / 2000
        return tokens * cost_per_token

    def list_models(self) -> List[str]:
        """List all configured API models."""
        return list(self.api_configs.keys())

    async def check_availability(self) -> bool:
        """Check if any APIs are configured."""
        return len(self.api_configs) > 0

    async def close(self):
        """Close the HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()

    def __del__(self):
        """Cleanup on deletion."""
        if self.session and not self.session.closed:
            try:
                asyncio.get_event_loop().run_until_complete(self.session.close())
            except:
                pass


# Predefined API configurations
def get_predefined_apis() -> Dict[str, APIConfig]:
    """Get predefined API configurations (without API keys)."""
    return {
        "OpenAI GPT-4": APIConfig(
            name="OpenAI GPT-4",
            api_key="",  # To be filled by user
            base_url="https://api.openai.com/v1",
            model="gpt-4-turbo-preview",
            api_format="openai",
            cost_per_1k_input=0.01,
            cost_per_1k_output=0.03
        ),
        "OpenAI GPT-3.5": APIConfig(
            name="OpenAI GPT-3.5",
            api_key="",
            base_url="https://api.openai.com/v1",
            model="gpt-3.5-turbo",
            api_format="openai",
            cost_per_1k_input=0.0005,
            cost_per_1k_output=0.0015
        ),
        "Google Gemini Pro": APIConfig(
            name="Google Gemini Pro",
            api_key="",
            base_url="https://generativelanguage.googleapis.com",
            model="gemini-pro",
            api_format="gemini",
            cost_per_1k_input=0.000125,
            cost_per_1k_output=0.000375
        ),
        "Anthropic Claude 3": APIConfig(
            name="Anthropic Claude 3",
            api_key="",
            base_url="https://api.anthropic.com",
            model="claude-3-opus-20240229",
            api_format="claude",
            cost_per_1k_input=0.015,
            cost_per_1k_output=0.075
        ),
        "OpenRouter (Any Model)": APIConfig(
            name="OpenRouter",
            api_key="",
            base_url="https://openrouter.ai/api/v1",
            model="openai/gpt-3.5-turbo",  # Can be changed
            api_format="openai",
            cost_per_1k_input=0.0,
            cost_per_1k_output=0.0
        ),
        "Together AI": APIConfig(
            name="Together AI",
            api_key="",
            base_url="https://api.together.xyz/v1",
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            api_format="openai",
            cost_per_1k_input=0.0006,
            cost_per_1k_output=0.0006
        ),
        "Groq": APIConfig(
            name="Groq",
            api_key="",
            base_url="https://api.groq.com/openai/v1",
            model="mixtral-8x7b-32768",
            api_format="openai",
            cost_per_1k_input=0.00027,
            cost_per_1k_output=0.00027
        ),
        # MegaLLM - Only the requested models
        "MegaLLM GPT-5 Mini": APIConfig(
            name="MegaLLM GPT-5 Mini",
            api_key="",
            base_url="https://ai.megallm.io/v1",
            model="gpt-5-mini",
            api_format="openai",
            cost_per_1k_input=0.0,  # Update with actual pricing from MegaLLM dashboard
            cost_per_1k_output=0.0
        ),
        "MegaLLM Claude Haiku 4.5": APIConfig(
            name="MegaLLM Claude Haiku 4.5",
            api_key="",
            base_url="https://ai.megallm.io/v1",
            model="claude-haiku-4-5",  # Verify exact model ID from MegaLLM dashboard
            api_format="openai",
            cost_per_1k_input=0.0,  # Update with actual pricing from MegaLLM dashboard
            cost_per_1k_output=0.0
        ),
        "MegaLLM Gemini 2.5 Flash": APIConfig(
            name="MegaLLM Gemini 2.5 Flash",
            api_key="",
            base_url="https://ai.megallm.io/v1",
            model="gemini-2-5-flash",  # Verify exact model ID from MegaLLM dashboard
            api_format="openai",
            cost_per_1k_input=0.0,  # Update with actual pricing from MegaLLM dashboard
            cost_per_1k_output=0.0
        )
    }
