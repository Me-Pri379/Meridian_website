from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .config import get_settings
from .utils import ensure_dir, read_json, write_json_atomic

INDEX_DIR_NAME = "policy_faiss_index"
METADATA_FILE_NAME = "policy_vectorstore_metadata.json"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 300
SEARCH_K = 4


def _get_settings():
    return get_settings()


def _load_policy_documents() -> list[Any]:
    settings = _get_settings()
    policy_dir = settings.policy_dir
    if not policy_dir.exists():
        raise FileNotFoundError(f"Policy documents directory not found at {policy_dir}")

    documents = []
    pdf_files = sorted([p for p in policy_dir.iterdir() if p.suffix.lower() == ".pdf"])
    for pdf_file in pdf_files:
        loader = PyPDFLoader(str(pdf_file))
        pages = loader.load()
        documents.extend(pages)
    return documents


def _create_splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )


def _metadata_path(index_dir: Path) -> Path:
    return index_dir / METADATA_FILE_NAME


def _vectorstore_dir() -> Path:
    settings = _get_settings()
    return ensure_dir(settings.vector_db_dir / INDEX_DIR_NAME)


def _embedding_model() -> OpenAIEmbeddings:
    settings = _get_settings()
    return OpenAIEmbeddings(model=settings.embedding_model)


def _load_vectorstore(index_dir: Path, embeddings: OpenAIEmbeddings) -> FAISS | None:
    if not index_dir.exists():
        return None
    metadata_path = _metadata_path(index_dir)
    if not metadata_path.exists():
        return None

    metadata = read_json(metadata_path)
    settings = _get_settings()
    if metadata.get("embedding_model") != settings.embedding_model:
        return None

    try:
        return FAISS.load_local(str(index_dir), embeddings)
    except Exception:
        return None


def _persist_vectorstore(vectorstore: FAISS, index_dir: Path) -> None:
    vectorstore.save_local(str(index_dir))
    settings = _get_settings()
    metadata = {
        "embedding_model": settings.embedding_model,
        "created_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "index_dir": str(index_dir),
    }
    write_json_atomic(_metadata_path(index_dir), metadata)


def load_or_build_policy_retriever():
    index_dir = _vectorstore_dir()
    embeddings = _embedding_model()
    vectorstore = _load_vectorstore(index_dir, embeddings)
    if vectorstore is not None:
        return vectorstore.as_retriever(search_kwargs={"k": SEARCH_K})

    documents = _load_policy_documents()
    splitter = _create_splitter()
    chunks = splitter.split_documents(documents)
    vectorstore = FAISS.from_documents(chunks, embeddings)
    _persist_vectorstore(vectorstore, index_dir)
    return vectorstore.as_retriever(search_kwargs={"k": SEARCH_K})


_policy_retriever_chain: Any | None = None


def get_policy_retriever_chain():
    global _policy_retriever_chain
    if _policy_retriever_chain is None:
        _policy_retriever_chain = load_or_build_policy_retriever()
    return _policy_retriever_chain
