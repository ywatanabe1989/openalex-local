---
description: MCP tools for OpenAlex search and lookup.
---

# MCP Tools

Started via `openalex-local mcp start` (FastMCP). Tool names:

| Tool | Description |
|------|-------------|
| `search` | FTS5 full-text search across 284M+ works |
| `search_by_id` | Get a work by OpenAlex ID or DOI |
| `enrich_ids` | Batch-fetch full metadata for IDs/DOIs |
| `status` | Database stats (work count, FTS count, path) |

## Client configuration

Local (stdio, Claude Desktop / Claude Code):

```json
{
  "mcpServers": {
    "openalex-local": {
      "command": "openalex-local",
      "args": ["mcp", "start"],
      "env": {"OPENALEX_LOCAL_DB": "/path/to/openalex.db"}
    }
  }
}
```

Remote (HTTP, persistent server):

```bash
openalex-local mcp start -t http --host 0.0.0.0 --port 8083
```

```json
{
  "mcpServers": {
    "openalex-remote": {"url": "http://your-server:8083/mcp"}
  }
}
```
