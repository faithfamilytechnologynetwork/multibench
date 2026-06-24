"""Pydantic v2 schemas for the machine-readable tradition files (spec §5.2/§5.4).

All models are **closed** (``extra="forbid"`` — unknown keys are errors) and
**strict** (``strict=True`` — no type coercion, so YAML 1.1's ``no`` → ``False`` for a
string field is a type error, not a silent value). This is the machine-checkable
contract the spec requires.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

_STRICT = ConfigDict(extra="forbid", strict=True, populate_by_name=True)


class CanonicalSource(BaseModel):
    model_config = _STRICT
    title: str = Field(min_length=1)
    author: str = Field(min_length=1)
    locus_unit: str = Field(min_length=1)


class Maintainer(BaseModel):
    model_config = _STRICT
    name: str = Field(min_length=1)
    contact: str | None = None


class ScholarReview(BaseModel):
    model_config = _STRICT
    status: Literal["none", "in_progress", "reviewed"]
    reviewers: list[str] = Field(default_factory=list)


class TaxonomyAxis(BaseModel):
    model_config = _STRICT
    description: str = Field(min_length=1)
    applies_to: Literal["scenario", "response"]
    values: list[str] = Field(min_length=1)

    @field_validator("values")
    @classmethod
    def _values_non_empty_no_dupes(cls, v: list[str]) -> list[str]:
        if any(not isinstance(x, str) or not x.strip() for x in v):
            raise ValueError("axis values must be non-empty strings")
        if len(set(v)) != len(v):
            dupes = sorted({x for x in v if v.count(x) > 1})
            raise ValueError(f"duplicate axis values: {dupes}")
        return v


class TraditionManifest(BaseModel):
    model_config = _STRICT
    id: str = Field(min_length=1)
    schema_version: int
    display_name: str = Field(min_length=1)
    # 'construct' is the YAML key; the Python attribute is aliased to avoid shadowing
    # the deprecated BaseModel.construct method (pydantic UserWarning).
    construct_: str = Field(min_length=1, alias="construct")
    canonical_source: CanonicalSource
    adherent_noun: str = Field(min_length=1)
    maintainers: list[Maintainer] = Field(min_length=1)
    scholar_review: ScholarReview
    taxonomies: dict[str, TaxonomyAxis] = Field(min_length=1)
    scenario_id_pattern: str = Field(min_length=1)

    @field_validator("id")
    @classmethod
    def _id_is_slug(cls, v: str) -> str:
        if not re.fullmatch(r"[a-z][a-z0-9-]*", v):
            raise ValueError(f"id must match ^[a-z][a-z0-9-]*$ (got {v!r})")
        return v

    @field_validator("scenario_id_pattern")
    @classmethod
    def _scenario_id_pattern_compiles(cls, v: str) -> str:
        try:
            re.compile(v)
        except re.error as e:
            raise ValueError(f"scenario_id_pattern is not a valid regex: {e}") from e
        return v


class ScenariosIndex(BaseModel):
    model_config = _STRICT
    schema_version: int
    # Required (no default): a missing `scenarios` key is a malformed index, so it must
    # surface as a located "Field required" error — not silently default to [] and then
    # mis-report every on-disk folder as drift. An explicit empty list is still allowed
    # (caught downstream by the "no scenario folders" / drift checks).
    scenarios: list[str]


class ScenarioMeta(BaseModel):
    """``scenario.yaml`` (spec §5.4). Shape + types only; ``tags`` axis/value membership is
    checked against the manifest's declared taxonomies in the validator."""

    model_config = _STRICT
    id: str = Field(min_length=1)
    tags: dict[str, list[str]] = Field(min_length=1)
    source_locus: int
    locus_label: str = Field(min_length=1)
    identity_signal: Literal["clean", "leaky", "intrinsic"]
