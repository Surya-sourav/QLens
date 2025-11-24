# QLens - Agentic-AI For Complex Data Analysis

QLens is an intelligent data analysis platform that allows you to have natural conversations with your data. Upload CSV or Excel files and ask questions in plain English to get insights, visualizations, calculations, and data manipulation results.

## 🚀 New Features (Latest Update)

# Visuals :



<img width="1027" height="665" alt="Screenshot from 2025-08-02 11-14-27" src="https://github.com/user-attachments/assets/687c0201-e3c2-41ff-88bc-1bb875fea534" />


<img width="1480" height="797" alt="Screenshot from 2025-08-02 12-37-04" src="https://github.com/user-attachments/assets/964b963e-de4e-4310-b452-d86c5e8e9ccf" />


<img width="1789" height="876" alt="Screenshot from 2025-08-02 10-36-25" src="https://github.com/user-attachments/assets/e732fbb3-921d-4e90-a2c5-594d32cb1f8a" />


<img width="1789" height="876" alt="Screenshot from 2025-08-02 10-38-51" src="https://github.com/user-attachments/assets/8aa1edbe-8f86-45a4-b0c7-7158a08efea9" />


### 🤖 Agentic Data Analysis
QLens now supports intelligent, agentic interactions with your data:

- **📊 Smart Query Understanding**: Automatically detects your intent (calculations, visualizations, analysis, etc.)
- **🧮 Data Calculations**: Ask for totals, averages, counts, and more
- **🔍 Data Manipulation**: Filter, sort, group, and transform your data
- **📈 Intelligent Analysis**: Get AI-powered insights and pattern recognition
- **🎨 Dynamic Visualizations**: Generate charts based on your data and queries

### 📋 CSV/Excel Preview
Enhanced file viewing capabilities:

- **📄 Interactive Data Tables**: View your data with pagination and sorting
- **📊 File Information**: See detailed metadata about your uploaded files
- **🔍 Column Analysis**: Understand data types and column categories
- **📱 Responsive Design**: Works seamlessly on desktop and mobile

## ✨ Key Features

### Natural Language Queries
Ask questions in plain English:
- "What's the total cost?"
- "Show me transactions above $1000"
- "Create a bar chart of expenses by category"
- "Analyze spending patterns"
- "Calculate the average balance"

### Multi-Modal Responses
Get rich, contextual responses:
- **Text explanations** with insights and analysis
- **Interactive charts** and visualizations
- **Data tables** with filtered/sorted results
- **Calculations** with formatted results
- **Statistical summaries** and trends

### File Support
- **CSV files** (.csv)
- **Excel files** (.xlsx, .xls)
- **Large datasets** (up to 50MB)
- **Automatic data type detection**
- **Header recognition and processing**

### Real-time Chat Interface
- **WebSocket support** for real-time responses
- **Session management** for conversation continuity
- **Response type indicators** (calculation, visualization, analysis, etc.)
- **Error handling** with helpful feedback

## 🏗️ Architecture

### Backend (FastAPI + Python)
- **LangGraph Orchestrator**: Intelligent query routing and processing
- **Agentic Service**: Handles calculations, data manipulation, and analysis
- **LLM Integration**: Cerebras AI for natural language understanding
- **Code Execution**: Safe Python code execution for data processing
- **Database**: SQLAlchemy with PostgreSQL for data persistence

### Frontend (React + TypeScript)
- **Modern UI**: Clean, responsive interface with Tailwind CSS
- **Real-time Updates**: WebSocket integration for live responses
- **File Upload**: Drag-and-drop interface with progress tracking
- **Data Preview**: Interactive tables with pagination
- **Chart Rendering**: Dynamic visualization display

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- PostgreSQL (optional, SQLite for development)

### Backend Setup
```bash
cd backend
pip install -r requirements.txt

# Set up environment variables
cp env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Start the server
python -m uvicorn app.main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Docker Setup
```bash
docker-compose up -d
```

## 📖 Usage Examples

### 1. Upload and Preview Data
1. Upload a CSV or Excel file
2. Click the table icon to preview your data
3. Explore file information and column details

### 2. Ask Questions
Try these example queries:

**Calculations:**
- "What's the total cost?"
- "Calculate the average balance"
- "Show me the maximum transaction amount"
- "Count the number of transactions"

**Data Manipulation:**
- "Show me transactions above $1000"
- "Sort by date descending"
- "Filter by category 'Food'"
- "Show the top 10 largest transactions"

**Analysis:**
- "Analyze spending patterns"
- "Find trends in the data"
- "What are the most common categories?"
- "Identify outliers in the data"

**Visualizations:**
- "Create a bar chart of expenses by category"
- "Show me a line chart of spending over time"
- "Generate a pie chart of budget allocation"
- "Create a scatter plot of income vs expenses"

### 3. View Results
- **Calculation results** appear with formatted numbers and units
- **Data manipulation** shows filtered/sorted tables
- **Analysis results** provide insights and recommendations
- **Charts** render dynamically with interactive features

## 🔧 Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/qlens

# AI Service
CEREBRAS_API_KEY=your_cerebras_api_key

# File Upload
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=52428800

# CORS
CORS_ORIGINS=["http://localhost:3000"]
```

### API Endpoints

#### Chat
- `POST /api/v1/chat/message` - Send a message
- `GET /api/v1/chat/sessions` - List chat sessions
- `GET /api/v1/chat/session/{id}/messages` - Get session messages

#### File Upload
- `POST /api/v1/upload/file` - Upload a file
- `GET /api/v1/upload/files` - List uploaded files
- `DELETE /api/v1/upload/file/{id}` - Delete a file

#### CSV Preview
- `POST /api/v1/csv-preview/preview` - Get paginated data preview
- `GET /api/v1/csv-preview/file/{id}/info` - Get file information
- `GET /api/v1/csv-preview/file/{id}/columns` - Get column details

## 🧪 Testing

Run the comprehensive test suite:
```bash
# Test agentic features
node test_agentic_features.js

# Test backend
cd backend
pytest

# Test frontend
cd frontend
npm test
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check the inline code comments and API docs
- **Issues**: Report bugs and feature requests on GitHub
- **Discussions**: Join the community discussions

## 🔮 Roadmap

- [ ] Database connection support (PostgreSQL, MySQL)
- [ ] Advanced chart types (heatmaps, 3D plots)
- [ ] Data export functionality
- [ ] Collaborative features
- [ ] Mobile app
- [ ] API rate limiting and authentication
- [ ] Advanced analytics and machine learning

---

**QLens** - Making data analysis conversational and accessible to everyone! 🚀 