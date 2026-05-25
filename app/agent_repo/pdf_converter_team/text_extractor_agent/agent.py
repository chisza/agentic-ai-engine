"""Text extractor agent – extracts text and code from PDF pages."""

from google.adk.agents import LlmAgent

from app import config
from app.agent_repo.pdf_converter_team.text_extractor_agent.prompt import TEXT_EXTRACTOR_INSTRUCTION

text_extractor_agent = LlmAgent(
    name="text_extractor_agent",
    model=config.DEFAULT_LLM_MODEL,
    description=(
        "Extracts clean structured text from PDF page content, preserving headings, lists, "
        "tables, and code snippets. Marks diagram and image locations as HTML comments."
    ),
    instruction=TEXT_EXTRACTOR_INSTRUCTION,
)
