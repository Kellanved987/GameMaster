# memory/ingest.py

from memory.chunker import chunk_text
from memory.index import add_chunks

def chunk_and_store(text: str, session_id: int, max_words: int = 200, overlap: int = 20) -> list[str]:
    """
    Chunks text, embeds, and adds to vector index for session.
    Returns the list of text chunks stored.
    """
    chunks = chunk_text(text, max_words=max_words, overlap=overlap)
    add_chunks(chunks, session_id)
    return chunks
