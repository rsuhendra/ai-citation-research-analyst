SCHEMA_DESCRIPTION = """
FOCAL_PAPERS: selected papers with PAPER_ID, ARXIV_ID, TITLE, ABSTRACT, PUBLICATION_YEAR, PRIMARY_TOPIC, CITED_BY_COUNT, CITATIONS_PER_YEAR, IS_FOCAL, ARXIV_URL.
PAPERS: same curated paper rows.
CITATION_EDGES: CITING_PAPER_ID, CITED_PAPER_ID; both endpoints are in PAPERS.
CITATION_RELATIONSHIPS: readable citation view with citing/cited titles, years, topics, and citation counts.
Use FOCAL_PAPERS for rankings. Use CITATION_RELATIONSHIPS for citation questions.
"""
ROUTER_PROMPT = """Classify into exactly one route: direct, sql, rag, reject.
direct: general AI/ML, citations, research, RAG, embeddings, or app explanations without database data.
sql: filtering, counting, grouping, ranking, years, topics, citation counts, citation velocity, or citation relationships.
rag: semantic understanding of titles/abstracts, methods, findings, similarity, summaries, or papers about a concept.
reject: unrelated to AI/ML research, papers, citations, or this app.
Return one lowercase word only.
Context:
{history}
Question:
{question}"""
SQL_GENERATION_PROMPT = """Write one safe Snowflake SELECT query. Return SQL only.
{schema}
Rules: use only PAPERS, FOCAL_PAPERS, CITATION_EDGES, CITATION_RELATIONSHIPS; one SELECT/WITH; no mutations; use ILIKE for fuzzy title/topic; limit <=100; no semicolon.
Context:
{history}
Question:
{question}"""
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
