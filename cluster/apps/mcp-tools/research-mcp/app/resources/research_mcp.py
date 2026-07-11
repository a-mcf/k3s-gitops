"""deep_research MCP server, backed by the in-cluster Vane (Perplexica).

The heavyweight peer to search-mcp's web_search: Vane runs the multi-step
search + rerank + synthesis pipeline and returns a cited answer, which the
calling LLM reframes in its own voice. Served over SSE for Home Assistant's
`mcp` client integration.

Model selection is discovered from Vane's /api/providers at call time (the
config is UI-managed there); env vars can pin a specific provider/model.
"""

import os

import httpx
from mcp.server.fastmcp import FastMCP

VANE_URL = os.environ.get("VANE_URL", "http://vane.vane.svc.cluster.local:3000")
CHAT_PROVIDER_NAME = os.environ.get("VANE_CHAT_PROVIDER_NAME")
EMBED_PROVIDER_NAME = os.environ.get("VANE_EMBED_PROVIDER_NAME")

mcp = FastMCP("research", host="0.0.0.0", port=8000)


async def _pick_models(client: httpx.AsyncClient) -> tuple[dict, dict]:
    """Pick chat + embedding models from Vane's provider registry."""
    resp = await client.get(f"{VANE_URL}/api/providers")
    resp.raise_for_status()
    providers = resp.json()["providers"]

    chat = embed = None
    for p in providers:
        if p["chatModels"] and (chat is None or p["name"] == CHAT_PROVIDER_NAME):
            chat = {"providerId": p["id"], "key": p["chatModels"][0]["key"]}
        if p["embeddingModels"] and (embed is None or p["name"] == EMBED_PROVIDER_NAME):
            embed = {
                "providerId": p["id"],
                "key": p["embeddingModels"][0]["key"],
            }
    if not chat or not embed:
        raise RuntimeError("no usable chat/embedding model found in Vane")
    return chat, embed


@mcp.tool()
async def deep_research(query: str, quality: str = "balanced") -> str:
    """Research a question in depth and return a cited answer.

    Slower but much more thorough than web_search: a research pipeline
    searches multiple sources, reads them, and synthesizes an answer with
    numbered citations. Use it for questions that need current, multi-source
    or nuanced answers; use web_search for quick fact lookups. Takes a
    minute or two. quality is one of: speed, balanced, quality.
    """
    if quality not in ("speed", "balanced", "quality"):
        quality = "balanced"
    async with httpx.AsyncClient(timeout=240) as client:
        chat, embed = await _pick_models(client)
        resp = await client.post(
            f"{VANE_URL}/api/search",
            json={
                "query": query,
                "sources": ["web"],
                "chatModel": chat,
                "embeddingModel": embed,
                "optimizationMode": quality,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    lines = [data.get("message", "").strip(), "", "Sources:"]
    for i, source in enumerate(data.get("sources", []), start=1):
        meta = source.get("metadata", {})
        title = (meta.get("title") or "untitled").strip()
        lines.append(f"[{i}] {title} — {meta.get('url', '')}")
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run(transport="sse")
