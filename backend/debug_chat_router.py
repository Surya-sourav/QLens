#!/usr/bin/env python3
"""
Debug script to test the chat router's data context logic
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.database import get_db, FileUpload
import json

async def _prepare_data_context(data_sources: list, db) -> dict:
    """Copy of the exact function from chat router"""
    context = {}
    
    if not db:
        return context

    found_file = False
    # Add file data sources
    for source_id in data_sources:
        file_record = db.query(FileUpload).filter(FileUpload.id == source_id).first()
        if file_record and file_record.data_preview:
            found_file = True
            try:
                # Parse the data preview if it's a JSON string
                if isinstance(file_record.data_preview, str):
                    file_data = json.loads(file_record.data_preview)
                else:
                    file_data = file_record.data_preview
                # Add file path and type for full file loading
                file_data["file_path"] = file_record.file_path
                file_data["file_type"] = file_record.file_type
                # DEBUG LOGGING: Print columns for diagnosis
                print(f"[DEBUG] Loaded file_data for source {source_id}: columns={file_data.get('columns')}, preview={file_data}")
                context["file_data"] = file_data
                print(f"Added file data context for source: {source_id}")
            except json.JSONDecodeError as e:
                print(f"Failed to parse data preview for source {source_id}: {e}")
                context["file_data"] = file_record.data_preview
            
            # Add file analysis if available
            if file_record and hasattr(file_record, 'data_analysis') and file_record.data_analysis:
                context["file_analysis"] = file_record.data_analysis
                print(f"[DEBUG] Loaded file_analysis for source {source_id}: {file_record.data_analysis[:200]}")
        else:
            print(f"No file found for source_id: {source_id}")
    if not found_file:
        print(f"No valid file data found for data_sources: {data_sources}")
    # Log the final context sent to LLM
    print(f"[DEBUG] Final data context sent to LLM: {context}")
    return context

async def debug_chat_router_logic():
    """Debug the exact logic used in the chat router"""
    
    # Get database session
    db = next(get_db())
    
    try:
        # The file ID that actually exists in the database
        file_id = "d1a141ab-b5ef-4e30-8e93-ef975260211e"
        
        print(f"🔍 Testing _prepare_data_context with file ID: {file_id}")
        
        # Test the exact function from chat router
        data_sources = [file_id]
        data_context = await _prepare_data_context(data_sources, db)
        
        print(f"\n📊 Data context result:")
        print(f"   - Context exists: {bool(data_context)}")
        print(f"   - File data exists: {bool(data_context.get('file_data'))}")
        print(f"   - Context keys: {list(data_context.keys())}")
        
        if data_context.get('file_data'):
            file_data = data_context['file_data']
            print(f"   - File data keys: {list(file_data.keys())}")
            print(f"   - Columns: {file_data.get('columns', [])[:5]}...")
            print(f"   - Shape: {file_data.get('shape', 'Unknown')}")
            
        # Test the LLM service check
        print(f"\n🧪 Testing LLM service data context check...")
        print(f"   - data_context exists: {bool(data_context)}")
        print(f"   - file_data exists: {bool(data_context.get('file_data'))}")
        
        if not data_context or not data_context.get("file_data"):
            print(f"❌ LLM service will return 'no data' message")
        else:
            print(f"✅ LLM service should process the data")
            
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(debug_chat_router_logic()) 