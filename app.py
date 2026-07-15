from __future__ import annotations

import pandas as pd
import streamlit as st

from src.chat_memory import add_message, ensure_chat_state
from src.config import AppConfig
from src.router import answer_question
from src.snowflake_io import (
    clear_snowflake_connections,
    execute,
)
from src.usage import (
    enforce_limit,
    get_usage_count,
    record_usage,
)


st.set_page_config(
    page_title="Natural Language Research Analytics",
    layout="wide",
)


config = AppConfig.from_secrets()
ensure_chat_state()


EXAMPLES = [
    (
        "Most cited papers",
        "What are the 10 most cited papers in the corpus?",
    ),
    (
        "Citation velocity",
        "Which papers have the highest citations per year?",
    ),
    (
        "Efficient transformers",
        (
            "Which papers discuss efficient transformer "
            "training or inference?"
        ),
    ),
    (
        "Multimodal learning",
        (
            "Summarize the papers about multimodal "
            "representation learning."
        ),
    ),
]


ROUTE_DESCRIPTIONS = {
    "direct": "Answered using Snowflake Cortex AI.",
    "sql": "Generated and executed SQL against the citation database.",
    "rag": "Retrieved relevant paper abstracts using Cortex Search.",
    "reject": "The question is outside the scope of this application.",
}


def queue_example(question: str) -> None:
    """
    Queue an example question for submission on the next Streamlit rerun.
    """
    st.session_state["pending_question"] = question


def render_search_results(
    search_results: list[dict] | None,
) -> None:
    """
    Display the paper records returned by Cortex Search.
    """
    if not search_results:
        return

    with st.expander("Retrieved papers"):
        for index, paper in enumerate(
            search_results,
            start=1,
        ):
            title = paper.get(
                "TITLE",
                "Untitled",
            )

            year = paper.get(
                "PUBLICATION_YEAR",
                "",
            )

            citations = paper.get(
                "CITED_BY_COUNT",
                "",
            )

            url = paper.get(
                "ARXIV_URL",
                "",
            )

            st.markdown(
                f"**{index}. {title}**  \n"
                f"Year: {year} · "
                f"Citations: {citations}"
            )

            if url:
                st.markdown(
                    f"[Open on arXiv]({url})"
                )


def render_message_metadata(
    message: dict,
) -> None:
    """
    Display route information and supporting query or retrieval results.
    """
    route = message.get("route")

    if route:
        st.caption(
            ROUTE_DESCRIPTIONS.get(
                route,
                route,
            )
        )

    sql = message.get("sql")

    if sql:
        with st.expander("Generated SQL"):
            st.code(
                sql,
                language="sql",
            )

    sql_results = message.get(
        "sql_results"
    )

    if isinstance(
        sql_results,
        pd.DataFrame,
    ):
        with st.expander("Query results"):
            st.dataframe(
                sql_results,
                use_container_width=True,
            )

    render_search_results(
        message.get("search_results")
    )


if "pending_question" not in st.session_state:
    st.session_state["pending_question"] = None


# -------------------------------------------------------------------
# Header
# -------------------------------------------------------------------

st.title(
    "Natural Language Research Analytics with Snowflake"
)

st.markdown(
    """
A natural-language interface over a curated corpus of highly cited
AI and machine learning papers published from 2021 through 2025.

The application automatically routes each question to the appropriate
pipeline, using **Snowflake Cortex AI** for query routing, reasoning,
and SQL generation, **Snowflake Cortex Search** for semantic retrieval
over paper abstracts, and **Snowflake SQL** for structured analysis of
citation relationships and publication metadata.
"""
)


capability_col1, capability_col2, capability_col3 = st.columns(3)

with capability_col1:
    st.subheader("Citation Analytics")
    st.write(
        "Explore citation rankings, publication years, "
        "citation velocity, and relationships between papers."
    )

with capability_col2:
    st.subheader("Semantic Search")
    st.write(
        "Retrieve papers by meaning rather than exact keywords "
        "using titles and abstracts."
    )

with capability_col3:
    st.subheader("Research Synthesis")
    st.write(
        "Summarize methods, compare approaches, and answer "
        "questions using retrieved abstracts as evidence."
    )


# -------------------------------------------------------------------
# Sidebar
# -------------------------------------------------------------------

with st.sidebar:
    st.header("Usage")

    try:
        used = get_usage_count()
    except Exception as exc:
        st.warning(
            "Unable to read the current usage count."
        )
        st.caption(str(exc))
        used = 0

    remaining = max(
        0,
        config.daily_prompt_limit - used,
    )

    st.metric(
        "Prompts remaining today",
        remaining,
    )

    if config.daily_prompt_limit > 0:
        st.progress(
            min(
                1.0,
                used / config.daily_prompt_limit,
            )
        )

    st.caption(
        "Shared application-wide daily limit."
    )

    st.divider()

    if st.button(
        "Reconnect to Snowflake",
        use_container_width=True,
    ):
        clear_snowflake_connections()
        st.success(
            "Snowflake connection refreshed."
        )
        st.rerun()

    if st.button(
        "Clear conversation",
        use_container_width=True,
    ):
        st.session_state["messages"] = []
        st.session_state["pending_question"] = None
        st.rerun()


# -------------------------------------------------------------------
# Example questions
# -------------------------------------------------------------------

st.subheader("Example questions")

example_columns = st.columns(2)

for index, (label, question) in enumerate(EXAMPLES):
    example_columns[index % 2].button(
        label,
        key=f"example_{index}",
        use_container_width=True,
        on_click=queue_example,
        args=(question,),
        help=question,
    )


st.divider()


# -------------------------------------------------------------------
# Existing conversation
# -------------------------------------------------------------------

for message in st.session_state["messages"]:
    with st.chat_message(
        message["role"]
    ):
        st.markdown(
            message["content"]
        )

        if message["role"] == "assistant":
            render_message_metadata(
                message
            )


# -------------------------------------------------------------------
# Chat input
# -------------------------------------------------------------------

typed_question = st.chat_input(
    "Ask about papers, citations, methods, or research topics"
)

question = typed_question

if (
    question is None
    and st.session_state["pending_question"]
):
    question = st.session_state[
        "pending_question"
    ]

    st.session_state[
        "pending_question"
    ] = None


# -------------------------------------------------------------------
# Process a new question
# -------------------------------------------------------------------

if question:
    question = question.strip()

    try:
        enforce_limit(
            config.daily_prompt_limit,
        )

    except RuntimeError as exc:
        st.error(str(exc))
        st.stop()

    add_message(
        "user",
        question,
    )

    with st.chat_message("user"):
        st.markdown(question)

    try:
        with st.chat_message("assistant"):
            with st.spinner(
                "Analyzing the research corpus..."
            ):
                result = answer_question(
                    question
                )

            st.caption(
                ROUTE_DESCRIPTIONS.get(
                    result.route,
                    result.route,
                )
            )

            st.markdown(
                result.answer
            )

            if result.sql:
                with st.expander(
                    "Generated SQL"
                ):
                    st.code(
                        result.sql,
                        language="sql",
                    )

            if (
                result.sql_results
                is not None
            ):
                with st.expander(
                    "Query results"
                ):
                    st.dataframe(
                        result.sql_results,
                        use_container_width=True,
                    )

            render_search_results(
                result.search_results
            )

        record_usage(
            result.route,
            question,
            True,
        )

        execute(
            """
            INSERT INTO QUERY_LOG (
                USER_KEY,
                QUESTION,
                ROUTE,
                GENERATED_SQL,
                ANSWER
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                None,
                question,
                result.route,
                result.sql,
                result.answer,
            ],
        )

        add_message(
            "assistant",
            result.answer,
            route=result.route,
            sql=result.sql,
            sql_results=result.sql_results,
            search_results=result.search_results,
        )

        st.rerun()

    except Exception as exc:
        record_usage(
            "error",
            question,
            False,
        )

        st.error(
            f"Request failed: {exc}"
        )

        if st.button(
            "Reconnect and retry",
            use_container_width=True,
        ):
            clear_snowflake_connections()

            # Remove the user message that was just added so it
            # is not duplicated when the question is retried.
            if (
                st.session_state["messages"]
                and st.session_state["messages"][-1].get("role")
                == "user"
                and st.session_state["messages"][-1].get("content")
                == question
            ):
                st.session_state["messages"].pop()

            st.session_state["pending_question"] = question
            st.rerun()