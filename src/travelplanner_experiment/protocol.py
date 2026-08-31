"""Byte-stable common task contract for the registered experiment."""

from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass(frozen=True)
class Case:
    case_id: int
    query: str

    def __post_init__(self) -> None:
        if type(self.case_id) is not int or self.case_id < 1:
            raise ValueError("case_id must be a positive integer")
        if not isinstance(self.query, str) or not self.query:
            raise ValueError("query must be a non-empty string")


COMMON_TASK_TEMPLATE = """You are a travel planning assistant. Use the available TravelPlanner tools to build a complete trip plan for the user query below.

User query:
{query}

Requirements:
1. Search flights, accommodations, restaurants, and attractions as needed.
2. Respect the budget, number of travelers, dates, and any local constraints in the query.
3. Return ONLY a JSON object inside a markdown code block. The JSON must have this exact shape:

```json
{{
  "idx": {idx},
  "query": {query_json},
  "plan": [
    {{
      "day": 1,
      "current_city": "from Origin to Destination",
      "transportation": "Flight Number: F1234567, from Origin to Destination, Departure Time: 09:00, Arrival Time: 11:00",
      "breakfast": "-",
      "attraction": "Attraction Name, City;Another Attraction, City;",
      "lunch": "Restaurant Name, City",
      "dinner": "Restaurant Name, City",
      "accommodation": "Accommodation Name, City"
    }},
    ...
  ]
}}
```

Field rules:
- `day`: 1-indexed integer.
- `current_city`: on the first day use "from <origin> to <destination>"; on the last day use "from <current city> to <origin/home>"; otherwise the city name.
- `transportation`: use the exact flight/self-driving/taxi format returned by the tools, or "-" if no travel that day.
- `breakfast`, `lunch`, `dinner`: "<Name>, <City>" or "-".
- `attraction`: semicolon-separated "<Name>, <City>;" entries, or "-".
- `accommodation`: "<Name>, <City>" or "-".

Do not include any explanation outside the JSON code block.
"""


def render_prompt(case: Case) -> str:
    """Render the common contract while preserving the query's exact characters."""

    return COMMON_TASK_TEMPLATE.format(
        idx=json.dumps(case.case_id),
        query=case.query,
        query_json=json.dumps(case.query),
    )
