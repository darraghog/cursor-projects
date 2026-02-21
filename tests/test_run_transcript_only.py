"""Unit tests for run_transcript_only script: transcript validation."""
import json
import sys
from pathlib import Path

import pytest

# Script lives in scripts/
SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))


def test_validation_rejects_json_without_results_items(tmp_path):
    bad_json = tmp_path / "bad.json"
    bad_json.write_text(json.dumps({"results": {}}), encoding="utf-8")
    with pytest.raises(SystemExit) as exc_info:
        sys.argv = ["run_transcript_only.py", "--transcript", str(bad_json)]
        import run_transcript_only as script
        script.main()
    assert exc_info.value.code == 1


def test_validation_rejects_json_without_results(tmp_path):
    bad_json = tmp_path / "bad.json"
    bad_json.write_text(json.dumps({"items": []}), encoding="utf-8")
    with pytest.raises(SystemExit) as exc_info:
        sys.argv = ["run_transcript_only.py", "--transcript", str(bad_json)]
        import run_transcript_only as script
        script.main()
    assert exc_info.value.code == 1
