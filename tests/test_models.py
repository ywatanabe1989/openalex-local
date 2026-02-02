"""Tests for openalex_local.models."""

from openalex_local import Work, SearchResult


class TestWork:
    """Tests for Work model."""

    def test_from_openalex_basic(self):
        """Test creating Work from OpenAlex API response."""
        data = {
            "id": "https://openalex.org/W2741809807",
            "doi": "https://doi.org/10.7717/peerj.4375",
            "title": "The state of OA",
            "publication_year": 2018,
            "authorships": [
                {"author": {"display_name": "Heather Piwowar"}},
                {"author": {"display_name": "Jason Priem"}},
            ],
            "abstract_inverted_index": {
                "Despite": [0],
                "growing": [1],
                "interest": [2],
            },
            "primary_location": {
                "source": {
                    "display_name": "PeerJ",
                    "issn": ["2167-8359"],
                }
            },
            "cited_by_count": 500,
            "open_access": {
                "is_oa": True,
                "oa_url": "https://peerj.com/articles/4375/",
            },
        }

        work = Work.from_openalex(data)

        assert work.openalex_id == "W2741809807"
        assert work.doi == "10.7717/peerj.4375"
        assert work.title == "The state of OA"
        assert work.year == 2018
        assert len(work.authors) == 2
        assert "Heather Piwowar" in work.authors
        assert work.abstract == "Despite growing interest"
        assert work.source == "PeerJ"
        assert work.issn == "2167-8359"
        assert work.cited_by_count == 500
        assert work.is_oa is True

    def test_from_openalex_missing_fields(self):
        """Test Work with minimal data."""
        data = {
            "id": "https://openalex.org/W123",
            "title": "Test",
        }

        work = Work.from_openalex(data)

        assert work.openalex_id == "W123"
        assert work.doi is None
        assert work.abstract is None
        assert work.authors == []

    def test_to_dict(self):
        """Test Work serialization."""
        work = Work(
            openalex_id="W123",
            doi="10.1234/test",
            title="Test Work",
            year=2024,
        )

        d = work.to_dict()

        assert d["openalex_id"] == "W123"
        assert d["doi"] == "10.1234/test"
        assert d["title"] == "Test Work"
        assert d["year"] == 2024


class TestWorkCitation:
    """Tests for Work.citation() method."""

    def test_citation_apa_basic(self):
        """Test APA citation with basic fields."""
        work = Work(
            openalex_id="W123",
            title="Test Article Title",
            authors=["John Smith", "Jane Doe"],
            year=2023,
            source="Nature",
            doi="10.1234/test",
        )
        citation = work.citation("apa")
        assert "Smith, J." in citation
        assert "Doe, J." in citation
        assert "(2023)" in citation
        assert "Test Article Title" in citation
        assert "*Nature*" in citation
        assert "https://doi.org/10.1234/test" in citation

    def test_citation_apa_single_author(self):
        """Test APA citation with single author."""
        work = Work(
            openalex_id="W123",
            title="Solo Work",
            authors=["Alice Brown"],
            year=2022,
        )
        citation = work.citation("apa")
        assert "Brown, A." in citation
        assert "&" not in citation

    def test_citation_apa_two_authors(self):
        """Test APA citation with two authors."""
        work = Work(
            openalex_id="W123",
            title="Dual Work",
            authors=["Alice Brown", "Bob White"],
            year=2022,
        )
        citation = work.citation("apa")
        assert "Brown, A. & White, B." in citation

    def test_citation_apa_many_authors(self):
        """Test APA citation with many authors."""
        work = Work(
            openalex_id="W123",
            title="Group Work",
            authors=["Author One", "Author Two", "Author Three"],
            year=2022,
        )
        citation = work.citation("apa")
        assert ", & " in citation  # Final author preceded by &

    def test_citation_apa_with_volume_issue(self):
        """Test APA citation with volume and issue."""
        work = Work(
            openalex_id="W123",
            title="Journal Article",
            authors=["Test Author"],
            year=2023,
            source="Test Journal",
            volume="10",
            issue="2",
            pages="100-110",
        )
        citation = work.citation("apa")
        assert "*Test Journal*" in citation
        assert "*10*" in citation
        assert "(2)" in citation
        assert "100-110" in citation

    def test_citation_bibtex_article(self):
        """Test BibTeX citation for article."""
        work = Work(
            openalex_id="W2741809807",
            title="The state of OA",
            authors=["Heather Piwowar", "Jason Priem"],
            year=2018,
            source="PeerJ",
            volume="6",
            pages="e4375",
            doi="10.7717/peerj.4375",
            type="journal-article",
        )
        bibtex = work.citation("bibtex")
        assert "@article{W2741809807," in bibtex
        assert "title = {The state of OA}" in bibtex
        assert "author = {Heather Piwowar and Jason Priem}" in bibtex
        assert "year = {2018}" in bibtex
        assert "journal = {PeerJ}" in bibtex
        assert "doi = {10.7717/peerj.4375}" in bibtex

    def test_citation_bibtex_book(self):
        """Test BibTeX citation for book."""
        work = Work(
            openalex_id="W123",
            title="Test Book",
            authors=["Test Author"],
            year=2023,
            publisher="Test Publisher",
            type="book",
        )
        bibtex = work.citation("bibtex")
        assert "@book{W123," in bibtex
        assert "publisher = {Test Publisher}" in bibtex

    def test_citation_bibtex_inproceedings(self):
        """Test BibTeX citation for proceedings."""
        work = Work(
            openalex_id="W123",
            title="Conference Paper",
            authors=["Conference Author"],
            year=2023,
            source="Conference Proceedings",
            type="proceedings-article",
        )
        bibtex = work.citation("bibtex")
        assert "@inproceedings{W123," in bibtex
        assert "booktitle = {Conference Proceedings}" in bibtex

    def test_citation_default_is_apa(self):
        """Test default citation style is APA."""
        work = Work(openalex_id="W123", title="Test", year=2023)
        assert work.citation() == work.citation("apa")

    def test_citation_style_case_insensitive(self):
        """Test citation style is case insensitive."""
        work = Work(openalex_id="W123", title="Test", year=2023)
        assert work.citation("BIBTEX") == work.citation("bibtex")
        assert work.citation("APA") == work.citation("apa")

    def test_citation_minimal_fields(self):
        """Test citation with minimal fields doesn't crash."""
        work = Work(openalex_id="W123")
        apa = work.citation("apa")
        bibtex = work.citation("bibtex")
        assert isinstance(apa, str)
        assert isinstance(bibtex, str)
        assert "@" in bibtex  # Should have BibTeX structure


class TestSearchResult:
    """Tests for SearchResult model."""

    def test_search_result_iteration(self):
        """Test SearchResult is iterable."""
        works = [
            Work(openalex_id="W1", title="Work 1"),
            Work(openalex_id="W2", title="Work 2"),
        ]
        result = SearchResult(works=works, total=100, query="test", elapsed_ms=10.0)

        assert len(result) == 2
        assert result[0].openalex_id == "W1"
        assert list(result) == works
