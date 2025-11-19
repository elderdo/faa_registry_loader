import io, zipfile, csv
from loader import load_table_from_zip

def test_load_table_from_zip_inserts_unique_rows(tmp_path):
    # Create a fake ZIP with a sample table
    table_name = "TEST"
    columns = ["ID", "NAME"]
    data = "ID,NAME\n1,Alice\n2,Bob\n1,Alice\n"
    zip_path = tmp_path / "test.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr(f"{table_name}.txt", data)

    # Setup in-memory SQLite
    import sqlite3
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE "TEST" ("ID" TEXT, "NAME" TEXT)')

    # Run loader
    with zipfile.ZipFile(zip_path, "r") as zf:
        load_table_from_zip(zf, table_name, columns, cursor)

    cursor.execute("SELECT COUNT(*) FROM TEST")
    assert cursor.fetchone()[0] == 2  # deduplicated by ID