# memory/index.py

import faiss
import numpy as np
from memory.embeddings import embed_text

# Each session gets its own FAISS index
# Maps: session_id -> (index, id_to_chunk)
_index_store = {}

def _get_or_create_index(session_id: int, dim: int = 384):
    if session_id not in _index_store:
        index = faiss.IndexFlatL2(dim)
        id_to_chunk = []
        _index_store[session_id] = (index, id_to_chunk)
    return _index_store[session_id]

def add_chunks(chunks: list[str], session_id: int):
    vectors = embed_text(chunks)
    index, id_to_chunk = _get_or_create_index(session_id, dim=vectors.shape[1])
    index.add(np.array(vectors))
    id_to_chunk.extend(chunks)

def search_chunks(query: str, session_id: int, k: int = 5) -> list[str]:
    index, id_to_chunk = _get_or_create_index(session_id)
    query_vec = embed_text([query])

    # Make sure we don't ask for more chunks than exist
    k = min(k, len(id_to_chunk))
    if k == 0:
        return []

    D, I = index.search(np.array(query_vec), k)

    # Filter out invalid indices
    return [id_to_chunk[i] for i in I[0] if 0 <= i < len(id_to_chunk)]
