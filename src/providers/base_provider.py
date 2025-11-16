"""
Base Provider Abstract Class

Defines the interface that all LLM providers must implement.
"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, List, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Chat message structure"""
    role: str  # 'system', 'user', 'assistant'
    content: str

    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass
class GenerationConfig:
    """Configuration for text generation"""
    temperature: float = 0.7
    max_tokens: int = 500
    top_p: float = 0.9
    top_k: int = 40
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop_sequences: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values"""
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class GenerationResult:
    """Result from text generation"""
    text: str
    model: str
    tokens_used: int
    cost: float
    latency_ms: int
    metadata: Optional[Dict[str, Any]] = None


class BaseProvider(ABC):
    """
    Abstract base class for all LLM providers.

    All providers must implement:
    - generate(): Synchronous text generation
    - generate_stream(): Streaming text generation
    - calculate_cost(): Calculate API costs
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize provider with configuration

        Args:
            config: Provider-specific configuration
        """
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model: str,
        generation_config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> GenerationResult:
        """
        Generate text from a prompt (non-streaming)

        Args:
            prompt: Input text prompt
            model: Model name/identifier
            generation_config: Generation parameters
            **kwargs: Additional provider-specific arguments

        Returns:
            GenerationResult with text and metadata

        Raises:
            Exception: If generation fails
        """
        pass

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        model: str,
        generation_config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Generate text from a prompt (streaming)

        Args:
            prompt: Input text prompt
            model: Model name/identifier
            generation_config: Generation parameters
            **kwargs: Additional provider-specific arguments

        Yields:
            Text chunks as they are generated

        Raises:
            Exception: If generation fails
        """
        pass

    @abstractmethod
    async def chat(
        self,
        messages: List[Message],
        model: str,
        generation_config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> GenerationResult:
        """
        Chat completion (non-streaming)

        Args:
            messages: List of chat messages
            model: Model name/identifier
            generation_config: Generation parameters
            **kwargs: Additional provider-specific arguments

        Returns:
            GenerationResult with response and metadata

        Raises:
            Exception: If generation fails
        """
        pass

    @abstractmethod
    async def chat_stream(
        self,
        messages: List[Message],
        model: str,
        generation_config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Chat completion (streaming)

        Args:
            messages: List of chat messages
            model: Model name/identifier
            generation_config: Generation parameters
            **kwargs: Additional provider-specific arguments

        Yields:
            Text chunks as they are generated

        Raises:
            Exception: If generation fails
        """
        pass

    @abstractmethod
    def calculate_cost(
        self,
        tokens_input: int,
        tokens_output: int,
        model: str
    ) -> float:
        """
        Calculate cost for API usage

        Args:
            tokens_input: Number of input tokens
            tokens_output: Number of output tokens
            model: Model name/identifier

        Returns:
            Cost in USD
        """
        pass

    @abstractmethod
    async def list_models(self) -> List[str]:
        """
        List available models for this provider

        Returns:
            List of model names/identifiers
        """
        pass

    @abstractmethod
    async def check_availability(self) -> bool:
        """
        Check if the provider is available/accessible

        Returns:
            True if provider is available, False otherwise
        """
        pass

    def _handle_error(self, error: Exception, context: str = "") -> None:
        """
        Handle and log errors consistently

        Args:
            error: The exception that occurred
            context: Additional context about where the error occurred
        """
        error_msg = f"Error in {self.__class__.__name__}"
        if context:
            error_msg += f" ({context})"
        error_msg += f": {str(error)}"
        self.logger.error(error_msg)
