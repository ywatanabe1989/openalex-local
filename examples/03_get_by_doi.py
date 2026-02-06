#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2026-02-03 (ywatanabe)"
# File: /home/ywatanabe/proj/openalex-local/examples/02_get_by_doi.py

"""Get work by DOI with detailed metadata.

Demonstrates:
- Retrieving a specific work by DOI or OpenAlex ID
- Accessing detailed metadata (abstract, concepts, etc.)
- Checking open access status
"""

try:
    import scitex as stx
    HAS_SCITEX = True
except ImportError:
    HAS_SCITEX = False
    import logging
    logging.basicConfig(level=logging.INFO, format="%(message)s")

from openalex_local import get


def _main(doi, logger):
    """Core logic."""
    logger.info(f"Looking up: {doi}")
    logger.info("")

    work = get(doi)

    if work is None:
        logger.warning(f"Work not found: {doi}")
        return 1

    logger.info(f"Title: {work.title}")
    logger.info(f"Year: {work.year}")
    logger.info(f"DOI: {work.doi}")
    logger.info(f"OpenAlex ID: {work.openalex_id}")
    logger.info(f"Type: {work.type}")
    logger.info(f"Journal: {work.source or 'N/A'}")
    logger.info(f"Citations: {work.cited_by_count:,}")
    logger.info(f"Open Access: {work.is_oa}")

    if work.authors:
        logger.info("")
        logger.info(f"Authors ({len(work.authors)}):")
        for author in work.authors[:5]:
            logger.info(f"  - {author}")

    if work.abstract:
        logger.info("")
        logger.info("Abstract:")
        abstract_preview = work.abstract[:500]
        if len(work.abstract) > 500:
            abstract_preview += "..."
        logger.info(abstract_preview)

    return 0


if HAS_SCITEX:
    @stx.session
    def main(
        doi: str = "10.1038/nature14539",
        CONFIG=stx.INJECTED,
        logger=stx.INJECTED,
    ):
        """Retrieve work by DOI."""
        return _main(doi, logger)
else:
    def main(doi="10.1038/nature14539"):
        """Retrieve work by DOI."""
        logger = logging.getLogger(__name__)
        return _main(doi, logger)


if __name__ == "__main__":
    main()

# EOF
