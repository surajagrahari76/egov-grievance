import os
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

TEST_DB_DIR = tempfile.mkdtemp(prefix="egov_test_")
os.environ["APP_ENV"] = "test"
os.environ["JOB_RUNNER"] = "none"
os.environ["DATABASE_URL"] = f"sqlite:///{(Path(TEST_DB_DIR) / 'test.db').as_posix()}"
os.environ["UPLOAD_DIR"] = str(Path(TEST_DB_DIR) / "uploads")
os.environ["DEMO_MODE"] = "true"

from app.core.database import Base, SessionLocal, engine, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import seed_database  # noqa: E402


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_database(db)
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client(db_session):
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
