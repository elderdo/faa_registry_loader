import pytest
from convert import convert_schema

def test_convert_drop_and_create():
    sqlite_sql = '''
    DROP TABLE IF EXISTS "ACFTREF";
    CREATE TABLE IF NOT EXISTS "ACFTREF" (
        "CODE" TEXT PRIMARY KEY,
        "MFR" TEXT,
        "MODEL" TEXT
    );
    '''
    result = convert_schema(sqlite_sql)
    assert "IF OBJECT_ID('ACFTREF'" in result
    assert "CREATE TABLE [ACFTREF]" in result
    assert "[CODE] NVARCHAR(255) PRIMARY KEY" in result