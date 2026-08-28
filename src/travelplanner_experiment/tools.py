"""Focused, read-only TravelPlanner tools for one isolated benchmark case."""

from __future__ import annotations

import ast
import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any


def _normalize(value: str) -> str:
    return " ".join(value.casefold().split())


def _strip_parenthetical(value: str) -> str:
    return re.sub(r"\s*\([^)]*\)\s*$", "", value).strip()


@lru_cache(maxsize=512)
def _load_reference(path_text: str) -> tuple[dict[str, Any], ...]:
    text = Path(path_text).read_text(encoding="utf-8").strip()
    if not text:
        return ()
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        value = ast.literal_eval(text)
    if not isinstance(value, list):
        raise ValueError("TravelPlanner case reference must be a list")
    return tuple(row for row in value if isinstance(row, dict))


class TravelPlannerTools:
    """Query only the official reference row assigned to this case."""

    def __init__(self, reference_path: Path):
        self.reference_path = reference_path.resolve()

    def _content_for(self, description: str) -> str | None:
        target = _normalize(description)
        for row in _load_reference(str(self.reference_path)):
            if _normalize(str(row.get("Description", ""))) == target:
                return str(row.get("Content", ""))
        return None

    def _city_content(self, kind: str, city: str) -> str:
        city = _strip_parenthetical(city)
        content = self._content_for(f"{kind} in {city}")
        if content is None:
            return f"There is no {kind.casefold()} data for {city} in this case's official reference."
        return content

    async def search_flights(self, origin: str, destination: str, departure_date: str) -> str:
        origin = _strip_parenthetical(origin)
        destination = _strip_parenthetical(destination)
        description = f"Flight from {origin} to {destination} on {departure_date.strip()}"
        content = self._content_for(description)
        return content if content is not None else f"There is no flight from {origin} to {destination} on {departure_date.strip()}."

    async def search_accommodations(self, city: str) -> str:
        return self._city_content("Accommodations", city)

    async def search_restaurants(self, city: str) -> str:
        return self._city_content("Restaurants", city)

    async def search_attractions(self, city: str) -> str:
        return self._city_content("Attractions", city)

    async def compute_distance(self, origin: str, destination: str, mode: str = "self-driving") -> str:
        origin = _strip_parenthetical(origin)
        destination = _strip_parenthetical(destination)
        normalized = mode.strip().casefold()
        label = "Self-driving" if normalized in {"driving", "self driving", "self-driving"} else "Taxi" if normalized == "taxi" else ""
        if not label:
            return "[Error] mode must be self-driving or taxi"
        content = self._content_for(f"{label} from {origin} to {destination}")
        return content if content is not None else f"{label.casefold()}, from {origin} to {destination}, no valid information."
