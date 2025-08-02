# QLens - AI-Powered Data Conversation Platform

QLens is an intelligent data analysis platform that allows users to have natural conversations with their data. Upload CSV/Excel files and ask questions to get instant visualizations and insights powered by AI.


##Visuals :
<img width="1027" height="665" alt="Screenshot from 2025-08-02 11-14-27" src="https://github.com/user-attachments/assets/687c0201-e3c2-41ff-88bc-1bb875fea534" />

<img width="1480" height="797" alt="Screenshot from 2025-08-02 12-37-04" src="https://github.com/user-attachments/assets/964b963e-de4e-4310-b452-d86c5e8e9ccf" />
<img width="1789" height="876" alt="Screenshot from 2025-08-02 10-36-25" src="https://github.com/user-attachments/assets/e732fbb3-921d-4e90-a2c5-594d32cb1f8a" />
<img width="1789" height="876" alt="Screenshot from 2025-08-02 10-38-51" src="https://github.com/user-attachments/assets/8aa1edbe-8f86-45a4-b0c7-7158a08efea9" />

## 🚀 Features

- **Natural Language Queries**: Ask questions about your data in plain English
- **AI-Powered Analysis**: Advanced LLM integration for intelligent data interpretation
- **Interactive Visualizations**: Generate charts, graphs, and plots automatically
- **File Upload Support**: Upload CSV and Excel files for analysis
- **Real-time Chat Interface**: Interactive conversation with your data
- **PostgreSQL Integration**: Connect to external databases
- **Docker Support**: Easy deployment with containerization

## 🏗️ Architecture

- **Frontend**: React.js with modern UI components
- **Backend**: FastAPI with Python
- **Database**: PostgreSQL (Neon DB)
- **AI/LLM**: Cerebras API integration
- **Containerization**: Docker & Docker Compose
- **Orchestration**: LangGraph for workflow management

## 📋 Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Node.js 18+ (for frontend development)
- PostgreSQL database (or Neon DB)

## 🛠️ Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Surya-sourav/QLens.git
cd QLens
```

### 2. Environment Configuration

Create a `.env` file in the root directory:

```bash
# Database Configuration
DATABASE_URL=postgresql://username:password@host:port/database

# Cerebras API Configuration
CEREBRAS_API_KEY=your_cerebras_api_key

# Redis Configuration
REDIS_URL=redis://redis:6379

# Application Configuration
SECRET_KEY=your-secret-key
DEBUG=True
HOST=0.0.0.0
PORT=8000

# File Upload Configuration
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=10485760
```

### 3. Using Docker (Recommended)

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 4. Manual Setup

#### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Initialize database
python init_db.py

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## 🚀 Usage

1. **Start the Application**: Run `docker-compose up -d`
2. **Access the Interface**: Open `http://localhost:3000` in your browser
3. **Upload Data**: Upload CSV or Excel files through the interface
4. **Ask Questions**: Use natural language to query your data
5. **View Results**: Get instant visualizations and insights

### Example Queries

- "Show me a bar chart of sales by region"
- "What's the trend of revenue over time?"
- "Create a pie chart showing customer distribution"
- "Which products have the highest profit margins?"

## 📁 Project Structure

```
QLens/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── models/         # Database models
│   │   ├── routers/        # API endpoints
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utility functions
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/         # Page components
│   │   └── services/      # API services
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml      # Docker orchestration
├── .gitignore
└── README.md
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `CEREBRAS_API_KEY` | Cerebras API key | Required |
| `REDIS_URL` | Redis connection string | `redis://redis:6379` |
| `SECRET_KEY` | Application secret key | Required |
| `DEBUG` | Debug mode | `True` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |

### API Endpoints

- `POST /api/v1/upload/file` - Upload files
- `POST /api/v1/chat/message` - Send chat messages
- `GET /api/v1/upload/files` - List uploaded files
- `GET /api/v1/chat/sessions` - List chat sessions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/Surya-sourav/QLens/issues) page
2. Create a new issue with detailed information
3. Contact the development team

## 🗺️ Roadmap

- [ ] Enhanced chart customization options
- [ ] Support for more file formats
- [ ] Advanced analytics features
- [ ] User authentication and authorization
- [ ] Collaborative workspaces
- [ ] API rate limiting and optimization
- [ ] Mobile application

## 🙏 Acknowledgments

- FastAPI for the robust backend framework
- React for the modern frontend framework
- Cerebras for AI/LLM capabilities
- LangGraph for workflow orchestration
- Docker for containerization support 
