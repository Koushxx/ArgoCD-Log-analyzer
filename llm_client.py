"""
LLM Client — handles communication with the Bosch Azure OpenAI API.
Uses api-key header and Azure deployment URL format.
"""

import requests
from config import get_api_key, LLM_API_URL

# Proxy strategies in order of preference:
# 1. Local auth proxy (CNTLM/Px) — handles NTLM auth transparently
# 2. Direct connection — works on some networks
_PROXY_STRATEGIES = [
    {"http": "http://localhost:3128", "https": "http://localhost:3128"},
    {"http": None, "https": None},
]


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

    last_err = None
    for proxies in _PROXY_STRATEGIES:
        try:
            resp = requests.post(
                LLM_API_URL, headers=headers, json=payload,
                timeout=120, proxies=proxies,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except (requests.exceptions.ProxyError,
                requests.exceptions.ConnectionError) as e:
            last_err = e
            continue

    raise ConnectionError(
        "Could not reach Bosch LLM API. "
        "Please ensure your local proxy (CNTLM/Px) is running on port 3128, "
        "or connect to a network that can reach aoai-farm.bosch-temp.com directly."
    ) from last_err
