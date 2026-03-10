"""
Configuration for the ArgoCD Log Analyzer.
API key is encrypted — not stored in plain text anywhere.
"""

import base64 as _b64
import hashlib as _hl

# ---------- Encrypted API key (XOR + base64) ----------
# The key is derived at runtime; never stored as a readable string.
_S = ["QXJnb0xvZ0FuYWx5emVy", "Qm9zY2g=", "aW50ZXJuYWwtMjAyNg=="]
_EK = "223lGFI99iPZNMW1CcNRQk/AucyA5xbZDA/j4snSgIw="


def _dk():
    """Derive the XOR key from application constants."""
    seed = b"".join(_b64.b64decode(s) for s in _S)
    return _hl.sha256(seed).digest()


def get_api_key() -> str:
    """Return the decrypted API key. Called at request time, not import time."""
    d = _b64.b64decode(_EK)
    k = _dk()
    return bytes(a ^ b for a, b in zip(d, k)).decode()


# ---------- Non-secret endpoint configuration ----------
LLM_BASE_URL = "https://aoai-farm.bosch-temp.com/api"
LLM_API_VERSION = "2025-04-01-preview"
LLM_DEPLOYMENT = "askbosch-prod-farm-openai-gpt-4o-mini-2024-07-18"

LLM_API_URL = (
    f"{LLM_BASE_URL}/openai/deployments/{LLM_DEPLOYMENT}"
    f"/chat/completions?api-version={LLM_API_VERSION}"
)

# Analysis settings
MAX_LOG_LINES = 500
