"""
LESSON 1 — Hello, LLM
=====================

Goal: Understand what an LLM actually IS by talking to one directly.

Mental model
------------
An LLM is a function. You put text in, you get text out.

    text_in  ──►  [ GPT-4 ]  ──►  text_out

That's it. No memory between calls. No internet access. No tools.
Just: "given this text, what text should come next?"

Everything fancy you've heard about (agents, RAG, memory, tools) is just
PYTHON CODE around this one simple function call. We'll build those layers
in later lessons.

In this lesson, we will:
  1. Load our API key from .env
  2. Send one message to GPT-4o-mini
  3. Print the reply

Run it:
    python lessons/01_hello_llm.py
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

# ---------------------------------------------------------------------------
# STEP 1: Load the API key from the .env file in the project root.
# ---------------------------------------------------------------------------
# `load_dotenv()` reads .env and puts its values into os.environ, so
# `os.getenv("OPENAI_API_KEY")` returns your real key.
#
# WHY .env?  So we never hard-code secrets in code that might get pushed
# to GitHub.
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key or api_key.startswith("sk-replace"):
    raise SystemExit(
        "❌ No OPENAI_API_KEY found. Copy .env.example to .env and paste your key."
    )

# ---------------------------------------------------------------------------
# STEP 2: Create the OpenAI client.
# ---------------------------------------------------------------------------
# Think of `client` as a remote control for OpenAI's servers.
client = OpenAI(api_key=api_key)

# ---------------------------------------------------------------------------
# STEP 3: Send a message.
# ---------------------------------------------------------------------------
# The "messages" list is a conversation. Each item has a ROLE and CONTENT.
# Three roles exist:
#   - "system"    → hidden instructions that shape the model's behavior
#   - "user"      → what a human said
#   - "assistant" → what the model said back (we'll see this in lesson 3)
#
# Here we tell it to act as a crypto teacher, and we ask one beginner question.
messages = [
    {
        "role": "system",
        "content": (
            "You are a friendly crypto and Web3 teacher. "
            "Explain things simply, using plain English and short examples. "
            "Avoid jargon unless you define it."
        ),
    },
    {
        "role": "user",
        "content": "In 3 short paragraphs, explain what a blockchain is to a total beginner.",
    },
]

# The actual API call. `model` picks which LLM to use.
# gpt-4o-mini is cheap (~$0.0001 per call) and smart enough for learning.
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=messages,
    temperature=0.3,   # 0 = deterministic, 1 = creative. 0.3 = mostly factual.
)

# ---------------------------------------------------------------------------
# STEP 4: Read the reply.
# ---------------------------------------------------------------------------
# The response object is nested. The actual text we want lives at:
#   response.choices[0].message.content
reply = response.choices[0].message.content

print("=" * 60)
print("ASSISTANT REPLY")
print("=" * 60)
print(reply)
print("=" * 60)

# Bonus info: how many tokens we used (= how much it cost).
usage = response.usage
print(
    f"\nTokens used — prompt: {usage.prompt_tokens}, "
    f"reply: {usage.completion_tokens}, "
    f"total: {usage.total_tokens}"
)

# ---------------------------------------------------------------------------
# EXERCISES (try these — just edit the file and re-run)
# ---------------------------------------------------------------------------
# 1. Change the system prompt to: "You are a grumpy crypto veteran from 2013.
#    You hate hype. Reply in a sarcastic tone." Re-run. Notice how PERSONALITY
#    comes entirely from the system prompt.
#
# 2. Change temperature to 0.0 and run twice. Same answer?
#    Now change it to 1.2 and run twice. Different answers?
#
# 3. Ask: "What is the current price of Bitcoin?"
#    → The model will either refuse or make something up. WHY? Because LLMs
#      have NO live internet access and their training data is frozen.
#    → This is exactly why we need TOOLS. That's lesson 2.
# ---------------------------------------------------------------------------
