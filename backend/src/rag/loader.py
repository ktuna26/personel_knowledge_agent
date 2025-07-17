# backend/src/rag/loader.py
"""
Document Loader for the RAG pipeline.
- Loads, parses, and chunks text/markdown/pdf docs from directory (recursive).
- Yields LangChain Document objects with metadata.
- Supports robust logging and error handling.
"""

import logging
from pathlib import Path
from typing import List, Optional, Union, Dict

from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None  # PDF support will error if used

logger = logging.getLogger(__name__)

def load_text_file(file_path: Union[str, Path]) -> str:
    """
    Load plain text content from a text or markdown file.

    Args:
        file_path: Path to file.
    Returns:
        The file content as a string.
    """
    file_path = Path(file_path)
    try:
        with file_path.open("r", encoding="utf-8-sig") as file:
            text = file.read()
            logger.debug(f"Loaded text file: {file_path}")
            return text
    except Exception as e:
        logger.error(f"Failed to read {file_path}: {e}")
        raise

def load_pdf_file(file_path: Union[str, Path]) -> str:
    """
    Extract all text from a PDF.
    """
    if PdfReader is None:
        raise ImportError("PyPDF2 is required for PDF support.")
    file_path = Path(file_path)
    try:
        with file_path.open("rb") as file:
            reader = PdfReader(file)
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            logger.debug(f"Loaded PDF {file_path} with {len(reader.pages)} pages")
            return text
    except Exception as e:
        logger.error(f"Failed to read PDF {file_path}: {e}")
        raise

def load_documents_from_dir(
    directory: Union[str, Path],
    extensions: Optional[List[str]] = None
) -> List[Document]:
    """
    Recursively loads documents from directory, filtered by extension.

    Args:
        directory: Directory to scan.
        extensions: Allowed extensions (default [".txt", ".md", ".pdf"])
    Returns:
        List of LangChain Documents.
    """
    directory = Path(directory)
    if not directory.exists() or not directory.is_dir():
        logger.error(f"Directory {directory} does not exist or is not a directory.")
        raise ValueError(f"Directory {directory} does not exist or is not a directory.")

    allowed_exts = extensions or [".txt", ".md", ".pdf"]
    documents = []

    for file_path in directory.rglob("*"):
        if file_path.suffix.lower() not in allowed_exts:
            continue

        try:
            if file_path.suffix.lower() == ".pdf":
                content = load_pdf_file(file_path)
            else:
                content = load_text_file(file_path)
            if not content.strip():
                logger.warning(f"Skipping empty file: {file_path}")
                continue

            # Add richer metadata
            stat = file_path.stat()
            metadata = {
                "source": str(file_path.resolve()),
                "filename": file_path.name,
                "extension": file_path.suffix.lower(),
                "size": stat.st_size
            }
            documents.append(Document(page_content=content, metadata=metadata))
            logger.info(f"Loaded document: {file_path}")
        except Exception as e:
            logger.warning(f"Skipping {file_path} due to error: {e}")

    if not documents:
        logger.error(f"No valid documents found in {directory}")
        raise ValueError(f"No valid documents found in directory: {directory}")

    return documents

def chunk_documents(
    documents: List[Document],
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> List[Document]:
    """
    Chunk each document into smaller pieces.
    Args:
        documents: List of LangChain Documents.
        chunk_size: Max chars per chunk.
        chunk_overlap: Overlap chars between chunks.
    Returns:
        List of chunked LangChain Documents.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    # It's efficient enough to do per-doc splitting for most corpora
    chunked_docs = []
    for doc in documents:
        chunks = splitter.split_documents([doc])
        chunked_docs.extend(chunks)
    logger.info(f"Chunked {len(documents)} docs into {len(chunked_docs)} chunks")
    return chunked_docs

def load_and_chunk_documents(
    source_dir: Union[str, Path],
    extensions: Optional[List[str]] = None,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> List[Document]:
    """
    Load and chunk documents from a directory.
    Args:
        source_dir: Directory containing documents.
        extensions: Allowed file extensions.
        chunk_size: Chunk size in characters.
        chunk_overlap: Overlap size.
    Returns:
        List of chunked LangChain Documents.
    """
    docs = load_documents_from_dir(source_dir, extensions)
    return chunk_documents(docs, chunk_size, chunk_overlap)

def load_single_document(
    file_path: Union[str, Path]
) -> Document:
    """
    Load a single document file as a LangChain Document.
    """
    file_path = Path(file_path)
    ext = file_path.suffix.lower()
    if ext == ".pdf":
        content = load_pdf_file(file_path)
    elif ext in (".txt", ".md"):
        content = load_text_file(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")
    metadata = {
        "source": str(file_path.resolve()),
        "filename": file_path.name,
        "extension": ext,
        "size": file_path.stat().st_size
    }
    return Document(page_content=content, metadata=metadata)
