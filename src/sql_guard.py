import re
import sqlglot
from sqlglot import exp
ALLOWED_RELATIONS={"PAPERS","FOCAL_PAPERS","CITATION_EDGES","CITATION_RELATIONSHIPS"}
FORBIDDEN=(exp.Insert,exp.Update,exp.Delete,exp.Drop,exp.Create,exp.Alter,exp.Command,exp.Merge,exp.Copy)
# def validate_and_limit_sql(sql: str, max_rows: int = 100) -> str:
#     cleaned=re.sub(r"^```sql\s*|\s*```$","",sql.strip().strip("`"),flags=re.I)
#     statements=sqlglot.parse(cleaned,read="snowflake")
#     if len(statements)!=1: raise ValueError("Exactly one SQL statement is permitted.")
#     tree=statements[0]
#     if not tree.find(exp.Select): raise ValueError("Only SELECT or WITH queries are permitted.")
#     for t in FORBIDDEN:
#         if tree.find(t): raise ValueError(f"Forbidden SQL operation: {t.__name__}")
#     relations={tbl.name.upper() for tbl in tree.find_all(exp.Table) if tbl.name}
#     bad=relations-ALLOWED_RELATIONS
#     if bad: raise ValueError("Non-allowlisted relations: "+", ".join(sorted(bad)))
#     if not tree.args.get("limit"): tree=tree.limit(max_rows)
#     return tree.sql(dialect="snowflake")

def validate_and_limit_sql(
    sql: str,
    max_rows: int = 100,
) -> str:
    cleaned = sql.strip().rstrip(";")

    statements = sqlglot.parse(
        cleaned,
        read="snowflake",
    )

    if len(statements) != 1:
        raise ValueError(
            "Exactly one SQL statement is permitted."
        )

    tree = statements[0]

    if not tree.find(exp.Select):
        raise ValueError(
            "Only SELECT or WITH queries are permitted."
        )

    for node_type in FORBIDDEN:
        if tree.find(node_type):
            raise ValueError(
                f"Forbidden SQL operation: "
                f"{node_type.__name__}"
            )

    relations = {
        table.name.upper()
        for table in tree.find_all(exp.Table)
        if table.name
    }

    disallowed = relations - ALLOWED_RELATIONS

    if disallowed:
        raise ValueError(
            "Query referenced non-allowlisted relations: "
            + ", ".join(sorted(disallowed))
        )

    if not tree.args.get("limit"):
        tree = tree.limit(max_rows)

    return tree.sql(dialect="snowflake")