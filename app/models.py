from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class ValidatorResponse(BaseModel):
    """
    Response model from document validator component.
    Contains the validation decision for uploaded documents.
    """
    decision: Literal["accept", "reject"] = Field(..., description="Decision to accept or reject the document either 'accept' or 'reject'")


class AnalyzerResponse(BaseModel):
    """
    Response model from document analyzer component.
    Contains comprehensive analysis results for accepted documents.
    """
    decision: str = Field("accept", description="Decision status of the document")
    document_type: str = Field(..., description="Type of legal document")
    summary: str = Field(..., description="detailed summary of the document")
    important_clauses: List[str] = Field(..., description="3-5 important clauses explained in simple terms")


class RejectionResponse(BaseModel):
    """
    Response model for rejected documents.
    Provides rejection decision and reasoning.
    """
    decision: str = Field("reject", description="Rejection decision")
    reason: str = Field(..., description="Cause for rejection")


class ErrorResponse(BaseModel):
    """
    Standard error response model for API endpoints.
    Provides error message and optional detailed information.
    """
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")


class ChatMessage(BaseModel):
    """
    Individual chat message model for conversation history.
    Represents a single message exchange between user and assistant.
    """
    role: Literal["user", "assistant"] = Field(..., description="Role of the message sender")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """
    Request model for RAG-based document chat.
    Allows users to query documents with optional session continuity.
    """
    message: str = Field(..., description="User message to chat with the document")
    session_id: Optional[str] = Field(None, description="Optional session ID for conversation continuity")


class ChatResponse(BaseModel):
    """
    Response model for RAG-based document chat.
    Contains assistant response with session tracking information.
    """
    response: str = Field(..., description="Assistant response")
    session_id: str = Field(..., description="Session ID for conversation tracking")
    document_processed: bool = Field(False, description="Whether a document was processed in this session")


class DocumentChatRequest(BaseModel):
    """
    Request model for initiating new document chat sessions.
    Provides default welcome message for document interactions.
    """
    message: Optional[str] = Field("Hello! I've uploaded a document. Can you help me understand it?", description="Initial message after document upload")