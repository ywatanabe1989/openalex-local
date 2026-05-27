---
description: |
  [TOPIC] CLI reference
  [DETAILS] `openalex-local` console entry — search, search-by-doi, cache (8 sub), export-if, show-status, mcp, relay, docs, list-python-apis.
tags: [openalex-local-cli-reference]
---

# CLI Reference

```
openalex-local [OPTIONS] COMMAND [ARGS]...
```

Local OpenAlex database with 284M+ works and full-text search.

## Global options

| Flag | Purpose |
|---|---|
| `-h`, `--help` | Show this message and exit |
| `-V`, `--version` | Show the version and exit |
| `--http` | Use HTTP API instead of direct database |
| `--api-url TEXT` | API URL for http mode (default: auto-detect) |
| `--json` | Emit machine-readable JSON (where supported) |
| `--help-recursive` | Show help for all commands recursively |

## Configuration precedence (highest → lowest)

1. CLI flags / function kwargs
2. `./config.yaml` (project-local)
3. `$OPENALEX_LOCAL_CONFIG` (env var pointing to a YAML file)
4. `~/.scitex/openalex-local/config.yaml` (user-level)
5. Built-in defaults

## Commands by category

### Lookup

| Command | Purpose |
|---|---|
| `search` | Search for works by title, abstract, or authors |
| `search-by-doi` | Search for a work by DOI |

### Cache

| Command | Purpose |
|---|---|
| `cache create` | Create a new cache from search or IDs |
| `cache append` | Append papers to an existing cache |
| `cache list` | List all caches |
| `cache query` | Query a cache with filters |
| `cache show-ids` | Print all OpenAlex IDs in a cache |
| `cache show-stats` | Show cache statistics |
| `cache export` | Export cache to file |
| `cache delete` | Delete a cache |

### Impact factor + status

| Command | Purpose |
|---|---|
| `export-if` | Export SciTeX Impact Factors (OpenAlex) to CSV or JSON |
| `show-status` | Show status and configuration |
| `list-python-apis` | List Python APIs (alias for `scitex introspect api openalex_local`) |

### Servers

| Command | Purpose |
|---|---|
| `relay` | Run HTTP relay server (FastAPI) for remote DB access |
| `mcp start` | Start the MCP server |
| `mcp doctor` | Diagnose MCP setup |
| `mcp list-tools` | List available MCP tools |
| `mcp show-installation` | Print MCP client installation instructions |

### Docs

| Command | Purpose |
|---|---|
| `docs` | View package documentation |
| `skills` | View package skills (workflow-oriented guides) |

## Common flags

`search`:
```
-n, --number INTEGER         Number of results
-o, --offset INTEGER         Skip first N results
-a, --abstracts              Show abstracts
-A, --authors                Show authors
--concepts                   Show concepts/topics
-if, --impact-factor         Show journal impact factor
--save PATH --format FMT     Save to file (text|json|bibtex)
```

`search-by-doi`:
```
--citation                   Output as APA citation
--bibtex                     Output as BibTeX entry
--save PATH --format FMT     Save to file (text|json|bibtex)
```

`export-if`:
```
-o, --output TEXT       Output file (csv or json)
--format [csv|json]     Output format (auto from extension)
--limit INTEGER         Limit rows (0=all)
--dry-run               Show what would be exported without writing
-y, --yes               Skip confirmation prompts
```

`relay`:
```
--host TEXT       Host to bind
--port INTEGER    Port (default 31292)
--force           Kill existing process if port in use
```

## Examples

```bash
openalex-local search "graph neural network" -n 5 -A --concepts
openalex-local search-by-doi 10.1038/nature12373 --bibtex
openalex-local cache create --query "CRISPR" --name crispr2024
openalex-local cache show-stats crispr2024
openalex-local export-if -o scitex_if.csv
openalex-local relay --port 31292
openalex-local --http search "transformer attention"
openalex-local mcp doctor
```

## See also

- [11_cli-reference.md](11_cli-reference.md) — historical CLI notes
- [12_mcp-tools.md](12_mcp-tools.md) — MCP tool catalog
- [10_database-setup.md](10_database-setup.md) — snapshot setup
