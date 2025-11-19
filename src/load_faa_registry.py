"""FAA Registry Loader - Legacy Entry Point

This file serves as the original entry point for the FAA Registry Loader application.
It has been refactored into a modular architecture, with all functionality now
organized into separate, focused modules:

- config.py: Configuration settings and table definitions
- db_connection.py: Database connection abstraction (SQLite/SQL Server)
- schema.py: Database schema initialization
- loader.py: Data download and loading logic
- main.py: Main orchestration and command-line interface

This file now simply delegates to the refactored main() function, maintaining
backward compatibility for users who may have scripts or processes that call
this file directly.

For new usage, prefer calling main.py directly:
    python src/main.py --engine sqlite
    python src/main.py --engine sqlserver --server localhost --database FAA
"""

# Import the refactored main function from the main module
# This provides access to all the modular functionality
from main import main


# Entry point: delegate to the modularized main function
# This maintains backward compatibility while using the new architecture
if __name__ == "__main__":
    # Call the main orchestration function which handles:
    # - Command-line argument parsing
    # - Database connection setup
    # - Schema initialization
    # - Data downloading and loading
    # - Transaction management
    main()