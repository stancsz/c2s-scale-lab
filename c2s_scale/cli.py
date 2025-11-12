#!/usr/bin/env python3
"""
c2s_scale.cli - simple interactive CLI to chat with an LLM or exercise the local Client stub.

Usage:
  python -m c2s_scale.cli chat        # interactive REPL
  python -m c2s_scale.cli send "Hi"  # send a single message and exit
  python -m c2s_scale.cli run --config path/to/config.yaml  # call Client.run()

Behavior:
- If OPENAI_API_KEY is set in the environment, the CLI will send messages to OpenAI's chat completions endpoint.
- Otherwise it falls back to a safe local stub reply (non-network).
"""
from __future__ import annotations
import argparse
import os
import sys
import json
import requests
from typing import List, Optional

DEFAULT_OPENAI_MODEL = "gpt-3.5-turbo"
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"


def send_to_openai(messages: List[dict], model: str = DEFAULT_OPENAI_MODEL, timeout: int = 15) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 1024,
    }
    resp = requests.post(OPENAI_API_URL, headers=headers, json=payload, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    # Defensive: navigate response
    try:
        return data["choices"][0]["message"]["content"]
    except Exception:
        return json.dumps(data, indent=2)


def local_stub_response(user_message: str) -> str:
    # Deterministic, safe fallback used when no API key is available.
    return f"[local-stub] Received: {user_message!r}. Set OPENAI_API_KEY to use a real model."


class LLMAgent:
    def __init__(self, model: str = DEFAULT_OPENAI_MODEL):
        self.model = model
        self.history: List[dict] = []

    def send(self, user_text: str) -> str:
        # append user message to history
        self.history.append({"role": "user", "content": user_text})
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            try:
                return send_to_openai(self.history, model=self.model)
            except Exception as e:
                # Return a readable error for the CLI rather than raising
                return f"[error] OpenAI request failed: {e}"
        else:
            return local_stub_response(user_text)


def repl(agent: LLMAgent):
    print("c2s-scale CLI chat REPL")
    print("Type your message and press Enter to send.")
    print("Commands: /exit, /help, /history, /model <name>, /clear")
    while True:
        try:
            user = input("> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("")  # newline
            print("Exiting.")
            return

        if not user:
            continue

        if user.startswith("/"):
            parts = user.split()
            cmd = parts[0].lower()
            if cmd == "/exit":
                print("Exiting.")
                return
            if cmd == "/help":
                print("Commands:")
                print("  /exit            - exit the REPL")
                print("  /help            - show this help")
                print("  /history         - show message history (roles & content)")
                print("  /model <name>    - change model (e.g. gpt-3.5-turbo)")
                print("  /clear           - clear history")
                continue
            if cmd == "/history":
                for i, m in enumerate(agent.history):
                    print(f"{i:02d} {m['role']}: {m['content']}")
                continue
            if cmd == "/model":
                if len(parts) < 2:
                    print("Usage: /model <model-name>")
                    continue
                agent.model = parts[1]
                print(f"Model set to: {agent.model}")
                continue
            if cmd == "/clear":
                agent.history.clear()
                print("History cleared.")
                continue
            print(f"Unknown command: {cmd}. Try /help.")
            continue

        # send the message
        response = agent.send(user)
        # include assistant message in history (best-effort)
        agent.history.append({"role": "assistant", "content": response})
        print(response)
        # keep loop


def main(argv: Optional[List[str]] = None):
    parser = argparse.ArgumentParser(prog="c2s-scale", description="Simple CLI to chat with an LLM or run the local Client.")
    sub = parser.add_subparsers(dest="cmd")

    p_chat = sub.add_parser("chat", help="Interactive chat REPL (default if no args).")
    p_chat.add_argument("--model", "-m", default=DEFAULT_OPENAI_MODEL, help="Model to use when OPENAI_API_KEY is set.")

    p_send = sub.add_parser("send", help="Send a single message and print the response.")
    p_send.add_argument("message", help="Message to send to the model.")
    p_send.add_argument("--model", "-m", default=DEFAULT_OPENAI_MODEL, help="Model to use when OPENAI_API_KEY is set.")

    p_run = sub.add_parser("run", help="Call the local c2s_scale Client.run(config).")
    p_run.add_argument("--config", "-c", default="example-config.yaml", help="Path to config file.")

    # if no args provided, go to chat
    args = parser.parse_args(argv)

    if args.cmd is None:
        # default to chat
        args.cmd = "chat"

    if args.cmd == "chat":
        agent = LLMAgent(model=getattr(args, "model", DEFAULT_OPENAI_MODEL))
        repl(agent)
        return

    if args.cmd == "send":
        agent = LLMAgent(model=getattr(args, "model", DEFAULT_OPENAI_MODEL))
        resp = agent.send(args.message)
        print(resp)
        return

    if args.cmd == "run":
        # use local c2s_scale client if available
        try:
            import c2s_scale
            Client = getattr(c2s_scale, "Client", None)
            if Client is None:
                print("c2s_scale imported but no Client found.")
                return
            client = Client()
            result = client.run(args.config)
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"Failed to import or run c2s_scale.Client: {e}", file=sys.stderr)
            sys.exit(2)


if __name__ == "__main__":
    main()
