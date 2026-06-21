from abc import ABC, abstractmethod
from src.database.models import ContentPost


class BasePlatform(ABC):
    @abstractmethod
    def post(self, content: ContentPost) -> str:
        """Post content to the platform. Returns the platform post ID."""

    @abstractmethod
    def validate_credentials(self) -> bool:
        """Return True if credentials are valid."""

    @staticmethod
    def _check_graph_api_response(data: dict) -> None:
        """Raise RuntimeError if the Meta Graph API returned an error body (even on HTTP 200)."""
        if "error" in data:
            err = data["error"]
            raise RuntimeError(
                f"Meta API error {err.get('code', '?')}: {err.get('message', data)}"
            )
