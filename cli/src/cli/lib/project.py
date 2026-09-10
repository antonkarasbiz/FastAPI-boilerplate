"""Locate the user's project on disk and read context from it.

The CLI is shipped inside ``backend/src/cli`` of the boilerplate, but
when invoked it operates on whichever directory the user is in. These
helpers resolve the repo root, the backend directory, and read values
from the project's ``.env`` files without importing the application.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectContext:
    """Resolved paths the CLI needs to operate on the user's repo."""

    repo_root: Path
    backend_dir: Path

    @property
    def env_file(self) -> Path:
        return self.backend_dir / ".env"

    @property
    def env_example(self) -> Path:
        return self.backend_dir / ".env.example"

    @property
    def compose_file(self) -> Path:
        return self.repo_root / "docker-compose.yml"


def discover_project(start: Path | None = None) -> ProjectContext:
    """Walk up from ``start`` looking for a ``backend/pyproject.toml`` marker.

    Falls back to the current working directory if no marker is found —
    the caller is responsible for deciding whether that's acceptable.
    """
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "backend" / "pyproject.toml").is_file():
            return ProjectContext(repo_root=candidate, backend_dir=candidate / "backend")
        if (candidate / "pyproject.toml").is_file() and candidate.name == "backend":
            return ProjectContext(repo_root=candidate.parent, backend_dir=candidate)
    return ProjectContext(repo_root=current, backend_dir=current / "backend")


def read_env_value(env_path: Path, key: str) -> str | None:
    """Read a single value from a ``.env``-style file.

    Returns ``None`` if the file is missing or the key isn't set. Quotes
    around the value (single or double) are stripped. Lines beginning
    with ``#`` are skipped.
    """
    if not env_path.is_file():
        return None
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, _, value = line.partition("=")
        if name.strip() != key:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        return value
    return None
