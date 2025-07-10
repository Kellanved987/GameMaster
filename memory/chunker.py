# memory/chunker.py

def chunk_text(text: str, max_words: int = 200, overlap: int = 20) -> list[str]:
    """
    Splits input text into overlapping chunks of words.

    Args:
        text (str): Full input text to be chunked.
        max_words (int): Max words per chunk (default 200).
        overlap (int): Number of words to overlap between chunks.

    Returns:
        list[str]: List of text chunks.
    """
    words = text.split()
    chunks = []

    i = 0
    while i < len(words):
        chunk = words[i:i + max_words]
        chunks.append(" ".join(chunk))
        i += max_words - overlap  # step forward with overlap

    return chunks
