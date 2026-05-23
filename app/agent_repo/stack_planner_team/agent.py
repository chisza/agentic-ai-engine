"""PDF-to-Markdown coordinator agent.
Hierarchical pipeline:
  pdf_to_markdown_coordinator
    ├── ocr_vision_agent   (extracts text, identifies diagrams)
    └── mermaid_agent      (converts diagram descriptions to Mermaid syntax)
"""

from google.adk.agents import LlmAgent
from google.adk.tools import AgentTool

from app import config
from app.agent_repo.stack_planner_team.mermaid_agent import mermaid_agent
from app.agent_repo.stack_planner_team.ocr_vision_agent import ocr_vision_agent
from app.agent_repo.stack_planner_team.prompt import COORDINATOR_INSTRUCTION
from app.agent_repo.stack_planner_team.tools import save_markdown

pdf_to_markdown_coordinator = LlmAgent(
    name="pdf_to_markdown_coordinator",
    model=config.DEFAULT_LLM_MODEL,
    description="Converts an uploaded PDF to a Markdown file with Mermaid diagrams.",
    instruction=COORDINATOR_INSTRUCTION,
    tools=[
        AgentTool(agent=ocr_vision_agent),
        AgentTool(agent=mermaid_agent),
        save_markdown,
    ],
    sub_agents = []
)