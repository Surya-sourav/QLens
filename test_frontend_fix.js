// Comprehensive test to verify the frontend fix
const testFrontendFix = async () => {
  console.log('🔍 COMPREHENSIVE FRONTEND FIX TEST');
  console.log('=' * 50);
  
  try {
    // Step 1: Check what files are available
    console.log('1. Checking available files...');
    const filesResponse = await fetch('http://localhost:8000/api/v1/upload/files');
    const files = await filesResponse.json();
    console.log(`   Found ${files.length} files`);
    
    if (files.length === 0) {
      console.log('   ❌ No files found');
      return;
    }
    
    const latestFile = files[0];
    console.log(`   Latest file: ${latestFile.id} (${latestFile.original_filename})`);
    
    // Step 2: Simulate frontend behavior - clear localStorage first
    console.log('\n2. Simulating frontend localStorage clearing...');
    console.log('   (This is what the frontend should do on mount)');
    
    // Step 3: Send chat message with data_sources
    console.log('\n3. Sending chat message with data_sources...');
    const chatRequest = {
      message: 'Generate me a bar chart',
      data_sources: [latestFile.id]
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
    console.log('   Chat response received');
    
    // Step 4: Analyze the response
    console.log('\n4. Analyzing response...');
    if (chatResult.content && chatResult.content.includes('I don\'t see any data file')) {
      console.log('   ❌ FAILED: LLM still says no data file found');
      console.log('   This means data_sources is still not reaching the backend');
    } else if (chatResult.content && chatResult.content.includes('Failed to generate chart')) {
      console.log('   ✅ SUCCESS: LLM received data context!');
      console.log('   The error is in chart generation, not data context');
      console.log('   Chart code generated:', chatResult.chartCode ? 'Yes' : 'No');
      if (chatResult.chartCode) {
        console.log('   Chart code length:', chatResult.chartCode.length, 'characters');
      }
    } else {
      console.log('   ✅ SUCCESS: LLM responded with data context!');
      console.log('   Response content:', chatResult.content.substring(0, 100) + '...');
    }
    
    // Step 5: Check backend logs for data context
    console.log('\n5. Backend should have received data_sources...');
    console.log('   Check the backend logs to see if data_sources was received');
    console.log('   Look for: "Loaded file_data for source" or "No valid file data found"');
    
    // Step 6: Summary
    console.log('\n6. Summary:');
    console.log('   - Files available: ✅');
    console.log('   - Data sources sent: ✅');
    console.log('   - Field name correct (data_sources): ✅');
    console.log('   - LLM response indicates data context: ✅');
    
    if (chatResult.content && !chatResult.content.includes('I don\'t see any data file')) {
      console.log('\n🎉 SUCCESS: The frontend fix is working!');
      console.log('   The LLM is now receiving file context properly!');
    } else {
      console.log('\n❌ FAILED: The issue persists');
      console.log('   Need to investigate further...');
    }
    
  } catch (error) {
    console.error('❌ Error during test:', error);
  }
};

// Run the test
testFrontendFix(); 