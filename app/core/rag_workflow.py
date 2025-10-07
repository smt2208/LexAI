import uuid
import asyncio
import secrets
import string
from datetime import datetime
from typing import Dict, List, Optional, TypedDict, Annotated
from langchain_openai import OpenAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from fastapi import UploadFile, HTTPException
from app.logging_config import logger

from app.utils.doc_process import DocumentProcessor
from app.core.validator import ContentValidator
from app.models import ChatResponse, ValidatorResponse
from app.config import settings


class RAGState(TypedDict):
    """State for RAG workflow."""
    document_content: str
    validation_result: Optional[ValidatorResponse]
    vector_store_id: Optional[str]
    messages: List[Dict[str, str]]
    user_message: str
    response: str
    session_id: str
    document_processed: bool


class RAGWorkflow:
    """RAG workflow for conversational document chat."""

    def __init__(self):
        """Initialize RAG workflow with necessary components."""
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=settings.OPENAI_API_KEY)
        self.llm = ChatGoogleGenerativeAI(
            model=settings.MODEL_NAME,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.7
        )
        self.document_processor = DocumentProcessor()
        self.validator = ContentValidator()
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        self.vector_stores: Dict[str, FAISS] = {}
        self.workflow = self._build_workflow()
        self.memory = MemorySaver()
        self.app = self.workflow.compile(checkpointer=self.memory)

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow with conditional routing."""
        workflow = StateGraph(RAGState)
        workflow.add_node("route_initial", self._route_initial)
        workflow.add_node("validate_document", self._validate_document)
        workflow.add_node("process_document", self._process_document)
        workflow.add_node("answer_question", self._answer_question)
        workflow.add_node("handle_rejection", self._handle_rejection)

        workflow.set_entry_point("route_initial")

        workflow.add_conditional_edges(
            "route_initial",
            self._route_decision,
            {"validate": "validate_document", "answer": "answer_question"}
        )
        
        workflow.add_conditional_edges(
            "validate_document",
            self._should_process_document,
            {"process": "process_document", "reject": "handle_rejection"}
        )
        workflow.add_edge("process_document", "answer_question")
        workflow.add_edge("answer_question", END)
        workflow.add_edge("handle_rejection", END)
        
        return workflow

    def _generate_session_id(self) -> str:
        """Generate a unique session ID using cryptographically secure random string."""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(32))

    def _route_initial(self, state: RAGState) -> RAGState:
        """Route the initial request based on document presence."""
        return state

    def _route_decision(self, state: RAGState) -> str:
        """Decide the initial routing based on document content and processing status."""
        has_content = state.get("document_content")
        already_processed = state.get("document_processed", False)
        
        if has_content and not already_processed:
            return "validate"
        else:
            return "answer"

    async def _validate_document(self, state: RAGState) -> RAGState:
        """Validate if the document is legal-related."""
        if not state.get("document_content"):
            state["validation_result"] = ValidatorResponse(decision="reject")
            return state
        
        try:
            validation_result = await self.validator.is_legal_document(state["document_content"])
            state["validation_result"] = validation_result
        except Exception as e:
            logger.error(f"Error in document validation: {e}")
            state["validation_result"] = ValidatorResponse(decision="reject")
        return state

    def _should_process_document(self, state: RAGState) -> str:
        """Decide whether to process the document or reject."""
        return "process" if state["validation_result"].decision == "accept" else "reject"

    async def _process_document(self, state: RAGState) -> RAGState:
        """Process the document and create a vector store."""
        try:
            docs = [Document(page_content=state["document_content"])]
            chunks = self.text_splitter.split_documents(docs)
            
            vector_store = FAISS.from_documents(chunks, self.embeddings)
            
            session_id = state["session_id"]
            self.vector_stores[session_id] = vector_store
            state["vector_store_id"] = session_id
            state["document_processed"] = True
            logger.info(f"Document processed into {len(chunks)} chunks for session {session_id}")
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            state["response"] = "Error processing document. Please try again."
        return state

    async def _answer_question(self, state: RAGState) -> RAGState:
        """Answer user questions using RAG."""
        try:
            session_id = state["session_id"]
            vector_store = self.vector_stores.get(session_id)

            if not vector_store:
                state["response"] = "No document has been processed for this session."
                return state

            retriever = vector_store.as_retriever(search_kwargs={"k": 3})
            docs = await asyncio.get_event_loop().run_in_executor(None, retriever.invoke, state["user_message"])
            context = "\n\n".join([doc.page_content for doc in docs])

            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a specialized legal document assistant designed to help users understand legal documents and answer legal-related questions only.

IMPORTANT GUIDELINES:
1. ONLY respond to questions about:
   - Legal document content, clauses, and terms
   - Legal concepts, definitions, and explanations
   - Document analysis, interpretation, and implications
   - Legal rights, obligations, and responsibilities mentioned in documents
   - Contractual terms, conditions, and legal language clarification

2. POLITELY DECLINE non-legal questions such as:
   - General conversation, greetings, or small talk
   - Technical support or software questions
   - Personal advice unrelated to legal documents
   - Questions about other topics (science, history, entertainment, etc.)
   - Requests to perform non-legal tasks

3. When declining non-legal questions, respond with:
   "I'm a specialized legal document assistant and can only help with questions related to legal documents, contracts, and legal concepts. Please ask me about the legal document you've uploaded or other legal matters."

4. Base your legal responses on:
   - The document context provided below
   - General legal knowledge when relevant
   - Clear, simple explanations for complex legal terms

5. Always provide helpful, accurate legal information while encouraging users to consult qualified legal professionals for specific legal advice.

Document Context: {context}"""),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{question}")
            ])
            
            chat_history = [HumanMessage(content=msg["content"]) if msg["role"] == "user" else AIMessage(content=msg["content"]) for msg in state["messages"]]
            
            chain = prompt | self.llm
            response = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: chain.invoke({
                    "context": context, 
                    "question": state["user_message"], 
                    "chat_history": chat_history
                })
            )
            
            state["response"] = response.content
            state["messages"].extend([
                {"role": "user", "content": state["user_message"]},
                {"role": "assistant", "content": response.content}
            ])
        except Exception as e:
            state["response"] = "I encountered an error while processing your legal query. Please try again."
        return state

    def _handle_rejection(self, state: RAGState) -> RAGState:
        """Handle the rejection of a document."""
        state["response"] = "I can only help with legal documents. Please upload a valid document."
        state["document_processed"] = False
        return state

    async def chat(self, message: str, session_id: str, file: Optional[UploadFile] = None) -> ChatResponse:
        """Handle both initial and follow-up chat messages."""
        config = {"configurable": {"thread_id": session_id}}
        
        try:
            current_state = self.memory.get(config)
            messages = current_state.values.get("messages", []) if current_state else []
            document_processed = current_state.values.get("document_processed", False) if current_state else False
        except Exception:
            messages = []
            document_processed = False

        initial_state: RAGState = {
            "document_content": "",
            "user_message": message,
            "session_id": session_id,
            "messages": messages,
            "document_processed": document_processed,
        }

        if file and not document_processed:
            initial_state["document_content"] = await self.document_processor.extract_text(file)
            initial_state["document_processed"] = False
        elif file and document_processed:
            logger.info(f"File provided for session {session_id} but document already processed, ignoring file")
            initial_state["document_content"] = ""

        try:
            result = await self.app.ainvoke(initial_state, config=config)
            return ChatResponse(
                response=result["response"],
                session_id=session_id,
                document_processed=result.get("document_processed", False)
            )
        except Exception as e:
            logger.error(f"Error in chat workflow: {e}")
            raise HTTPException(status_code=500, detail=f"Error during chat: {str(e)}")