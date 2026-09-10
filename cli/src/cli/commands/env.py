"""``bp env`` — inspect and prepare the runtime environment.

Two commands today:

- ``bp env gen-secret`` prints a 64-char hex string suitable for
  ``SECRET_KEY``. No filesystem I/O — pipe it into your secrets manager.

- ``bp env validate`` runs the production security validator against
  the current settings, regardless of the configured environment, and
  prints critical errors and warnings.
"""

from __future__ import annotations

import logging
import secrets

import typer

# The installed package layout puts `infrastructure`, `modules`, etc.
# at the top of the import tree (see [tool.setuptools.packages.find]
# in backend/pyproject.toml). The CLI is only callable when the package
# is installed, so this form is always valid here.
from infrastructure.config.settings import get_settings
from infrastructure.security.production_validator import (
    ProductionSecurityError,
    ProductionSecurityValidator,
)

from ..lib.prompts import error, info, success, warn

app = typer.Typer(no_args_is_help=True, help="Inspect and prepare the runtime environment.")


@app.command("gen-secret")
def gen_secret(
    bytes_: int = typer.Option(32, "--bytes", min=16, max=128, help="Number of random bytes (hex output is 2x)."),
) -> None:
    """Generate a high-entropy hex secret suitable for ``SECRET_KEY``."""
    typer.echo(secrets.token_hex(bytes_))


@app.command("validate")
def validate() -> None:
    """Run the production security validator against the current settings.

    Forces production-mode validation regardless of ``ENVIRONMENT`` so
    you can audit a dev or staging config the same way prod is gated.
    """
    settings = get_settings()

    class _ForcedProd(ProductionSecurityValidator):
        def _is_production(self) -> bool:
            return True

    validator = _ForcedProd(settings)

    captured_warnings: list[str] = []
    handler = _CapturingHandler(captured_warnings)
    validator.logger.addHandler(handler)
    # Silence the validator's normal logging while we drive it — we render
    # the result ourselves below.
    previous_level = validator.logger.level
    previous_propagate = validator.logger.propagate
    validator.logger.setLevel(logging.CRITICAL + 1)
    validator.logger.propagate = False
    handler.setLevel(logging.WARNING)  # still capture warnings via the dedicated handler

    critical_errors: list[str] = []
    try:
        try:
            validator.validate_production_security()
        except ProductionSecurityError as exc:
            critical_errors = [line.strip(" •") for line in str(exc).splitlines()[1:] if line.strip()]
    finally:
        validator.logger.removeHandler(handler)
        validator.logger.setLevel(previous_level)
        validator.logger.propagate = previous_propagate

    if not critical_errors and not captured_warnings:
        success("No issues found. Configuration would pass production validation.")
        return

    if critical_errors:
        error(f"Critical ({len(critical_errors)}):")
        for item in critical_errors:
            typer.secho(f"  • {item}", fg=typer.colors.RED)

    if captured_warnings:
        if critical_errors:
            info("")
        warn(f"Warnings ({len(captured_warnings)}):")
        for item in captured_warnings:
            typer.secho(f"  • {item}", fg=typer.colors.YELLOW)

    if critical_errors:
        raise typer.Exit(code=1)


class _CapturingHandler(logging.Handler):
    """Capture only the warning lines emitted by the production validator."""

    def __init__(self, sink: list[str]) -> None:
        super().__init__(level=logging.WARNING)
        self._sink = sink

    def emit(self, record: logging.LogRecord) -> None:
        message = record.getMessage()
        marker = "PRODUCTION SECURITY WARNING: "
        if marker in message:
            self._sink.append(message.split(marker, 1)[1])
