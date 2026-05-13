# AI Agent Learning — Build a Web3 / Crypto AI Agent from Scratch

Welcome! This is a **beginner-friendly, zero-prior-knowledge course** that teaches you how AI agents work by building one, step by step. The domain we focus on is **Web3 and crypto**, so every example uses real crypto data.

> You do **not** need to know AI, machine learning, or Web3 in depth. You only need:
> - Basic Python (you can read a for-loop and a function)
> - An OpenAI API key (we'll show you how to get one)
> - Curiosity

---

## The big idea (read this once)

An **AI agent** is not magic. It is three boring things glued together:

1. **A brain** — a Large Language Model (LLM) like GPT-4. It reads text and writes text. That's it.
2. **Tools** — normal Python functions (e.g. `get_btc_price()`) that the brain is *allowed to call* when it needs real-world data.
3. **A loop** — code that keeps asking the brain "what do you want to do next?" until the brain says "I'm done, here's the final answer."

That's the whole trick. Everything else (LangChain, CrewAI, AutoGen, etc.) is just fancier versions of this same pattern.

### Visualized

```
          ┌─────────────────────────────────────────┐
          │                 YOU                     │
          │   "What is Bitcoin's price right now?"  │
          └────────────────────┬────────────────────┘
                               │
                               ▼
          ┌─────────────────────────────────────────┐
          │              THE AGENT LOOP             │
          │                                         │
          │   1. Send question + tool list to LLM   │
          │   2. LLM replies: "call get_btc_price"  │
          │   3. Python runs get_btc_price() → $67k │
          │   4. Send result back to LLM            │
          │   5. LLM replies: "BTC is $67,000"      │
          │   6. Done → show answer to user         │
          └─────────────────────────────────────────┘
```

---

## Course structure

Each lesson is a **single Python file** you can run. Every file is heavily commented so reading the code IS the lesson.

| # | Lesson | What you learn |
|---|---|---|
| 1 | `lessons/01_hello_llm.py` | What an LLM is. One prompt in, one answer out. |
| 2 | `lessons/02_llm_with_tool.py` | How to give the LLM a tool (a crypto price function) and let it call that tool. |
| 3 | `lessons/03_agent_loop.py` | The real agent: the LLM decides which tool to call, possibly many times, until it answers. |
| 4 | `lessons/04_multi_tool_agent.py` | Multi-tool agent: live price + crypto news + on-chain ETH wallet balance (web3.py). |
| 5 | `lessons/05_rag_knowledge_base.py` | RAG: embed local markdown docs into a Chroma vector DB and let the agent search them. |
| 6 | `lessons/06_memory.py` | Short-term conversation memory + long-term facts that survive restarts. |
| 7 | `lessons/07_streamlit_ui.py` | Chat UI that combines everything: tools + RAG + memory in a browser. |

### What's where

```
lessons/          one Python file per lesson, runnable on its own
data/knowledge/   markdown primers used by lesson 5's RAG index
data/chroma/      auto-created local vector DB (gitignored)
data/memory.json  auto-created long-term fact store for lesson 6 (gitignored)
```

---

## Setup (5 minutes)

### 1. Install Python 3.10+
Check with:
```bash
python3 --version
```

### 2. Clone and enter the repo
```bash
git clone https://github.com/Prasmanto/ai-agent-learning.git
cd ai-agent-learning
```

### 3. Create a virtual environment
A venv is just an isolated folder of Python packages so you don't pollute your system.
```bash
python3 -m venv .venv
source .venv/bin/activate     # on Windows: .venv\Scripts\activate
```

### 4. Install dependencies
```bash
pip install -r requirements.txt
```

### 5. Get an OpenAI API key
- Go to https://platform.openai.com/api-keys
- Create a key (starts with `sk-...`)
- You get some free credit; lessons 1–3 cost fractions of a cent each.

### 6. Create your `.env`
```bash
cp .env.example .env
```
Then open `.env` and paste your key:
```
OPENAI_API_KEY=sk-your-key-here
```

### 7. Run Lesson 1
```bash
python lessons/01_hello_llm.py
```

If you see the model reply with text, you're set. 🎉

---

## Key vocabulary (bookmark this)

| Term | Plain-English meaning |
|---|---|
| **LLM** | A text-in / text-out AI model. GPT-4, Claude, Llama. |
| **Prompt** | The text you send to the LLM. |
| **System prompt** | Hidden instructions that set the LLM's role ("You are a helpful crypto analyst"). |
| **Token** | A chunk of a word. LLMs charge per token. 1000 tokens ≈ 750 English words. |
| **Tool / Function calling** | A standardized way for the LLM to say "please run function X with these arguments." |
| **Agent** | An LLM that is allowed to call tools in a loop until it finishes a task. |
| **RAG** | "Retrieval-Augmented Generation" — fetching relevant documents and pasting them into the prompt so the LLM can answer from your data. |
| **Embedding** | A list of numbers that represents the meaning of a piece of text. Used for RAG. |
| **Vector database** | A database that stores embeddings and finds the most similar ones. Chroma, Pinecone, etc. |
| **Fine-tuning** | Actually retraining a model on your data. Expensive. Usually NOT needed — RAG is better for most cases. |

---

## Why Web3 / crypto is a great domain to learn on

1. **Free, public data.** Every blockchain is a public database. No auth needed.
2. **Fast-moving.** LLMs have stale training data, so you immediately see *why* agents need live tools.
3. **Lots of APIs.** CoinGecko, DeFiLlama, Etherscan, Alchemy — all free tiers.
4. **Real use cases.** Price research, portfolio tracking, on-chain forensics, news summarization.

---

## Running the later lessons

```bash
# Lesson 4 — multi-tool agent
python lessons/04_multi_tool_agent.py

# Lesson 5 — first run embeds the docs into data/chroma/ (takes a few seconds)
python lessons/05_rag_knowledge_base.py

# Lesson 6 — interactive chatbot with persistent memory
python lessons/06_memory.py

# Lesson 7 — browser chat UI combining everything
streamlit run lessons/07_streamlit_ui.py
```

## Where to go after lesson 7

You now have the mental model to read any framework's docs and understand
what it's actually doing. Natural next steps:

- **Swap models**: try `gpt-4o` for tougher reasoning; Anthropic Claude or
  a local Llama via Ollama for privacy/cost.
- **More tools**: DeFiLlama TVL, Etherscan tx history, Dune Analytics SQL.
- **Evals**: a small test set of Q&A pairs you run nightly to catch
  regressions when prompts or models change.
- **A framework** — but only after you've hit a wall without one.
  LangGraph for branching/parallel tool use; CrewAI for multi-agent teams.

Happy hacking.
