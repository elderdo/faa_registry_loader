# Standard library imports for file handling and data processing
import csv          # For reading CSV-formatted files
import io           # For handling in-memory text streams
import time         # For performance timing
import zipfile      # For extracting files from ZIP archives
import requests     # For HTTP requests to download files
import socket       # For network connection configuration
import requests.packages.urllib3.util.connection as urllib3_cn  # For forcing IPv4 connections
from config import CONFIG  # Application configuration settings

# ──────────────────────────────────────────────────────────────
# 📥 Download the FAA ZIP file
# ──────────────────────────────────────────────────────────────
def download_zip(url, zip_path):
    """
    Download the FAA aircraft registry ZIP file from the specified URL.
    
    This function forces IPv4 connections to avoid potential IPv6 issues
    with the FAA server. It uses a custom User-Agent header to ensure
    the request is accepted by the server.
    
    Args:
        url (str): The URL of the ZIP file to download
        zip_path (str): The local file path where the ZIP should be saved
    
    Raises:
        requests.HTTPError: If the download fails (non-200 status code)
    """
    import socket, requests, requests.packages.urllib3.util.connection as urllib3_cn
    # Force IPv4 connections only to avoid IPv6 connectivity issues
    urllib3_cn.allowed_gai_family = lambda: socket.AF_INET
    # Set User-Agent to mimic a browser request
    headers = {"User-Agent": "Mozilla/5.0"}
    print(f"📥 Downloading: {url}")
    # Download the file with a 30-second timeout
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()  # Raise an error for bad status codes
    # Write the downloaded content to disk
    with open(zip_path, "wb") as f:
        f.write(response.content)
    print("✅ Download complete.")

def truncate_tables(cursor, tables):
    """
    Remove all existing data from the specified database tables.
    
    This prepares the tables for fresh data loading by deleting all rows.
    Uses DELETE instead of TRUNCATE for better compatibility across
    different database systems.
    
    Args:
        cursor: Database cursor object for executing SQL statements
        tables (dict): Dictionary of table names (keys are used)
    """
    for table in tables:
        # Execute DELETE statement for each table (table names are lowercased)
        cursor.execute(f'DELETE FROM "{table.lower()}"')
    print("🧹 Tables truncated.")


def load_table_from_zip(zip_file, table_name, columns, cursor, batch_size=5000):
    """
    Load data from a CSV file within a ZIP archive into a database table.
    
    This function reads a CSV file from the ZIP, removes duplicates based on
    the first column (assumed to be the primary key), and inserts the data
    in batches for optimal performance.
    
    Args:
        zip_file (ZipFile): Open ZipFile object containing the data files
        table_name (str): Name of the database table to load
        columns (list): List of column names in the order they appear in the CSV
        cursor: Database cursor for executing SQL statements
        batch_size (int): Number of rows to insert per batch (default: 5000)
    """
    # Construct the filename within the ZIP (e.g., "MASTER.txt")
    filename = f"{table_name}.txt"
    # First column is used as the primary key for duplicate detection
    key_column = columns[0]
    # Quote column names for SQL safety (handles reserved words)
    quoted = [f'"{col}"' for col in columns]
    # Create placeholders for parameterized query (one ? per column)
    placeholders = ', '.join(['?' for _ in columns])
    # Build the INSERT SQL statement
    sql = f'INSERT INTO "{table_name}" ({", ".join(quoted)}) VALUES ({placeholders})'

    # Initialize tracking variables
    seen_keys = set()      # Track unique keys to prevent duplicates
    batch = []             # Accumulate rows for batch insertion
    total_inserted = 0     # Count of successfully inserted rows
    skipped = 0            # Count of duplicate/empty rows skipped

    # Open the CSV file from within the ZIP archive
    with zip_file.open(filename) as f:
        # Wrap the binary stream in a text wrapper with UTF-8 BOM handling
        reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig"))
        for row in reader:
            # Extract and clean the primary key value
            key = row.get(key_column, "").strip()
            # Only process rows with non-empty, unique keys
            if key and key not in seen_keys:
                seen_keys.add(key)  # Mark this key as seen
                # Build tuple of values in correct column order, stripping whitespace
                batch.append(tuple(row.get(col, "").strip() for col in columns))
                # When batch reaches target size, insert to database
                if len(batch) >= batch_size:
                    cursor.executemany(sql, batch)
                    total_inserted += len(batch)
                    batch.clear()  # Reset batch for next group
            else:
                skipped += 1  # Count duplicates or empty keys

        # Insert any remaining rows in the final partial batch
        if batch:
            cursor.executemany(sql, batch)
            total_inserted += len(batch)

    print(f"📦 Loaded {total_inserted:,} rows into {table_name.lower()} (skipped {skipped:,}).")


def run_loader(config, args, cursor):
    """
    Main orchestrator function for loading FAA registry data into the database.
    
    This function coordinates the complete loading process:
    1. Truncates all target tables to remove old data
    2. Opens the ZIP archive containing FAA data files
    3. Loads each table from its corresponding CSV file within the ZIP
    4. Reports timing information for each table
    
    Args:
        config (dict): Configuration dictionary containing TABLES and ZIP_PATH
        args: Command-line arguments object with batch_size attribute
        cursor: Database cursor for executing SQL statements
    """
    # First, clear all existing data from the tables
    truncate_tables(cursor, config["TABLES"])
    
    # Open the ZIP file containing all the FAA data files
    with zipfile.ZipFile(config["ZIP_PATH"]) as z:
        # Process each table defined in the configuration
        for table, columns in config["TABLES"].items():
            start = time.time()  # Start timing for this table
            # Load the data from the ZIP into the database table
            load_table_from_zip(z, table, columns, cursor, batch_size=args.batch_size)
            # Report how long this table took to load
            print(f"⏱️ {table} loaded in {time.time() - start:.2f} seconds")