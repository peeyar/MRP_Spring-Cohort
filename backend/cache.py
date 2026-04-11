"""In-memory cache for pre-generated LLM details, keyed by contact LinkedIn URL."""

from models import LLMDetails

_store: dict[str, LLMDetails] = {}


def get(contact_url: str) -> LLMDetails | None:
    return _store.get(contact_url)


def set(contact_url: str, details: LLMDetails) -> None:
    _store[contact_url] = details
