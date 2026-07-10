"""web_search MCP server, backed by the in-cluster SearXNG.

Serves a single `web_search` tool over SSE (the transport Home Assistant's
`mcp` client integration speaks). The tool returns compact plain text —
titles, URLs, snippets — for the calling LLM to synthesize from, rather
than a finished answer: the persona doing the talking should be the one
composing from raw results.
"""

import os

import httpx
from mcp.server.fastmcp import FastMCP

SEARXNG_URL = os.environ.get(
    "SEARXNG_URL", "http://searxng.searxng.svc.cluster.local:8080"
)

# FastMCP binds loopback by default, which is unreachable through a
# kubernetes Service
mcp = FastMCP("search", host="0.0.0.0", port=8000)


@mcp.tool()
async def web_search(query: str, max_results: int = 6) -> str:
    """Search the web and return the top results.

    Use this to look up current events, weather, prices, or any fact you
    are unsure about or that may have changed recently. Results are
    titles, URLs and text snippets from a metasearch engine — synthesize
    your answer from them and mention which source it came from when it
    matters.
    """
    max_results = max(1, min(int(max_results), 10))
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(
            f"{SEARXNG_URL}/search",
            params={"q": query, "format": "json"},
        )
        resp.raise_for_status()
        data = resp.json()

    lines = []

    # direct answers and infoboxes first: highest-density facts, and for a
    # voice assistant often all that is needed
    for answer in data.get("answers", []):
        text = answer.get("answer") if isinstance(answer, dict) else str(answer)
        if text:
            lines.append(f"Answer: {text}")
    for box in data.get("infoboxes", []):
        content = (box.get("content") or "").strip()
        if content:
            lines.append(f"{box.get('infobox', 'Info')}: {content}")

    for i, result in enumerate(data.get("results", [])[:max_results], start=1):
        lines.append(f"{i}. {result.get('title')} — {result.get('url')}")
        content = (result.get("content") or "").strip()
        if content:
            lines.append(f"   {content}")

    if not lines:
        return f"No results found for {query!r}. Try a different phrasing."
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run(transport="sse")
