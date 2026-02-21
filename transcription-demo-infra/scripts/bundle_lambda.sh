#!/usr/bin/env bash
# Bundle Lambda code + dependencies for CDK asset. Run before 'cdk deploy' when Lambda code or deps change.
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LAMBDA_SRC="$REPO_ROOT/lambda"
BUNDLE_DIR="$REPO_ROOT/.lambda_bundle"
rm -rf "$BUNDLE_DIR"
mkdir -p "$BUNDLE_DIR"
cp -r "$LAMBDA_SRC"/* "$BUNDLE_DIR/"
if command -v uv >/dev/null 2>&1; then
  uv pip install -r "$BUNDLE_DIR/requirements.txt" --target "$BUNDLE_DIR" --quiet
else
  python3 -m pip install -r "$BUNDLE_DIR/requirements.txt" -t "$BUNDLE_DIR" --quiet
fi
rm -f "$BUNDLE_DIR/requirements.txt"
echo "Lambda bundle ready at $BUNDLE_DIR"
