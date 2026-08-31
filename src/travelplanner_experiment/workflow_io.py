"""Workspace-confined read/write helpers for isolated Workflow authoring."""

from __future__ import annotations

from pathlib import Path


class WorkspaceIO:
    def __init__(self, workspace: Path):
        self.workspace = workspace.resolve()

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
        content = path.read_text(encoding="utf-8", errors="replace")
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
