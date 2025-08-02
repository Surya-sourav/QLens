#!/usr/bin/env python3

import asyncio
import json
import logging
from app.models.database import get_db, FileUpload
from app.routers.chat import _prepare_data_context
from app.services.code_executor import code_executor
from app.models.schemas import CodeExecutionRequest

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def debug_chart_capture():
    """
    Debug script to test chart capture logic
    """
    print("=== DEBUGGING CHART CAPTURE ===")
    
    # Get a CSV file from database
    db = next(get_db())
    try:
        files = db.query(FileUpload).all()
        if not files:
            print("❌ No files found in database!")
            return
        
        csv_file = None
        for file in files:
            if file.original_filename.endswith('.csv') and file.data_preview:
                csv_file = file
                break
        
        if not csv_file:
            print("❌ No CSV file with data preview found!")
            return
        
        print(f"📁 Using CSV file: {csv_file.original_filename}")
        
        # Prepare data context
        data_context = await _prepare_data_context([csv_file.id], db)
        if not data_context:
            print("❌ Failed to prepare data context")
            return
        
        print(f"✅ Data context prepared")
        
        # Test different chart generation codes
        test_codes = [
            # Test 1: Simple matplotlib with plt.gcf()
            """
import matplotlib.pyplot as plt
plt.figure(figsize=(10,6))
plt.scatter(df['Transaction Amount'], df['Account Balance After Transaction'], alpha=0.5)
plt.xlabel('Transaction Amount')
plt.ylabel('Account Balance After Transaction')
plt.title('Transaction Amount vs Account Balance After Transaction')
plt.grid(True)
fig = plt.gcf()
""",
            # Test 2: Direct matplotlib without fig assignment
            """
import matplotlib.pyplot as plt
plt.figure(figsize=(10,6))
plt.scatter(df['Transaction Amount'], df['Account Balance After Transaction'], alpha=0.5)
plt.xlabel('Transaction Amount')
plt.ylabel('Account Balance After Transaction')
plt.title('Transaction Amount vs Account Balance After Transaction')
plt.grid(True)
""",
            # Test 3: Using subplots
            """
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(10,6))
ax.scatter(df['Transaction Amount'], df['Account Balance After Transaction'], alpha=0.5)
ax.set_xlabel('Transaction Amount')
ax.set_ylabel('Account Balance After Transaction')
ax.set_title('Transaction Amount vs Account Balance After Transaction')
ax.grid(True)
""",
        ]
        
        for i, test_code in enumerate(test_codes, 1):
            print(f"\n🧪 Test {i}: Chart generation")
            print(f"Code: {test_code.strip()}")
            
            # Create execution request
            request = CodeExecutionRequest(
                code=test_code,
                data_context=data_context
            )
            
            # Execute code
            try:
                result = await code_executor.execute_code(request)
                print(f"✅ Code execution successful: {result.success}")
                print(f"📊 Chart data exists: {result.chart_data is not None}")
                
                if result.chart_data:
                    print(f"📈 Chart type: {result.chart_data.get('type')}")
                    print(f"🖼️ Image data exists: {result.chart_data.get('data') is not None}")
                    if result.chart_data.get('data'):
                        print(f"📏 Image data length: {len(result.chart_data['data'])}")
                        print("🎉 SUCCESS: Chart image captured!")
                        return  # Found working solution
                else:
                    print("❌ No chart data captured")
                    if result.output:
                        print(f"📄 Output: {result.output[:200]}...")
                    
            except Exception as e:
                print(f"❌ Error during execution: {e}")
                import traceback
                traceback.print_exc()
        
        print("\n❌ All tests failed - chart capture is not working")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(debug_chart_capture()) 