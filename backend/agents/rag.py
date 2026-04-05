from sentence_transformers import SentenceTransformer
import chromadb
from .utils import split_text_with_overlap


class EmbeddingService:
    _instance = None
    _model = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            cls._model = SentenceTransformer("all-MiniLM-L6-v2")
        return cls._model

    @classmethod
    def embed(cls, texts: list[str]) -> list[list[float]]:
        model = cls.get_model()
        return model.encode(texts, show_progress_bar=False).tolist()


class DocumentStore:
    def __init__(self):
        self.client = chromadb.Client()
        self.embedding_service = EmbeddingService()

    def get_or_create_collection(self, name: str = "default"):
        return self.client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"}
        )

    def add_document(self, doc_id: str, text: str, collection_name: str = "default",
                     chunk_size: int = 400, chunk_overlap: int = 50):
        collection = self.get_or_create_collection(collection_name)
        chunks = split_text_with_overlap(text, chunk_size, chunk_overlap)
        embeddings = self.embedding_service.embed(chunks)

        ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [{"doc_id": doc_id, "chunk_index": i} for i in range(len(chunks))]

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas
        )
        return len(chunks)

    def query(self, question: str, collection_name: str = "default",
              n_results: int = 5, doc_filter: str | None = None):
        collection = self.get_or_create_collection(collection_name)
        query_embedding = self.embedding_service.embed([question])

        where_filter = {"doc_id": doc_filter} if doc_filter else None

        results = collection.query(
            query_embeddings=query_embedding,
            n_results=n_results,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )

        sources = []
        if results["documents"] and results["documents"][0]:
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            ):
                sources.append({
                    "text": doc,
                    "doc_id": meta["doc_id"],
                    "chunk_index": meta["chunk_index"],
                    "score": round(1 - dist, 3)
                })

        return sources

    def get_doc_ids(self, collection_name: str = "default") -> list[str]:
        collection = self.get_or_create_collection(collection_name)
        results = collection.get(include=["metadatas"])
        doc_ids = set()
        for meta in results["metadatas"]:
            doc_ids.add(meta["doc_id"])
        return list(doc_ids)

    def delete_collection(self, name: str = "default"):
        try:
            self.client.delete_collection(name)
        except Exception:
            pass

    def reset(self, collection_name: str = "default"):
        self.delete_collection(collection_name)
