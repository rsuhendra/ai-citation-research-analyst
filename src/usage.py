from __future__ import annotations

import hashlib

from src.snowflake_io import execute, fetch_df


def get_usage_count() -> int:
    df = fetch_df(
        """
        SELECT COUNT(*) AS N
        FROM PROMPT_USAGE
        WHERE USAGE_DATE = CURRENT_DATE()
          AND SUCCEEDED = TRUE
        """
    )

    return int(df.iloc[0]["N"])


def enforce_limit(daily_limit: int) -> None:
    used = get_usage_count()

    if used >= daily_limit:
        raise RuntimeError(
            f"Daily application limit reached "
            f"({used}/{daily_limit} prompts)."
        )


def record_usage(
    route: str,
    question: str,
    succeeded: bool,
) -> None:
    question_hash = hashlib.sha256(
        question.encode("utf-8")
    ).hexdigest()

    execute(
        """
        INSERT INTO PROMPT_USAGE (
            ROUTE,
            QUESTION_HASH,
            SUCCEEDED
        )
        VALUES (?, ?, ?)
        """,
        [
            route,
            question_hash,
            succeeded,
        ],
    )