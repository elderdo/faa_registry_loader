"""Schema Conversion Module for SQLite to SQL Server

This module provides functionality to convert SQLite database schema (DDL)
to SQL Server compatible T-SQL syntax. It handles differences in:
- Data type mappings (TEXT -> NVARCHAR, INTEGER -> INT)
- Table creation syntax (IF NOT EXISTS -> IF OBJECT_ID)
- Column name quoting (double quotes -> square brackets)
- Primary key column type optimization
"""

import re

# Data type mapping from SQLite types to SQL Server types
# This dictionary defines the default conversions for standard types
TYPE_MAP = {
    "TEXT": "NVARCHAR(MAX)",  # Text fields default to max length for flexibility
    "INTEGER": "INT",          # SQLite INTEGER maps to SQL Server INT
    "DATE": "DATE"             # DATE type is compatible in both systems
}

def convert_type(sqlite_type, is_key=False):
    """
    Convert a SQLite data type to its SQL Server equivalent.
    
    Special handling for TEXT fields: primary key columns are limited to
    NVARCHAR(255) for indexing efficiency, while regular TEXT fields use
    NVARCHAR(MAX) for maximum flexibility.
    
    Args:
        sqlite_type (str): The SQLite data type (e.g., "TEXT", "INTEGER")
        is_key (bool): Whether this column is a primary key (default: False)
    
    Returns:
        str: The equivalent SQL Server data type
    """
    # TEXT fields need special handling based on whether they're primary keys
    if sqlite_type.upper() == "TEXT":
        # Primary keys limited to 255 chars for better index performance
        # Regular TEXT fields use MAX for unlimited storage
        return "NVARCHAR(255)" if is_key else "NVARCHAR(MAX)"
    # Look up other types in the mapping dictionary, return as-is if not found
    return TYPE_MAP.get(sqlite_type.upper(), sqlite_type)

def convert_schema(sqlite_sql):
    """
    Convert a complete SQLite schema SQL script to SQL Server T-SQL format.
    
    This function processes SQLite DDL statements line by line and converts them
    to SQL Server compatible syntax. It handles:
    - DROP TABLE statements (IF EXISTS -> IF OBJECT_ID)
    - CREATE TABLE statements (IF NOT EXISTS -> conditional check)
    - Column definitions (type conversion and bracket quoting)
    - Trailing comma removal before closing parenthesis
    
    Args:
        sqlite_sql (str): Complete SQLite schema as a multi-line string
    
    Returns:
        str: SQL Server compatible T-SQL schema script
    """
    output_lines = []           # Accumulated output lines for the converted schema
    lines = sqlite_sql.splitlines()  # Split input into individual lines
    inside_create = False       # Flag to track if we're inside a CREATE TABLE block
    table_name = ""             # Current table being processed

    # Process each line of the input SQL
    for line in lines:
        stripped = line.strip()
        
        # Convert SQLite's "DROP TABLE IF EXISTS" to SQL Server's IF OBJECT_ID pattern
        if stripped.upper().startswith("DROP TABLE IF EXISTS"):
            # Extract table name from the DROP statement
            table = re.findall(r"DROP TABLE IF EXISTS\s+\"?(\w+)\"?;", stripped, re.IGNORECASE)
            if table:
                # SQL Server checks for object existence using OBJECT_ID
                # 'U' parameter specifies user tables
                output_lines.append(f"IF OBJECT_ID('{table[0]}', 'U') IS NOT NULL DROP TABLE [{table[0]}];")
            continue
        # Convert SQLite's "CREATE TABLE IF NOT EXISTS" to SQL Server syntax
        if stripped.upper().startswith("CREATE TABLE IF NOT EXISTS"):
            # Extract the table name from the CREATE statement
            table_name = re.findall(r"CREATE TABLE IF NOT EXISTS\s+\"?(\w+)\"?", stripped, re.IGNORECASE)[0]
            # SQL Server uses square brackets for identifiers instead of double quotes
            output_lines.append(f"CREATE TABLE [{table_name}] (")
            inside_create = True  # Mark that we're now processing column definitions
            continue
        # Process lines inside a CREATE TABLE statement
        if inside_create:
            # Check for the closing parenthesis that ends the table definition
            if stripped == ");":
                output_lines.append(");")
                inside_create = False  # Exit the CREATE TABLE block
                continue
            
            # Parse column definitions: "column_name" TYPE [constraints]
            col_match = re.match(r'"(.+?)"\s+(\w+)(.*)', stripped.rstrip(","))
            if col_match:
                col_name, col_type, extras = col_match.groups()
                # Check if this column is a primary key to optimize type selection
                is_primary_key = "PRIMARY KEY" in extras.upper()
                # Convert the SQLite type to SQL Server type
                sql_type = convert_type(col_type, is_key=is_primary_key)
                # Format with square brackets and add trailing comma
                output_lines.append(f"    [{col_name}] {sql_type}{extras},")
            else:
                # Handle any other lines within CREATE TABLE (constraints, etc.)
                output_lines.append("    " + stripped)

    # Post-processing: Remove trailing commas before closing parentheses
    # SQL Server doesn't allow a comma after the last column definition
    for i in range(len(output_lines) - 1):
        if output_lines[i].strip().endswith(",") and output_lines[i + 1].strip() == ");":
            # Remove the trailing comma from the last column
            output_lines[i] = output_lines[i].rstrip(",")

    # Join all lines back into a single string with newlines
    return "\n".join(output_lines)