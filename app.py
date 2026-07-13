from __future__ import annotations

import pandas as pd
import streamlit as st

from src.chat_memory import add_message, ensure_chat_state
from src.config import AppConfig
from src.router import answer_question
from src.snowflake_io import execute
from src.usage import enforce_limit, get_usage_count, get_user_key, record_usage

st.set_page_config(
    page_title="AI Citation Research Analyst",
    page_icon="🔬",
    layout="wide",
)

config = AppConfig.from_secrets()
user_key = get_user_key()
ensure_chat_state()


def fill_question(text: str) -> None:
    st.session_state["research_query"] = text


if "research_query" not in st.session_state:
    st.session_state["research_query"] = ""

EXAMPLES = [
    ("Most cited papers", "What are the 10 most cited papers in the corpus?"),
    ("Citation velocity", "Which papers have the highest citations per year?"),
    (
        "Citation relationships",
        "Which papers are cited by the largest number of other papers in this corpus?",
    ),
    (
        "Diffusion models",
        "Which papers discuss diffusion models, and what are their main ideas?",
    ),
    (
        "Efficient transformers",
        "Which papers discuss efficient transformer training or inference?",
    ),
    (
        "Multimodal learning",
        "Summarize the papers about multimodal representation learning.",
    ),
]

st.title("🔬 AI Citation Research Analyst")
st.caption(
    "Ask structured citation questions or semantic questions about highly cited ML/AI paper abstracts."
)

with st.sidebar:
    used = get_usage_count(user_key)
    st.metric(
        "Prompts remaining today",
        max(0, config.daily_prompt_limit - used),
    )
    st.progress(
        min(1.0, used / config.daily_prompt_limit)
        if config.daily_prompt_limit
        else 1.0
    )

    st.markdown(
        """
- **Direct:** general AI/ML explanations
- **SQL:** counts, rankings, years, citations
- **RAG:** methods and concepts in abstracts
- **Reject:** unrelated requests
"""
    )

    if st.button("Clear conversation", use_container_width=True):
        st.session_state["messages"] = []
        st.session_state["research_query"] = ""
        st.rerun()

st.subheader("💡 Try an example")
columns = st.columns(2)
for index, (label, example_question) in enumerate(EXAMPLES):
    columns[index % 2].button(
        label,
        key=f"example_{index}",
        use_container_width=True,
        on_click=fill_question,
        args=(example_question,),
        help=example_question,
    )

for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message.get("sql"):
            with st.expander("Generated SQL"):
                st.code(message["sql"], language="sql")

        if isinstance(message.get("sql_results"), pd.DataFrame):
            with st.expander("SQL results"):
                st.dataframe(message["sql_results"], use_container_width=True)

        if message.get("search_results"):
            with st.expander("Retrieved papers"):
                for index, paper in enumerate(
                    message["search_results"], start=1
                ):
                    st.markdown(
                        f"**{index}. {paper.get('TITLE', 'Untitled')}**  \n"
                        f"Year: {paper.get('PUBLICATION_YEAR', '')} · "
                        f"Citations: {paper.get('CITED_BY_COUNT', '')}  \n"
                        f"{paper.get('ARXIV_URL', '')}"
                    )

question = st.text_input(
    "Ask about the research corpus",
    key="research_query",
    placeholder="Example: Which papers discuss parameter-efficient fine-tuning?",
)

if st.button("Ask", type="primary", disabled=not question.strip()):
    question = question.strip()

    try:
        enforce_limit(user_key, config.daily_prompt_limit)
    except RuntimeError as exc:
        st.error(str(exc))
        st.stop()

    add_message("user", question)

    with st.chat_message("user"):
        st.markdown(question)

    try:
        with st.chat_message("assistant"):
            with st.spinner("Analyzing the question..."):
                result = answer_question(question)

            st.markdown(result.answer)

            if result.sql:
                with st.expander("Generated SQL"):
                    st.code(result.sql, language="sql")

            if result.sql_results is not None:
                with st.expander("SQL results"):
                    st.dataframe(result.sql_results, use_container_width=True)

            if result.search_results:
                with st.expander("Retrieved papers"):
                    for index, paper in enumerate(
                        result.search_results, start=1
                    ):
                        st.markdown(
                            f"**{index}. {paper.get('TITLE', 'Untitled')}**  \n"
                            f"Year: {paper.get('PUBLICATION_YEAR', '')} · "
                            f"Citations: {paper.get('CITED_BY_COUNT', '')}  \n"
                            f"{paper.get('ARXIV_URL', '')}"
                        )

        record_usage(user_key, result.route, question, True)
        execute(
            "INSERT INTO QUERY_LOG (USER_KEY, QUESTION, ROUTE, GENERATED_SQL, ANSWER) VALUES (?, ?, ?, ?, ?)",
            [user_key, question, result.route, result.sql, result.answer],
        )
        add_message(
            "assistant",
            result.answer,
            route=result.route,
            sql=result.sql,
            sql_results=result.sql_results,
            search_results=result.search_results,
        )

    except Exception as exc:
        record_usage(user_key, "error", question, False)
        st.error(f"Request failed: {exc}")
