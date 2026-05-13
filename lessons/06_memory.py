"""
LESSON 6 — Memory
=================

Every agent we've built so far is *amnesiac*. Each call to `run_agent()`
starts from scratch. That's fine for one-shot research, but ruins any real
conversation:

    You: "My wallet is 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045."
    You: "What's its ETH balance?"
    Agent: "Which wallet?"  ← has no memory of the previous turn

There are two kinds of memory we want:

  1. **Short-term / conversational**: remember the current chat.
     Implementation: keep the messages list across turns.

  2. **Long-term / persistent**: remember facts across sessions, even
     after restarting the program.
     Implementation: save key-value facts to a JSON file (or a DB).
     Expose "save_fact" and "recall_facts" as TOOLS so the LLM decides
     what is worth remembering.

This lesson builds a CLI chatbot that has BOTH. It deliberately has zero
crypto tools so you can focus on the memory pattern. In the exercises
below we show how to plug memory into lessons 4/5.

Run it:
    python lessons/06_memory.py
Type /quit to exit, /forget to clear long-term memory.
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---------------------------------------------------------------------------
# Long-term memory: just a JSON file. Simple, inspectable, sharable.
# ---------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
MEMORY_FILE = HERE.parent / "data" / "memory.json"
MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)

def _load_memory() -> dict:
    if MEMORY_FILE.exists():
        try:
            return json.loads(MEMORY_FILE.read_text())
        except json.JSONDecodeError:
            return {}
    return {}

def _save_memory(mem: dict) -> None:
    MEMORY_FILE.write_text(json.dumps(mem, indent=2))


# ---------------------------------------------------------------------------
# Memory-as-tools — the LLM decides what to remember and when to recall.
# ---------------------------------------------------------------------------
def save_fact(key: str, value: str) -> dict:
    """Persist a small fact about the user under a stable key."""
    mem = _load_memory()
    mem[key] = value
    _save_memory(mem)
    return {"ok": True, "saved": {key: value}, "total_facts": len(mem)}

def recall_facts() -> dict:
    """Return every fact we've stored so far."""
    mem = _load_memory()
    return {"facts": mem, "count": len(mem)}

def forget_fact(key: str) -> dict:
    """Delete one fact by key."""
    mem = _load_memory()
    existed = key in mem
    mem.pop(key, None)
    _save_memory(mem)
    return {"ok": True, "existed": existed, "remaining_facts": len(mem)}


TOOL_REGISTRY = {
    "save_fact": save_fact,
    "recall_facts": recall_facts,
    "forget_fact": forget_fact,
}

TOOLS_SPEC = [
    {
        "type": "function",
        "function": {
            "name": "save_fact",
            "description": (
                "Save a durable fact about the user (e.g. their wallet address, "
                "risk tolerance, favorite L2). Use short stable keys like "
                "'eth_wallet', 'preferred_chain', 'experience_level'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Short snake_case key."},
                    "value": {"type": "string", "description": "The fact, as plain text."},
                },
                "required": ["key", "value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recall_facts",
            "description": "Return all facts stored about the user. Call this at the start of a conversation.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "forget_fact",
            "description": "Remove one fact by key.",
            "parameters": {
                "type": "object",
                "properties": {"key": {"type": "string"}},
                "required": ["key"],
            },
        },
    },
]

SYSTEM_PROMPT = (
    "You are a helpful crypto assistant with a persistent memory. "
    "At the very start of the conversation, call `recall_facts` so you know "
    "what you already know about the user. "
    "When the user volunteers a durable fact about themselves (wallet "
    "address, risk tolerance, preferred chain, experience level, etc.), "
    "call `save_fact` to store it. "
    "Do NOT save ephemeral things (current mood, one-off questions). "
    "Speak naturally; don't narrate your tool use."
)


# ---------------------------------------------------------------------------
# Short-term memory = we simply KEEP the same `messages` list across turns
# ---------------------------------------------------------------------------
def step(messages: list) -> str:
    """
    Run the agent loop until the LLM stops calling tools, then return the
    final assistant text. `messages` is mutated in place — that IS the
    short-term memory.
    """
    for _ in range(6):  # safety cap
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=TOOLS_SPEC,
            tool_choice="auto",
        )
        msg = resp.choices[0].message
        if not msg.tool_calls:
            messages.append({"role": "assistant", "content": msg.content})
            return msg.content

        messages.append(msg)
        for call in msg.tool_calls:
            args = json.loads(call.function.arguments or "{}")
            fn = TOOL_REGISTRY.get(call.function.name)
            result = fn(**args) if fn else {"error": "unknown tool"}
            messages.append(
                {"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)}
            )
    return "(hit internal step cap)"


def main():
    print("Crypto assistant with memory. Type /quit to exit, /forget to wipe long-term memory.")
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        try:
            user = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user:
            continue
        if user == "/quit":
            break
        if user == "/forget":
            MEMORY_FILE.write_text("{}")
            print("(long-term memory cleared)")
            continue

        messages.append({"role": "user", "content": user})
        reply = step(messages)
        print(f"\nAssistant: {reply}")


if __name__ == "__main__":
    main()

# ---------------------------------------------------------------------------
# Try this dialog
# ---------------------------------------------------------------------------
# You: Hi! My wallet is 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 and I'm
#      a DeFi beginner.
# You: What's my wallet address again?
# (quit with /quit, restart the program)
# You: Remind me who I am.
#
# The last answer should correctly recall both your wallet and your
# experience level — that is LONG-term memory persisted to data/memory.json.
#
# EXERCISES
# ---------
# 1. Merge this with lesson 4: add get_eth_wallet_balance as a 4th tool.
#    Now you can say "what's my balance?" and the agent will recall your
#    wallet AND look it up on-chain without you re-pasting the address.
#
# 2. Long-term memory in a plain JSON file doesn't scale. Swap it for
#    SQLite (one file, zero deps) or a vector DB for "semantic memory"
#    where the agent retrieves past messages by similarity.
#
# 3. Short-term memory grows unbounded — every turn adds messages. For a
#    long conversation you'd eventually hit the token limit. Real systems
#    summarize older turns into a single "conversation so far" message
#    once the history exceeds N messages. Try implementing that.
# ---------------------------------------------------------------------------
