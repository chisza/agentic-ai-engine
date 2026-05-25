"""Tools for the PDF converter coordinator."""

from datetime import datetime, timezone
from pathlib import Path

from google.adk.tools.tool_context import ToolContext


def save_markdown(content: str, output_path: str, tool_context: ToolContext) -> str:
    """Save the assembled Markdown document to a file.

    Args:
        content: The full Markdown text to write.
        output_path: Destination path (e.g. ``/tmp/document.md``).
        tool_context: Injected by ADK — persists save metadata in session state.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

    tool_context.state["last_saved_file"] = {
        "path": output_path,
        "size": len(content),
        "saved_at": datetime.now(timezone.utc).isoformat(),
    }

    return f"Saved {len(content)} characters to {output_path}"
