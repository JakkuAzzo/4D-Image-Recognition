"""Notification dispatch script.

Reads a status JSON file (e.g., regression_status.json or ui_visual_diff_report.json)
and posts a concise summary to a configured webhook (Slack compatible) or stdout.

Environment Variables:
  NOTIFY_WEBHOOK_URL   - If set, POST JSON payload to this URL.
  NOTIFY_CHANNEL       - Optional channel hint (for Slack webhook proxies).
  NOTIFY_USERNAME      - Optional display name.
  NOTIFY_ICON_EMOJI    - Optional emoji icon.
  DRY_RUN              - If '1', do not POST, just print payload.

Usage:
  python -m scripts.notification_dispatch --input path/to/status.json --title "Nightly Regression"

Status JSON Expectations (flexible):
  - If contains keys: {"summary": { ... }} use summary.
  - If contains keys: {"passed": int, "failed": int} derive summary.
  - Otherwise transmit truncated raw JSON snippet.

Exit Codes:
  0 on success (even if webhook unset), non-zero on unexpected failure.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
import urllib.request
import urllib.error
from typing import Any, Dict


def _summarize(data: Dict[str, Any]) -> str:
    # Visual diff style
    if "images" in data and "summary" in data:
        s = data["summary"]
        return f"Visual Diff: {s.get('passed', '?')} passed / {s.get('failed', '?')} failed"
    # Generic pass/fail
    if {"passed", "failed"}.issubset(data.keys()):
        return f"Results: {data['passed']} passed / {data['failed']} failed"
    # Pipeline regression style
    if "regressions" in data:
        reg = data["regressions"]
        count = len(reg) if isinstance(reg, list) else reg
        return f"Regressions detected: {count}" if count else "No regressions"
    # Fallback: truncated JSON
    raw = json.dumps(data)[:200]
    return f"Status Payload: {raw}..." if len(raw) == 200 else f"Status Payload: {raw}"


def build_payload(title: str, summary: str, data: Dict[str, Any]) -> Dict[str, Any]:
    blocks = [
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*{title}*"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": summary}},
    ]
    if "summary" in data and isinstance(data["summary"], dict):
        details_lines = [f"• {k}: {v}" for k, v in data["summary"].items()]
        if details_lines:
            blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": "\n".join(details_lines)}})
    # Optional fusion provenance block
    fusion = data.get("fusion")
    if isinstance(fusion, dict) and {"score", "category"}.issubset(fusion.keys()):
        comp_lines = []
        comps = fusion.get("components", {})
        for k, v in comps.items():
            comp_lines.append(f"{k}={v:.3f}")
        comp_text = ", ".join(comp_lines)
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Fusion* score={fusion['score']:.3f} ({fusion['category']})\n{comp_text}"}
        })
    return {
        "username": os.environ.get("NOTIFY_USERNAME", "pipeline-bot"),
        "icon_emoji": os.environ.get("NOTIFY_ICON_EMOJI", ":satellite:"),
        "channel": os.environ.get("NOTIFY_CHANNEL"),
        "text": f"{title}: {summary}",
        "blocks": blocks,
    }


def post_webhook(url: str, payload: Dict[str, Any]) -> None:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:  # nosec B310
        if resp.status >= 400:
            raise RuntimeError(f"Webhook POST failed with status {resp.status}")


def main(argv: list[str] | None = None) -> int:  # pragma: no cover (CLI)
    parser = argparse.ArgumentParser(description="Dispatch a notification for status JSON.")
    parser.add_argument("--input", required=True, help="Path to status JSON file")
    parser.add_argument("--title", required=True, help="Title for the notification")
    parser.add_argument("--print", action="store_true", help="Always print payload to stdout")
    args = parser.parse_args(argv)

    try:
        with open(args.input, "r") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Failed to load status JSON: {e}", file=sys.stderr)
        return 2

    summary = _summarize(data)
    payload = build_payload(args.title, summary, data)
    if args.print or True:  # Always print for transparency
        print(json.dumps(payload, indent=2))

    url = os.environ.get("NOTIFY_WEBHOOK_URL")
    if not url:
        print("NOTIFY_WEBHOOK_URL not set; skipping webhook POST (success).")
        return 0
    if os.environ.get("DRY_RUN") == "1":
        print("DRY_RUN=1; not posting to webhook.")
        return 0
    try:
        post_webhook(url, payload)
        print("Webhook POST succeeded.")
        return 0
    except Exception as e:
        print(f"Webhook POST failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
