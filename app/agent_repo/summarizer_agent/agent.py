"""Summarizer agent – summarizes text and scores the result via a remote critic A2A agent."""

from google.adk.agents import LlmAgent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.tools import AgentTool
from google.adk.tools.google_search_agent_tool import GoogleSearchAgentTool, create_google_search_agent
from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset

from app import config
from app.agent_repo.summarizer_agent.prompt import summarizer_agent_INSTRUCTION

_critic_remote_agent = RemoteA2aAgent(
    name="critic_agent",
    agent_card="http://localhost:8002/.well-known/agent-card.json",
    description=(
        "Evaluates a summary against the original content and returns a structured score "
        "across completeness, conciseness, accuracy, and clarity (each out of 10)."
    ),
)

_tools = [
    GoogleSearchAgentTool(agent=create_google_search_agent(config.DEFAULT_LLM_MODEL)),
    McpToolset(
        connection_params=SseConnectionParams(url="http://localhost:8001/sse"),
        tool_filter=["fetch"],
    ),
    AgentTool(agent=_critic_remote_agent),
]

summarizer_agent = LlmAgent(
    name="summarizer_agent",
    model=config.DEFAULT_LLM_MODEL,
    description="Agent that summarizes text provided by the user.",
    instruction=summarizer_agent_INSTRUCTION,
    tools=_tools
)