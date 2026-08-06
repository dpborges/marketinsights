"""Minimal SQLAlchemy engine and request-scoped session management."""

from collections.abc import Generator

from fastapi import Request
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker


class DatabaseManager:
    """Own the application's single synchronous SQLAlchemy engine."""

    def __init__(self, database_url: str) -> None:
        self.engine: Engine = create_engine(
            database_url,
            pool_pre_ping=True,
            pool_recycle=1800,
        )
        self._session_factory = sessionmaker(
            bind=self.engine,
            class_=Session,
            autoflush=False,
            expire_on_commit=False,
        )

    def session(self) -> Session:
        """Create a database session."""

        return self._session_factory()

    def is_ready(self) -> bool:
        """Execute an inexpensive connection health check."""

        with self.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True

    def dispose(self) -> None:
        """Release pooled database connections."""

        self.engine.dispose()


def get_database_session(request: Request) -> Generator[Session, None, None]:
    """Provide and reliably close a request-scoped SQLAlchemy session."""

    manager: DatabaseManager | None = request.app.state.database
    if manager is None:
        raise RuntimeError("Database connectivity is not configured")

    session = manager.session()
    try:
        yield session
    finally:
        session.close()
