"""Byte-level provenance records for external inputs and run configuration."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


@dataclass(frozen=True)
class ArtifactDigest:
    """Logical identity, byte count, and digest of one frozen input."""

    name: str
    size_bytes: int
    sha256: str

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("artifact name must not be empty")
        if type(self.size_bytes) is not int or self.size_bytes < 0:
            raise ValueError("artifact size_bytes must be a non-negative integer")
        valid = len(self.sha256) == 64 and all(
            character in "0123456789abcdef" for character in self.sha256
        )
        if not valid:
            raise ValueError("artifact sha256 must be a lowercase SHA-256 digest")

    @classmethod
    def from_bytes(cls, name: str, content: bytes) -> ArtifactDigest:
        return cls(name=name, size_bytes=len(content), sha256=sha256_bytes(content))

    @classmethod
    def from_file(cls, name: str, path: Path) -> ArtifactDigest:
        return cls.from_bytes(name, path.read_bytes())

    def as_dict(self) -> dict[str, str | int]:
        return {"name": self.name, "size_bytes": self.size_bytes, "sha256": self.sha256}


def create_manifest(
    *,
    configuration: Mapping[str, Any],
    artifacts: Iterable[ArtifactDigest],
) -> bytes:
    """Return a deterministic manifest suitable for storage and hashing."""

    artifact_list = tuple(artifacts)
    names = [artifact.name for artifact in artifact_list]
    if len(set(names)) != len(names):
        raise ValueError("artifact names must be unique")
    payload = {
        "schema_version": 1,
        "configuration": configuration,
        "artifacts": [
            artifact.as_dict()
            for artifact in sorted(artifact_list, key=lambda item: item.name)
        ],
    }
    return (
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")
