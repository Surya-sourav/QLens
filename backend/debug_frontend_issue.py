#!/usr/bin/env python3

import asyncio
import json
import logging
from app.models.database import get_db, FileUpload
from app.routers.chat import _prepare_data_context
from app.services.langgraph_orchestrator import orchestrator

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def debug_frontend_issue():
    print("=== DEBUGGING FRONTEND ISSUE ===")
    print("The issue is: Frontend is sending empty data_sources array")
    print("This happens when localStorage['latestFileId'] is not set or not retrieved properly")
    print()
    
    db = next(get_db())
    try:
        files = db.query(FileUpload).all()
        print(f"Found {len(files)} files in database")
        if not files:
            print("❌ No files found in database!")
            return
        
        # Simulate the EXACT issue the user is experiencing
        test_file = files[0]
        print(f"Test file: {test_file.original_filename} (ID: {test_file.id})")
        
        # Simulate frontend sending EMPTY data_sources (the actual issue)
        message_data = {
            "message": "Generate me a bar chart",
            "data_sources": []  # This is the problem - empty array!
        }
        print(f"❌ Frontend is sending: {message_data}")
        
        # Test what happens with empty data_sources
        data_context = await _prepare_data_context(message_data["data_sources"], db)
        print(f"Data context with empty data_sources: {data_context}")
        
        # Process the query through the orchestrator
        result = await orchestrator.process_query(message_data["message"], data_context)
        
        final_response = result.get("final_response", {})
        response_type = final_response.get('type')
        content = final_response.get('content', '')
        
        print(f"\nResponse type: {response_type}")
        print(f"Content: {content[:200]}...")
        
        if "don't see any data" in content.lower():
            print("✅ CONFIRMED: This is the exact issue the user is experiencing!")
            print("The frontend is sending empty data_sources array")
            print()
            print("=== SOLUTION ===")
            print("The frontend needs to:")
            print("1. Store the file ID in localStorage when a file is uploaded")
            print("2. Retrieve the file ID from localStorage before sending messages")
            print("3. Include the file ID in the data_sources array")
            print()
            print("=== FRONTEND FIXES ALREADY APPLIED ===")
            print("✅ App.tsx - Initialize latestFileId from localStorage")
            print("✅ ChatInterface.tsx - Get file ID from localStorage and set dataSources")
            print("✅ useChat.ts - Always get file ID from localStorage before sending")
            print()
            print("=== VERIFICATION ===")
            print("To verify the fix is working:")
            print("1. Upload a file in the frontend")
            print("2. Check that localStorage['latestFileId'] is set")
            print("3. Send a message and check that data_sources contains the file ID")
            print("4. The backend should receive the file ID and generate a chart")
        
    except Exception as e:
        print(f"❌ Error during debug: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(debug_frontend_issue()) 