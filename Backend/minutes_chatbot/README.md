# Minutes Chatbot - ChatGPT Style

A production-ready chatbot system with email authentication, document upload, and RAG-based Q&A capabilities.

## 🎯 Features

- **Email-based authentication** - Users login with email (no password required)
- **AI-generated agenda detection** - Automatically shows user's agendas
- **Document upload** - Supports PDF, Excel, PPT, Word, scanned PDFs
- **RAG Q&A** - Ask questions about uploaded documents
- **Chat history** - Conversation history saved per user (like ChatGPT)
- **PostgreSQL database** - Production-grade database on Azure
- **Semantic search** - Vector embeddings for intelligent document search

## 📁 Project Structure

```
minutes_chatbot/
├── config/
│   ├── __init__.py
│   ├── settings.py          # Configuration management
│   └── logging_config.py    # Logging setup
├── database/
│   ├── __init__.py
│   ├── models.py            # SQLAlchemy models
│   ├── connection.py        # Database connection
│   └── init_db.py           # Database initialization
├── services/
│   ├── __init__.py
│   ├── auth_service.py      # User authentication
│   ├── document_service.py  # Document upload & processing
│   ├── embedding_service.py # Vector embeddings
│   ├── chatbot_service.py   # RAG chatbot logic
│   └── agenda_service.py    # Agenda detection
├── api/
│   ├── __init__.py
│   ├── auth.py              # Authentication endpoints
│   ├── documents.py         # Document endpoints
│   ├── chatbot.py           # Chatbot endpoints
│   └── history.py           # Chat history endpoints
├── utils/
│   ├── __init__.py
│   ├── text_extraction.py   # Extract text from files
│   └── validators.py        # Input validation
├── tests/
│   ├── test_auth.py
│   ├── test_documents.py
│   └── test_chatbot.py
├── uploads/                 # Uploaded documents storage
├── .env                     # Environment variables (not in git)
├── .env.example             # Example environment variables
├── requirements.txt         # Python dependencies
├── main.py                  # FastAPI application entry point
└── README.md                # This file
```

## 🛠️ Prerequisites

- Python 3.9+
- PostgreSQL database (Azure-hosted)
- Azure OpenAI API access
- pip (Python package manager)

## 📦 Installation

### Step 1: Clone/Create Project Directory

```bash
cd /Users/sohelkumarsahoo/Downloads/aegis_chatbot_shared_3
mkdir minutes_chatbot
cd minutes_chatbot
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your actual values:
```
# PostgreSQL Database
PGHOST=az10psqldmrcbtp01.postgres.database.azure.com
PGUSER=psqladmin
PGPORT=5432
PGDATABASE=postgres
PGPASSWORD=your_actual_password_here

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002

# Application
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=10485760  # 10MB in bytes
ALLOWED_EXTENSIONS=pdf,docx,xlsx,pptx,doc,xls,ppt
```

### Step 4: Initialize Database

```bash
python -m database.init_db
```

This will:
- Create all 5 tables (users, agendas, documents, chat_history, document_embeddings)
- Create indexes for performance
- Enable pgvector extension

### Step 5: Run the Application

```bash
python main.py
```

The API will be available at: `http://localhost:8000`

## 🚀 Usage

### 1. User Login (Email)

```bash
POST /api/auth/login
{
  "email": "cfo@adanigreen.com"
}
```

Response:
```json
{
  "user_id": 1,
  "email": "cfo@adanigreen.com",
  "agendas": [
    {
      "id": 1,
      "title": "Board Meeting - Q3 Review",
      "meeting_date": "2024-02-15"
    }
  ]
}
```

### 2. Upload Document

```bash
POST /api/documents/upload
Headers: { "X-User-Email": "cfo@adanigreen.com" }
Form Data: { "file": <file> }
```

### 3. Ask Question

```bash
POST /api/chatbot/query
{
  "email": "cfo@adanigreen.com",
  "query": "What was the revenue growth in Q3?",
  "session_id": "session_20240204_1730"
}
```

Response:
```json
{
  "answer": "According to the Q3 Financial Results document, revenue grew by 15% year-over-year to Rs. 5,200 Crores.",
  "sources": [
    {
      "document": "Q3_Results.pdf",
      "chunk": "Q3 revenue grew by 15% to Rs. 5,200 Cr"
    }
  ]
}
```

### 4. Get Chat History

```bash
GET /api/history/{email}?session_id=session_20240204_1730
```

## 🏗️ Architecture

### Layered Architecture

```
┌─────────────────────────────────────┐
│   Presentation Layer (FastAPI)     │  ← API endpoints
├─────────────────────────────────────┤
│   Business Logic Layer (Services)  │  ← Core logic
├─────────────────────────────────────┤
│   Data Access Layer (Database)     │  ← PostgreSQL
└─────────────────────────────────────┘
```

### RAG Flow

```
User Query
    ↓
Convert to Embedding
    ↓
Search Document Embeddings (Semantic Search)
    ↓
Retrieve Top-K Relevant Chunks
    ↓
Send to LLM with Context
    ↓
Generate Answer
    ↓
Save to Chat History
    ↓
Return to User
```

## 📊 Database Schema

### Tables

1. **users** - User accounts (email-based)
2. **agendas** - AI-generated agendas
3. **documents** - Uploaded files metadata
4. **chat_history** - Conversation history
5. **document_embeddings** - Vector embeddings for search

See [POSTGRESQL_DATABASE_GUIDE.md](../POSTGRESQL_DATABASE_GUIDE.md) for detailed schema.

## 🔒 Security Best Practices

- Environment variables for sensitive data
- Input validation on all endpoints
- File type and size validation
- SQL injection prevention (SQLAlchemy ORM)
- CORS configuration

## 📝 Logging

Logs are written to:
- Console (INFO level)
- File: `logs/minutes_chatbot.log` (DEBUG level)

Example log:
```
2024-02-04 18:00:00 - INFO - User cfo@adanigreen.com logged in
2024-02-04 18:01:00 - INFO - Document uploaded: Q3_Results.pdf (2.5 MB)
2024-02-04 18:02:00 - INFO - Query processed: "What was the revenue growth?"
```

## 🧪 Testing

Run tests:
```bash
pytest tests/
```

Run with coverage:
```bash
pytest --cov=. tests/
```

## 📚 API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🐛 Troubleshooting

### Database Connection Error
```
Error: could not connect to server
```
**Solution:** Check your PostgreSQL credentials in `.env` file

### pgvector Extension Not Found
```
Error: extension "vector" does not exist
```
**Solution:** Run `CREATE EXTENSION vector;` in PostgreSQL

### File Upload Error
```
Error: File too large
```
**Solution:** Check `MAX_FILE_SIZE` in `.env` (default: 10MB)

## 📞 Support

For issues or questions, contact the development team.

## 📄 License

Proprietary - Adani Group
