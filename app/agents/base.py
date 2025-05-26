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

# Set Tesseract path for Windows
if os.name == 'nt':
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class DocumentType(str, Enum):
    BILL = "bill"
    DISCHARGE = "discharge"
    UNKNOWN = "unknown"

class BaseAgent:
    def __init__(self, api_key: str):
        """Initialize the agent with Google API key."""
        if not api_key:
            raise ValueError("API key is required")
        
        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
    
    async def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF using PyPDF2 and OCR if needed."""
        try:
            with open(file_path, 'rb') as file:
                reader = PdfReader(file)
                text = ""
                
                for page in reader.pages:
                    # Try extracting text directly
                    page_text = page.extract_text()
                    
                    # If no text found, try OCR
                    if not page_text.strip():
                        if '/XObject' in page['/Resources']:
                            for obj in page['/Resources']['/XObject'].get_object().values():
                                if obj['/Subtype'] == '/Image':
                                    image = Image.open(io.BytesIO(obj.get_data()))
                                    page_text = pytesseract.image_to_string(image)
                    
                    text += page_text + "\n"
                
                return text.strip()
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")
    
    async def classify_document(self, text: str) -> str:
        """Classify document type based on content."""
        prompt = f"""
        Analyze this medical document and classify it as either a medical bill or discharge summary.
        Return only one word: 'bill' or 'discharge'.

        Document text:
        {text}
        """
        
        response = await self.model.generate_content_async(prompt)
        return response.text.strip().lower()

    async def extract_info(self, text: str, doc_type: DocumentType) -> dict:
        """Extract relevant information based on document type."""
        if doc_type == DocumentType.BILL:
            prompt = f"""Extract the following information from this medical bill and return ONLY a JSON object with these exact keys:
- "Patient Name"
- "Hospital"
- "Total Amount" (as a number)
- "Date of Service"

Medical bill text:
{text}
"""
        else:
            prompt = f"""Extract the following information from this discharge summary and return ONLY a JSON object with these exact keys:
- "Patient Name"
- "Hospital"
- "Admission Date"
- "Discharge Date"
- "Diagnosis"
- "Treatment Summary"

Discharge summary text:
{text}
"""
        
        try:
            text_response = await self._generate_content_with_retry(prompt)
            if text_response.startswith('```json'):
                text_response = text_response[7:-3]  # Remove ```json and ```
            elif text_response.startswith('{'):
                text_response = text_response
            else:
                return {}
                
            result = json.loads(text_response)
            # Ensure all keys are present
            if doc_type == DocumentType.BILL:
                required_keys = ["Patient Name", "Hospital", "Total Amount", "Date of Service"]
            else:
                required_keys = ["Patient Name", "Hospital", "Admission Date", "Discharge Date", "Diagnosis", "Treatment Summary"]
                
            # Add missing keys with None values
            for key in required_keys:
                if key not in result:
                    result[key] = None
                    
            return result
        except Exception as e:
            return {}

    async def validate_documents(self, bill_text: str, discharge_text: str) -> dict:
        """Validate consistency between bill and discharge documents."""
        if not bill_text or not discharge_text:
            return {
                "is_valid": False,
                "discrepancies": ["Missing required documents"],
                "validation_details": {}
            }
            
        prompt = f"""Compare these medical documents and check for consistency.
Return ONLY a JSON object with these exact keys:
- "is_valid": boolean
- "discrepancies": list of strings describing any inconsistencies
- "validation_details": dictionary with validation checks

Bill text:
{bill_text}

Discharge text:
{discharge_text}
"""
        try:
            text_response = await self._generate_content_with_retry(prompt)
            if text_response.startswith('```json'):
                text_response = text_response[7:-3]
            elif text_response.startswith('{'):
                text_response = text_response
            else:
                return {
                    "is_valid": False,
                    "discrepancies": ["Error processing validation"],
                    "validation_details": {}
                }
                
            return json.loads(text_response)
        except Exception:
            return {
                "is_valid": False,
                "discrepancies": ["Error processing validation"],
                "validation_details": {}
            }

async def process_documents(files: List[UploadFile]) -> Dict[str, Any]:
    """Process multiple medical documents and return extracted information."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise Exception("Google API key not configured")

    agent = BaseAgent(api_key)
    results = []
    
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
                doc_info = await agent.extract_info(text_content, doc_type)
                
                results.append({
                    "type": doc_type,
                    "filename": file.filename,
                    "data": doc_info
                })
            
            # Validate documents
            validation = await agent.validate_documents(results)
            
            return {
                "documents": results,
                "validation": validation
            }
            
        except Exception as e:
            raise Exception(f"Failed to process documents: {str(e)}")