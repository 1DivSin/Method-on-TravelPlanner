"""Deterministic quality gate for an assembled TravelPlanner itinerary."""

from __future__ import annotations

import json
from math import ceil
from pathlib import Path
from typing import Any


DAY_KEYS = {"day", "current_city", "transportation", "breakfast", "attraction", "lunch", "dinner", "accommodation"}


def _norm(value: str) -> str:
    return " ".join(value.casefold().split())


def _name_city(value: object) -> tuple[str, str] | None:
    if not isinstance(value, str) or value in {"", "-"} or "," not in value:
        return None
    name, city = value.rsplit(",", 1)
    return (_norm(name), _norm(city)) if name.strip() and city.strip() else None


class TravelPlanValidator:
    def __init__(self, structured_reference_path: Path, constraints_path: Path):
        self.reference = json.loads(structured_reference_path.read_text(encoding="utf-8"))
        self.constraints = json.loads(constraints_path.read_text(encoding="utf-8"))
        if not isinstance(self.reference, dict) or not isinstance(self.constraints, dict):
            raise ValueError("reference and constraints must be JSON objects")

    def _indexes(self) -> dict[str, Any]:
        restaurants: dict[tuple[str, str], dict[str, Any]] = {}
        accommodations: dict[tuple[str, str], dict[str, Any]] = {}
        flights: dict[str, dict[str, Any]] = {}
        for description, rows in self.reference.items():
            if not isinstance(rows, list):
                continue
            if description.startswith("Restaurants in "):
                for row in rows:
                    restaurants[(_norm(str(row.get("Name", ""))), _norm(str(row.get("City", ""))))] = row
            elif description.startswith("Accommodations in "):
                for row in rows:
                    accommodations[(_norm(str(row.get("NAME", ""))), _norm(str(row.get("city", ""))))] = row
            elif description.startswith("Flight from "):
                for row in rows:
                    flights[_norm(str(row.get("Flight Number", "")))] = row
        return {"restaurants": restaurants, "accommodations": accommodations, "flights": flights}

    def validate(self, plan_json: str) -> str:
        violations: list[dict[str, Any]] = []

        def fail(constraint: str, message: str, *, day: int | None = None, field: str | None = None) -> None:
            item: dict[str, Any] = {"constraint": constraint, "message": message}
            if day is not None:
                item["day"] = day
            if field is not None:
                item["field"] = field
            violations.append(item)

        try:
            document = json.loads(plan_json)
        except json.JSONDecodeError as error:
            document = {}
            fail("schema.json", f"invalid JSON: {error.msg}")
        itinerary = document.get("plan") if isinstance(document, dict) else None
        if not isinstance(itinerary, list):
            itinerary = []
            fail("schema.plan", "plan must be an array")
        expected_days = int(self.constraints.get("days") or 0)
        if len(itinerary) != expected_days:
            fail("schema.day_count", f"expected {expected_days} days, received {len(itinerary)}")

        indexes = self._indexes()
        travelers = int(self.constraints.get("people_number") or 1)
        budget = float(self.constraints.get("budget") or 0)
        seen_restaurants: set[tuple[str, str]] = set()
        accommodation_runs: list[tuple[tuple[str, str], int, dict[str, Any]]] = []
        total_cost = 0.0

        for position, day in enumerate(itinerary, 1):
            if not isinstance(day, dict):
                fail("schema.day", "day must be an object", day=position)
                continue
            missing = sorted(DAY_KEYS - day.keys())
            if missing:
                fail("schema.required_fields", f"missing fields: {missing}", day=position)
            if day.get("day") != position:
                fail("schema.day_number", f"day must equal {position}", day=position)
            for field in ("breakfast", "lunch", "dinner"):
                value = day.get(field)
                key = _name_city(value)
                if key is None:
                    continue
                candidate = indexes["restaurants"].get(key)
                if candidate is None:
                    fail("membership.restaurant", f"{value!r} is not a candidate", day=position, field=field)
                    continue
                if key in seen_restaurants:
                    fail("diversity.restaurant", f"{value!r} is repeated", day=position, field=field)
                seen_restaurants.add(key)
                total_cost += float(candidate.get("Average Cost") or 0) * travelers

            accommodation = _name_city(day.get("accommodation"))
            if accommodation is not None:
                row = indexes["accommodations"].get(accommodation)
                if row is None:
                    fail("membership.accommodation", f"{day.get('accommodation')!r} is not a candidate", day=position)
                else:
                    occupancy = int(row.get("maximum occupancy") or 0)
                    if occupancy < 1:
                        fail("accommodation.occupancy", "maximum occupancy must be positive", day=position)
                    else:
                        total_cost += float(row.get("price") or 0) * ceil(travelers / occupancy)
                    accommodation_runs.append((accommodation, position, row))

            transportation = str(day.get("transportation") or "")
            if transportation.startswith("Flight Number:"):
                number = _norm(transportation.split(",", 1)[0].split(":", 1)[1])
                flight = indexes["flights"].get(number)
                if flight is None:
                    fail("membership.flight", "flight is not a candidate", day=position)
                else:
                    total_cost += float(flight.get("Price") or 0) * travelers

        start = 0
        while start < len(accommodation_runs):
            key, first_day, row = accommodation_runs[start]
            end = start + 1
            while end < len(accommodation_runs) and accommodation_runs[end][0] == key and accommodation_runs[end][1] == accommodation_runs[end - 1][1] + 1:
                end += 1
            used = end - start
            minimum = int(float(row.get("minimum nights") or 0))
            if used < minimum:
                fail("accommodation.minimum_nights", f"requires {minimum} nights but is used for {used}", day=first_day)
            start = end

        if budget and total_cost > budget:
            fail("hard.budget", f"estimated cost {total_cost:.2f} exceeds budget {budget:.2f}")
        return json.dumps(
            {
                "schema_version": 1,
                "valid": not violations,
                "violation_count": len(violations),
                "violations": violations,
                "computed": {"estimated_total_cost": round(total_cost, 2), "budget": budget},
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
