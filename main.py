from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.models import AnalyzerResponse, RejectionResponse, ErrorResponse, ChatRequest, ChatResponse, DocumentChatRequest
from app.core.workflow import DocumentWorkflow
from app.core.rag_workflow import RAGWorkflow
from app.logging_config import logger
from typing import Union, Optional
import sys
import time

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="LangGraph-powered legal document analyzer",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)

allowed_origins = ["*"] if settings.DEBUG else [
    "http://localhost:3000",
    "http://localhost:3001", 
    "https://yourdomain.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    max_age=600,
)

workflow = DocumentWorkflow()
rag_workflow = RAGWorkflow()

@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "description": "Legal document analyzer",
        "endpoints": {
            "analyze": "/analyze-document",
            "chat": "/chat",
            "continue-chat": "/chat/continue",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": time.time()
    }

@app.post("/analyze-document")
async def analyze_document(
    file: UploadFile = File(..., description="Legal document (PDF or DOCX)")
):
    try:
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="File must have a name"
            )
        
        allowed_extensions = ['.pdf', '.docx']
        filename_lower = file.filename.lower()
        if not any(filename_lower.endswith(ext) for ext in allowed_extensions):
            raise HTTPException(
                status_code=400,
                detail="Only PDF and DOCX files are supported"
            )
        
        result = await workflow.process_document(file)

        if result is None:
            raise HTTPException(status_code=500, detail="Document processing failed")

        if isinstance(result, RejectionResponse):
            return JSONResponse(
                status_code=200,
                content={"decision": result.decision,
                         "reason": result.reason}
            )
        elif isinstance(result, AnalyzerResponse):
            return JSONResponse(
                status_code=200,
                content={"decision": result.decision,
                    "document_type": result.document_type,
                    "summary": result.summary,
                    "important_clauses": result.important_clauses
                }
            )
        else:
            raise HTTPException(status_code=500, detail="Unexpected response format")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

@app.post("/chat", response_model=ChatResponse)
async def chat_with_document(
    message: Optional[str] = Form(None, max_length=2000, description="Optional message to chat with the document. Leave empty when only uploading a file."),
    session_id: Optional[str] = Form(None, description="Optional session ID for conversation continuity. Auto-generated if not provided."),
    file: Optional[UploadFile] = File(None, description="Optional document file (PDF or DOCX) to upload and process."),
):
    try:
        if file and file.filename:
            allowed_extensions = ['.pdf', '.docx']
            filename_lower = file.filename.lower()
            if not any(filename_lower.endswith(ext) for ext in allowed_extensions):
                raise HTTPException(
                    status_code=400,
                    detail="Only PDF and DOCX files are supported"
                )
        
        if not session_id or session_id == "string":
            session_id = rag_workflow._generate_session_id()
        
        if not message or not message.strip():
            if file and file.filename:
                try:
                    config = {"configurable": {"thread_id": session_id}}
                    document_content = await rag_workflow.document_processor.extract_text(file)
                    
                    initial_state = {
                        "document_content": document_content,
                        "user_message": "",
                        "session_id": session_id,
                        "messages": [],
                        "document_processed": False,
                    }
                    
                    await rag_workflow.app.ainvoke(initial_state, config=config)
                    
                    return ChatResponse(
                        response="",
                        session_id=session_id,
                        document_processed=True
                    )
                except Exception as e:
                    raise HTTPException(status_code=500, detail="Failed to process document")
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Message is required when no file is provided"
                )
        
        if not message.strip():
            raise HTTPException(
                status_code=400,
                detail="Message cannot be empty"
            )
        
        result = await rag_workflow.chat(
            message=message.strip(),
            session_id=session_id,
            file=file
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": f"HTTP {exc.status_code}", "detail": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "detail": "An unexpected error occurred"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )