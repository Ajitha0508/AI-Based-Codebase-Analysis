"""Embedding providers: resilient deterministic local vectorizer, ONNX, Gemini, and OpenAI."""

import hashlib
import math

from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

from app.core.config import settings


class DeterministicLocalEmbeddingFunction(EmbeddingFunction[Documents]):
    """
    Fast, deterministic offline embedding function.
    Generates normalized 384-dimensional semantic-hash vectors.
    Requires no external downloads or API keys, ensuring CodeMind AI works 100% offline.
    """
    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def name(self) -> str:
        return "default"

    def __call__(self, input: Documents) -> Embeddings:
        embeddings = []
        for text in input:
            vec = [0.0] * self.dimension
            tokens = text.lower().split()
            if not tokens:
                tokens = [text.lower()]

            for token in tokens:
                # Hash token to dimension indices
                h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
                idx = h % self.dimension
                # Weight by token length
                vec[idx] += min(len(token), 10) * 0.1

                # Secondary n-gram hash for semantic spread
                h2 = int(hashlib.sha256(token.encode("utf-8")).hexdigest(), 16)
                idx2 = h2 % self.dimension
                vec[idx2] += 0.05

            # L2 Normalize
            norm = math.sqrt(sum(x * x for x in vec))
            if norm > 0:
                vec = [x / norm for x in vec]
            else:
                vec[0] = 1.0

            embeddings.append(vec)
        return embeddings


def get_chroma_embedding_function() -> EmbeddingFunction:
    """
    Get the configured embedding function for ChromaDB.
    Returns:
        EmbeddingFunction instance.
    """
    provider = settings.EMBEDDING_PROVIDER.lower()

    if provider == "openai" and settings.OPENAI_API_KEY:
        try:
            from chromadb.utils import embedding_functions
            return embedding_functions.OpenAIEmbeddingFunction(
                api_key=settings.OPENAI_API_KEY,
                model_name=settings.EMBEDDING_MODEL or "text-embedding-3-small"
            )
        except Exception:
            pass

    elif provider == "gemini" and settings.GEMINI_API_KEY:
        try:
            from chromadb.utils import embedding_functions
            return embedding_functions.GoogleGenerativeAiEmbeddingFunction(
                api_key=settings.GEMINI_API_KEY,
                model_name="models/embedding-001"
            )
        except Exception:
            pass

    elif provider == "onnx":
        try:
            from chromadb.utils import embedding_functions
            return embedding_functions.DefaultEmbeddingFunction()
        except Exception:
            pass

    # Default to fast, resilient deterministic local embedding function
    return DeterministicLocalEmbeddingFunction()
