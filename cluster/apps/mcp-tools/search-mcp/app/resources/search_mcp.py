"""web_search + read_page MCP server, backed by the in-cluster SearXNG.

Serves two tools over SSE (the transport Home Assistant's `mcp` client
integration speaks): `web_search` returns compact plain text — titles,
URLs, snippets — and `read_page` returns the readable text of one page,
for when the answer lives in the body rather than the snippet. Both hand
raw material to the calling LLM to synthesize from rather than a finished
answer: the persona doing the talking should be the one composing from
raw results.

Every tool must finish well inside Home Assistant's hard 10-second MCP
tool-call ceiling (TIMEOUT = 10 in its mcp component) — budget fetch
timeouts accordingly.
"""

import os

import anyio
import httpx
import trafilatura
from mcp.server.fastmcp import FastMCP

SEARXNG_URL = os.environ.get(
    "SEARXNG_URL", "http://searxng.searxng.svc.cluster.local:8080"
)
# outbound page fetches leave through the VPN egress proxy, like searxng's
# own engine traffic; side effect: cluster/LAN addresses are unreachable
# from there, so the tool cannot be steered at internal services
PROXY_URL = os.environ.get("PROXY_URL", "")

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


@mcp.tool()
async def read_page(url: str, max_chars: int = 6000) -> str:
    """Fetch one web page and return its readable text.

    Use this after web_search when the answer needs the page's actual
    content — instructions, recipe steps, documentation, article body —
    rather than the search snippet. Pass the URL of the most promising
    result. The page is reduced to plain text and may be truncated;
    mention the page you read when it matters.
    """
    if not url.lower().startswith(("http://", "https://")):
        return "Only http(s) URLs can be read."
    max_chars = max(500, min(int(max_chars), 20000))
    try:
        async with httpx.AsyncClient(
            # HA abandons tool calls at 10s; leave room to extract and reply
            timeout=7,
            proxy=PROXY_URL or None,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"},
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
    except httpx.HTTPStatusError as err:
        return f"The page returned HTTP {err.response.status_code}."
    except httpx.HTTPError as err:
        return f"Could not fetch the page ({err.__class__.__name__})."

    # extraction is CPU-bound; keep it off the event loop
    text = await anyio.to_thread.run_sync(
        lambda: trafilatura.extract(
            resp.text, include_comments=False, include_tables=True
        )
    )
    if not text:
        return "Could not extract readable text from that page."
    if len(text) > max_chars:
        text = text[:max_chars].rsplit(" ", 1)[0] + " …[truncated]"
    return f"Text of {url}:\n\n{text}"


if __name__ == "__main__":
    mcp.run(transport="sse")
