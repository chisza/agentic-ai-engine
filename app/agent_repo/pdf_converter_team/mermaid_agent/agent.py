"""Mermaid agent – converts diagram descriptions to valid Mermaid syntax."""

from google.adk.agents import LlmAgent

from app import config
from app.agent_repo.pdf_converter_team.callbacks import save_markdown_after_conversion
from app.agent_repo.pdf_converter_team.mermaid_agent.prompt import MERMAID_AGENT_INSTRUCTION

mermaid_agent = LlmAgent(
    name="pdf_converter_mermaid_agent",
    model=config.DEFAULT_LLM_MODEL,
    description=(
        "Receives a plain-text description of a diagram and returns only a valid fenced "
        "Mermaid code block. Supports flowchart, sequenceDiagram, classDiagram, erDiagram, "
        "stateDiagram-v2, gantt, and pie."
    ),
    instruction=MERMAID_AGENT_INSTRUCTION,
    output_key="final_markdown",
    after_agent_callback=save_markdown_after_conversion,
)
