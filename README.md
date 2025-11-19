
# ✈️ FAA Aircraft Registry Loader

This project automates the ingestion of the FAA Releasable Aircraft Registry into a normalized SQLite database. It downloads the latest ZIP archive, parses all 7 CSV-formatted `.txt` files, and loads them into structured tables with referential integrity.

---

## 📦 Features

- ✅ Downloads and parses the latest FAA registry ZIP
- ✅ Normalized schema with foreign keys and ergonomic naming
- ✅ Truncates old data before each load for freshness
- ✅ Logs row counts and errors for transparency
- ✅ Easily extendable to SQL Server or C# workflows

---

### 🗂️ File Structure

```text
faa-registry-loader/
├── src/
│   └── load_faa_registry.py     # Main Python loader
├── db/
│   ├── schema.sql               # SQLite schema with 7 tables
│   └── faa_registry.db          # Generated SQLite database
├── data/
│   └── ReleasableAircraft.zip   # FAA ZIP archive (optional)
├── .gitignore
├── README.md
└── requirements.txt
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
   git clone https://github.com/yourusername/faa-registry-loader.git
   cd faa-registry-loader
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the loader:

   ```bash
   python src/load_faa_registry.py
   ```

This will download the ZIP, truncate old data, and load fresh records into `db/faa_registry.db`.

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

### 🛠️ Extending

- Add SQL Server support via `pyodbc` or C# `SqlBulkCopy`
- Build dashboards with Power BI or Tableau
- Integrate with FAA lifecycle or compliance workflows

---

### Optional Tools

If you don't have SQLite, you can download them:

- [SQLite Command-Line Shell](https://www.sqlite.org/download.html): For inspecting the database manually via `.schema`, `.tables`, and SQL queries.
- [DB Browser for SQLite](https://sqlitebrowser.org/): A GUI tool for browsing tables, running queries, and inspecting data visually.

### 📄 License

MIT License — free to use, modify, and share.

---
