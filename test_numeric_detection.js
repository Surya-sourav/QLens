const axios = require('axios');

const BASE_URL = 'http://localhost:8000';

async function testNumericDetection() {
    console.log('🧪 Testing Numeric Column Detection Fix...\n');
    
    try {
        // 1. Check API health
        console.log('1. Checking API health...');
        const healthResponse = await axios.get(`${BASE_URL}/health`);
        console.log('✅ API is healthy\n');
        
        // 2. List files to see what's uploaded
        console.log('2. Listing uploaded files...');
        const filesResponse = await axios.get(`${BASE_URL}/api/v1/upload/files`);
        const files = filesResponse.data;
        console.log(`📁 Found ${files.length} files:`);
        files.forEach(file => {
            console.log(`   - ${file.filename} (${file.file_type})`);
        });
        console.log();
        
        if (files.length === 0) {
            console.log('❌ No files found. Please upload a CSV file first.');
            return;
        }
        
        // 3. Get file info for the first file
        const firstFile = files[0];
        console.log(`3. Getting file info for: ${firstFile.filename}`);
        const fileInfoResponse = await axios.get(`${BASE_URL}/api/v1/csv-preview/file/${firstFile.id}/info`);
        const fileInfo = fileInfoResponse.data;
        
        console.log('📊 File Information:');
        console.log(`   - Shape: ${fileInfo.data_info.total_rows} x ${fileInfo.data_info.total_columns}`);
        console.log(`   - Columns: ${fileInfo.data_info.columns.join(', ')}`);
        console.log(`   - Numeric Columns: ${fileInfo.data_info.numeric_columns.join(', ')}`);
        console.log(`   - Categorical Columns: ${fileInfo.data_info.categorical_columns.join(', ')}`);
        console.log();
        
        // 4. Test calculation query
        console.log('4. Testing calculation query...');
        const chatResponse = await axios.post(`${BASE_URL}/api/v1/chat/message`, {
            message: "Please give me the total mrp of the brand titan",
            data_sources: [firstFile.id]
        });
        
        const response = chatResponse.data;
        console.log('💬 Chat Response:');
        console.log(`   - Response Type: ${response.response_type}`);
        console.log(`   - Content: ${response.content}`);
        
        if (response.calculation_result) {
            console.log('🧮 Calculation Result:');
            console.log(`   - Operation: ${response.calculation_result.operation}`);
            console.log(`   - Result: ${response.calculation_result.result}`);
            console.log(`   - Description: ${response.calculation_result.description}`);
        }
        
        console.log('\n✅ Test completed!');
        
    } catch (error) {
        console.error('❌ Test failed:', error.response?.data || error.message);
    }
}

testNumericDetection(); 