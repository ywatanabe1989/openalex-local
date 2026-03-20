---
name: openalex-local
description: Local OpenAlex database with 284M+ works, abstracts, and semantic search. Use when searching academic literature, looking up papers by DOI, building bibliographies, or analyzing citations.
allowed-tools: mcp__scitex__openalex_*
---

# Literature Search with openalex-local

## Quick Start

```python
from openalex_local import search, get, count

# Full-text search (title + abstract)
results = search("machine learning neural networks")

# Get by OpenAlex ID or DOI
work = get("W2741809807")
work = get("10.1038/nature12373")

# Count matches
n = count("CRISPR genome editing")
```

## Common Workflows

### "I want to find papers on a topic"

```python
from openalex_local import search

# Basic search
results = search("neural oscillations gamma band", limit=20)
for work in results:
    print(f"{work.title} ({work.year}) - {work.cited_by_count} citations")
    print(f"  DOI: {work.doi}")

# Paginate through results
page1 = search("deep learning", limit=50, offset=0)
page2 = search("deep learning", limit=50, offset=50)
print(f"Total matches: {page1.total}")
```

### "I need a specific paper by DOI or ID"

```python
from openalex_local import get, exists

# By DOI
work = get("10.1038/nature12373")

# By OpenAlex ID
work = get("W2741809807")

# Check existence without fetching
if exists("10.1038/nature12373"):
    print("Paper found in database")
```

### "I want to build a bibliography"

```python
from openalex_local import search, save

results = search("CRISPR applications", limit=100)

# Export as BibTeX
save(results, "references.bib", format="bibtex")

# Export as JSON
save(results, "papers.json", format="json")

# Get individual citations
work = get("W2741809807")
print(work.citation("apa"))     # APA format
print(work.citation("bibtex"))  # BibTeX entry
```

### "I want to enrich DOIs with metadata"

```python
from openalex_local import enrich_ids

dois = [
    "10.1038/nature12373",
    "10.1126/science.1157996",
    "10.1016/j.cell.2014.05.010",
]

works = enrich_ids(dois)
for work in works:
    print(f"{work.title}")
    print(f"  Authors: {', '.join(work.authors[:3])}")
    print(f"  Journal: {work.source}")
    print(f"  Citations: {work.cited_by_count}")
    print(f"  Abstract: {work.abstract[:200]}...")
```

### "I want to batch-lookup multiple papers"

```python
from openalex_local import get_many

ids = ["W2741809807", "W2100837269", "W1775749144"]
works = get_many(ids)
for work in works:
    print(f"{work.title} ({work.year})")
```

### "I want to cache results for later"

```python
from openalex_local import cache

# Create cache from search
cache.create("my_review", query="neural oscillations", limit=500)

# Create cache from specific IDs
cache.create("key_papers", ids=["W2741809807", "10.1038/nature12373"])

# Query cached papers
cache.query("my_review", year_min=2020)

# Export cache
cache.export("my_review", "review_papers.json")

# List all caches
cache.list()
```

## Work Object

Every lookup returns a `Work` dataclass with these fields:

```python
work = get("W2741809807")
work.openalex_id       # "W2741809807"
work.doi               # "10.1038/nature12373"
work.title             # "Paper title"
work.abstract          # Full abstract text
work.authors           # ["Author One", "Author Two"]
work.year              # 2023
work.source            # "Nature"
work.issn              # "0028-0836"
work.type              # "journal-article"
work.cited_by_count    # 42
work.concepts          # [{"name": "Machine learning", "score": 0.95}]
work.is_oa             # True
work.oa_url            # "https://..."
work.referenced_works  # ["W123...", "W456..."]

# Methods
work.to_dict()         # Full dictionary
work.citation("apa")   # APA citation string
work.citation("bibtex")  # BibTeX entry
```

## SearchResult Object

```python
results = search("deep learning", limit=20)
results.total       # Total matching works (e.g., 1523847)
results.query       # "deep learning"
results.elapsed_ms  # 45.2
results.works       # List[Work]
len(results)        # Number of works returned
for work in results:  # Iterable
    print(work.title)
```

## Access Modes

```python
from openalex_local import configure, configure_http, get_mode, info

# Direct database (default if database found)
configure("/path/to/openalex.db")

# HTTP API (connect to relay server)
configure_http("http://localhost:31292")

# Check current mode
print(get_mode())  # "db" or "http"

# Database statistics
print(info())  # {"status": "ok", "mode": "db", "work_count": 284000000, ...}
```

## Async API

```python
from openalex_local import aio

# Async search
results = await aio.search("quantum computing", limit=10)

# Async get
work = await aio.get("W2741809807")

# Async batch
works = await aio.get_many(["W2741809807", "W2100837269"])
```

## CLI Commands

```bash
# Search
openalex-local search "CRISPR genome editing" -n 10
openalex-local search "neural network" -n 5 -a       # with abstracts
openalex-local search "deep learning" --json          # JSON output
openalex-local search "machine learning" --save results.bib --format bibtex

# Lookup by DOI or ID
openalex-local search-by-doi 10.1038/nature12373
openalex-local search-by-doi W2741809807 --bibtex
openalex-local search-by-doi W2741809807 --citation

# Status and info
openalex-local status
openalex-local status --json

# Cache management
openalex-local cache create my_review --query "neural oscillations" --limit 500
openalex-local cache list
openalex-local cache query my_review
openalex-local cache export my_review -o papers.json

# Impact factors
openalex-local export-if -o scitex_if.csv
openalex-local search "machine learning" --with-if

# HTTP relay server
openalex-local relay --port 31292

# MCP server
openalex-local mcp start
openalex-local mcp doctor
openalex-local mcp list-tools

# Skills and docs
openalex-local skills list
openalex-local docs list
```

## MCP Tools (for AI agents)

| Tool | Purpose |
|------|---------|
| `openalex_search` | Full-text search across 284M+ works |
| `openalex_search_by_id` | Get work by OpenAlex ID or DOI |
| `openalex_enrich_ids` | Batch lookup DOIs/IDs with full metadata |
| `openalex_status` | Database statistics and health |

## Export Formats

| Format | Extension | Use case |
|--------|-----------|----------|
| `json` | `.json` | Machine-readable, full metadata |
| `bibtex` | `.bib` | LaTeX bibliography |
| `text` | `.txt` | Human-readable summary |

## Specific Topics

* **Search syntax and FTS5 patterns** [references/search-syntax.md](references/search-syntax.md)
* **Database setup and architecture** [references/database-setup.md](references/database-setup.md)
