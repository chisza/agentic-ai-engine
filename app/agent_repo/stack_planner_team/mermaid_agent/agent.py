"""Mermaid agent – converts diagram descriptions to valid Mermaid syntax."""

from google.adk.agents import LlmAgent

from app import config
from app.agent_repo.stack_planner_team.mermaid_agent.prompt import MERMAID_AGENT_INSTRUCTION

mermaid_agent = LlmAgent(
    name="mermaid_agent",
    model=config.DEFAULT_LLM_MODEL,
    description=(
        "Receives a plain-text description of a diagram and returns only valid Mermaid syntax. "
        "Supports flowchart, sequenceDiagram, classDiagram, erDiagram, stateDiagram-v2, gantt, pie."
    ),
    instruction=MERMAID_AGENT_INSTRUCTION,
)