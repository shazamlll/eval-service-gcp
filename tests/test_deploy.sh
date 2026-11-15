#!/usr/bin/env bash
# Offline command-contract tests: this function replaces gcloud completely.
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
CALLS="$(mktemp)"
export CALLS
trap 'rm -f -- "$CALLS"' EXIT
gcloud() { printf '%s\n' "$*" >> "$CALLS"; }
export -f gcloud
export PROJECT_ID=synthetic-demo-project
export REGION=us-central1
export REPOSITORY=demo-images
export SERVICE_NAME=eval-service-gcp
failures=0
check() {
    if "$@"; then printf 'PASS: %s\n' "$*";
    else printf 'FAIL: %s\n' "$*"; failures=$((failures + 1)); fi
}

# Invocation must work outside the repository, and be private by default.
(cd /tmp && bash "$SCRIPT_DIR/deploy.sh") >/dev/null
check grep -Fq 'us-central1-docker.pkg.dev/synthetic-demo-project/demo-images/eval-service-gcp:latest' "$CALLS"
check grep -Fq -- '--no-allow-unauthenticated' "$CALLS"
check grep -Fq -- "--project synthetic-demo-project $SCRIPT_DIR" "$CALLS"

: > "$CALLS"
PUBLIC_ACCESS=true bash "$SCRIPT_DIR/deploy.sh" >/dev/null
check grep -Fq -- '--allow-unauthenticated' "$CALLS"

: > "$CALLS"
if PUBLIC_ACCESS=typo bash "$SCRIPT_DIR/deploy.sh" >/dev/null 2>&1; then
    printf 'FAIL: invalid PUBLIC_ACCESS was accepted\n'
    failures=$((failures + 1))
fi
check test ! -s "$CALLS"
exit "$failures"
