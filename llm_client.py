"""
LLM Client — handles communication with the Bosch Azure OpenAI API.
Uses api-key header and Azure deployment URL format.
"""

import requests
from config import get_api_key, LLM_API_URL


def call_llm(system_prompt: str, user_prompt: str) -> str:
    """Send a prompt to the Bosch LLM and return the assistant response."""

    api_key = get_api_key()
    if not api_key:
        raise EnvironmentError("API key could not be loaded.")

    headers = {
        "Content-Type": "application/json",
        "api-key": api_key,
    }

    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,  # low temp for deterministic, factual analysis
    }

    # Bypass any system/corporate proxy for the Bosch API endpoint
    resp = requests.post(
        LLM_API_URL, headers=headers, json=payload, timeout=120,
        proxies={"http": None, "https": None},
    )
    resp.raise_for_status()

    data = resp.json()
    return data["choices"][0]["message"]["content"]
