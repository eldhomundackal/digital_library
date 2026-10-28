"""Pagination helper utilities."""

import math


def compute_pages(total: int, limit: int) -> int:
    """Return total page count given total items and page size."""
    if limit <= 0:
        return 0
    return math.ceil(total / limit)
