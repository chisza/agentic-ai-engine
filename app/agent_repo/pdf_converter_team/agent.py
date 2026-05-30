"""PDF converter coordinator – hierarchical agent team for PDF-to-Markdown conversion."""

from google.adk.agents import LlmAgent

from app import config
from app.agent_repo.pdf_converter_team.image_agent import image_agent
from app.agent_repo.pdf_converter_team.mermaid_agent import mermaid_agent
from app.agent_repo.pdf_converter_team.prompt import COORDINATOR_INSTRUCTION
from app.agent_repo.pdf_converter_team.rag_tool import add_to_knowledge_base, lookup_definitions
from app.agent_repo.pdf_converter_team.text_extractor_agent import text_extractor_agent

pdf_converter_coordinator = LlmAgent(
    name="pdf_converter_coordinator",
    model=config.DEFAULT_LLM_MODEL,
    description=(
        "Converts a PDF containing text, code snippets, images, and diagrams into a clean "
        "Markdown file. Images become described figure blocks; diagrams become Mermaid code blocks."
    ),
    instruction=COORDINATOR_INSTRUCTION,
    tools=[lookup_definitions, add_to_knowledge_base],
    sub_agents=[text_extractor_agent, image_agent, mermaid_agent],
    output_key="pdf_converter_output",
)
