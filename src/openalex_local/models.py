"""Data models for openalex_local."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class Work:
    """
    Represents a scholarly work from OpenAlex.

    Attributes:
        openalex_id: OpenAlex ID (e.g., W2741809807)
        doi: Digital Object Identifier
        title: Work title
        abstract: Abstract text (reconstructed from inverted index)
        authors: List of author names
        year: Publication year
        source: Journal/venue name
        issn: Journal ISSN
        volume: Volume number
        issue: Issue number
        pages: Page range
        publisher: Publisher name
        type: Work type (journal-article, book-chapter, etc.)
        concepts: List of OpenAlex concepts
        topics: List of OpenAlex topics
        cited_by_count: Number of citations
        referenced_works: List of referenced OpenAlex IDs
        is_oa: Is open access
        oa_url: Open access URL
    """

    openalex_id: str
    doi: Optional[str] = None
    title: Optional[str] = None
    abstract: Optional[str] = None
    authors: List[str] = field(default_factory=list)
    year: Optional[int] = None
    source: Optional[str] = None
    issn: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    publisher: Optional[str] = None
    type: Optional[str] = None
    concepts: List[Dict[str, Any]] = field(default_factory=list)
    topics: List[Dict[str, Any]] = field(default_factory=list)
    cited_by_count: Optional[int] = None
    referenced_works: List[str] = field(default_factory=list)
    is_oa: bool = False
    oa_url: Optional[str] = None

    @classmethod
    def from_openalex(cls, data: dict) -> "Work":
        """
        Create Work from OpenAlex API/snapshot JSON.

        Args:
            data: OpenAlex work dictionary

        Returns:
            Work instance
        """
        # Extract OpenAlex ID
        openalex_id = data.get("id", "").replace("https://openalex.org/", "")

        # Extract DOI
        doi = data.get("doi", "").replace("https://doi.org/", "") if data.get("doi") else None

        # Extract authors
        authors = []
        for authorship in data.get("authorships", []):
            author = authorship.get("author", {})
            name = author.get("display_name")
            if name:
                authors.append(name)

        # Reconstruct abstract from inverted index
        abstract = None
        inv_index = data.get("abstract_inverted_index")
        if inv_index:
            words = sorted(
                [(pos, word) for word, positions in inv_index.items() for pos in positions]
            )
            abstract = " ".join(word for _, word in words)

        # Extract source info
        primary_location = data.get("primary_location") or {}
        source_info = primary_location.get("source") or {}
        source = source_info.get("display_name")
        issns = source_info.get("issn") or []
        issn = issns[0] if issns else None

        # Extract biblio
        biblio = data.get("biblio") or {}

        # Extract concepts (top 5)
        concepts = [
            {"name": c.get("display_name"), "score": c.get("score")}
            for c in (data.get("concepts") or [])[:5]
        ]

        # Extract topics (top 3)
        topics = [
            {"name": t.get("display_name"), "subfield": t.get("subfield", {}).get("display_name")}
            for t in (data.get("topics") or [])[:3]
        ]

        # Extract OA info
        oa_info = data.get("open_access") or {}

        return cls(
            openalex_id=openalex_id,
            doi=doi,
            title=data.get("title") or data.get("display_name"),
            abstract=abstract,
            authors=authors,
            year=data.get("publication_year"),
            source=source,
            issn=issn,
            volume=biblio.get("volume"),
            issue=biblio.get("issue"),
            pages=biblio.get("first_page"),
            publisher=source_info.get("host_organization_name"),
            type=data.get("type"),
            concepts=concepts,
            topics=topics,
            cited_by_count=data.get("cited_by_count"),
            referenced_works=[
                r.replace("https://openalex.org/", "")
                for r in (data.get("referenced_works") or [])
            ],
            is_oa=oa_info.get("is_oa", False),
            oa_url=oa_info.get("oa_url"),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "openalex_id": self.openalex_id,
            "doi": self.doi,
            "title": self.title,
            "abstract": self.abstract,
            "authors": self.authors,
            "year": self.year,
            "source": self.source,
            "issn": self.issn,
            "volume": self.volume,
            "issue": self.issue,
            "pages": self.pages,
            "publisher": self.publisher,
            "type": self.type,
            "concepts": self.concepts,
            "topics": self.topics,
            "cited_by_count": self.cited_by_count,
            "referenced_works": self.referenced_works,
            "is_oa": self.is_oa,
            "oa_url": self.oa_url,
        }


@dataclass
class SearchResult:
    """
    Container for search results with metadata.

    Attributes:
        works: List of Work objects
        total: Total number of matches
        query: Original search query
        elapsed_ms: Search time in milliseconds
    """

    works: List[Work]
    total: int
    query: str
    elapsed_ms: float

    def __len__(self) -> int:
        return len(self.works)

    def __iter__(self):
        return iter(self.works)

    def __getitem__(self, idx):
        return self.works[idx]
