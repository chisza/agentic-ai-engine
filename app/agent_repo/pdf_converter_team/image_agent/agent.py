"""Image agent – converts image descriptions into Markdown image blocks."""

from google.adk.agents import LlmAgent

from app import config
from app.agent_repo.pdf_converter_team.image_agent.prompt import IMAGE_AGENT_INSTRUCTION

image_agent = LlmAgent(
    name="image_agent",
    model=config.DEFAULT_LLM_MODEL,
    description=(
        "Receives a description of an image from a PDF and returns a Markdown image block "
        "with a descriptive alt text and a figure caption."
    ),
    instruction=IMAGE_AGENT_INSTRUCTION,
)
