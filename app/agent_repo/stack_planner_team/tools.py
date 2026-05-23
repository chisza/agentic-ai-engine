"""Tools for the PDF-to-Markdown agent team."""

from pathlib import Path


def save_markdown(content: str, output_path: str) -> str:
    """Save the assembled Markdown content to a file.

    Args:
        content: The full Markdown text to save.
        output_path: Path where the .md file should be written (e.g. /tmp/output.md).
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return f"Saved {len(content)} characters to {output_path}"