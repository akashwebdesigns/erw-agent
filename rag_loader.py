import faiss
import pickle

INDEX_PATH = "rag/index.faiss"
META_PATH = "rag/metadata.pkl"


def load_rag():

    index = faiss.read_index(INDEX_PATH)

    with open(META_PATH, "rb") as f:
        metadata = pickle.load(f)

    return index, metadata
