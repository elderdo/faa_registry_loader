"""Main Entry Point for FAA Registry Loader

This module orchestrates the complete FAA aircraft registry data loading process
by coordinating several specialized modules:

- db_connection: Handles database connectivity abstraction (SQLite/SQL Server)
- schema: Manages database schema creation and initialization
- loader: Performs the actual data extraction and loading from FAA ZIP files
- config: Provides centralized configuration (URLs, paths, table definitions)

The modular design separates concerns, making the codebase:
- More maintainable (each module has a single responsibility)
- More testable (modules can be tested independently)
- More flexible (easy to swap database engines or modify logic)
"""

import argparse  # For parsing command-line arguments
import os        # For environment variable access in error messages

# Import database connection factory - abstracts SQLite vs SQL Server differences
from db_connection import get_connection

# Import schema initialization - creates/recreates database tables
from schema import initialize_schema

# Import data loader - handles downloading and importing FAA data
from loader import run_loader, download_zip

# Import configuration constants - centralized settings for the application
from config import CONFIG


def parse_args():
    """
    Parse command-line arguments for database configuration and loading options.
    
    Provides flexible configuration through command-line interface, allowing users
    to specify database engine (SQLite or SQL Server), connection parameters,
    and loading options without modifying code.
    
    Returns:
        argparse.Namespace: Parsed arguments with all configuration options
    """
    parser = argparse.ArgumentParser(
        description="Load FAA Aircraft Registry data into SQLite or SQL Server"
    )
    
    # Database engine selection - determines which database system to use
    parser.add_argument(
        "--engine",
        choices=["sqlite", "sqlserver"],
        default="sqlite",
        help="Database engine to use (default: sqlite)"
    )
    
    # SQLite-specific options
    parser.add_argument(
        "--db-path",
        default=CONFIG["DB_PATH"],
        help="Path to SQLite database file (default: from CONFIG)"
    )
    
    # SQL Server-specific options
    parser.add_argument(
        "--server",
        help="SQL Server hostname or instance (required for sqlserver engine)"
    )
    parser.add_argument(
        "--database",
        default="FAARegistry",
        help="SQL Server database name (default: FAARegistry)"
    )
    parser.add_argument(
        "--trusted",
        action="store_true",
        help="Use Windows authentication for SQL Server (default: SQL auth)"
    )
    parser.add_argument(
        "--username",
        help="SQL Server username (required if not using --trusted)"
    )
    parser.add_argument(
        "--password",
        help="SQL Server password (required if not using --trusted)"
    )
    
    # Loading options
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5000,
        help="Number of rows to insert per batch (default: 5000)"
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip downloading ZIP file (use existing local file)"
    )
    parser.add_argument(
        "--no-create-db",
        action="store_true",
        help="Don't automatically create database if it doesn't exist (SQL Server only)"
    )
    
    args = parser.parse_args()
    
    # Validate SQL Server required arguments
    if args.engine == "sqlserver":
        if not args.server or not args.database:
            parser.error("--server and --database are required for SQL Server")
        if not args.trusted and (not args.username or not args.password):
            parser.error("--username and --password required when not using --trusted")
    
    return args


def create_sqlserver_database(args):
    """
    Create SQL Server database if it doesn't exist.
    
    Connects to the master database to check for and create the target database.
    This is necessary because SQL Server doesn't allow connecting to a non-existent
    database, unlike SQLite which creates the file automatically.
    
    Args:
        args: Parsed arguments containing server and database information
    """
    import pyodbc
    from urllib.parse import quote_plus
    
    print(f"🔍 Checking if database '{args.database}' exists...")
    
    # Connect to master database to create the target database
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={args.server};DATABASE=master;"
    )
    conn_str += "Trusted_Connection=yes;" if args.trusted else f"UID={args.username};PWD={quote_plus(args.password)};"
    
    try:
        # Connect with autocommit=True to allow CREATE DATABASE outside of transactions
        conn = pyodbc.connect(conn_str, autocommit=True)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(
            "SELECT database_id FROM sys.databases WHERE name = ?",
            (args.database,)
        )
        
        if cursor.fetchone():
            print(f"✅ Database '{args.database}' already exists.")
        else:
            # Create the database (autocommit mode allows this)
            print(f"🔨 Creating database '{args.database}'...")
            cursor.execute(f"CREATE DATABASE [{args.database}]")
            print(f"✅ Database '{args.database}' created successfully.")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        print("\nYou may need to:")
        print("  1. Grant CREATE DATABASE permission to your Windows user")
        print("  2. Create the database manually as a SQL Server admin")
        print("  3. Use SQL authentication with a user that has CREATE DATABASE rights")
        raise


def main():
    """
    Main orchestration function for the FAA registry loading process.
    
    This function coordinates the complete data loading workflow:
    1. Parse command-line arguments to determine database engine and connection params
    2. Download FAA ZIP file (unless --skip-download is specified)
    3. Establish database connection using the appropriate driver
    4. Initialize/recreate the database schema (tables and structure)
    5. Load FAA registry data from ZIP file into database tables
    6. Commit all changes and close the connection
    
    The modular approach means each step is handled by a specialized module,
    making the main flow easy to understand and modify. Error handling and
    transaction management are handled at this top level to ensure data integrity.
    """
    # Parse command-line arguments (engine type, connection details, batch size, etc.)
    # This allows the user to control behavior without modifying code
    args = parse_args()
    
    # Download the FAA ZIP file unless user specified --skip-download
    # This allows reusing an existing file during testing/development
    if not args.skip_download:
        download_zip(CONFIG["FAA_URL"], CONFIG["ZIP_PATH"])
    
    # For SQL Server, automatically create the database if it doesn't exist
    # (unless --no-create-db flag is specified). This matches SQLite behavior.
    if args.engine == "sqlserver" and not args.no_create_db:
        create_sqlserver_database(args)
    
    # Establish database connection using the factory pattern
    # get_connection() abstracts away SQLite vs SQL Server differences
    # Returns appropriate connection object based on args.engine
    try:
        conn = get_connection(args)
    except Exception as e:
        if args.engine == "sqlserver":
            print(f"\n❌ Failed to connect to SQL Server database '{args.database}'.")
            print("\nPossible causes:")
            print("  1. Database creation failed (check permissions)")
            print("  2. Windows user lacks SQL Server login permissions")
            print("  3. Incorrect server name or instance")
            print("\nTo fix login issues, run as SQL Server admin:")
            print(f"  sqlcmd -S {args.server} -E -Q \"CREATE LOGIN [{os.environ.get('COMPUTERNAME', 'COMPUTER')}\\{os.environ.get('USERNAME', 'USER')}] FROM WINDOWS\"")
            print(f"\nOriginal error: {e}")
        raise
    
    # Create a cursor for executing SQL statements
    # Cursor object provides method for running queries and managing results
    cursor = conn.cursor()
    
    # Initialize the database schema (create tables if needed)
    # This ensures the database structure is ready before loading data
    # Handles both SQLite and SQL Server schema differences
    initialize_schema(cursor, args.engine)
    
    # Load the FAA registry data from ZIP file into database tables
    # This is the core operation: extract and bulk insert with duplicate detection
    # Passes CONFIG dict, args namespace, and cursor to the loader module
    run_loader(CONFIG, args, cursor)
    
    # Commit all changes to make them permanent
    # This is critical - without commit, all work would be rolled back
    conn.commit()
    
    # Clean up: close the database connection and release resources
    conn.close()
    
    print("✅ FAA registry load complete.")


# Entry point: only execute main() when script is run directly
# This allows the module to be imported without executing main()
if __name__ == "__main__":
    main()