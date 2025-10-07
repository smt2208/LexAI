from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings
from app.models import ValidatorResponse
from app.logging_config import logger
import asyncio

class ContentValidator:
    """Validator to check if document content is related to legal domain."""
    
    def __init__(self):
        """Initialize the content validator with language model."""
        self.llm = ChatGoogleGenerativeAI(
            model=settings.MODEL_NAME,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.1,
            timeout=30,  # Add timeout for API calls
            max_retries=2  # Add retry logic
        )
        self.structured_llm = self.llm.with_structured_output(ValidatorResponse)
    
    async def is_legal_document(self, text: str) -> ValidatorResponse:
        """Check if the document content is legal-related using structured output with timeout."""
        try:
            if len(text.strip()) < 100:
                logger.info("Document too short, rejecting")
                return ValidatorResponse(decision="reject")
            
            sample_text = text[:1500] if len(text) > 1500 else text
            
            prompt = f"""
            You are a legal document classifier. Analyze the following document and determine if it is a legal document.

            LEGAL DOCUMENTS include: contracts, agreements, terms of service, privacy policies,
            legal notices, leases, employment agreements, NDAs, loan documents, insurance policies,
            court documents, legal forms, wills, patents, licenses, legal briefs, motions.

            NON-LEGAL DOCUMENTS include: stories, novels, recipes, manuals, emails, reports,
            technical documentation, news articles, blogs, personal letters, fiction, academic papers.

            Document text to analyze:
            {sample_text}

            Based on the content above, classify this document.
            """
            
            messages = [{"role": "user", "content": prompt}]
            
            # Add timeout to AI call
            result = await asyncio.wait_for(
                self.structured_llm.ainvoke(messages),
                timeout=45.0  # 45 second timeout for validation
            )
            
            if result is not None and hasattr(result, 'decision'):
                logger.info(f"Validation result: {result.decision}")
                return result
            else:
                logger.warning("Structured LLM returned None or invalid result, defaulting to reject")
                return ValidatorResponse(decision="reject")
            
        except asyncio.TimeoutError:
            logger.error("Document validation timed out after 45 seconds")
            return ValidatorResponse(decision="reject")
        except Exception as e:
            logger.error(f"Error in document validation: {str(e)}")
            return ValidatorResponse(decision="reject")