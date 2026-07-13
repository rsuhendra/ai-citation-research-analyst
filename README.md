# AI Citation Research Analyst

A Streamlit + Snowflake research assistant over a fixed corpus of highly cited ML/AI arXiv papers.

## Routes

- `direct`: general AI/ML, citation, or app questions
- `sql`: structured questions over paper metadata and citation relationships
- `rag`: semantic questions over paper titles and abstracts
- `reject`: unrelated questions outside the project scope

There is intentionally no hybrid route.

## Dataset

The one-time build script selects 20 highly cited arXiv ML/AI papers for each year from 2021 through 2025.

`PAPERS` stores only: paper ID, arXiv ID, title, abstract, year, topic, citation count, citations/year, focal flag, URL, and search text.

`CITATION_EDGES` keeps only edges where both endpoints are already in `PAPERS`.

## Setup

1. Create a virtual environment and install dependencies.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Create `.env` for the one-time dataset build.

```bash
OPENALEX_API_KEY=your_key
OPENALEX_EMAIL=you@example.com
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=your_user
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_ROLE=E2E_SNOW_MLOPS_ROLE
SNOWFLAKE_WAREHOUSE=E2E_SNOW_MLOPS_WH
SNOWFLAKE_DATABASE=E2E_SNOW_MLOPS_DB
SNOWFLAKE_SCHEMA=MLOPS_SCHEMA
```

3. Run `sql/01_setup.sql`.
4. Run `python scripts/build_research_dataset.py` once.
5. Run `sql/02_views_and_search.sql`.
6. Run `sql/03_app_role.sql` and grant the role to your Streamlit user.
7. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and fill it in.
8. Run `streamlit run app.py`.

## Security

Generated SQL is parsed with SQLGlot, restricted to one SELECT/WITH statement, limited to allowlisted relations, and capped at 100 rows. The Streamlit Snowflake role should remain read-only except for prompt/query logging.
