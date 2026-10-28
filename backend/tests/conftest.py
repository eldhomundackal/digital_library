"""Shared pytest fixtures for the Digital Library test suite."""
import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from app.core.config import settings


@pytest.fixture(scope="session")
def event_loop_policy():
    return asyncio.DefaultEventLoopPolicy()


@pytest.fixture
def mock_db():
    """Async SQLAlchemy session mock."""
    db = AsyncMock()
    # execute() is awaited; the result object's methods are called synchronously
    result = MagicMock()
    result.scalar_one_or_none = MagicMock(return_value=None)
    result.scalars = MagicMock()
    db.execute = AsyncMock(return_value=result)
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.fixture
def mock_redis():
    """Async Redis client mock."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.setex = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    redis.incr = AsyncMock(return_value=1)
    redis.exists = AsyncMock(return_value=0)
    return redis


@pytest.fixture
def mock_auth_provider():
    """LocalAuthProvider mock."""
    provider = MagicMock()
    provider.register = AsyncMock()
    provider.login = AsyncMock()
    provider.logout = AsyncMock()
    provider.refresh_token = AsyncMock()
    return provider


@pytest.fixture
def mock_response():
    """FastAPI Response mock for cookie operations."""
    response = MagicMock()
    response.set_cookie = MagicMock()
    response.delete_cookie = MagicMock()
    return response
