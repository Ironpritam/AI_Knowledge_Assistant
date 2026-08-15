#!/usr/bin/env python
"""
Reset all databases for fresh testing
"""
import os
import shutil
from pathlib import Path

# Clear ChromaDB
vector_db_path = Path("storage/vector_db")
if vector_db_path.exists():
    shutil.rmtree(vector_db_path)
    print("✓ ChromaDB cleared")
else:
    print("✓ ChromaDB already empty")

# Clear PostgreSQL
os.system("""
psql -U postgres -d postgres -c "DROP DATABASE IF EXISTS ai_knowledge;"
psql -U postgres -d postgres -c "CREATE DATABASE ai_knowledge;"
echo "✓ PostgreSQL database reset"
""")

print("\n✓ All databases cleared. Start the app to re-run migrations.")