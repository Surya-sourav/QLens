const axios = require('axios');

const API_BASE_URL = 'http://localhost:8000/api/v1';

async function testDataContext() {
  console.log('🔍 Testing data context and file information...\n');

  try {
    // Test 1: Get uploaded files
    console.log('1. Getting uploaded files...');
    const filesResponse = await axios.get(`${API_BASE_URL}/upload/files`);
    console.log('✅ Files found:', filesResponse.data.length);

    if (filesResponse.data.length === 0) {
      console.log('⚠️  No files found. Please upload a file first.');
      return;
    }

    const file = filesResponse.data[0];
    console.log('📁 File details:');
    console.log('   - ID:', file.id);
    console.log('   - Name:', file.originalFilename);
    console.log('   - Type:', file.fileType);
    console.log('   - Size:', file.size);
    console.log('   - Processed:', file.processed);

    // Test 2: Get file info
    console.log('\n2. Getting file info...');
    const infoResponse = await axios.get(`${API_BASE_URL}/csv-preview/file/${file.id}/info`);
    console.log('✅ File info:', JSON.stringify(infoResponse.data, null, 2));

    // Test 3: Get file columns
    console.log('\n3. Getting file columns...');
    const columnsResponse = await axios.get(`${API_BASE_URL}/csv-preview/file/${file.id}/columns`);
    console.log('✅ File columns:', JSON.stringify(columnsResponse.data, null, 2));

    // Test 4: Get CSV preview
    console.log('\n4. Getting CSV preview...');
    const previewResponse = await axios.post(`${API_BASE_URL}/csv-preview/preview`, {
      fileId: file.id,
      page: 1,
      pageSize: 5
    });
    console.log('✅ CSV preview:');
    console.log('   - Total rows:', previewResponse.data.totalRows);
    console.log('   - Total pages:', previewResponse.data.totalPages);
    console.log('   - Columns:', previewResponse.data.columns);
    console.log('   - Sample data:', previewResponse.data.data.slice(0, 2));

    // Test 5: Test a simple calculation query
    console.log('\n5. Testing calculation query...');
    const calcResponse = await axios.post(`${API_BASE_URL}/chat/message`, {
      message: "What's the total cost?",
      data_sources: [file.id]
    });
    
    console.log('✅ Calculation response:');
    console.log('   - Response type:', calcResponse.data.responseType);
    console.log('   - Content:', calcResponse.data.content.substring(0, 200) + '...');
    console.log('   - Has calculation result:', !!calcResponse.data.calculationResult);
    
    if (calcResponse.data.calculationResult) {
      console.log('   - Calculation details:', calcResponse.data.calculationResult);
    }

    console.log('\n🎉 Data context test completed!');

  } catch (error) {
    console.error('❌ Test failed:', error.response?.data || error.message);
    if (error.response?.data) {
      console.log('Error details:', JSON.stringify(error.response.data, null, 2));
    }
  }
}

// Run the test
testDataContext(); 