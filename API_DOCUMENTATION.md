# API Documentation

Complete API reference for the Legal Document Analyzer & RAG Chatbot application.

## Base URL

```
Development: http://localhost:8000
Production: https://your-domain.com
```

## Authentication

No authentication required for current version. All endpoints are publicly accessible.

## Content Types

- **Request**: `multipart/form-data` (for file uploads)
- **Response**: `application/json`

---

## Endpoints

### 1. Root Information

**GET** `/`

Get basic API information and available endpoints.

#### Request
```bash
curl -X GET "http://localhost:8000/"
```

#### Response
```json
{
  "message": "Welcome to Legal Document Analyzer",
  "version": "1.0.0",
  "description": "Legal document analyzer",
  "endpoints": {
    "analyze": "/analyze-document",
    "chat": "/chat",
    "continue-chat": "/chat/continue",
    "health": "/health"
  }
}
```

---

### 2. Health Check

**GET** `/health`

Check service health status and basic information.

#### Request
```bash
curl -X GET "http://localhost:8000/health"
```

#### Response
```json
{
  "status": "healthy",
  "service": "Legal Document Analyzer",
  "version": "1.0.0",
  "timestamp": 1726828800.123
}
```

---

### 3. Document Analysis

**POST** `/analyze-document`

Analyze legal documents and return structured analysis results.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | File | ✅ Yes | Legal document (PDF or DOCX, max 50MB) |

#### Request Examples

**cURL:**
```bash
curl -X POST "http://localhost:8000/analyze-document" \
     -F "file=@contract.pdf"
```

**JavaScript (React):**
```javascript
const formData = new FormData();
formData.append('file', selectedFile);

const response = await fetch('/analyze-document', {
  method: 'POST',
  body: formData
});

const result = await response.json();
```

**Python:**
```python
import requests

with open('contract.pdf', 'rb') as file:
    response = requests.post(
        'http://localhost:8000/analyze-document',
        files={'file': file}
    )
    
result = response.json()
```

#### Response Examples

**Accepted Document:**
```json
{
  "decision": "accept",
  "document_type": "Employment Contract",
  "summary": "This is a comprehensive employment contract between ABC Corporation and John Doe for the position of Software Engineer. The contract outlines salary, benefits, working conditions, confidentiality requirements, and termination procedures. Key terms include a base salary of $85,000, standard health benefits, and a 2-week notice period.",
  "important_clauses": [
    "Compensation: Annual salary of $85,000 with performance-based bonuses",
    "Confidentiality: Employee must maintain confidentiality of company information",
    "Termination: Either party may terminate with 2 weeks written notice",
    "Non-compete: 6-month non-compete period in same industry within 50 miles",
    "Benefits: Health insurance, dental, vision, and 401k matching"
  ]
}
```

**Rejected Document:**
```json
{
  "decision": "reject",
  "reason": "The uploaded document does not appear to be a legal document. It contains general business correspondence without legal clauses or formal structure."
}
```

#### Error Responses

**Invalid File Type (400):**
```json
{
  "error": "HTTP 400",
  "detail": "Only PDF and DOCX files are supported"
}
```

**File Too Large (413):**
```json
{
  "error": "HTTP 413",
  "detail": "File size exceeds maximum limit of 50MB"
}
```

**Processing Error (500):**
```json
{
  "error": "Internal Server Error",
  "detail": "An unexpected error occurred"
}
```

---

### 4. RAG Chat

**POST** `/chat`

Handle both new document uploads and chat conversations with documents.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `message` | String | ❌ Optional | User message (max 2000 chars). Leave empty for file-only uploads |
| `session_id` | String | ❌ Optional | Session ID for conversation continuity. Auto-generated if not provided |
| `file` | File | ❌ Optional | Document file (PDF or DOCX) to upload and process |

#### Use Cases

##### Case 1: File Upload Only (Silent Processing)
Upload a document without asking questions - prepares document for future queries.

**Request:**
```bash
curl -X POST "http://localhost:8000/chat" \
     -F "file=@contract.pdf"
```

**Response:**
```json
{
  "response": "",
  "session_id": "chat_20240920_abc123def456",
  "document_processed": true
}
```

##### Case 2: Chat with Existing Document
Ask questions about a previously uploaded document.

**Request:**
```bash
curl -X POST "http://localhost:8000/chat" \
     -F "message=What is the salary mentioned in this contract?" \
     -F "session_id=chat_20240920_abc123def456"
```

**Response:**
```json
{
  "response": "According to the employment contract, the annual salary is $85,000. Additionally, the contract mentions performance-based bonuses that could provide additional compensation based on meeting specific objectives.",
  "session_id": "chat_20240920_abc123def456",
  "document_processed": true
}
```

##### Case 3: Upload Document with Initial Question
Upload a document and ask a question in the same request.

**Request:**
```bash
curl -X POST "http://localhost:8000/chat" \
     -F "message=Can you summarize the key terms?" \
     -F "file=@contract.pdf"
```

**Response:**
```json
{
  "response": "Based on the employment contract you've uploaded, here are the key terms:\n\n1. **Position**: Software Engineer at ABC Corporation\n2. **Salary**: $85,000 annually with performance bonuses\n3. **Benefits**: Health, dental, vision insurance plus 401k matching\n4. **Notice Period**: 2 weeks required for termination\n5. **Non-compete**: 6-month restriction within 50 miles\n6. **Confidentiality**: Must maintain company information confidentiality\n\nThe contract appears to be standard for this type of role with competitive compensation and typical legal protections.",
  "session_id": "chat_20240920_abc123def456",
  "document_processed": true
}
```

#### Request Examples

**JavaScript (React) - File Upload Only:**
```javascript
// Silent document processing
const formData = new FormData();
formData.append('file', selectedFile);

const response = await fetch('/chat', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log('Session ID:', result.session_id); // Save for future queries
```

**JavaScript (React) - Chat with Document:**
```javascript
// Ask questions about uploaded document
const formData = new FormData();
formData.append('message', 'What are the termination conditions?');
formData.append('session_id', savedSessionId);

const response = await fetch('/chat', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log('AI Response:', result.response);
```

**Python - Complete Workflow:**
```python
import requests

# Step 1: Upload document silently
with open('contract.pdf', 'rb') as file:
    response = requests.post(
        'http://localhost:8000/chat',
        files={'file': file}
    )
    
session_data = response.json()
session_id = session_data['session_id']

# Step 2: Ask questions
chat_response = requests.post(
    'http://localhost:8000/chat',
    data={
        'message': 'What are the key obligations for the employee?',
        'session_id': session_id
    }
)

answer = chat_response.json()
print(f"AI: {answer['response']}")
```

#### Error Responses

**Missing Message and File (400):**
```json
{
  "error": "HTTP 400",
  "detail": "Message is required when no file is provided"
}
```

**Invalid File Type (400):**
```json
{
  "error": "HTTP 400",
  "detail": "Only PDF and DOCX files are supported"
}
```

**Empty Message (400):**
```json
{
  "error": "HTTP 400",
  "detail": "Message cannot be empty"
}
```

**Processing Error (500):**
```json
{
  "error": "Internal Server Error",
  "detail": "An unexpected error occurred"
}
```

---

## Response Models

### AnalyzerResponse
```json
{
  "decision": "accept",
  "document_type": "string",
  "summary": "string",
  "important_clauses": ["string", "string", "..."]
}
```

### RejectionResponse
```json
{
  "decision": "reject",
  "reason": "string"
}
```

### ChatResponse
```json
{
  "response": "string",
  "session_id": "string",
  "document_processed": boolean
}
```

### ErrorResponse
```json
{
  "error": "string",
  "detail": "string"
}
```

---

## Frontend Integration Guide

### React Implementation Example

```jsx
import React, { useState } from 'react';

function DocumentAnalyzer() {
  const [file, setFile] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [analysis, setAnalysis] = useState(null);

  // Analyze document
  const analyzeDocument = async () => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/analyze-document', {
        method: 'POST',
        body: formData
      });
      
      const result = await response.json();
      setAnalysis(result);
      
      // Automatically prepare for chat
      await initializeChat();
    } catch (error) {
      console.error('Analysis failed:', error);
    }
  };

  // Initialize chat session
  const initializeChat = async () => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/chat', {
        method: 'POST',
        body: formData
      });
      
      const result = await response.json();
      setSessionId(result.session_id);
    } catch (error) {
      console.error('Chat initialization failed:', error);
    }
  };

  // Send chat message
  const sendMessage = async (message) => {
    const formData = new FormData();
    formData.append('message', message);
    formData.append('session_id', sessionId);

    try {
      const response = await fetch('/chat', {
        method: 'POST',
        body: formData
      });
      
      const result = await response.json();
      setMessages(prev => [...prev, 
        { role: 'user', content: message },
        { role: 'assistant', content: result.response }
      ]);
    } catch (error) {
      console.error('Chat failed:', error);
    }
  };

  return (
    <div>
      {/* File upload and analysis UI */}
      <input 
        type="file" 
        onChange={(e) => setFile(e.target.files[0])}
        accept=".pdf,.docx"
      />
      <button onClick={analyzeDocument}>Analyze Document</button>
      
      {/* Analysis results */}
      {analysis && (
        <div>
          <h3>Analysis Results</h3>
          <p><strong>Type:</strong> {analysis.document_type}</p>
          <p><strong>Summary:</strong> {analysis.summary}</p>
          {/* ... display important clauses */}
        </div>
      )}
      
      {/* Chat interface */}
      {sessionId && (
        <div>
          <h3>Chat with Document</h3>
          {/* Chat messages display */}
          {/* Message input */}
        </div>
      )}
    </div>
  );
}
```

---

## Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 400 | Bad Request | Invalid input parameters |
| 413 | Payload Too Large | File size exceeds limit |
| 422 | Unprocessable Entity | Validation error |
| 500 | Internal Server Error | Server processing error |

---

## Rate Limits

Currently no rate limiting is implemented. For production use, consider implementing:
- **Per IP**: 100 requests per minute
- **Per Session**: 50 document uploads per hour
- **File Size**: Maximum 50MB per file

---

## Best Practices

### For Document Analysis
1. **File Preparation**: Ensure documents are text-readable (not scanned images)
2. **File Size**: Keep files under 10MB for optimal performance
3. **Error Handling**: Always check the `decision` field in responses

### For RAG Chat
1. **Session Management**: Store and reuse session IDs for conversations
2. **File Upload**: Upload documents before starting conversations
3. **Message Length**: Keep messages under 2000 characters
4. **Context**: Reference specific sections when asking questions

### Performance Tips
1. **Concurrent Requests**: Limit concurrent file uploads
2. **Timeout Handling**: Implement proper timeout handling (30s+ for large files)
3. **Error Recovery**: Implement retry logic for network failures
4. **Progress Indicators**: Show upload progress for large files

---

## Troubleshooting

### Common Issues

**File Upload Fails:**
- Check file format (PDF/DOCX only)
- Verify file size (< 50MB)
- Ensure file is not corrupted

**Analysis Returns "Reject":**
- Document may not be a legal document
- File might be scanned image (not searchable text)
- Content might be too short or unclear

**Chat Session Lost:**
- Session IDs expire after inactivity
- Re-upload document to create new session
- Check session_id format and validity

**Empty Responses:**
- File may not have extractable text
- Document processing might have failed
- Check application logs for details

### Error Handling Example

```javascript
async function handleDocumentUpload(file) {
  try {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch('/analyze-document', {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Upload failed');
    }
    
    const result = await response.json();
    
    if (result.decision === 'reject') {
      alert(`Document rejected: ${result.reason}`);
      return null;
    }
    
    return result;
    
  } catch (error) {
    console.error('Upload error:', error);
    alert('Failed to upload document. Please try again.');
    return null;
  }
}
```