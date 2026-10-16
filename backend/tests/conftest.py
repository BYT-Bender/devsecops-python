"""
Pytest configuration and shared fixtures for the TaskBoard API test suite.
Provides an isolated in-memory SQLite database and FastAPI TestClient.
"""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

# Override DATABASE_URL BEFORE importing the app so config picks up SQLite
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from app.main import app
from app.db import Base, get_db

# ---------------------------------------------------------------------------
# Engine & Session for isolated SQLite test database
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# Enable WAL mode for concurrent test access
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ---------------------------------------------------------------------------
# Session-scoped fixture: create schema once per test session
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create all tables before the session; drop them after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    # Clean up test.db file if present
    if os.path.exists("test.db"):
        try:
            os.remove("test.db")
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Function-scoped fixture: fresh DB session per test (with rollback)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="function")
def db_session(setup_database):
    """Provide a transactional scope around each test, rolled back after."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# ---------------------------------------------------------------------------
# Function-scoped fixture: FastAPI TestClient with DB override
# ---------------------------------------------------------------------------
@pytest.fixture(scope="function")
def client(db_session):
    """Override FastAPI's get_db dependency with the test session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
