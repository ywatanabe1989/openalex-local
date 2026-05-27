"""Tests for openalex_local.models."""

import pytest

from openalex_local import Work, SearchResult


# ---------------------------------------------------------------------------
# Work.from_openalex
# ---------------------------------------------------------------------------

@pytest.fixture
def openalex_basic_payload():
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


@pytest.fixture
def basic_work_from_payload(openalex_basic_payload):
    return Work.from_openalex(openalex_basic_payload)


def test_from_openalex_basic_extracts_openalex_id(basic_work_from_payload):
    # Arrange
    work = basic_work_from_payload
    # Act
    value = work.openalex_id
    # Assert
    assert value == "W2741809807"


def test_from_openalex_basic_strips_doi_url_prefix(basic_work_from_payload):
    # Arrange
    work = basic_work_from_payload
    # Act
    value = work.doi
    # Assert
    assert value == "10.7717/peerj.4375"


def test_from_openalex_basic_extracts_title(basic_work_from_payload):
    # Arrange
    work = basic_work_from_payload
    # Act
    value = work.title
    # Assert
    assert value == "The state of OA"


def test_from_openalex_basic_extracts_publication_year(basic_work_from_payload):
    # Arrange
    work = basic_work_from_payload
    # Act
    value = work.year
    # Assert
    assert value == 2018


def test_from_openalex_basic_extracts_two_authors(basic_work_from_payload):
    # Arrange
    work = basic_work_from_payload
    # Act
    count = len(work.authors)
    # Assert
    assert count == 2


def test_from_openalex_basic_contains_first_author(basic_work_from_payload):
    # Arrange
    work = basic_work_from_payload
    # Act
    names = work.authors
    # Assert
    assert "Heather Piwowar" in names


def test_from_openalex_basic_reconstructs_abstract_from_inverted_index(
    basic_work_from_payload,
):
    # Arrange
    work = basic_work_from_payload
    # Act
    value = work.abstract
    # Assert
    assert value == "Despite growing interest"


def test_from_openalex_basic_extracts_source_display_name(basic_work_from_payload):
    # Arrange
    work = basic_work_from_payload
    # Act
    value = work.source
    # Assert
    assert value == "PeerJ"


def test_from_openalex_basic_extracts_issn(basic_work_from_payload):
    # Arrange
    work = basic_work_from_payload
    # Act
    value = work.issn
    # Assert
    assert value == "2167-8359"


def test_from_openalex_basic_extracts_cited_by_count(basic_work_from_payload):
    # Arrange
    work = basic_work_from_payload
    # Act
    value = work.cited_by_count
    # Assert
    assert value == 500


def test_from_openalex_basic_flags_open_access_true(basic_work_from_payload):
    # Arrange
    work = basic_work_from_payload
    # Act
    value = work.is_oa
    # Assert
    assert value is True


@pytest.fixture
def minimal_work_from_payload():
    payload = {
        "id": "https://openalex.org/W123",
        "title": "Test",
    }
    return Work.from_openalex(payload)


def test_from_openalex_minimal_extracts_openalex_id(minimal_work_from_payload):
    # Arrange
    work = minimal_work_from_payload
    # Act
    value = work.openalex_id
    # Assert
    assert value == "W123"


def test_from_openalex_minimal_defaults_doi_to_none(minimal_work_from_payload):
    # Arrange
    work = minimal_work_from_payload
    # Act
    value = work.doi
    # Assert
    assert value is None


def test_from_openalex_minimal_defaults_abstract_to_none(minimal_work_from_payload):
    # Arrange
    work = minimal_work_from_payload
    # Act
    value = work.abstract
    # Assert
    assert value is None


def test_from_openalex_minimal_defaults_authors_to_empty_list(
    minimal_work_from_payload,
):
    # Arrange
    work = minimal_work_from_payload
    # Act
    value = work.authors
    # Assert
    assert value == []


# ---------------------------------------------------------------------------
# Work.to_dict
# ---------------------------------------------------------------------------

@pytest.fixture
def work_for_serialization():
    return Work(
        openalex_id="W123",
        doi="10.1234/test",
        title="Test Work",
        year=2024,
    )


def test_to_dict_serializes_openalex_id(work_for_serialization):
    # Arrange
    work = work_for_serialization
    # Act
    d = work.to_dict()
    # Assert
    assert d["openalex_id"] == "W123"


def test_to_dict_serializes_doi(work_for_serialization):
    # Arrange
    work = work_for_serialization
    # Act
    d = work.to_dict()
    # Assert
    assert d["doi"] == "10.1234/test"


def test_to_dict_serializes_title(work_for_serialization):
    # Arrange
    work = work_for_serialization
    # Act
    d = work.to_dict()
    # Assert
    assert d["title"] == "Test Work"


def test_to_dict_serializes_year(work_for_serialization):
    # Arrange
    work = work_for_serialization
    # Act
    d = work.to_dict()
    # Assert
    assert d["year"] == 2024


# ---------------------------------------------------------------------------
# Work.citation — APA
# ---------------------------------------------------------------------------

@pytest.fixture
def apa_basic_citation():
    work = Work(
        openalex_id="W123",
        title="Test Article Title",
        authors=["John Smith", "Jane Doe"],
        year=2023,
        source="Nature",
        doi="10.1234/test",
    )
    return work.citation("apa")


def test_citation_apa_basic_includes_first_author(apa_basic_citation):
    # Arrange
    citation = apa_basic_citation
    # Act
    contains = "Smith, J." in citation
    # Assert
    assert contains


def test_citation_apa_basic_includes_second_author(apa_basic_citation):
    # Arrange
    citation = apa_basic_citation
    # Act
    contains = "Doe, J." in citation
    # Assert
    assert contains


def test_citation_apa_basic_includes_publication_year(apa_basic_citation):
    # Arrange
    citation = apa_basic_citation
    # Act
    contains = "(2023)" in citation
    # Assert
    assert contains


def test_citation_apa_basic_includes_article_title(apa_basic_citation):
    # Arrange
    citation = apa_basic_citation
    # Act
    contains = "Test Article Title" in citation
    # Assert
    assert contains


def test_citation_apa_basic_italicizes_source(apa_basic_citation):
    # Arrange
    citation = apa_basic_citation
    # Act
    contains = "*Nature*" in citation
    # Assert
    assert contains


def test_citation_apa_basic_includes_doi_url(apa_basic_citation):
    # Arrange
    citation = apa_basic_citation
    # Act
    contains = "https://doi.org/10.1234/test" in citation
    # Assert
    assert contains


@pytest.fixture
def apa_single_author_citation():
    work = Work(
        openalex_id="W123",
        title="Solo Work",
        authors=["Alice Brown"],
        year=2022,
    )
    return work.citation("apa")


def test_citation_apa_single_author_includes_initial(apa_single_author_citation):
    # Arrange
    citation = apa_single_author_citation
    # Act
    contains = "Brown, A." in citation
    # Assert
    assert contains


def test_citation_apa_single_author_omits_ampersand(apa_single_author_citation):
    # Arrange
    citation = apa_single_author_citation
    # Act
    contains_amp = "&" in citation
    # Assert
    assert not contains_amp


def test_citation_apa_two_authors_uses_ampersand_separator():
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


def test_citation_apa_many_authors_inserts_comma_before_ampersand():
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
    assert ", & " in citation  # Final author preceded by comma-&


@pytest.fixture
def apa_volume_issue_citation():
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
    return work.citation("apa")


def test_citation_apa_with_volume_includes_italic_source(apa_volume_issue_citation):
    # Arrange
    citation = apa_volume_issue_citation
    # Act
    contains = "*Test Journal*" in citation
    # Assert
    assert contains


def test_citation_apa_with_volume_includes_italic_volume(apa_volume_issue_citation):
    # Arrange
    citation = apa_volume_issue_citation
    # Act
    contains = "*10*" in citation
    # Assert
    assert contains


def test_citation_apa_with_issue_renders_in_parentheses(apa_volume_issue_citation):
    # Arrange
    citation = apa_volume_issue_citation
    # Act
    contains = "(2)" in citation
    # Assert
    assert contains


def test_citation_apa_with_pages_includes_page_range(apa_volume_issue_citation):
    # Arrange
    citation = apa_volume_issue_citation
    # Act
    contains = "100-110" in citation
    # Assert
    assert contains


# ---------------------------------------------------------------------------
# Work.citation — BibTeX
# ---------------------------------------------------------------------------

@pytest.fixture
def bibtex_article_citation():
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
    return work.citation("bibtex")


def test_citation_bibtex_article_uses_article_entry_type(bibtex_article_citation):
    # Arrange
    bibtex = bibtex_article_citation
    # Act
    contains = "@article{W2741809807," in bibtex
    # Assert
    assert contains


def test_citation_bibtex_article_includes_title_field(bibtex_article_citation):
    # Arrange
    bibtex = bibtex_article_citation
    # Act
    contains = "title = {The state of OA}" in bibtex
    # Assert
    assert contains


def test_citation_bibtex_article_joins_authors_with_and(bibtex_article_citation):
    # Arrange
    bibtex = bibtex_article_citation
    # Act
    contains = "author = {Heather Piwowar and Jason Priem}" in bibtex
    # Assert
    assert contains


def test_citation_bibtex_article_includes_year(bibtex_article_citation):
    # Arrange
    bibtex = bibtex_article_citation
    # Act
    contains = "year = {2018}" in bibtex
    # Assert
    assert contains


def test_citation_bibtex_article_emits_journal_field(bibtex_article_citation):
    # Arrange
    bibtex = bibtex_article_citation
    # Act
    contains = "journal = {PeerJ}" in bibtex
    # Assert
    assert contains


def test_citation_bibtex_article_emits_doi_field(bibtex_article_citation):
    # Arrange
    bibtex = bibtex_article_citation
    # Act
    contains = "doi = {10.7717/peerj.4375}" in bibtex
    # Assert
    assert contains


@pytest.fixture
def bibtex_book_citation():
    work = Work(
        openalex_id="W123",
        title="Test Book",
        authors=["Test Author"],
        year=2023,
        publisher="Test Publisher",
        type="book",
    )
    return work.citation("bibtex")


def test_citation_bibtex_book_uses_book_entry_type(bibtex_book_citation):
    # Arrange
    bibtex = bibtex_book_citation
    # Act
    contains = "@book{W123," in bibtex
    # Assert
    assert contains


def test_citation_bibtex_book_emits_publisher_field(bibtex_book_citation):
    # Arrange
    bibtex = bibtex_book_citation
    # Act
    contains = "publisher = {Test Publisher}" in bibtex
    # Assert
    assert contains


@pytest.fixture
def bibtex_proceedings_citation():
    work = Work(
        openalex_id="W123",
        title="Conference Paper",
        authors=["Conference Author"],
        year=2023,
        source="Conference Proceedings",
        type="proceedings-article",
    )
    return work.citation("bibtex")


def test_citation_bibtex_proceedings_uses_inproceedings_entry_type(
    bibtex_proceedings_citation,
):
    # Arrange
    bibtex = bibtex_proceedings_citation
    # Act
    contains = "@inproceedings{W123," in bibtex
    # Assert
    assert contains


def test_citation_bibtex_proceedings_emits_booktitle_field(
    bibtex_proceedings_citation,
):
    # Arrange
    bibtex = bibtex_proceedings_citation
    # Act
    contains = "booktitle = {Conference Proceedings}" in bibtex
    # Assert
    assert contains


def test_citation_default_style_matches_apa_explicit():
    # Arrange
    work = Work(openalex_id="W123", title="Test", year=2023)
    # Act
    same = work.citation() == work.citation("apa")
    # Assert
    assert same


def test_citation_style_argument_treats_bibtex_case_insensitive():
    # Arrange
    work = Work(openalex_id="W123", title="Test", year=2023)
    # Act
    same = work.citation("BIBTEX") == work.citation("bibtex")
    # Assert
    assert same


def test_citation_style_argument_treats_apa_case_insensitive():
    # Arrange
    work = Work(openalex_id="W123", title="Test", year=2023)
    # Act
    same = work.citation("APA") == work.citation("apa")
    # Assert
    assert same


def test_citation_apa_returns_string_for_minimal_work():
    # Arrange
    work = Work(openalex_id="W123")
    # Act
    apa = work.citation("apa")
    # Assert
    assert isinstance(apa, str)


def test_citation_bibtex_returns_string_for_minimal_work():
    # Arrange
    work = Work(openalex_id="W123")
    # Act
    bibtex = work.citation("bibtex")
    # Assert
    assert isinstance(bibtex, str)


def test_citation_bibtex_minimal_work_includes_at_sigil():
    # Arrange
    work = Work(openalex_id="W123")
    # Act
    bibtex = work.citation("bibtex")
    # Assert
    assert "@" in bibtex


# ---------------------------------------------------------------------------
# SearchResult container
# ---------------------------------------------------------------------------

@pytest.fixture
def two_work_search_result():
    works = [
        Work(openalex_id="W1", title="Work 1"),
        Work(openalex_id="W2", title="Work 2"),
    ]
    return SearchResult(works=works, total=100, query="test", elapsed_ms=10.0)


def test_search_result_len_returns_works_count(two_work_search_result):
    # Arrange
    result = two_work_search_result
    # Act
    length = len(result)
    # Assert
    assert length == 2


def test_search_result_index_zero_returns_first_work(two_work_search_result):
    # Arrange
    result = two_work_search_result
    # Act
    first = result[0]
    # Assert
    assert first.openalex_id == "W1"


def test_search_result_iter_matches_underlying_works(two_work_search_result):
    # Arrange
    result = two_work_search_result
    # Act
    items = list(result)
    # Assert
    assert items == result.works
