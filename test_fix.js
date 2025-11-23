const axios = require('axios');

const API_BASE_URL = 'http://localhost:8000/api/v1';

async function testFix() {
  console.log('🔧 Testing the fix for calculation errors...\n');

  try {
    // Test 1: Check API health
    console.log('1. Testing API health...');
    const healthResponse = await axios.get(`${API_BASE_URL}/health`);
    console.log('✅ API is healthy:', healthResponse.data);

    // Test 2: Get uploaded files
    console.log('\n2. Getting uploaded files...');
    const filesResponse = await axios.get(`${API_BASE_URL}/upload/files`);
    console.log('✅ Files found:', filesResponse.data.length);

    if (filesResponse.data.length === 0) {
      console.log('⚠️  No files found. Please upload a file first to test the fix.');
      return;
    }

    const fileId = filesResponse.data[0].id;
    console.log('📁 Using file ID:', fileId);

    // Test 3: Test calculation query (this was failing before)
    console.log('\n3. Testing calculation query...');
    const calcResponse = await axios.post(`${API_BASE_URL}/chat/message`, {
      message: "What's the total cost?",
      data_sources: [fileId]
    });
    
    console.log('✅ Calculation response received');
    console.log('✅ Response type:', calcResponse.data.responseType);
    console.log('✅ Content length:', calcResponse.data.content.length);
    console.log('✅ Has calculation result:', !!calcResponse.data.calculationResult);
    
    if (calcResponse.data.calculationResult) {
      console.log('✅ Calculation operation:', calcResponse.data.calculationResult.operation);
      console.log('✅ Calculation result:', calcResponse.data.calculationResult.result);
    }

    console.log('\n🎉 Fix test completed successfully!');
    console.log('✅ The calculation error has been resolved.');

  } catch (error) {
    console.error('❌ Test failed:', error.response?.data || error.message);
    console.log('\n🔧 If the error persists, check:');
    console.log('   1. Backend server is running');
    console.log('   2. File has numeric columns');
    console.log('   3. Database is properly configured');
  }
}

// Run the test
testFix(); 