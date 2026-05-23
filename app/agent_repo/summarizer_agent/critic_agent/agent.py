"""Critic agent – scores a summary on completeness, conciseness, accuracy, and clarity."""

from google.adk.agents import LlmAgent

from app import config
from app.agent_repo.summarizer_agent.critic_agent.prompt import CRITIC_AGENT_INSTRUCTION

critic_agent = LlmAgent(
    name="critic_agent",
    model=config.DEFAULT_LLM_MODEL,
    description=(
        "Evaluates a summary against the original content and returns a structured score "
        "across completeness, conciseness, accuracy, and clarity (each out of 10)."
    ),
    instruction=CRITIC_AGENT_INSTRUCTION,
)