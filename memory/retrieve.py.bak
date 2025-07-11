# memory/retrieve.py

from memory.index import search_chunks
from memory.relevance_filter import filter_relevant_chunks

def retrieve_relevant_chunks(user_input: str, session_id: int, top_k: int = 8):
    """
    Retrieves top-k relevant memory chunks for the given session and query.
    Uses vector similarity + GPT relevance filter.
    """
    rough_matches = search_chunks(session_id, user_input, k=top_k)
    refined = filter_relevant_chunks(user_input, rough_matches, top_n=5)
    return [{"text": chunk} for chunk in refined]
