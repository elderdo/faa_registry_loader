import os
import csv
import io
import sqlite3
import zipfile
import requests

# ──────────────────────────────────────────────────────────────
# 📦 Configuration block — all paths and constants in one place
# ──────────────────────────────────────────────────────────────

# Auto-detect project root based on script location
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Configurable paths and constants
CONFIG = {
    "FAA_URL": "https://registry.faa.gov/database/ReleasableAircraft.zip",
    "ZIP_PATH": os.path.join(ROOT, "data", "ReleasableAircraft.zip"),
    "DB_PATH": os.path.join(ROOT, "db", "faa_registry.db"),
    "SCHEMA_PATH": os.path.join(ROOT, "db", "schema.sql"),
    "TABLES": {
        "ACFTREF": [
            "CODE", "MFR", "MODEL", "TYPE-ACFT", "TYPE-ENG", "AC-CAT", "BUILD-CERT-IND",
            "NO-ENG", "NO-SEATS", "AC-WEIGHT", "SPEED", "TC-DATA-SHEET", "TC-DATA-HOLDER"
        ],
        "DEALER": [
            "CERTIFICATE-NUMBER", "OWNERSHIP", "CERTIFICATE-DATE", "EXPIRATION-DATE", "EXPIRATION-FLAG",
            "CERTIFICATE-ISSUE-COUNT", "NAME", "STREET", "STREET2", "CITY", "STATE-ABBREV", "ZIP-CODE",
            "OTHER-NAMES-COUNT", "OTHER-NAMES-1", "OTHER-NAMES-2", "OTHER-NAMES-3", "OTHER-NAMES-4",
            "OTHER-NAMES-5", "OTHER-NAMES-6", "OTHER-NAMES-7", "OTHER-NAMES-8", "OTHER-NAMES-9",
            "OTHER-NAMES-10", "OTHER-NAMES-11", "OTHER-NAMES-12", "OTHER-NAMES-13", "OTHER-NAMES-14",
            "OTHER-NAMES-15", "OTHER-NAMES-16", "OTHER-NAMES-17", "OTHER-NAMES-18", "OTHER-NAMES-19",
            "OTHER-NAMES-20", "OTHER-NAMES-21", "OTHER-NAMES-22", "OTHER-NAMES-23", "OTHER-NAMES-24",
            "OTHER-NAMES-25"
        ],
        "DEREG": [
            "N-NUMBER", "SERIAL-NUMBER", "MFR-MDL-CODE", "STATUS-CODE", "NAME", "STREET-MAIL", "STREET2-MAIL",
            "CITY-MAIL", "STATE-ABBREV-MAIL", "ZIP-CODE-MAIL", "ENG-MFR-MDL", "YEAR-MFR", "CERTIFICATION",
            "REGION", "COUNTY-MAIL", "COUNTRY-MAIL", "AIR-WORTH-DATE", "CANCEL-DATE", "MODE-S-CODE",
            "INDICATOR-GROUP", "EXP-COUNTRY", "LAST-ACT-DATE", "CERT-ISSUE-DATE", "STREET-PHYSICAL",
            "STREET2-PHYSICAL", "CITY-PHYSICAL", "STATE-ABBREV-PHYSICAL", "ZIP-CODE-PHYSICAL",
            "COUNTY-PHYSICAL", "COUNTRY-PHYSICAL", "OTHER-NAMES(1)", "OTHER-NAMES(2)", "OTHER-NAMES(3)",
            "OTHER-NAMES(4)", "OTHER-NAMES(5)", "KIT MFR", "KIT MODEL", "MODE S CODE HEX"
        ],
        "DOCINDEX": [
            "TYPE-COLLATERAL", "COLLATERAL", "PARTY", "DOC-ID", "DRDATE", "PROCESSING-DATE", "CORR-DATE",
            "CORR-ID", "SERIAL-ID", "DOC-TYPE"
        ],
        "ENGINE": [
            "CODE", "MFR", "MODEL", "TYPE", "HORSEPOWER", "THRUST"
        ],
        "MASTER": [
            "N-NUMBER", "SERIAL NUMBER", "MFR MDL CODE", "ENG MFR MDL", "YEAR MFR", "TYPE REGISTRANT", "NAME",
            "STREET", "STREET2", "CITY", "STATE", "ZIP CODE", "REGION", "COUNTY", "COUNTRY",
            "LAST ACTION DATE", "CERT ISSUE DATE", "CERTIFICATION", "TYPE AIRCRAFT", "TYPE ENGINE",
            "STATUS CODE", "MODE S CODE", "FRACT OWNER", "AIR WORTH DATE", "OTHER NAMES(1)", "OTHER NAMES(2)",
            "OTHER NAMES(3)", "OTHER NAMES(4)", "OTHER NAMES(5)", "EXPIRATION DATE", "UNIQUE ID",
            "KIT MFR", "KIT MODEL", "MODE S CODE HEX"
        ],
        "RESERVED": [
            "N-NUMBER", "REGISTRANT", "STREET", "STREET2", "CITY", "STATE", "ZIP CODE", "RSV DATE", "TR",
            "EXP DATE", "N-NUM-CHG", "PURGE DATE"
        ]
    }
}

# ──────────────────────────────────────────────────────────────
# 📥 Download the FAA ZIP file
# ──────────────────────────────────────────────────────────────

def download_zip():
    """Download the FAA ZIP file with IPv4 and browser headers."""
    try:
        print("📥 Starting download from:", CONFIG["FAA_URL"])
        # Force IPv4
        import socket
        import requests.packages.urllib3.util.connection as urllib3_cn
        urllib3_cn.allowed_gai_family = lambda: socket.AF_INET

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }

        response = requests.get(CONFIG["FAA_URL"], headers=headers, timeout=30)
        response.raise_for_status()

        with open(CONFIG["ZIP_PATH"], "wb") as f:
            f.write(response.content)

        print("✅ Download complete.")
    except Exception as e:
        print(f"❌ Error downloading ZIP: {e}")
        raise

# ──────────────────────────────────────────────────────────────
# 🧱 Initialize the SQLite schema from schema.sql
# ──────────────────────────────────────────────────────────────

def initialize_schema(cursor):
    """Create tables from schema.sql if they don't already exist."""
    try:
        with open(CONFIG["SCHEMA_PATH"], "r") as f:
            cursor.executescript(f.read())
        print("🧱 Schema initialized from schema.sql.")
    except Exception as e:
        print(f"❌ Error initializing schema: {e}")
        raise

# ──────────────────────────────────────────────────────────────
# 🧹 Truncate all FAA tables before reloading
# ──────────────────────────────────────────────────────────────

def truncate_tables(cursor):
    """Truncate all FAA tables to prepare for fresh load."""
    try:
        for table in CONFIG["TABLES"]:
            cursor.execute(f"DELETE FROM {table.lower()}")
        print("🧹 All tables truncated.")
    except Exception as e:
        print(f"❌ Error truncating tables: {e}")
        raise

# ──────────────────────────────────────────────────────────────
# 📦 Load a single FAA table from the ZIP into SQLite
# ──────────────────────────────────────────────────────────────

def load_table_from_zip(zip_file, table_name, cursor):
    """Load a single FAA table from the ZIP file into SQLite, skipping duplicates based on primary key."""
    try:
        filename = f"{table_name}.txt"
        columns = CONFIG["TABLES"][table_name]

        with zip_file.open(filename) as f:
            reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig"))

            seen_keys = set()
            rows = []
            skipped = 0

            # Use first column as deduplication key (usually the primary key)
            key_column = columns[0]

            for row in reader:
                key = row.get(key_column, "").strip()
                if key and key not in seen_keys:
                    seen_keys.add(key)
                    rows.append(tuple(row.get(col, "").strip() for col in columns))
                else:
                    skipped += 1

            quoted_columns = [f'"{col}"' for col in columns]
            placeholders = ', '.join(['?' for _ in columns])

            cursor.executemany(
                f'INSERT INTO "{table_name}" ({", ".join(quoted_columns)}) VALUES ({placeholders})',
                rows
            )

        print(f"📦 Loaded {len(rows):,} rows into {table_name.lower()} (skipped {skipped:,} duplicates).")
    except Exception as e:
        print(f"❌ Error loading {table_name}: {e}")
        raise
    
# ──────────────────────────────────────────────────────────────
# 🚀 Main workflow: download, extract, load
# ──────────────────────────────────────────────────────────────

def main():
    """Main function to download, extract, and load FAA registry data."""
    try:
        # Step 1: Download the ZIP file
        download_zip()

        # Step 2: Connect to SQLite database
        conn = sqlite3.connect(CONFIG["DB_PATH"])
        cursor = conn.cursor()

        # Step 3: Initialize schema from schema.sql
        initialize_schema(cursor)

        # Step 4: Truncate existing data
        truncate_tables(cursor)

        # Step 5: Load each table from the ZIP
        with zipfile.ZipFile(CONFIG["ZIP_PATH"]) as z:
            for table in CONFIG["TABLES"]:
                load_table_from_zip(z, table, cursor)

        # Step 6: Commit and close
        conn.commit()
        conn.close()
        print("✅ FAA registry load complete.")
    except Exception as e:
        print(f"🚨 Fatal error: {e}")

if __name__ == "__main__":
    main()