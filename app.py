"""
ArgoCD Log Analyzer — Web UI (Streamlit)
========================================
Run with:  streamlit run app.py
"""

import streamlit as st
import os
import sys

# Ensure imports work when running from the project directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analyzer import analyze_log, detect_log_type

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Argo Log Analyzer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# ArgoCD-themed CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    /* ── ArgoCD Color Palette ─────────────────────────────────
       Background:  #0d1117 (deep navy)
       Surface:     #161b22 (card bg)
       Border:      #21262d (subtle dividers)
       Primary:     #0dadea (ArgoCD teal/cyan)
       Success:     #18be94 (synced green)
       Warning:     #f4c030 (out-of-sync yellow)
       Danger:      #e96d76 (degraded red)
       Text:        #c9d1d9 (light gray)
       Muted:       #8b949e (secondary text)
    ──────────────────────────────────────────────────────── */

    /* Root overrides */
    :root {
        --argo-bg: #0d1117;
        --argo-surface: #161b22;
        --argo-border: #21262d;
        --argo-cyan: #0dadea;
        --argo-green: #18be94;
        --argo-yellow: #f4c030;
        --argo-red: #e96d76;
        --argo-orange: #e8863a;
        --argo-text: #c9d1d9;
        --argo-muted: #8b949e;
    }

    /* App background */
    .stApp {
        background: var(--argo-bg) !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #010409 !important;
        border-right: 1px solid var(--argo-border) !important;
    }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown li {
        color: var(--argo-muted) !important;
        font-size: 13px;
    }
    section[data-testid="stSidebar"] h3 {
        color: var(--argo-cyan) !important;
        font-size: 14px !important;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-top: 20px !important;
    }

    /* All headings */
    h1 { color: #ffffff !important; }
    h2 { color: var(--argo-cyan) !important; }
    h3 { color: var(--argo-text) !important; }
    p, li, span { color: var(--argo-text); }

    /* Text area */
    .stTextArea textarea {
        background: var(--argo-surface) !important;
        border: 1px solid var(--argo-border) !important;
        color: var(--argo-text) !important;
        border-radius: 8px !important;
        font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace !important;
        font-size: 13px !important;
    }
    .stTextArea textarea:focus {
        border-color: var(--argo-cyan) !important;
        box-shadow: 0 0 0 2px rgba(13,173,234,0.15) !important;
    }

    /* Primary button — ArgoCD cyan */
    .stButton > button[kind="primary"],
    .stButton > button[data-testid="stBaseButton-primary"] {
        background: linear-gradient(135deg, #0dadea, #0995c7) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        padding: 12px 24px !important;
        letter-spacing: 0.5px;
        transition: all 0.2s ease;
    }
    .stButton > button[kind="primary"]:hover,
    .stButton > button[data-testid="stBaseButton-primary"]:hover {
        background: linear-gradient(135deg, #0995c7, #0780ab) !important;
        box-shadow: 0 4px 20px rgba(13,173,234,0.3) !important;
    }

    /* Secondary buttons */
    .stDownloadButton > button {
        background: var(--argo-surface) !important;
        color: var(--argo-cyan) !important;
        border: 1px solid var(--argo-border) !important;
        border-radius: 8px !important;
    }
    .stDownloadButton > button:hover {
        border-color: var(--argo-cyan) !important;
        background: rgba(13,173,234,0.08) !important;
    }

    /* Select box */
    .stSelectbox > div > div {
        background: var(--argo-surface) !important;
        border: 1px solid var(--argo-border) !important;
        border-radius: 8px !important;
    }

    /* File uploader */
    .stFileUploader > div {
        background: var(--argo-surface) !important;
        border: 1px dashed var(--argo-border) !important;
        border-radius: 8px !important;
    }

    /* Radio buttons */
    .stRadio > div { gap: 12px; }
    .stRadio label {
        background: var(--argo-surface) !important;
        padding: 8px 18px !important;
        border-radius: 20px !important;
        border: 1px solid var(--argo-border) !important;
        transition: all 0.2s ease;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background: var(--argo-surface) !important;
        border-radius: 8px !important;
        color: var(--argo-text) !important;
    }

    /* Divider line */
    hr { border-color: var(--argo-border) !important; }

    /* ── Custom components ───────────────────────────────── */

    /* Header bar */
    .argo-header {
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 20px 0 12px 0;
        border-bottom: 1px solid var(--argo-border);
        margin-bottom: 28px;
    }
    .argo-header-icon {
        width: 48px;
        height: 48px;
        background: linear-gradient(135deg, #0dadea22, #18be9422);
        border: 1px solid var(--argo-cyan);
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
    }
    .argo-header h1 {
        margin: 0 !important;
        font-size: 28px !important;
        font-weight: 700 !important;
        background: linear-gradient(90deg, #0dadea, #18be94);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .argo-header-sub {
        color: var(--argo-muted);
        font-size: 13px;
        margin: 2px 0 0 0;
        letter-spacing: 1px;
    }

    /* Status badges (ArgoCD style chips) */
    .argo-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 5px 14px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }
    .argo-badge-argocd {
        background: rgba(13,173,234,0.12);
        border: 1px solid var(--argo-cyan);
        color: var(--argo-cyan);
    }
    .argo-badge-pod {
        background: rgba(24,190,148,0.12);
        border: 1px solid var(--argo-green);
        color: var(--argo-green);
    }
    .argo-badge-app {
        background: rgba(232,134,58,0.12);
        border: 1px solid var(--argo-orange);
        color: var(--argo-orange);
    }
    .argo-badge-unknown {
        background: rgba(139,148,158,0.12);
        border: 1px solid var(--argo-muted);
        color: var(--argo-muted);
    }
    .argo-badge-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
    }

    /* Analysis result cards */
    .argo-result-card {
        background: var(--argo-surface);
        border: 1px solid var(--argo-border);
        border-radius: 8px;
        padding: 24px 28px;
        margin: 16px 0;
        border-left: 3px solid var(--argo-cyan);
    }

    /* Info cards (sidebar) */
    .argo-info-card {
        background: rgba(13,173,234,0.05);
        border: 1px solid var(--argo-border);
        border-radius: 8px;
        padding: 14px;
        margin: 8px 0;
    }
    .argo-info-card code {
        color: var(--argo-cyan) !important;
        background: rgba(13,173,234,0.1) !important;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 12px;
    }

    /* Stat row */
    .argo-stats {
        display: flex;
        gap: 16px;
        margin: 20px 0;
    }
    .argo-stat {
        flex: 1;
        background: var(--argo-surface);
        border: 1px solid var(--argo-border);
        border-radius: 8px;
        padding: 16px 20px;
        text-align: center;
    }
    .argo-stat-value {
        font-size: 24px;
        font-weight: 700;
        color: var(--argo-cyan);
    }
    .argo-stat-label {
        font-size: 11px;
        color: var(--argo-muted);
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 4px;
    }

    /* Logo in sidebar */
    .sidebar-logo {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 16px 0 8px 0;
    }
    .sidebar-logo svg {
        width: 160px;
        height: 160px;
    }

    /* Spinner */
    .stSpinner > div > div {
        border-top-color: var(--argo-cyan) !important;
    }

    /* Code blocks */
    .stCodeBlock, pre, code {
        background: #0d1117 !important;
        border: 1px solid var(--argo-border) !important;
        border-radius: 6px !important;
    }

    /* Footer */
    .argo-footer {
        text-align: center;
        color: var(--argo-muted);
        font-size: 11px;
        margin-top: 60px;
        padding: 20px;
        border-top: 1px solid var(--argo-border);
        letter-spacing: 0.5px;
    }
    .argo-footer a {
        color: var(--argo-cyan);
        text-decoration: none;
    }

    /* Smooth scrollbar */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: var(--argo-bg); }
    ::-webkit-scrollbar-thumb { background: var(--argo-border); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--argo-muted); }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    # Logo
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.svg")
    if os.path.exists(logo_path):
        with open(logo_path, "r") as f:
            svg_content = f.read()
        st.markdown(
            f'<div class="sidebar-logo">{svg_content}</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    st.markdown("### ⚙️ Configuration")

    log_type_choice = st.selectbox(
        "Log Type Detection",
        ["Auto-Detect", "ArgoCD", "Pod / Kubernetes", "Application"],
        help="Auto-Detect classifies the log automatically based on keywords",
    )

    st.markdown("---")

    st.markdown("### 📖 Getting Started")
    st.markdown("""
    <div class="argo-info-card">
        <strong style="color: #c9d1d9;">1.</strong> Paste your logs or upload a file<br>
        <strong style="color: #c9d1d9;">2.</strong> Select log type or use Auto-Detect<br>
        <strong style="color: #c9d1d9;">3.</strong> Click <strong style="color: #0dadea;">Analyze</strong><br>
        <strong style="color: #c9d1d9;">4.</strong> Get a plain-English diagnosis
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("### 🛠️ Quick Commands")
    st.markdown("""
    <div class="argo-info-card">
        <div style="margin-bottom: 8px; color: #8b949e; font-size: 11px; text-transform: uppercase; letter-spacing: 1px;">ArgoCD Sync Errors</div>
        <code>argocd app get &lt;app-name&gt;</code>
    </div>
    <div class="argo-info-card">
        <div style="margin-bottom: 8px; color: #8b949e; font-size: 11px; text-transform: uppercase; letter-spacing: 1px;">Previous Pod Logs</div>
        <code>kubectl logs &lt;pod&gt; -n &lt;ns&gt; --previous</code>
    </div>
    <div class="argo-info-card">
        <div style="margin-bottom: 8px; color: #8b949e; font-size: 11px; text-transform: uppercase; letter-spacing: 1px;">Cluster Events</div>
        <code>kubectl get events -n &lt;ns&gt; --sort-by='.lastTimestamp'</code>
    </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Main content — Header
# ---------------------------------------------------------------------------
st.markdown("""
<div class="argo-header">
    <div class="argo-header-icon">🔍</div>
    <div>
        <h1>Argo Log Analyzer</h1>
        <p class="argo-header-sub">DECODE · DIAGNOSE · DEPLOY</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Stats row
log_types = ["ArgoCD Sync", "Pod / K8s Events", "Application Errors"]
st.markdown(f"""
<div class="argo-stats">
    <div class="argo-stat">
        <div class="argo-stat-value" style="color: #0dadea;">⟳</div>
        <div class="argo-stat-label">ArgoCD Sync Errors</div>
    </div>
    <div class="argo-stat">
        <div class="argo-stat-value" style="color: #18be94;">☸</div>
        <div class="argo-stat-label">Pod / K8s Events</div>
    </div>
    <div class="argo-stat">
        <div class="argo-stat-value" style="color: #e8863a;">⚡</div>
        <div class="argo-stat-label">App Stack Traces</div>
    </div>
    <div class="argo-stat">
        <div class="argo-stat-value" style="color: #e96d76;">🤖</div>
        <div class="argo-stat-label">AI-Powered Analysis</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Input section
# ---------------------------------------------------------------------------
input_method = st.radio(
    "Choose input method",
    ["📋  Paste Logs", "📁  Upload File"],
    horizontal=True,
    label_visibility="collapsed",
)

log_text = ""

if input_method == "📋  Paste Logs":
    log_text = st.text_area(
        "Paste your logs here",
        height=280,
        placeholder=(
            "Paste ArgoCD sync errors, kubectl logs, pod events, "
            "or application stack traces here...\n\n"
            "Examples of supported logs:\n"
            '  • time="2026-03-10T08:15:32Z" level=error msg="ComparisonError: ..."\n'
            "  • Warning  FailedScheduling  0/3 nodes are available: 3 Insufficient cpu\n"
            "  • java.lang.NullPointerException at com.example.Service.run(Service.java:42)\n"
            "  • OOMKilled / CrashLoopBackOff / ImagePullBackOff"
        ),
    )
else:
    uploaded_file = st.file_uploader(
        "Upload a log file",
        type=["log", "txt", "json", "yaml", "yml"],
    )
    if uploaded_file is not None:
        log_text = uploaded_file.read().decode("utf-8", errors="replace")
        with st.expander("📄 Preview uploaded log", expanded=False):
            st.code(
                log_text[:3000] + ("\n..." if len(log_text) > 3000 else ""),
                language="text",
            )

# Analyze button
st.markdown("")
analyze_clicked = st.button(
    "🚀  Analyze Logs",
    type="primary",
    use_container_width=True,
    disabled=not log_text.strip(),
)

# ---------------------------------------------------------------------------
# Analysis Results
# ---------------------------------------------------------------------------
if analyze_clicked and log_text.strip():
    detected_type = detect_log_type(log_text)
    override = None if log_type_choice == "Auto-Detect" else log_type_choice
    display_type = override or detected_type

    # ArgoCD-style badge
    badge_map = {
        "ArgoCD": ("argo-badge-argocd", "#0dadea"),
        "Pod / Kubernetes": ("argo-badge-pod", "#18be94"),
        "Application": ("argo-badge-app", "#e8863a"),
    }
    badge_cls, badge_color = badge_map.get(display_type, ("argo-badge-unknown", "#8b949e"))

    st.markdown(f"""
    <div style="margin: 20px 0 12px 0; display: flex; align-items: center; gap: 12px;">
        <span class="argo-badge {badge_cls}">
            <span class="argo-badge-dot" style="background: {badge_color};"></span>
            {display_type}
        </span>
        <span style="color: #8b949e; font-size: 12px;">
            {"Auto-detected from log patterns" if not override else "Manually selected"}
        </span>
    </div>
    """, unsafe_allow_html=True)

    with st.spinner("Analyzing logs with Bosch LLM..."):
        try:
            result = analyze_log(log_text, override)

            # Strip CLI header (=== box)
            lines = result.split("\n")
            content_start = 0
            for i, line in enumerate(lines):
                if line.strip().startswith("##") or (i > 3):
                    content_start = i
                    break
            clean_result = "\n".join(lines[content_start:])

            st.markdown(f"""
            <div class="argo-result-card">
            """, unsafe_allow_html=True)
            st.markdown(clean_result)
            st.markdown("</div>", unsafe_allow_html=True)

            # Action row
            col_dl, col_copy = st.columns([1, 1])
            with col_dl:
                st.download_button(
                    label="📥  Download Report (.md)",
                    data=result,
                    file_name="argo-log-analysis.md",
                    mime="text/markdown",
                    use_container_width=True,
                )

        except EnvironmentError as e:
            st.error(f"⚙️ **Configuration Error:** {e}")
            st.info("Ensure your `.env` file has `BOSCH_LLM_API_KEY` set correctly.")
        except Exception as e:
            error_msg = str(e)
            st.error(f"**Analysis Failed:** {error_msg}")
            if "404" in error_msg:
                st.warning(
                    "**404 Not Found** — The deployment name is likely incorrect. "
                    "Check the Bosch LLM Farm Model Catalog for the exact deployment name "
                    "and update `BOSCH_LLM_DEPLOYMENT` in your `.env` file."
                )
            elif "401" in error_msg or "403" in error_msg:
                st.warning(
                    "**Authentication failed** — Check your `BOSCH_LLM_API_KEY` in the `.env` file."
                )

elif analyze_clicked:
    st.warning("Please paste some logs or upload a file first.")


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown("""
<div class="argo-footer">
    ARGO LOG ANALYZER &nbsp;·&nbsp; Powered by Bosch LLM &nbsp;·&nbsp; Built for DevOps & Application Engineers
</div>
""", unsafe_allow_html=True)
