import os
import sys
from pathlib import Path
from typing import List

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(ROOT_DIR))

from langchain_core.documents import Document
from langchain_core.tools import tool
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    CSVLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter

from logs.cmd.setup_logger import get_logger

LOG_NAME = "workspace_search_tool"
logger = get_logger(name=LOG_NAME)

TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".py",
    ".js",
    ".ts",
    ".json",
    ".yaml",
    ".yml",
    ".sh",
    ".html",
    ".css",
    ".sql",
    ".env",
    ".toml",
}

IGNORE_DIRS = {".venv", ".git", "__pycache__", "chroma_db", "logs"}


def _load_single_file(file_path: Path) -> List[Document]:
    ext = file_path.suffix.lower()
    try:
        if ext == ".pdf":
            return PyPDFLoader(str(file_path)).load()
        elif ext == ".csv":
            return CSVLoader(str(file_path), encoding="utf-8").load()
        elif ext in TEXT_EXTENSIONS:
            return TextLoader(str(file_path), encoding="utf-8").load()
        else:
            return TextLoader(str(file_path), encoding="utf-8").load()
    except Exception as e:
        logger.debug(
            f"ignoring {file_path.name} format not supported (Binary/Unsupported): {e}"
        )
        return []


def _load_all_workspace_docs(workspace_dir: Path) -> List[Document]:
    documents = []

    for file_path in workspace_dir.rglob("*"):
        if any(part in IGNORE_DIRS for part in file_path.parts):
            continue

        if file_path.is_file() and not file_path.name.startswith("."):
            docs = _load_single_file(file_path)
            documents.extend(docs)

    return documents


def _get_retriever():
    workspace_dir = ROOT_DIR
    chroma_dir = ROOT_DIR / "chroma_db"

    embeddings = OllamaEmbeddings(model="nomic-embed-text")

    if os.path.exists(chroma_dir) and os.listdir(chroma_dir):
        logger.info("loading existing local database...")
        vectorstore = Chroma(persist_directory=str(chroma_dir), embedding_function=embeddings)
    else:
        logger.info(f"mapping files in repository: {workspace_dir}")
        docs = _load_all_workspace_docs(workspace_dir)

        if docs:
            splits = RecursiveCharacterTextSplitter(
                chunk_size=1000, chunk_overlap=200
            ).split_documents(docs)

            vectorstore = Chroma.from_documents(
                documents=splits, embedding=embeddings, persist_directory=str(chroma_dir)
            )
        else:
            vectorstore = Chroma(
                persist_directory=str(chroma_dir), embedding_function=embeddings
            )

    return vectorstore.as_retriever(search_kwargs={"k": 5})


@tool
def search_workspace_files(query: str) -> str:
    """
    search information within files (PDFs, code, text, CSVs, etc.)
    saved in the entire project repository.
    """
    logger.info(f"searching in local files: {query}")
    retriever = _get_retriever()
    results = retriever.invoke(query)

    if not results:
        return "SYSTEM_ERROR: no relevant documents found. Tell the user the file might not exist or the keywords do not match."  # noqa E501

    return "\n---\n".join([doc.page_content for doc in results])
