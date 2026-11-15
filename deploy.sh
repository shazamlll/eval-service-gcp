#!/usr/bin/env bash
# Deploy eval-service-gcp to Google Cloud Run.
#
# NOT EXECUTED as part of building this repo. A follow-up agent (or a
# human) runs this after completing the "Remaining work" steps in the
# README: enable the required GCP APIs, create a project, set a budget
# alert, and authenticate with `gcloud auth login`.
#
# Usage:
#   PROJECT_ID=my-project REGION=us-central1 ./deploy.sh
set -euo pipefail

PROJECT_ID="${PROJECT_ID:?set PROJECT_ID to your GCP project id}"
REGION="${REGION:-us-central1}"
SERVICE_NAME="${SERVICE_NAME:-eval-service-gcp}"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"

echo "Building image ${IMAGE}..."
gcloud builds submit --tag "${IMAGE}" --project "${PROJECT_ID}" .

echo "Deploying to Cloud Run (${REGION})..."
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE}" \
  --platform managed \
  --region "${REGION}" \
  --project "${PROJECT_ID}" \
  --allow-unauthenticated \
  --port 8080 \
  --set-env-vars EVAL_PASS_RATE_THRESHOLD=0.8

echo "Done. Verify with:"
echo "  curl \"\$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --project ${PROJECT_ID} --format 'value(status.url)')/health\""
