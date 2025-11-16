#!/usr/bin/env python3
"""
Test script for MegaLLM API integration

This script verifies that your MegaLLM API configuration is working correctly.
Run this before using the full chatPDF application to ensure everything is set up.

Usage:
    python test_megallm.py

Requirements:
    - MEGALLM_API_KEY set in .env file
    - aiohttp installed (pip install aiohttp)
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from src.providers.generic_api_provider import GenericAPIProvider, APIConfig, get_predefined_apis


async def test_megallm_api():
    """Test MegaLLM API connection and all 3 models"""

    print("=" * 70)
    print("MegaLLM API Integration Test")
    print("=" * 70)
    print()

    # Load environment
    load_dotenv()

    # Check API key
    api_key = os.getenv("MEGALLM_API_KEY")
    if not api_key:
        print("❌ ERROR: MEGALLM_API_KEY not found in environment")
        print()
        print("Please:")
        print("1. Copy .env.example to .env")
        print("2. Add your MegaLLM API key to .env")
        print("3. Run this script again")
        return False

    print(f"✅ API Key found: {api_key[:10]}...{api_key[-4:]}")
    print()

    # Get predefined configs
    predefined = get_predefined_apis()

    # Configure the 3 MegaLLM models
    models_to_test = [
        "MegaLLM GPT-5 Mini",
        "MegaLLM Claude Haiku 4.5",
        "MegaLLM Gemini 2.5 Flash"
    ]

    configs = []
    for model_name in models_to_test:
        if model_name in predefined:
            config = predefined[model_name]
            config.api_key = api_key
            configs.append(config)

    # Initialize provider
    print(f"Initializing Generic API Provider with {len(configs)} models...")
    provider = GenericAPIProvider(configs)
    print("✅ Provider initialized")
    print()

    # Test each model
    test_prompt = "Hello! Please respond with just 'Hi' to confirm you're working."

    all_passed = True
    for config in configs:
        print("-" * 70)
        print(f"Testing: {config.name}")
        print(f"  Model ID: {config.model}")
        print(f"  Base URL: {config.base_url}")
        print(f"  Format: {config.api_format}")
        print()

        try:
            print(f"  Sending test request...")
            response = await provider.generate(
                prompt=test_prompt,
                model=config.name,
                temperature=0.7,
                max_tokens=50
            )

            print(f"  ✅ SUCCESS!")
            print(f"  Response: {response[:100]}")
            print()

        except Exception as e:
            print(f"  ❌ FAILED: {str(e)}")
            print()
            all_passed = False

            # Provide troubleshooting hints
            if "401" in str(e) or "Unauthorized" in str(e):
                print("  💡 Hint: API key may be invalid. Check your MegaLLM dashboard.")
            elif "404" in str(e) or "not found" in str(e):
                print("  💡 Hint: Model ID may be incorrect. Verify at https://megallm.io/dashboard/models")
            elif "connection" in str(e).lower():
                print("  💡 Hint: Cannot reach MegaLLM API. Check your internet connection.")
            print()

    # Cleanup
    await provider.close()

    # Summary
    print("=" * 70)
    if all_passed:
        print("✅ All tests PASSED! MegaLLM integration is working correctly.")
        print()
        print("You can now use these models in the chatPDF application:")
        for config in configs:
            print(f"  - {config.name}")
    else:
        print("❌ Some tests FAILED. Please fix the errors above before using chatPDF.")
        print()
        print("Common issues:")
        print("  1. Invalid API key - Get one from https://megallm.io/dashboard")
        print("  2. Wrong model IDs - Verify at https://megallm.io/dashboard/models")
        print("  3. No internet - Check your connection")
        print("  4. API quota exceeded - Check your MegaLLM usage limits")
    print("=" * 70)

    return all_passed


async def test_streaming():
    """Test streaming responses"""
    load_dotenv()

    api_key = os.getenv("MEGALLM_API_KEY")
    if not api_key:
        return

    print()
    print("=" * 70)
    print("Testing Streaming Response (Optional)")
    print("=" * 70)
    print()

    # Use fastest model for streaming test
    config = APIConfig(
        name="MegaLLM Gemini 2.5 Flash",
        api_key=api_key,
        base_url="https://ai.megallm.io/v1",
        model="gemini-2-5-flash",
        api_format="openai"
    )

    provider = GenericAPIProvider([config])

    try:
        print("Streaming response from Gemini 2.5 Flash...")
        print("Response: ", end="", flush=True)

        async for chunk in provider.generate_stream(
            prompt="Count from 1 to 5, one number per line.",
            model="MegaLLM Gemini 2.5 Flash",
            temperature=0.7,
            max_tokens=100
        ):
            print(chunk, end="", flush=True)

        print()
        print()
        print("✅ Streaming test passed!")

    except Exception as e:
        print(f"\n❌ Streaming failed: {e}")

    await provider.close()


def main():
    """Main test function"""
    print()
    print("🚀 Starting MegaLLM Integration Tests")
    print()

    # Run basic tests
    success = asyncio.run(test_megallm_api())

    # If basic tests pass, offer streaming test
    if success:
        print()
        response = input("Run streaming test? (y/n): ").strip().lower()
        if response == 'y':
            asyncio.run(test_streaming())

    print()
    print("Tests complete!")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
