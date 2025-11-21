#!/usr/bin/env python3
"""
Script to fix database schema by creating missing tables.
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
try:
    from dotenv import load_dotenv
    env_path = project_root / ".env"
    load_dotenv(dotenv_path=env_path)
except ImportError:
    pass

from app.core.db import create_tables, get_engine
from sqlalchemy import inspect

def main():
    print("Fixing database schema...")
    
    # Check existing tables before
    engine = get_engine()
    inspector = inspect(engine)
    tables_before = inspector.get_table_names()
    print(f"Tables before: {tables_before}")
    
    # Create tables
    print("Running create_tables()...")
    create_tables()
    
    # Check existing tables after
    inspector = inspect(engine)
    tables_after = inspector.get_table_names()
    print(f"Tables after: {tables_after}")
    
    # Calculate added tables
    added = set(tables_after) - set(tables_before)
    if added:
        print(f"Successfully created tables: {added}")
    else:
        print("No new tables created (they might already exist).")

if __name__ == "__main__":
    main()
