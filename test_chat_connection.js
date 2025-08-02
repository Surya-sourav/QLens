// Test script to verify chat connection with file data
const testChatConnection = async () => {
  console.log('🧪 Testing Chat Connection with File Data');
  console.log('=' * 50);
  
  try {
    // Step 1: Get files from API
    console.log('1. Getting files from API...');
    const filesResponse = await fetch('http://localhost:8000/api/v1/upload/files');
    const files = await filesResponse.json();
    console.log(`   Found ${files.length} files`);
    
    if (files.length === 0) {
      console.log('   ❌ No files found');
      return;
    }
    
    const latestFile = files[0];
    console.log(`   Latest file: ${latestFile.id} (${latestFile.original_filename})`);
    
    // Step 2: Test chat message with file data
    console.log('\n2. Testing chat message with file data...');
    const chatResponse = await fetch('http://localhost:8000/api/v1/chat/message', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: 'Generate me a bar chart',
        dataSources: [latestFile.id]
      })
    });
    
    const chatResult = await chatResponse.json();
    console.log('   Chat response:', chatResult);
    
    // Step 3: Check if data context was properly passed
    console.log('\n3. Checking data context...');
    if (chatResult.content && chatResult.content.includes('I don\'t see any data file')) {
      console.log('   ❌ LLM still says no data file found');
    } else {
      console.log('   ✅ LLM received data context properly');
    }
    
  } catch (error) {
    console.error('❌ Error during test:', error);
  }
};

// Run the test
testChatConnection(); 