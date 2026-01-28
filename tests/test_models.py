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
