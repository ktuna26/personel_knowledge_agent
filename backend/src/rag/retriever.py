# backend/src/rag/retriever.py
"""
Retriever module for the RAG pipeline.

Responsibilities:
- Build a vector store index from embedded documents.
- Provide similarity search retriever.
- Interface for querying top-k relevant documents.
- Support saving/loading vectorstore to disk (FAISS).
"""

import logging
from pathlib import Path
from typing import List, Optional, Union

from langchain.docstore.document import Document
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings.embeddings import Embeddings

logger = logging.getLogger(__name__)

class Retriever:
    """
    Retriever built on a vector store (default: FAISS).
    Supports both in-memory and persistent usage.
    """

    def __init__(
        self,
        embedding_model: Embeddings,
        documents: Optional[List[Document]] = None,
        embeddings: Optional[List[List[float]]] = None,
        faiss_path: Optional[Union[str, Path]] = None,
    ):
        """
        Initialize Retriever.
        If faiss_path is provided and file exists, loads vectorstore from disk.
        Otherwise builds new vectorstore from provided documents (and optional embeddings).

        Args:
            embedding_model: Embedding model instance.
            documents: List of LangChain Documents (optional if loading from disk).
            embeddings: Precomputed embeddings (optional).
            faiss_path: Optional path for saving/loading FAISS vectorstore.
        """
        self.embedding_model = embedding_model
        self.vectorstore: Optional[FAISS] = None
        self.faiss_path = Path(faiss_path) if faiss_path else None

        if self.faiss_path and self.faiss_path.exists():
            try:
                self.vectorstore = FAISS.load_local(str(self.faiss_path), self.embedding_model)
                logger.info(f"Loaded FAISS vectorstore from {self.faiss_path}")
            except Exception as e:
                logger.error(f"Failed to load FAISS index: {e}", exc_info=True)
                raise

        elif documents is not None:
            # Build from docs/embeddings
            try:
                if embeddings is not None:
                    # Let FAISS compute the embeddings
                    self.vectorstore = FAISS.from_documents(
                        documents=documents,
                        embedding=embedding_model,
                    )
                    logger.info(f"FAISS vector store created with {len(documents)} documents (FAISS computed embeddings).")
                else:
                    # Use precomputed embeddings (texts and metadatas must match)
                    self.vectorstore = FAISS.from_embeddings(
                        texts=[doc.page_content for doc in documents],
                        embedding=embedding_model,
                        metadatas=[doc.metadata for doc in documents],
                        embeddings=embeddings,
                    )
                    logger.info(f"FAISS vector store created with {len(documents)} documents (precomputed embeddings).")
                logger.info(f"FAISS vectorstore created with {len(documents)} documents.")
                # Save to disk if path provided
                if self.faiss_path:
                    self.vectorstore.save_local(str(self.faiss_path))
                    logger.info(f"FAISS vectorstore saved to {self.faiss_path}")
            except Exception as e:
                logger.error(f"Failed to build FAISS vectorstore: {e}", exc_info=True)
                raise
        else:
            raise ValueError("Either documents or faiss_path must be provided.")

    def query(self, query_text: str, top_k: int = 5) -> List[Document]:
        """
        Perform similarity search to retrieve top_k relevant documents.

        Args:
            query_text: Text query.
            top_k: Number of top documents to retrieve.

        Returns:
            List[Document]: Top matching LangChain Document objects.
        """
        if not self.vectorstore:
            logger.error("Vectorstore not initialized.")
            return []
        try:
            results = self.vectorstore.similarity_search(query_text, k=top_k)
            logger.info(f"Retrieved {len(results)} documents for query.")
            return results
        except Exception as e:
            logger.error(f"Similarity search failed: {e}", exc_info=True)
            return []

    def save_index(self, path: Union[str, Path]) -> None:
        """
        Persist the FAISS vectorstore to disk.
        """
        if not self.vectorstore:
            logger.warning("Nothing to save; vectorstore not initialized.")
            return
        path = Path(path)
        self.vectorstore.save_local(str(path))
        logger.info(f"FAISS vectorstore saved to {path}")

    def load_index(self, path: Union[str, Path]) -> None:
        """
        Load the FAISS vectorstore from disk.
        """
        path = Path(path)
        self.vectorstore = FAISS.load_local(str(path), self.embedding_model)
        logger.info(f"FAISS vectorstore loaded from {path}")

