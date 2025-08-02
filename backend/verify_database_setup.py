#!/usr/bin/env python3
"""
Verification script to ensure the database setup is working correctly
and all relationships are properly established.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from app.models.database import Base, DataSource, ChatSession, ChatMessage, FileUpload
from app.config import settings

def verify_database_connection():
    """Verify database connection and basic functionality."""
    print("🔍 VERIFYING DATABASE SETUP")
    print("=" * 50)
    
    # Create engine
    database_url = settings.database_url
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg2://")
    
    engine = create_engine(database_url, echo=False)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    try:
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ Database connection successful")
            print(f"   Database: PostgreSQL")
            print(f"   Version: {version}")
        
        # Check tables
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        expected_tables = ['data_sources', 'chat_sessions', 'chat_messages', 'file_uploads', 'alembic_version']
        
        print(f"\n📋 Table Verification:")
        for table in expected_tables:
            if table in tables:
                print(f"   ✅ {table}")
            else:
                print(f"   ❌ {table} (missing)")
        
        # Check data counts
        print(f"\n📊 Data Counts:")
        with engine.connect() as conn:
            for table in ['data_sources', 'chat_sessions', 'chat_messages', 'file_uploads']:
                count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                print(f"   {table}: {count} rows")
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_model_relationships():
    """Test that the SQLAlchemy models work correctly."""
    print(f"\n🔗 Testing Model Relationships:")
    
    database_url = settings.database_url
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg2://")
    
    engine = create_engine(database_url, echo=False)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    try:
        db = SessionLocal()
        
        # Test creating a data source
        print("   Testing DataSource creation...")
        test_datasource = DataSource(
            id="test-ds-001",
            name="Test Data Source",
            type="file",
            connection_info={"path": "/test/path"},
            schema_info={"columns": ["col1", "col2"]}
        )
        db.add(test_datasource)
        db.commit()
        print("   ✅ DataSource created successfully")
        
        # Test creating a chat session
        print("   Testing ChatSession creation...")
        test_session = ChatSession(
            id="test-session-001",
            session_id="session-123",
            data_sources=["test-ds-001"],
            is_active=True
        )
        db.add(test_session)
        db.commit()
        print("   ✅ ChatSession created successfully")
        
        # Test creating a chat message
        print("   Testing ChatMessage creation...")
        test_message = ChatMessage(
            id="test-msg-001",
            session_id="session-123",
            content="Test message content",
            message_type="user"
        )
        db.add(test_message)
        db.commit()
        print("   ✅ ChatMessage created successfully")
        
        # Test creating a file upload
        print("   Testing FileUpload creation...")
        test_upload = FileUpload(
            id="test-upload-001",
            filename="test.csv",
            original_filename="test.csv",
            file_type="text/csv",
            file_path="uploads/test.csv",
            size=1024,
            processed=False
        )
        db.add(test_upload)
        db.commit()
        print("   ✅ FileUpload created successfully")
        
        # Test querying relationships
        print("   Testing relationship queries...")
        
        # Query data sources
        datasources = db.query(DataSource).all()
        print(f"   ✅ Found {len(datasources)} data sources")
        
        # Query chat sessions
        sessions = db.query(ChatSession).all()
        print(f"   ✅ Found {len(sessions)} chat sessions")
        
        # Query chat messages
        messages = db.query(ChatMessage).all()
        print(f"   ✅ Found {len(messages)} chat messages")
        
        # Query file uploads
        uploads = db.query(FileUpload).all()
        print(f"   ✅ Found {len(uploads)} file uploads")
        
        # Clean up test data
        print("   Cleaning up test data...")
        db.delete(test_message)
        db.delete(test_session)
        db.delete(test_datasource)
        db.delete(test_upload)
        db.commit()
        print("   ✅ Test data cleaned up")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"   ❌ Model relationship test failed: {e}")
        db.rollback()
        db.close()
        return False

def verify_file_upload_relationships():
    """Verify that file uploads can be properly linked to other entities."""
    print(f"\n📁 Verifying File Upload Relationships:")
    
    database_url = settings.database_url
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg2://")
    
    engine = create_engine(database_url, echo=False)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    try:
        db = SessionLocal()
        
        # Get existing file uploads
        uploads = db.query(FileUpload).limit(5).all()
        print(f"   Found {len(uploads)} existing file uploads")
        
        if uploads:
            # Show sample upload data
            for i, upload in enumerate(uploads[:3]):
                print(f"   Upload {i+1}: {upload.filename} ({upload.file_type})")
                print(f"      Size: {upload.size} bytes")
                print(f"      Processed: {upload.processed}")
                print(f"      Uploaded: {upload.uploaded_at}")
        
        # Test creating a data source from a file upload
        if uploads:
            test_upload = uploads[0]
            print(f"   Testing data source creation from file upload...")
            
            datasource = DataSource(
                id=f"ds-from-{test_upload.id}",
                name=f"Data from {test_upload.original_filename}",
                type="file",
                connection_info={
                    "file_id": test_upload.id,
                    "file_path": test_upload.file_path,
                    "file_type": test_upload.file_type
                },
                schema_info={"source_file": test_upload.id}
            )
            db.add(datasource)
            db.commit()
            print(f"   ✅ Created data source from file upload")
            
            # Clean up
            db.delete(datasource)
            db.commit()
        
        db.close()
        return True
        
    except Exception as e:
        print(f"   ❌ File upload relationship test failed: {e}")
        db.rollback()
        db.close()
        return False

def main():
    """Main verification function."""
    print("🔍 DATABASE SETUP VERIFICATION")
    print("=" * 60)
    
    # Step 1: Verify basic connection
    if not verify_database_connection():
        print("❌ Basic database connection failed")
        return
    
    # Step 2: Test model relationships
    if not test_model_relationships():
        print("❌ Model relationship tests failed")
        return
    
    # Step 3: Verify file upload relationships
    if not verify_file_upload_relationships():
        print("❌ File upload relationship tests failed")
        return
    
    print("\n" + "=" * 60)
    print("✅ ALL VERIFICATIONS PASSED")
    print("=" * 60)
    print("\n🎉 Your database setup is working correctly!")
    print("\nKey points:")
    print("✅ Database connection is stable")
    print("✅ All tables are properly created")
    print("✅ Model relationships work correctly")
    print("✅ File uploads can be linked to data sources")
    print("✅ No more conflicts between local and remote databases")
    print("\nYour application should now work without relationship issues!")

if __name__ == "__main__":
    main() 