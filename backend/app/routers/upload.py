import os
import uuid
import json
import logging
from typing import List
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.database import get_db, FileUpload as FileUploadORM
from app.models.schemas import UploadResponse
from app.services.upload_manager import UploadManager
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/upload", tags=["upload"])
upload_manager = UploadManager()

@router.get("/debug/files")
async def debug_list_files(db: Session = Depends(get_db)):
    """Debug endpoint to test database connection"""
    try:
        logger.info("Debug: Testing database connection...")
        
        # Test 1: Direct SQL query
        with db.bind.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM file_uploads"))
            count = result.scalar()
            logger.info(f"Debug: Direct SQL count: {count}")
            
            if count > 0:
                result = conn.execute(text("SELECT id, filename FROM file_uploads ORDER BY uploaded_at DESC LIMIT 5"))
                files = result.fetchall()
                logger.info(f"Debug: Direct SQL files: {files}")
        
        # Test 2: SQLAlchemy ORM query
        orm_count = db.query(FileUploadORM).count()
        logger.info(f"Debug: ORM count: {orm_count}")
        
        orm_files = db.query(FileUploadORM).order_by(FileUploadORM.uploaded_at.desc()).limit(5).all()
        logger.info(f"Debug: ORM files: {[(f.id, f.filename) for f in orm_files]}")
        
        return {
            "direct_sql_count": count,
            "orm_count": orm_count,
            "direct_sql_files": files if count > 0 else [],
            "orm_files": [(f.id, f.filename) for f in orm_files]
        }
        
    except Exception as e:
        logger.error(f"Debug error: {e}")
        import traceback
        logger.error(f"Debug traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Debug error: {str(e)}")

@router.post("/file", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a file and process it"""
    
    logger.info(f"File upload request: {file.filename} ({file.content_type})")
    
    try:
        # Validate file type
        allowed_types = [
            "text/csv",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ]
        
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file.content_type} not supported. Supported types: {allowed_types}"
            )
        
        # Validate file size
        if file.size > settings.max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"File size {file.size} exceeds maximum allowed size {settings.max_file_size}"
            )
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        filename = f"{file_id}{file.filename}"
        file_path = os.path.join(settings.upload_dir, filename)
        
        logger.info(f"Generated file path: {file_path}")
        
        # Save file to disk
        try:
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            logger.info(f"File saved to disk: {file_path}")
        except Exception as save_error:
            logger.error(f"Error saving file to disk: {save_error}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save file: {str(save_error)}"
            )
        
        # Process file and generate data preview
        try:
            logger.info("Processing file for data preview...")
            data_preview = await upload_manager.process_file(file_path, file.content_type)
            data_preview_dict = json.loads(data_preview) if isinstance(data_preview, str) else data_preview
            logger.info("LLM analysis completed successfully")
        except Exception as process_error:
            logger.error(f"Error processing file: {process_error}")
            # Clean up file if processing failed
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except:
                pass
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process file: {str(process_error)}"
            )
        
        # Save to database
        try:
            logger.info("Creating database record...")
            db_file = FileUploadORM(
                id=file_id,
                filename=filename,
                original_filename=file.filename,
                file_type=file.content_type,
                file_path=file_path,
                size=file.size,
                processed=True,
                data_preview=data_preview,
                data_analysis=None  # Will be populated later if needed
            )
            
            # Add to database
            db.add(db_file)
            db.commit()
            db.refresh(db_file)
            
            logger.info(f"File uploaded successfully: {db_file.id}")
            
            # Verify the file was actually saved to database
            saved_file = db.query(FileUploadORM).filter(FileUploadORM.id == file_id).first()
            if not saved_file:
                logger.error(f"File was not found in database after commit: {file_id}")
                raise HTTPException(
                    status_code=500,
                    detail="File was uploaded but not properly saved to database"
                )
            
            logger.info(f"File verified in database: {saved_file.id}")
            
            # Return success response
            return UploadResponse(
                success=True,
                fileId=db_file.id,
                message="File uploaded and processed successfully",
                data_preview=data_preview_dict
            )
            
        except Exception as db_error:
            logger.error(f"Database error during file upload: {db_error}")
            db.rollback()
            
            # Clean up file if database save failed
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Cleaned up file: {file_path}")
            except Exception as cleanup_error:
                logger.error(f"Error cleaning up file: {cleanup_error}")
            
            raise HTTPException(
                status_code=500,
                detail=f"Database error during file upload: {str(db_error)}"
            )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"Upload failed: {str(e)}")
        logger.error(f"Traceback: {error_traceback}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/files", response_model=List[dict])
async def list_uploaded_files(db: Session = Depends(get_db)):
    """List all uploaded files"""
    try:
        # Use a fresh database session to ensure we get all files
        logger.info("Listing uploaded files...")
        
        # First, let's check how many files we have
        total_count = db.query(FileUploadORM).count()
        logger.info(f"Total files in database: {total_count}")
        
        # Get all files ordered by upload date
        files = db.query(FileUploadORM).order_by(FileUploadORM.uploaded_at.desc()).all()
        logger.info(f"Files retrieved from database: {len(files)}")
        
        # Convert to response format
        result = []
        for f in files:
            try:
                data_preview = json.loads(f.data_preview) if f.data_preview else None
            except json.JSONDecodeError:
                data_preview = f.data_preview
            
            result.append({
                "id": f.id,
                "filename": f.filename,
                "original_filename": f.original_filename,
                "file_type": f.file_type,
                "file_path": f.file_path,
                "size": f.size,
                "uploaded_at": f.uploaded_at.isoformat() if f.uploaded_at else None,
                "processed": f.processed,
                "data_preview": data_preview
            })
        
        logger.info(f"Returning {len(result)} files")
        return result
        
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")


@router.delete("/file/{file_id}")
async def delete_file(file_id: str, db: Session = Depends(get_db)):
    """Delete an uploaded file"""
    try:
        file_record = db.query(FileUploadORM).filter(FileUploadORM.id == file_id).first()
        
        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Delete physical file
        if os.path.exists(file_record.file_path):
            os.remove(file_record.file_path)
        
        # Delete database record
        db.delete(file_record)
        db.commit()
        
        return {"success": True, "message": "File deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")