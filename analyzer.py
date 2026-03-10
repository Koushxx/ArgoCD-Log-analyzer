"""
Log Analyzer — classifies log type and orchestrates LLM analysis.
"""

import re
from config import MAX_LOG_LINES
from llm_client import call_llm
from prompts import SYSTEM_PROMPT, SYSTEM_PROMPT_HEALTHY, build_user_prompt


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

# Patterns that indicate something is wrong in the logs
ERROR_INDICATORS = [
    r"\bERR(OR)?\b",
    r"\bFATAL\b",
    r"\bCRIT(ICAL)?\b",
    r"\bPANIC\b",
    r"\bFAIL(ED|URE)?\b",
    r"\bException\b",
    r"\bTraceback\b",
    r"\bCrashLoopBackOff\b",
    r"\bOOMKilled\b",
    r"\bImagePullBackOff\b",
    r"\bErrImagePull\b",
    r"\bBackoff\b",
    r"\bSyncError\b",
    r"\bComparisonError\b",
    r"\bOutOfSync\b",
    r"\bUnhealthy\b",
    r"\bDegraded\b",
    r"\bNot\s*Ready\b",
    r"\bfailed\b",
    r"\bconnection\s*refused\b",
    r"\bpermission\s*denied\b",
    r"\bstack\s*trace\b",
    r"\bsegmentation\s*fault\b",
    r"\bkilled\b",
    r"\bexit\s*code\s*[1-9]",
    r"\bWARN(ING)?\b",
]


def detect_log_health(log_text: str) -> str:
    """Return 'error' if logs contain problems, 'healthy' otherwise."""
    error_count = 0
    for pat in ERROR_INDICATORS:
        matches = re.findall(pat, log_text, re.IGNORECASE)
        error_count += len(matches)
    # Threshold: a few WARNINGs alone don't make it unhealthy
    # but any ERROR/FATAL/Exception does
    severe = [
        r"\bERR(OR)?\b", r"\bFATAL\b", r"\bCRIT(ICAL)?\b", r"\bPANIC\b",
        r"\bException\b", r"\bTraceback\b", r"\bCrashLoopBackOff\b",
        r"\bOOMKilled\b", r"\bSyncError\b", r"\bFAIL(ED|URE)?\b",
    ]
    for pat in severe:
        if re.search(pat, log_text, re.IGNORECASE):
            return "error"
    if error_count >= 3:
        return "error"
    return "healthy"


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
    2. Detect log health (error vs healthy).
    3. Truncate if needed.
    4. Call LLM with the appropriate prompt.
    5. Return formatted analysis.
    """
    log_type = log_type_override or detect_log_type(log_text)
    health = detect_log_health(log_text)
    is_healthy = health == "healthy"
    trimmed = truncate_log(log_text)
    user_prompt = build_user_prompt(log_type, trimmed, is_healthy=is_healthy)
    sys_prompt = SYSTEM_PROMPT_HEALTHY if is_healthy else SYSTEM_PROMPT

    analysis = call_llm(sys_prompt, user_prompt)

    status = "✅ HEALTHY" if is_healthy else "❌ ERRORS DETECTED"
    header = (
        f"{'=' * 60}\n"
        f"  LOG TYPE  ➜  {log_type}   |   STATUS  ➜  {status}\n"
        f"{'=' * 60}\n"
    )
    return header + "\n" + analysis
