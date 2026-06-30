"""Single-source the universal core (framings, pressures, helpers).

The three framings and the six pressures are **universal core**, defined ONCE in
``tradition_validator.core`` (spec §5.6; issue: "coordinate … don't fork
divergently"). This module re-exports them so the judging workflow never
redefines them — keeping every tradition comparable against the same axes.
"""

from __future__ import annotations

from tradition_validator.core import (  # noqa: F401  -- re-exported on purpose
    FRAMINGS,
    IDENTITY_SIGNALS,
    PRESSURES,
    STATED_TEMPLATE,
    normalize_heading,
    stated_prompt,
)

__all__ = [
    "FRAMINGS",
    "IDENTITY_SIGNALS",
    "PRESSURES",
    "STATED_TEMPLATE",
    "normalize_heading",
    "stated_prompt",
]
