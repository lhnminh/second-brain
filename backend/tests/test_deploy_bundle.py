"""Deployment source includes current edits, without secrets or stale files."""

import importlib.util
import json
import subprocess
from pathlib import Path


def test_clean_bundle_uses_current_files_and_excludes_even_tracked_credentials(
    tmp_path,
):
    script = Path(__file__).resolve().parents[2] / "scripts/deploy.py"
    spec = importlib.util.spec_from_file_location("deploy_helper", script)
    deploy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(deploy)
    root, target = tmp_path / "repo", tmp_path / "bundle"
    root.mkdir()
    target.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    (root / ".gitignore").write_text(".vercel/\n.uv-cache/\n", encoding="utf-8")
    (root / "app.py").write_text("old content", encoding="utf-8")
    (root / "deleted.py").write_text("old file", encoding="utf-8")
    (root / ".env").write_text("PRIVATE_KEY=secret", encoding="utf-8")
    (root / "private.db").write_bytes(b"private database")
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    (root / "app.py").write_text("latest saved content", encoding="utf-8")
    (root / "deleted.py").unlink()
    (root / "new_feature.py").write_text("new code", encoding="utf-8")
    (root / ".env.second-brain-hosted").write_text(
        "DATABASE_URL=private", encoding="utf-8"
    )
    (root / ".uv-cache").mkdir()
    (root / ".uv-cache/private.txt").write_text("private fixture", encoding="utf-8")
    (root / ".vercel").mkdir()
    (root / ".vercel/project.json").write_text(
        json.dumps({"projectId": "project", "orgId": "team", "projectName": "test"}),
        encoding="utf-8",
    )
    project, _ = deploy.prepare_source(root, target)
    assert project["projectId"] == "project"
    assert (target / "app.py").read_text() == "latest saved content"
    assert (target / "new_feature.py").is_file()
    assert (target / ".vercel/project.json").is_file()
    for name in (
        ".git",
        ".env",
        ".env.second-brain-hosted",
        "private.db",
        ".uv-cache",
        "deleted.py",
    ):
        assert not (target / name).exists()
