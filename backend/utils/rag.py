import os
import pickle
import hashlib
import logging
from typing import List

import faiss
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# =========================================================
# CONFIG
# =========================================================

VECTOR_STORE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "vector_store"
)

os.makedirs(VECTOR_STORE_DIR, exist_ok=True)

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

MAX_ROWS_FOR_EMBEDDING = 300
TOP_K_RESULTS = 5

_embedding_model = None


# =========================================================
# EMBEDDING MODEL (LAZY SINGLETON)
# =========================================================

def get_embedding_model():
    global _embedding_model

    if _embedding_model is None:
        logger.info("Loading embedding model...")
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        logger.info("Embedding model loaded.")

    return _embedding_model


# =========================================================
# FILE HASHING
# =========================================================

def generate_file_hash(filepath: str) -> str:
    hasher = hashlib.md5()

    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)

    return hasher.hexdigest()


def get_cache_paths(filepath: str):
    file_hash = generate_file_hash(filepath)

    index_path = os.path.join(
        VECTOR_STORE_DIR,
        f"{file_hash}.faiss"
    )

    metadata_path = os.path.join(
        VECTOR_STORE_DIR,
        f"{file_hash}.pkl"
    )

    return index_path, metadata_path


# =========================================================
# DATAFRAME OPTIMIZATION
# =========================================================

def optimize_dataframe(df: pd.DataFrame) -> pd.DataFrame:

    for col in df.select_dtypes(include=["int64"]).columns:
        df[col] = pd.to_numeric(df[col], downcast="integer")

    for col in df.select_dtypes(include=["float64"]).columns:
        df[col] = pd.to_numeric(df[col], downcast="float")

    return df


# =========================================================
# HIGH SIGNAL ROW SELECTION
# =========================================================

def select_high_signal_rows(df: pd.DataFrame, max_rows: int = MAX_ROWS_FOR_EMBEDDING) -> pd.DataFrame:

    if len(df) <= max_rows:
        return df.drop_duplicates()

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

    if not numeric_cols:
        return df.drop_duplicates().head(max_rows)

    sampled_frames = []

    for col in numeric_cols[:3]:
        try:
            top_values = df.nlargest(max_rows // 6, col)
            bottom_values = df.nsmallest(max_rows // 6, col)

            sampled_frames.append(top_values)
            sampled_frames.append(bottom_values)

        except Exception:
            continue

    sampled_frames.append(
        df.sample(min(max_rows // 3, len(df)), random_state=42)
    )

    combined = pd.concat(sampled_frames, ignore_index=True)
    combined = combined.drop_duplicates()

    return combined.head(max_rows)


# =========================================================
# CHUNK CREATION
# =========================================================

def dataframe_to_chunks(df: pd.DataFrame) -> List[str]:

    chunks = []

    for _, row in df.iterrows():
        row_text = []

        for col in df.columns:
            value = row[col]

            if pd.isna(value):
                continue

            value = str(value).strip()

            if not value:
                continue

            row_text.append(f"{col}: {value}")

        if row_text:
            chunks.append(" | ".join(row_text))

    return list(dict.fromkeys(chunks))


# =========================================================
# VECTOR STORE CREATION
# =========================================================

def build_vector_store(filepath: str):

    index_path, metadata_path = get_cache_paths(filepath)

    if os.path.exists(index_path) and os.path.exists(metadata_path):
        logger.info("Using cached FAISS index.")
        return

    logger.info("Building FAISS vector store...")

    df = pd.read_csv(filepath)

    df = optimize_dataframe(df)
    df = select_high_signal_rows(df)

    chunks = dataframe_to_chunks(df)

    if not chunks:
        raise ValueError("No valid chunks generated.")

    model = get_embedding_model()

    embeddings = model.encode(
        chunks,
        show_progress_bar=False,
        convert_to_numpy=True
    )

    embeddings = np.array(embeddings, dtype=np.float32)

    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)

    faiss.write_index(index, index_path)

    with open(metadata_path, "wb") as f:
        pickle.dump(chunks, f)

    logger.info("FAISS vector store created successfully.")


# =========================================================
# RETRIEVAL
# =========================================================

def retrieve_relevant_chunks(filepath: str, query: str, top_k: int = TOP_K_RESULTS) -> List[str]:

    index_path, metadata_path = get_cache_paths(filepath)

    if not os.path.exists(index_path) or not os.path.exists(metadata_path):
        build_vector_store(filepath)

    index = faiss.read_index(index_path)

    with open(metadata_path, "rb") as f:
        chunks = pickle.load(f)

    model = get_embedding_model()

    query_embedding = model.encode(
        [query],
        show_progress_bar=False,
        convert_to_numpy=True
    )

    query_embedding = np.array(query_embedding, dtype=np.float32)

    _, indices = index.search(query_embedding, top_k)

    results = []
    seen = set()

    for idx in indices[0]:
        if idx >= len(chunks):
            continue

        chunk = chunks[idx]

        if chunk in seen:
            continue

        seen.add(chunk)
        results.append(chunk)

    return results


# =========================================================
# COMPRESSED CONTEXT
# =========================================================

def get_compressed_context(filepath: str, query: str, top_k: int = TOP_K_RESULTS) -> str:
    chunks = retrieve_relevant_chunks(filepath, query, top_k)
    return "\n".join(chunks)


# =========================================================
# BACKWARD COMPATIBILITY (FIXED)
# =========================================================

def add_chunks(filepath: str):
    """
    Backward-compatible wrapper for old imports.
    """
    build_vector_store(filepath)