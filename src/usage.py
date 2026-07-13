import hashlib, uuid
import streamlit as st
from src.snowflake_io import execute, fetch_df

def get_user_key()->str:
    try:
        if getattr(st.user,"is_logged_in",False):
            email=getattr(st.user,"email",None)
            if email:return "user:"+str(email).strip().lower()
    except Exception: pass
    if "anonymous_user_key" not in st.session_state: st.session_state["anonymous_user_key"]="session:"+str(uuid.uuid4())
    return st.session_state["anonymous_user_key"]

def get_usage_count(user_key:str)->int:
    df=fetch_df("SELECT COUNT(*) AS N FROM PROMPT_USAGE WHERE USER_KEY=? AND USAGE_DATE=CURRENT_DATE() AND SUCCEEDED=TRUE",[user_key])
    return int(df.iloc[0]["N"])

def enforce_limit(user_key:str,daily_limit:int)->None:
    if get_usage_count(user_key)>=daily_limit: raise RuntimeError(f"Daily prompt limit reached ({daily_limit}/{daily_limit}).")

def record_usage(user_key:str,route:str,question:str,succeeded:bool)->None:
    execute("INSERT INTO PROMPT_USAGE (USER_KEY,ROUTE,QUESTION_HASH,SUCCEEDED) VALUES (?,?,?,?)",[user_key,route,hashlib.sha256(question.encode()).hexdigest(),succeeded])
