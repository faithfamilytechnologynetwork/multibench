"""Single-source the universal core (framings, pressures).

The three framings and the six pressures are **universal core**, defined ONCE in
``tradition_validator.core`` and identical across every tradition. This module
re-exports them (mirroring ``workflows/judging``'s ``core_imports``) so the
analysis workflow never redefines them — keeping figure column/row order and every
cross-tradition comparison on the same canonical axes.
"""

from __future__ import annotations

from tradition_validator.core import (  # noqa: F401  -- re-exported on purpose
    FRAMINGS,
    PRESSURES,
)

__all__ = ["FRAMINGS", "PRESSURES"]
