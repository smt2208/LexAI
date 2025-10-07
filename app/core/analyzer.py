from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings
from app.models import AnalyzerResponse
from app.logging_config import logger
import asyncio

class DocumentAnalyzer:
    """Document analyzer using Gemini AI for legal document analysis."""
    
    def __init__(self):
        """Initialize the document analyzer with language model."""
        self.llm = ChatGoogleGenerativeAI(
            model=settings.MODEL_NAME,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=settings.TEMPERATURE,
            timeout=60,  # Longer timeout for analysis
            max_retries=2
        )
        self.structured_llm = self.llm.with_structured_output(AnalyzerResponse)

    async def analyze(self, document_text: str) -> AnalyzerResponse:
        """Analyze legal document using Gemini with structured output and timeout."""
        try:
            logger.info("Starting document analysis with Gemini")
            
            # Limit document size for analysis to prevent timeouts
            max_chars = 8000
            if len(document_text) > max_chars:
                logger.info(f"Document too long ({len(document_text)} chars), truncating to {max_chars}")
                document_text = document_text[:max_chars] + "\n\n[Document truncated for analysis]"
            
            prompt = f"""
            You are a legal document analyzer. Analyze this legal document and provide:

            1. Document Type: Specific type (e.g., "Rental Agreement", "Employment Contract", "NDA", "Privacy Policy", etc.)
            2. Summary: a detailed summary of the document in the language of the document.
            3. Important Clauses: List 3-5 important clauses from the document, each explained in simple terms.

            Document Text:
            {document_text}

            Provide your analysis in the specified format.
            """
            
            messages = [{"role": "user", "content": prompt}]
            
            # Add timeout to analysis
            result = await asyncio.wait_for(
                self.structured_llm.ainvoke(messages),
                timeout=90.0  # 90 second timeout for analysis
            )

            if result is not None:
                logger.info(f"Analysis completed for document type: {result.document_type}")
                return result
            
            else:
                logger.warning("Structured LLM returned None for analysis, using fallback")
                return AnalyzerResponse(
                    document_type="Unknown",
                    summary="Analysis could not be completed due to structured output failure.",
                    important_clauses=[
                        "No structured response received from analyzer",
                        "Please try uploading the document again",
                        "If issue persists, contact support"
                    ]
                )
            
        except asyncio.TimeoutError:
            logger.error("Document analysis timed out after 90 seconds")
            return AnalyzerResponse(
                document_type="Unknown",
                summary="Document analysis timed out. Please try with a smaller document.",
                important_clauses=[
                    "Analysis timed out due to document complexity or size",
                    "Try uploading a smaller document",
                    "Consider breaking large documents into sections"
                ]
            )
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            return AnalyzerResponse(
                document_type="Unknown",
                summary=f"Document analysis failed: {str(e)}. Please try again or consult a legal professional.",
                important_clauses=[
                    "Analysis encountered an error",
                    "Document may require manual review", 
                    "Consider consulting a legal professional"
                ]
            )