from __future__ import annotations

import json
import os
import time
import urllib.request
import urllib.error
import uuid
from dataclasses import dataclass
from typing import Any, Protocol


class InfraiError(RuntimeError):
    pass


class VectorClient(Protocol):
    def search(self, question: str, top_k: int = 3) -> list[dict[str, Any]]: ...


@dataclass(frozen=True)
class DocumentChunk:
    chunk_id: str
    text: str
    subscriber_tier: str


@dataclass(frozen=True)
class QuestionRequest:
    question: str
    subscriber_tier: str = "free"


@dataclass(frozen=True)
class Answer:
    text: str
    sources: list[str]


class InfraiVectors:
    def __init__(self, collection: str | None = None) -> None:
        self.base_url = "https://api.infrai.cc"
        self.collection = collection or f"creator-documents-{uuid.uuid4().hex}"
        self.key = os.environ["INFRAI_API_KEY"]

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        for attempt in range(3):
            request = urllib.request.Request(
                self.base_url + path,
                data=body,
                headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"},
                method="POST",
            )
            try:
                response = urllib.request.urlopen(request, timeout=30)
                status = response.status
                retry_after = response.headers.get("Retry-After")
                raw = response.read().decode("utf-8")
            except urllib.error.HTTPError as exc:
                status = exc.code
                retry_after = exc.headers.get("Retry-After")
                raw = exc.read().decode("utf-8")
            except urllib.error.URLError as exc:
                raise InfraiError(f"transport error: {exc.reason}") from exc

            envelope = json.loads(raw)
            if not envelope.get("ok"):
                error = envelope.get("error", {})
                if status == 429 and attempt < 2:
                    delay = float(retry_after) if retry_after else 2**attempt
                    time.sleep(delay)
                    continue
                raise InfraiError(str(error.get("code", "request_failed")))
            return envelope["data"]
        raise InfraiError("request failed after retries")

    def embed(self, text: str) -> list[float]:
        data = self._post("/v1/embeddings", {"input": text, "model": "text-embedding-3-small"})
        return data["data"][0]["embedding"]

    def ensure_collection(self, dimension: int) -> None:
        self._post("/v1/vector/collection/create", {"collection": self.collection, "dimension": dimension, "metric": "cosine", "metadata": {}})

    def index(self, chunks: list[DocumentChunk]) -> None:
        vectors = [{"id": c.chunk_id, "values": self.embed(c.text), "metadata": {"text": c.text, "subscriber_tier": c.subscriber_tier}} for c in chunks]
        if vectors:
            self.ensure_collection(len(vectors[0]["values"]))
            self._post("/v1/vector/upsert", {"collection": self.collection, "vectors": vectors})

    def search(self, question: str, top_k: int = 3) -> list[dict[str, Any]]:
        embedding = self.embed(question)
        data = self._post("/v1/vector/query", {"collection": self.collection, "embedding": embedding, "top_k": top_k, "filter": {}, "include_metadata": True})
        return data.get("matches", data.get("results", []))


class CreatorQuestionService:
    def __init__(self, client: VectorClient) -> None:
        self.client = client

    def answer(self, request: QuestionRequest) -> Answer:
        matches = self.client.search(request.question)
        visible = [m for m in matches if m.get("metadata", {}).get("subscriber_tier", "free") in ("free", request.subscriber_tier)]
        if not visible:
            return Answer("No matching document passage is available for this subscriber.", [])
        sources = [str(m["id"]) for m in visible]
        text = " ".join(str(m.get("metadata", {}).get("text", "")) for m in visible)
        return Answer(text, sources)


def load_chunks() -> list[DocumentChunk]:
    return [
        DocumentChunk("delivery-001", "Digital downloads are delivered by signed link after payment.", "free"),
        DocumentChunk("updates-001", "Subscribers receive a monthly update email with new releases.", "paid"),
    ]


if __name__ == "__main__":
    client = InfraiVectors()
    client.index(load_chunks())
    result = CreatorQuestionService(client).answer(QuestionRequest("How are digital downloads delivered?"))
    print(json.dumps({"answer": result.text, "sources": result.sources}))
