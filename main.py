#!/usr/bin/env python3
"""
ArgoCD Log Analyzer CLI
=======================
Paste logs or point to a file — get a plain-English diagnosis powered by your Bosch LLM.

Usage examples
--------------
  # Analyze a log file
  python main.py --file /tmp/argocd-sync-error.log

  # Pipe logs from kubectl
  kubectl logs deploy/my-app -n staging | python main.py

  # Paste logs interactively
  python main.py

  # Override auto-detected log type
  python main.py --file crash.log --type pod

  # Save analysis to a file
  python main.py --file error.log --output report.md
"""

import argparse
import sys

import requests
from analyzer import analyze_log


def read_log_input(args) -> str:
    """Read log text from file, stdin pipe, or interactive paste."""

    # 1. From --file argument
    if args.file:
        with open(args.file, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    # 2. From piped stdin (e.g. kubectl logs ... | python main.py)
    if not sys.stdin.isatty():
        return sys.stdin.read()

    # 3. Interactive paste
    print("=" * 60)
    print("  ArgoCD Log Analyzer  —  Paste your logs below")
    print("  (Press Ctrl+Z then Enter on Windows, or Ctrl+D on Linux/Mac to finish)")
    print("=" * 60)
    lines = []
    try:
        while True:
            lines.append(input())
    except EOFError:
        pass
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze ArgoCD / Kubernetes / Application logs with AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--file", "-f",
        help="Path to a log file to analyze",
    )
    parser.add_argument(
        "--type", "-t",
        choices=["argocd", "pod", "application"],
        help="Override auto-detected log type (argocd | pod | application)",
    )
    parser.add_argument(
        "--output", "-o",
        help="Save the analysis to a file (e.g. report.md)",
    )
    args = parser.parse_args()

    # Map CLI type names to display names
    type_map = {
        "argocd": "ArgoCD",
        "pod": "Pod / Kubernetes",
        "application": "Application",
    }

    log_text = read_log_input(args)

    if not log_text.strip():
        print("No log content provided. Exiting.")
        sys.exit(1)

    log_type_override = type_map.get(args.type) if args.type else None

    print("\n⏳ Analyzing logs with Bosch LLM ... please wait.\n")

    try:
        result = analyze_log(log_text, log_type_override)
    except requests.exceptions.HTTPError as e:
        print(f"❌ LLM API error: {e}")
        if e.response is not None and e.response.status_code == 404:
            print("\n💡 404 means the deployment name is likely wrong.")
            print("   Check the Bosch LLM Farm Model Catalog for the exact name")
            print("   and update BOSCH_LLM_DEPLOYMENT in your .env file.")
        sys.exit(1)
    except EnvironmentError as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ LLM request failed: {e}")
        sys.exit(1)

    print(result)

    # Optionally save to file
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"\n📄 Analysis saved to {args.output}")


if __name__ == "__main__":
    main()
