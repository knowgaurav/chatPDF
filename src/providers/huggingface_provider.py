"""
HuggingFace Provider Implementation

Integrates with HuggingFace Hub for accessing open-source models
"""

import os
import time
from typing import AsyncGenerator, Dict, List, Optional, Any
import logging
import asyncio

from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TextIteratorStreamer,
    pipeline
)
import torch
from threading import Thread

from .base_provider import (
    BaseProvider,
    Message,
    GenerationConfig,
    GenerationResult
)

logger = logging.getLogger(__name__)


class HuggingFaceProvider(BaseProvider):
    """HuggingFace provider for local/cloud model inference"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize HuggingFace provider

        Args:
            config: Configuration dict with optional 'api_key', 'cache_dir', 'device'
        """
        super().__init__(config)

        self.api_key = self.config.get("api_key") or os.getenv("HF_API_KEY")
        self.cache_dir = self.config.get("cache_dir") or os.getenv("HF_CACHE_DIR", "./data/models/huggingface")
        self.device = self.config.get("device", "cuda" if torch.cuda.is_available() else "cpu")

        # Cache for loaded models
        self.loaded_models = {}
        self.loaded_tokenizers = {}

        self.logger.info(f"HuggingFace provider initialized (device: {self.device})")

    def _load_model(self, model: str) -> tuple:
        """
        Load model and tokenizer (with caching)

        Args:
            model: Model name or path

        Returns:
            Tuple of (model, tokenizer)
        """
        if model in self.loaded_models:
            return self.loaded_models[model], self.loaded_tokenizers[model]

        try:
            self.logger.info(f"Loading model: {model}")

            # Load tokenizer
            tokenizer = AutoTokenizer.from_pretrained(
                model,
                cache_dir=self.cache_dir,
                token=self.api_key
            )

            # Load model
            model_obj = AutoModelForCausalLM.from_pretrained(
                model,
                cache_dir=self.cache_dir,
                token=self.api_key,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                low_cpu_mem_usage=True
            )

            # Move to device
            model_obj = model_obj.to(self.device)

            # Cache
            self.loaded_models[model] = model_obj
            self.loaded_tokenizers[model] = tokenizer

            self.logger.info(f"Model loaded successfully: {model}")
            return model_obj, tokenizer

        except Exception as e:
            self._handle_error(e, f"load_model ({model})")
            raise

    async def generate(
        self,
        prompt: str,
        model: str = "gpt2",
        generation_config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> GenerationResult:
        """
        Generate text from a prompt using HuggingFace

        Args:
            prompt: Input text prompt
            model: HuggingFace model name
            generation_config: Generation parameters
            **kwargs: Additional generation arguments

        Returns:
            GenerationResult with generated text and metadata
        """
        start_time = time.time()
        config = generation_config or GenerationConfig()

        try:
            # Load model and tokenizer
            model_obj, tokenizer = await asyncio.to_thread(self._load_model, model)

            # Tokenize input
            inputs = tokenizer(prompt, return_tensors="pt").to(self.device)
            input_length = inputs.input_ids.shape[1]

            # Generate
            with torch.no_grad():
                outputs = await asyncio.to_thread(
                    model_obj.generate,
                    inputs.input_ids,
                    max_new_tokens=config.max_tokens,
                    temperature=config.temperature,
                    top_p=config.top_p,
                    top_k=config.top_k,
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id,
                    **kwargs
                )

            # Decode output
            generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

            # Remove the prompt from output
            if generated_text.startswith(prompt):
                generated_text = generated_text[len(prompt):].strip()

            # Calculate tokens
            output_length = outputs.shape[1]
            tokens_output = output_length - input_length
            total_tokens = output_length

            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)

            # HuggingFace local is free
            cost = 0.0

            return GenerationResult(
                text=generated_text,
                model=model,
                tokens_used=total_tokens,
                cost=cost,
                latency_ms=latency_ms,
                metadata={
                    "tokens_input": input_length,
                    "tokens_output": tokens_output,
                    "device": self.device
                }
            )

        except Exception as e:
            self._handle_error(e, "generate")
            raise

    async def generate_stream(
        self,
        prompt: str,
        model: str = "gpt2",
        generation_config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Generate text from a prompt (streaming)

        Args:
            prompt: Input text prompt
            model: HuggingFace model name
            generation_config: Generation parameters
            **kwargs: Additional generation arguments

        Yields:
            Text chunks as they are generated
        """
        config = generation_config or GenerationConfig()

        try:
            # Load model and tokenizer
            model_obj, tokenizer = await asyncio.to_thread(self._load_model, model)

            # Tokenize input
            inputs = tokenizer(prompt, return_tensors="pt").to(self.device)

            # Create streamer
            streamer = TextIteratorStreamer(
                tokenizer,
                skip_prompt=True,
                skip_special_tokens=True
            )

            # Generation kwargs
            generation_kwargs = {
                "input_ids": inputs.input_ids,
                "max_new_tokens": config.max_tokens,
                "temperature": config.temperature,
                "top_p": config.top_p,
                "top_k": config.top_k,
                "do_sample": True,
                "pad_token_id": tokenizer.eos_token_id,
                "streamer": streamer,
                **kwargs
            }

            # Run generation in thread
            thread = Thread(target=model_obj.generate, kwargs=generation_kwargs)
            thread.start()

            # Stream tokens
            for token in streamer:
                yield token

            # Wait for thread to complete
            thread.join()

        except Exception as e:
            self._handle_error(e, "generate_stream")
            raise

    async def chat(
        self,
        messages: List[Message],
        model: str = "gpt2",
        generation_config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> GenerationResult:
        """
        Chat completion using HuggingFace

        Args:
            messages: List of chat messages
            model: HuggingFace model name
            generation_config: Generation parameters
            **kwargs: Additional generation arguments

        Returns:
            GenerationResult with response and metadata
        """
        # Convert messages to a single prompt
        prompt = self._messages_to_prompt(messages)

        # Use generate method
        return await self.generate(prompt, model, generation_config, **kwargs)

    async def chat_stream(
        self,
        messages: List[Message],
        model: str = "gpt2",
        generation_config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Chat completion (streaming)

        Args:
            messages: List of chat messages
            model: HuggingFace model name
            generation_config: Generation parameters
            **kwargs: Additional generation arguments

        Yields:
            Text chunks as they are generated
        """
        # Convert messages to a single prompt
        prompt = self._messages_to_prompt(messages)

        # Use generate_stream method
        async for chunk in self.generate_stream(prompt, model, generation_config, **kwargs):
            yield chunk

    def _messages_to_prompt(self, messages: List[Message]) -> str:
        """
        Convert chat messages to a single prompt string

        Args:
            messages: List of chat messages

        Returns:
            Formatted prompt string
        """
        prompt_parts = []

        for msg in messages:
            if msg.role == "system":
                prompt_parts.append(f"System: {msg.content}")
            elif msg.role == "user":
                prompt_parts.append(f"User: {msg.content}")
            elif msg.role == "assistant":
                prompt_parts.append(f"Assistant: {msg.content}")

        prompt_parts.append("Assistant:")
        return "\n".join(prompt_parts)

    def calculate_cost(
        self,
        tokens_input: int,
        tokens_output: int,
        model: str
    ) -> float:
        """
        Calculate cost for HuggingFace usage (always free for local)

        Args:
            tokens_input: Number of input tokens
            tokens_output: Number of output tokens
            model: Model name

        Returns:
            Cost in USD (always 0.0 for local models)
        """
        return 0.0

    async def list_models(self) -> List[str]:
        """
        List commonly used HuggingFace models

        Returns:
            List of model names
        """
        # Return a curated list of popular models
        return [
            "gpt2",
            "gpt2-medium",
            "gpt2-large",
            "facebook/opt-1.3b",
            "facebook/opt-2.7b",
            "meta-llama/Llama-2-7b-chat-hf",
            "mistralai/Mistral-7B-Instruct-v0.1",
            "microsoft/phi-2",
            "google/flan-t5-base",
            "google/flan-t5-large",
        ]

    async def check_availability(self) -> bool:
        """
        Check if HuggingFace transformers is available

        Returns:
            True if transformers is installed, False otherwise
        """
        try:
            import transformers
            return True
        except ImportError:
            self.logger.warning("transformers package not installed")
            return False

    def unload_model(self, model: str):
        """
        Unload a model from memory

        Args:
            model: Model name to unload
        """
        if model in self.loaded_models:
            del self.loaded_models[model]
            del self.loaded_tokenizers[model]

            # Free GPU memory if using CUDA
            if self.device == "cuda":
                torch.cuda.empty_cache()

            self.logger.info(f"Model unloaded: {model}")

    def unload_all_models(self):
        """Unload all models from memory"""
        for model in list(self.loaded_models.keys()):
            self.unload_model(model)

    def get_model_info(self, model: str) -> Dict[str, Any]:
        """
        Get information about a loaded model

        Args:
            model: Model name

        Returns:
            Dictionary with model information
        """
        if model not in self.loaded_models:
            return {"loaded": False}

        model_obj = self.loaded_models[model]
        return {
            "loaded": True,
            "device": str(model_obj.device),
            "num_parameters": sum(p.numel() for p in model_obj.parameters()),
            "dtype": str(model_obj.dtype)
        }
