"""
Pinecone vector store management: index creation, JSONL ingestion, and semantic search.
"""

import json
import hashlib
from pathlib import Path
from pinecone import Pinecone, ServerlessSpec
from config.settings import (
    PINECONE_API_KEY,
    PINECONE_INDEX_NAME,
    PINECONE_DIMENSION,
    PINECONE_METRIC,
    PINECONE_NAMESPACE_QA,
    PINECONE_NAMESPACE_KB,
)

KNOWLEDGE_DIR = Path(__file__).parent.parent / "data" / "knowledge_base"
BATCH_SIZE = 96  # Pinecone recommended batch size


def _get_pinecone_client() -> Pinecone:
    if not PINECONE_API_KEY:
        raise ValueError("PINECONE_API_KEY is not set. Add it to your .env file.")
    return Pinecone(api_key=PINECONE_API_KEY)


def _ensure_index(pc: Pinecone) -> None:
    """Create the Pinecone index if it doesn't exist."""
    existing = [idx.name for idx in pc.list_indexes()]
    if PINECONE_INDEX_NAME not in existing:
        pc.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=PINECONE_DIMENSION,
            metric=PINECONE_METRIC,
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        print(f"Created Pinecone index: {PINECONE_INDEX_NAME}")
    else:
        print(f"Pinecone index '{PINECONE_INDEX_NAME}' already exists.")


def _embed_texts(pc: Pinecone, texts: list[str]) -> list[list[float]]:
    """Generate embeddings using Pinecone's built-in inference API."""
    embeddings = pc.inference.embed(
        model="multilingual-e5-large",
        inputs=texts,
        parameters={"input_type": "passage"},
    )
    return [e.values for e in embeddings.data]


def _embed_query(pc: Pinecone, query: str) -> list[float]:
    """Generate embedding for a single query."""
    embeddings = pc.inference.embed(
        model="multilingual-e5-large",
        inputs=[query],
        parameters={"input_type": "query"},
    )
    return embeddings.data[0].values


def ingest_finance_qa(pc: Pinecone) -> int:
    """Ingest finance_qa_dataset.jsonl into Pinecone."""
    filepath = KNOWLEDGE_DIR / "finance_qa_dataset.jsonl"
    if not filepath.exists():
        print(f"File not found: {filepath}")
        return 0

    records = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line.strip())
            records.append(record)

    index = pc.Index(PINECONE_INDEX_NAME)
    total_upserted = 0

    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i : i + BATCH_SIZE]

        # Combine question + answer as the text to embed
        texts = [f"Q: {r['question']} A: {r['answer']}" for r in batch]
        embeddings = _embed_texts(pc, texts)

        vectors = []
        for rec, emb in zip(batch, embeddings):
            vectors.append({
                "id": rec["id"],
                "values": emb,
                "metadata": {
                    "question": rec["question"],
                    "answer": rec["answer"],
                    "topic": rec.get("topic", "general"),
                    "source_file": "finance_qa_dataset.jsonl",
                    "text": texts[batch.index(rec)],
                },
            })

        index.upsert(vectors=vectors, namespace=PINECONE_NAMESPACE_QA)
        total_upserted += len(vectors)
        print(f"  [finance_qa] Upserted batch {i // BATCH_SIZE + 1}: {total_upserted}/{len(records)}")

    print(f"Ingested {total_upserted} records into namespace '{PINECONE_NAMESPACE_QA}'")
    return total_upserted


def ingest_pinecone_kb(pc: Pinecone) -> int:
    """Ingest pinecone_kb.jsonl into Pinecone."""
    filepath = KNOWLEDGE_DIR / "pinecone_kb.jsonl"
    if not filepath.exists():
        print(f"File not found: {filepath}")
        return 0

    records = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line.strip())
            records.append(record)

    index = pc.Index(PINECONE_INDEX_NAME)
    total_upserted = 0

    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i : i + BATCH_SIZE]

        texts = [r["text"] for r in batch]
        embeddings = _embed_texts(pc, texts)

        vectors = []
        for rec, emb in zip(batch, embeddings):
            metadata = rec.get("metadata", {})
            metadata["text"] = rec["text"]
            metadata["source_file"] = "pinecone_kb.jsonl"
            vectors.append({
                "id": rec["id"],
                "values": emb,
                "metadata": metadata,
            })

        index.upsert(vectors=vectors, namespace=PINECONE_NAMESPACE_KB)
        total_upserted += len(vectors)
        print(f"  [pinecone_kb] Upserted batch {i // BATCH_SIZE + 1}: {total_upserted}/{len(records)}")

    print(f"Ingested {total_upserted} records into namespace '{PINECONE_NAMESPACE_KB}'")
    return total_upserted


def query_pinecone(query: str, top_k: int = 5, namespace: str | None = None) -> list[dict]:
    """Query Pinecone for semantically similar documents.
    If namespace is None, queries both namespaces and merges results.
    """
    pc = _get_pinecone_client()
    index = pc.Index(PINECONE_INDEX_NAME)
    query_embedding = _embed_query(pc, query)

    namespaces = [namespace] if namespace else [PINECONE_NAMESPACE_QA, PINECONE_NAMESPACE_KB]
    all_results = []

    for ns in namespaces:
        response = index.query(
            vector=query_embedding,
            top_k=top_k,
            namespace=ns,
            include_metadata=True,
        )
        for match in response.matches:
            all_results.append({
                "id": match.id,
                "score": match.score,
                "namespace": ns,
                "metadata": match.metadata,
            })

    # Sort by score descending, take top_k overall
    all_results.sort(key=lambda x: x["score"], reverse=True)
    return all_results[:top_k]


def run_full_ingestion():
    """Run the complete ingestion pipeline: create index + ingest both JSONL files."""
    print("=" * 60)
    print("Pinecone Ingestion Pipeline")
    print("=" * 60)

    pc = _get_pinecone_client()

    print("\n[Step 1] Ensuring Pinecone index exists...")
    _ensure_index(pc)

    print(f"\n[Step 2] Ingesting finance_qa_dataset.jsonl...")
    qa_count = ingest_finance_qa(pc)

    print(f"\n[Step 3] Ingesting pinecone_kb.jsonl...")
    kb_count = ingest_pinecone_kb(pc)

    print("\n" + "=" * 60)
    print(f"Ingestion complete!")
    print(f"  finance_qa_dataset.jsonl: {qa_count} vectors")
    print(f"  pinecone_kb.jsonl:        {kb_count} vectors")
    print(f"  Total:                    {qa_count + kb_count} vectors")
    print(f"  Index:                    {PINECONE_INDEX_NAME}")
    print("=" * 60)


if __name__ == "__main__":
    run_full_ingestion()
