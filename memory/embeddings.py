# memory/embeddings.py

import os
from sentence_transformers import SentenceTransformer
from openai import OpenAI

_use_openai = os.getenv("USE_OPENAI_EMBEDDINGS", "false").lower() == "true"
_model = None

def load_embedding_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def embed_text(texts):
    """
    Returns list of vector embeddings.
    Uses OpenAI if USE_OPENAI_EMBEDDINGS=true in .env
    """
    if _use_openai:
        return _embed_with_openai(texts)
    else:
        model = load_embedding_model()
        return model.encode(texts, convert_to_numpy=True)

def _embed_with_openai(texts):
    client = OpenAI()
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=texts
    )
    return [e.embedding for e in response.data]
