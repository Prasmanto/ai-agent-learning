"""
LESSON 4 — A Real Multi-Tool Crypto Agent
==========================================

Recap:
  Lesson 3: The LLM + a tool + a loop = an "agent". The model decomposes
  a question into tool calls on its own.

Now we level up by giving the agent THREE tools that cover the three most
common Web3 research needs:

  1. get_crypto_price(coin_id)              → live market price   (CoinGecko)
  2. get_latest_crypto_news(topic)          → recent headlines    (CryptoCompare)
  3. get_eth_wallet_balance(address)        → on-chain balance    (web3.py)

With these three, the agent can answer questions like:

  "What's the price of ETH, and is there any news about it right now?"
  "How much ETH does vitalik.eth (0xd8dA...) hold today, and what is that in USD?"
  "Summarize today's biggest crypto story in one paragraph."

THE BIG LESSON HERE
-------------------
You will see that moving from 1 tool → 3 tools does NOT require rewriting
the loop. The loop is the same as lesson 3. You only:
  (a) add a Python function,
  (b) add a JSON schema describing it,
  (c) register it in TOOL_REGISTRY.

That pattern scales to 10 or 100 tools. Frameworks like LangChain are
essentially nice wrappers around this exact pattern.

Run it:
    python lessons/04_multi_tool_agent.py
"""

import os
import json
import requests
from dotenv import load_dotenv
from openai import OpenAI
from web3 import Web3

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ===========================================================================
# TOOL 1 — live price (same as lesson 3, copied for self-containment)
# ===========================================================================
def get_crypto_price(coin_id: str, vs_currency: str = "usd") -> dict:
    """Live price of a coin via CoinGecko's free API."""
    r = requests.get(
        "https://api.coingecko.com/api/v3/simple/price",
        params={"ids": coin_id, "vs_currencies": vs_currency},
        timeout=10,
    )
    r.raise_for_status()
    data = r.json()
    if coin_id not in data:
        return {"error": f"Unknown coin_id '{coin_id}'. Use lowercase ids like 'bitcoin'."}
    return {"coin_id": coin_id, "currency": vs_currency, "price": data[coin_id][vs_currency]}


# ===========================================================================
# TOOL 2 — crypto news headlines
# ===========================================================================
# CryptoCompare's news endpoint is free and needs no API key. Great for demos.
def get_latest_crypto_news(topic: str = "", limit: int = 5) -> dict:
    """Latest crypto news headlines, optionally filtered by topic keyword."""
    r = requests.get(
        "https://min-api.cryptocompare.com/data/v2/news/",
        params={"lang": "EN"},
        timeout=15,
    )
    r.raise_for_status()
    payload = r.json()
    items = payload.get("Data", []) or []

    topic_lower = topic.lower().strip()
    if topic_lower:
        items = [
            a for a in items
            if topic_lower in (a.get("title", "") + " " + a.get("body", "")).lower()
        ]

    # Trim to what the LLM actually needs. Don't send huge bodies — they
    # waste tokens and slow things down.
    trimmed = [
        {
            "title": a.get("title"),
            "source": a.get("source"),
            "url": a.get("url"),
            "published_on": a.get("published_on"),   # unix timestamp
            "summary": (a.get("body", "") or "")[:300],
        }
        for a in items[:limit]
    ]
    return {"topic": topic or "all", "count": len(trimmed), "articles": trimmed}


# ===========================================================================
# TOOL 3 — Ethereum wallet balance (the first "on-chain" tool!)
# ===========================================================================
# We connect to a public Ethereum JSON-RPC endpoint. This is READ-ONLY —
# we are not signing transactions, just reading the public ledger.
ETH_RPC_URL = os.getenv("ETH_RPC_URL", "https://eth.llamarpc.com")
_w3 = Web3(Web3.HTTPProvider(ETH_RPC_URL, request_kwargs={"timeout": 15}))

def get_eth_wallet_balance(address: str) -> dict:
    """Current ETH balance of any Ethereum address, in ETH (not wei)."""
    # web3.py wants a checksummed address. Try to normalize.
    try:
        checksum = Web3.to_checksum_address(address)
    except ValueError:
        return {"error": f"'{address}' is not a valid Ethereum address."}

    try:
        wei = _w3.eth.get_balance(checksum)
    except Exception as e:
        return {"error": f"RPC call failed: {e}"}

    eth = _w3.from_wei(wei, "ether")
    return {
        "address": checksum,
        "balance_eth": float(eth),
        "balance_wei": wei,
        "rpc": ETH_RPC_URL,
    }


# ===========================================================================
# Registry + schemas
# ===========================================================================
TOOL_REGISTRY = {
    "get_crypto_price": get_crypto_price,
    "get_latest_crypto_news": get_latest_crypto_news,
    "get_eth_wallet_balance": get_eth_wallet_balance,
}

TOOLS_SPEC = [
    {
        "type": "function",
        "function": {
            "name": "get_crypto_price",
            "description": "Get the current market price of a cryptocurrency in a fiat currency.",
            "parameters": {
                "type": "object",
                "properties": {
                    "coin_id": {"type": "string", "description": "Lowercase CoinGecko id, e.g. 'bitcoin', 'ethereum'."},
                    "vs_currency": {"type": "string", "description": "Fiat code, default 'usd'."},
                },
                "required": ["coin_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_latest_crypto_news",
            "description": (
                "Get recent crypto news headlines. Optionally filter by a topic keyword "
                "(e.g. 'ethereum', 'regulation', 'SEC'). Use this when the user asks "
                "for news, sentiment, or what's happening today."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Optional keyword filter."},
                    "limit": {"type": "integer", "description": "Max number of articles (default 5, max 10)."},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_eth_wallet_balance",
            "description": (
                "Look up the live ETH balance of any Ethereum wallet address on mainnet. "
                "Address must be a 0x-prefixed hex string."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "address": {"type": "string", "description": "0x-prefixed Ethereum address."},
                },
                "required": ["address"],
            },
        },
    },
]


# ===========================================================================
# Agent loop (identical shape to lesson 3 — the pattern scales)
# ===========================================================================
SYSTEM_PROMPT = (
    "You are a crypto research agent with three tools: live prices, news, "
    "and on-chain ETH wallet balances. "
    "When a question needs live or on-chain data, ALWAYS use the tools — "
    "never invent numbers. "
    "You may call several tools in sequence. When you have enough information, "
    "write a clear final answer. Include units (USD, ETH) and cite article "
    "titles when you used the news tool."
)


def run_agent(question: str, max_steps: int = 8, verbose: bool = True) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]

    for step in range(1, max_steps + 1):
        if verbose:
            print(f"\n── Step {step} ──")

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=TOOLS_SPEC,
            tool_choice="auto",
        )
        msg = resp.choices[0].message

        if not msg.tool_calls:
            return msg.content  # final answer

        messages.append(msg)
        for call in msg.tool_calls:
            name = call.function.name
            args = json.loads(call.function.arguments or "{}")
            if verbose:
                print(f"LLM → wants to call: {name}({args})")

            fn = TOOL_REGISTRY.get(name)
            try:
                result = fn(**args) if fn else {"error": f"Unknown tool: {name}"}
            except Exception as e:
                result = {"error": str(e)}

            if verbose:
                preview = json.dumps(result)
                print(f"Tool → {preview[:200]}{'...' if len(preview) > 200 else ''}")

            messages.append(
                {"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)}
            )

    return "⚠️ Agent hit max_steps without producing a final answer."


# ===========================================================================
# DEMO
# ===========================================================================
if __name__ == "__main__":
    # Vitalik Buterin's famously public address — safe to query.
    question = (
        "Do three things for me: "
        "1) Tell me the current ETH price in USD. "
        "2) Check the ETH balance of 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045. "
        "3) Convert that balance to USD using the price from step 1, "
        "and give me one recent news headline mentioning Ethereum."
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
# What you just built
# ---------------------------------------------------------------------------
# Your agent just composed THREE independent APIs (market, media, blockchain)
# to answer one question. That's already a useful research assistant.
#
# EXERCISES
# ---------
# 1. Add a 4th tool: get_trending_coins() → GET https://api.coingecko.com/api/v3/search/trending
#    Register it in TOOL_REGISTRY and TOOLS_SPEC. Then ask:
#    "What are the trending coins right now, and how does the #1 price
#     compare to Bitcoin's price?"
#
# 2. Replace the hard-coded demo question with `input("> ")` and wrap
#    run_agent in a while-loop. You now have a CLI chatbot (stateless).
#
# 3. Each call still starts from zero context — the agent does not remember
#    previous questions. That's what lesson 6 (memory) will fix.
#
# 4. We're sending tool schemas on EVERY call. That's fine for now.
#    Later (lesson 5) you'll see that RAG does the opposite: instead of
#    adding more TOOLS, it injects relevant TEXT into the prompt.
# ---------------------------------------------------------------------------
