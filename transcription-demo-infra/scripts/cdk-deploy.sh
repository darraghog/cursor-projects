#!/usr/bin/env bash
# Run CDK deploy with only the named profile (no AWS_ACCESS_KEY_ID etc.) so the profile is used.
# Usage: ./scripts/cdk-deploy.sh [cdk deploy args...]
# Example: ./scripts/cdk-deploy.sh --all --require-approval never
set -e

PROFILE="${AWS_PROFILE:-administrator}"
# Optional: pass account/region to avoid "Unable to resolve AWS account"
ACCOUNT="${CDK_ACCOUNT:-}"
REGION="${CDK_REGION:-us-east-1}"

# Build minimal env: no credential env vars, so SDK uses the profile
export AWS_PROFILE="$PROFILE"
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN

# Ensure config files are found (default paths)
export AWS_CONFIG_FILE="${AWS_CONFIG_FILE:-$HOME/.aws/config}"
export AWS_SHARED_CREDENTIALS_FILE="${AWS_SHARED_CREDENTIALS_FILE:-$HOME/.aws/credentials}"

CDK_ARGS=("$@")
[[ -n "$ACCOUNT" ]] && CDK_ARGS+=(-c "account=$ACCOUNT")
[[ -n "$ACCOUNT" ]] && CDK_ARGS+=( -c "region=$REGION")

cd "$(dirname "$0")/.."
exec cdk deploy "${CDK_ARGS[@]}"
