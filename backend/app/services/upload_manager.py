import os
import uuid
import aiofiles
from typing import Dict, Any, Optional
from datetime import datetime
import pandas as pd
from fastapi import UploadFile, HTTPException
from app.config import settings
from app.models.schemas import UploadResponse, FileUploadCreate
from app.models.database import FileUpload as FileUploadModel
import numpy as np
import logging


class UploadManager:
    def __init__(self):
        self.upload_dir = settings.upload_dir
        os.makedirs(self.upload_dir, exist_ok=True)
    
    async def save_file(self, file: UploadFile) -> FileUploadCreate:
        """Save uploaded file and return file info"""
        # Read file content first
        content = await file.read()
        file_size = len(content)
        if file_size > settings.max_file_size:
            raise HTTPException(status_code=413, detail="File too large")
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1] if file.filename else ""
        filename = f"{file_id}{file_extension}"
        file_path = os.path.join(self.upload_dir, filename)
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Create file upload record
        file_upload = FileUploadCreate(
            filename=filename,
            file_type=file.content_type or "application/octet-stream",
            size=file_size,
            uploaded_at=datetime.now()
        )
        
        return file_upload
    
    def _make_json_serializable(self, obj):
        import pandas as pd
        if isinstance(obj, dict):
            return {k: self._make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(v) for v in obj]
        elif isinstance(obj, (np.integer, np.floating)):
            return obj.item()
        elif isinstance(obj, (np.dtype,)):
            return str(obj)
        elif hasattr(obj, 'item'):
            try:
                return obj.item()
            except Exception:
                return str(obj)
        elif hasattr(pd, 'api') and isinstance(obj, pd.api.extensions.ExtensionDtype):
            return str(obj)
        elif hasattr(obj, '__module__') and 'pandas' in obj.__module__:
            return str(obj)
        elif obj is pd.NA:
            return None
        elif hasattr(obj, '__class__') and 'DType' in obj.__class__.__name__:
            return str(obj)
        elif pd.isna(obj):  # Handle NaN values
            return None
        else:
            try:
                import json
                json.dumps(obj)
                return obj
            except Exception:
                return str(obj)
    
    async def process_file(self, file_path: str, file_type: str) -> str:
        """Process uploaded file and extract data preview"""
        try:
            # Determine file type based on extension if content type is not reliable
            file_extension = os.path.splitext(file_path)[1].lower()
            
            # Use file extension to determine how to read the file
            if file_extension == '.csv' or file_type in ["text/csv", "application/csv"]:
                df = pd.read_csv(file_path)
            elif file_extension in ['.xlsx', '.xls'] or file_type in ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                             "application/vnd.ms-excel"]:
                df = pd.read_excel(file_path)
            else:
                # Try to determine file type from content
                if file_type == "application/octet-stream":
                    # For octet-stream, try to determine from file extension
                    if file_extension == '.csv':
                        df = pd.read_csv(file_path)
                    elif file_extension in ['.xlsx', '.xls']:
                        df = pd.read_excel(file_path)
                    else:
                        raise ValueError(f"Unsupported file type: {file_type} with extension {file_extension}")
                else:
                    raise ValueError(f"Unsupported file type: {file_type}")
            
            # Create data preview
            dtypes_dict = {}
            for col, dtype in df.dtypes.items():
                dtype_str = getattr(dtype, 'name', str(dtype))
                dtypes_dict[str(col)] = dtype_str
                logging.debug(f"[DEBUG] dtype for column {col}: {dtype} (type: {type(dtype)}), name: {dtype_str}")
            # Convert all columns to native Python types for preview
            df_native = df.convert_dtypes().astype(object)
            preview = {
                "shape": list(df.shape),
                "columns": [str(col) for col in df.columns.tolist()],
                "dtypes": dtypes_dict,
                "head": self._make_json_serializable(df_native.head(5).to_dict(orient='records')),
                "null_counts": self._make_json_serializable(df_native.isnull().sum().to_dict()),
                "numeric_columns": [str(col) for col in df_native.select_dtypes(include=['number']).columns.tolist()],
                "categorical_columns": [str(col) for col in df_native.select_dtypes(include=['object']).columns.tolist()]
            }
            # Clean preview for numeric columns (e.g., strip $ and convert to float for Debit/Credit)
            import re
            preview_head = df_native.head(5).to_dict(orient='records')
            for row in preview_head:
                for col in preview['numeric_columns']:
                    val = row.get(col)
                    if isinstance(val, str):
                        # Remove $ and commas, convert to float if possible
                        cleaned = re.sub(r'[^0-9.\-]', '', val)
                        try:
                            row[col] = float(cleaned)
                        except Exception:
                            pass
            preview["head"] = self._make_json_serializable(preview_head)
            import json
            preview_str = json.dumps(preview, default=str)
            logging.info(f"[DEBUG] Preview string before DB save: {preview_str}")
            return preview_str
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")
    
    async def get_file_data(self, file_path: str, file_type: str) -> pd.DataFrame:
        """Get pandas DataFrame from uploaded file"""
        try:
            if file_type in ["text/csv", "application/csv"]:
                return pd.read_csv(file_path)
            elif file_type in ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                             "application/vnd.ms-excel"]:
                return pd.read_excel(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")


upload_manager = UploadManager()
