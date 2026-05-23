"""OCR and visual analysis agent – extracts text and identifies diagrams from PDF pages."""

from google.adk.agents import LlmAgent

from app import config
from app.agent_repo.stack_planner_team.ocr_vision_agent.prompt import OCR_VISION_AGENT_INSTRUCTION

ocr_vision_agent = LlmAgent(
    name="ocr_vision_agent",
    model=config.DEFAULT_LLM_MODEL,
    description=(
        "Receives page content from a PDF and returns: "
        "(1) clean extracted text in reading order, "
        "(2) a structured description of any diagrams found."
    ),
    instruction=OCR_VISION_AGENT_INSTRUCTION,
)