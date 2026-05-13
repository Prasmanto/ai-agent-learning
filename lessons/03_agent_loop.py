"""
LESSON 3 — The Agent Loop (this is the whole "agent" concept!)
==============================================================

Recap:
  Lesson 1: LLM = text in, text out.
  Lesson 2: We can give the LLM a tool, run it ourselves, send the result back.

In Lesson 2 we did ONE round-trip. But real questions often need MANY steps:

    "Which is worth more right now: 3 Ethereum or 50,000 Dogecoin?"

To answer that, the LLM needs to:
    1. Call get_crypto_price("ethereum")   → $3,100
    2. Call get_crypto_price("dogecoin")   → $0.15
    3. Multiply + compare    → "3 ETH = $9,300, 50,000 DOGE = $7,500, ETH wins."

So we need a LOOP:

    while the LLM keeps asking to use tools:
        run the tool(s) it asked for
        append the result to the conversation
        ask the LLM again
    when the LLM finally replies with plain text:
        that's the final answer → return it

THAT LOOP IS WHAT PEOPLE CALL "AN AGENT".

Every framework (LangChain, CrewAI, AutoGen, LangGraph) is essentially this
loop with more bells and whistles. Once you understand these ~40 lines, you
understand agents.

We'll also add a SECOND tool so you can see the LLM pick between tools.

Run it:
    python lessons/03_agent_loop.py
"""

import os
import json
import requests
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ===========================================================================
# TOOLS — plain Python functions
# ===========================================================================
def get_crypto_price(coin_id: str, vs_currency: str = "usd") -> dict:
    """Live price of a coin, via CoinGecko."""
    url = "https://api.coingecko.com/api/v3/simple/price"
    r = requests.get(
        url, params={"ids": coin_id, "vs_currencies": vs_currency}, timeout=10
    )
    r.raise_for_status()
    data = r.json()
    if coin_id not in data:
        return {"error": f"Unknown coin_id '{coin_id}'."}
    return {"coin_id": coin_id, "currency": vs_currency, "price": data[coin_id][vs_currency]}


def get_coin_info(coin_id: str) -> dict:
    """Basic metadata about a coin (symbol, rank, description)."""
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
    params = {"localization": "false", "tickers": "false", "market_data": "false",
              "community_data": "false", "developer_data": "false"}
    r = requests.get(url, params=params, timeout=10)
    if r.status_code != 200:
        return {"error": f"Could not find coin '{coin_id}'."}
    data = r.json()
    # Trim the description — CoinGecko descriptions are enormous.
    description = (data.get("description", {}) or {}).get("en", "") or ""
    return {
        "id": data.get("id"),
        "symbol": data.get("symbol"),
        "name": data.get("name"),
        "market_cap_rank": data.get("market_cap_rank"),
        "description_short": description[:400] + ("..." if len(description) > 400 else ""),
    }


# A registry maps the tool NAME (string the LLM uses) → real function.
TOOL_REGISTRY = {
    "get_crypto_price": get_crypto_price,
    "get_coin_info": get_coin_info,
}


# ===========================================================================
# TOOL SCHEMAS — how we describe the tools to the LLM
# ===========================================================================
TOOLS_SPEC = [
    {
        "type": "function",
        "function": {
            "name": "get_crypto_price",
            "description": "Get the current market price of a cryptocurrency in a fiat currency.",
            "parameters": {
                "type": "object",
                "properties": {
                    "coin_id": {
                        "type": "string",
                        "description": "Lowercase CoinGecko id, e.g. 'bitcoin', 'ethereum', 'dogecoin'.",
                    },
                    "vs_currency": {
                        "type": "string",
                        "description": "Fiat currency code. Default 'usd'.",
                    },
                },
                "required": ["coin_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_coin_info",
            "description": (
                "Get metadata about a cryptocurrency: symbol, name, market-cap rank, "
                "and a short description. Use this when the user asks WHAT a coin is, "
                "not how much it costs."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "coin_id": {
                        "type": "string",
                        "description": "Lowercase CoinGecko id, e.g. 'bitcoin', 'chainlink'.",
                    },
                },
                "required": ["coin_id"],
            },
        },
    },
]


# ===========================================================================
# THE AGENT LOOP — the whole point of this lesson
# ===========================================================================
SYSTEM_PROMPT = (
    "You are a crypto research agent. "
    "You have tools to fetch live prices and coin metadata. "
    "When a question requires live data, call the right tool. "
    "If you need multiple facts, call multiple tools (one at a time is fine). "
    "Never invent prices or market caps — always use the tools. "
    "When you have enough info, give a clear, concise final answer."
)


def run_agent(user_question: str, max_steps: int = 6, verbose: bool = True) -> str:
    """
    Run the agent loop until the LLM produces a final text answer
    (or until we hit max_steps, as a safety net).
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_question},
    ]

    for step in range(1, max_steps + 1):
        if verbose:
            print(f"\n── Step {step} ──")

        # Ask the LLM what to do next, given the whole conversation so far.
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=TOOLS_SPEC,
            tool_choice="auto",
        )
        msg = response.choices[0].message

        # CASE A: The LLM is done and just wrote a final answer.
        if not msg.tool_calls:
            if verbose:
                print("LLM: (final answer, no more tool calls)")
            return msg.content

        # CASE B: The LLM wants to call one or more tools. Run them.
        # First, append the assistant message (it holds the tool_call ids).
        messages.append(msg)

        for tool_call in msg.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            if verbose:
                print(f"LLM → wants to call: {name}({args})")

            fn = TOOL_REGISTRY.get(name)
            if fn is None:
                result = {"error": f"Unknown tool: {name}"}
            else:
                try:
                    result = fn(**args)
                except Exception as e:
                    result = {"error": str(e)}

            if verbose:
                # Truncate noisy outputs so the log stays readable.
                preview = json.dumps(result)
                if len(preview) > 200:
                    preview = preview[:200] + "..."
                print(f"Tool → returned: {preview}")

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result),
                }
            )

        # Loop again — the LLM now sees the tool results and decides next step.

    return "⚠️ Agent hit max_steps without finishing. Try a simpler question or raise max_steps."


# ===========================================================================
# DEMO — ask a question that needs MULTIPLE tool calls
# ===========================================================================
if __name__ == "__main__":
    question = (
        "Compare Bitcoin and Solana for me. "
        "First, tell me what each one is in one sentence, "
        "then give me their current USD prices, "
        "and finally tell me which has the higher market-cap rank."
    )

    print("USER QUESTION:")
    print(question)

    answer = run_agent(question, verbose=True)

    print("\n" + "=" * 60)
    print("FINAL ANSWER")
    print("=" * 60)
    print(answer)
    print("=" * 60)

# ---------------------------------------------------------------------------
# What just happened?
# ---------------------------------------------------------------------------
# You should see the agent take several steps:
#   Step 1: call get_coin_info(bitcoin)
#   Step 2: call get_coin_info(solana)
#   Step 3: call get_crypto_price(bitcoin)
#   Step 4: call get_crypto_price(solana)
#   Step 5: no tool calls → final answer written
#
# The LLM planned that sequence on its own. You did NOT hard-code the order.
# THAT is the superpower of an agent: it decomposes a task into tool calls
# dynamically. Congrats — you now understand agents. 🎉
#
# EXERCISES
# ---------
# 1. Change the question to: "I have 0.5 BTC and 10 ETH. What's my portfolio
#    worth in EUR?" Watch the agent call the price tool TWICE with different
#    coins and currency.
#
# 2. Add a third tool, e.g. `get_trending_coins()` that calls
#    https://api.coingecko.com/api/v3/search/trending . Register it in
#    TOOL_REGISTRY and TOOLS_SPEC. Then ask: "What coins are trending today,
#    and what are their prices?"
#
# 3. Set verbose=False and wrap run_agent() in a while-loop that reads
#    input() from the user — you now have a CLI chatbot. Each call still
#    starts fresh though (no memory). Memory = lesson 6.
# ---------------------------------------------------------------------------
