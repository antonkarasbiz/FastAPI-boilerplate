"""Look up features by name across in-tree and plugin sources.

In-tree features are imported lazily so that adding new ones doesn't
slow down every CLI invocation. Plugin features come from the
``bp.features`` entry-point group.
"""

from __future__ import annotations

import warnings

from .. import plugins as _plugins
from ._builtins.deploy.feature import DeployFeature
from .base import Feature


def _builtin_features() -> dict[str, Feature]:
    """Return in-tree features."""
    return {
        "deploy": DeployFeature(),
    }


def all_features() -> dict[str, Feature]:
    """Return ``{name: feature}`` for every in-tree and plugin feature.

    In-tree features take precedence on name collisions; a warning is
    surfaced when a plugin tries to shadow a built-in.
    """
    found: dict[str, Feature] = dict(_builtin_features())
    for name, feature in _plugins.discover_feature_plugins().items():
        if name in found:
            warnings.warn(
                f"feature plugin {name!r} shadows a built-in; ignoring plugin.",
                RuntimeWarning,
                stacklevel=2,
            )
            continue
        found[name] = feature
    return found


def get_feature(name: str) -> Feature | None:
    return all_features().get(name)
