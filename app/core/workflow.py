from app.utils.doc_process import DocumentProcessor
from app.core.analyzer import DocumentAnalyzer
from app.core.validator import ContentValidator
from app.models import AnalyzerResponse, RejectionResponse
from app.config import settings
from langchain_google_genai import ChatGoogleGenerativeAI
from app.logging_config import logger
from fastapi import UploadFile
from typing import Union, TypedDict

from langgraph.graph import StateGraph, END, START

class DocumentState(TypedDict):
    """State object for document processing workflow."""
    file: UploadFile
    document_text: str
    validation_decision: str
    result: Union[AnalyzerResponse, RejectionResponse, None]
    error: str

class DocumentWorkflow:
    """LangGraph-powered document processing workflow."""

    def __init__(self):
        """Initialize document processing workflow."""
        self.processor = DocumentProcessor()
        self.validator = ContentValidator()
        self.analyzer = DocumentAnalyzer()
        self.llm = ChatGoogleGenerativeAI(
            model=settings.MODEL_NAME,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.1
        )
        self.rejection_llm = self.llm.with_structured_output(RejectionResponse)
        self.graph = self._build_workflow_graph()

    def _build_workflow_graph(self) -> StateGraph:
        """Build workflow with conditional routing."""
        workflow = StateGraph(DocumentState)

        workflow.add_node("extract_text", self._extract_text_node)
        workflow.add_node("validate_document", self._validate_document_node)
        workflow.add_node("analyze_document", self._analyze_document_node)
        workflow.add_node("generate_rejection", self._generate_rejection_node)

        workflow.add_edge(START, "extract_text")
        workflow.add_edge("extract_text", "validate_document")
        
        workflow.add_conditional_edges(
            "validate_document",
            self._route_after_validation,
            {
                "reject": "generate_rejection",
                "accept": "analyze_document"
            }
        )
        
        workflow.add_edge("generate_rejection", END)
        workflow.add_edge("analyze_document", END)

        return workflow.compile()

    async def _extract_text_node(self, state: DocumentState) -> DocumentState:
        """Extract text from the uploaded document."""
        try:
            logger.info("Extracting text from document")
            state["document_text"] = await self.processor.extract_text(state["file"])
            return state
        except Exception as e:
            logger.error(f"Text extraction failed: {str(e)}")
            state["error"] = f"Text extraction failed: {str(e)}"
            state["result"] = RejectionResponse(
                decision="reject",
                reason=f"Could not extract text from document: {str(e)}"
            )
            return state

    async def _validate_document_node(self, state: DocumentState) -> DocumentState:
        """Validate if the document is a legal document."""
        try:
            logger.info("Validating document content")
            validation_result = await self.validator.is_legal_document(state["document_text"])
            
            if validation_result is None or not hasattr(validation_result, 'decision'):
                logger.error("Validation failed - invalid result")
                state["result"] = RejectionResponse(
                    decision="reject",
                    reason="Document validation failed"
                )
            else:
                state["validation_decision"] = validation_result.decision
                
            return state
        except Exception as e:
            logger.error(f"Document validation failed: {str(e)}")
            state["result"] = RejectionResponse(
                decision="reject",
                reason=f"Validation failed: {str(e)}"
            )
            return state

    def _route_after_validation(self, state: DocumentState) -> str:
        """Route workflow based on validation result."""
        if state.get("result") is not None:
            return "reject"
        
        validation_decision = state.get("validation_decision", "reject")
        return "reject" if validation_decision == "reject" else "accept"

    async def _analyze_document_node(self, state: DocumentState) -> DocumentState:
        """Analyze the validated document."""
        try:
            logger.info("Document accepted, analyzing content")
            analysis_result = await self.analyzer.analyze(state["document_text"])
            state["result"] = analysis_result
            return state
        except Exception as e:
            logger.error(f"Document analysis failed: {str(e)}")
            state["result"] = RejectionResponse(
                decision="reject",
                reason=f"Analysis failed: {str(e)}"
            )
            return state

    async def _generate_rejection_node(self, state: DocumentState) -> DocumentState:
        """Generate rejection reason for rejected documents."""
        try:
            if state.get("result") is not None:
                return state
                
            logger.info("Document rejected, generating reason")
            rejection_result = await self._generate_rejection_reason(state["document_text"])
            state["result"] = rejection_result
            return state
        except Exception as e:
            logger.error(f"Rejection reason generation failed: {str(e)}")
            state["result"] = RejectionResponse(
                decision="reject",
                reason="Document was rejected during validation process"
            )
            return state

    async def _generate_rejection_reason(self, document_text: str) -> RejectionResponse:
        """Generate a structured rejection reason."""
        try:
            prompt = f"""
            A document was rejected during validation. Provide a clear reason why this document
            is not suitable for legal analysis.

            Document text (first 500 characters):
            {document_text[:500]}

            Provide a professional rejection reason.
            """

            rejection_result = await self.rejection_llm.ainvoke([{"role": "user", "content": prompt}])

            if rejection_result is None:
                return RejectionResponse(
                    decision="reject",
                    reason="This document was rejected because it does not appear to be a legal document."
                )

            return rejection_result

        except Exception as e:
            logger.error(f"Rejection reason generation failed: {str(e)}")
            return RejectionResponse(
                decision="reject",
                reason="Document was rejected during validation process"
            )

    async def process_document(self, file: UploadFile) -> Union[AnalyzerResponse, RejectionResponse]:
        """Process document using workflow with conditional routing."""
        initial_state = {
            "file": file,
            "document_text": "",
            "validation_decision": "",
            "result": None,
            "error": None,
        }
        final_state = await self.graph.ainvoke(initial_state)
        return final_state["result"]