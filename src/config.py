import os

# ──────────────────────────────────────────────────────────────
# 📦 Configuration block — all paths and constants in one place
# ──────────────────────────────────────────────────────────────
# This module centralizes all configuration for the FAA Registry loader,
# including file paths, database locations, and table schema definitions.
# All paths are dynamically calculated relative to the project root to
# ensure portability across different systems and deployment environments.

# Auto-detect project root based on script location
# Goes up two levels from this file (src/config.py) to reach project root
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Main configuration dictionary containing all application settings
CONFIG = {
    # URL to download the FAA aircraft registry database (updated regularly by FAA)
    "FAA_URL": "https://registry.faa.gov/database/ReleasableAircraft.zip",
    
    # Local path where the downloaded ZIP file will be saved
    "ZIP_PATH": os.path.join(ROOT, "data", "ReleasableAircraft.zip"),
    
    # Path to the SQLite database file that will store the imported data
    "DB_PATH": os.path.join(ROOT, "db", "faa_registry.db"),
    
    # Path to the SQL schema file used to create the database structure
    "SCHEMA_PATH": os.path.join(ROOT, "db", "schema.sql"),
    
    # Table definitions: maps table names to their column lists
    # The column order must match the order in the FAA's CSV files
    # The first column in each list is treated as the primary key for duplicate detection
    "TABLES": {
        # ACFTREF: Aircraft Reference table - contains aircraft model specifications
        # Includes manufacturer, model codes, engine type, category, weight, and certification data
        "ACFTREF": [
            "CODE", "MFR", "MODEL", "TYPE-ACFT", "TYPE-ENG", "AC-CAT", "BUILD-CERT-IND",
            "NO-ENG", "NO-SEATS", "AC-WEIGHT", "SPEED", "TC-DATA-SHEET", "TC-DATA-HOLDER"
        ],
        
        # DEALER: Aircraft dealer certificate information
        # Contains dealer certificates, ownership details, and up to 25 alternate business names
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
        
        # DEREG: Deregistered aircraft records
        # Historical data for aircraft that have been removed from the registry
        # Includes registration details, owner information, and deregistration dates
        "DEREG": [
            "N-NUMBER", "SERIAL-NUMBER", "MFR-MDL-CODE", "STATUS-CODE", "NAME", "STREET-MAIL", "STREET2-MAIL",
            "CITY-MAIL", "STATE-ABBREV-MAIL", "ZIP-CODE-MAIL", "ENG-MFR-MDL", "YEAR-MFR", "CERTIFICATION",
            "REGION", "COUNTY-MAIL", "COUNTRY-MAIL", "AIR-WORTH-DATE", "CANCEL-DATE", "MODE-S-CODE",
            "INDICATOR-GROUP", "EXP-COUNTRY", "LAST-ACT-DATE", "CERT-ISSUE-DATE", "STREET-PHYSICAL",
            "STREET2-PHYSICAL", "CITY-PHYSICAL", "STATE-ABBREV-PHYSICAL", "ZIP-CODE-PHYSICAL",
            "COUNTY-PHYSICAL", "COUNTRY-PHYSICAL", "OTHER-NAMES(1)", "OTHER-NAMES(2)", "OTHER-NAMES(3)",
            "OTHER-NAMES(4)", "OTHER-NAMES(5)", "KIT MFR", "KIT MODEL", "MODE S CODE HEX"
        ],
        
        # DOCINDEX: Document index for aircraft-related legal documents
        # Tracks liens, security agreements, and other legal filings
        "DOCINDEX": [
            "TYPE-COLLATERAL", "COLLATERAL", "PARTY", "DOC-ID", "DRDATE", "PROCESSING-DATE", "CORR-DATE",
            "CORR-ID", "SERIAL-ID", "DOC-TYPE"
        ],
        
        # ENGINE: Aircraft engine reference data
        # Contains engine specifications including manufacturer, model, type, and power ratings
        "ENGINE": [
            "CODE", "MFR", "MODEL", "TYPE", "HORSEPOWER", "THRUST"
        ],
        
        # MASTER: Main aircraft registration table
        # The primary table containing all currently registered aircraft in the US
        # Includes N-numbers, owner details, aircraft specs, certification, and airworthiness dates
        "MASTER": [
            "N-NUMBER", "SERIAL NUMBER", "MFR MDL CODE", "ENG MFR MDL", "YEAR MFR", "TYPE REGISTRANT", "NAME",
            "STREET", "STREET2", "CITY", "STATE", "ZIP CODE", "REGION", "COUNTY", "COUNTRY",
            "LAST ACTION DATE", "CERT ISSUE DATE", "CERTIFICATION", "TYPE AIRCRAFT", "TYPE ENGINE",
            "STATUS CODE", "MODE S CODE", "FRACT OWNER", "AIR WORTH DATE", "OTHER NAMES(1)", "OTHER NAMES(2)",
            "OTHER NAMES(3)", "OTHER NAMES(4)", "OTHER NAMES(5)", "EXPIRATION DATE", "UNIQUE ID",
            "KIT MFR", "KIT MODEL", "MODE S CODE HEX"
        ],
        
        # RESERVED: Reserved N-numbers
        # Contains N-numbers that have been reserved but not yet registered to an aircraft
        # Includes reservation dates, expiration dates, and registrant information
        "RESERVED": [
            "N-NUMBER", "REGISTRANT", "STREET", "STREET2", "CITY", "STATE", "ZIP CODE", "RSV DATE", "TR",
            "EXP DATE", "N-NUM-CHG", "PURGE DATE"
        ]
    }
}