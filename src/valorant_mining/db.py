"""Small helpers around the raw SQLite database."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator

import pandas as pd

from .config import DB_PATH


@contextmanager
def connect(db_path=DB_PATH) -> Iterator[sqlite3.Connection]:
    con = sqlite3.connect(db_path)
    try:
        yield con
    finally:
        con.close()


def read_sql(query: str, db_path=DB_PATH) -> pd.DataFrame:
    with connect(db_path) as con:
        return pd.read_sql_query(query, con)


def table_counts() -> pd.DataFrame:
    rows = []
    with connect() as con:
        for table in ("Matches", "Games", "Game_Scoreboard", "Game_Rounds"):
            n = con.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            rows.append({"table": table, "rows": n})
    return pd.DataFrame(rows)
