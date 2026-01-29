#!/usr/bin/env python3
"""Example: Get work by DOI.

Demonstrates:
- Retrieving a specific work by DOI
- Accessing detailed metadata
"""

from openalex_local import get

# Example DOI (Nature paper on deep learning)
doi = "10.1038/nature14539"

work = get(doi)

if work:
    print(f"Title: {work.title}")
    print(f"Year: {work.year}")
    print(f"DOI: {work.doi}")
    print(f"OpenAlex ID: {work.openalex_id}")
    print(f"Type: {work.type}")
    print(f"Citations: {work.cited_by_count:,}")
    print(f"Open Access: {work.is_oa}")

    if work.authors:
        print(f"\nAuthors ({len(work.authors)}):")
        for author in work.authors[:5]:
            print(f"  - {author}")

    if work.abstract:
        print(f"\nAbstract:\n{work.abstract[:500]}...")
else:
    print(f"Work not found: {doi}")
