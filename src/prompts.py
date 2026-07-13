# SCHEMA_DESCRIPTION = """
# FOCAL_PAPERS: selected papers with PAPER_ID, ARXIV_ID, TITLE, ABSTRACT, PUBLICATION_YEAR, PRIMARY_TOPIC, CITED_BY_COUNT, CITATIONS_PER_YEAR, IS_FOCAL, ARXIV_URL.
# PAPERS: same curated paper rows.
# CITATION_EDGES: CITING_PAPER_ID, CITED_PAPER_ID; both endpoints are in PAPERS.
# CITATION_RELATIONSHIPS: readable citation view with citing/cited titles, years, topics, and citation counts.
# Use FOCAL_PAPERS for rankings. Use CITATION_RELATIONSHIPS for citation questions.
# """

SCHEMA_DESCRIPTION = """
Table: FOCAL_PAPERS
Contains one row per paper in the curated research corpus.

Columns:
- PAPER_ID: Unique integer identifier for the paper.
- ARXIV_ID: Original arXiv identifier.
- TITLE: Paper title.
- ABSTRACT: Paper abstract.
- PUBLICATION_YEAR: Year the paper was published.
- PRIMARY_TOPIC: High-level research area assigned to the paper.
- CITED_BY_COUNT: Total number of citations the paper has received.
- CITATIONS_PER_YEAR: Average citations per year since publication.
- IS_FOCAL: True if the paper belongs to the curated top-cited corpus.
- ARXIV_URL: Link to the paper on arXiv.

Table: PAPERS
Contains the same curated paper metadata. Use only if specifically needed.

Columns:
- PAPER_ID
- TITLE
- ABSTRACT
- PUBLICATION_YEAR
- PRIMARY_TOPIC
- CITED_BY_COUNT
- CITATIONS_PER_YEAR
- ARXIV_URL

Table: CITATION_EDGES
Each row represents one citation relationship between two papers in the corpus.

Columns:
- CITING_PAPER_ID: PAPER_ID of the paper making the citation.
- CITED_PAPER_ID: PAPER_ID of the paper being cited.

Table: CITATION_RELATIONSHIPS
Human-readable citation view joining paper metadata.

Columns:
- CITING_TITLE
- CITED_TITLE
- CITING_YEAR
- CITED_YEAR
- CITING_TOPIC
- CITED_TOPIC
- CITING_CITATIONS
- CITED_CITATIONS

Guidelines:
- Use FOCAL_PAPERS for rankings, filtering, and statistics.
- Use CITATION_RELATIONSHIPS for citation graph questions.
- "Most cited" means order by CITED_BY_COUNT DESC.
- "Citation velocity" or "citations per year" means order by CITATIONS_PER_YEAR DESC.
- Never substitute CITATIONS_PER_YEAR when the user asks for total citations.
- Prefer the simplest possible SQL.
- Do not use CTEs (WITH clauses).
"""

# ROUTER_PROMPT = """Classify into exactly one route: direct, sql, rag, reject.
# direct: general AI/ML, citations, research, RAG, embeddings, or app explanations without database data.
# sql: filtering, counting, grouping, ranking, years, topics, citation counts, citation velocity, or citation relationships.
# rag: semantic understanding of titles/abstracts, methods, findings, similarity, summaries, or papers about a concept.
# reject: unrelated to AI/ML research, papers, citations, or this app.
# Return one lowercase word only.
# Context:
# {history}
# Question:
# {question}"""

ROUTER_PROMPT = """
You route requests for a research assistant over a curated ML/AI paper corpus.

Choose exactly one route:

direct:
A general question about AI, machine learning, research methods, citations,
RAG, embeddings, or how the application works. It does not require paper data.

sql:
A structured database question requiring exact filtering, counting, grouping,
ranking, publication years, citation counts, citation velocity, or explicit
citation relationships.

rag:
A semantic question requiring understanding paper titles or abstracts.
Use rag for requests to summarize, compare, explain, identify methods,
describe findings, discuss limitations, or find papers about a concept.

Examples of rag:
- Summarize the papers about multimodal representation learning.
- Which papers discuss efficient transformer inference?
- Compare the approaches used in diffusion-model papers.
- What methods do the retrieved papers use?

reject:
The request is unrelated to AI/ML research, research papers, citations,
or this application.

Return exactly one lowercase word:
direct, sql, rag, or reject.

Conversation context:
{history}

Current question:
{question}
"""


# SQL_GENERATION_PROMPT = """Write one safe Snowflake SELECT query. Return SQL only.
# {schema}
# Rules: use only PAPERS, FOCAL_PAPERS, CITATION_EDGES, CITATION_RELATIONSHIPS; one SELECT/WITH; no mutations; use ILIKE for fuzzy title/topic; limit <=100; no semicolon.
# Context:
# {history}
# Question:
# {question}"""

SQL_GENERATION_PROMPT = """
Write exactly one valid Snowflake SQL query that answers the user's question.

{schema}

Rules:
- Return only SQL.
- The first word must be SELECT.
- Do NOT use WITH clauses or CTEs.
- Write a single SELECT statement.
- Use only these tables/views:
  - FOCAL_PAPERS
  - PAPERS
  - CITATION_RELATIONSHIPS
  - CITATION_EDGES
- Use ORDER BY, GROUP BY, HAVING, subqueries, and JOINs if needed.
- Do not include markdown fences.
- Do not include explanations.
- Do not write phrases such as "Here is the query."
- The first word must be SELECT or WITH.
- Prefer FOCAL_PAPERS for rankings and paper metadata.
- Prefer CITATION_RELATIONSHIPS for citation questions.
- Generate exactly one SELECT or WITH query.
- Never use INSERT, UPDATE, DELETE, DROP, ALTER, CREATE,
  CALL, COPY, MERGE, GRANT, or REVOKE.
- Use ILIKE for fuzzy title or topic matching.
- Use NULLS LAST when sorting nullable fields.
- Limit results to 100 rows or fewer.
- Do not include a trailing semicolon.

Conversation context:
{history}

Question:
{question}
"""

DIRECT_PROMPT = """Answer clearly within AI/ML research, citations, or this app. Do not claim database access.
Context:
{history}
Question:
{question}"""
RAG_ANSWER_PROMPT = """Answer only from supplied titles, metadata, and abstracts. Do not claim full-paper access. Cite [Paper 1], [Paper 2], etc. Say when evidence is insufficient.
Context:
{history}
Question:
{question}
Evidence:
{evidence}"""
SQL_ANSWER_PROMPT = """Answer only from the SQL result. Mention key values and do not invent records.
Context:
{history}
Question:
{question}
SQL:
{sql}
Result:
{result}"""
REJECT_MESSAGE = """This question is outside the scope of this research assistant.

Please ask about highly cited ML/AI papers, citation statistics, citation relationships, paper abstracts, AI/ML research concepts, or how this application works."""
