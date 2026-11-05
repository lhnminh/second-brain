"""Deploy saved project files to this laptop's linked Vercel project.

Usage: .venv/Scripts/python.exe scripts/deploy.py [--prepare-only]
Credentials stay in .env.second-brain-hosted and Vercel environment variables.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from dotenv import dotenv_values


def source_files(root):
    output = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root,
    )
    for name in dict.fromkeys(os.fsdecode(output).split("\0")):
        if not name:
            continue
        relative = Path(name)
        parts = {part.lower() for part in relative.parts}
        if parts.intersection(
            {
                ".git",
                ".vercel",
                ".venv",
                ".uv-cache",
                ".browser-workspace",
                "__pycache__",
            }
        ):
            continue
        if any(part == ".env" or part.startswith(".env.") for part in parts):
            continue
        if relative.name.lower().endswith(
            (".db", ".db-journal", ".db-wal", ".db-shm", ".pyc")
        ):
            continue
        source = root / relative
        if not source.is_file():
            continue  # Deleted tracked files must not return in the deployment.
        if not source.resolve().is_relative_to(root.resolve()):
            raise ValueError(f"Source file leaves the project directory: {relative}")
        yield relative


def prepare_source(root, target):
    files = list(source_files(root))
    for relative in files:
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / relative, destination)
    link = root / ".vercel" / "project.json"
    if not link.is_file():
        raise ValueError("Link your Vercel project first with: vercel link")
    project = json.loads(link.read_text(encoding="utf-8"))
    if not project.get("projectId") or not project.get("orgId"):
        raise ValueError("The local Vercel project link is incomplete")
    (target / ".vercel").mkdir(exist_ok=True)
    shutil.copy2(link, target / ".vercel" / "project.json")
    return project, len(files)


def vercel_command(root):
    # The existing laptop setup uses a private npm cache, without a global install.
    cached = sorted(
        (root / ".uv-cache/npm-cache/_npx").glob("*/node_modules/vercel/dist/vc.js")
    )
    if cached and shutil.which("node"):
        return [shutil.which("node"), str(cached[-1])]
    if installed := shutil.which("vercel"):
        return [installed]
    raise ValueError(
        "Install the official Vercel CLI and sign in: npm install -g vercel; vercel login"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--prepare-only",
        action="store_true",
        help="Check the source bundle without migrating or deploying",
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    try:
        # Outside the repository: no inherited Git owner/author metadata and no
        # stale files left over from earlier source snapshots.
        # Vercel's Windows helper can hold the folder briefly after exiting.
        # Cleanup must not turn a successful production deployment into failure.
        with tempfile.TemporaryDirectory(
            prefix="second-brain-deploy-", ignore_cleanup_errors=True
        ) as folder:
            target = Path(folder)
            project, count = prepare_source(root, target)
            print(
                f"Prepared {count} saved source files for {project.get('projectName', project['projectId'])}.",
                flush=True,
            )
            if args.prepare_only:
                print("Bundle checked. No database or deployment changes made.")
                return
            command = vercel_command(root)
            values = dotenv_values(root / ".env.second-brain-hosted")
            database_url = os.environ.get("DATABASE_URL") or values.get("DATABASE_URL")
            if not database_url or not database_url.startswith(
                ("postgres://", "postgresql://", "postgresql+psycopg://")
            ):
                raise ValueError(
                    "Set your hosted Postgres DATABASE_URL in .env.second-brain-hosted before deploying"
                )
            env = {
                **os.environ,
                "DATABASE_URL": database_url,
                "PYTHONPATH": str(target / "backend"),
            }
            print("Applying pending migrations to your hosted database...", flush=True)
            migration = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "alembic",
                    "-c",
                    str(target / "backend/alembic.ini"),
                    "upgrade",
                    "head",
                ],
                cwd=target,
                env=env,
                check=False,
                capture_output=True,
                text=True,
            )
            if migration.returncode:
                # Database errors can contain connection credentials. Preserve
                # privacy and stop before publishing incompatible application code.
                raise ValueError(
                    "Database migration failed. Deployment stopped; database error output withheld to protect credentials."
                )
            print("Migrations complete. Deploying to Vercel...", flush=True)
            deploy_args = [
                "deploy",
                "--prod",
                "--yes",
                "--scope",
                project["orgId"],
                "--cwd",
                str(target),
            ]
            # Keep hosting choices local when the shared repo serves deployments
            # whose databases live in different regions.
            if region := values.get("DEPLOY_REGION"):
                deploy_args.extend(["--regions", region])
            subprocess.run(
                command + deploy_args,
                check=True,
            )
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
