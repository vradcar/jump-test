"""
AI Client — unified wrapper for OpenAI and Google Gemini.

Provides a single `chat()` function that works with either provider
based on the AI_PROVIDER setting in .env.
"""

import time
import re
from rich.console import Console

import config

console = Console()

MAX_RETRIES = 3


def chat(system_prompt: str, user_message: str, temperature: float = 0.2) -> str:
    """
    Send a system + user message to the configured AI provider.
    Returns the assistant's response text.
    """
    provider = config.AI_PROVIDER

    if provider == "groq":
        return _groq_chat(system_prompt, user_message, temperature)
    elif provider == "gemini":
        return _gemini_chat(system_prompt, user_message, temperature)
    elif provider == "openai":
        return _openai_chat(system_prompt, user_message, temperature)
    else:
        raise ValueError(f"Unknown AI_PROVIDER: '{provider}'. Use 'groq', 'gemini', or 'openai'.")


def _groq_chat(system_prompt: str, user_message: str, temperature: float) -> str:
    """Call Groq API (free, fast — uses Llama/Mixtral models)."""
    from groq import Groq

    client = Groq(api_key=config.GROQ_API_KEY)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=config.GROQ_MODEL,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
            )
            return response.choices[0].message.content.strip()
        except Exception as exc:
            if "rate_limit" in str(exc).lower() or "429" in str(exc):
                wait = 30
                match = re.search(r"try again in (\d+\.?\d*)", str(exc), re.IGNORECASE)
                if match:
                    wait = int(float(match.group(1))) + 2
                if attempt < MAX_RETRIES:
                    console.print(
                        f"  [yellow]Rate limited — waiting {wait}s "
                        f"(attempt {attempt}/{MAX_RETRIES}) …[/yellow]"
                    )
                    time.sleep(wait)
                else:
                    raise
            else:
                raise


def _gemini_chat(system_prompt: str, user_message: str, temperature: float) -> str:
    """Call Google Gemini API with automatic retry on rate limits."""
    import google.generativeai as genai
    from google.api_core.exceptions import ResourceExhausted

    genai.configure(api_key=config.GEMINI_API_KEY)

    model = genai.GenerativeModel(
        model_name=config.GEMINI_MODEL,
        system_instruction=system_prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=temperature,
        ),
    )

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = model.generate_content(user_message)
            return response.text.strip()
        except ResourceExhausted as exc:
            # Extract retry delay from error message if available
            wait = 60  # default wait
            match = re.search(r"retry in (\d+\.?\d*)", str(exc), re.IGNORECASE)
            if match:
                wait = int(float(match.group(1))) + 5  # add 5s buffer

            if attempt < MAX_RETRIES:
                console.print(
                    f"  [yellow]Rate limited — waiting {wait}s "
                    f"(attempt {attempt}/{MAX_RETRIES}) …[/yellow]"
                )
                time.sleep(wait)
            else:
                console.print("  [red]Rate limit persists after retries.[/red]")
                raise


def _openai_chat(system_prompt: str, user_message: str, temperature: float) -> str:
    """Call OpenAI API."""
    from openai import OpenAI

    client = OpenAI(api_key=config.OPENAI_API_KEY)

    response = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )

    return response.choices[0].message.content.strip()
