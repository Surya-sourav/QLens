from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
import pandas as pd
import json
import logging
from app.models.schemas import CSVPreviewRequest, CSVPreviewResponse
from app.models.database import get_db, FileUpload as FileUploadORM
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/csv-preview", tags=["csv-preview"])


@router.post("/preview", response_model=CSVPreviewResponse)
async def get_csv_preview(request: CSVPreviewRequest, db: Session = Depends(get_db)):
    """Get paginated preview of CSV/Excel file data"""
    try:
        # Get file record
        file_record = db.query(FileUploadORM).filter(FileUploadORM.id == request.file_id).first()
        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Read from actual file instead of cached data_preview
        import pandas as pd
        import os
        
        file_path = file_record.file_path
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found on disk")
        
        # Read the actual file
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                raise HTTPException(status_code=400, detail="Unsupported file format")
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")
        
        # Get columns and data
        columns = df.columns.tolist()
        total_rows = len(df)
        
        # Calculate pagination
        total_pages = (total_rows + request.page_size - 1) // request.page_size
        start_idx = (request.page - 1) * request.page_size
        end_idx = start_idx + request.page_size
        
        # Get page data
        page_df = df.iloc[start_idx:end_idx]
        
        # Convert to list of dictionaries
        result_data = page_df.to_dict('records')
        
        return CSVPreviewResponse(
            success=True,
            data=result_data,
            columns=columns,
            total_rows=total_rows,
            current_page=request.page,
            total_pages=total_pages,
            page_size=request.page_size
        )
        
    except Exception as e:
        logger.error(f"Error getting CSV preview: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get CSV preview: {str(e)}")


@router.get("/file/{file_id}/info")
async def get_file_info(file_id: str, db: Session = Depends(get_db)):
    """Get file information and basic statistics"""
    try:
        # Get file record
        file_record = db.query(FileUploadORM).filter(FileUploadORM.id == file_id).first()
        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Read from actual file instead of cached data_preview
        import pandas as pd
        import os
        
        file_path = file_record.file_path
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found on disk")
        
        # Read the actual file
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                raise HTTPException(status_code=400, detail="Unsupported file format")
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")
        
        # Get basic info from actual file
        total_rows, total_columns = df.shape
        columns = df.columns.tolist()
        
        # Determine numeric and categorical columns
        numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
        categorical_columns = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Get file stats
        file_stats = os.stat(file_path)
        
        return {
            "file_info": {
                "filename": file_record.original_filename,
                "fileType": file_record.file_type,
                "size": file_stats.st_size,
                "uploadedAt": file_record.uploaded_at.isoformat(),
                "processed": file_record.processed
            },
            "data_info": {
                "totalRows": total_rows,
                "totalColumns": total_columns,
                "hasHeaders": True,  # Assuming CSV files have headers
                "numericColumns": numeric_columns,
                "categoricalColumns": categorical_columns
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting file info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get file info: {str(e)}")


@router.get("/file/{file_id}/columns")
async def get_file_columns(file_id: str, db: Session = Depends(get_db)):
    """Get detailed column information"""
    try:
        # Get file record
        file_record = db.query(FileUploadORM).filter(FileUploadORM.id == file_id).first()
        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Read from actual file instead of cached data_preview
        import pandas as pd
        import os
        
        file_path = file_record.file_path
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found on disk")
        
        # Read the actual file
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                raise HTTPException(status_code=400, detail="Unsupported file format")
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")
        
        # Get column information
        columns = df.columns.tolist()
        data_types = df.dtypes.to_dict()
        numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
        categorical_columns = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Convert data types to strings
        data_types_str = {col: str(dtype) for col, dtype in data_types.items()}
        
        return {
            "columns": {
                "actualColumns": columns,
                "dataTypes": data_types_str,
                "numericColumns": numeric_columns,
                "categoricalColumns": categorical_columns
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting file columns: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get file columns: {str(e)}")


def _convert_nulls_to_none(obj):
    """Recursively convert null values to None for Python compatibility"""
    if obj is None:
        return None
    elif isinstance(obj, dict):
        converted = {}
        for k, v in obj.items():
            converted[k] = _convert_nulls_to_none(v)
        return converted
    elif isinstance(obj, list):
        converted = []
        for item in obj:
            converted.append(_convert_nulls_to_none(item))
        return converted
    else:
        return obj 