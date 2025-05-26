from enum import Enum
from typing import Dict, List, Any, Optional
import google.generativeai as genai
from PyPDF2 import PdfReader
import pytesseract
from PIL import Image
import io
import os
from fastapi import UploadFile
import tempfile
from pathlib import Path
import json
import asyncio

# Set Tesseract path for Windows
if os.name == 'nt':
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class DocumentType(str, Enum):
    BILL = "bill"
    DISCHARGE = "discharge"
    UNKNOWN = "unknown"

class BaseAgent:
    def __init__(self, api_key: str):
        """Initialize the Gemini agent with API key."""
        self.api_key = api_key
        try:
            # Configure the Gemini API
            genai.configure(api_key=self.api_key)
            # Initialize the model
            self.model = genai.GenerativeModel('gemini-pro')
            # Test the API key with a simple generation
            self._test_api_key()
        except Exception as e:
            raise ValueError(f"Failed to initialize Gemini API: {str(e)}")

    def _test_api_key(self) -> None:
        """Test if the API key is valid by making a simple request."""
        try:
            response = self.model.generate_content("Hello")
            if not response:
                raise ValueError("No response from Gemini API")
        except Exception as e:
            raise ValueError(f"Invalid API key or API error: {str(e)}")

    async def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from a PDF file."""
        try:
            with open(file_path, 'rb') as file:
                # Check if file is a valid PDF
                header = file.read(4)
                if header != b'%PDF':
                    return "Empty document"
                
                # Read the content for processing
                content = file.read().decode('utf-8', errors='ignore')
                if not content.strip():
                    return "Empty document"
                
                return content
        except Exception as e:
            print(f"Error extracting text from PDF: {str(e)}")
            return "Empty document"

    async def classify_document(self, text: str) -> str:
        """Classify the document type."""
        prompt = f"""
        Analyze the following medical document text and classify it as either 'bill' or 'discharge':
        
        Text: {text[:1000]}  # Using first 1000 chars for classification
        
        Return ONLY 'bill' or 'discharge' as response.
        """
        
        try:
            response = await self._generate_content_with_retry(prompt)
            doc_type = response.strip().lower()
            if doc_type in ['bill', 'discharge']:
                return doc_type
            return 'unknown'
        except Exception as e:
            print(f"Error classifying document: {str(e)}")
            return 'unknown'

    async def extract_info(self, text: str, doc_type: DocumentType) -> Dict[str, Any]:
        """Extract relevant information based on document type."""
        prompt = f"""
        Extract key information from this {doc_type.value} document.
        
        Text: {text[:2000]}  # Using first 2000 chars for extraction
        
        Return the information in JSON format with these fields:
        For bills:
        - total_amount
        - service_date
        - provider_name
        
        For discharge summaries:
        - discharge_date
        - diagnosis
        - treatment_plan
        """
        
        try:
            response = await self._generate_content_with_retry(prompt)
            # Clean up response to ensure it's valid JSON
            json_str = response
            if json_str.startswith('```json'):
                json_str = json_str[7:-3]
            return json.loads(json_str)
        except Exception as e:
            print(f"Error extracting information: {str(e)}")
            return {"error": str(e)}

    async def validate_documents(self, bill_text: str, discharge_text: str) -> Dict[str, Any]:
        """Validate consistency between bill and discharge documents."""
        if not bill_text or not discharge_text:
            return {
                "is_valid": False,
                "discrepancies": ["Missing required documents"],
                "validation_details": {
                    "patient_name_match": False,
                    "hospital_match": False,
                    "dates_consistent": False
                }
            }

        prompt = f"""
        Compare these medical documents for consistency:
        
        BILL:
        {bill_text[:1000]}
        
        DISCHARGE:
        {discharge_text[:1000]}
        
        Check for:
        1. Patient name matches
        2. Hospital/provider matches
        3. Dates are consistent
        
        Return JSON with:
        - is_valid (boolean)
        - discrepancies (list of strings)
        - validation_details (object with patient_name_match, hospital_match, dates_consistent)
        """
        
        try:
            response = await self._generate_content_with_retry(prompt)
            if response.startswith('```json'):
                response = response[7:-3]
            
            result = json.loads(response)
            return result
        except Exception as e:
            return {
                "is_valid": False,
                "discrepancies": [f"Validation error: {str(e)}"],
                "validation_details": {
                    "patient_name_match": False,
                    "hospital_match": False,
                    "dates_consistent": False
                }
            }

    async def _generate_content_with_retry(self, prompt: str, max_retries: int = 3) -> str:
        """Generate content with retry logic."""
        last_error = None
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                return response.text
            except Exception as e:
                last_error = e
                if attempt == max_retries - 1:
                    raise Exception(f"Failed after {max_retries} attempts: {str(e)}")
        raise last_error

async def process_documents(files: List[UploadFile]) -> Dict[str, Any]:
    """Process multiple medical documents and return extracted information."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise Exception("Google API key not configured")

    agent = BaseAgent(api_key)
    results = []
    bill_text = None
    discharge_text = None
    
    # Create temporary directory for file processing
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Process each file
            for file in files:
                temp_file = Path(temp_dir) / file.filename
                
                # Save uploaded file
                with open(temp_file, "wb") as buffer:
                    content = await file.read()
                    buffer.write(content)
                
                # Extract text from PDF
                text_content = await agent.extract_text_from_pdf(str(temp_file))
                
                # Classify and extract information
                doc_type = await agent.classify_document(text_content)
                doc_info = await agent.extract_info(text_content, DocumentType(doc_type))
                
                # Store text content for validation
                if doc_type == "bill":
                    bill_text = text_content
                elif doc_type == "discharge":
                    discharge_text = text_content
                
                results.append({
                    "type": doc_type,
                    "filename": file.filename,
                    "data": doc_info
                })
            
            # Validate documents if we have both types
            validation = await agent.validate_documents(
                bill_text or "", 
                discharge_text or ""
            )
            
            return {
                "documents": results,
                "validation": validation
            }
            
        except Exception as e:
            raise Exception(f"Failed to process documents: {str(e)}")