#!/usr/bin/env python3
"""
Script to reprocess existing files with enhanced numeric column detection
"""
import os
import sys
import json
import logging
from sqlalchemy.orm import Session
from app.models.database import get_db, FileUpload as FileUploadORM
from app.services.upload_manager import UploadManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reprocess_files():
    """Reprocess all existing files with enhanced numeric column detection"""
    try:
        # Get database session
        db = next(get_db())
        
        # Get all files
        files = db.query(FileUploadORM).all()
        logger.info(f"Found {len(files)} files to reprocess")
        
        upload_manager = UploadManager()
        
        for file_record in files:
            try:
                logger.info(f"Reprocessing file: {file_record.original_filename}")
                
                # Check if file exists on disk
                if not os.path.exists(file_record.file_path):
                    logger.warning(f"File not found on disk: {file_record.file_path}")
                    continue
                
                # Reprocess the file
                new_preview = upload_manager.process_file(file_record.file_path, file_record.file_type)
                
                # Update the database record
                file_record.data_preview = new_preview
                db.commit()
                
                logger.info(f"Successfully reprocessed: {file_record.original_filename}")
                
            except Exception as e:
                logger.error(f"Error reprocessing {file_record.original_filename}: {e}")
                db.rollback()
                continue
        
        logger.info("File reprocessing completed!")
        
    except Exception as e:
        logger.error(f"Error in reprocess_files: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    reprocess_files() 