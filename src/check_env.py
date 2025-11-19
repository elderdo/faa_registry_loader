import sys, platform, importlib.util

def check_module(name):
    spec = importlib.util.find_spec(name)
    return spec is not None

print("🔍 Checking Python environment...\n")

# Basic info
print(f"ℹ️ Python version: {platform.python_version()}")
print(f"ℹ️ Platform: {platform.system()} {platform.release()}")
print(f"ℹ️ Architecture: {platform.architecture()[0]}\n")

# Module checks
modules = {
    "pyodbc": check_module("pyodbc"),
    "sqlite3": check_module("sqlite3"),
    "requests": check_module("requests")
}

for name, available in modules.items():
    icon = "✅" if available else "❌"
    print(f"{icon} {name}: {'Available' if available else 'Missing'}")

# ODBC driver check (only if pyodbc is available)
if modules["pyodbc"]:
    import pyodbc
    drivers = pyodbc.drivers()
    print("\n🧩 Installed ODBC Drivers:")
    for d in drivers:
        print(f"  • {d}")
    if any("ODBC Driver 18" in d for d in drivers):
        print("✅ ODBC Driver 18 is installed.")
    elif any("ODBC Driver 17" in d for d in drivers):
        print("⚠️ ODBC Driver 17 is installed — works fine, but 18 is recommended.")
    else:
        print("❌ No Microsoft SQL Server ODBC driver found.")
else:
    print("\n⚠️ Skipping ODBC driver check — pyodbc is not installed.")

# Final verdict
missing = [k for k, v in modules.items() if not v]
if missing:
    print(f"\n✖ Environment check failed. Missing modules: {', '.join(missing)}")
else:
    print("\n✔ Environment check passed.")