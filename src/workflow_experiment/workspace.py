"""Ordinary file access confined to one isolated experiment workspace."""

from __future__ import annotations

from pathlib import Path

from .provenance import ArtifactDigest


class WorkspaceFiles:
    def __init__(self, root: Path):
        self.root = root.resolve()
        if not self.root.is_dir():
            raise ValueError("workspace root must be an existing directory")

    def resolve(self, file_path: str | Path) -> Path:
        raw = Path(file_path)
        candidate = raw.resolve() if raw.is_absolute() else (self.root / raw).resolve()
        if not candidate.is_relative_to(self.root):
            raise ValueError("path must remain inside the current workspace")
        return candidate

    def read_text(self, file_path: str | Path, *, encoding: str = "utf-8") -> str:
        return self.resolve(file_path).read_text(encoding=encoding, errors="replace")

    def write_text(
        self,
        file_path: str | Path,
        content: str,
        *,
        encoding: str = "utf-8",
    ) -> ArtifactDigest:
        path = self.resolve(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        encoded = content.encode(encoding)
        path.write_bytes(encoded)
        return ArtifactDigest.from_bytes(path.relative_to(self.root).as_posix(), encoded)
