"""Tests for openalex_local.models."""

import pytest

from openalex_local import Work, SearchResult


@pytest.fixture
def full_openalex_response():
    """Return a fully-populated OpenAlex API response dict."""
    return {
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


class TestWorkFromOpenalex:
    """Tests for Work.from_openalex parsing."""

    def test_from_openalex_parses_openalex_id(self, full_openalex_response):
        """Test from_openalex strips the URL prefix off the OpenAlex ID."""
        # Arrange
        data = full_openalex_response
        # Act
        work = Work.from_openalex(data)
        # Assert
        assert work.openalex_id == "W2741809807"

    def test_from_openalex_parses_doi(self, full_openalex_response):
        """Test from_openalex strips the URL prefix off the DOI."""
        # Arrange
        data = full_openalex_response
        # Act
        work = Work.from_openalex(data)
        # Assert
        assert work.doi == "10.7717/peerj.4375"

    def test_from_openalex_parses_title(self, full_openalex_response):
        """Test from_openalex copies the title verbatim."""
        # Arrange
        data = full_openalex_response
        # Act
        work = Work.from_openalex(data)
        # Assert
        assert work.title == "The state of OA"

    def test_from_openalex_parses_publication_year(self, full_openalex_response):
        """Test from_openalex maps publication_year onto year."""
        # Arrange
        data = full_openalex_response
        # Act
        work = Work.from_openalex(data)
        # Assert
        assert work.year == 2018

    def test_from_openalex_collects_all_authors(self, full_openalex_response):
        """Test from_openalex flattens every authorship display_name."""
        # Arrange
        data = full_openalex_response
        # Act
        work = Work.from_openalex(data)
        # Assert
        assert work.authors == ["Heather Piwowar", "Jason Priem"]

    def test_from_openalex_decodes_inverted_abstract(self, full_openalex_response):
        """Test from_openalex reconstructs the abstract from the inverted index."""
        # Arrange
        data = full_openalex_response
        # Act
        work = Work.from_openalex(data)
        # Assert
        assert work.abstract == "Despite growing interest"

    def test_from_openalex_parses_source_name(self, full_openalex_response):
        """Test from_openalex reads the primary location source name."""
        # Arrange
        data = full_openalex_response
        # Act
        work = Work.from_openalex(data)
        # Assert
        assert work.source == "PeerJ"

    def test_from_openalex_parses_first_issn(self, full_openalex_response):
        """Test from_openalex takes the first ISSN of the source."""
        # Arrange
        data = full_openalex_response
        # Act
        work = Work.from_openalex(data)
        # Assert
        assert work.issn == "2167-8359"

    def test_from_openalex_parses_cited_by_count(self, full_openalex_response):
        """Test from_openalex copies the cited_by_count."""
        # Arrange
        data = full_openalex_response
        # Act
        work = Work.from_openalex(data)
        # Assert
        assert work.cited_by_count == 500

    def test_from_openalex_parses_open_access_flag(self, full_openalex_response):
        """Test from_openalex reads the open_access is_oa flag."""
        # Arrange
        data = full_openalex_response
        # Act
        work = Work.from_openalex(data)
        # Assert
        assert work.is_oa is True

    def test_from_openalex_missing_doi_is_none(self):
        """Test from_openalex leaves doi None when absent."""
        # Arrange
        data = {"id": "https://openalex.org/W123", "title": "Test"}
        # Act
        work = Work.from_openalex(data)
        # Assert
        assert work.doi is None

    def test_from_openalex_missing_abstract_is_none(self):
        """Test from_openalex leaves abstract None when absent."""
        # Arrange
        data = {"id": "https://openalex.org/W123", "title": "Test"}
        # Act
        work = Work.from_openalex(data)
        # Assert
        assert work.abstract is None

    def test_from_openalex_missing_authors_is_empty(self):
        """Test from_openalex defaults authors to an empty list."""
        # Arrange
        data = {"id": "https://openalex.org/W123", "title": "Test"}
        # Act
        work = Work.from_openalex(data)
        # Assert
        assert work.authors == []


class TestWorkToDict:
    """Tests for Work.to_dict serialization."""

    @pytest.fixture
    def work(self):
        """Return a Work with fixed fields."""
        return Work(
            openalex_id="W123",
            doi="10.1234/test",
            title="Test Work",
            year=2024,
        )

    def test_to_dict_includes_openalex_id(self, work):
        """Test to_dict serializes the openalex_id field."""
        # Arrange
        source = work
        # Act
        result = source.to_dict()
        # Assert
        assert result["openalex_id"] == "W123"

    def test_to_dict_includes_doi(self, work):
        """Test to_dict serializes the doi field."""
        # Arrange
        source = work
        # Act
        result = source.to_dict()
        # Assert
        assert result["doi"] == "10.1234/test"

    def test_to_dict_includes_title(self, work):
        """Test to_dict serializes the title field."""
        # Arrange
        source = work
        # Act
        result = source.to_dict()
        # Assert
        assert result["title"] == "Test Work"

    def test_to_dict_includes_year(self, work):
        """Test to_dict serializes the year field."""
        # Arrange
        source = work
        # Act
        result = source.to_dict()
        # Assert
        assert result["year"] == 2024


class TestWorkCitationApa:
    """Tests for Work.citation() APA rendering."""

    @pytest.fixture
    def full_work(self):
        """Return a fully-populated Work for APA rendering."""
        return Work(
            openalex_id="W123",
            title="Test Article Title",
            authors=["John Smith", "Jane Doe"],
            year=2023,
            source="Nature",
            doi="10.1234/test",
        )

    def test_citation_apa_includes_first_author(self, full_work):
        """Test APA citation abbreviates the first author."""
        # Arrange
        work = full_work
        # Act
        citation = work.citation("apa")
        # Assert
        assert "Smith, J." in citation

    def test_citation_apa_includes_second_author(self, full_work):
        """Test APA citation abbreviates the second author."""
        # Arrange
        work = full_work
        # Act
        citation = work.citation("apa")
        # Assert
        assert "Doe, J." in citation

    def test_citation_apa_includes_year(self, full_work):
        """Test APA citation parenthesizes the year."""
        # Arrange
        work = full_work
        # Act
        citation = work.citation("apa")
        # Assert
        assert "(2023)" in citation

    def test_citation_apa_includes_title(self, full_work):
        """Test APA citation contains the article title."""
        # Arrange
        work = full_work
        # Act
        citation = work.citation("apa")
        # Assert
        assert "Test Article Title" in citation

    def test_citation_apa_italicizes_source(self, full_work):
        """Test APA citation italicizes the journal name."""
        # Arrange
        work = full_work
        # Act
        citation = work.citation("apa")
        # Assert
        assert "*Nature*" in citation

    def test_citation_apa_includes_doi_url(self, full_work):
        """Test APA citation renders the DOI as a URL."""
        # Arrange
        work = full_work
        # Act
        citation = work.citation("apa")
        # Assert
        assert "https://doi.org/10.1234/test" in citation

    def test_citation_apa_single_author_has_initial(self):
        """Test APA citation abbreviates a sole author."""
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
        assert "Brown, A." in citation

    def test_citation_apa_single_author_has_no_ampersand(self):
        """Test APA citation omits the ampersand for a sole author."""
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
        """Test APA citation joins two authors with an ampersand."""
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

    def test_citation_apa_many_authors_use_serial_ampersand(self):
        """Test APA citation precedes the final author with a serial ampersand."""
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

    def test_citation_apa_includes_italic_volume(self):
        """Test APA citation italicizes the volume number."""
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

    def test_citation_apa_includes_issue_in_parens(self):
        """Test APA citation parenthesizes the issue number."""
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

    def test_citation_apa_includes_page_range(self):
        """Test APA citation contains the page range."""
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

    def test_citation_apa_tolerates_empty_author_name(self):
        """Test APA citation does not crash on a blank author name."""
        # Arrange
        work = Work(
            openalex_id="W123",
            title="Sparse Metadata Work",
            authors=["", "Jane Doe"],
            year=2023,
        )
        # Act
        citation = work.citation("apa")
        # Assert
        assert "Doe, J." in citation


class TestWorkCitationBibtex:
    """Tests for Work.citation() BibTeX rendering."""

    @pytest.fixture
    def article_work(self):
        """Return a journal-article Work for BibTeX rendering."""
        return Work(
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

    def test_citation_bibtex_article_uses_article_entry(self, article_work):
        """Test BibTeX renders journal articles as @article."""
        # Arrange
        work = article_work
        # Act
        bibtex = work.citation("bibtex")
        # Assert
        assert "@article{W2741809807," in bibtex

    def test_citation_bibtex_article_includes_title(self, article_work):
        """Test BibTeX article entry contains the title field."""
        # Arrange
        work = article_work
        # Act
        bibtex = work.citation("bibtex")
        # Assert
        assert "title = {The state of OA}" in bibtex

    def test_citation_bibtex_article_joins_authors_with_and(self, article_work):
        """Test BibTeX article entry joins authors with `and`."""
        # Arrange
        work = article_work
        # Act
        bibtex = work.citation("bibtex")
        # Assert
        assert "author = {Heather Piwowar and Jason Priem}" in bibtex

    def test_citation_bibtex_article_includes_year(self, article_work):
        """Test BibTeX article entry contains the year field."""
        # Arrange
        work = article_work
        # Act
        bibtex = work.citation("bibtex")
        # Assert
        assert "year = {2018}" in bibtex

    def test_citation_bibtex_article_includes_journal(self, article_work):
        """Test BibTeX article entry contains the journal field."""
        # Arrange
        work = article_work
        # Act
        bibtex = work.citation("bibtex")
        # Assert
        assert "journal = {PeerJ}" in bibtex

    def test_citation_bibtex_article_includes_doi(self, article_work):
        """Test BibTeX article entry contains the doi field."""
        # Arrange
        work = article_work
        # Act
        bibtex = work.citation("bibtex")
        # Assert
        assert "doi = {10.7717/peerj.4375}" in bibtex

    def test_citation_bibtex_book_uses_book_entry(self):
        """Test BibTeX renders books as @book."""
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
        """Test BibTeX book entry contains the publisher field."""
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

    def test_citation_bibtex_proceedings_uses_inproceedings_entry(self):
        """Test BibTeX renders proceedings as @inproceedings."""
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
        """Test BibTeX proceedings entry contains the booktitle field."""
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


class TestWorkCitationStyles:
    """Tests for Work.citation() style selection."""

    def test_citation_default_style_matches_apa(self):
        """Test citation defaults to APA when no style is given."""
        # Arrange
        work = Work(openalex_id="W123", title="Test", year=2023)
        # Act
        default = work.citation()
        # Assert
        assert default == work.citation("apa")

    def test_citation_bibtex_style_is_case_insensitive(self):
        """Test citation accepts the BibTeX style in upper case."""
        # Arrange
        work = Work(openalex_id="W123", title="Test", year=2023)
        # Act
        upper = work.citation("BIBTEX")
        # Assert
        assert upper == work.citation("bibtex")

    def test_citation_apa_style_is_case_insensitive(self):
        """Test citation accepts the APA style in upper case."""
        # Arrange
        work = Work(openalex_id="W123", title="Test", year=2023)
        # Act
        upper = work.citation("APA")
        # Assert
        assert upper == work.citation("apa")

    def test_citation_apa_minimal_returns_string(self):
        """Test APA citation of a bare Work returns a string."""
        # Arrange
        work = Work(openalex_id="W123")
        # Act
        apa = work.citation("apa")
        # Assert
        assert isinstance(apa, str)

    def test_citation_bibtex_minimal_returns_string(self):
        """Test BibTeX citation of a bare Work returns a string."""
        # Arrange
        work = Work(openalex_id="W123")
        # Act
        bibtex = work.citation("bibtex")
        # Assert
        assert isinstance(bibtex, str)

    def test_citation_bibtex_minimal_has_entry_marker(self):
        """Test BibTeX citation of a bare Work keeps its `@` entry marker."""
        # Arrange
        work = Work(openalex_id="W123")
        # Act
        bibtex = work.citation("bibtex")
        # Assert
        assert "@" in bibtex


class TestSearchResult:
    """Tests for SearchResult model."""

    @pytest.fixture
    def two_work_result(self):
        """Return a SearchResult wrapping two Works."""
        works = [
            Work(openalex_id="W1", title="Work 1"),
            Work(openalex_id="W2", title="Work 2"),
        ]
        return SearchResult(works=works, total=100, query="test", elapsed_ms=10.0)

    def test_search_result_len_counts_works(self, two_work_result):
        """Test SearchResult length reflects the number of works."""
        # Arrange
        result = two_work_result
        # Act
        length = len(result)
        # Assert
        assert length == 2

    def test_search_result_getitem_returns_work(self, two_work_result):
        """Test SearchResult indexing returns the work at that position."""
        # Arrange
        result = two_work_result
        # Act
        first = result[0]
        # Assert
        assert first.openalex_id == "W1"

    def test_search_result_iterates_over_works(self, two_work_result):
        """Test SearchResult iteration yields the wrapped works."""
        # Arrange
        result = two_work_result
        # Act
        listed = list(result)
        # Assert
        assert [w.openalex_id for w in listed] == ["W1", "W2"]
