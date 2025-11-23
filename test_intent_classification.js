const axios = require('axios');

const BASE_URL = 'http://localhost:8000';

async function testIntentClassification() {
    console.log('🧪 Testing Enhanced Intent Classification...\n');
    
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
            console.log('❌ No files found. Please upload a file first.');
            return;
        }
        
        const firstFile = files[0];
        console.log(`📊 Using file: ${firstFile.filename}\n`);
        
        // 3. Test various query types to verify intent classification
        const testQueries = [
            {
                query: "How many Quantity are there of Titan & Chumbak ?",
                expectedIntent: "calculation",
                description: "Count query with 'many' keyword"
            },
            {
                query: "What is the total mrp of the brand titan?",
                expectedIntent: "calculation", 
                description: "Total calculation query"
            },
            {
                query: "Give me the average price",
                expectedIntent: "calculation",
                description: "Average calculation query"
            },
            {
                query: "Show me a bar chart of brands",
                expectedIntent: "visualization",
                description: "Visualization query"
            },
            {
                query: "Filter by brand",
                expectedIntent: "data_manipulation",
                description: "Data manipulation query"
            },
            {
                query: "Hello, how are you?",
                expectedIntent: "general_query",
                description: "General greeting"
            }
        ];
        
        console.log('3. Testing Intent Classification:');
        console.log('=' .repeat(60));
        
        for (let i = 0; i < testQueries.length; i++) {
            const testCase = testQueries[i];
            console.log(`\n${i + 1}. Testing: "${testCase.query}"`);
            console.log(`   Expected: ${testCase.expectedIntent}`);
            console.log(`   Description: ${testCase.description}`);
            
            try {
                const chatResponse = await axios.post(`${BASE_URL}/api/v1/chat/message`, {
                    message: testCase.query,
                    data_sources: [firstFile.id]
                });
                
                const response = chatResponse.data;
                const actualIntent = response.query_intent;
                const responseType = response.response_type;
                
                console.log(`   Actual Intent: ${actualIntent}`);
                console.log(`   Response Type: ${responseType}`);
                
                if (actualIntent === testCase.expectedIntent) {
                    console.log(`   ✅ PASS - Intent correctly classified`);
                } else {
                    console.log(`   ❌ FAIL - Expected ${testCase.expectedIntent}, got ${actualIntent}`);
                }
                
                // Show response details for calculation queries
                if (actualIntent === 'calculation' && response.calculation_result) {
                    const calcResult = response.calculation_result;
                    console.log(`   📊 Calculation Result:`);
                    console.log(`      Operation: ${calcResult.operation}`);
                    console.log(`      Result: ${calcResult.result}`);
                    console.log(`      Description: ${calcResult.description}`);
                }
                
            } catch (error) {
                console.log(`   ❌ ERROR: ${error.response?.data?.detail || error.message}`);
            }
        }
        
        console.log('\n' + '=' .repeat(60));
        console.log('🎯 Intent Classification Test Complete!');
        
    } catch (error) {
        console.error('❌ Test failed:', error.response?.data || error.message);
    }
}

testIntentClassification(); 