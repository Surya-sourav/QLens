// Test script to verify the complete frontend data flow
const testFrontendDataFlow = async () => {
  console.log('🧪 Testing Frontend Data Flow');
  console.log('=' * 50);
  
  try {
    // Step 1: Get files from API (like frontend does)
    console.log('1. Getting files from API (frontend simulation)...');
    const filesResponse = await fetch('http://localhost:8000/api/v1/upload/files');
    const files = await filesResponse.json();
    console.log(`   Found ${files.length} files`);
    
    if (files.length === 0) {
      console.log('   ❌ No files found');
      return;
    }
    
    const latestFile = files[0];
    console.log(`   Latest file: ${latestFile.id} (${latestFile.original_filename})`);
    
    // Step 2: Simulate what frontend should do - set data sources
    console.log('\n2. Simulating frontend data source setup...');
    const dataSources = [latestFile.id];
    console.log(`   Data sources to send: ${JSON.stringify(dataSources)}`);
    
    // Step 3: Send chat message with data sources (like frontend should)
    console.log('\n3. Sending chat message with data sources...');
    const chatRequest = {
      message: 'Generate me a bar chart',
      data_sources: dataSources  // FIXED: Use data_sources (with underscore) to match backend schema
    };
    console.log(`   Chat request: ${JSON.stringify(chatRequest)}`);
    
    const chatResponse = await fetch('http://localhost:8000/api/v1/chat/message', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(chatRequest)
    });
    
    const chatResult = await chatResponse.json();
    console.log('   Chat response:', chatResult);
    
    // Step 4: Check if data context was properly passed
    console.log('\n4. Checking data context...');
    if (chatResult.content && chatResult.content.includes('I don\'t see any data file')) {
      console.log('   ❌ LLM still says no data file found');
      console.log('   This means the data sources are not reaching the LLM');
    } else {
      console.log('   ✅ LLM received data context properly');
    }
    
    // Step 5: Check backend logs for data context
    console.log('\n5. Backend should have received data sources...');
    console.log('   Check the backend logs to see if data_sources was received');
    
  } catch (error) {
    console.error('❌ Error during test:', error);
  }
};

// Run the test
testFrontendDataFlow(); 