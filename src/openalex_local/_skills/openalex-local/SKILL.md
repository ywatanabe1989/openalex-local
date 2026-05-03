---
name: openalex-local
description: |
  [WHAT] Offline, zero-API-key search over the full OpenAlex academic corpus.
  [WHEN] Use when the user asks to "search papers", "find literature on X", "look up a DOI", "get metadata for this paper", "enrich these OpenAlex IDs", "batch-resolve DOIs to BibTeX", "search by title/abstract/author".
  [HOW] `import openalex_local` then call `pyalex.Works().search(...)`.
tags: [openalex-local]
allowed-tools: mcp__scitex__openalex_*
primary_interface: python
interfaces:
  python: 3
  cli: 2
  mcp: 2
  skills: 2
  hook: 0
  http: 0
---


# openalex-local

> **Interfaces:** Python ⭐⭐⭐ (primary) · CLI ⭐⭐ · MCP ⭐⭐ · Skills ⭐⭐ · Hook — · HTTP —

## Installation & import

`pip install openalex-local` installs the standalone:

```python
import openalex_local
```

This package does not ship as a submodule of the `scitex` umbrella.

## Sub-skills

### Core
- [01_quick-start.md](01_quick-start.md) — Basic usage
- [02_search-syntax.md](02_search-syntax.md) — FTS5 query syntax

### Workflows
- [10_database-setup.md](10_database-setup.md) — Database architecture, build pipeline, access modes
- [11_cli-reference.md](11_cli-reference.md) — CLI commands
- [12_mcp-tools.md](12_mcp-tools.md) — MCP tools for AI agents

## CLI

```bash
openalex-local search "neural network attention"
openalex-local search-by-id W2741809807
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `openalex_search` | Full-text search across works |
| `openalex_search_by_id` | Get work by OpenAlex ID |
| `openalex_enrich_ids` | Enrich IDs with metadata |
| `openalex_status` | Database status |
