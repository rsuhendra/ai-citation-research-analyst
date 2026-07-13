from src.chat_memory import conversation_context
from src.config import AppConfig
from src.cortex import ai_complete, dataframe_for_prompt, search_evidence_text, search_papers
from src.models import AssistantResult
from src.prompts import *
from src.snowflake_io import fetch_df
from src.sql_guard import validate_and_limit_sql
VALID={"direct","sql","rag","reject"}
def choose_route(question:str)->str:
    c=AppConfig.from_secrets(); raw=ai_complete(ROUTER_PROMPT.format(history=conversation_context(),question=question),c.router_model,8)
    route=raw.lower().strip().split()[0]
    return route if route in VALID else "reject"
def generate_sql(question:str)->str:
    c=AppConfig.from_secrets(); raw=ai_complete(SQL_GENERATION_PROMPT.format(schema=SCHEMA_DESCRIPTION,history=conversation_context(),question=question),c.main_model,700)
    return validate_and_limit_sql(raw,100)
def answer_question(question:str)->AssistantResult:
    c=AppConfig.from_secrets(); route=choose_route(question); history=conversation_context()
    if route=="reject": return AssistantResult(route,REJECT_MESSAGE)
    if route=="direct": return AssistantResult(route,ai_complete(DIRECT_PROMPT.format(history=history,question=question),c.main_model,700))
    if route=="rag":
        papers=search_papers(question,8)
        ans=ai_complete(RAG_ANSWER_PROMPT.format(history=history,question=question,evidence=search_evidence_text(papers)),c.main_model,1100)
        return AssistantResult(route,ans,search_results=papers)
    sql=generate_sql(question); results=fetch_df(sql)
    ans=ai_complete(SQL_ANSWER_PROMPT.format(history=history,question=question,sql=sql,result=dataframe_for_prompt(results)),c.main_model,900)
    return AssistantResult("sql",ans,sql=sql,sql_results=results)
