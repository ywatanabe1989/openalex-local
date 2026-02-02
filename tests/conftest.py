"""Shared test fixtures for openalex_local tests."""

import os
import pytest

from openalex_local._core.config import Config


# Sample OpenAlex IDs for testing (known to exist in most datasets)
SAMPLE_OPENALEX_IDS = [
    "W2741809807",  # "The state of OA" - well-known paper
    "W2100837269",  # Nature paper
]

# Sample DOIs for testing
SAMPLE_DOIS = [
    "10.7717/peerj.4375",  # "The state of OA"
]


@pytest.fixture
def sample_openalex_id():
    """Return a sample OpenAlex ID."""
    return SAMPLE_OPENALEX_IDS[0]


@pytest.fixture
def sample_doi():
    """Return a sample DOI."""
    return SAMPLE_DOIS[0]


@pytest.fixture
def db_available():
    """Check if database is available for integration tests."""
    try:
        Config.reset()
        Config.get_db_path()
        return True
    except FileNotFoundError:
        return False


@pytest.fixture
def reset_config():
    """Reset configuration before and after test."""
    Config.reset()
    yield
    Config.reset()


@pytest.fixture
def sample_work_data():
    """Return sample OpenAlex API response data."""
    return {
        "id": "https://openalex.org/W2741809807",
        "doi": "https://doi.org/10.7717/peerj.4375",
        "title": "The state of OA: a large-scale analysis of the prevalence and impact of Open Access articles",
        "publication_year": 2018,
        "authorships": [
            {"author": {"display_name": "Heather Piwowar"}},
            {"author": {"display_name": "Jason Priem"}},
            {"author": {"display_name": "Vincent Larivière"}},
            {"author": {"display_name": "Juan Pablo Alperin"}},
            {"author": {"display_name": "Lisa Matthias"}},
            {"author": {"display_name": "Bree Norlander"}},
            {"author": {"display_name": "Ashley Farley"}},
            {"author": {"display_name": "Jevin West"}},
            {"author": {"display_name": "Stefanie Haustein"}},
        ],
        "abstract_inverted_index": {
            "Despite": [0],
            "growing": [1],
            "interest": [2],
            "in": [3, 15],
            "Open": [4],
            "Access": [5],
        },
        "primary_location": {
            "source": {
                "display_name": "PeerJ",
                "issn": ["2167-8359"],
                "host_organization_name": "PeerJ",
            }
        },
        "biblio": {
            "volume": "6",
            "issue": None,
            "first_page": "e4375",
        },
        "type": "journal-article",
        "cited_by_count": 1500,
        "concepts": [
            {"display_name": "Open access", "score": 0.95},
            {"display_name": "Citation", "score": 0.85},
        ],
        "topics": [
            {"display_name": "Scholarly Communication", "subfield": {"display_name": "Library Science"}},
        ],
        "open_access": {
            "is_oa": True,
            "oa_url": "https://peerj.com/articles/4375/",
        },
        "referenced_works": [
            "https://openalex.org/W123",
            "https://openalex.org/W456",
        ],
    }
