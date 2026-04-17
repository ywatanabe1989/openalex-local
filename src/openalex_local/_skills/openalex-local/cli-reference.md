---
description: CLI commands for openalex-local.
---

# CLI Reference

```bash
# Search
openalex-local search "neural network attention" -n 20 -a -A --concepts
openalex-local search "CRISPR" --save results.json --format json
openalex-local search-by-doi 10.1038/nature12373
openalex-local search-by-doi W2741809807 --bibtex

# Status / info
openalex-local status
openalex-local --version
openalex-local --help-recursive

# HTTP relay (FastAPI)
openalex-local relay --host 0.0.0.0 --port 31292

# MCP server
openalex-local mcp start                    # stdio
openalex-local mcp start -t http --port 8083
openalex-local mcp doctor
openalex-local mcp list-tools
openalex-local mcp installation

# SciTeX Impact Factor export
openalex-local export-if -o scitex_if.csv
openalex-local export-if -o top1000.json --limit 1000

# Local cache management (see: openalex-local cache --help)
openalex-local cache list
openalex-local cache stats <name>

# Python API introspection
openalex-local list-python-apis -v
```

Aliases: `s` → `search`, `doi` → `search-by-doi`, `st` → `status`.
Use `--http` / `--api-url` to switch to HTTP-relay mode.
