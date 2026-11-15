"""eval-service-gcp: a small evaluation API service.

Portfolio demo — NOT production. Runs a deterministic, offline rubric
judge over a built-in synthetic eval set (fictional bookstore domain) or
over caller-supplied {question, answer, expected} items.
"""
from __future__ import annotations

import os

from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.eval_set import BUILTIN_CASES
from app.judge import case_passes, judge

SERVICE_VERSION = "0.1.0"
DEFAULT_THRESHOLD = float(os.environ.get("EVAL_PASS_RATE_THRESHOLD", "0.8"))

app = FastAPI(
    title="eval-service-gcp",
    version=SERVICE_VERSION,
    description="Small eval-as-a-service demo: deterministic rubric judging with a pass/fail gate.",
)


class EvalItem(BaseModel):
    question: str
    answer: str
    expected: str = ""


class EvaluateRequest(BaseModel):
    items: list[EvalItem] = Field(default_factory=list)
    threshold: float = Field(default=DEFAULT_THRESHOLD, ge=0.0, le=1.0)


class CaseResult(BaseModel):
    id: str | None = None
    question: str
    scores: dict[str, int]
    total: int
    passed: bool


class EvaluateResponse(BaseModel):
    results: list[CaseResult]
    summary: dict


@app.get("/")
def root() -> dict:
    return {
        "service": "eval-service-gcp",
        "version": SERVICE_VERSION,
        "description": "Deterministic eval-as-a-service demo (offline rubric judge).",
        "endpoints": ["/", "/health", "/evaluate"],
        "builtin_cases": len(BUILTIN_CASES),
        "default_pass_rate_threshold": DEFAULT_THRESHOLD,
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/evaluate", response_model=EvaluateResponse)
def evaluate(req: EvaluateRequest) -> EvaluateResponse:
    if req.items:
        cases = [
            {"id": None, "question": it.question, "gold": it.expected, "answer": it.answer}
            for it in req.items
        ]
    else:
        cases = BUILTIN_CASES

    results: list[CaseResult] = []
    passed_count = 0
    for case in cases:
        scores = judge(case["question"], case["gold"], case["answer"])
        passed = case_passes(scores)
        passed_count += int(passed)
        results.append(
            CaseResult(
                id=case.get("id"),
                question=case["question"],
                scores=scores,
                total=sum(scores.values()),
                passed=passed,
            )
        )

    total = len(results)
    pass_rate = (passed_count / total) if total else 0.0
    summary = {
        "total": total,
        "passed": passed_count,
        "failed": total - passed_count,
        "pass_rate": round(pass_rate, 4),
        "threshold": req.threshold,
        "verdict": "pass" if pass_rate >= req.threshold else "fail",
    }
    return EvaluateResponse(results=results, summary=summary)
