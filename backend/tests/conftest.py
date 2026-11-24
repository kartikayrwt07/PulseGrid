import gc
import os
import secrets
import sqlite3
from collections.abc import Iterator
from contextlib import closing, suppress
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure test environment never relies on missing .env or hardcoded secrets
os.environ.setdefault("SECRET_KEY", secrets.token_hex(32))
os.environ.setdefault("DEMO_MODE", "true")

BACKEND_TESTS_DIR = Path(__file__).resolve().parent
MAIN_DB_PATH = BACKEND_TESTS_DIR.parent / "pulsegrid.db"
TEST_DB_PATH = BACKEND_TESTS_DIR / "test_pulsegrid.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"

from app.core.config import get_settings  # noqa: E402

get_settings.cache_clear()

from app.core.auth import create_access_token  # noqa: E402
from app.core.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


def _cleanup_test_db() -> None:
    for suffix in ("", "-wal", "-shm"):
        p = Path(f"{TEST_DB_PATH}{suffix}")
        if p.exists():
            with suppress(PermissionError):
                p.unlink()


@pytest.fixture(scope="session", autouse=True)
def setup_test_db() -> Iterator[None]:
    _cleanup_test_db()
    if MAIN_DB_PATH.exists():
        with closing(sqlite3.connect(MAIN_DB_PATH)) as src, closing(
            sqlite3.connect(TEST_DB_PATH)
        ) as dst:
            src.backup(dst)
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()
    gc.collect()
    _cleanup_test_db()


@pytest.fixture()
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def faculty_headers() -> dict[str, str]:
    token = create_access_token(subject="faculty:FAC-001", role="faculty")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def student1_headers() -> dict[str, str]:
    token = create_access_token(subject="student:1", role="student", student_id=1)
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Hero Persona fixtures — imported here so pytest auto-discovers them for
# all test modules without requiring direct imports (eliminates F811 errors).
# ---------------------------------------------------------------------------
from tests.fixtures.hero_personas import (  # noqa: E402, F401
    aarav_df,
    aarav_weekly_composites,
    meera_df,
    rohan_cn_lab_ponr_input,
    safe_student_ponr_input,
    tough_exam_cohort_df,
)
