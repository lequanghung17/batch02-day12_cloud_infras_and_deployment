from __future__ import annotations

import os
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


TOKEN_RE = re.compile(r"\w+", re.UNICODE)


@dataclass
class Chunk:
    doc_id: str
    source: str
    content: str
    tokens: set[str]


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def _chunk_text(text: str, chunk_size: int = 900, overlap: int = 120) -> list[str]:
    cleaned = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not cleaned:
        return []
    if len(cleaned) <= chunk_size:
        return [cleaned]

    chunks: list[str] = []
    step = max(1, chunk_size - overlap)
    for start in range(0, len(cleaned), step):
        chunk = cleaned[start : start + chunk_size].strip()
        if chunk:
            chunks.append(chunk)
        if start + chunk_size >= len(cleaned):
            break
    return chunks


class VietnameseLegalRagAgent:
    """Small offline RAG agent built from the student's Day07 legal KB."""

    def __init__(self, data_dir: str | Path) -> None:
        self.data_dir = Path(data_dir)
        self.chunks: list[Chunk] = []
        self._load()

    def _load(self) -> None:
        if not self.data_dir.exists():
            return

        for path in sorted(self.data_dir.glob("*.md")):
            text = path.read_text(encoding="utf-8", errors="ignore")
            for chunk in _chunk_text(text):
                tokens = set(_tokenize(chunk))
                self.chunks.append(
                    Chunk(
                        doc_id=path.stem,
                        source=path.name,
                        content=chunk,
                        tokens=tokens,
                    )
                )

    def _score(self, question: str, chunk: Chunk) -> float:
        query_tokens = set(_tokenize(question))
        if not query_tokens:
            return 0.0

        overlap = query_tokens & chunk.tokens
        score = len(overlap) / max(1, len(query_tokens))

        question_lower = question.lower()
        content_lower = chunk.content.lower()
        for phrase in re.findall(r"\w+(?:\s+\w+){1,4}", question_lower, re.UNICODE):
            if phrase in content_lower:
                score += 0.25
        return score

    def retrieve(self, question: str, top_k: int = 3) -> list[tuple[float, Chunk]]:
        scored = [
            (self._score(question, chunk), chunk)
            for chunk in self.chunks
        ]
        scored = [item for item in scored if item[0] > 0]
        scored.sort(key=lambda item: item[0], reverse=True)
        return scored[:top_k]

    def answer(self, question: str) -> str:
        results = self.retrieve(question, top_k=3)
        if not results:
            return (
                "Toi chua tim thay noi dung phu hop trong bo tai lieu luat da nap. "
                "Hay hoi cu the hon ve phong chay chua chay, suc khoe nhan dan, "
                "bien gioi quoc gia, thi dua khen thuong hoac si quan quan doi."
            )

        lines = [
            "Day la cau tra loi tu Vietnamese Legal RAG Agent dua tren tai lieu Day07.",
            "",
            "Tom tat nguon lien quan:",
        ]
        for index, (score, chunk) in enumerate(results, start=1):
            excerpt = re.sub(r"\s+", " ", chunk.content).strip()
            if len(excerpt) > 420:
                excerpt = excerpt[:420].rsplit(" ", 1)[0] + "..."
            lines.append(f"{index}. [{chunk.source}] score={score:.2f}: {excerpt}")

        lines.extend([
            "",
            "Ket luan ngan:",
            (
                "Cac doan tai lieu tren la can cu gan nhat voi cau hoi. "
                "Vui long doi chieu van ban goc neu can cau tra loi phap ly chinh thuc."
            ),
        ])
        return "\n".join(lines)

    def stats(self) -> dict:
        return {
            "data_dir": str(self.data_dir),
            "documents": len({chunk.source for chunk in self.chunks}),
            "chunks": len(self.chunks),
        }


@lru_cache(maxsize=1)
def get_agent() -> VietnameseLegalRagAgent:
    data_dir = os.getenv("LEGAL_RAG_DATA_DIR", "/app/data")
    if not Path(data_dir).exists():
        data_dir = str(Path(__file__).resolve().parents[1] / "data")
    return VietnameseLegalRagAgent(data_dir=data_dir)


def answer_question(question: str) -> str:
    return get_agent().answer(question)


def knowledge_base_stats() -> dict:
    return get_agent().stats()
