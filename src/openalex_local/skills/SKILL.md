---
name: openalex-local
description: Local OpenAlex database with 284M+ works, abstracts, and semantic search. Use when searching academic literature metadata, citations, or building bibliometric analyses.
allowed-tools: mcp__scitex__openalex_*
---

# Local OpenAlex with openalex-local

## Quick Start

```python
from openalex_local import search, search_by_id

# Search works
results = search("neural oscillations gamma band", limit=20)

# Get by OpenAlex ID
work = search_by_id("W2741809807")

# Enrich DOIs with metadata
enriched = enrich_ids(["10.1038/s41586-024-00001-1"])
```

## CLI Commands

```bash
openalex-local search "deep learning EEG" --limit 20
openalex-local search-by-id W2741809807
openalex-local enrich-ids 10.1038/s41586-024-00001-1
openalex-local status

# Skills
openalex-local skills list
```

## MCP Tools

| Tool | Purpose |
|------|---------|
| `openalex_search` | Full-text search across 284M+ works |
| `openalex_search_by_id` | Get work by OpenAlex ID |
| `openalex_enrich_ids` | Enrich DOIs with metadata |
| `openalex_status` | Database status |
