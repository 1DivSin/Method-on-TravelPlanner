"""Workspace-confined read/write helpers for isolated Workflow authoring."""

from __future__ import annotations

from pathlib import Path


class WorkspaceIO:
    def __init__(self, workspace: Path, *, read_once_references: bool = False):
        self.workspace = workspace.resolve()
        self.read_once_references = read_once_references
        self._reference_reads: set[str] = set()

    @staticmethod
    def _reference_key(path: Path) -> str | None:
        lowered = tuple(part.casefold() for part in path.parts)
        for skill_name in ("workflow", "workflow-skill"):
            if lowered[-3:] == ("skills", skill_name, "skill.md"):
                return "workflow-skill"
            if lowered[-4:] == ("skills", skill_name, "grammar", "fusionflow.g4"):
                return "workflow-grammar"
        return None

    def _path(self, file_path: str) -> Path:
        raw = Path(file_path.strip())
        candidate = raw.resolve() if raw.is_absolute() else (self.workspace / raw).resolve()
        if not candidate.is_relative_to(self.workspace):
            raise ValueError("file path must stay inside the current TravelPlanner workspace")
        return candidate

    async def read(self, file_path: str, offset: int = 0, limit: int = 0) -> str:
        path = self._path(file_path)
        if not path.is_file():
            return f"[Error] File not found: {path}"
        reference_key = self._reference_key(path)
        if self.read_once_references and reference_key is not None:
            if reference_key in self._reference_reads:
                return (
                    f"[Already loaded] {reference_key} may be read only once in this "
                    "TravelPlanner attempt. Reuse the content already present in the conversation."
                )
            self._reference_reads.add(reference_key)
        content = path.read_text(encoding="utf-8", errors="replace")
        if self.read_once_references and reference_key is not None:
            # Static references are returned atomically even if the caller asks
            # for a partial range, avoiding another model round for pagination.
            return content
        if offset == 0 and limit == 0:
            return content
        lines = content.splitlines(keepends=True)
        selected = lines[offset:] if limit == 0 else lines[offset : offset + limit]
        return "".join(selected)

    async def write(self, file_path: str, content: str) -> str:
        path = self._path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return f"[OK] Written {len(content.encode('utf-8'))} bytes to {path}"
