"""Typed candidate surfaces and deterministic pre-selection filters."""

from __future__ import annotations

import json
from math import ceil
from pathlib import Path
from typing import Any


def _normalize(value: str) -> str:
    return " ".join(value.casefold().split())


def _room_type_allowed(actual: str, required: str) -> bool:
    required = _normalize(required)
    actual = _normalize(actual)
    if not required:
        return True
    if required == "not shared room":
        return actual != "shared room"
    if required == "entire room":
        return actual == "entire home/apt"
    return actual == required


def _house_rule_allowed(actual: str, required: str) -> bool:
    required = _normalize(required)
    if not required:
        return True
    forbidden = {
        "smoking": "no smoking",
        "parties": "no parties",
        "children under 10": "no children under 10",
        "visitors": "no visitors",
        "pets": "no pets",
    }.get(required)
    return forbidden is None or forbidden not in _normalize(actual)


class TypedTravelPlannerTools:
    """Expose official candidates as compact JSON with stable field names."""

    def __init__(
        self,
        structured_reference_path: Path,
        *,
        session_id: str = "",
        workflow_step_only: bool = False,
    ):
        value = json.loads(structured_reference_path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("structured TravelPlanner reference must be an object")
        self.reference = value
        self.session_id = session_id.strip()
        self.workflow_step_only = workflow_step_only

    def _require_workflow_step(self) -> None:
        if self.workflow_step_only and self.session_id:
            raise PermissionError(
                "TravelPlanner data tools are restricted to Agent Steps inside run_flow; "
                "the outer session may only author and invoke the Workflow."
            )

    def _source_rows(self, description: str) -> list[dict[str, Any]]:
        value = self.reference.get(description, [])
        if not isinstance(value, list):
            raise ValueError(f"typed reference {description!r} must be an array")
        return [item for item in value if isinstance(item, dict)]

    @staticmethod
    def _result(kind: str, source: str, candidates: list[dict[str, Any]], **extra: Any) -> str:
        return json.dumps(
            {
                "schema_version": 1,
                "kind": kind,
                "source": source,
                "candidate_count": len(candidates),
                "candidates": candidates,
                **extra,
            },
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        )

    async def search_flights(self, origin: str, destination: str, departure_date: str) -> str:
        self._require_workflow_step()
        source = f"Flight from {origin} to {destination} on {departure_date}"
        rows = [
            {
                "flight_number": item.get("Flight Number"),
                "price": item.get("Price"),
                "departure_time": item.get("DepTime"),
                "arrival_time": item.get("ArrTime"),
                "date": item.get("FlightDate"),
                "origin": item.get("OriginCityName"),
                "destination": item.get("DestCityName"),
                "distance": item.get("Distance"),
            }
            for item in self._source_rows(source)
        ]
        return self._result("flight", source, rows)

    async def search_accommodations(
        self,
        city: str,
        required_nights: int = 0,
        travelers: int = 0,
        required_room_type: str = "",
        required_house_rule: str = "",
    ) -> str:
        self._require_workflow_step()
        source = f"Accommodations in {city}"
        source_rows = self._source_rows(source)
        kept: list[dict[str, Any]] = []
        rejected = {"minimum_nights": 0, "room_type": 0, "house_rule": 0, "invalid_occupancy": 0}
        for item in source_rows:
            row = {
                "name": item.get("NAME"),
                "city": item.get("city"),
                "price": item.get("price"),
                "room_type": item.get("room type"),
                "house_rules": item.get("house_rules"),
                "minimum_nights": item.get("minimum nights"),
                "maximum_occupancy": item.get("maximum occupancy"),
                "review_rate": item.get("review rate number"),
            }
            minimum_nights = float(row["minimum_nights"] or 0)
            occupancy = int(row["maximum_occupancy"] or 0)
            if required_nights and minimum_nights > required_nights:
                rejected["minimum_nights"] += 1
                continue
            if not _room_type_allowed(str(row["room_type"] or ""), required_room_type):
                rejected["room_type"] += 1
                continue
            if not _house_rule_allowed(str(row["house_rules"] or ""), required_house_rule):
                rejected["house_rule"] += 1
                continue
            if occupancy < 1:
                rejected["invalid_occupancy"] += 1
                continue
            row["rooms_required"] = ceil(max(1, travelers) / occupancy) if travelers else 1
            kept.append(row)
        return self._result(
            "accommodation",
            source,
            kept,
            filter={
                "required_nights": required_nights,
                "travelers": travelers,
                "required_room_type": required_room_type or None,
                "required_house_rule": required_house_rule or None,
                "source_candidate_count": len(source_rows),
                "rejected_counts": rejected,
            },
        )

    async def search_restaurants(self, city: str) -> str:
        self._require_workflow_step()
        source = f"Restaurants in {city}"
        rows = [
            {
                "name": item.get("Name"),
                "city": item.get("City"),
                "average_cost": item.get("Average Cost"),
                "cuisines": item.get("Cuisines"),
                "aggregate_rating": item.get("Aggregate Rating"),
            }
            for item in self._source_rows(source)
        ]
        return self._result("restaurant", source, rows)

    async def search_attractions(self, city: str) -> str:
        self._require_workflow_step()
        source = f"Attractions in {city}"
        rows = [
            {
                "name": item.get("Name"),
                "city": item.get("City"),
                "address": item.get("Address"),
                "latitude": item.get("Latitude"),
                "longitude": item.get("Longitude"),
            }
            for item in self._source_rows(source)
        ]
        return self._result("attraction", source, rows)
