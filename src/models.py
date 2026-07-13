from dataclasses import dataclass
from typing import Any
import pandas as pd
@dataclass
class AssistantResult:
    route: str
    answer: str
    sql: str | None = None
    sql_results: pd.DataFrame | None = None
    search_results: list[dict[str, Any]] | None = None
