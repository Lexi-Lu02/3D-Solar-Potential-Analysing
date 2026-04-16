"""
Regression: every *.sql file in app/sql/ must pass psycopg's placeholder
parser. A stray '%' in a comment crashes psycopg at execute() time, but
FakeCursor used to swallow it silently — this test makes sure new SQL
files can't reintroduce the bug even before they're wired into a service.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from psycopg._queries import PostgresQuery
from psycopg.adapt import Transformer

SQL_DIR = Path(__file__).parent.parent / "app" / "sql"

# Enough keys to satisfy every .sql file's named placeholders. Extra keys
# are harmless; missing keys would raise.
_DUMMY_PARAMS = {"id": 1, "structure_id": 1, "q": "x"}


@pytest.mark.parametrize("sql_path", sorted(SQL_DIR.glob("*.sql")), ids=lambda p: p.name)
def test_sql_file_parses(sql_path: Path) -> None:
    sql = sql_path.read_text(encoding="utf-8").encode()
    PostgresQuery(Transformer()).convert(sql, _DUMMY_PARAMS)
