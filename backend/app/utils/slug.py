"""Slug generation for categories and tags."""

import re
import unicodedata


def slugify(text: str) -> str:
    """
    Convert a string to a URL-safe slug.
    e.g. 'Science Fiction' -> 'science-fiction'
    """
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text
