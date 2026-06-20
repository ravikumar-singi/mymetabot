from abc import ABC, abstractmethod
from src.database.models import ContentPost


class BasePlatform(ABC):
    @abstractmethod
    def post(self, content: ContentPost) -> str:
        """Post content to the platform. Returns the platform post ID."""

    @abstractmethod
    def validate_credentials(self) -> bool:
        """Return True if credentials are valid."""
