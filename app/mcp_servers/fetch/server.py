"""MCP fetch server — exposes a `fetch` tool that retrieves URL content."""

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("fetch", host="0.0.0.0", port=8001)


@mcp.tool()
async def fetch(url: str, max_length: int = 20000) -> str:
    """Fetch the content of a URL and return it as plain text.

    Args:
        url: The URL to fetch.
        max_length: Maximum number of characters to return (default 20000).
    """
    async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
        response = await client.get(url, headers={"User-Agent": "mcp-fetch/1.0"})
        response.raise_for_status()

    content_type = response.headers.get("content-type", "")
    if "html" in content_type:
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
        except ImportError:
            text = response.text
    else:
        text = response.text

    return text[:max_length]


if __name__ == "__main__":
    mcp.run(transport="sse")
