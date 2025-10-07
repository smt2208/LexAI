# Project Architecture Flow Diagram

## Complete System Architecture

```mermaid
graph TD
    %% Frontend Layer
    FE[React Frontend] --> |File Upload| API[FastAPI Backend]
    FE --> |Chat Message| API
    FB[(Firebase Database)] --> FE
    
    %% API Gateway
    API --> |/analyze-document| AW[Analyze Workflow]
    API --> |/chat| CW[Chat Workflow]
    
    %% Document Processing Common Layer
    AW --> DP[Document Processor]
    CW --> DP
    DP --> |Extract Text| PDF[PDF/DOCX Files]
    
    %% Validation Layer (Common)
    DP --> VAL[Content Validator]
    VAL --> |Validate Legal Document| GEMINI1[Gemini 2.5 Flash]
    
    %% Analyze Workflow Branch
    VAL --> |Accept| ANALYZER[Document Analyzer]
    VAL --> |Reject| REJ1[Rejection Response]
    ANALYZER --> |Analysis| GEMINI2[Gemini 2.5 Flash]
    GEMINI2 --> |Analysis Result| RESP1[Analyzer Response]
    REJ1 --> API
    RESP1 --> API
    
    %% Chat Workflow Branch  
    VAL --> |Accept for Chat| RAG[RAG Workflow]
    VAL --> |Reject for Chat| REJ2[Chat Rejection]
    
    %% RAG Processing Pipeline
    RAG --> SPLIT[Text Splitter]
    SPLIT --> |Chunks| EMB[OpenAI Embeddings]
    EMB --> |text-embedding-3-small| FAISS[(FAISS Vector Store)]
    
    %% Chat Processing
    RAG --> |User Query| RET[Document Retriever]
    RET --> |Retrieve| FAISS
    RET --> |Context + Query| GEMINI3[Gemini 2.5 Flash]
    GEMINI3 --> |Generated Response| CHAT_RESP[Chat Response]
    
    %% Session Management
    RAG --> MEM[Memory Saver]
    MEM --> |Session State| LANG[LangGraph State]
    
    %% Workflow Orchestration
    LANG_WF[LangGraph Workflow] --> AW
    LANG_WF --> CW
    LANG_CHAIN[LangChain] --> RAG
    
    %% Response Flow
    CHAT_RESP --> API
    REJ2 --> API
    API --> |JSON Response| FE
    
    %% Styling
    classDef frontend fill:#e1f5fe
    classDef api fill:#f3e5f5
    classDef workflow fill:#e8f5e8
    classDef ai fill:#fff3e0
    classDef storage fill:#fce4ec
    classDef processing fill:#f1f8e9
    
    class FE,FB frontend
    class API api
    class AW,CW,RAG,LANG_WF,LANG_CHAIN workflow
    class GEMINI1,GEMINI2,GEMINI3,EMB ai
    class FAISS,MEM storage
    class DP,VAL,ANALYZER,SPLIT,RET processing
```

## Detailed Flow Description

### 1. **Frontend Layer (React + Firebase)**
- React frontend handles file uploads and user interactions
- Firebase database stores application data
- Communicates with FastAPI backend via REST APIs

### 2. **API Layer (FastAPI)**
- **Main Endpoints:**
  - `/analyze-document` - Document analysis workflow
  - `/chat` - Conversational chat with documents
- **CORS Configuration** for frontend communication
- **Error Handling** and response formatting

### 3. **Document Processing Pipeline**
- **Document Processor** extracts text from PDF/DOCX files
- **Content Validator** uses Gemini 2.5 Flash to determine if document is legal-related
- **Validation Decision Points:**
  - Accept → Continue to next stage
  - Reject → Return rejection response with reason

### 4. **Analyze Workflow (LangGraph)**
- **Sequential Processing:**
  1. Text Extraction
  2. Document Validation
  3. Document Analysis (if accepted)
  4. Response Generation
- **Document Analyzer** uses Gemini 2.5 Flash for comprehensive analysis
- **Structured Output:** Document type, summary, important clauses

### 5. **Chat Workflow (RAG + LangGraph)**
- **Document Processing:**
  1. Text extraction and validation
  2. Text chunking using RecursiveCharacterTextSplitter
  3. Embedding generation using OpenAI's text-embedding-3-small
  4. Vector storage in FAISS database
- **Chat Processing:**
  1. Query processing with document retrieval
  2. Context-aware response generation using Gemini 2.5 Flash
  3. Session management with LangGraph checkpointing

### 6. **AI Models & Tools**
- **Gemini 2.5 Flash** - Primary LLM for validation, analysis, and chat
- **OpenAI Embeddings** - Vector embeddings for document chunks
- **FAISS** - Vector database for similarity search
- **LangChain** - Framework for LLM applications
- **LangGraph** - Workflow orchestration and state management

### 7. **Key Features**
- **Conditional Routing** based on validation results
- **Session Management** for conversational continuity
- **Memory Persistence** using LangGraph's MemorySaver
- **Error Handling** at each workflow stage
- **Structured Responses** using Pydantic models

## Technology Stack Summary

| Component | Technology |
|-----------|------------|
| Frontend | React |
| Database | Firebase |
| Backend API | FastAPI |
| Workflow Engine | LangGraph |
| LLM Framework | LangChain |
| Primary LLM | Gemini 2.5 Flash |
| Embeddings | OpenAI text-embedding-3-small |
| Vector Store | FAISS |
| Document Processing | PDF/DOCX extraction |
| Session Management | LangGraph MemorySaver |