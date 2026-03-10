# ArgoCD Log Analyzer 🔍

A CLI tool that analyzes ArgoCD, Kubernetes pod, and application logs using your **Bosch LLM** and returns a **plain-English diagnosis** — including what went wrong, where the issue is, possible causes, and how to fix it.

Built for **application engineers** who don't want to spend hours decoding cryptic Kubernetes errors.

---

## Features

- **Auto-detects log type** — ArgoCD sync errors, Pod/K8s events, or application-level exceptions
- **Structured diagnosis** — Summary → Location → Causes → Fixes → Next Steps
- **Simple language** — written for app engineers, not just K8s experts
- **Multiple input modes** — file, stdin pipe, or interactive paste
- **Exportable** — save analysis to a markdown file

---

## Quick Start

### 1. Install dependencies

```bash
cd argo-log-analyzer
pip install -r requirements.txt
```

### 2. Configure your Bosch LLM key

```bash
cp .env.example .env
# Edit .env and fill in your actual values:
#   BOSCH_LLM_API_KEY=your-real-key
#   BOSCH_LLM_API_URL=https://your-bosch-llm-endpoint/v1/chat/completions
#   BOSCH_LLM_MODEL=gpt-4
```

### 3. Run it

```bash
# Analyze a log file
python main.py --file /path/to/error.log

# Pipe from kubectl
kubectl logs deploy/my-app -n staging | python main.py

# Paste interactively
python main.py

# Override detected type
python main.py --file sync-error.log --type argocd

# Save output
python main.py --file crash.log --output report.md
```

---

## Example Output

```
============================================================
  LOG TYPE DETECTED  ➜  Pod / Kubernetes
============================================================

## 🔍 What Happened (Summary)
The pod "payment-service-7f8b9c-xyz" was killed because it exceeded its
memory limit (OOMKilled). Kubernetes restarted it but it keeps crashing,
entering a CrashLoopBackOff state.

## 📍 Where Is the Problem?
**Kubernetes Manifest / YAML Level** — the memory limit in the Deployment
spec for `payment-service` is set too low for the application's needs.
Resource: `Deployment/payment-service` in namespace `production`.

## ⚠️ Possible Causes
1. Memory limit in the pod spec is too low (currently 256Mi).
2. The application has a memory leak in recent code changes.
3. A spike in traffic is causing higher-than-normal memory usage.

## ✅ Recommended Fixes
1. Increase memory limits:
   ```yaml
   resources:
     limits:
       memory: "512Mi"
     requests:
       memory: "256Mi"
   ```
2. Profile the application for memory leaks.
3. Add a Horizontal Pod Autoscaler (HPA) to handle traffic spikes.

## 🔎 Where to Look Next
- Run: `kubectl describe pod payment-service-7f8b9c-xyz -n production`
- Check: `deployment.yaml` → `spec.containers[].resources`
- Monitor: Grafana memory dashboard for the `production` namespace
```

---

## How It Works

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│  Log Input   │────▶│  Auto-Classify   │────▶│   Bosch LLM  │
│  (file/pipe/ │     │  (ArgoCD / Pod / │     │  Analysis     │
│   paste)     │     │   Application)   │     │              │
└──────────────┘     └──────────────────┘     └──────┬───────┘
                                                      │
                                              ┌───────▼───────┐
                                              │  Structured   │
                                              │  Plain-English│
                                              │  Report       │
                                              └───────────────┘
```

1. **Input** — Reads logs from a file (`--file`), piped stdin, or interactive paste.
2. **Classify** — Pattern-matches keywords to detect whether the log is from ArgoCD, K8s pods, or the application itself.
3. **Analyze** — Sends the log + a carefully-crafted prompt to your Bosch LLM.
4. **Report** — Prints (and optionally saves) a structured diagnosis.

---

## Project Structure

```
argo-log-analyzer/
├── main.py          # CLI entry point
├── analyzer.py      # Log classifier + LLM orchestration
├── llm_client.py    # Bosch LLM API client
├── prompts.py       # System & user prompt templates
├── config.py        # Configuration (reads from .env)
├── .env.example     # Template for your secrets
├── requirements.txt # Python dependencies
└── README.md        # This file
```

---

## CLI Options

| Flag | Short | Description |
|------|-------|-------------|
| `--file` | `-f` | Path to a log file |
| `--type` | `-t` | Override auto-detection: `argocd`, `pod`, or `application` |
| `--output` | `-o` | Save the analysis to a file |

---

## Tips for Your Team

- **ArgoCD sync errors**: Copy the error from the ArgoCD UI → paste into the tool.
- **Pod crashes**: Run `kubectl logs <pod> -n <ns> --previous` and pipe it in.
- **App exceptions**: Grab the stack trace from your logging system and feed it in.
- Share the generated `report.md` in your team chat for collaborative debugging.
