from sqlalchemy import Column, String, DateTime, Text, JSON, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func, text
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Database connection - handle both PostgreSQL and SQLite
database_url = settings.database_url
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg2://")
elif database_url.startswith("sqlite://"):
    # SQLite doesn't need additional configuration
    pass

# Create engine with proper configuration for Neon PostgreSQL
engine = create_engine(
    database_url, 
    echo=False,  # Set to True for debugging
    future=True,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=300,    # Recycle connections every 5 minutes
    isolation_level="READ_COMMITTED"  # Use READ_COMMITTED isolation level
)

SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine,
    expire_on_commit=False  # Prevent objects from expiring after commit
)

Base = declarative_base()


class DataSource(Base):
    __tablename__ = "data_sources"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # "file" or "database"
    connection_info = Column(JSON)
    schema_info = Column(JSON)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(String, primary_key=True)
    session_id = Column(String, unique=True, nullable=False)
    data_sources = Column(JSON, default=list)
    created_at = Column(DateTime, default=func.now())
    last_activity = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(String, primary_key=True)
    session_id = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    message_type = Column(String, nullable=False)  # "user", "assistant", "system"
    timestamp = Column(DateTime, default=func.now())
    message_metadata = Column(JSON)  # Changed from metadata to message_metadata
    chart_data = Column(JSON)
    chart_type = Column(String)
    chart_code = Column(Text)


class FileUpload(Base):
    __tablename__ = "file_uploads"
    
    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    size = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime, default=func.now())
    processed = Column(Boolean, default=False)
    data_preview = Column(Text)  # Changed from JSON to Text
    data_analysis = Column(Text)  # Stores LLM-driven data analysis output (text or JSON)


def get_db():
    """Get database session with proper error handling"""
    db = SessionLocal()
    try:
        # Test the connection
        db.execute(text("SELECT 1"))
        yield db
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
