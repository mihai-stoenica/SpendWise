from pathlib import Path

import pytest

from spendwise.repositories.db import init_db


@pytest.fixture()
def temp_db_path(tmp_path: Path) -> Path:
    db_file = tmp_path / "test_data.db"
    init_db(db_file)
    return db_file
