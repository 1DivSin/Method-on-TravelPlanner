"""Pinned psi-agent revisions for registered TravelPlanner treatments."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeRevision:
    commit: str
    patch: str | None = None
    patch_sha256: str | None = None


V6_BASE_RUNTIME = RuntimeRevision(
    commit="54f55089b036badd1c56c57fff68190bbc34086d",
)

V6_PROTOCOL_DEDUP_RUNTIME = RuntimeRevision(
    commit="ff4f605a65092f90fc7e49f2b726e6d81d2d5e9b",
    patch="patches/psi-agent/0002-perf-workflow-deduplicate-Agent-step-output-protocol.patch",
    patch_sha256="2bc4bc4934af7cb0faa484a024cd4a80054c35e372d47b3a86490508046ecaed",
)


def runtime_revision(variant: str) -> RuntimeRevision:
    """Return the registered runtime; only stack layer four changes it."""

    if variant.casefold() == "v6-min-04-step-protocol-dedup":
        return V6_PROTOCOL_DEDUP_RUNTIME
    return V6_BASE_RUNTIME
