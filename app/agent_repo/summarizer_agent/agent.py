"""Summarizer agent – summarizes text and scores the result via a remote critic A2A agent."""

from google.adk.agents import LlmAgent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.tools import AgentTool, preload_memory
from google.adk.tools.google_search_agent_tool import GoogleSearchAgentTool, create_google_search_agent
from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset

from app import config
from app.agent_repo.summarizer_agent.artifact_tools import (
    list_artifact_store_contents,
    load_summary_from_artifact_store,
    save_summary_as_artifact,
    save_summary_to_artifact_store,
)
from app.agent_repo.summarizer_agent.prompt import summarizer_agent_INSTRUCTION
from app.context.memory.memory_tools import memorize_session, save_summary_to_memory

_critic_remote_agent = RemoteA2aAgent(
    name="critic_agent",
    agent_card=config.CRITIC_A2A_URL,
    description=(
        "Evaluates a summary against the original content and returns a structured score "
        "across completeness, conciseness, accuracy, and clarity (each out of 10)."
    ),
)

_mcp_url = config.MCP_FETCH_URL or "http://localhost:8001/sse"

_tools = [
    preload_memory,
    memorize_session,
    save_summary_to_memory,
    save_summary_as_artifact,
    save_summary_to_artifact_store,
    load_summary_from_artifact_store,
    list_artifact_store_contents,
    GoogleSearchAgentTool(agent=create_google_search_agent(config.DEFAULT_LLM_MODEL)),
    McpToolset(
        connection_params=SseConnectionParams(url=_mcp_url),
        tool_filter=["fetch"],
    ),
    AgentTool(agent=_critic_remote_agent),
]

summarizer_agent = LlmAgent(
    name="summarizer_agent",
    model=config.DEFAULT_LLM_MODEL,
    description="Agent that summarizes text provided by the user.",
    instruction=summarizer_agent_INSTRUCTION,
    tools=_tools,
    output_key="summarizer_agent_output",
)