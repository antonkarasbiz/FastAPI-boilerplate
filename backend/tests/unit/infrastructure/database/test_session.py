"""Tests for database session management."""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.session import async_session

pytestmark = pytest.mark.asyncio


class TestDatabaseSession:
    """Test cases for database session management."""

    async def test_async_session(self):
        """Test getting an async database session."""
        async for session in async_session():
            assert isinstance(session, AsyncSession)
            break  # Just test that we can get a session

    async def test_session_transaction(self, db_session: AsyncSession):
        """Test database session transaction handling."""
        # Test that we can execute a simple query
        result = await db_session.execute(text("SELECT 1 as test_value"))
        row = result.fetchone()
        assert row is not None
        assert row[0] == 1

    async def test_session_rollback(self, db_session: AsyncSession):
        """Test session rollback functionality."""
        # Start a transaction
        await db_session.begin()

        # Execute some operation
        await db_session.execute(text("SELECT 1"))

        # Rollback
        await db_session.rollback()

        # Session should still be usable
        result = await db_session.execute(text("SELECT 2"))
        row = result.fetchone()
        assert row is not None
        assert row[0] == 2

    async def test_session_commit(self, db_session: AsyncSession):
        """Test session commit functionality."""
        # The session fixture should handle commits automatically
        # This test verifies the session is working properly
        result = await db_session.execute(text("SELECT 3"))
        row = result.fetchone()
        assert row is not None
        assert row[0] == 3

        # Commit should work without errors
        await db_session.commit()
