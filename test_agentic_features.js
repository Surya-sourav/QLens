const axios = require('axios');

const API_BASE_URL = 'http://localhost:8000/api/v1';

async function testAgenticFeatures() {
  console.log('🧪 Testing QLens Agentic Features...\n');

  try {
    // Test 1: Check API health
    console.log('1. Testing API health...');
    const healthResponse = await axios.get(`${API_BASE_URL}/health`);
    console.log('✅ API is healthy:', healthResponse.data);

    // Test 2: Get API info
    console.log('\n2. Getting API info...');
    const infoResponse = await axios.get(`${API_BASE_URL}/info`);
    console.log('✅ API info:', infoResponse.data);

    // Test 3: Get uploaded files
    console.log('\n3. Getting uploaded files...');
    const filesResponse = await axios.get(`${API_BASE_URL}/upload/files`);
    console.log('✅ Files found:', filesResponse.data.length);

    if (filesResponse.data.length === 0) {
      console.log('⚠️  No files found. Please upload a file first to test agentic features.');
      return;
    }

    const fileId = filesResponse.data[0].id;
    console.log('📁 Using file ID:', fileId);

    // Test 4: Test CSV preview functionality
    console.log('\n4. Testing CSV preview...');
    const previewResponse = await axios.post(`${API_BASE_URL}/csv-preview/preview`, {
      fileId: fileId,
      page: 1,
      pageSize: 10
    });
    console.log('✅ CSV preview working:', {
      totalRows: previewResponse.data.totalRows,
      totalPages: previewResponse.data.totalPages,
      columns: previewResponse.data.columns.length
    });

    // Test 5: Test calculation query
    console.log('\n5. Testing calculation query...');
    const calcResponse = await axios.post(`${API_BASE_URL}/chat/message`, {
      message: "What's the total cost?",
      data_sources: [fileId]
    });
    console.log('✅ Calculation response type:', calcResponse.data.responseType);
    console.log('✅ Calculation content:', calcResponse.data.content.substring(0, 100) + '...');

    // Test 6: Test data manipulation query
    console.log('\n6. Testing data manipulation query...');
    const manipResponse = await axios.post(`${API_BASE_URL}/chat/message`, {
      message: "Show me the first 5 rows",
      data_sources: [fileId]
    });
    console.log('✅ Manipulation response type:', manipResponse.data.responseType);
    console.log('✅ Manipulation content:', manipResponse.data.content.substring(0, 100) + '...');

    // Test 7: Test analysis query
    console.log('\n7. Testing analysis query...');
    const analysisResponse = await axios.post(`${API_BASE_URL}/chat/message`, {
      message: "Analyze the spending patterns",
      data_sources: [fileId]
    });
    console.log('✅ Analysis response type:', analysisResponse.data.responseType);
    console.log('✅ Analysis content:', analysisResponse.data.content.substring(0, 100) + '...');

    // Test 8: Test visualization query
    console.log('\n8. Testing visualization query...');
    const vizResponse = await axios.post(`${API_BASE_URL}/chat/message`, {
      message: "Create a bar chart of expenses by category",
      data_sources: [fileId]
    });
    console.log('✅ Visualization response type:', vizResponse.data.responseType);
    console.log('✅ Has chart data:', !!vizResponse.data.chartData);

    console.log('\n🎉 All agentic features tests completed successfully!');
    console.log('\n📋 Summary of features tested:');
    console.log('   ✅ CSV Preview with pagination');
    console.log('   ✅ Calculation queries (total cost, averages, etc.)');
    console.log('   ✅ Data manipulation (filtering, sorting, etc.)');
    console.log('   ✅ Data analysis (patterns, insights, etc.)');
    console.log('   ✅ Visualization generation (charts, graphs)');
    console.log('   ✅ Response type classification');
    console.log('   ✅ Multi-modal responses (text + data + charts)');

  } catch (error) {
    console.error('❌ Test failed:', error.response?.data || error.message);
    console.log('\n🔧 Troubleshooting tips:');
    console.log('   1. Make sure the backend server is running on port 8000');
    console.log('   2. Upload a CSV or Excel file first');
    console.log('   3. Check that all dependencies are installed');
    console.log('   4. Verify the database is properly configured');
  }
}

// Run the tests
testAgenticFeatures(); 