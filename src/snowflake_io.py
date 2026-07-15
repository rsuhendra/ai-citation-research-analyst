from __future__ import annotations
from contextlib import contextmanager
from typing import Any, Iterator
import pandas as pd
import streamlit as st
from snowflake.core import Root
from snowflake.snowpark import Session
from src.config import SnowflakeConfig

def create_session() -> Session:
    config = SnowflakeConfig.from_env()
    return Session.builder.configs(config.to_snowpark_dict()).create()

@st.cache_resource
def get_connection(): return st.connection("snowflake")

@contextmanager
def cursor() -> Iterator[Any]:
    cur = get_connection().cursor()
    try: yield cur
    finally: cur.close()

def clear_snowflake_connections() -> None:
    try:
        get_connection().close()
    except Exception:
        pass

    try:
        get_snowpark_session().close()
    except Exception:
        pass

    get_root.clear()
    get_snowpark_session.clear()
    get_connection.clear()

def fetch_df(sql: str, params: list[Any] | None = None) -> pd.DataFrame:
    with cursor() as cur:
        cur.execute(sql, params or [])
        return cur.fetch_pandas_all()

def execute(sql: str, params: list[Any] | None = None) -> None:
    with cursor() as cur: cur.execute(sql, params or [])

@st.cache_resource
def get_snowpark_session() -> Session:
    return Session.builder.configs(dict(st.secrets["connections"]["snowflake"])).create()

@st.cache_resource
def get_root() -> Root: return Root(get_snowpark_session())
