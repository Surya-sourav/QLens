from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from app.models.schemas import DatabaseConnection, DatabaseConnectionResponse
from app.services.db_connector import db_connector
from app.models.database import get_db, DataSource
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

router = APIRouter(prefix="/database", tags=["database"])


@router.post("/connect", response_model=DatabaseConnectionResponse)
async def connect_database(
    connection: DatabaseConnection,
    db: Session = Depends(get_db)
):
    """Connect to a PostgreSQL database"""
    
    try:
        # Test connection
        await db_connector.test_connection(connection)
        
        # Get tables
        tables = await db_connector.get_tables(connection)
        
        # Create connection record
        connection_id = str(uuid.uuid4())
        db_connection = DataSource(
            id=connection_id,
            name=f"PostgreSQL - {connection.host}:{connection.port}/{connection.database}",
            type="database",
            connection_info={
                "host": connection.host,
                "port": connection.port,
                "database": connection.database,
                "username": connection.username,
                "schema": connection.schema
            },
            schema_info={"tables": tables},
            created_at=datetime.now()
        )
        
        db.add(db_connection)
        db.commit()
        db.refresh(db_connection)
        
        return DatabaseConnectionResponse(
            success=True,
            connection_id=connection_id,
            message="Database connected successfully",
            tables=tables,
            schema_info={"tables": tables}
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Connection failed: {str(e)}")


@router.get("/connections", response_model=List[Dict[str, Any]])
async def list_connections(db: Session = Depends(get_db)):
    """List all database connections"""
    connections = db.query(DataSource).filter(DataSource.type == "database").all()
    
    return [
        {
            "id": conn.id,
            "name": conn.name,
            "connection_info": conn.connection_info,
            "schema_info": conn.schema_info,
            "created_at": conn.created_at
        }
        for conn in connections
    ]


@router.get("/connection/{connection_id}/tables", response_model=List[str])
async def get_tables(connection_id: str, db: Session = Depends(get_db)):
    """Get tables for a specific database connection"""
    connection_record = db.query(DataSource).filter(DataSource.id == connection_id).first()
    
    if not connection_record:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    return connection_record.schema_info.get("tables", [])


@router.get("/connection/{connection_id}/table/{table_name}/preview")
async def get_table_preview(
    connection_id: str,
    table_name: str,
    db: Session = Depends(get_db)
):
    """Get preview of table data"""
    connection_record = db.query(DataSource).filter(DataSource.id == connection_id).first()
    
    if not connection_record:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    try:
        # Recreate connection object
        conn_info = connection_record.connection_info
        connection = DatabaseConnection(
            host=conn_info["host"],
            port=conn_info["port"],
            database=conn_info["database"],
            username=conn_info["username"],
            schema=conn_info.get("schema")
        )
        
        # Get table preview
        preview = await db_connector.get_table_preview(connection, table_name)
        
        return {
            "success": True,
            "table_name": table_name,
            "preview": preview
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting table preview: {str(e)}")


@router.post("/connection/{connection_id}/query")
async def execute_query(
    connection_id: str,
    query: str,
    db: Session = Depends(get_db)
):
    """Execute a SQL query on the connected database"""
    connection_record = db.query(DataSource).filter(DataSource.id == connection_id).first()
    
    if not connection_record:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    try:
        # Recreate connection object
        conn_info = connection_record.connection_info
        connection = DatabaseConnection(
            host=conn_info["host"],
            port=conn_info["port"],
            database=conn_info["database"],
            username=conn_info["username"],
            schema=conn_info.get("schema")
        )
        
        # Execute query
        df = await db_connector.query_data(connection, query)
        
        return {
            "success": True,
            "data": df.to_dict(orient='records'),
            "shape": df.shape,
            "columns": df.columns.tolist()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query execution failed: {str(e)}")


@router.delete("/connection/{connection_id}")
async def delete_connection(connection_id: str, db: Session = Depends(get_db)):
    """Delete a database connection"""
    connection_record = db.query(DataSource).filter(DataSource.id == connection_id).first()
    
    if not connection_record:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    db.delete(connection_record)
    db.commit()
    
    return {"success": True, "message": "Connection deleted successfully"}
