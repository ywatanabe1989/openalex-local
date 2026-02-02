# OpenAlex Local Examples

Demonstration scripts for `openalex-local` features.

## Quick Start

```bash
# Run all examples
./00_run_all.sh

# Or run individually
python 01_basic_search.py
python 02_get_by_doi.py
```

## Examples

| File | Description |
|------|-------------|
| `00_run_all.sh` | Run all examples in sequence |
| `01_basic_search.py` | Full-text search across 459M+ works |
| `02_get_by_doi.py` | Retrieve work by DOI with metadata |
| `03_citations.py` | Generate APA and BibTeX citations |
| `04_cache_workflow.py` | Local caching for offline analysis |
| `05_async_search.py` | Concurrent async search operations |
| `06_enrich_workflow.py` | Enrich search results with metadata |
| `07_quickstart.ipynb` | Interactive Jupyter notebook guide |

## Output

Each Python script uses `@stx.session` for automatic logging.
Outputs are saved to:

```
script_out/
  FINISHED_SUCCESS_<timestamp>/
    01_basic_search/
      log.txt
      ...
```

## CLI Examples

```bash
# Search
openalex-local search "machine learning" -n 5
openalex-local s "neural networks" -n 3  # alias

# Get by DOI
openalex-local search-by-doi "10.7717/peerj.4375"
openalex-local doi "10.7717/peerj.4375" --citation  # APA
openalex-local doi "10.7717/peerj.4375" --bibtex    # BibTeX

# Cache
openalex-local cache create mypapers -q "CRISPR" -l 100
openalex-local cache list
openalex-local cache stats mypapers
openalex-local cache query mypapers --year-min 2020
openalex-local cache export mypapers refs.bib -f bibtex
openalex-local cache delete mypapers --yes
```

## Requirements

- Python 3.10+
- `openalex-local` installed
- `scitex` for logging (optional, but recommended)
- OpenAlex database (~900GB)
