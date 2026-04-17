---
name: openalex-local
description: Local OpenAlex database with 284M+ works, abstracts, and full-text search (FTS5). Python API, CLI, HTTP relay, and MCP server.
type: reference
---

# openalex-local

Local mirror of the [OpenAlex](https://openalex.org) scholarly-works snapshot
with SQLite + FTS5 full-text search across 284M+ works. Ships a Python API,
a `openalex-local` CLI, a FastAPI HTTP relay, and an MCP server.

## Installation

```bash
pip install openalex-local               # core (CLI + Python API)
pip install openalex-local[mcp]          # + FastMCP server
pip install openalex-local[server]       # + FastAPI relay
pip install openalex-local[all]          # server + mcp + dev + docs
```

## Sub-skills

- [quick-start.md](quick-start.md) — Basic Python usage
- [search-syntax.md](search-syntax.md) — FTS5 query syntax, async, cache
- [database-setup.md](database-setup.md) — Build pipeline, access modes
- [cli-reference.md](cli-reference.md) — CLI commands
- [mcp-tools.md](mcp-tools.md) — MCP tools for AI agents

## Python API

Top-level `openalex_local` exports (verified against source):

| Name | Purpose |
|------|---------|
| `search(query, limit=20, offset=0)` | FTS5 full-text search → `SearchResult` |
| `count(query)` | Count matches for a query |
| `get(id_or_doi)` | Fetch a single `Work` by OpenAlex ID or DOI |
| `get_many(ids)` | Fetch multiple works |
| `exists(id)` | Boolean existence check |
| `info()` | Database stats (work count, FTS count, path) |
| `enrich(work)` / `enrich_ids(ids)` | Add full metadata (abstract, concepts, OA) |
| `save(result, path, format=...)` | Export to text/json/bibtex |
| `configure(mode=...)` / `get_mode()` | Switch db vs http mode |
| `Work`, `SearchResult` | Dataclasses |
| `aio` | Async variants (`aio.search`, `aio.count`, `aio.get`, …) |
| `cache` | Local result cache (`create`, `query`, `append`, `stats`, `export`) |
| `jobs` | Simple batch-job queue (`jobs.create`, `jobs.run`, `jobs.list_jobs`) |

## CLI (`openalex-local`)

Verified from `openalex-local --help`:

```bash
openalex-local search "neural network attention" -n 20    # alias: s
openalex-local search-by-doi 10.1038/nature12373          # alias: doi
openalex-local status                                     # alias: st
openalex-local export-if -o scitex_if.csv                 # SciTeX IF export
openalex-local relay --host 0.0.0.0 --port 31292          # FastAPI HTTP relay
openalex-local mcp start                                  # MCP stdio server
openalex-local mcp start -t http --port 8083              # MCP HTTP server
openalex-local mcp doctor | installation | list-tools
openalex-local cache ...                                  # cache mgmt
openalex-local list-python-apis [-v|-vv|-vvv]
```

Global flags: `--http` / `--api-url` switch the CLI to HTTP-relay mode.

## MCP Tools

Exposed by `openalex-local mcp start` (FastMCP). Tool names as registered:

| Tool | Description |
|------|-------------|
| `search` | FTS5 full-text search across works |
| `search_by_id` | Get a work by OpenAlex ID or DOI |
| `enrich_ids` | Batch-fetch full metadata for IDs/DOIs |
| `status` | Database statistics |

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `OPENALEX_LOCAL_DB` | Path to the SQLite database |
| `OPENALEX_LOCAL_MODE` | Force `db`, `http`, or `auto` |
| `OPENALEX_LOCAL_API_URL` | HTTP relay URL for http mode |
| `OPENALEX_LOCAL_HOST` / `OPENALEX_LOCAL_PORT` | Relay bind settings |
| `OPENALEX_LOCAL_MCP_HOST` / `OPENALEX_LOCAL_MCP_PORT` | MCP HTTP settings |
