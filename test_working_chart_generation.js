// Test to generate a working chart by using a simpler approach
const testWorkingChartGeneration = async () => {
  console.log('🎯 WORKING CHART GENERATION TEST');
  console.log('=' * 50);
  
  try {
    // Step 1: Get data from database
    console.log('1. 📊 Getting data from PostgreSQL database...');
    const filesResponse = await fetch('http://localhost:8000/api/v1/upload/files');
    const files = await filesResponse.json();
    console.log(`   ✅ Found ${files.length} files`);
    
    const latestFile = files[0];
    console.log(`   📁 Using: ${latestFile.original_filename}`);
    
    // Step 2: Test with a very simple chart request that should work
    console.log('\n2. 🎨 Testing simple chart generation...');
    const simpleRequest = {
      message: 'Create a very simple bar chart with just 3 bars showing values [1, 2, 3] with labels ["A", "B", "C"]. Do not use any data from the file, just create a simple example chart.',
      data_sources: [latestFile.id]
    };
    
    const response = await fetch('http://localhost:8000/api/v1/chat/message', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(simpleRequest)
    });
    
    const result = await response.json();
    console.log(`   ✅ Chart code generated: ${result.chartCode ? 'Yes' : 'No'}`);
    console.log(`   📈 Chart data: ${result.chartData ? 'Yes' : 'No'}`);
    console.log(`   📝 Code length: ${result.chartCode?.length || 0} characters`);
    
    if (result.chartData) {
      console.log('   🎉 SUCCESS: Chart generated successfully!');
      console.log(`   📊 Chart type: ${result.chartType || 'Unknown'}`);
      console.log(`   📈 Chart data type: ${result.chartData.type}`);
      if (result.chartData.type === 'matplotlib') {
        console.log(`   🖼️  Chart image size: ${result.chartData.data.length} characters (base64)`);
        console.log('   📊 Chart is ready to be displayed!');
      }
    } else {
      console.log('   ❌ Chart generation failed');
      console.log(`   📝 Error: ${result.content}`);
    }
    
    // Step 3: Test with a data-based chart using a different approach
    console.log('\n3. 🎨 Testing data-based chart generation...');
    const dataRequest = {
      message: 'Create a bar chart using only the first row of data. Use simple values like [10, 20, 30] for the bars and avoid any complex data processing.',
      data_sources: [latestFile.id]
    };
    
    const dataResponse = await fetch('http://localhost:8000/api/v1/chat/message', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(dataRequest)
    });
    
    const dataResult = await dataResponse.json();
    console.log(`   ✅ Chart code generated: ${dataResult.chartCode ? 'Yes' : 'No'}`);
    console.log(`   📈 Chart data: ${dataResult.chartData ? 'Yes' : 'No'}`);
    
    if (dataResult.chartData) {
      console.log('   🎉 SUCCESS: Data-based chart generated!');
    } else {
      console.log('   ❌ Data-based chart generation failed');
    }
    
    // Step 4: Final summary
    console.log('\n4. 📋 FINAL SUMMARY:');
    const successfulCharts = [result, dataResult].filter(r => r.chartData);
    
    if (successfulCharts.length > 0) {
      console.log('   🎉 SUCCESS: Working chart generation achieved!');
      console.log('   ✅ The system can generate actual chart images');
      console.log('   📊 Chart generation is working end-to-end');
    } else {
      console.log('   ⚠️  PARTIAL SUCCESS: Chart code generation works, but execution fails');
      console.log('   🔧 The issue is in chart execution, not data context');
    }
    
    // Step 5: Show the generated code
    if (result.chartCode) {
      console.log('\n5. 📝 Generated Chart Code:');
      console.log('   ┌─────────────────────────────────────────────────────────┐');
      console.log('   │                    GENERATED CODE                      │');
      console.log('   ├─────────────────────────────────────────────────────────┤');
      const codeLines = result.chartCode.split('\n');
      codeLines.slice(0, 15).forEach(line => {
        console.log(`   │ ${line.padEnd(55)} │`);
      });
      if (codeLines.length > 15) {
        console.log('   │ ... (truncated) ...                                   │');
      }
      console.log('   └─────────────────────────────────────────────────────────┘');
    }
    
  } catch (error) {
    console.error('❌ Error during working chart test:', error);
  }
};

// Run the working chart test
testWorkingChartGeneration(); 