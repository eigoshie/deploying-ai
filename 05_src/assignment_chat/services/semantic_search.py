# Service 2 (semantic search): hybrid lexical + semantic search over a
# hand-curated dataset of 120 zoo animals, backed by a persistent
# ChromaDB collection.
#
# data/build_dataset.py writes data/animal_facts.csv (see that file for
# why it's hand-typed instead of scraped). The first time
# get_or_build_collection() runs, it embeds each row's "description"
# text into Chroma at data/chroma_db/; after that it just loads the
# saved vectors from disk.
#
# Embedding model: OpenAI's text-embedding-3-small by default (reuses
# the same OPENAI_API_KEY as the chat model). Falls back to Chroma's
# local ONNX model if no key is set (downloads once, then works
# offline). Force the local model with EMBEDDING_BACKEND=local.
#
# Hybrid part: first check for an exact animal-name match in the query
# (lexical), then run the vector search to fill in the rest
# (semantic) -- this is the "lexical search followed by semantic
# search" approach mentioned in the assignment.

import os
import chromadb
import pandas as pd
from chromadb.utils import embedding_functions

from core.config import OPENAI_API_KEY

THIS_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(THIS_DIR, "data")
CSV_PATH = os.path.join(DATA_DIR, "animal_facts.csv")
CHROMA_PATH = os.path.join(DATA_DIR, "chroma_db")
COLLECTION_NAME = "animal_facts"

_collection = None  # cached so we don't reopen it on every message

SEARCH_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_animal_facts",
        "description": (
            "Search the zoo's animal knowledge base using natural "
            "language. Good for open-ended questions like 'what "
            "animals live in the arctic' or 'show me something "
            "endangered', as well as questions about a specific animal."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The visitor's question, in natural language.",
                },
                "n_results": {
                    "type": "integer",
                    "description": "How many matching animals to return (default 3).",
                },
            },
            "required": ["query"],
        },
    },
}


def get_embedding_function():
    backend = os.getenv("EMBEDDING_BACKEND")
    if backend is None:
        backend = "openai" if OPENAI_API_KEY else "local"

    if backend == "openai" and OPENAI_API_KEY:
        return embedding_functions.OpenAIEmbeddingFunction(
            api_key=OPENAI_API_KEY, model_name="text-embedding-3-small"
        )
    return embedding_functions.DefaultEmbeddingFunction()


def get_or_build_collection():
    global _collection
    if _collection is not None:
        return _collection

    os.makedirs(CHROMA_PATH, exist_ok=True)
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    ef = get_embedding_function()
    collection = client.get_or_create_collection(name=COLLECTION_NAME, embedding_function=ef)

    if collection.count() == 0:
        df = pd.read_csv(CSV_PATH)

        ids = []
        documents = []
        metadatas = []
        for _, row in df.iterrows():
            ids.append(str(row["id"]))
            documents.append(row["description"])
            metadatas.append({
                "name": row["name"],
                "scientific_name": row["scientific_name"],
                "category": row["category"],
                "habitat": row["habitat"],
                "region": row["region"],
                "diet": row["diet"],
                "conservation_status": row["conservation_status"],
                "fun_fact": row["fun_fact"],
            })

        collection.add(ids=ids, documents=documents, metadatas=metadatas)

    _collection = collection
    return _collection


def find_lexical_matches(query, df, max_matches=2):
    query_lower = query.lower()
    matches = []
    for _, row in df.iterrows():
        if row["name"].lower() in query_lower:
            matches.append(row)
            if len(matches) >= max_matches:
                break
    return matches


def search_animal_facts(query, n_results=3):
    collection = get_or_build_collection()

    n_results = int(n_results) if n_results else 3
    n_results = max(1, min(n_results, 8))

    results_by_name = {}  # avoids adding the same animal twice

    # lexical pass
    try:
        df = pd.read_csv(CSV_PATH)
        for row in find_lexical_matches(query, df):
            results_by_name[row["name"]] = {
                "name": row["name"],
                "scientific_name": row["scientific_name"],
                "category": row["category"],
                "habitat": row["habitat"],
                "region": row["region"],
                "diet": row["diet"],
                "conservation_status": row["conservation_status"],
                "fun_fact": row["fun_fact"],
                "match_type": "lexical",
            }
    except Exception:
        pass

    # semantic pass
    try:
        semantic_results = collection.query(query_texts=[query], n_results=n_results)
        metadatas = semantic_results["metadatas"][0]
        distances = semantic_results["distances"][0]

        for i in range(len(metadatas)):
            meta = metadatas[i]
            name = meta.get("name")
            if name in results_by_name:
                continue
            results_by_name[name] = {
                "name": meta.get("name"),
                "scientific_name": meta.get("scientific_name"),
                "category": meta.get("category"),
                "habitat": meta.get("habitat"),
                "region": meta.get("region"),
                "diet": meta.get("diet"),
                "conservation_status": meta.get("conservation_status"),
                "fun_fact": meta.get("fun_fact"),
                "match_type": "semantic",
                "similarity_distance": round(float(distances[i]), 4),
            }
    except Exception as e:
        if len(results_by_name) == 0:
            return [{"error": "Search failed: " + type(e).__name__}]

    return list(results_by_name.values())[:n_results]
