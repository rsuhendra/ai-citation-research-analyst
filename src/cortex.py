from __future__ import annotations

import json
from typing import Any

import pandas as pd

from src.config import AppConfig
from src.snowflake_io import fetch_df, get_root


def ai_complete(prompt: str, model: str, max_tokens: int = 1200) -> str:
    df = fetch_df(
        "SELECT AI_COMPLETE(?, ?, OBJECT_CONSTRUCT('temperature', 0, 'max_tokens', ?)) AS RESPONSE",
        [model, prompt, max_tokens],
    )
    return str(df.iloc[0]["RESPONSE"]).strip()


def search_papers(query: str, limit: int = 8) -> list[dict[str, Any]]:
    config = AppConfig.from_secrets()
    root = get_root()
    service = (
        root.databases[config.database]
        .schemas[config.schema]
        .cortex_search_services[config.search_service]
    )
    response = service.search(
        query=query,
        columns=[
            "PAPER_ID",
            "TITLE",
            "ABSTRACT",
            "PUBLICATION_YEAR",
            "PRIMARY_TOPIC",
            "CITED_BY_COUNT",
            "CITATIONS_PER_YEAR",
            "ARXIV_URL",
        ],
        filter={"@eq": {"IS_FOCAL": True}},
        limit=max(1, min(limit, 12)),
    )
    return list(json.loads(response.to_json()).get("results", []))


def search_evidence_text(papers: list[dict[str, Any]]) -> str:
    sections: list[str] = []
    for index, paper in enumerate(papers, start=1):
        sections.append(
            "\n".join(
                [
                    f"Paper {index}",
                    f"Title: {paper.get('TITLE', '')}",
                    f"Year: {paper.get('PUBLICATION_YEAR', '')}",
                    f"Topic: {paper.get('PRIMARY_TOPIC', '')}",
                    f"Citation count: {paper.get('CITED_BY_COUNT', '')}",
                    f"Citations per year: {paper.get('CITATIONS_PER_YEAR', '')}",
                    f"Abstract: {paper.get('ABSTRACT', '')}",
                    f"URL: {paper.get('ARXIV_URL', '')}",
                ]
            )
        )
    return "\n\n".join(sections)


def dataframe_for_prompt(df: pd.DataFrame, max_rows: int = 50) -> str:
    if df.empty:
        return "[]"
    records = (
        df.head(max_rows)
        .where(pd.notna(df), None)
        .to_dict(orient="records")
    )
    return json.dumps(records, ensure_ascii=False, default=str)
