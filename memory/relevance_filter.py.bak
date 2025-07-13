# memory/relevance_filter.py

from gemini_interface.gemini_client import call_gemini_with_tools

def filter_relevant_chunks(user_input: str, chunks: list, top_n: int = 5):
    """
    Uses Gemini to identify the most relevant memory chunks from a list.
    """
    if not chunks:
        return []

    # Normalize and number the chunks for the AI to see
    text_chunks = [
        c["text"].strip() if isinstance(c, dict) else str(c).strip()
        for c in chunks
    ]
    numbered_list = "\n".join(f"{i+1}. {chunk}" for i, chunk in enumerate(text_chunks))

    prompt = f"""
You are an intelligent memory assistant.
Your job is to identify which pieces of prior memory are most relevant to the current user input.
From the numbered list below, select the {top_n} most relevant memory snippets.
Call the `select_relevant_memories` tool with the corresponding numbers as a list of integers.

Current player input: "{user_input.strip()}"

Prior memory:
{numbered_list}
"""
    # Note: Because this tool doesn't use the database, we can pass `None` for the db_session and session_id.
    # The client needs a slight modification to handle this gracefully.
    selected_indices = call_gemini_with_tools(None, None, prompt)

    # The AI will return a list of integers directly.
    # We add a check to ensure the response is what we expect.
    if isinstance(selected_indices, list):
        # We subtract 1 from the AI's 1-based numbering
        return [chunks[i - 1] for i in selected_indices if 0 < i <= len(chunks)]

    # Fallback if the tool call fails for some reason
    print("Warning: Relevance filter did not return a list. Falling back to top N.")
    return chunks[:top_n]