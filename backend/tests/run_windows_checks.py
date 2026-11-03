"""Run unchanged Node harnesses on Windows without exceeding command-line limits.

Usage: uv run python backend/tests/run_windows_checks.py backend/tests -q
This changes only script transport and large binary-fixture display names.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

original_run = subprocess.run


def run_with_script_file(args, *rest, **kwargs):
    if (
        isinstance(args, list)
        and len(args) >= 3
        and str(args[0]).lower().endswith(("node", "node.exe"))
        and args[1] == "-e"
    ):
        with tempfile.TemporaryDirectory(prefix="second-brain-check-") as folder:
            script = Path(folder) / "harness.cjs"
            script.write_text(args[2], encoding="utf-8")
            return original_run([args[0], str(script), *args[3:]], *rest, **kwargs)
    return original_run(args, *rest, **kwargs)


subprocess.run = run_with_script_file


class ShortByteIds:
    def pytest_make_parametrize_id(self, config, val, argname):
        if isinstance(val, bytes):
            from hashlib import sha256

            return argname + "-" + sha256(val).hexdigest()[:12]


raise SystemExit(pytest.main(sys.argv[1:], plugins=[ShortByteIds()]))
