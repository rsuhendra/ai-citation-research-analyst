from __future__ import annotations
import os
from dataclasses import dataclass
import streamlit as st
from dotenv import load_dotenv
load_dotenv()

@dataclass(frozen=True)
class SnowflakeConfig:
    account: str; user: str; password: str; role: str; warehouse: str; database: str; schema: str
    @classmethod
    def from_env(cls) -> "SnowflakeConfig":
        names = ["SNOWFLAKE_ACCOUNT","SNOWFLAKE_USER","SNOWFLAKE_PASSWORD","SNOWFLAKE_ROLE","SNOWFLAKE_WAREHOUSE","SNOWFLAKE_DATABASE","SNOWFLAKE_SCHEMA"]
        missing = [n for n in names if not os.getenv(n)]
        if missing: raise RuntimeError("Missing required environment variables: " + ", ".join(missing))
        return cls(*(os.environ[n] for n in names))
    def to_snowpark_dict(self) -> dict[str, str]:
        return {"account":self.account,"user":self.user,"password":self.password,"role":self.role,"warehouse":self.warehouse,"database":self.database,"schema":self.schema}

@dataclass(frozen=True)
class AppConfig:
    database: str; schema: str; router_model: str; main_model: str; search_service: str; daily_prompt_limit: int
    @classmethod
    def from_secrets(cls) -> "AppConfig":
        sf = st.secrets["connections"]["snowflake"]
        return cls(str(sf["database"]), str(sf["schema"]), str(st.secrets.get("ROUTER_MODEL","llama3.2-3b")), str(st.secrets.get("MAIN_MODEL","llama3.2-3b")), str(st.secrets.get("CORTEX_SEARCH_SERVICE","PAPER_SEARCH")), int(st.secrets.get("DAILY_PROMPT_LIMIT",20)))
