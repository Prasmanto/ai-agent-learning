"""
LESSON 5 — RAG: Teach the Agent from Documents
==============================================

So far our agent uses LIVE tools (APIs). But a lot of knowledge is in
static documents: whitepapers, protocol docs, glossaries, your own notes.

Two (bad) ways to handle this:
  1. Paste the whole book into every prompt → too expensive, too slow.
  2. Fine-tune a model on the docs → expensive, slow to update, overkill.

The right way: **RAG — Retrieval-Augmented Generation.**

     ┌─────────────────────────────────────────────────────────┐
     │ ONE-TIME INGESTION (done once, or whenever docs change) │
     │                                                         │
     │ docs → chunk them → embed each chunk → store in a       │
     │                                     vector database     │
     └─────────────────────────────────────────────────────────┘

     ┌─────────────────────────────────────────────────────────┐
     │ EVERY USER QUESTION                                     │
     │                                                         │
     │ question → embed → find top-K most-similar chunks →     │
     │ paste those chunks into the prompt → LLM answers        │
     └─────────────────────────────────────────────────────────┘

What's an "embedding"?
----------------------
A function that turns a piece of text into a fixed-length vector of
numbers (e.g. 1536 floats). Texts with similar MEANING end up close
together in that vector space. "Ethereum is PoS" and "ETH uses
proof-of-stake" will be nearby; "pizza recipe" will be far away.

What's a "vector database"?
---------------------------
A database optimized for "find the N vectors closest to this one".
We use Chroma because it runs locally, no server, no API key.

This lesson:
  1. Reads every .md file in data/knowledge/
  2. Splits them into chunks
  3. Embeds and stores them in a local Chroma DB (data/chroma/)
  4. Wraps the whole thing as a TOOL the agent can call.
  5. The agent now has a new superpower: it can "look up" facts from
     your documents the same way it looks up live prices.

Run it:
    python lessons/05_rag_knowledge_base.py
"""

import os
import json
import glob
from dotenv import load_dotenv
from openai import OpenAI
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# ---------------------------------------------------------------------------
# Paths — the knowledge base lives in data/knowledge/ and the vector DB
# is persisted to data/chroma/ so we don't re-embed on every run.
# ---------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
KNOWLEDGE_DIR = os.path.join(ROOT, "data", "knowledge")
CHROMA_DIR = os.path.join(ROOT, "data", "chroma")
COLLECTION_NAME = "crypto_kb"

# ---------------------------------------------------------------------------
# STEP A — Chunking
# ---------------------------------------------------------------------------
# LLMs are bad at picking the needle from a huge haystack. We split each
# document into ~500-char chunks with a small overlap so a single concept
# isn't sliced in half. Real systems use smarter splitters (e.g. by heading).
def chunk_text(text: str, chunk_size: int = 500, overlap: int = 80) -> list[str]:
    chunks = []
    i = 0
    while i < len(text):
        chunks.append(text[i : i + chunk_size])
        i += chunk_size - overlap
    return [c.strip() for c in chunks if c.strip()]


# ---------------------------------------------------------------------------
# STEP B — Build (or reuse) the vector DB
# ---------------------------------------------------------------------------
def build_or_load_collection():
    """
    Returns a Chroma collection that contains every chunk of every .md
    file under data/knowledge/. Idempotent: if the collection already has
    as many chunks as the filesystem, we skip re-embedding.
    """
    db = chromadb.PersistentClient(path=CHROMA_DIR)
    embedder = OpenAIEmbeddingFunction(
        api_key=OPENAI_API_KEY,
        model_name="text-embedding-3-small",   # cheap + good enough
    )
    coll = db.get_or_create_collection(name=COLLECTION_NAME, embedding_function=embedder)

    # Gather all chunks from disk.
    files = sorted(glob.glob(os.path.join(KNOWLEDGE_DIR, "*.md")))
    docs, ids, metas = [], [], []
    for path in files:
        with open(path, encoding="utf-8") as f:
            text = f.read()
        for idx, chunk in enumerate(chunk_text(text)):
            docs.append(chunk)
            ids.append(f"{os.path.basename(path)}::chunk-{idx}")
            metas.append({"source": os.path.basename(path), "chunk": idx})

    if coll.count() == len(docs) and len(docs) > 0:
        print(f"✅ Knowledge base already indexed ({coll.count()} chunks). Skipping embedding.")
        return coll

    # Rebuild from scratch for simplicity — fine for small KBs.
    if coll.count() > 0:
        print("♻️  Knowledge base changed; rebuilding index...")
        db.delete_collection(COLLECTION_NAME)
        coll = db.get_or_create_collection(name=COLLECTION_NAME, embedding_function=embedder)

    print(f"⏳ Embedding {len(docs)} chunks from {len(files)} file(s)...")
    coll.add(ids=ids, documents=docs, metadatas=metas)
    print(f"✅ Indexed {coll.count()} chunks into Chroma at {CHROMA_DIR}")
    return coll


# ---------------------------------------------------------------------------
# STEP C — The retrieval tool the agent will use
# ---------------------------------------------------------------------------
# We expose RAG as just another TOOL. To the agent loop from lesson 3/4,
# it looks identical to a price lookup — but instead of hitting an API,
# it queries a vector DB.
_collection = None
def _get_collection():
    global _collection
    if _collection is None:
        _collection = build_or_load_collection()
    return _collection


def search_knowledge_base(query: str, k: int = 4) -> dict:
    """Semantic search over the local crypto knowledge base."""
    coll = _get_collection()
    res = coll.query(query_texts=[query], n_results=k)
    hits = []
    for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        hits.append(
            {
                "source": meta.get("source"),
                "chunk": meta.get("chunk"),
                # Chroma returns squared-L2 distance for the default metric.
                "distance": round(float(dist), 4),
                "text": doc,
            }
        )
    return {"query": query, "hits": hits}


# ---------------------------------------------------------------------------
# STEP D — Same agent loop, with ONE new tool
# ---------------------------------------------------------------------------
TOOL_REGISTRY = {"search_knowledge_base": search_knowledge_base}

TOOLS_SPEC = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": (
                "Semantic search over a curated crypto/Web3 knowledge base "
                "(primers on Bitcoin and Ethereum, and a DeFi glossary). "
                "Use this for conceptual questions ('what is MEV?', 'how does "
                "proof-of-stake work?'), not for live prices or market data. "
                "Returns the most relevant text chunks with their source file."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The user's question, rephrased as a search query."},
                    "k": {"type": "integer", "description": "How many chunks to retrieve (default 4, max 8)."},
                },
                "required": ["query"],
            },
        },
    }
]

SYSTEM_PROMPT = (
    "You are a crypto tutor. You have a tool `search_knowledge_base` that "
    "retrieves passages from a curated knowledge base. "
    "For any conceptual question, FIRST call the tool, then answer using "
    "those passages. Cite the source filename (e.g. 'source: ethereum.md') "
    "inline. If the KB does not contain the answer, say so honestly "
    "instead of guessing."
)


def run_agent(question: str, max_steps: int = 4, verbose: bool = True) -> str:
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
            return msg.content
        messages.append(msg)
        for call in msg.tool_calls:
            name = call.function.name
            args = json.loads(call.function.arguments or "{}")
            if verbose:
                print(f"LLM → wants to call: {name}({args})")
            fn = TOOL_REGISTRY.get(name)
            result = fn(**args) if fn else {"error": f"Unknown tool: {name}"}
            if verbose:
                preview = json.dumps(result)
                print(f"Tool → {preview[:220]}{'...' if len(preview) > 220 else ''}")
            messages.append(
                {"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)}
            )
    return "⚠️ Agent hit max_steps without finishing."


if __name__ == "__main__":
    # Ingest once at startup so the first question is fast.
    _get_collection()

    question = (
        "Explain what MEV is, how it typically happens on an AMM, and why "
        "proof-of-stake didn't eliminate it. Keep it to 5 sentences."
    )
    print("\nUSER QUESTION:", question)
    answer = run_agent(question, verbose=True)
    print("\n" + "=" * 60)
    print("FINAL ANSWER")
    print("=" * 60)
    print(answer)
    print("=" * 60)

# ---------------------------------------------------------------------------
# What just happened?
# ---------------------------------------------------------------------------
# • On first run, every .md file in data/knowledge/ was chunked, embedded,
#   and stored locally in data/chroma/. This takes a few seconds and costs
#   a fraction of a cent.
# • On subsequent runs, the DB is reused — fast and free.
# • When you asked about MEV, the agent turned your question into a vector,
#   Chroma returned the top 4 most-similar chunks, and the model composed
#   an answer grounded in YOUR documents — not its training data.
#
# EXERCISES
# ---------
# 1. Drop your own .md file into data/knowledge/ (e.g. notes on a protocol
#    you care about). Re-run — the agent will pick it up automatically.
#
# 2. Ask a question whose answer is NOT in the KB (e.g. "What is Monero?").
#    A well-behaved agent should admit ignorance. If yours hallucinates,
#    tighten the system prompt.
#
# 3. Combine lessons 4 and 5: in one script, register BOTH the RAG tool
#    AND the price/news/wallet tools. You now have an agent that can
#    reason over concepts AND live data in the same conversation. This is
#    essentially what ChatGPT-with-browsing does.
# ---------------------------------------------------------------------------
