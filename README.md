
# ✈️ FAA Aircraft Registry Loader

This project automates the ingestion of the FAA Releasable Aircraft Registry into either SQLite or SQL Server databases. It downloads the latest ZIP archive, parses all 7 CSV-formatted `.txt` files, and loads them into structured tables with referential integrity.

---

## 📦 Features

- ✅ **Multi-database support**: Works with both SQLite and SQL Server
- ✅ **Modular architecture**: Clean separation of concerns for maintainability
- ✅ **Automatic database creation**: Creates databases automatically if they don't exist
- ✅ **Downloads and parses** the latest FAA registry ZIP
- ✅ **Normalized schema** with foreign keys and ergonomic naming
- ✅ **Duplicate detection**: Skips duplicate records based on primary keys
- ✅ **Batch loading**: Configurable batch sizes for optimal performance
- ✅ **Flexible configuration**: Command-line arguments for all options
- ✅ **Comprehensive logging**: Row counts, timing, and error reporting

---

### 🗂️ File Structure

```text
faa-registry-loader/
├── src/
│   ├── main.py                  # Main entry point with CLI
│   ├── load_faa_registry.py     # Legacy entry point (delegates to main.py)
│   ├── config.py                # Configuration and table definitions
│   ├── db_connection.py         # Database connection abstraction
│   ├── schema.py                # Schema initialization
│   ├── loader.py                # Data download and loading logic
│   └── convert.py               # SQLite to SQL Server schema converter
├── db/
│   ├── schema.sql               # SQLite schema with 7 tables
│   ├── schema_sqlserver.sql     # SQL Server schema (converted)
│   └── faa_registry.db          # Generated SQLite database
├── data/
│   └── ReleasableAircraft.zip   # FAA ZIP archive (downloaded)
├── tests/
│   └── test_*.py                # Unit tests for modules
├── .gitignore
├── README.md
├── requirements.txt
└── pytest.ini
```

---

### 🧱 Schema Overview

| Table       | Description                                |
|-------------|--------------------------------------------|
| `master`    | Active aircraft registrations              |
| `acftref`   | Aircraft reference data                    |
| `engine`    | Engine reference data                      |
| `dereg`     | Deregistered aircraft records              |
| `reserve`   | Reserved N-number records                  |
| `dealer`    | Aircraft dealer registrations              |
| `docindex`  | Document index for registration actions    |

Foreign keys link `master` to `acftref`, `engine`, and `docindex`.

                        ┌────────────┐
                        │  ACFTREF   │
                        │ (code PK)  │
                        └────┬───────┘
                             │
                             │
                             ▼
                         ┌────────┐
                         │ MASTER │
                         │(n_number PK)
                         └────┬────┘
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
     ┌────────┐          ┌────────┐           ┌──────────┐
     │ ENGINE │          │ DOCINDEX│          │  DEREG   │
     │(code PK)│          │(n_number FK)│      │(n_number)│
     └────────┘          └────────┘           └──────────┘

         ▼
     ┌──────────┐
     │ RESERVE  │
     │(n_number PK)│
     └──────────┘

         ▼
     ┌──────────┐
     │  DEALER  │
     │(dealer_no PK)│
     └──────────┘

---

📌 Legend:
• PK = Primary Key
• FK = Foreign Key
• links to ACFTREF and ENGINE via acft_code and eng_code
• DOCINDEX, DEREG, RESERVE and reference n_number, but ares not enforced via foreign keys (optional)

### 🚀 Getting Started

1. Clone the repo:

   ```bash
   git clone https://github.com/elderdo/faa-registry-loader.git
   cd faa-registry-loader
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the loader:

   **For SQLite (default):**
   ```bash
   python src/main.py
   ```

   **For SQL Server:**
   ```bash
   # Windows Authentication
   python src/main.py --engine sqlserver --server "SERVERNAME\INSTANCE" --trusted

   # SQL Authentication
   python src/main.py --engine sqlserver --server "SERVERNAME\INSTANCE" \
     --username your_user --password your_password
   ```

This will download the ZIP, create the database (if needed), initialize the schema, and load all tables.

---

### ⚙️ Command-Line Options

```bash
# General Options
--engine {sqlite,sqlserver}   # Database engine (default: sqlite)
--batch-size N                # Rows per batch insert (default: 5000)
--skip-download               # Skip ZIP download, use existing file

# SQLite Options
--db-path PATH                # SQLite database file path

# SQL Server Options
--server SERVER               # SQL Server hostname/instance (required)
--database DBNAME             # Database name (default: FAARegistry)
--trusted                     # Use Windows authentication
--username USER               # SQL Server username
--password PASS               # SQL Server password
--no-create-db                # Don't auto-create database
```

**Examples:**

```bash
# SQLite with custom path
python src/main.py --db-path /custom/path/faa.db

# SQL Server with custom database name
python src/main.py --engine sqlserver --server localhost \
  --database CustomFAA --trusted

# Skip download and use larger batches
python src/main.py --skip-download --batch-size 10000

# Legacy entry point (backward compatible)
python src/load_faa_registry.py
```

---

### 🧪 Sample Queries

```sql
-- Count active aircraft by state
SELECT state, COUNT(*) FROM master GROUP BY state ORDER BY COUNT(*) DESC;

-- Find aircraft with deregistration records
SELECT m."N-NUMBER", m."NAME", d."CANCEL-DATE", d."STATUS-CODE"
FROM master m
JOIN dereg d ON m."N-NUMBER" = d."N-NUMBER";
```

---

### 🏗️ Architecture

The project uses a modular architecture for maintainability and flexibility:

- **`config.py`**: Centralized configuration (URLs, paths, table definitions)
- **`db_connection.py`**: Database connection factory (SQLite/SQL Server abstraction)
- **`schema.py`**: Schema initialization with automatic SQLite→SQL Server conversion
- **`loader.py`**: Download and data loading with duplicate detection
- **`convert.py`**: Schema converter for SQL Server compatibility
- **`main.py`**: CLI orchestrator coordinating all modules

Benefits:
- ✅ **Testable**: Each module can be tested independently
- ✅ **Maintainable**: Single responsibility per module
- ✅ **Extensible**: Easy to add new database engines or features

---

### 🛠️ Extending

- ✅ **SQL Server support**: Already included with Windows and SQL authentication
- Build dashboards with Power BI or Tableau
- Integrate with FAA lifecycle or compliance workflows
- Add PostgreSQL or MySQL support following the modular pattern
- Implement incremental updates instead of full reloads

---

### Optional Tools

If you don't have SQLite, you can download them:

- [SQLite Command-Line Shell](https://www.sqlite.org/download.html): For inspecting the database manually via `.schema`, `.tables`, and SQL queries.
- [DB Browser for SQLite](https://sqlitebrowser.org/): A GUI tool for browsing tables, running queries, and inspecting data visually.

### 📄 License

MIT License — free to use, modify, and share.

---
