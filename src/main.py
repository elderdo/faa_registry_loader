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

# Import database connection factory - abstracts SQLite vs SQL Server differences
from db_connection import get_connection

# Import schema initialization - creates/recreates database tables
from schema import initialize_schema

# Import data loader - handles downloading and importing FAA data
from loader import run_loader

# Import configuration constants - centralized settings for the application
from config import CONFIG


def main():
    """
    Main orchestration function for the FAA registry loading process.
    
    This function coordinates the complete data loading workflow:
    1. Parse command-line arguments to determine database engine and connection params
    2. Establish database connection using the appropriate driver
    3. Initialize/recreate the database schema (tables and structure)
    4. Load FAA registry data from ZIP file into database tables
    5. Commit all changes and close the connection
    
    The modular approach means each step is handled by a specialized module,
    making the main flow easy to understand and modify. Error handling and
    transaction management are handled at this top level to ensure data integrity.
    """
    # Parse command-line arguments (engine type, connection details, batch size, etc.)
    # This allows the user to control behavior without modifying code
    args = parse_args()
    
    # Establish database connection using the factory pattern
    # get_connection() abstracts away SQLite vs SQL Server differences
    # Returns appropriate connection object based on args.engine
    conn = get_connection(args)
    
    # Create a cursor for executing SQL statements
    # Cursor object provides method for running queries and managing results
    cursor = conn.cursor()
    
    # Initialize the database schema (create tables if needed)
    # This ensures the database structure is ready before loading data
    # Handles both SQLite and SQL Server schema differences
    initialize_schema(cursor, args.engine)
    
    # Load the FAA registry data from ZIP file into database tables
    # This is the core operation: download (if needed), extract, and bulk insert
    # Processes multiple tables defined in CONFIG with duplicate detection
    run_loader(args, cursor)
    
    # Commit all changes to make them permanent
    # This is critical - without commit, all work would be rolled back
    conn.commit()
    
    # Clean up: close the database connection and release resources
    conn.close()