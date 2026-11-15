# eval-service-gcp

A small evaluation API service, built as a **portfolio demo** — not production.

It exposes a deterministic, offline rubric judge over a synthetic eval set
(fictional online-bookstore domain, all data invented). The point of this
repo is to demonstrate **packaging a small eval service for GCP Cloud Run**:
a FastAPI app with a pass/fail quality gate, a Dockerfile, and a deployment
script. Cloud deployment has not been performed.

## What it does

| Endpoint | Description |
| --- | --- |
| `GET /` | Service info (version, endpoints, built-in case count) |
| `GET /health` | Health check (`{"status": "ok"}`) |
| `POST /evaluate` | Score answers and return a pass/fail verdict |

`POST /evaluate` accepts either:

- a list of items — `{"items": [{"question": "...", "answer": "...", "expected": "..."}]}` — or
- no body, `{}`, or `{"items": []}`, which runs the built-in synthetic set (15 cases).

Custom items require a nonblank `question` and `expected`, plus an `answer`
string (an empty answer is valid and scores zero). Unknown fields are rejected
with HTTP 422 so a misspelled `items` cannot silently run the built-in set.
Thresholds must be finite JSON numbers in `[0, 1]`; strings and booleans are
rejected. An invalid environment threshold prevents startup.

Each case is scored 0–2 on three rubrics — **groundedness**, **relevance**,
**accuracy** — and passes when it scores at least 4/6 with no rubric at 0.
The response reports per-case scores plus an aggregate pass rate and a
`pass`/`fail` verdict against a configurable threshold (default `0.8`,
overridable per request or via `EVAL_PASS_RATE_THRESHOLD`).
The gate compares the unrounded pass rate; the reported rate is rounded to
four decimals. For example, 13/15 fails a threshold of `0.8667` despite the
displayed pass rate also being `0.8667`.

The judge is **deterministic and works offline** (token-overlap scoring,
no API key, no network). It is intentionally simple: a stand-in for a real
LLM judge, good enough to show the shape of an eval gate.

## Run locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m uvicorn app.main:app --port 8080
```

Then:

```bash
curl localhost:8080/health
curl -X POST localhost:8080/evaluate
curl -X POST localhost:8080/evaluate -H 'Content-Type: application/json' -d '{}'
```

## Run the tests

```bash
pip install -r requirements.txt
pytest -q
python tests/smoke_http.py
bash -n deploy.sh
bash tests/test_deploy.sh
```

The HTTP smoke launches a temporary Uvicorn process bound to loopback, tests
real HTTP requests, then stops it. The shell test replaces `gcloud` with a
function that records arguments; it never invokes Google Cloud.

## Docker

```bash
docker build -t eval-service-gcp .
docker run -p 8080:8080 eval-service-gcp
```

The container runs as a nonroot user, honors `PORT`, and uses `exec` so
Uvicorn receives termination signals. `.github/workflows/verify.yml` runs
the tests, builds the image, and checks `/health` and a bodyless `/evaluate`
inside the container on a nondefault port. It runs on pull requests, pushes
to `main`, and manual dispatch. This workflow makes no cloud calls.

## Verification status

Local verification on 2026-11-15 (Windows, Python 3.13; Bash via Ubuntu WSL):

- **Passed:** 30 pytest cases, real Uvicorn HTTP smoke, `pip check`, Bash syntax,
  and offline mocked `gcloud` command checks.
- The built-in synthetic set remains **13/15 passed**, with the default
  gate unchanged at **0.8**.
- Pytest reports one upstream Starlette/AnyIO deprecation warning.
- **Passed on GitHub-hosted Linux:** Docker image build, nonroot runtime,
  `PORT=9090`, `/health`, and a bodyless `/evaluate`
  ([verified run](https://github.com/shazamlll/eval-service-gcp/actions/runs/43692320763)).
  The first run exposed a startup-probe connection reset; readiness now uses
  bounded polling. Local Windows/WSL still has no Docker/Podman CLI.
- **Not verified:** Cloud Build, registry permissions, Cloud Run deployment,
  public endpoint, real LLM judge, or real traffic. No cloud resources were
  created and no paid APIs were called.

## Remaining work

Deployment and wiring were deliberately left out of this repo. A follow-up
agent (or a human) still needs to:

1. Completed: GitHub-hosted Docker build and container smoke verification.
2. When cloud deployment is explicitly authorized, choose a GCP project,
   enable Cloud Run, Cloud Build, and Artifact Registry, and create a Docker
   Artifact Registry repository in the chosen region with the required IAM permissions.
3. Set a **budget alert** before deploying anything. An alert is not a spending cap.
4. Authenticate, then run `PROJECT_ID=my-project REPOSITORY=demo-images REGION=us-central1 bash deploy.sh`
   from Bash/WSL. The script uses Artifact Registry (`REGION-docker.pkg.dev`)
   and builds from its own repository directory. It has only been tested
   with mocked `gcloud`, never against a cloud account.
5. Verify `/health` and a bodyless `POST /evaluate` at the deployed URL.
   The script defaults to **private access**: use an authorized identity token,
   for example `curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" <service-url>/health`.
   Set `PUBLIC_ACCESS=true` only when intentionally publishing this unauthenticated demo.
6. Optionally wire a real LLM judge: add an API key via Cloud Run secrets / env vars and swap the deterministic judge in `app/judge.py` for a model-backed one — keeping the same response shape so the gate logic does not change.

## Honest limits

- The judge is a keyword-overlap heuristic, not an LLM judge; it cannot catch subtle hallucinations or reasoning errors.
- Token overlap does not reliably understand negation or contradictory numbers; high overlap can still produce a false pass.
- All eval data is synthetic. Nothing here has been validated on real traffic.
- No auth, no rate limiting, no persistence — this is a demo, not a service you would put in front of users.
- The app has no request-size or item-count limits. Keep access private for controlled demonstrations.
