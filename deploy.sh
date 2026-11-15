#!/usr/bin/env bash
# Deploy eval-service-gcp to Google Cloud Run.
#
# NOT EXECUTED as part of building this repo. A follow-up agent (or a
# human) runs this after completing the "Remaining work" steps in the
# README: enable the required GCP APIs, create a project, set a budget
# alert, and authenticate with `gcloud auth login`.
#
# Requires an existing Docker Artifact Registry repository in REGION.
# Usage (private service by default):
#   PROJECT_ID=my-project REPOSITORY=demo-images bash deploy.sh
set -euo pipefail

PROJECT_ID="${PROJECT_ID:?set PROJECT_ID to your GCP project id}"
REGION="${REGION:-us-central1}"
SERVICE_NAME="${SERVICE_NAME:-eval-service-gcp}"
REPOSITORY="${REPOSITORY:?set REPOSITORY to an existing Artifact Registry Docker repository}"
PUBLIC_ACCESS="${PUBLIC_ACCESS:-false}"
case "$PUBLIC_ACCESS" in
  true) ACCESS_FLAG=--allow-unauthenticated ;;
  false) ACCESS_FLAG=--no-allow-unauthenticated ;;
  *) echo 'PUBLIC_ACCESS must be true or false' >&2; exit 1 ;;
esac
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${SERVICE_NAME}:latest"

echo "Building image ${IMAGE}..."
gcloud builds submit --tag "${IMAGE}" --project "${PROJECT_ID}" "${SCRIPT_DIR}"

echo "Deploying to Cloud Run (${REGION})..."
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE}" \
  --platform managed \
  --region "${REGION}" \
  --project "${PROJECT_ID}" \
  "${ACCESS_FLAG}" \
  --port 8080 \
  --set-env-vars EVAL_PASS_RATE_THRESHOLD=0.8

echo "Done. Verify with:"
echo "  Read the service URL with gcloud run services describe ${SERVICE_NAME} --region ${REGION} --project ${PROJECT_ID} --format 'value(status.url)'"
if [[ "$PUBLIC_ACCESS" == false ]]; then
  echo '  curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" <service-url>/health'
else
  echo '  curl <service-url>/health'
fi
