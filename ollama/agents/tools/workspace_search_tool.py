import os
from pathlib import Path
from typing import List

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
from langchain_community.document_loaders import UnstructuredExcelLoader

# list of extensions treated as simple text and source code
TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".json",
    ".yaml",
    ".yml",
    ".sh",
    ".html",
    ".css",
    ".sql",
    ".c",
    ".cpp",
    ".h",
    ".java",
    ".env",
    ".toml",
}


def _load_single_file(file_path: Path) -> List[Document]:
    """Identifica a extensão do arquivo e usa o carregador apropriado."""
    ext = file_path.suffix.lower()
    try:
        if ext == ".pdf":
            return PyPDFLoader(str(file_path)).load()
        elif ext == ".csv":
            return CSVLoader(str(file_path), encoding="utf-8").load()
        elif ext in TEXT_EXTENSIONS:
            return TextLoader(str(file_path), encoding="utf-8").load()
        elif ext in [".xlsx", ".xls"]:
            try:
                return UnstructuredExcelLoader(str(file_path)).load()
            except ImportError:
                print(
                    f"WARNING: to load Excel files ({file_path.name}), "
                    "install 'openpyxl' and 'unstructured'. Skipping..."
                )
                return []
        else:
            # generic reading attempt for unknown extensions
            return TextLoader(str(file_path), encoding="utf-8").load()
    except Exception as e:
        print(f"Erro ao carregar o arquivo '{file_path.name}': {e}")
        return []


def _load_all_workspace_docs(workspace_dir: str) -> List[Document]:
    """
    search recursively through the workspace folder loading all valid files.
    """
    documents = []
    workspace_path = Path(workspace_dir)

    for file_path in workspace_path.rglob("*"):
        # ignores directories and hidden files (e.g., .gitignore, .DS_Store)
        if file_path.is_file() and not file_path.name.startswith("."):
            docs = _load_single_file(file_path)
            documents.extend(docs)

    return documents


def _get_retriever():
    workspace_dir = "./workspace"
    chroma_dir = "./chroma_db"

    if not os.path.exists(workspace_dir):
        os.makedirs(workspace_dir)

    embeddings = OllamaEmbeddings(model="nomic-embed-text")

    # if the local store was already generated and has data, just reconnect
    if os.path.exists(chroma_dir) and os.listdir(chroma_dir):
        vectorstore = Chroma(persist_directory=chroma_dir, embedding_function=embeddings)
    else:
        # loads files of multiple formats
        docs = _load_all_workspace_docs(workspace_dir)

        if docs:
            splits = RecursiveCharacterTextSplitter(
                chunk_size=1000, chunk_overlap=200
            ).split_documents(docs)

            vectorstore = Chroma.from_documents(
                documents=splits, embedding=embeddings, persist_directory=chroma_dir
            )
        else:
            vectorstore = Chroma(persist_directory=chroma_dir, embedding_function=embeddings)

    return vectorstore.as_retriever(search_kwargs={"k": 3})


@tool
def search_workspace_files(query: str) -> str:
    """
    search information within files (PDFs, code, text, CSVs, etc.)
    saved in the ./workspace folder of the computer.
    """
    retriever = _get_retriever()
    results = retriever.invoke(query)
    if not results:
        return "none relevant documents were found in the workspace folder."

    return "\n---\n".join([doc.page_content for doc in results])
