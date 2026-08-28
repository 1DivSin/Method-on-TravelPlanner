"""Versioned, byte-stable prompt contracts for TravelPlanner experiments."""

from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass(frozen=True)
class Case:
    case_id: str
    query: str


BASE_PROMPT_TEMPLATE = """You are a travel planning assistant. Use the available TravelPlanner tools to build a complete trip plan for the user query below.

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

WORKFLOW_V1 = "Please complete the task using workflow skill.\n\n"

WORKFLOW_V2 = """Please complete the task using workflow skill.

Workflow execution contract for this trial:
1. Author and run one concrete Workflow through run_flow before returning the answer.
2. Decompose the work into bounded Steps; parallelize only independent searches.
3. Each Step must return its declared structured Artifact without prose.
4. Return the final `{idx, query, plan}` Artifact unchanged.

"""

WORKFLOW_V3 = """Please complete the task using workflow skill.

Workflow execution contract for this validator trial:
1. Author and run one concrete Workflow through run_flow before returning the answer.
2. Preserve candidate fields required for membership, budget, route, and lodging checks.
3. Assemble, validate, repair only invalid fields when necessary, and validate again.
4. Return the final `{idx, query, plan}` Artifact unchanged.

"""

# Adapted from the Claude Code Dynamic Workflow carrier. The itinerary and
# output contracts stay the same; only the local Workflow entry point and Agent
# Step terminology are specific to Haitun/FusionFlow.
CC_DYNAMIC_WORKFLOW_PROMPT_TEMPLATE = """Please complete the task using workflow skill. Author and run one Workflow through run_flow to plan a complete TravelPlanner itinerary for the user query below.

User query:
{query}

Workflow design constraints (CRITICAL - follow exactly):
1. Keep the workflow SMALL and FAST. Use at most 3 phases and at most 5 Agent Steps (subagents) total.
2. Prefer SEQUENTIAL phases over deep nesting or excessive parallelism.
3. Each Agent Step (subagent) should make at most 5 tool calls. If a tool returns no results, try ONE alternative and then move on - do not loop or retry repeatedly.
4. The entire workflow must complete within 10 minutes. Bias toward producing a good-enough plan quickly rather than an optimal plan slowly.
5. Do not create Agent Steps (subagents) for tasks that can be done inline. Only parallelize independent searches (e.g. different cities).

Itinerary requirements:
1. Use the available TravelPlanner tools (flights, accommodations, restaurants, attractions, distance) as needed.
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

V5_TYPED_CANDIDATE_CONTRACT = """Accuracy treatment: candidate contracts and pre-filtering.
- Search Steps must return structured candidate arrays with canonical source fields, never raw tables or prose.
- Accommodation searches must pass required_nights, travelers, required_room_type, and required_house_rule so invalid lodging is filtered before selection.
- Selection and assembly may choose only members of the typed candidate Artifacts.

"""

V5_VALIDATION_CONTRACT = """Accuracy treatment: deterministic validation and targeted repair.
- After assembly, JSON-encode the complete `{idx, query, plan}` object and call `validate_travel_plan`.
- The validation_report Artifact must be exactly the structured tool result; an LLM prose review does not count.
- If validation fails, repair only reported fields using the original typed candidates, then validate once more.
- A failed second validation must return the required empty-plan object.

"""


def render_prompt(case: Case, *, arm: str, variant: str = "v1") -> str:
    """Render one registered treatment without reading host paths or secrets."""

    try:
        idx: int | str = int(case.case_id)
    except ValueError:
        idx = case.case_id
    common = BASE_PROMPT_TEMPLATE.format(
        idx=json.dumps(idx),
        query=case.query,
        query_json=json.dumps(case.query),
    )
    if arm == "no-workflow":
        return common
    if arm != "auto-workflow":
        raise ValueError(f"unknown arm: {arm}")
    if variant.casefold() == "v4":
        return CC_DYNAMIC_WORKFLOW_PROMPT_TEMPLATE.format(
            idx=json.dumps(idx),
            query=case.query,
            query_json=json.dumps(case.query),
        )
    if variant.casefold() == "v5-typed-candidates":
        return V5_TYPED_CANDIDATE_CONTRACT + CC_DYNAMIC_WORKFLOW_PROMPT_TEMPLATE.format(
            idx=json.dumps(idx), query=case.query, query_json=json.dumps(case.query)
        )
    if variant.casefold() == "v5-validated":
        return V5_TYPED_CANDIDATE_CONTRACT + V5_VALIDATION_CONTRACT + CC_DYNAMIC_WORKFLOW_PROMPT_TEMPLATE.format(
            idx=json.dumps(idx), query=case.query, query_json=json.dumps(case.query)
        )
    treatments = {"v1": WORKFLOW_V1, "v2": WORKFLOW_V2, "v3": WORKFLOW_V3}
    try:
        return treatments[variant.casefold()] + common
    except KeyError as error:
        raise ValueError(f"unknown prompt variant: {variant}") from error
