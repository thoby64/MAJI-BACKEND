#!/usr/bin/env python
"""
Database Initialization Script
Creates all database tables based on SQLAlchemy models
Usage: python init_db.py
"""

import sys
from app.database.session import engine
from app.models import Base

def init_db():
    """Create all database tables"""
    print("=" * 60)
    print("🗄️  Majiscope Database Initialization")
    print("=" * 60)
    
    try:
        print("\n📝 Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        print("\n📊 Tables created:")
        for table_name in Base.metadata.tables.keys():
            print(f"   - {table_name}")
        print("\n" + "=" * 60)
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = init_db()
    sys.exit(0 if success else 1)
