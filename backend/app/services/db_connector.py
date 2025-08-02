import psycopg2
import pandas as pd
from typing import Dict, Any, List, Optional
from sqlalchemy import create_engine, text
from fastapi import HTTPException
from app.models.schemas import DatabaseConnection, DatabaseConnectionResponse


class DatabaseConnector:
    def __init__(self):
        self.connections = {}
    
    async def test_connection(self, connection: DatabaseConnection) -> bool:
        """Test database connection"""
        try:
            conn_string = f"postgresql://{connection.username}:{connection.password}@{connection.host}:{connection.port}/{connection.database}"
            engine = create_engine(conn_string)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Database connection failed: {str(e)}")
    
    async def get_tables(self, connection: DatabaseConnection) -> List[str]:
        """Get list of tables in the database"""
        try:
            conn_string = f"postgresql://{connection.username}:{connection.password}@{connection.host}:{connection.port}/{connection.database}"
            engine = create_engine(conn_string)
            
            with engine.connect() as conn:
                # Get tables from the specified schema or public schema
                schema = connection.schema or "public"
                query = text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = :schema 
                    AND table_type = 'BASE TABLE'
                """)
                result = conn.execute(query, {"schema": schema})
                tables = [row[0] for row in result.fetchall()]
            
            return tables
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error getting tables: {str(e)}")
    
    async def get_table_schema(self, connection: DatabaseConnection, table_name: str) -> Dict[str, Any]:
        """Get schema information for a specific table"""
        try:
            conn_string = f"postgresql://{connection.username}:{connection.password}@{connection.host}:{connection.port}/{connection.database}"
            engine = create_engine(conn_string)
            
            with engine.connect() as conn:
                schema = connection.schema or "public"
                query = text("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_schema = :schema 
                    AND table_name = :table_name
                    ORDER BY ordinal_position
                """)
                result = conn.execute(query, {"schema": schema, "table_name": table_name})
                columns = [{"name": row[0], "type": row[1], "nullable": row[2], "default": row[3]} 
                          for row in result.fetchall()]
            
            return {
                "table_name": table_name,
                "schema": schema,
                "columns": columns
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error getting table schema: {str(e)}")
    
    async def query_data(self, connection: DatabaseConnection, query: str) -> pd.DataFrame:
        """Execute SQL query and return results as DataFrame"""
        try:
            conn_string = f"postgresql://{connection.username}:{connection.password}@{connection.host}:{connection.port}/{connection.database}"
            engine = create_engine(conn_string)
            
            df = pd.read_sql(query, engine)
            return df
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error executing query: {str(e)}")
    
    async def get_table_preview(self, connection: DatabaseConnection, table_name: str, limit: int = 100) -> Dict[str, Any]:
        """Get preview of table data"""
        try:
            schema = connection.schema or "public"
            query = f"SELECT * FROM {schema}.{table_name} LIMIT {limit}"
            df = await self.query_data(connection, query)
            
            preview = {
                "shape": df.shape,
                "columns": df.columns.tolist(),
                "dtypes": df.dtypes.to_dict(),
                "head": df.head(5).to_dict(orient='records'),
                "null_counts": df.isnull().sum().to_dict(),
                "numeric_columns": df.select_dtypes(include=['number']).columns.tolist(),
                "categorical_columns": df.select_dtypes(include=['object']).columns.tolist()
            }
            
            return preview
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error getting table preview: {str(e)}")
    
    def create_connection_string(self, connection: DatabaseConnection) -> str:
        """Create connection string for database"""
        return f"postgresql://{connection.username}:{connection.password}@{connection.host}:{connection.port}/{connection.database}"


db_connector = DatabaseConnector()
