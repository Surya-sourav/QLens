#!/usr/bin/env python3
"""
Database initialization script for QLens application.
This script creates all necessary tables in the Neon PostgreSQL database.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from app.models.database import Base
from app.config import settings

def init_database():
    """Initialize the database with all tables."""
    print("Initializing database...")
    
    # Create engine
    database_url = settings.database_url
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg2://")
    
    engine = create_engine(database_url, echo=True)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    print("✅ Database initialization completed successfully!")

if __name__ == "__main__":
    init_database()
