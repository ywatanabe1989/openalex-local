"""Tests for openalex_local.models."""

import pytest

from openalex_local import Work, SearchResult


@pytest.mark.unit
class TestWork:
    """Tests for Work model."""

    def test_from_openalex_sets_openalex_id(self):
        """Test creating Work from OpenAlex API response sets ID."""
        # Arrange
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
        # Act
        work = Work.from_openalex(data)
        # Assert
        assert work.openalex_id == "W2741809807"

    def test_from_openalex_strips_doi_prefix(self):
        """Test from_openalex strips https://doi.org/ prefix."""
        # Arrange
        data = {
            "id": "https://openalex.org/W2741809807",
            "doi": "https://doi.org/10.7717/peerj.4375",
            "title": "The state of OA",
        }
        # Act
        work = Work.from_openalex(data)
        # Assert
        assert work.doi == "10.7717/peerj.4375"

    def test_from_openalex_sets_title(self):
        """Test from_openalex sets title."""
        # Arrange
        data = {"id": "https://openalex.org/W1", "title": "The state of OA"}
        # Act
        work = Work.from_openalex(data)
        # Assert
        assert work.title == "The state of OA"

    def test_from_openalex_sets_publication_year(self):
        """Test from_openalex sets publication year."""
        # Arrange
        data = {
            "id": "https://openalex.org/W1",
            "title": "Test",
            "publication_year": 2018,
        }
        # Act
        work = Work.from_openalex(data)
        # Assert
        assert work.year == 2018

    def test_from_openalex_extracts_author_count(self):
        """Test from_openalex extracts correct number of authors."""
        # Arrange
        data = {
            "id": "https://openalex.org/W1",
            "title": "Test",
            "authorships": [
                {"author": {"display_name": "Heather Piwowar"}},
                {"author": {"display_name": "Jason Priem"}},
            ],
        }
        # Act
        work = Work.from_openalex(data)
        # Assert
        assert len(work.authors) == 2

    def test_from_openalex_includes_author_names(self):
        """Test from_openalex includes author display names."""
        # Arrange
        data = {
            "id": "https://openalex.org/W1",
            "title": "Test",
            "authorships": [
                {"author": {"display_name": "Heather Piwowar"}},
                {"author": {"display_name": "Jason Priem"}},
            ],
        }
        # Act
        work = Work.from_openalex(data)
        # Assert
        assert "Heather Piwowar" in work.authors

    def test_from_openalex_reconstructs_abstract(self):
        """Test from_openalex reconstructs abstract from inverted index."""
        # Arrange
        data = {
            "id": "https://openalex.org/W1",
            "title": "Test",
            "abstract_inverted_index": {
                "Despite": [0],
                "growing": [1],
                "interest": [2],
            },
        }
        # Act
        work = Work.from_openalex(data)
        # Assert
        assert work.abstract == "Despite growing interest"

    def test_from_openalex_extracts_source_name(self):
        """Test from_openalex extracts source display name."""
        # Arrange
        data = {
            "id": "https://openalex.org/W1",
            "title": "Test",
            "primary_location": {
                "source": {"display_name": "PeerJ", "issn": ["2167-8359"]}
            },
        }
        # Act
        work = Work.from_openalex(data)
        # Assert
        assert work.source == "PeerJ"

    def test_from_openalex_extracts_issn(self):
        """Test from_openalex extracts ISSN."""
        # Arrange
        data = {
            "id": "https://openalex.org/W1",
            "title": "Test",
            "primary_location": {
                "source": {"display_name": "PeerJ", "issn": ["2167-8359"]}
            },
        }
        # Act
        work = Work.from_openalex(data)
        # Assert
        assert work.issn == "2167-8359"

    def test_from_openalex_sets_cited_by_count(self):
        """Test from_openalex sets cited_by_count."""
        # Arrange
        data = {
            "id": "https://openalex.org/W1",
            "title": "Test",
            "cited_by_count": 500,
        }
        # Act
        work = Work.from_openalex(data)
        # Assert
        assert work.cited_by_count == 500

    def test_from_openalex_sets_open_access_flag(self):
        """Test from_openalex sets is_oa flag."""
        # Arrange
        data = {
            "id": "https://openalex.org/W1",
            "title": "Test",
            "open_access": {"is_oa": True, "oa_url": "https://example.com"},
        }
        # Act
        work = Work.from_openalex(data)
        # Assert
        assert work.is_oa is True

    def test_from_openalex_missing_fields_sets_none_doi(self):
        """Test Work with minimal data sets doi to None."""
        # Arrange
        data = {"id": "https://openalex.org/W123", "title": "Test"}
        # Act
        work = Work.from_openalex(data)
        # Assert
        assert work.doi is None

    def test_from_openalex_missing_fields_sets_none_abstract(self):
        """Test Work with minimal data sets abstract to None."""
        # Arrange
        data = {"id": "https://openalex.org/W123", "title": "Test"}
        # Act
        work = Work.from_openalex(data)
        # Assert
        assert work.abstract is None

    def test_from_openalex_missing_fields_sets_empty_authors(self):
        """Test Work with minimal data sets authors to empty list."""
        # Arrange
        data = {"id": "https://openalex.org/W123", "title": "Test"}
        # Act
        work = Work.from_openalex(data)
        # Assert
        assert work.authors == []

    def test_to_dict_contains_openalex_id(self):
        """Test Work serialization includes openalex_id."""
        # Arrange
        work = Work(
            openalex_id="W123", doi="10.1234/test", title="Test Work", year=2024
        )
        # Act
        d = work.to_dict()
        # Assert
        assert d["openalex_id"] == "W123"

    def test_to_dict_contains_doi(self):
        """Test Work serialization includes doi."""
        # Arrange
        work = Work(
            openalex_id="W123", doi="10.1234/test", title="Test Work", year=2024
        )
        # Act
        d = work.to_dict()
        # Assert
        assert d["doi"] == "10.1234/test"

    def test_to_dict_contains_title(self):
        """Test Work serialization includes title."""
        # Arrange
        work = Work(
            openalex_id="W123", doi="10.1234/test", title="Test Work", year=2024
        )
        # Act
        d = work.to_dict()
        # Assert
        assert d["title"] == "Test Work"

    def test_to_dict_contains_year(self):
        """Test Work serialization includes year."""
        # Arrange
        work = Work(
            openalex_id="W123", doi="10.1234/test", title="Test Work", year=2024
        )
        # Act
        d = work.to_dict()
        # Assert
        assert d["year"] == 2024


@pytest.mark.unit
class TestWorkCitation:
    """Tests for Work.citation() method."""

    def test_citation_apa_includes_first_author_lastname(self):
        """Test APA citation includes first author last name."""
        # Arrange
        work = Work(
            openalex_id="W123",
            title="Test Article Title",
            authors=["John Smith", "Jane Doe"],
            year=2023,
            source="Nature",
            doi="10.1234/test",
        )
        # Act
        citation = work.citation("apa")
        # Assert
        assert "Smith, J." in citation

    def test_citation_apa_includes_second_author_lastname(self):
        """Test APA citation includes second author last name."""
        # Arrange
        work = Work(
            openalex_id="W123",
            title="Test Article Title",
            authors=["John Smith", "Jane Doe"],
            year=2023,
            source="Nature",
            doi="10.1234/test",
        )
        # Act
        citation = work.citation("apa")
        # Assert
        assert "Doe, J." in citation

    def test_citation_apa_includes_year(self):
        """Test APA citation includes publication year."""
        # Arrange
        work = Work(
            openalex_id="W123",
            title="Test Article Title",
            authors=["John Smith"],
            year=2023,
            source="Nature",
            doi="10.1234/test",
        )
        # Act
        citation = work.citation("apa")
        # Assert
        assert "(2023)" in citation

    def test_citation_apa_includes_title(self):
        """Test APA citation includes article title."""
        # Arrange
        work = Work(
            openalex_id="W123",
            title="Test Article Title",
            authors=["John Smith"],
            year=2023,
            source="Nature",
            doi="10.1234/test",
        )
        # Act
        citation = work.citation("apa")
        # Assert
        assert "Test Article Title" in citation

    def test_citation_apa_includes_source_in_italics(self):
        """Test APA citation includes source name in italics."""
        # Arrange
        work = Work(
            openalex_id="W123",
            title="Test Article Title",
            authors=["John Smith"],
            year=2023,
            source="Nature",
            doi="10.1234/test",
        )
        # Act
        citation = work.citation("apa")
        # Assert
        assert "*Nature*" in citation

    def test_citation_apa_includes_doi_url(self):
        """Test APA citation includes DOI URL."""
        # Arrange
        work = Work(
            openalex_id="W123",
            title="Test Article Title",
            authors=["John Smith"],
            year=2023,
            source="Nature",
            doi="10.1234/test",
        )
        # Act
        citation = work.citation("apa")
        # Assert
        assert "https://doi.org/10.1234/test" in citation

    def test_citation_apa_single_author_excludes_ampersand(self):
        """Test APA citation with single author has no ampersand."""
        # Arrange
        work = Work(
            openalex_id="W123",
            title="Solo Work",
            authors=["Alice Brown"],
            year=2022,
        )
        # Act
        citation = work.citation("apa")
        # Assert
        assert "&" not in citation

    def test_citation_apa_two_authors_joined_by_ampersand(self):
        """Test APA citation with two authors joined by ampersand."""
        # Arrange
        work = Work(
            openalex_id="W123",
            title="Dual Work",
            authors=["Alice Brown", "Bob White"],
            year=2022,
        )
        # Act
        citation = work.citation("apa")
        # Assert
        assert "Brown, A. & White, B." in citation

    def test_citation_apa_many_authors_uses_comma_ampersand(self):
        """Test APA citation with many authors uses comma before ampersand."""
        # Arrange
        work = Work(
            openalex_id="W123",
            title="Group Work",
            authors=["Author One", "Author Two", "Author Three"],
            year=2022,
        )
        # Act
        citation = work.citation("apa")
        # Assert
        assert ", & " in citation

    def test_citation_apa_includes_volume(self):
        """Test APA citation includes volume number."""
        # Arrange
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
        # Act
        citation = work.citation("apa")
        # Assert
        assert "*10*" in citation

    def test_citation_apa_includes_issue(self):
        """Test APA citation includes issue number."""
        # Arrange
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
        # Act
        citation = work.citation("apa")
        # Assert
        assert "(2)" in citation

    def test_citation_apa_includes_pages(self):
        """Test APA citation includes page range."""
        # Arrange
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
        # Act
        citation = work.citation("apa")
        # Assert
        assert "100-110" in citation

    def test_citation_bibtex_article_entry_type(self):
        """Test BibTeX citation uses @article for journal articles."""
        # Arrange
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
        # Act
        bibtex = work.citation("bibtex")
        # Assert
        assert "@article{W2741809807," in bibtex

    def test_citation_bibtex_article_includes_title(self):
        """Test BibTeX article citation includes title field."""
        # Arrange
        work = Work(
            openalex_id="W2741809807",
            title="The state of OA",
            authors=["Heather Piwowar", "Jason Priem"],
            year=2018,
            source="PeerJ",
            doi="10.7717/peerj.4375",
            type="journal-article",
        )
        # Act
        bibtex = work.citation("bibtex")
        # Assert
        assert "title = {The state of OA}" in bibtex

    def test_citation_bibtex_article_includes_authors(self):
        """Test BibTeX article citation includes author field."""
        # Arrange
        work = Work(
            openalex_id="W2741809807",
            title="The state of OA",
            authors=["Heather Piwowar", "Jason Priem"],
            year=2018,
            source="PeerJ",
            doi="10.7717/peerj.4375",
            type="journal-article",
        )
        # Act
        bibtex = work.citation("bibtex")
        # Assert
        assert "author = {Heather Piwowar and Jason Priem}" in bibtex

    def test_citation_bibtex_article_includes_year(self):
        """Test BibTeX article citation includes year field."""
        # Arrange
        work = Work(
            openalex_id="W2741809807",
            title="The state of OA",
            authors=["Heather Piwowar"],
            year=2018,
            source="PeerJ",
            doi="10.7717/peerj.4375",
            type="journal-article",
        )
        # Act
        bibtex = work.citation("bibtex")
        # Assert
        assert "year = {2018}" in bibtex

    def test_citation_bibtex_article_includes_journal(self):
        """Test BibTeX article citation includes journal field."""
        # Arrange
        work = Work(
            openalex_id="W2741809807",
            title="The state of OA",
            authors=["Heather Piwowar"],
            year=2018,
            source="PeerJ",
            doi="10.7717/peerj.4375",
            type="journal-article",
        )
        # Act
        bibtex = work.citation("bibtex")
        # Assert
        assert "journal = {PeerJ}" in bibtex

    def test_citation_bibtex_article_includes_doi(self):
        """Test BibTeX article citation includes doi field."""
        # Arrange
        work = Work(
            openalex_id="W2741809807",
            title="The state of OA",
            authors=["Heather Piwowar"],
            year=2018,
            source="PeerJ",
            doi="10.7717/peerj.4375",
            type="journal-article",
        )
        # Act
        bibtex = work.citation("bibtex")
        # Assert
        assert "doi = {10.7717/peerj.4375}" in bibtex

    def test_citation_bibtex_book_uses_book_entry(self):
        """Test BibTeX citation uses @book for book type."""
        # Arrange
        work = Work(
            openalex_id="W123",
            title="Test Book",
            authors=["Test Author"],
            year=2023,
            publisher="Test Publisher",
            type="book",
        )
        # Act
        bibtex = work.citation("bibtex")
        # Assert
        assert "@book{W123," in bibtex

    def test_citation_bibtex_book_includes_publisher(self):
        """Test BibTeX book citation includes publisher."""
        # Arrange
        work = Work(
            openalex_id="W123",
            title="Test Book",
            authors=["Test Author"],
            year=2023,
            publisher="Test Publisher",
            type="book",
        )
        # Act
        bibtex = work.citation("bibtex")
        # Assert
        assert "publisher = {Test Publisher}" in bibtex

    def test_citation_bibtex_proceedings_uses_inproceedings(self):
        """Test BibTeX citation uses @inproceedings for proceedings."""
        # Arrange
        work = Work(
            openalex_id="W123",
            title="Conference Paper",
            authors=["Conference Author"],
            year=2023,
            source="Conference Proceedings",
            type="proceedings-article",
        )
        # Act
        bibtex = work.citation("bibtex")
        # Assert
        assert "@inproceedings{W123," in bibtex

    def test_citation_bibtex_proceedings_includes_booktitle(self):
        """Test BibTeX proceedings citation includes booktitle."""
        # Arrange
        work = Work(
            openalex_id="W123",
            title="Conference Paper",
            authors=["Conference Author"],
            year=2023,
            source="Conference Proceedings",
            type="proceedings-article",
        )
        # Act
        bibtex = work.citation("bibtex")
        # Assert
        assert "booktitle = {Conference Proceedings}" in bibtex

    def test_citation_default_matches_explicit_apa(self):
        """Test default citation style is APA."""
        # Arrange
        work = Work(openalex_id="W123", title="Test", year=2023)
        # Act
        default = work.citation()
        apa = work.citation("apa")
        # Assert
        assert default == apa

    def test_citation_uppercase_bibtex_matches_lowercase(self):
        """Test BIBTEX matches bibtex output."""
        # Arrange
        work = Work(openalex_id="W123", title="Test", year=2023)
        # Act
        upper = work.citation("BIBTEX")
        lower = work.citation("bibtex")
        # Assert
        assert upper == lower

    def test_citation_uppercase_apa_matches_lowercase(self):
        """Test APA matches apa output."""
        # Arrange
        work = Work(openalex_id="W123", title="Test", year=2023)
        # Act
        upper = work.citation("APA")
        lower = work.citation("apa")
        # Assert
        assert upper == lower

    def test_citation_apa_minimal_returns_string(self):
        """Test APA citation with minimal fields returns string."""
        # Arrange
        work = Work(openalex_id="W123")
        # Act
        apa = work.citation("apa")
        # Assert
        assert isinstance(apa, str)

    def test_citation_bibtex_minimal_has_at_symbol(self):
        """Test BibTeX citation with minimal fields has @ symbol."""
        # Arrange
        work = Work(openalex_id="W123")
        # Act
        bibtex = work.citation("bibtex")
        # Assert
        assert "@" in bibtex


@pytest.mark.unit
class TestSearchResult:
    """Tests for SearchResult model."""

    def test_search_result_len_returns_two(self):
        """Test SearchResult len returns correct count."""
        # Arrange
        works = [
            Work(openalex_id="W1", title="Work 1"),
            Work(openalex_id="W2", title="Work 2"),
        ]
        result = SearchResult(works=works, total=100, query="test", elapsed_ms=10.0)
        # Act
        length = len(result)
        # Assert
        assert length == 2

    def test_search_result_first_item_has_correct_id(self):
        """Test SearchResult first item has correct openalex_id."""
        # Arrange
        works = [
            Work(openalex_id="W1", title="Work 1"),
            Work(openalex_id="W2", title="Work 2"),
        ]
        result = SearchResult(works=works, total=100, query="test", elapsed_ms=10.0)
        # Act
        first = result[0]
        # Assert
        assert first.openalex_id == "W1"

    def test_search_result_iter_matches_original_works(self):
        """Test SearchResult iteration yields original works."""
        # Arrange
        works = [
            Work(openalex_id="W1", title="Work 1"),
            Work(openalex_id="W2", title="Work 2"),
        ]
        result = SearchResult(works=works, total=100, query="test", elapsed_ms=10.0)
        # Act
        items = list(result)
        # Assert
        assert items == works
