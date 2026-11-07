"""Token-aware chunking of paragraphs. Standard library only.

Token counts here are a heuristic (about 1.3 tokens per word), because the
embedding model has not been chosen yet. When it is, pass its tokenizer as
`count_tokens`. Chunks never split inside a sentence unless one sentence alone
exceeds the limit, in which case it is split on word boundaries.
"""
import math
import re
from collections.abc import Callable

_WORD = re.compile(r"\w+(?:['’]\w+)?")
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def approx_tokens(text: str) -> int:
    """Heuristic token count: about 1.3 tokens per word."""
    return math.ceil(len(_WORD.findall(text)) * 1.3)


def _split_long_unit(text: str, max_tokens: int, count: Callable[[str], int]) -> list[str]:
    """Split an oversize paragraph into sentences, and oversize sentences into word groups."""
    units: list[str] = []
    for sentence in _SENTENCE_END.split(text):
        sentence = sentence.strip()
        if not sentence:
            continue
        if count(sentence) <= max_tokens:
            units.append(sentence)
            continue
        words = sentence.split()
        piece: list[str] = []
        for word in words:
            candidate = " ".join(piece + [word])
            if piece and count(candidate) > max_tokens:
                units.append(" ".join(piece))
                piece = [word]
            else:
                piece.append(word)
        if piece:
            units.append(" ".join(piece))
    return units


def chunk_paragraphs(
    paragraphs: list[str],
    max_tokens: int = 220,
    overlap_tokens: int = 40,
    count_tokens: Callable[[str], int] = approx_tokens,
) -> list[str]:
    """Pack paragraphs into chunks of at most `max_tokens`, repeating a small tail as overlap."""
    if max_tokens < 1:
        raise ValueError("max_tokens must be at least 1")
    if overlap_tokens < 0 or overlap_tokens >= max_tokens:
        raise ValueError("overlap_tokens must be >= 0 and smaller than max_tokens")

    units: list[str] = []
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        if count_tokens(paragraph) <= max_tokens:
            units.append(paragraph)
        else:
            units.extend(_split_long_unit(paragraph, max_tokens, count_tokens))

    chunks: list[str] = []
    current: list[str] = []
    current_tokens = 0
    for unit in units:
        unit_tokens = count_tokens(unit)
        if current and current_tokens + unit_tokens > max_tokens:
            chunks.append("\n\n".join(current))
            carried: list[str] = []
            carried_tokens = 0
            for previous in reversed(current):
                previous_tokens = count_tokens(previous)
                if carried_tokens + previous_tokens > overlap_tokens:
                    break
                carried.insert(0, previous)
                carried_tokens += previous_tokens
            if carried_tokens + unit_tokens > max_tokens:
                carried, carried_tokens = [], 0
            current, current_tokens = carried, carried_tokens
        current.append(unit)
        current_tokens += unit_tokens
    if current:
        chunks.append("\n\n".join(current))
    return chunks
