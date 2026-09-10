"""Feature contracts: manifest, plan, base class, and operation types.

The shapes here are designed so that today's "render templates to disk"
features and tomorrow's "drop a module + edit settings + run a
migration" features can both describe themselves with the same plan
schema. Installers grow capabilities over time; manifests don't have
to change.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..lib.project import ProjectContext


@dataclass(frozen=True)
class FeatureManifest:
    """Static metadata about a feature.

    The manifest is the part that's safe to read without executing
    anything — used by ``bp feature list`` / ``bp feature info`` to
    describe what's available.
    """

    name: str
    version: str
    summary: str
    requires_features: tuple[str, ...] = ()
    adds_dependencies: tuple[str, ...] = ()


@dataclass(frozen=True)
class FileOp:
    """Render a Jinja template and write it to ``target``.

    ``template`` is interpreted relative to the feature's templates
    directory. ``target`` is an absolute path on the user's disk.
    """

    template: str
    target: Path
    overwrite: bool = False
    skip_if_exists: bool = False
    executable: bool = False


@dataclass(frozen=True)
class Codemod:
    """Reserved for AST-aware edits to existing source files.

    Not implemented in v1. Defining the type here means feature plans
    can reference codemods today without breaking the manifest schema
    when the installer learns to execute them.
    """

    target: Path
    operation: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Hook:
    """Reserved for post-install commands (alembic revisions, scripts, etc.)."""

    name: str
    command: tuple[str, ...]
    cwd: Path | None = None


@dataclass(frozen=True)
class FeaturePlan:
    """Concrete description of what a feature wants to do, given parameters."""

    manifest: FeatureManifest
    templates_root: Path | None
    template_context: dict[str, Any] = field(default_factory=dict)
    files: tuple[FileOp, ...] = ()
    codemods: tuple[Codemod, ...] = ()
    hooks: tuple[Hook, ...] = ()


class Feature(ABC):
    """Base class for all features.

    Subclasses declare a static ``manifest()`` and an instance-method
    ``plan(params, project)`` that yields the concrete plan for the
    current invocation.
    """

    @abstractmethod
    def manifest(self) -> FeatureManifest: ...

    @abstractmethod
    def plan(self, params: dict[str, Any], project: ProjectContext) -> FeaturePlan: ...
