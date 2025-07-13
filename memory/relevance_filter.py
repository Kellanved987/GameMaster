# memory/relevance_filter.py

from gemini_interface.gemini_client import call_gemini_with_tools

def filter_relevant_chunks(user_input: str, chunks: list, top_n: int = 5):
    """
    Uses Gemini to identify the most relevant memory chunks from a list.
    """
    if not chunks:
        return []

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
    # --- THIS IS THE FIX ---
    # We now call with return_after_tools=True. This tells the client to execute the
    # 'select_relevant_memories' tool and return its result directly, preventing a loop.
    response = call_gemini_with_tools(None, None, prompt, model_name='gemini-2.5-flash', return_after_tools=True)

    if isinstance(response, list):
        try:
            selected_indices = [int(i) for i in response]
            return [chunks[i - 1] for i in selected_indices if 0 < i <= len(chunks)]
        except (ValueError, TypeError):
            print("Warning: Relevance filter returned a list with invalid data.")
            return chunks[:top_n]

    print("Warning: Relevance filter did not return a list. Falling back to top N.")
    return chunks[:top_n]
