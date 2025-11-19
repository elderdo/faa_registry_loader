from config import CONFIG
from convert import convert_schema

def initialize_schema(cursor, engine):
    schema_file = CONFIG["SCHEMA_PATH"]
    if engine == "sqlserver":
        with open(schema_file, "r", encoding="utf-8") as f:
            sqlite_sql = f.read()
        schema_sql = convert_schema(sqlite_sql)
        statements = [s.strip() for s in schema_sql.split(";") if s.strip()]
        for stmt in statements:
            cursor.execute(stmt)
    else:
        with open(schema_file, "r", encoding="utf-8") as f:
            cursor.executescript(f.read())
    print("🧱 Schema initialized.")