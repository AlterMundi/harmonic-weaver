"""Typed, protocol-safe failures raised by the Weaver engine."""

from __future__ import annotations

from typing import Any


class WeaverError(ValueError):
    """A validation or state error with a Stage Contract error code."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        details: Any | None = None,
        current_stage_revision: int | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details
        self.current_stage_revision = current_stage_revision


def validation(message: str, *, details: Any | None = None) -> WeaverError:
    return WeaverError("validation_failed", message, details=details)


__all__ = ["WeaverError", "validation"]
