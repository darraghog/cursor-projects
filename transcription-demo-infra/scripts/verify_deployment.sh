#!/usr/bin/env bash
# Verify deployment: get bucket from CDK stack output, run transcript-only demo, assert results.txt appears.
# Run from transcription-demo-infra. Requires AWS credentials and a deployed stack.
set -e

PROFILE="${AWS_PROFILE:-administrator}"
INSTANCE="${INSTANCE:-default}"
STACK_NAME="TranscriptionDemoLambda"
if [[ "$INSTANCE" != "default" ]]; then
  STACK_NAME="${STACK_NAME}-${INSTANCE}"
fi

echo "Getting bucket name from stack ${STACK_NAME}..."
BUCKET=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --profile "$PROFILE" --query "Stacks[0].Outputs[?OutputKey=='BucketName'].OutputValue" --output text 2>/dev/null || true)
if [[ -z "$BUCKET" || "$BUCKET" == "None" ]]; then
  echo "Error: Could not get BucketName output from stack $STACK_NAME. Is it deployed? Try: cdk deploy TranscriptionDemoLambda" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INFRA_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
# transcription-demo is typically a sibling of transcription-demo-infra (cursor-projects/transcription-demo)
DEMO_DIR="${DEMO_DIR:-$(cd "$INFRA_DIR/../transcription-demo" 2>/dev/null && pwd)}"
if [[ -z "$DEMO_DIR" || ! -d "$DEMO_DIR" ]]; then
  echo "Error: transcription-demo not found at $INFRA_DIR/../transcription-demo. Set DEMO_DIR or run from cursor-projects." >&2
  exit 1
fi

echo "Running transcript-only demo against bucket: $BUCKET"
cd "$DEMO_DIR"
uv run python scripts/run_transcript_only.py --bucket "$BUCKET" --profile "$PROFILE" --wait-seconds 45
echo "Verification passed: Lambda wrote results.txt to the bucket."
