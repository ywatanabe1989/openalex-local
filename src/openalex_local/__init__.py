"""
OpenAlex Local - Local OpenAlex database with 284M+ works and semantic search.

Example:
    >>> from openalex_local import search, get
    >>> results = search("machine learning neural networks")
    >>> work = get("W2741809807")  # OpenAlex ID
    >>> work = get("10.1038/nature12373")  # or DOI
"""

__version__ = "0.1.0"

# API will be exposed here after implementation
# from .api import search, get, count, info
