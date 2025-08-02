// Test to debug the null serialization issue
const testNullFix = async () => {
  console.log('🔍 DEBUGGING NULL SERIALIZATION ISSUE');
  console.log('=' * 50);
  
  try {
    // Step 1: Get data from database
    console.log('1. 📊 Getting data from PostgreSQL database...');
    const filesResponse = await fetch('http://localhost:8000/api/v1/upload/files');
    const files = await filesResponse.json();
    
    const latestFile = files[0];
    console.log(`   📁 File: ${latestFile.original_filename}`);
    
    // Step 2: Check the data structure
    console.log('\n2. 🔍 Checking data structure...');
    const dataPreview = latestFile.data_preview;
    console.log(`   📊 Data type: ${typeof dataPreview}`);
    console.log(`   📋 Data keys: ${Object.keys(dataPreview).join(', ')}`);
    
    // Step 3: Check for null values in the data
    console.log('\n3. 🔍 Checking for null values...');
    const headData = dataPreview.head;
    console.log(`   📊 Head data type: ${typeof headData}`);
    console.log(`   📋 Head data length: ${headData.length}`);
    
    // Check first row for null values
    if (headData.length > 0) {
      const firstRow = headData[0];
      console.log(`   📊 First row keys: ${Object.keys(firstRow).slice(0, 5).join(', ')}...`);
      
      // Find null values
      const nullValues = [];
      Object.entries(firstRow).forEach(([key, value]) => {
        if (value === null) {
          nullValues.push(key);
        }
      });
      console.log(`   ❌ Null values found: ${nullValues.length} (${nullValues.slice(0, 3).join(', ')}...)`);
    }
    
    // Step 4: Test with a simple chart request
    console.log('\n4. 🎨 Testing simple chart request...');
    const chartRequest = {
      message: 'Create a simple bar chart with just 2 bars showing [1, 2] with labels ["A", "B"]. Do not use any data from the file.',
      data_sources: [latestFile.id]
    };
    
    const response = await fetch('http://localhost:8000/api/v1/chat/message', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(chartRequest)
    });
    
    const result = await response.json();
    console.log(`   ✅ Chart code generated: ${result.chartCode ? 'Yes' : 'No'}`);
    console.log(`   📈 Chart data: ${result.chartData ? 'Yes' : 'No'}`);
    
    if (result.chartData) {
      console.log('   🎉 SUCCESS: Chart generated successfully!');
    } else {
      console.log('   ❌ Chart generation failed');
      console.log(`   📝 Error: ${result.content}`);
    }
    
  } catch (error) {
    console.error('❌ Error during null fix test:', error);
  }
};

// Run the null fix test
testNullFix(); 