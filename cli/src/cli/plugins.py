"""Plugin discovery for the bp CLI.

Two extension points, kept deliberately separate:

- ``bp.commands`` — a Typer sub-app mounted under the root, e.g.
  ``bp aws deploy``. Plugin packages declare entry points whose values
  resolve to a ``typer.Typer`` instance.

- ``bp.features`` — a ``Feature`` instance that ``bp feature`` can list
  and apply. Plugin packages declare entry points whose values resolve
  to ``Feature`` instances (or callables that return one).

A broken plugin must not break the CLI. Discovery wraps each load in a
broad except and surfaces a warning so the user can still operate the
working subset.
"""

from __future__ import annotations

import sys
import warnings
from importlib.metadata import EntryPoint, entry_points

import typer

from .features.base import Feature

COMMANDS_GROUP = "bp.commands"
FEATURES_GROUP = "bp.features"


def _safe_load(ep: EntryPoint) -> object | None:
    try:
        loaded: object = ep.load()
    except Exception as exc:
        warnings.warn(
            f"Failed to load plugin {ep.name!r} from {ep.value!r}: {exc!s}",
            RuntimeWarning,
            stacklevel=2,
        )
        return None
    return loaded


def discover_command_plugins() -> dict[str, typer.Typer]:
    """Return ``{name: typer_app}`` for every healthy ``bp.commands`` entry point."""
    found: dict[str, typer.Typer] = {}
    for ep in entry_points(group=COMMANDS_GROUP):
        loaded = _safe_load(ep)
        if loaded is None:
            continue
        if isinstance(loaded, typer.Typer):
            found[ep.name] = loaded
        else:
            warnings.warn(
                f"Plugin {ep.name!r} resolved to {type(loaded).__name__}, expected typer.Typer; ignoring.",
                RuntimeWarning,
                stacklevel=2,
            )
    return found


def discover_feature_plugins() -> dict[str, Feature]:
    """Return ``{name: feature}`` for every healthy ``bp.features`` entry point.

    Entry-point values may be either a ``Feature`` instance or a callable
    that returns one (helpful when constructing features needs the project
    context).
    """
    found: dict[str, Feature] = {}
    for ep in entry_points(group=FEATURES_GROUP):
        loaded = _safe_load(ep)
        if loaded is None:
            continue
        candidate = loaded() if callable(loaded) and not isinstance(loaded, Feature) else loaded
        if isinstance(candidate, Feature):
            found[ep.name] = candidate
        else:
            warnings.warn(
                f"Feature plugin {ep.name!r} resolved to {type(candidate).__name__}, expected Feature; ignoring.",
                RuntimeWarning,
                stacklevel=2,
            )
    return found


def emit_plugin_warnings_to_stderr() -> None:
    """Route plugin-load warnings to stderr so CLI output stays clean."""
    warnings.filterwarnings("default", category=RuntimeWarning, module=__name__)
    if not any(isinstance(h, _StderrWarningHandler) for h in _installed_handlers()):
        warnings.showwarning = _StderrWarningHandler()


class _StderrWarningHandler:
    def __call__(
        self,
        message: Warning | str,
        category: type[Warning],
        filename: str,
        lineno: int,
        file: object = None,
        line: str | None = None,
    ) -> None:
        print(f"warning: {message}", file=sys.stderr)


def _installed_handlers() -> list[object]:
    handler = warnings.showwarning
    return [handler] if handler is not None else []
