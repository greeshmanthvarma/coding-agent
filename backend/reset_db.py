"""
Script to drop all database tables and recreate them with the current schema.
WARNING: This will delete all data in the database!

Run this script from the backend directory:
    python3 -m app.reset_db
    OR
    python3 reset_db.py
"""
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect
from app.database import Base, engine
from app.models import User, Session, Message, Review

load_dotenv()

def drop_all_tables():
    """Drop all tables in the database."""
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("✓ All tables dropped")

def create_all_tables():
    """Create all tables based on current models."""
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ All tables created")

def list_tables():
    """List all tables in the database."""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    if tables:
        print(f"\nCurrent tables in database:")
        for table in tables:
            print(f"  - {table}")
    else:
        print("\nNo tables in database")
    return tables

if __name__ == "__main__":
    print("=" * 50)
    print("Database Reset Script")
    print("=" * 50)
    
    # List current tables
    print("\n1. Checking current database state...")
    list_tables()
    
    # Drop all tables
    print("\n2. Dropping all tables...")
    drop_all_tables()
    
    # Create all tables
    print("\n3. Creating all tables with new schema...")
    create_all_tables()
    
    # Verify tables were created
    print("\n4. Verifying tables were created...")
    tables = list_tables()
    
    print("\n" + "=" * 50)
    print("Database reset complete!")
    print("=" * 50)
    print(f"\nCreated {len(tables)} table(s):")
    for table in tables:
        print(f"  ✓ {table}")

