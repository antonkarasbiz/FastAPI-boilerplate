"""bp — the FastAPI-boilerplate command-line tool.

The CLI is a Typer application with two extension points:

- `bp.commands` entry-point group: third-party packages can register
  top-level Typer sub-apps that mount under `bp <name>`.
- `bp.features` entry-point group: third-party packages can register
  ``Feature`` instances that ``bp feature`` can list, install, and remove.

In-tree commands and features live alongside this package and follow
the same contracts as plugins.
"""
