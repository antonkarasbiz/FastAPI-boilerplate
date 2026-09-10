"""Consistent prompt helpers used across the CLI.

Centralizes ``--yes`` (assume-yes) and ``--quiet`` handling so individual
commands don't each invent their own.
"""

from __future__ import annotations

import typer


def confirm_overwrite(path: str, *, assume_yes: bool) -> bool:
    """Confirm overwriting an existing file. Returns True to proceed."""
    if assume_yes:
        return True
    return typer.confirm(f"{path} already exists. Overwrite?", default=False)


def info(message: str) -> None:
    typer.echo(message)


def success(message: str) -> None:
    typer.secho(message, fg=typer.colors.GREEN)


def warn(message: str) -> None:
    typer.secho(message, fg=typer.colors.YELLOW)


def error(message: str) -> None:
    typer.secho(message, fg=typer.colors.RED, err=True)
