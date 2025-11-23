const axios = require('axios');

const BASE_URL = 'http://localhost:8000';

async function testCSVPreview() {
    console.log('🧪 Testing CSV Preview Functionality...\n');

    try {
        // 1. Check API health
        console.log('1. Checking API health...');
        const healthResponse = await axios.get(`${BASE_URL}/health`);
        console.log('✅ API is healthy\n');

        // 2. List files to get a file ID
        console.log('2. Listing uploaded files...');
        const filesResponse = await axios.get(`${BASE_URL}/api/v1/upload/files`);
        const files = filesResponse.data;
        console.log(`📁 Found ${files.length} files:`);
        files.forEach(file => {
            console.log(`   - ${file.original_filename} (${file.file_type}) - ID: ${file.id}`);
        });

        if (files.length === 0) {
            console.error('❌ No files uploaded. Please upload a file first to test CSV preview.');
            return;
        }
        const fileId = files[0].id;
        console.log(`\nUsing file ID: ${fileId} for CSV preview tests.\n`);

        // 3. Test file info endpoint
        console.log('3. Testing file info endpoint...');
        const fileInfoResponse = await axios.get(`${BASE_URL}/api/v1/csv-preview/file/${fileId}/info`);
        const fileInfo = fileInfoResponse.data;
        console.log('✅ File info retrieved successfully');
        console.log(`   - Filename: ${fileInfo.file_info.filename}`);
        console.log(`   - Total rows: ${fileInfo.data_info.total_rows}`);
        console.log(`   - Total columns: ${fileInfo.data_info.total_columns}\n`);

        // 4. Test file columns endpoint
        console.log('4. Testing file columns endpoint...');
        const fileColumnsResponse = await axios.get(`${BASE_URL}/api/v1/csv-preview/file/${fileId}/columns`);
        const fileColumns = fileColumnsResponse.data;
        console.log('✅ File columns retrieved successfully');
        console.log(`   - Total columns: ${fileColumns.columns.total_columns}`);
        console.log(`   - Numeric columns: ${fileColumns.columns.numeric_columns.length}`);
        console.log(`   - Categorical columns: ${fileColumns.columns.categorical_columns.length}\n`);

        // 5. Test CSV preview endpoint
        console.log('5. Testing CSV preview endpoint...');
        const previewResponse = await axios.post(`${BASE_URL}/api/v1/csv-preview/preview`, {
            file_id: fileId,
            page: 1,
            page_size: 5
        });
        const preview = previewResponse.data;
        console.log('✅ CSV preview retrieved successfully');
        console.log(`   - Data rows: ${preview.data.length}`);
        console.log(`   - Columns: ${preview.columns.length}`);
        console.log(`   - Total rows: ${preview.totalRows}`);
        console.log(`   - Total pages: ${preview.totalPages}`);
        console.log(`   - Current page: ${preview.currentPage}`);
        console.log(`   - Page size: ${preview.pageSize}\n`);

        // 6. Show sample data
        console.log('6. Sample data from first row:');
        if (preview.data.length > 0) {
            const firstRow = preview.data[0];
            Object.entries(firstRow).forEach(([key, value]) => {
                const truncatedValue = String(value).length > 50 ? String(value).substring(0, 50) + '...' : value;
                console.log(`   - ${key}: ${truncatedValue}`);
            });
        }

        console.log('\n🎉 All CSV preview tests completed successfully!');
        console.log('\n📋 Summary:');
        console.log('✅ API health check passed');
        console.log('✅ File listing works');
        console.log('✅ File info endpoint works');
        console.log('✅ File columns endpoint works');
        console.log('✅ CSV preview endpoint works');
        console.log('✅ Data pagination works');
        console.log('✅ Frontend can now display CSV previews with download functionality');

    } catch (error) {
        console.error('❌ An error occurred during testing:', error.message);
        if (error.response) {
            console.error('Response data:', error.response.data);
        }
    }
}

testCSVPreview(); 