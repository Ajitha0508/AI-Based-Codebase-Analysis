"""Persistent ChromaDB vector database manager with repository-level isolation."""

from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import settings
from app.rag.chunker import CodeChunk
from app.rag.embeddings import get_chroma_embedding_function


class VectorStoreManager:
    """Manages persistent ChromaDB vector storage and isolated retrieval."""

    def __init__(self):
        Path(settings.CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.embedding_fn = get_chroma_embedding_function()
        self.collection_name = "codemind_code_chunks"
        self._collection = None

    def get_collection(self):
        """Retrieve or create the main code chunks collection."""
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_fn,
                metadata={"hnsw:space": "cosine"}
            )
        return self._collection

    def add_chunks(self, repository_id: str, chunks: List[CodeChunk]) -> int:
        """
        Batch add code chunks to ChromaDB.
        Avoids payload limits by batching 100 items at a time.
        """
        if not chunks:
            return 0

        coll = self.get_collection()
        batch_size = 100
        total_added = 0

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i: i + batch_size]
            ids = [c.chunk_id for c in batch]
            documents = [c.content for c in batch]
            metadatas = [c.to_metadata() for c in batch]

            coll.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
            )
            total_added += len(batch)

        return total_added

    def search(
        self,
        repository_id: str,
        query: str,
        top_k: int = 5,
        filter_language: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant code chunks strictly isolated to the specified repository_id.
        """
        if not query.strip():
            return []

        coll = self.get_collection()

        # Build repository isolation filter
        where_filter: Dict[str, Any] = {"repository_id": repository_id}
        if filter_language:
            where_filter = {
                "$and": [
                    {"repository_id": repository_id},
                    {"language": filter_language},
                ]
            }

        try:
            results = coll.query(
                query_texts=[query],
                n_results=top_k,
                where=where_filter,
                include=["documents", "metadatas", "distances"],
            )
        except Exception:
            # If collection is empty or filter finds 0 items
            return []

        retrieved = []
        if results and results.get("ids") and len(results["ids"]) > 0:
            doc_list = results["documents"][0]
            meta_list = results["metadatas"][0]
            dist_list = results["distances"][0] if "distances" in results else [0.0] * len(doc_list)

            for doc, meta, dist in zip(doc_list, meta_list, dist_list):
                # Convert cosine distance to similarity score
                similarity = max(0.0, min(1.0, 1.0 - (dist if dist is not None else 0.0)))
                retrieved.append({
                    "content": doc,
                    "metadata": meta,
                    "similarity": round(similarity, 4),
                    "file_path": meta.get("file_path", ""),
                    "start_line": meta.get("start_line", 1),
                    "end_line": meta.get("end_line", 1),
                    "symbol_name": meta.get("symbol_name", ""),
                    "language": meta.get("language", ""),
                })

        return retrieved

    def delete_repository_index(self, repository_id: str) -> None:
        """Remove all indexed chunks belonging to a repository."""
        coll = self.get_collection()
        try:
            coll.delete(where={"repository_id": repository_id})
        except Exception:
            pass

    def count_repository_chunks(self, repository_id: str) -> int:
        """Count how many chunks exist for a given repository."""
        coll = self.get_collection()
        try:
            res = coll.get(where={"repository_id": repository_id}, include=[])
            return len(res.get("ids", []))
        except Exception:
            return 0


# Global singleton instance
vector_store = VectorStoreManager()
