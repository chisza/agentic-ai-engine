"""Custom memory tools for the Vertex AI Memory Bank."""

from __future__ import annotations

from datetime import datetime, timezone

import structlog
from google.adk.memory.memory_entry import MemoryEntry
from google.adk.tools.tool_context import ToolContext
from google.genai.types import Content, Part

logger = structlog.get_logger(__name__)


async def memorize_session(tool_context: ToolContext) -> dict:
    """Save the current conversation to the memory bank for future recall.

    Call this when the user asks to save or remember the conversation,
    or at the end of an important interaction. Key points will be available
    in future sessions via the preloaded memory context.
    """
    try:
        await tool_context.add_session_to_memory()
        logger.info("Session saved to memory bank", user_id=tool_context.user_id)
        return {
            "status": "success",
            "message": "Conversation saved to memory. Key points will be available in future sessions.",
        }
    except ValueError as e:
        logger.warning("Memory service not available", error=str(e))
        return {"status": "error", "message": "Memory service is not configured."}
    except Exception as e:
        logger.error("Failed to save session to memory", error=str(e))
        return {"status": "error", "message": str(e)}


_MAX_FACT_CHARS = 2000  # Vertex AI Memory Bank hard limit is 2048; stay safely under


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


async def save_summary_to_memory(
    topic: str,
    summary: str,
    critic_score: str,
    tool_context: ToolContext,
) -> dict:
    """Save a summary and its critic score to the memory bank as structured entries.

    Saves two separate entries (summary + critic score) to stay within the
    Memory Bank's 2048-character-per-entry limit.

    Call this after completing a summarization and receiving the critic score.
    The entries will be retrievable in future sessions when the user asks about
    the same topic or requests a similar summarization.

    Args:
        topic: A short description of the topic or source that was summarized.
        summary: The full summary text produced by this agent.
        critic_score: The full critic score and feedback as returned by critic_agent.
    """
    ts = datetime.now(timezone.utc).isoformat()

    # Reserve space for the fixed prefix so the total stays under the limit.
    summary_prefix = f"Topic: {topic}\n\nSummary:\n"
    critic_prefix = f"Topic: {topic} — Critic Score:\n"

    summary_body = _truncate(summary, _MAX_FACT_CHARS - len(summary_prefix))
    critic_body = _truncate(critic_score, _MAX_FACT_CHARS - len(critic_prefix))

    entries = [
        MemoryEntry(
            content=Content(parts=[Part(text=summary_prefix + summary_body)], role="model"),
            author="summarizer_agent",
            timestamp=ts,
            custom_metadata={"type": "summary", "topic": topic},
        ),
        MemoryEntry(
            content=Content(parts=[Part(text=critic_prefix + critic_body)], role="model"),
            author="summarizer_agent",
            timestamp=ts,
            custom_metadata={"type": "critic_score", "topic": topic},
        ),
    ]
    try:
        await tool_context.add_memory(memories=entries)
        logger.info("Summary saved to memory bank", topic=topic, user_id=tool_context.user_id)
        return {
            "status": "success",
            "message": f"Summary and critic score for '{topic}' saved to memory.",
        }
    except (ValueError, NotImplementedError) as e:
        # InMemoryMemoryService (used by adk eval) raises NotImplementedError
        # for direct add_memory() calls. Degrade gracefully so eval runs complete.
        logger.warning("Memory write skipped — service does not support direct writes", error=str(e))
        return {"status": "skipped", "message": "Memory write not supported in this environment."}
    except Exception as e:
        logger.error("Failed to save summary to memory", topic=topic, error=str(e))
        return {"status": "error", "message": str(e)}
