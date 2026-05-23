"""Critic A2A server.

Wraps the critic LlmAgent as a standalone A2A-compliant HTTP service.
The Agent Card is served at /.well-known/agent.json (and the new canonical
path /.well-known/agent-card.json).

Run with:
    uvicorn app.a2a_servers.critic.server:app --host 0.0.0.0 --port 8002
"""

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryPushNotificationConfigStore, InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from google.adk.a2a.executor.a2a_agent_executor import A2aAgentExecutor
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.auth.credential_service.in_memory_credential_service import InMemoryCredentialService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService

from app import config
from app.agent_repo.summarizer_agent.critic_agent.agent import critic_agent

_DESCRIPTION = (
    "Evaluates a summary against the original content and returns a structured score "
    "across completeness, conciseness, accuracy, and clarity (each out of 10)."
)

_agent_card = AgentCard(
    name="critic_agent",
    description=_DESCRIPTION,
    url=f"http://{config.CRITIC_A2A_HOST}:{config.CRITIC_A2A_PORT}/",
    capabilities=AgentCapabilities(streaming=False),
    default_input_modes=["text/plain"],
    default_output_modes=["text/plain"],
    skills=[
        AgentSkill(
            id="score_summary",
            name="Score Summary",
            description=_DESCRIPTION,
            tags=["scoring", "evaluation"],
        )
    ],
    version="1.0.0",
)


async def _create_runner() -> Runner:
    return Runner(
        app_name=critic_agent.name,
        agent=critic_agent,
        artifact_service=InMemoryArtifactService(),
        session_service=InMemorySessionService(),
        memory_service=InMemoryMemoryService(),
        credential_service=InMemoryCredentialService(),
    )


app = A2AStarletteApplication(
    agent_card=_agent_card,
    http_handler=DefaultRequestHandler(
        agent_executor=A2aAgentExecutor(runner=_create_runner),
        task_store=InMemoryTaskStore(),
        push_config_store=InMemoryPushNotificationConfigStore(),
    ),
).build()
