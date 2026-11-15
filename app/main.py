"""eval-service-gcp: a small evaluation API service.

Portfolio demo — NOT production. Runs a deterministic, offline rubric
judge over a built-in synthetic eval set (fictional bookstore domain) or
over caller-supplied {question, answer, expected} items.
"""
from __future__ import annotations

import os
from typing import Annotated

from fastapi import Body, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, TypeAdapter

from app.eval_set import BUILTIN_CASES
from app.judge import case_passes, judge

SERVICE_VERSION = "0.1.0"
Threshold = Annotated[float, Field(ge=0.0, le=1.0, allow_inf_nan=False)]
DEFAULT_THRESHOLD = TypeAdapter(Threshold).validate_python(
    os.environ.get("EVAL_PASS_RATE_THRESHOLD", "0.8")
)
NonBlankText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]

app = FastAPI(
    title="eval-service-gcp",
    version=SERVICE_VERSION,
    description="Small eval-as-a-service demo: deterministic rubric judging with a pass/fail gate.",
)


@app.exception_handler(RequestValidationError)
async def invalid_request(_request: Request, exc: RequestValidationError) -> JSONResponse:
    # Do not echo raw inputs: NaN/Infinity in them cannot be serialized as JSON.
    errors = [{key: error[key] for key in ("loc", "msg", "type")} for error in exc.errors()]
    return JSONResponse(status_code=422, content={"detail": errors})


class EvalItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: NonBlankText
    answer: str
    expected: NonBlankText


class EvaluateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[EvalItem] = Field(default_factory=list)
    threshold: Threshold = Field(default=DEFAULT_THRESHOLD, strict=True)


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
def evaluate(req: EvaluateRequest = Body(default_factory=EvaluateRequest)) -> EvaluateResponse:
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
