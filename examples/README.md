# Examples

Demonstration scripts for openalex-local.

## Prerequisites

```bash
pip install openalex-local
```

Ensure database is configured:
```bash
export OPENALEX_LOCAL_DB=/path/to/openalex.db
```

## Examples

| Script | Description |
|--------|-------------|
| `01_basic_search.py` | Full-text search across works |
| `02_get_by_doi.py` | Retrieve work by DOI |
| `03_batch_processing.py` | Batch processing with jobs module |

## Run All

```bash
./00_run_all.sh
```

## CLI Examples

```bash
# Search
openalex-local search "machine learning" -n 5

# Get by DOI
openalex-local search-by-doi "10.1038/nature14539"

# Status
openalex-local status
```
