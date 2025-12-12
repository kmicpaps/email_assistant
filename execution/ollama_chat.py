#!/usr/bin/env python3
"""
Minimal Ollama Chat Tool
Calls local Ollama API for light coding tasks.

Usage:
    python ollama_chat.py --model qwen2.5-coder:7b-instruct --prompt "Write a function to parse CSV"
    echo "Fix the bug in this code: ..." | python ollama_chat.py --model qwen2.5-coder:7b-instruct
"""

import sys
import json
import argparse
import requests


def call_ollama(host, model, messages, format_type=None, timeout=600):
    """
    Call Ollama chat API.

    Args:
        host: Ollama API host
        model: Model name
        messages: List of message dicts
        format_type: Optional format (e.g., "json")
        timeout: Request timeout in seconds

    Returns:
        Assistant's response content
    """
    url = f"{host}/api/chat"

    payload = {
        "model": model,
        "messages": messages,
        "stream": False
    }

    if format_type:
        payload["format"] = format_type

    try:
        response = requests.post(url, json=payload, timeout=timeout)

        if response.status_code != 200:
            print(f"Error: Ollama returned status {response.status_code}", file=sys.stderr)
            print(f"Response: {response.text}", file=sys.stderr)
            sys.exit(1)

        data = response.json()
        return data.get("message", {}).get("content", "")

    except requests.exceptions.ConnectionError:
        print(f"Error: Cannot connect to Ollama at {host}", file=sys.stderr)
        print("Is Ollama running? Try: ollama serve", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.Timeout:
        print(f"Error: Request timed out after {timeout} seconds", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Call local Ollama API for coding tasks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Simple prompt
  python ollama_chat.py --model qwen2.5-coder:7b-instruct --prompt "Write a function to calculate fibonacci"

  # From stdin
  echo "Refactor this code: def foo(): pass" | python ollama_chat.py --model qwen2.5-coder:7b-instruct

  # Request unified diff
  python ollama_chat.py --model qwen2.5-coder:7b-instruct --system "Output ONLY a unified diff patch" --prompt "Add error handling to: def divide(a,b): return a/b"

  # JSON output
  python ollama_chat.py --model qwen2.5-coder:7b-instruct --format json --prompt "List Python best practices as JSON"
        """
    )

    parser.add_argument("--model", required=True, help="Ollama model name (e.g., qwen2.5-coder:7b-instruct)")
    parser.add_argument("--system", help="System prompt")
    parser.add_argument("--prompt", help="User prompt (reads from stdin if not provided)")
    parser.add_argument("--format", choices=["json"], help="Response format")
    parser.add_argument("--host", default="http://localhost:11434", help="Ollama API host (default: http://localhost:11434)")
    parser.add_argument("--timeout", type=int, default=600, help="Request timeout in seconds (default: 600)")

    args = parser.parse_args()

    # Get prompt from args or stdin
    if args.prompt:
        user_prompt = args.prompt
    else:
        if sys.stdin.isatty():
            print("Error: No --prompt provided and stdin is empty", file=sys.stderr)
            print("Provide --prompt or pipe input via stdin", file=sys.stderr)
            sys.exit(1)
        user_prompt = sys.stdin.read().strip()

    if not user_prompt:
        print("Error: Prompt is empty", file=sys.stderr)
        sys.exit(1)

    # Build messages
    messages = []

    if args.system:
        messages.append({"role": "system", "content": args.system})

    messages.append({"role": "user", "content": user_prompt})

    # Call Ollama
    response = call_ollama(
        host=args.host,
        model=args.model,
        messages=messages,
        format_type=args.format,
        timeout=args.timeout
    )

    # Output only the assistant's response
    print(response)


if __name__ == "__main__":
    main()
