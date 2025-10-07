# Legal Document Analyzer & RAG Chatbot

A FastAPI-based application that provides intelligent legal document analysis and conversational AI capabilities using LangGraph workflows.

## 🚀 Features

- **Document Analysis**: Automated analysis of legal documents (PDF/DOCX) with intelligent validation
- **RAG Chatbot**: Conversational AI for document-based Q&A using retrieval-augmented generation
- **Multi-Modal Workflow**: Seamless integration between analysis and chat features
- **Session Management**: Persistent chat sessions with document context
- **Production Ready**: Comprehensive error handling, logging, and CORS configuration

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Project Structure](#-project-structure)
- [Development](#-development)
- [Deployment](#-deployment)
- [Contributing](#-contributing)

## 🏗️ Architecture

### Core Components

1. **Document Workflow**: LangGraph-powered document analysis pipeline
   - Content validation using LLM
   - Document type identification
   - Key clause extraction
   - Structured summary generation

2. **RAG Workflow**: Conversational AI with document context
   - Vector store for document embeddings
   - Session-based conversation management
   - Context-aware response generation
   - Multi-turn dialogue support

3. **Document Processing**: Robust file handling
   - PDF text extraction with timeout protection
   - DOCX document processing
   - File validation and sanitization
   - Memory-efficient processing

## 📦 Installation

### Prerequisites

- Python 3.11+
- OpenAI API Key
- Google Gemini API Key

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Google_genai
   ```

2. **Create virtual environment**
   ```bash
   conda create -n google python=3.11
   conda activate google
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   Create a `.env` file in the project root:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   GOOGLE_API_KEY=your_google_api_key_here
   APP_NAME="Legal Document Analyzer"
   APP_VERSION="1.0.0"
   DEBUG=true
   ```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `OPENAI_API_KEY` | OpenAI API key for embeddings (RAG chatbot) | Yes | - |
| `GOOGLE_API_KEY` | Google Gemini API key for LLM operations (analysis & chat) | Yes | - |
| `APP_NAME` | Application name | No | "Legal Document Analyzer" |
| `APP_VERSION` | Application version | No | "1.0.0" |
| `DEBUG` | Enable debug mode | No | false |

### CORS Configuration

The application includes production-ready CORS settings:
- **Development**: Allows all origins (`*`)
- **Production**: Restricted to specific domains (configure in `main.py`)

## 🚀 Usage

### Starting the Application

```bash
# Development mode
python main.py

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000

# With custom configuration
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information and health status |
| `/health` | GET | Health check endpoint |
| `/analyze-document` | POST | Analyze legal documents |
| `/chat` | POST | RAG chatbot for document queries |

### Basic Workflow

1. **Document Analysis**
   ```bash
   curl -X POST "http://localhost:8000/analyze-document" \
        -F "file=@document.pdf"
   ```

2. **RAG Chat Initialization**
   ```bash
   curl -X POST "http://localhost:8000/chat" \
        -F "file=@document.pdf"
   ```

3. **Chat with Document**
   ```bash
   curl -X POST "http://localhost:8000/chat" \
        -F "message=What are the key terms in this contract?" \
        -F "session_id=your_session_id"
   ```

## 🤖 RAG Chatbot System

The RAG (Retrieval-Augmented Generation) chatbot is a core feature that enables intelligent conversations with your legal documents. It combines document retrieval with AI generation for accurate, context-aware responses.

### How RAG Chatbot Works

1. **Document Processing**: When you upload a document, it's automatically:
   - Split into semantic chunks using `RecursiveCharacterTextSplitter`
   - Converted to embeddings using OpenAI's `text-embedding-3-small` model
   - Stored in a FAISS vector database for fast retrieval

2. **Query Processing**: When you ask a question:
   - Your query is converted to embeddings
   - Similar document chunks are retrieved (top 3 most relevant)
   - Context is combined with your question for the AI model

3. **Response Generation**: The AI assistant (Gemini 2.5 Flash):
   - Uses retrieved context to provide accurate answers
   - Maintains conversation history for multi-turn dialogues
   - Focuses only on legal queries (politely declines non-legal questions)

### RAG Chatbot Features

#### ✅ **Session Management**
- **Persistent Sessions**: Each conversation has a unique session ID
- **Auto-Generated IDs**: Session IDs are automatically created if not provided
- **Document Context**: Documents remain accessible throughout the session
- **Conversation History**: Multi-turn dialogues with context retention

#### ✅ **Intelligent Document Processing**
- **Silent Upload**: Upload documents without generating chat responses
- **Vector Storage**: Efficient embedding-based document storage
- **Chunk Optimization**: Smart text splitting for optimal retrieval
- **Memory Efficient**: Documents are processed and stored per session

#### ✅ **Legal-Focused AI Assistant**
- **Legal Scope Only**: Responds only to legal document queries
- **Polite Declining**: Non-legal questions are professionally declined
- **Context-Aware**: Uses document content to provide accurate answers
- **Plain Language**: Explains complex legal terms in simple language

### RAG Workflow Examples

#### Example 1: Complete Document Chat Workflow
```bash
# Step 1: Upload document silently (prepares for chat)
curl -X POST "http://localhost:8000/chat" \
     -F "file=@employment_contract.pdf"

# Response: {"response": "", "session_id": "abc123", "document_processed": true}

# Step 2: Start asking questions
curl -X POST "http://localhost:8000/chat" \
     -F "message=What is my salary according to this contract?" \
     -F "session_id=abc123"

# Step 3: Continue conversation
curl -X POST "http://localhost:8000/chat" \
     -F "message=What are the termination conditions?" \
     -F "session_id=abc123"
```

#### Example 2: Upload with Initial Question
```bash
curl -X POST "http://localhost:8000/chat" \
     -F "file=@lease_agreement.pdf" \
     -F "message=What are my responsibilities as a tenant?"
```

#### Example 3: Non-Legal Query (Politely Declined)
```bash
curl -X POST "http://localhost:8000/chat" \
     -F "message=What's the weather today?" \
     -F "session_id=abc123"

# Response: "I'm a specialized legal document assistant and can only help 
# with questions related to legal documents, contracts, and legal concepts..."
```

### RAG Technical Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Document      │───▶│   Text          │───▶│   Vector        │
│   Upload        │    │   Splitting     │    │   Store         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Validation    │    │   Embeddings    │    │   FAISS Index   │
│   (Legal Doc)   │    │   Generation    │    │   Storage       │
└─────────────────┘    └─────────────────┘    └─────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Query    │───▶│   Similarity    │───▶│   Context       │
│                 │    │   Search        │    │   Retrieval     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Query +       │───▶│   Gemini 2.5    │───▶│   Legal         │
│   Context       │    │   Flash         │    │   Response      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### RAG Configuration

#### Key Settings in `app/core/rag_workflow.py`:
- **Embedding Model**: `text-embedding-3-small` (OpenAI) for high-quality embeddings
- **LLM Model**: `gemini-2.5-flash` (Google) with temperature 0.7 for balanced responses
- **Chunk Size**: 1000 characters with 200 character overlap
- **Retrieval**: Top 3 most relevant chunks per query
- **Session Storage**: In-memory FAISS vector stores per session

#### Prompt Engineering:
The RAG chatbot uses carefully crafted prompts that:
- Restrict responses to legal topics only
- Encourage plain language explanations
- Maintain professional tone
- Guide users to consult legal professionals when needed

### Frontend Integration for RAG

#### React Example - Complete RAG Workflow:
```javascript
// 1. Upload document silently
const uploadDocument = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('/chat', {
    method: 'POST',
    body: formData
  });
  
  const result = await response.json();
  return result.session_id; // Save for future queries
};

// 2. Ask questions about the document
const askQuestion = async (question, sessionId) => {
  const formData = new FormData();
  formData.append('message', question);
  formData.append('session_id', sessionId);
  
  const response = await fetch('/chat', {
    method: 'POST',
    body: formData
  });
  
  const result = await response.json();
  return result.response;
};

// 3. Complete workflow
const handleDocumentChat = async () => {
  const sessionId = await uploadDocument(selectedFile);
  const answer1 = await askQuestion("What are the key terms?", sessionId);
  const answer2 = await askQuestion("What are my obligations?", sessionId);
};
```

### RAG Best Practices

#### For Optimal Performance:
- **Document Quality**: Ensure documents have clear, readable text
- **Question Specificity**: Ask specific questions about document content
- **Session Reuse**: Reuse session IDs for related questions
- **Legal Context**: Frame questions in legal context for best results

#### Common Use Cases:
- **Contract Analysis**: "What are the payment terms in this contract?"
- **Legal Obligations**: "What are my responsibilities under this agreement?"
- **Risk Assessment**: "What penalties are mentioned for non-compliance?"
- **Term Clarification**: "What does 'force majeure' mean in this context?"
- **Comparison Queries**: "How does this differ from standard contracts?"

## 📚 API Documentation

For detailed API documentation including request/response schemas, see [API_DOCUMENTATION.md](./API_DOCUMENTATION.md).

Interactive API documentation is available at:
- **Swagger UI**: `http://localhost:8000/docs` (development only)
- **ReDoc**: `http://localhost:8000/redoc` (development only)

## 📁 Project Structure

```
Google_genai/
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── API_DOCUMENTATION.md   # Detailed API documentation
├── .env                   # Environment variables (create this)
├── app/
│   ├── __init__.py
│   ├── config.py          # Application configuration
│   ├── models.py          # Pydantic models
│   ├── logging_config.py  # Logging configuration
│   ├── core/
│   │   ├── __init__.py
│   │   ├── workflow.py        # Document analysis workflow
│   │   ├── rag_workflow.py    # RAG chatbot workflow
│   │   ├── analyzer.py        # Document analyzer component
│   │   └── validator.py       # Content validator component
│   └── utils/
│       ├── __init__.py
│       └── doc_process.py     # Document processing utilities
└── logs/
    └── app.log            # Application logs
```

## 🛠️ Development

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=app

# Run specific test file
python -m pytest tests/test_workflow.py
```

### Code Quality

```bash
# Format code
black app/ main.py

# Lint code
flake8 app/ main.py

# Type checking
mypy app/ main.py
```

### Adding New Features

1. Create feature branch: `git checkout -b feature/new-feature`
2. Implement changes following existing patterns
3. Add tests for new functionality
4. Update documentation
5. Submit pull request

## 🚀 Deployment

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Considerations

1. **Environment Variables**: Use secure secret management
2. **CORS**: Configure allowed origins for your domain
3. **Logging**: Ensure log directory has proper permissions
4. **Rate Limiting**: Consider adding rate limiting for production
5. **Load Balancing**: Use multiple workers with `--workers` flag

### Monitoring

- Application logs: `logs/app.log`
- Health check endpoint: `/health`
- Metrics: Monitor response times and error rates

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests and documentation
5. Submit a pull request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add type hints to all functions
- Write comprehensive docstrings
- Include unit tests for new features
- Update documentation for API changes

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the [API Documentation](./API_DOCUMENTATION.md)
- Review the logs in `logs/app.log`

## 🔄 Changelog

### v1.0.0
- Initial release
- Document analysis workflow
- RAG chatbot implementation
- Multi-format document support
- Session management
- Production-ready configuration
- **Streaming Analysis**: Real-time progress updates during document processing
- **Enhanced Error Handling**: Robust error handling with graceful fallbacks
- **Async Performance**: Fully asynchronous architecture for optimal performance
- **Advanced PDF Processing**: Uses PyPDFLoader for superior text extraction

## 🛠 Enhanced Tech Stack

- **FastAPI 0.115.0**: Modern async web framework with latest features
- **LangChain 0.3.7**: Latest framework for LLM applications with LCEL support
- **LangGraph 0.2.34**: Advanced workflow orchestration with streaming
- **Google Gemini 2.5 Flash**: State-of-the-art language model for document analysis
- **Pydantic 2.9.2**: Advanced data validation and serialization
- **PyPDF 5.0.1 + PyPDFLoader**: Enhanced PDF text extraction
- **python-docx 1.1.2**: DOCX document processing
- **Async Support**: Full async/await pattern implementation

## 📁 Enhanced Project Structure

```
e:\Projects\Google_genai\
├── app/
│   ├── core/
│   │   ├── analyzer.py      # Enhanced LangChain + Gemini with LCEL
│   │   └── workflow.py      # Advanced LangGraph workflow with streaming
│   ├── utils/
│   │   └── doc_process.py  # Async PDF/DOCX processing with PyPDFLoader
│   ├── config.py           # Application configuration
│   └── models.py           # Enhanced Pydantic response models
├── main.py                 # Enhanced FastAPI app with streaming & monitoring
├── requirements.txt        # Latest compatible dependencies
├── test_api.py            # Enhanced testing script
├── .env.example           # Environment variables template
└── README.md              # This enhanced documentation
```

## 🔧 Setup Instructions

### 1. Clone and Navigate
```bash
cd e:\Projects\Google_genai
```

### 2. Create Virtual Environment
```powershell
python -m venv venv
venv\Scripts\activate  # Windows PowerShell
```

### 3. Install Enhanced Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
copy .env.example .env
```

Edit `.env` file and add your Google API key:
```
GOOGLE_API_KEY=your_actual_google_api_key_here
```

### 5. Run the Enhanced Application
```bash
python main.py
```

The enhanced API will be available at:
- **Main API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics

## 🔗 Enhanced API Endpoints

### POST /analyze-document
Upload a legal document for comprehensive analysis with enhanced features.

**Request:**
- Content-Type: `multipart/form-data`
- File: PDF or DOCX document (max 10MB)
- Enhanced validation and processing

**Response:**
```json
{
  "document_type": "rental_agreement",
  "summary": "This is a residential lease agreement...",
  "important_clauses_explained": [
    {
      "clause_title": "Security Deposit",
      "original_text": "Tenant shall deposit...",
      "simplified_explanation": "You need to pay $2,000 upfront...",
      "risk_level": "Medium",
      "key_points": ["$2,000 deposit required", "Refundable if no damages"],
      "potential_concerns": "No timeline mentioned for deposit return"
    }
  ]
}
```

### POST /analyze-document-stream
Stream real-time analysis progress for better user experience.

**Features:**
- Real-time progress updates
- Server-sent events (SSE)
- Live workflow status
- Enhanced error handling

### GET /health
Enhanced health check with component status monitoring.

### GET /metrics
System metrics and configuration information.

### GET /
API information with feature overview.

## 📊 Supported Document Types

- **Rental Agreements** - Lease contracts and rental terms
- **Loan Contracts** - Personal and business loan agreements
- **Terms of Service** - Website and platform agreements
- **Employment Contracts** - Job agreements and employment terms
- **Non-Disclosure Agreements (NDAs)** - Confidentiality agreements
- **Purchase Agreements** - Sales and purchase contracts
- **Insurance Policies** - Coverage and policy documents
- **Other Legal Documents** - General legal document analysis

## 💻 Enhanced Usage Examples

### Using httpx (Recommended):
```python
import httpx
import asyncio

async def analyze_document():
    async with httpx.AsyncClient() as client:
        files = {"file": open("contract.pdf", "rb")}
        response = await client.post(
            "http://localhost:8000/analyze-document", 
            files=files,
            timeout=30.0
        )
        result = response.json()
        print(f"Document Type: {result['document_type']}")
        print(f"Summary: {result['summary']}")

asyncio.run(analyze_document())
```

### Streaming Analysis:
```python
import httpx
import json

async def stream_analysis():
    async with httpx.AsyncClient() as client:
        files = {"file": open("contract.pdf", "rb")}
        async with client.stream(
            "POST", 
            "http://localhost:8000/analyze-document-stream", 
            files=files
        ) as response:
            async for chunk in response.aiter_text():
                if chunk.startswith("data: "):
                    data = json.loads(chunk[6:])
                    print(f"Status: {data['status']}")

asyncio.run(stream_analysis())
```

### Using PowerShell (Windows):
```powershell
# Regular analysis
$response = Invoke-RestMethod -Uri "http://localhost:8000/analyze-document" -Method Post -Form @{file=Get-Item "document.pdf"}

# Health check
$health = Invoke-RestMethod -Uri "http://localhost:8000/health"
Write-Host "API Status: $($health.status)"
```

## ⚙️ Enhanced Configuration

Key configuration options in `.env`:

```env
# Google Cloud AI API Key (Required)
GOOGLE_API_KEY=your_google_api_key_here

# Application Settings
APP_NAME=Legal Document Analyzer
APP_VERSION=1.0.0
DEBUG=True

# File Upload Settings
MAX_FILE_SIZE_MB=10
ALLOWED_FILE_TYPES=["pdf", "docx"]

# Enhanced LLM Settings
MODEL_NAME=gemini-2.5-flash
TEMPERATURE=0.1
MAX_TOKENS=4096
```

## 🛡️ Enhanced Security & Error Handling

- **File Validation**: Enhanced type and size validation
- **Async Processing**: Non-blocking document processing
- **Error Recovery**: Graceful fallbacks and error handling
- **Request Tracking**: Analysis ID tracking for debugging
- **Memory Management**: Efficient memory usage with streaming
- **Input Sanitization**: Comprehensive input validation
- **Structured Errors**: Detailed error responses with tracking IDs

## 🚀 Enhanced Performance Features

- **Async Architecture**: Full async/await implementation
- **Streaming Support**: Real-time progress updates
- **Background Tasks**: Non-blocking background operations
- **Memory Optimization**: Efficient document processing
- **Connection Pooling**: Optimized HTTP client usage
- **Caching**: Response caching where appropriate
- **Monitoring**: Performance metrics and health checks

## 🧪 Testing the Enhanced API

Run the enhanced test script:
```bash
python test_api.py
```

Or test individual components:
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test metrics
curl http://localhost:8000/metrics

# Test file upload
curl -X POST "http://localhost:8000/upload-test" -F "file=@test.pdf"
```

## 🔄 Development & Customization

### Adding New Document Types
1. Update `DocumentType` enum in `app/models.py`
2. Add detection patterns in `analyzer.py`
3. Update prompts and workflows as needed

### Enhancing Analysis
- Modify prompts in `app/core/analyzer.py`
- Adjust model parameters in `app/config.py`
- Extend workflow logic in `app/core/workflow.py`
- Add new endpoints in `main.py`

### Monitoring & Logging
- Structured logging with analysis IDs
- Performance metrics collection
- Error tracking and reporting
- Health monitoring endpoints

## 🎯 Next Steps

This enhanced **document analysis and summarization** component is now ready. Next components to build:

1. **RAG Chatbot**: Enhanced conversational interface for document Q&A
2. **Knowledge Base**: Advanced legal terminology database with vector search
3. **Enhanced Security**: Privacy layers, encryption, and compliance features
4. **Frontend Interface**: Modern web UI with real-time streaming
5. **Analytics Dashboard**: Usage analytics and performance monitoring

## 📋 What's New in This Version

- ✅ **Latest Dependencies**: FastAPI 0.115.0, LangChain 0.3.7, LangGraph 0.2.34
- ✅ **Full Async Architecture**: Complete async/await implementation
- ✅ **Enhanced PDF Processing**: PyPDFLoader for better text extraction
- ✅ **Streaming Support**: Real-time analysis progress
- ✅ **Better Error Handling**: Comprehensive error recovery
- ✅ **Performance Monitoring**: Health checks and metrics
- ✅ **Enhanced Validation**: Improved file and content validation
- ✅ **Workflow Optimization**: Advanced LangGraph patterns

