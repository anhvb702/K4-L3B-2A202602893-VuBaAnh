from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])(?:\s+|$)", text.strip()) if s.strip()]
        return [" ".join(sentences[i:i + self.max_sentences_per_chunk])
                for i in range(0, len(sentences), self.max_sentences_per_chunk)]


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        return [part.strip() for part in self._split(text.strip(), self.separators) if part.strip()]

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if len(current_text) <= self.chunk_size:
            return [current_text]
        if not remaining_separators:
            return [current_text[i:i + self.chunk_size]
                    for i in range(0, len(current_text), self.chunk_size)]
        separator = remaining_separators[0]
        if separator == "":
            pieces = [current_text[i:i + self.chunk_size]
                      for i in range(0, len(current_text), self.chunk_size)]
        else:
            pieces = current_text.split(separator)
            pieces = [p for p in pieces if p]
        if len(pieces) <= 1:
            return self._split(current_text, remaining_separators[1:])
        result: list[str] = []
        buffer = ""
        for piece in pieces:
            candidate = piece if not buffer else buffer + separator + piece
            if len(candidate) <= self.chunk_size:
                buffer = candidate
            else:
                if buffer:
                    result.extend(self._split(buffer, remaining_separators[1:]))
                buffer = piece
        if buffer:
            result.extend(self._split(buffer, remaining_separators[1:]))
        return result


class HeadingChunker:
    """Split Markdown into heading-based sections and recursively trim long sections."""

    def __init__(self, chunk_size: int = 500) -> None:
        self.chunk_size = chunk_size
        self._fallback = RecursiveChunker(chunk_size=chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        matches = list(re.finditer(r"(?m)^#{1,6}\s+.+$", text.strip()))
        if not matches:
            return self._fallback.chunk(text)
        sections: list[str] = []
        prefix = text[:matches[0].start()].strip()
        if prefix:
            sections.append(prefix)
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            heading = match.group(0).strip()
            body = text[match.end():end].strip()
            section = "\n\n".join(part for part in (heading, body) if part)
            if len(section) <= self.chunk_size:
                sections.append(section)
            else:
                for piece in self._fallback.chunk(body):
                    sections.append(f"{heading}\n\n{piece}")
        return [section.strip() for section in sections if section.strip()]


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    norm_a = math.sqrt(_dot(vec_a, vec_a))
    norm_b = math.sqrt(_dot(vec_b, vec_b))
    if not norm_a or not norm_b:
        return 0.0
    return _dot(vec_a, vec_b) / (norm_a * norm_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=0),
            "by_sentences": SentenceChunker(max_sentences_per_chunk=3),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }
        result = {}
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            result[name] = {
                "count": len(chunks),
                "avg_length": (sum(map(len, chunks)) / len(chunks)) if chunks else 0.0,
                "chunks": chunks,
            }
        return result
