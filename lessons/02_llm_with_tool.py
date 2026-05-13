"""
LESSON 2 — Giving the LLM a Tool
=================================

Recap from Lesson 1:
  LLM = text in, text out. No internet. No memory.
  → It CANNOT tell you today's Bitcoin price.

Solution: give the LLM a "tool" it can ask us to run.

What is a "tool"?
-----------------
A tool is just a normal Python function (e.g. `get_crypto_price("bitcoin")`)
that we DESCRIBE to the LLM using a JSON schema. The LLM can then reply
with: "please run get_crypto_price with symbol=bitcoin", and WE run it
and send the result back.

Flow in this lesson (manual — we do the thinking, no loop yet):

    ┌────────┐  1. question + tool list  ┌─────┐
    │  YOU   │ ─────────────────────────► │ LLM │
    └────────┘                            └──┬──┘
         ▲                                   │ 2. "call get_crypto_price"
         │ 5. final natural-language answer  │
         │                                   ▼
         │                          ┌─────────────────┐
         │                          │ Python function │  (real HTTP call
         │                          │ get_crypto_price│   to CoinGecko)
         │                          └────────┬────────┘
         │                                   │ 3. price = $67,321
         │   4. tool result sent back        │
         └───────────────────────────────────┘

This lesson does exactly ONE round-trip. Lesson 3 will put it in a loop
so the model can decide to call MULTIPLE tools before answering.

Run it:
    python lessons/02_llm_with_tool.py
"""

import os
import json
import requests
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ===========================================================================
# PART A — The actual Python function (our "tool" implementation)
# ===========================================================================
# This is just a normal function. It hits CoinGecko's free public API.
# CoinGecko uses "ids" like "bitcoin", "ethereum", "solana".
def get_crypto_price(coin_id: str, vs_currency: str = "usd") -> dict:
    """Fetch the current price of a coin from CoinGecko."""
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": coin_id, "vs_currencies": vs_currency}

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    # CoinGecko returns e.g. {"bitcoin": {"usd": 67321.5}}
    if coin_id not in data:
        return {"error": f"Unknown coin_id '{coin_id}'. Try 'bitcoin' or 'ethereum'."}

    price = data[coin_id][vs_currency]
    return {"coin_id": coin_id, "currency": vs_currency, "price": price}


# Quick sanity check you can uncomment to test the function directly:
# print(get_crypto_price("bitcoin"))


# ===========================================================================
# PART B — Describe the tool to the LLM using JSON schema
# ===========================================================================
# The LLM doesn't see Python code. It sees this description and decides
# WHEN and HOW to call it. Think of it as the function's signature + docs,
# translated into JSON.
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_crypto_price",
            "description": (
                "Get the current market price of a cryptocurrency in a given "
                "fiat currency. Use this whenever the user asks for a live or "
                "current price of a coin."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "coin_id": {
                        "type": "string",
                        "description": (
                            "CoinGecko coin id in lowercase, e.g. 'bitcoin', "
                            "'ethereum', 'solana', 'dogecoin'."
                        ),
                    },
                    "vs_currency": {
                        "type": "string",
                        "description": "Fiat currency code, e.g. 'usd', 'eur'. Default 'usd'.",
                    },
                },
                "required": ["coin_id"],
            },
        },
    }
]


# ===========================================================================
# PART C — One round-trip with tool-calling
# ===========================================================================
messages = [
    {
        "role": "system",
        "content": (
            "You are a helpful crypto analyst. "
            "When the user asks for live market data, call the appropriate tool. "
            "Never invent prices."
        ),
    },
    {
        "role": "user",
        "content": "What is the price of Ethereum right now in USD?",
    },
]

print("STEP 1 → Asking the LLM (with tool list attached)...")

# First call: we pass the `tools` list so the model knows what functions exist.
first_response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=messages,
    tools=tools,
    tool_choice="auto",   # "auto" = let the model decide whether to call a tool
)

assistant_msg = first_response.choices[0].message

# Did the model choose to call a tool, or did it reply with text directly?
if not assistant_msg.tool_calls:
    print("\n(The model answered without calling any tool.)")
    print("Reply:", assistant_msg.content)
    raise SystemExit(0)

# The model wants to call one or more tools. Let's see what it picked.
print(f"\nSTEP 2 → The model decided to call {len(assistant_msg.tool_calls)} tool(s).")

# IMPORTANT: we must append the assistant's message (with tool_calls) to the
# conversation history before sending tool results back.
messages.append(assistant_msg)

# Run each requested tool call and send the results back.
for tool_call in assistant_msg.tool_calls:
    name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)  # arguments come as a JSON string
    print(f"   → Calling {name}({args})")

    # Dispatch: map tool name → real Python function
    if name == "get_crypto_price":
        result = get_crypto_price(**args)
    else:
        result = {"error": f"Unknown tool: {name}"}

    print(f"   ← Tool returned: {result}")

    # Append the tool's output to the conversation, tagged with its call id.
    messages.append(
        {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(result),
        }
    )

print("\nSTEP 3 → Sending tool result back to the LLM for a final answer...")

# Second call: no `tools` parameter needed; we just want the model to read
# the tool result we appended and produce a normal, human-friendly answer.
second_response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=messages,
)

final_answer = second_response.choices[0].message.content

print("\n" + "=" * 60)
print("FINAL ANSWER")
print("=" * 60)
print(final_answer)
print("=" * 60)

# ---------------------------------------------------------------------------
# Key takeaways
# ---------------------------------------------------------------------------
# • The LLM never runs code itself. It only SAYS "please call X with Y".
# • WE (our Python script) actually run the function and pass the result back.
# • This required TWO API calls: one to decide the tool call, one to write
#   the final answer using the tool's result.
#
# EXERCISES
# ---------
# 1. Change the user question to: "How much is 2 BTC worth in EUR?"
#    Does the model correctly pick coin_id='bitcoin', vs_currency='eur'?
#    Notice it can do the multiplication (2 × price) on its own in the final
#    answer — that's LLM reasoning on top of a tool result.
#
# 2. Ask a question that does NOT need a tool, like "What does HODL mean?"
#    You should see "The model answered without calling any tool."
#
# 3. Ask about a made-up coin, e.g. "price of fakecoinxyz".
#    The tool returns an error dict. See how the LLM handles that gracefully.
#
# → But what if the user asks something that needs TWO tool calls?
#   e.g. "Compare the price of BTC and ETH right now."
#   Our current script only handles one round. The model might try to call
#   two tools at once, which this script DOES handle — but more commonly
#   the model wants to call tool A, see the result, THEN decide to call
#   tool B. For that we need a LOOP. → Lesson 3.
# ---------------------------------------------------------------------------
