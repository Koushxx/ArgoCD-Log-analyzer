"""
Log Analyzer — classifies log type and orchestrates LLM analysis.
"""

import re
from config import MAX_LOG_LINES
from llm_client import call_llm
from prompts import SYSTEM_PROMPT, build_user_prompt


# ---------------------------------------------------------------------------
# Log-type auto-detection
# ---------------------------------------------------------------------------

ARGOCD_PATTERNS = [
    r"argocd",
    r"application\.argoproj\.io",
    r"sync\s*(status|failed|succeeded|running)",
    r"ComparisonError",
    r"health\s*status",
    r"OutOfSync",
    r"SyncError",
    r"argocd-application-controller",
    r"argocd-server",
    r"argocd-repo-server",
]

POD_PATTERNS = [
    r"CrashLoopBackOff",
    r"OOMKilled",
    r"ImagePullBackOff",
    r"ErrImagePull",
    r"Pending",
    r"Back-off\s+restarting",
    r"Liveness\s+probe\s+failed",
    r"Readiness\s+probe\s+failed",
    r"kubectl",
    r"kubelet",
    r"FailedScheduling",
    r"Insufficient\s+(cpu|memory)",
    r"node\s+(NotReady|pressure)",
]

APPLICATION_PATTERNS = [
    r"Exception",
    r"Traceback",
    r"ERROR",
    r"FATAL",
    r"NullPointerException",
    r"ConnectionRefused",
    r"timeout",
    r"stacktrace",
    r"failed to connect",
    r"database.*error",
]


def detect_log_type(log_text: str) -> str:
    """Return the most likely log category: argocd, pod, or application."""

    scores = {"ArgoCD": 0, "Pod / Kubernetes": 0, "Application": 0}

    for pat in ARGOCD_PATTERNS:
        if re.search(pat, log_text, re.IGNORECASE):
            scores["ArgoCD"] += 1

    for pat in POD_PATTERNS:
        if re.search(pat, log_text, re.IGNORECASE):
            scores["Pod / Kubernetes"] += 1

    for pat in APPLICATION_PATTERNS:
        if re.search(pat, log_text, re.IGNORECASE):
            scores["Application"] += 1

    # pick highest; default to "Unknown / Mixed"
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "Unknown / Mixed"
    return best


def truncate_log(log_text: str) -> str:
    """Keep the log within a reasonable size for the LLM context window."""
    lines = log_text.splitlines()
    if len(lines) <= MAX_LOG_LINES:
        return log_text
    # Keep first and last portions so the LLM sees the start and end of the log
    half = MAX_LOG_LINES // 2
    kept = lines[:half] + [f"\n... ({len(lines) - MAX_LOG_LINES} lines truncated) ...\n"] + lines[-half:]
    return "\n".join(kept)


def analyze_log(log_text: str, log_type_override: str | None = None) -> str:
    """
    Main entry point.
    1. Auto-detect (or accept override) log type.
    2. Truncate if needed.
    3. Call LLM.
    4. Return formatted analysis.
    """
    log_type = log_type_override or detect_log_type(log_text)
    trimmed = truncate_log(log_text)
    user_prompt = build_user_prompt(log_type, trimmed)

    analysis = call_llm(SYSTEM_PROMPT, user_prompt)

    header = (
        f"{'=' * 60}\n"
        f"  LOG TYPE DETECTED  ➜  {log_type}\n"
        f"{'=' * 60}\n"
    )
    return header + "\n" + analysis
