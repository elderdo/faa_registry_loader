import pytest
from db_connection import get_connection
from unittest.mock import patch

def test_get_connection_sqlite():
    class Args:
        engine = "sqlite"
        db_path = ":memory:"
    conn = get_connection(Args())
    assert conn is not None
    conn.close()

def test_get_connection_invalid_engine():
    class Args:
        engine = "oracle"
    with pytest.raises(ValueError):
        get_connection(Args())

def test_sqlserver_connection_string_trusted():
    class Args:
        engine = "sqlserver"
        server = "localhost"
        database = "testdb"
        trusted = True
        username = None
        password = None

    with patch("db_connection.pyodbc.connect") as mock_connect:
        get_connection(Args())
        mock_connect.assert_called_once()
        assert "Trusted_Connection=yes" in mock_connect.call_args[0][0]