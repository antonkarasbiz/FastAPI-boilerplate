"""Feature framework: typed manifests, plans, and the installer.

A feature is a self-contained unit of work that mutates a user's
project — generating files, editing existing files, running setup
hooks. ``Feature`` subclasses describe themselves via a manifest and
emit a ``FeaturePlan`` that the installer executes.

For v1 only ``FileOp`` operations are supported. ``Codemod`` and ``Hook``
slots in the plan exist for forward compatibility — installers raise
``NotImplementedError`` if a plan asks for one.
"""

from .base import Codemod, Feature, FeatureManifest, FeaturePlan, FileOp, Hook
from .installer import FeatureInstaller, InstallResult

__all__ = [
    "Codemod",
    "Feature",
    "FeatureInstaller",
    "FeatureManifest",
    "FeaturePlan",
    "FileOp",
    "Hook",
    "InstallResult",
]
