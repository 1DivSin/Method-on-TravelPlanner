"""Apply the reviewed Workflow planning guidance to an isolated skill copy."""

from __future__ import annotations

from importlib.resources import files


MARKER = "## Planning Contract"


def guidance_text() -> str:
    return files("travelplanner_experiment").joinpath("workflow_skill_guidance.md").read_text(encoding="utf-8")


def apply_workflow_skill_guidance(skill_text: str) -> str:
    """Insert the guidance once while retaining frontmatter and existing text."""

    if MARKER in skill_text:
        return skill_text
    heading = "# Workflow"
    position = skill_text.find(heading)
    if position < 0:
        raise ValueError("Workflow skill is missing its '# Workflow' heading")
    next_section = skill_text.find("\n## ", position + len(heading))
    insertion = len(skill_text) if next_section < 0 else next_section
    return skill_text[:insertion].rstrip() + "\n\n" + guidance_text().strip() + "\n\n" + skill_text[insertion:].lstrip()
