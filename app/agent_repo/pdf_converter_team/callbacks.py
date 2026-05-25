"""Callbacks for the PDF converter team."""

import structlog
from pathlib import Path

from google.adk.agents.callback_context import CallbackContext
from google.genai.types import Part

logger = structlog.get_logger(__name__)

_DEFAULT_OUTPUT_PATH = "/tmp/converted_output.md"
_ARTIFACT_FILENAME = "converted_output.md"


async def save_markdown_after_conversion(callback_context: CallbackContext) -> None:
    """Persist the final Markdown and expose it as a downloadable artifact.

    Fires automatically after ``pdf_converter_mermaid_agent`` finishes.
    Reads ``final_markdown`` from session state (written via ``output_key``),
    saves to disk, and uploads to the GCS artifact store so the UI can offer
    a download link.
    """
    content = callback_context.state.get("final_markdown")
    if not content:
        logger.warning("save_markdown_after_conversion: final_markdown not in state, skipping")
        return

    # Save to disk
    output_path = callback_context.state.get("output_path", _DEFAULT_OUTPUT_PATH)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    callback_context.state["last_saved_file"] = str(path)
    logger.info("Markdown saved to disk", path=str(path), size=len(content))

    # Save as GCS artifact so the UI can offer a download link
    artifact = Part(
        inline_data={"mime_type": "text/markdown", "data": content.encode("utf-8")}
    )
    version = await callback_context.save_artifact(
        filename=_ARTIFACT_FILENAME,
        artifact=artifact,
    )
    logger.info("Markdown saved as artifact", filename=_ARTIFACT_FILENAME, version=version)