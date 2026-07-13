from __future__ import annotations
import os,re,time
from datetime import date
from typing import Any
import pandas as pd
import requests
from dotenv import load_dotenv
from src.snowflake_io import create_session
load_dotenv()
BASE="https://api.openalex.org"; YEARS=[2021,2022,2023,2024,2025]; N=20

def req(name:str)->str:
    v=os.getenv(name)
    if not v: raise RuntimeError(f"Missing environment variable: {name}")
    return v
class OA:
    def __init__(self):
        self.key=req("OPENALEX_API_KEY"); self.email=req("OPENALEX_EMAIL"); self.s=requests.Session(); self.s.headers["User-Agent"]=f"ai-citation-research-analyst/1.0 (mailto:{self.email})"
    def get(self,endpoint:str,params:dict[str,Any])->dict[str,Any]:
        r=self.s.get(f"{BASE}/{endpoint}",params={**params,"api_key":self.key,"mailto":self.email},timeout=60)
        if not r.ok: raise RuntimeError(f"OpenAlex {r.status_code}: {r.text}")
        time.sleep(.15); return r.json()
    def find(self,endpoint:str,term:str,exact:str|None=None)->str:
        rs=self.get(endpoint,{"search":term,"per_page":10})["results"]
        if exact:
            for x in rs:
                if x.get("display_name","").lower()==exact.lower(): return sid(x["id"])
        return sid(rs[0]["id"])
    def top(self,year:int,source:str,topics:list[str])->list[dict[str,Any]]:
        f=",".join([f"publication_year:{year}",f"locations.source.id:{source}","topics.id:"+"|".join(topics),"has_abstract:true","is_retracted:false"])
        rs=self.get("works",{"filter":f,"sort":"cited_by_count:desc","per_page":100}).get("results",[])
        return [w for w in rs if arxiv_id(w)][:N]
def sid(v:str)->str:return v.rstrip("/").split("/")[-1]
def abstract(idx):
    if not idx:return None
    pairs=[]
    for w,ps in idx.items():pairs.extend((p,w) for p in ps)
    return " ".join(w for _,w in sorted(pairs))
def arxiv_id(work):
    for loc in work.get("locations") or []:
        for key in ("landing_page_url","pdf_url"):
            u=loc.get(key)
            if u:
                m=re.search(r"arxiv\.org/(?:abs|pdf)/([^?#]+)",u,re.I)
                if m:return re.sub(r"\.pdf$","",m.group(1).strip("/"))
    return None
def record(w):
    pid=sid(w["id"]); aid=arxiv_id(w); title=w.get("display_name"); ab=abstract(w.get("abstract_inverted_index")); year=int(w["publication_year"]); cited=int(w.get("cited_by_count") or 0); topic=(w.get("primary_topic") or {}).get("display_name"); age=max(1,date.today().year-year+1)
    return {"PAPER_ID":pid,"ARXIV_ID":aid,"TITLE":title,"ABSTRACT":ab,"PUBLICATION_YEAR":year,"PRIMARY_TOPIC":topic,"CITED_BY_COUNT":cited,"CITATIONS_PER_YEAR":cited/age,"IS_FOCAL":True,"ARXIV_URL":f"https://arxiv.org/abs/{aid}" if aid else None,"TEXT_FOR_SEARCH":f"Title: {title or ''}\n\nTopic: {topic or ''}\n\nAbstract: {ab or ''}"}
def build():
    api=OA(); source=api.find("sources","arXiv","arXiv"); ml=api.find("topics","machine learning"); ai=api.find("topics","artificial intelligence"); works=[]
    for y in YEARS:
        batch=api.top(y,source,[ml,ai]); print(y,len(batch)); works.extend(batch)
    byid={sid(w["id"]):w for w in works}; papers=pd.DataFrame([record(w) for w in byid.values()]).drop_duplicates("PAPER_ID"); ids=set(papers.PAPER_ID); edges=[]
    for citing,w in byid.items():
        for raw in w.get("referenced_works") or []:
            cited=sid(raw)
            if cited in ids: edges.append({"CITING_PAPER_ID":citing,"CITED_PAPER_ID":cited})
    return papers,pd.DataFrame(edges,columns=["CITING_PAPER_ID","CITED_PAPER_ID"]).drop_duplicates()
def upload(papers,edges):
    s=create_session()
    try:
        s.sql("TRUNCATE TABLE PAPERS").collect(); s.sql("TRUNCATE TABLE CITATION_EDGES").collect(); s.create_dataframe(papers).write.mode("append").save_as_table("PAPERS")
        if not edges.empty:s.create_dataframe(edges).write.mode("append").save_as_table("CITATION_EDGES")
        print("Uploaded",len(papers),"papers and",len(edges),"edges")
    finally:s.close()
def main():
    p,e=build(); p.to_csv("papers_snapshot.csv",index=False); e.to_csv("citation_edges_snapshot.csv",index=False); upload(p,e)
if __name__=="__main__":main()
