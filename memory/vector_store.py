import faiss
import os
import pickle
from memory.embeddings import embed_text

INDEX_PATH = "faiss_index.bin"
META_PATH = "faiss_meta.pkl"

def build_index(chunks):
    texts = [c["text"] for c in chunks]
    vectors = embed_text(texts)

    index = faiss.IndexFlatL2(vectors.shape[1])
    index.add(vectors)

    with open(META_PATH, "wb") as f:
        pickle.dump(chunks, f)
    faiss.write_index(index, INDEX_PATH)

def load_index():
    if not os.path.exists(INDEX_PATH) or not os.path.exists(META_PATH):
        return None, []
    index = faiss.read_index(INDEX_PATH)
    with open(META_PATH, "rb") as f:
        chunks = pickle.load(f)
    return index, chunks