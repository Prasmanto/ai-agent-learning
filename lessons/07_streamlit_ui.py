"""
LESSON 7 — A Web UI with Streamlit
===================================

We've been running everything in the terminal. That's fine for learning,
but for demos (or sharing with a non-technical friend) a chat UI is much
better.

Streamlit turns a Python script into a web app. You write normal Python
and Streamlit paints it to a browser.

This lesson is the GRAND FINALE: a chat app that combines EVERYTHING
from lessons 1-6 into one agent:

  • Short-term memory (the chat history)
  • Long-term memory (the save_fact / recall_facts tools from lesson 6)
  • Live market price         (lesson 4)
  • Live crypto news          (lesson 4)
  • On-chain ETH balance      (lesson 4)
  • RAG over your knowledge base  (lesson 5)

Run it:
    streamlit run lessons/07_streamlit_ui.py

Your browser will open at http://localhost:8501 with a chat box.
"""

import os
import json
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# We reuse the building blocks you already wrote in earlier lessons.
# This also shows the power of treating each lesson as a module: as your
# project grows, you just import previous tools.
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

from importlib import import_module
lesson4 = import_module("04_multi_tool_agent")    # filenames with leading digits → import_module
lesson5 = import_module("05_rag_knowledge_base")
lesson6 = import_module("06_memory")

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---------------------------------------------------------------------------
# Combine every tool we've built so far into ONE registry + schema list.
# ---------------------------------------------------------------------------
TOOL_REGISTRY = {
    **lesson4.TOOL_REGISTRY,     # price / news / wallet
    "search_knowledge_base": lesson5.search_knowledge_base,
    **lesson6.TOOL_REGISTRY,     # save_fact / recall_facts / forget_fact
}

TOOLS_SPEC = [
    *lesson4.TOOLS_SPEC,
    *lesson5.TOOLS_SPEC,
    *lesson6.TOOLS_SPEC,
]

SYSTEM_PROMPT = (
    "You are a friendly crypto research assistant. "
    "You have tools for (a) live market prices, (b) recent crypto news, "
    "(c) on-chain ETH wallet balances, (d) semantic search over a local "
    "knowledge base of primers, and (e) a persistent memory for facts "
    "about the user. "
    "At the start of a new conversation, call `recall_facts` once so you "
    "know what you already know. "
    "Never invent prices, balances, or news — use the tools. "
    "For conceptual questions (what is MEV? what is PoS?), use "
    "`search_knowledge_base` and cite the source filename. "
    "When the user volunteers durable personal info (their wallet, their "
    "risk tolerance, their favorite chain), call `save_fact`."
)


# ---------------------------------------------------------------------------
# Agent step — same loop as before, no surprises.
# ---------------------------------------------------------------------------
def run_turn(messages: list, max_steps: int = 8) -> str:
    for _ in range(max_steps):
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
            try:
                result = fn(**args) if fn else {"error": "unknown tool"}
            except Exception as e:
                result = {"error": str(e)}
            messages.append(
                {"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)}
            )
    return "(agent hit max_steps)"


# ---------------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Crypto Agent", page_icon="🪙", layout="centered")
st.title("🪙 Crypto Research Agent")
st.caption("Lesson 7 — price + news + on-chain + RAG + memory, in one chat UI.")

# Session state holds the conversation across reruns (Streamlit re-runs the
# whole script every interaction, so we stash things in st.session_state).
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

# Render past messages (skip the system prompt; skip tool-call-only messages).
for m in st.session_state.messages:
    role = m["role"] if isinstance(m, dict) else getattr(m, "role", None)
    content = m.get("content") if isinstance(m, dict) else getattr(m, "content", None)
    if role in ("user", "assistant") and content:
        with st.chat_message(role):
            st.markdown(content)

# Input box at the bottom.
if prompt := st.chat_input("Ask me about crypto..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            reply = run_turn(st.session_state.messages)
        st.markdown(reply)

# Sidebar: inspect and clear memories.
with st.sidebar:
    st.header("Memory")
    if st.button("Show long-term facts"):
        st.json(lesson6.recall_facts())
    if st.button("Clear long-term memory"):
        lesson6.MEMORY_FILE.write_text("{}")
        st.success("Long-term memory cleared.")
    if st.button("Reset this chat"):
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.rerun()

    st.divider()
    st.markdown(
        "**Try asking**\n"
        "- What's the price of ETH in EUR?\n"
        "- Summarize one Ethereum news story from today.\n"
        "- My wallet is 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045. Save it.\n"
        "- What's my wallet balance?\n"
        "- Explain MEV in 3 sentences.\n"
    )

# ---------------------------------------------------------------------------
# Where to go from here
# ---------------------------------------------------------------------------
# You've built, end-to-end, what most \"AI agent\" products under the hood
# actually are. From here, natural next steps:
#
# • Swap the model: try gpt-4o for tougher reasoning; Anthropic's Claude
#   or a local Llama via Ollama for privacy/cost.
#
# • Add more tools: DeFiLlama TVL, Dune Analytics SQL queries,
#   Etherscan transaction history, Twitter/X sentiment.
#
# • Add evals: write a small test set of Q&A pairs; run them nightly to
#   catch regressions when you change prompts or models.
#
# • Reach for a framework ONLY WHEN YOU HIT A WALL. LangGraph is great for
#   branching/parallel tool use. CrewAI is great for multi-agent teams.
#   You'll use them effectively BECAUSE you understand the raw loop.
# ---------------------------------------------------------------------------
