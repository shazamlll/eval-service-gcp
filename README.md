# eval-service-gcp

A small evaluation API service, built as a **portfolio demo** — not production.

It exposes a deterministic, offline rubric judge over a synthetic eval set
(fictional online-bookstore domain, all data invented). The point of this
repo is to demonstrate **shipping a small eval service on GCP Cloud Run**:
a containerized FastAPI app with a pass/fail quality gate, ready to deploy.

## What it does

| Endpoint | Description |
| --- | --- |
| `GET /` | Service info (version, endpoints, built-in case count) |
| `GET /health` | Health check (`{"status": "ok"}`) |
| `POST /evaluate` | Score answers and return a pass/fail verdict |

`POST /evaluate` accepts either:

- a list of items — `{"items": [{"question": "...", "answer": "...", "expected": "..."}]}` — or
- no body, in which case it runs the built-in synthetic set (15 cases).

Each case is scored 0–2 on three rubrics — **groundedness**, **relevance**,
**accuracy** — and passes when it scores at least 4/6 with no rubric at 0.
The response reports per-case scores plus an aggregate pass rate and a
`pass`/`fail` verdict against a configurable threshold (default `0.8`,
overridable per request or via `EVAL_PASS_RATE_THRESHOLD`).

The judge is **deterministic and works offline** (token-overlap scoring,
no API key, no network). It is intentionally simple: a stand-in for a real
LLM judge, good enough to show the shape of an eval gate.

## Run locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

Then:

```bash
curl localhost:8080/health
curl -X POST localhost:8080/evaluate -H 'Content-Type: application/json' -d '{}'
```

## Run the tests

```bash
pip install -r requirements.txt
pytest -q
```

## Docker

```bash
docker build -t eval-service-gcp .
docker run -p 8080:8080 eval-service-gcp
```

## Remaining work

Deployment and wiring were deliberately left out of this repo. A follow-up
agent (or a human) still needs to:

1. Create a GCP project and enable the required APIs (Cloud Run, Cloud Build, Artifact Registry / Container Registry).
2. Set a **budget alert** on the project before deploying anything.
3. Authenticate with `gcloud auth login`, then run `./deploy.sh` (it contains the `gcloud` Cloud Run deploy commands; it has never been executed).
4. Verify the public endpoint: `curl <service-url>/health` and `POST <service-url>/evaluate`.
5. Optionally wire a real LLM judge: add an API key via Cloud Run secrets / env vars and swap the deterministic judge in `app/judge.py` for a model-backed one — keeping the same response shape so the gate logic does not change.

## Honest limits

- The judge is a keyword-overlap heuristic, not an LLM judge; it cannot catch subtle hallucinations or reasoning errors.
- All eval data is synthetic. Nothing here has been validated on real traffic.
- No auth, no rate limiting, no persistence — this is a demo, not a service you would put in front of users.
