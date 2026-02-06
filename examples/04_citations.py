#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2026-02-03 (ywatanabe)"
# File: /home/ywatanabe/proj/openalex-local/examples/03_citations.py

"""Generate APA and BibTeX citations.

Demonstrates:
- Work.citation() method for formatted citations
- APA style citations
- BibTeX entries for reference managers
"""

from pathlib import Path

try:
    import scitex as stx
    HAS_SCITEX = True
except ImportError:
    HAS_SCITEX = False
    import logging
    logging.basicConfig(level=logging.INFO, format="%(message)s")

from openalex_local import get, search


def _main(doi, search_query, limit, logger, output_dir=None):
    """Core logic."""
    if output_dir is None:
        output_dir = Path(".")

    # --- Single work citation ---
    logger.info("=== Single Work Citation ===")
    logger.info(f"DOI: {doi}")
    logger.info("")

    work = get(doi)
    if work:
        logger.info("APA Citation:")
        logger.info(work.citation("apa"))
        logger.info("")

        logger.info("BibTeX Entry:")
        logger.info(work.citation("bibtex"))
        logger.info("")
    else:
        logger.warning(f"Work not found: {doi}")

    # --- BibTeX export from search ---
    logger.info("=== BibTeX Export from Search ===")
    logger.info(f"Query: '{search_query}'")
    logger.info(f"Limit: {limit}")
    logger.info("")

    results = search(search_query, limit=limit)
    logger.info(f"Found {results.total:,} matches")
    logger.info("")

    # Generate BibTeX file
    bibtex_lines = []
    for work in results.works:
        bibtex_lines.append(work.citation("bibtex"))
        bibtex_lines.append("")

    bibtex_content = "\n".join(bibtex_lines)
    bibtex_path = output_dir / "references.bib"
    bibtex_path.write_text(bibtex_content)
    logger.info(f"Saved BibTeX to: {bibtex_path}")

    return 0


if HAS_SCITEX:
    @stx.session
    def main(
        doi: str = "10.7717/peerj.4375",
        search_query: str = "CRISPR gene editing",
        limit: int = 5,
        CONFIG=stx.INJECTED,
        logger=stx.INJECTED,
    ):
        """Generate citations for works."""
        output_dir = Path(CONFIG.SDIR_OUT)
        return _main(doi, search_query, limit, logger, output_dir)
else:
    def main(doi="10.7717/peerj.4375", search_query="CRISPR gene editing", limit=5):
        """Generate citations for works."""
        logger = logging.getLogger(__name__)
        return _main(doi, search_query, limit, logger)


if __name__ == "__main__":
    main()

# EOF
