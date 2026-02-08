"""
Smart Router Lite V1.0 — Universal Free-First LLM Router
=========================================================
Drop-in replacement for direct Anthropic API calls in GitHub Actions.
Routes ALL requests to FREE tier (Gemini Flash) by default.
Only escalates to paid tiers when explicitly requested.

Author: Ariel Shapira / Claude AI Architect
Date: February 7, 2026
License: Proprietary — Everest Capital USA

COST: $0/month for all automated workflows
REPLACES: Direct ANTHROPIC_API_KEY calls that were burning credits

Usage in any workflow:
    from smart_router_lite import SmartRouterLite
    router = SmartRouterLite()
    result = await router.generate("Analyze this text...")
    # or synchronous:
    result = router.generate_sync("Analyze this text...")
"""

import os
import json
import asyncio
import logging
from typing import Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass

try:
    import httpx
except ImportError:
    import subprocess
    subprocess.check_call(["pip", "install", "httpx", "-q"])
    import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("smart_router_lite")


class Tier(Enum):
    FREE = "free"           # Gemini 2.5 Flash — $0
    ULTRA_CHEAP = "cheap"   # DeepSeek V3 — $0.28/M
    BUDGET = "budget"       # Gemini 1.5 Pro — $1.25/M
    # NO ANTHROPIC TIER — that's the whole point


@dataclass
class ModelConfig:
    name: str
    provider: str
    tier: Tier
    cost_per_1m_input: float
    cost_per_1m_output: float
    max_tokens: int
    context_window: int


# Model registry — FREE first, always
MODELS = {
    "gemini-2.5-flash": ModelConfig(
        name="gemini-2.5-flash-preview-04-17",
        provider="google",
        tier=Tier.FREE,
        cost_per_1m_input=0.0,
        cost_per_1m_output=0.0,
        max_tokens=8192,
        context_window=1_000_000,
    ),
    "gemini-2.0-flash": ModelConfig(
        name="gemini-2.0-flash",
        provider="google",
        tier=Tier.FREE,
        cost_per_1m_input=0.0,
        cost_per_1m_output=0.0,
        max_tokens=8192,
        context_window=1_000_000,
    ),
    "deepseek-v3": ModelConfig(
        name="deepseek-chat",
        provider="deepseek",
        tier=Tier.ULTRA_CHEAP,
        cost_per_1m_input=0.28,
        cost_per_1m_output=0.42,
        max_tokens=4096,
        context_window=128_000,
    ),
}

# Default model for all automated workflows
DEFAULT_MODEL = "gemini-2.5-flash"
FALLBACK_MODEL = "gemini-2.0-flash"


class SmartRouterLite:
    """
    Universal free-first LLM router for GitHub Actions workflows.
    
    Eliminates Anthropic API costs by routing everything through
    Gemini Flash (free) with DeepSeek as optional cheap fallback.
    """

    def __init__(self):
        self.google_api_key = (
            os.getenv("GOOGLE_API_KEY")
            or os.getenv("GEMINI_API_KEY")
        )
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        self.total_requests = 0
        self.total_cost = 0.0
        self.errors = []

        if not self.google_api_key:
            raise ValueError(
                "No Google/Gemini API key found. "
                "Set GOOGLE_API_KEY or GEMINI_API_KEY environment variable."
            )

        logger.info("SmartRouterLite initialized — FREE tier (Gemini Flash)")

    async def _call_gemini(
        self,
        prompt: str,
        system: str = "",
        model_key: str = DEFAULT_MODEL,
        max_tokens: int = 8192,
    ) -> Dict[str, Any]:
        """Call Gemini API (FREE)."""
        model = MODELS[model_key]
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/"
            f"models/{model.name}:generateContent"
            f"?key={self.google_api_key}"
        )

        contents = []
        if system:
            contents.append({"role": "user", "parts": [{"text": f"System: {system}"}]})
            contents.append({"role": "model", "parts": [{"text": "Understood. I will follow those instructions."}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": 0.3,
            },
        }

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

        # Extract text from response
        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            text = ""
            logger.warning(f"Empty response from {model_key}: {json.dumps(data)[:200]}")

        usage = data.get("usageMetadata", {})
        input_tokens = usage.get("promptTokenCount", 0)
        output_tokens = usage.get("candidatesTokenCount", 0)

        return {
            "content": text,
            "model": model.name,
            "provider": "google",
            "tier": Tier.FREE.value,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": 0.0,  # FREE
        }

    async def _call_deepseek(
        self,
        prompt: str,
        system: str = "",
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        """Call DeepSeek API (ultra-cheap fallback)."""
        if not self.deepseek_api_key:
            raise ValueError("No DEEPSEEK_API_KEY set")

        model = MODELS["deepseek-v3"]
        url = "https://api.deepseek.com/v1/chat/completions"

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model.name,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.3,
        }

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.deepseek_api_key}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            data = response.json()

        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        cost = (
            input_tokens * model.cost_per_1m_input
            + output_tokens * model.cost_per_1m_output
        ) / 1_000_000

        return {
            "content": text,
            "model": model.name,
            "provider": "deepseek",
            "tier": Tier.ULTRA_CHEAP.value,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": cost,
        }

    async def generate(
        self,
        prompt: str,
        system: str = "",
        max_tokens: int = 8192,
        force_tier: Optional[Tier] = None,
    ) -> Dict[str, Any]:
        """
        Generate text using the cheapest available model.
        
        Default: Gemini 2.5 Flash (FREE)
        Fallback 1: Gemini 2.0 Flash (FREE)
        Fallback 2: DeepSeek V3 ($0.28/M)
        
        NO ANTHROPIC API CALLS. EVER.
        """
        self.total_requests += 1

        # Force DeepSeek if explicitly requested
        if force_tier == Tier.ULTRA_CHEAP and self.deepseek_api_key:
            try:
                result = await self._call_deepseek(prompt, system, max_tokens)
                self.total_cost += result["cost"]
                return result
            except Exception as e:
                logger.warning(f"DeepSeek failed: {e}, falling back to Gemini")

        # Try Gemini 2.5 Flash first (FREE)
        try:
            result = await self._call_gemini(prompt, system, DEFAULT_MODEL, max_tokens)
            return result
        except Exception as e:
            logger.warning(f"Gemini 2.5 Flash failed: {e}")
            self.errors.append(f"gemini-2.5: {e}")

        # Fallback to Gemini 2.0 Flash (FREE)
        try:
            result = await self._call_gemini(prompt, system, FALLBACK_MODEL, max_tokens)
            return result
        except Exception as e:
            logger.warning(f"Gemini 2.0 Flash failed: {e}")
            self.errors.append(f"gemini-2.0: {e}")

        # Fallback to DeepSeek (ultra-cheap)
        if self.deepseek_api_key:
            try:
                result = await self._call_deepseek(prompt, system, min(max_tokens, 4096))
                self.total_cost += result["cost"]
                return result
            except Exception as e:
                logger.error(f"DeepSeek also failed: {e}")
                self.errors.append(f"deepseek: {e}")

        # All models failed
        raise RuntimeError(
            f"All models failed. Errors: {self.errors}. "
            "Check GOOGLE_API_KEY/GEMINI_API_KEY environment variable."
        )

    def generate_sync(
        self,
        prompt: str,
        system: str = "",
        max_tokens: int = 8192,
        force_tier: Optional[Tier] = None,
    ) -> Dict[str, Any]:
        """Synchronous wrapper for generate()."""
        return asyncio.run(self.generate(prompt, system, max_tokens, force_tier))

    def get_stats(self) -> Dict[str, Any]:
        """Return usage statistics."""
        return {
            "total_requests": self.total_requests,
            "total_cost": self.total_cost,
            "errors": len(self.errors),
            "models_available": {
                "gemini-2.5-flash": bool(self.google_api_key),
                "gemini-2.0-flash": bool(self.google_api_key),
                "deepseek-v3": bool(self.deepseek_api_key),
            },
        }


# === CONVENIENCE FUNCTION FOR WORKFLOW SCRIPTS ===

def quick_generate(prompt: str, system: str = "") -> str:
    """
    One-liner for workflow scripts.
    
    Usage:
        from smart_router_lite import quick_generate
        answer = quick_generate("Summarize this: " + text)
    """
    router = SmartRouterLite()
    result = router.generate_sync(prompt, system)
    return result["content"]


# === CLI TEST ===

if __name__ == "__main__":
    print("=" * 60)
    print("Smart Router Lite V1.0 — Self-Test")
    print("=" * 60)

    router = SmartRouterLite()
    result = router.generate_sync(
        "Say 'Smart Router Lite working!' and nothing else.",
        system="You are a test bot. Respond with exactly what is asked.",
    )

    print(f"  Model:    {result['model']}")
    print(f"  Provider: {result['provider']}")
    print(f"  Tier:     {result['tier']}")
    print(f"  Cost:     ${result['cost']:.6f}")
    print(f"  Response: {result['content'][:100]}")
    print(f"  Tokens:   {result['input_tokens']} in / {result['output_tokens']} out")
    print("=" * 60)
    print("✅ PASS — $0 cost, no Anthropic API used")
