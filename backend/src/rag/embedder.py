# backend/src/rag/embedder.py
"""
Embedding module for the RAG pipeline.

Responsibilities:
- Generate embeddings for document chunks.
- Support pluggable embedding models.
- Provide batch processing for efficiency.
"""

import logging
from typing import List, Optional, Sequence, Tuple, Any

from langchain.docstore.document import Document
from langchain_core.embeddings.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings

logger = logging.getLogger(__name__)


class DocumentEmbedder:
    """
    Handles embedding of documents using a configurable embedding model.
    """

    def __init__(self, embedding_model: Optional[Embeddings] = None, batch_size: Optional[int] = None):
        """
        Initialize the embedder.

        Args:
            embedding_model (Embeddings, optional): LangChain Embeddings instance.
                If None, defaults to OpenAIEmbeddings.
            batch_size (int, optional): Batch size for embedding (if supported).
        """
        if embedding_model is None:
            try:
                self.embedding_model = OpenAIEmbeddings()
                logger.info("Using default OpenAIEmbeddings model.")
            except ImportError as e:
                logger.error("OpenAIEmbeddings not installed. Please install `openai` and `langchain`.")
                raise
        else:
            self.embedding_model = embedding_model
            logger.info(f"Using custom embedding model: {type(embedding_model).__name__}")

        self.batch_size = batch_size

    def embed_documents(self, documents: Sequence[Document]) -> List[List[float]]:
        """
        Generate embeddings for a list of documents.

        Args:
            documents (Sequence[Document]): List of LangChain Document objects.

        Returns:
            List[List[float]]: List of embedding vectors (one per document).
        """
        if not documents:
            logger.warning("No documents provided for embedding.")
            return []

        texts = [doc.page_content for doc in documents]

        try:
            logger.debug(f"Generating embeddings for {len(texts)} documents.")
            # If batch_size is supported by embedding_model
            if self.batch_size and hasattr(self.embedding_model, "embed_documents"):
                embeddings = self.embedding_model.embed_documents(texts, batch_size=self.batch_size)
            else:
                embeddings = self.embedding_model.embed_documents(texts)
            if len(embeddings) != len(texts):
                logger.warning(
                    f"Number of embeddings ({len(embeddings)}) does not match number of documents ({len(texts)})."
                )
            logger.info(f"Successfully generated embeddings for {len(embeddings)} documents.")
            return embeddings
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}", exc_info=True)
            raise

    def embed_with_metadata(self, documents: Sequence[Document]) -> List[Tuple[Document, List[float]]]:
        """
        Embed docs and return tuples of (Document, embedding).

        Returns:
            List[Tuple[Document, embedding]]
        """
        embeddings = self.embed_documents(documents)
        return list(zip(documents, embeddings))


def embed_documents(
    documents: Sequence[Document], embedding_model: Optional[Embeddings] = None, batch_size: Optional[int] = None
) -> List[List[float]]:
    """
    Convenience function to embed documents directly.
    """
    embedder = DocumentEmbedder(embedding_model=embedding_model, batch_size=batch_size)
    return embedder.embed_documents(documents)

