"""Frozen records for externally implemented tool surfaces."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .provenance import ArtifactDigest


@dataclass(frozen=True)
class ExternalToolSurface:
    """Provenance for one tool adapter; this class never changes tool behavior."""

    revision: str
    adapter: ArtifactDigest
    schema: ArtifactDigest
    visible_tools: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.revision:
            raise ValueError("tool adapter revision must not be empty")
        if not self.visible_tools:
            raise ValueError("at least one visible tool must be registered")
        if any(not name for name in self.visible_tools):
            raise ValueError("visible tool names must not be empty")
        if len(set(self.visible_tools)) != len(self.visible_tools):
            raise ValueError("visible tool names must be unique")

    def as_dict(self) -> dict[str, object]:
        return {
            "revision": self.revision,
            "adapter": self.adapter.as_dict(),
            "schema": self.schema.as_dict(),
            "visible_tools": list(self.visible_tools),
        }


def freeze_external_tool_surface(
    *,
    revision: str,
    adapter_path: Path,
    schema_path: Path,
    visible_tools: Iterable[str],
) -> ExternalToolSurface:
    """Hash an authoritative external adapter and its exported schema bytes."""

    return ExternalToolSurface(
        revision=revision,
        adapter=ArtifactDigest.from_file("tool-adapter", adapter_path),
        schema=ArtifactDigest.from_file("tool-schema", schema_path),
        visible_tools=tuple(visible_tools),
    )
