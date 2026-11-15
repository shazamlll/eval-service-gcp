"""Deterministic, offline rubric judge.

Scores an answer against a gold reference on three rubrics, each 0-2:
  - groundedness: how much of the gold answer's content the answer covers
  - relevance:    how much of the question the answer addresses
  - accuracy:     token-level F1 overlap between answer and gold

No model, no network, no API key. The judge is deliberately simple and
fully deterministic: the same input always produces the same score. It is
a placeholder for a real LLM judge (see README, "Remaining work").
"""
from __future__ import annotations

import re

# Common words that carry no scoring signal.
STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "it", "its",
    "in", "on", "at", "to", "of", "for", "with", "and", "or", "you", "your",
    "we", "our", "can", "do", "does", "i", "me", "my", "by", "from", "as",
    "if", "yes", "no", "not", "so", "that", "this", "there", "here", "how",
    "what", "when", "where", "which", "who", "is", "am", "have", "has",
    "get", "got", "per", "per", "us", "up", "out", "about", "into", "over",
}

_TOKEN_RE = re.compile(r"[a-z0-9]+(?:[.'\-][a-z0-9]+)?")


def _stem(word: str) -> str:
    """Minimal stemmer: -ies -> -y, strip -ing/-ed (undoubling a doubled
    consonant), strip a trailing -s. Applied to both sides, so paraphrases
    such as cancel/cancelled and order/orders match."""
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 4 and word.endswith("ing"):
        word = word[:-3]
    elif len(word) > 3 and word.endswith("ed"):
        word = word[:-2]
    if len(word) > 1 and word[-1] == word[-2] and word[-1] not in "aeiou":
        word = word[:-1]
    if len(word) > 3 and word.endswith("s") and not word.endswith(("ss", "us")):
        word = word[:-1]
    return word


def _tokens(text: str) -> set[str]:
    raw = {t for t in _TOKEN_RE.findall(text.lower()) if t not in STOPWORDS}
    return {s for s in (_stem(t) for t in raw) if s and s not in STOPWORDS}


def _score_from_ratio(ratio: float, high: float = 0.5, low: float = 0.25) -> int:
    if ratio >= high:
        return 2
    if ratio >= low:
        return 1
    return 0


def judge(question: str, gold: str, answer: str) -> dict[str, int]:
    """Score one answer. Returns {"groundedness": 0-2, "relevance": 0-2, "accuracy": 0-2}."""
    q_tokens = _tokens(question)
    gold_tokens = _tokens(gold)
    ans_tokens = _tokens(answer)

    if not ans_tokens:
        return {"groundedness": 0, "relevance": 0, "accuracy": 0}

    # Groundedness: share of gold content covered by the answer.
    groundedness = _score_from_ratio(
        len(gold_tokens & ans_tokens) / len(gold_tokens) if gold_tokens else 0.0
    )

    # Relevance: share of the question+gold vocabulary the answer covers.
    # (Measured against question ∪ gold, not the question alone: good short
    # answers such as "Yes, it is in stock" do not repeat the question's
    # nouns, so question-only overlap wrongly scores them 0.)
    topic = q_tokens | gold_tokens
    relevance = _score_from_ratio(
        len(topic & ans_tokens) / len(topic) if topic else 0.0
    )

    # Accuracy: F1 overlap between answer and gold content tokens.
    overlap = len(gold_tokens & ans_tokens)
    precision = overlap / len(ans_tokens)
    recall = overlap / len(gold_tokens) if gold_tokens else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )
    accuracy = 2 if f1 >= 0.6 else (1 if f1 >= 0.3 else 0)

    return {"groundedness": groundedness, "relevance": relevance, "accuracy": accuracy}


def case_passes(scores: dict[str, int]) -> bool:
    """A case passes when it scores at least 4/6 with no rubric at 0."""
    return sum(scores.values()) >= 4 and min(scores.values()) >= 1
