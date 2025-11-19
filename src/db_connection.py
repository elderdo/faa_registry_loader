"""Database Connection Module

Provides unified database connection handling for both SQLite and SQL Server.
This abstraction allows the application to work with either database engine
by specifying connection parameters through command-line arguments.

Supported engines:
- SQLite: Lightweight, file-based database (default)
- SQL Server: Enterprise database with optional Windows authentication
"""

import sqlite3  # Built-in SQLite database driver
from urllib.parse import quote_plus  # URL-encode passwords with special characters

# pyodbc is optional - only needed for SQL Server connections
# Gracefully handle missing dependency with None fallback
try:
    import pyodbc
except ImportError:
    pyodbc = None  # Will trigger informative error if SQL Server is requested
    

def get_connection(args):
    """
    Create and return a database connection based on the specified engine.
    
    This function provides a unified interface for connecting to either SQLite
    or SQL Server databases. Connection parameters are extracted from the args
    object (typically populated from command-line arguments).
    
    Args:
        args: Namespace object containing connection parameters:
            - engine: Database type ("sqlite" or "sqlserver")
            - db_path: SQLite database file path (for SQLite)
            - server: SQL Server hostname/instance (for SQL Server)
            - database: Database name (for SQL Server)
            - trusted: Use Windows authentication (for SQL Server)
            - username: SQL Server login username (if not using trusted)
            - password: SQL Server login password (if not using trusted)
    
    Returns:
        Database connection object (sqlite3.Connection or pyodbc.Connection)
    
    Raises:
        RuntimeError: If pyodbc is not installed when SQL Server is requested
        ValueError: If an unsupported database engine is specified
    """
    # SQLite connection: Simple file-based database
    if args.engine == "sqlite":
        # Connect to SQLite database file (creates if doesn't exist)
        return sqlite3.connect(args.db_path)
    
    # SQL Server connection: Requires pyodbc and connection string
    elif args.engine == "sqlserver":
        # Verify pyodbc is available before attempting connection
        if not pyodbc:
            raise RuntimeError("pyodbc is required for SQL Server support.")
        
        # Build ODBC connection string with server and database
        # Using ODBC Driver 17 (newer versions like 18 also work)
        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={args.server};DATABASE={args.database};"
        )
        
        # Add authentication: Windows (trusted) or SQL Server (username/password)
        # Trusted_Connection uses current Windows user credentials
        # Password is URL-encoded to handle special characters safely
        conn_str += "Trusted_Connection=yes;" if args.trusted else f"UID={args.username};PWD={quote_plus(args.password)};"
        
        # Establish and return the connection
        return pyodbc.connect(conn_str)
    
    # Unsupported engine specified
    else:
        raise ValueError("Unsupported engine.")