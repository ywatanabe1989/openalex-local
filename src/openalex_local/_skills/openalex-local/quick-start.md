---
description: Basic search and lookup — full-text search, DOI lookup, enrichment.
---

# Quick Start

```python
from openalex_local import (
    search, count, get, get_many, exists, info,
    enrich, enrich_ids, save, configure, get_mode,
)

# Full-text search (FTS5)
results = search("hippocampal sharp wave ripples", limit=10)
for work in results.works:
    print(f"{work.title} ({work.year})")

# Get a single work by OpenAlex ID or DOI
work = get("W2741809807")
work = get("10.1038/nature12373")

# Batch lookup
works = get_many(["W2741809807", "10.1038/nature12373"])

# Counts / existence / DB info
count("machine learning")
exists("W2741809807")
info()                         # {'work_count': ..., 'fts_indexed': ..., 'db_path': ...}

# Enrichment — add abstract, concepts, OA status, ...
enriched = enrich_ids(["W2741809807"])

# Export
save(results, "results.json", format="json")
save(results, "results.bib", format="bibtex")

# Mode (direct SQLite vs HTTP relay)
configure(mode="db")           # or "http"
get_mode()
```

## Async

```python
import asyncio
from openalex_local import aio

async def main():
    results = await aio.search("machine learning", limit=10)
    work    = await aio.get("W2741809807")

asyncio.run(main())
```
