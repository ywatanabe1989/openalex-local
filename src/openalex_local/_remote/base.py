"""Remote API client for openalex_local.

Connects to an OpenAlex Local API server instead of direct database access.
Use this when the database is on a remote server accessible via HTTP.
"""

import json
import urllib.request
import urllib.parse
import urllib.error
from typing import List, Optional, Dict, Any

from .._core.models import Work, SearchResult
from .._core.config import DEFAULT_PORT

# Default URL uses SCITEX port convention
DEFAULT_API_URL = f"http://localhost:{DEFAULT_PORT}"


class RemoteClient:
    """
    HTTP client for OpenAlex Local API server.

    Provides the same interface as the local API but connects
    to a remote server via HTTP.

    Example:
        >>> client = RemoteClient("http://localhost:31292")
        >>> results = client.search(query="machine learning", limit=10)
        >>> work = client.get("W2741809807")
    """

    def __init__(self, base_url: str = DEFAULT_API_URL, timeout: int = 30):
        """
        Initialize remote client.

        Args:
            base_url: API server URL (default: http://localhost:31292)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict]:
        """Make HTTP request to API."""
        url = f"{self.base_url}{endpoint}"
        if params:
            # Filter out None values
            params = {k: v for k, v in params.items() if v is not None}
            if params:
                url = f"{url}?{urllib.parse.urlencode(params)}"

        try:
            req_data = None
            if data is not None:
                req_data = json.dumps(data).encode("utf-8")

            req = urllib.request.Request(url, data=req_data, method=method)
            req.add_header("Accept", "application/json")
            if req_data:
                req.add_header("Content-Type", "application/json")

            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            raise ConnectionError(f"API request failed: {e.code} {e.reason}") from e
        except urllib.error.URLError as e:
            raise ConnectionError(
                f"Cannot connect to API at {self.base_url}: {e.reason}"
            ) from e
        except (ConnectionRefusedError, ConnectionResetError, OSError) as e:
            raise ConnectionError(
                f"Cannot connect to API at {self.base_url}: {e}"
            ) from e

    def health(self) -> Dict:
        """Check API server health."""
        return self._request("/health")

    def info(self) -> Dict:
        """Get database/API information."""
        root = self._request("/")
        info_data = self._request("/info")
        return {
            "api_url": self.base_url,
            "api_version": root.get("version", "unknown") if root else "unknown",
            "status": root.get("status", "unknown") if root else "unknown",
            "mode": "remote",
            "works": info_data.get("total_works", 0) if info_data else 0,
            "fts_indexed": info_data.get("fts_indexed", 0) if info_data else 0,
        }

    def search(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
    ) -> SearchResult:
        """
        Search for works.

        Args:
            query: Full-text search query
            limit: Maximum results (default: 20)
            offset: Skip first N results for pagination

        Returns:
            SearchResult with matching works
        """
        params = {
            "q": query,
            "limit": limit,
            "offset": offset,
        }

        data = self._request("/works", params)

        if not data:
            return SearchResult(works=[], total=0, query=query, elapsed_ms=0.0)

        works = []
        for item in data.get("results", []):
            work = Work(
                openalex_id=item.get("openalex_id", ""),
                doi=item.get("doi"),
                title=item.get("title"),
                authors=item.get("authors", []),
                year=item.get("year"),
                source=item.get("source"),
                issn=item.get("issn"),
                volume=item.get("volume"),
                issue=item.get("issue"),
                pages=item.get("pages"),
                abstract=item.get("abstract"),
                cited_by_count=item.get("cited_by_count"),
                concepts=item.get("concepts", []),
                topics=item.get("topics", []),
                is_oa=item.get("is_oa", False),
                oa_url=item.get("oa_url"),
            )
            works.append(work)

        return SearchResult(
            works=works,
            total=data.get("total", len(works)),
            query=query,
            elapsed_ms=data.get("elapsed_ms", 0.0),
        )

    def get(self, id_or_doi: str) -> Optional[Work]:
        """
        Get a work by OpenAlex ID or DOI.

        Args:
            id_or_doi: OpenAlex ID (e.g., W2741809807) or DOI

        Returns:
            Work object or None if not found
        """
        data = self._request(f"/works/{id_or_doi}")
        if not data or "error" in data:
            return None

        return Work(
            openalex_id=data.get("openalex_id", ""),
            doi=data.get("doi"),
            title=data.get("title"),
            authors=data.get("authors", []),
            year=data.get("year"),
            source=data.get("source"),
            issn=data.get("issn"),
            volume=data.get("volume"),
            issue=data.get("issue"),
            pages=data.get("pages"),
            abstract=data.get("abstract"),
            cited_by_count=data.get("cited_by_count"),
            concepts=data.get("concepts", []),
            topics=data.get("topics", []),
            is_oa=data.get("is_oa", False),
            oa_url=data.get("oa_url"),
        )

    def get_many(self, ids: List[str]) -> List[Work]:
        """
        Get multiple works by OpenAlex ID or DOI using batch endpoint.

        Args:
            ids: List of OpenAlex IDs or DOIs

        Returns:
            List of Work objects
        """
        try:
            data = {"ids": ids}
            req_data = json.dumps(data).encode("utf-8")
            req = urllib.request.Request(
                f"{self.base_url}/works/batch", data=req_data, method="POST"
            )
            req.add_header("Content-Type", "application/json")
            req.add_header("Accept", "application/json")

            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                result = json.loads(response.read().decode("utf-8"))

            works = []
            for item in result.get("results", []):
                work = Work(
                    openalex_id=item.get("openalex_id", ""),
                    doi=item.get("doi"),
                    title=item.get("title"),
                    authors=item.get("authors", []),
                    year=item.get("year"),
                    source=item.get("source"),
                    abstract=item.get("abstract"),
                    cited_by_count=item.get("cited_by_count"),
                )
                works.append(work)
            return works
        except Exception:
            # Fallback to individual lookups
            works = []
            for id_or_doi in ids:
                work = self.get(id_or_doi)
                if work:
                    works.append(work)
            return works

    def exists(self, id_or_doi: str) -> bool:
        """Check if a work exists."""
        return self.get(id_or_doi) is not None


# Module-level client for convenience
_client: Optional[RemoteClient] = None


def get_client(base_url: str = DEFAULT_API_URL) -> RemoteClient:
    """Get or create singleton remote client."""
    global _client
    if _client is None or _client.base_url != base_url:
        _client = RemoteClient(base_url)
    return _client


def reset_client() -> None:
    """Reset singleton client."""
    global _client
    _client = None
