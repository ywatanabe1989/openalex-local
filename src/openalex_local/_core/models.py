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
    # Source/journal metrics (from sources table)
    impact_factor: Optional[float] = None  # 2yr_mean_citedness
    source_h_index: Optional[int] = None
    source_cited_by_count: Optional[int] = None

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
        doi = (
            data.get("doi", "").replace("https://doi.org/", "")
            if data.get("doi")
            else None
        )

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
                [
                    (pos, word)
                    for word, positions in inv_index.items()
                    for pos in positions
                ]
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
            {
                "name": t.get("display_name"),
                "subfield": t.get("subfield", {}).get("display_name"),
            }
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

    @classmethod
    def from_db_row(cls, data: dict) -> "Work":
        """
        Create Work from database row dictionary.

        Args:
            data: Database row as dictionary (with parsed JSON fields)

        Returns:
            Work instance
        """
        return cls(
            openalex_id=data.get("openalex_id", ""),
            doi=data.get("doi"),
            title=data.get("title"),
            abstract=data.get("abstract"),
            authors=data.get("authors", []),
            year=data.get("year"),
            source=data.get("source"),
            issn=data.get("issn"),
            volume=data.get("volume"),
            issue=data.get("issue"),
            pages=data.get("pages"),
            publisher=data.get("publisher"),
            type=data.get("type"),
            concepts=data.get("concepts", []),
            topics=data.get("topics", []),
            cited_by_count=data.get("cited_by_count"),
            referenced_works=data.get("referenced_works", []),
            is_oa=bool(data.get("is_oa", False)),
            oa_url=data.get("oa_url"),
            impact_factor=data.get("impact_factor"),
            source_h_index=data.get("source_h_index"),
            source_cited_by_count=data.get("source_cited_by_count"),
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
            "impact_factor": self.impact_factor,
            "source_h_index": self.source_h_index,
            "source_cited_by_count": self.source_cited_by_count,
        }

    def citation(self, style: str = "apa") -> str:
        """
        Format work as a citation string.

        Args:
            style: Citation style - "apa" (default) or "bibtex"

        Returns:
            Formatted citation string

        Example:
            >>> work.citation()  # APA format
            'Piwowar, H., & Priem, J. (2018). The state of OA. PeerJ.'
            >>> work.citation("bibtex")  # BibTeX format
            '@article{W2741809807, title={The state of OA}, ...}'
        """
        if style.lower() == "bibtex":
            return self._citation_bibtex()
        return self._citation_apa()

    def _citation_apa(self) -> str:
        """Format as APA citation."""
        parts = []

        # Authors
        if self.authors:
            if len(self.authors) == 1:
                parts.append(self._format_author_apa(self.authors[0]))
            elif len(self.authors) == 2:
                parts.append(
                    f"{self._format_author_apa(self.authors[0])} & "
                    f"{self._format_author_apa(self.authors[1])}"
                )
            else:
                formatted = [self._format_author_apa(a) for a in self.authors[:19]]
                if len(self.authors) > 20:
                    formatted = formatted[:19] + ["..."] + [
                        self._format_author_apa(self.authors[-1])
                    ]
                parts.append(", ".join(formatted[:-1]) + ", & " + formatted[-1])

        # Year
        if self.year:
            parts.append(f"({self.year})")

        # Title
        if self.title:
            parts.append(f"{self.title}.")

        # Source (journal)
        if self.source:
            source_part = f"*{self.source}*"
            if self.volume:
                source_part += f", *{self.volume}*"
                if self.issue:
                    source_part += f"({self.issue})"
            if self.pages:
                source_part += f", {self.pages}"
            source_part += "."
            parts.append(source_part)

        # DOI
        if self.doi:
            parts.append(f"https://doi.org/{self.doi}")

        return " ".join(parts)

    def _format_author_apa(self, name: str) -> str:
        """Format author name for APA (Last, F. M.)."""
        parts = name.split()
        if len(parts) == 1:
            return parts[0]
        last = parts[-1]
        initials = " ".join(f"{p[0]}." for p in parts[:-1] if p)
        return f"{last}, {initials}"

    def _citation_bibtex(self) -> str:
        """Format as BibTeX entry."""
        # Determine entry type
        entry_type = "article"
        if self.type:
            type_map = {
                "book": "book",
                "book-chapter": "incollection",
                "proceedings": "inproceedings",
                "proceedings-article": "inproceedings",
                "dissertation": "phdthesis",
                "report": "techreport",
            }
            entry_type = type_map.get(self.type, "article")

        # Use OpenAlex ID as citation key
        key = self.openalex_id or "unknown"

        lines = [f"@{entry_type}{{{key},"]

        if self.title:
            lines.append(f"  title = {{{self.title}}},")

        if self.authors:
            author_str = " and ".join(self.authors)
            lines.append(f"  author = {{{author_str}}},")

        if self.year:
            lines.append(f"  year = {{{self.year}}},")

        if self.source:
            if entry_type == "article":
                lines.append(f"  journal = {{{self.source}}},")
            elif entry_type in ("incollection", "inproceedings"):
                lines.append(f"  booktitle = {{{self.source}}},")

        if self.volume:
            lines.append(f"  volume = {{{self.volume}}},")

        if self.issue:
            lines.append(f"  number = {{{self.issue}}},")

        if self.pages:
            lines.append(f"  pages = {{{self.pages}}},")

        if self.publisher:
            lines.append(f"  publisher = {{{self.publisher}}},")

        if self.doi:
            lines.append(f"  doi = {{{self.doi}}},")

        if self.oa_url:
            lines.append(f"  url = {{{self.oa_url}}},")

        lines.append("}")

        return "\n".join(lines)


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
