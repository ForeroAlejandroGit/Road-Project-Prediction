"""
Script to reset the database by dropping all tables and recreating them.
Run this from the project root directory.
"""
import sqlite3
import sys
sys.path.append('..')

from src.config import Config
from src.models import init_db


def drop_all_tables() -> None:
    """Drop all existing tables in the database."""
    db = sqlite3.connect(Config.DATABASE)
    cursor = db.cursor()
    # Drop children first due to foreign keys
    cursor.execute('DROP TABLE IF EXISTS item')
    cursor.execute('DROP TABLE IF EXISTS unidad_funcional')
    cursor.execute('DROP TABLE IF EXISTS proyectos')
    db.commit()
    db.close()


def reset_database() -> None:
    """Drop all tables and recreate them with sample data."""
    print("Dropping existing tables...")
    drop_all_tables()
    print("✓ Tables dropped")
    
    print("\nRecreating tables and adding sample data...")
    init_db()
    print("✓ Database reset complete")


if __name__ == '__main__':
    reset_database()

