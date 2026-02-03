#!/usr/bin/env python3
"""MCP server for OpenAlex Local - Claude integration.

This server exposes openalex-local functionality as MCP tools,
enabling Claude Desktop and other MCP clients to search academic papers.

Usage:
    openalex-local mcp start                    # stdio (Claude Desktop)
    openalex-local mcp start -t http --port 8083  # HTTP transport
"""

import json

from fastmcp import FastMCP

from .. import (
    get as _get,
    get_many as _get_many,
    info as _info,
    search as _search,
)

# Initialize MCP server
mcp = FastMCP(
    name="openalex-local",
    instructions="Local OpenAlex database with 284M+ works and full-text search. "
    "Use search to find papers by title/abstract, search_by_id for OpenAlex ID or DOI lookup, "
    "and status for database stats.",
)


@mcp.tool()
def search(
    query: str,
    limit: int = 10,
    offset: int = 0,
    with_abstracts: bool = False,
) -> str:
    """Search for academic works by title, abstract, or authors.

    Uses FTS5 full-text search index for fast searching across 284M+ papers.
    Supports FTS5 query syntax: AND, OR, NOT, "exact phrases".

    Args:
        query: Search query (e.g., "machine learning", "CRISPR", "neural network AND hippocampus")
        limit: Maximum number of results to return (default: 10)
        offset: Skip first N results for pagination (default: 0)
        with_abstracts: Include abstracts in results (default: False)

    Returns:
        JSON string with search results including total count and matching works.

    Examples:
        search("machine learning")
        search("CRISPR", limit=20)
        search("neural network AND memory", with_abstracts=True)
    """
    results = _search(query, limit=limit, offset=offset)

    works_data = []
    for work in results.works:
        work_dict = {
            "openalex_id": work.openalex_id,
            "doi": work.doi,
            "title": work.title,
            "authors": work.authors,
            "year": work.year,
            "source": work.source,
            "cited_by_count": work.cited_by_count,
        }
        if with_abstracts and work.abstract:
            work_dict["abstract"] = work.abstract
        works_data.append(work_dict)

    return json.dumps(
        {
            "query": results.query,
            "total": results.total,
            "returned": len(works_data),
            "elapsed_ms": round(results.elapsed_ms, 2),
            "works": works_data,
        },
        indent=2,
    )


@mcp.tool()
def search_by_id(identifier: str, as_citation: bool = False) -> str:
    """Get detailed information about a work by OpenAlex ID or DOI.

    Args:
        identifier: OpenAlex ID (e.g., "W2741809807") or DOI (e.g., "10.1038/nature12373")
        as_citation: Return formatted citation instead of full metadata

    Returns:
        JSON string with work metadata, or formatted citation string.

    Examples:
        search_by_id("W2741809807")
        search_by_id("10.1038/nature12373")
        search_by_id("10.1126/science.aax0758", as_citation=True)
    """
    work = _get(identifier)

    if work is None:
        return json.dumps({"error": f"Not found: {identifier}"})

    if as_citation:
        return work.citation()

    return json.dumps(work.to_dict(), indent=2)


@mcp.tool()
def status() -> str:
    """Get database statistics and status.

    Returns:
        JSON string with database path, work count, FTS index count.
    """
    db_info = _info()
    return json.dumps(db_info, indent=2)


@mcp.tool()
def enrich_ids(identifiers: list[str]) -> str:
    """Enrich OpenAlex IDs or DOIs with full metadata.

    Use this after search() to get detailed metadata for papers.
    The search() tool returns basic info (title, authors, year, source).
    This tool adds: abstract, concepts, is_oa, oa_url, etc.

    Typical workflow:
    1. search("epilepsy seizure prediction") -> get IDs
    2. enrich_ids([id1, id2, ...]) -> get full metadata

    Args:
        identifiers: List of OpenAlex IDs or DOIs

    Returns:
        JSON string with enriched works.

    Examples:
        enrich_ids(["W2741809807"])
        enrich_ids(["10.1038/nature12373", "W2741809807"])
    """
    works = _get_many(identifiers)

    works_data = []
    for work in works:
        works_data.append(work.to_dict())

    return json.dumps(
        {
            "requested": len(identifiers),
            "found": len(works_data),
            "works": works_data,
        },
        indent=2,
    )


def run_server(
    transport: str = "stdio",
    host: str = "localhost",
    port: int = 8083,
) -> None:
    """Run the MCP server.

    Args:
        transport: Transport protocol ("stdio", "sse", or "http")
        host: Host for HTTP/SSE transport
        port: Port for HTTP/SSE transport
    """
    if transport == "stdio":
        mcp.run(transport="stdio")
    elif transport == "sse":
        mcp.run(transport="sse", host=host, port=port)
    elif transport == "http":
        mcp.run(transport="streamable-http", host=host, port=port)
    else:
        raise ValueError(f"Unknown transport: {transport}")


def main():
    """Entry point for openalex-local-mcp command."""
    run_server(transport="stdio")


if __name__ == "__main__":
    main()
