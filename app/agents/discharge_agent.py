from typing import Dict, Any
from pathlib import Path
from .base import BaseAgent
from datetime import datetime

class DischargeAgent(BaseAgent):
    """Agent for processing discharge summaries."""
    
    EXTRACTION_PROMPT = """
    Extract the following information from this discharge summary:
    - Patient Name: Full name as written
    - Diagnosis: Primary diagnosis or condition
    - Admission Date: When the patient was admitted
    - Discharge Date: When the patient was released

    Format the response as a JSON object with these exact field names:
    {
        "patient_name": "string",
        "diagnosis": "string",
        "admission_date": "YYYY-MM-DD",
        "discharge_date": "YYYY-MM-DD"
    }
    Return only the JSON object, no additional text.
    """
    
    VALIDATION_PROMPT = """
    Validate the following discharge summary information:
    
    Check for:
    1. Patient name is complete (first and last name)
    2. Diagnosis is specific and valid
    3. Admission date is before discharge date
    4. Dates are valid and not in the future
    
    Return a JSON object with:
    {
        "is_valid": boolean,
        "errors": [list of error messages],
        "warnings": [list of warning messages]
    }
    """
    
    async def process_document(self, file_path: str) -> Dict[str, Any]:
        """Process a discharge summary and extract relevant information."""
        try:
            # Convert file path to Path object
            path = Path(file_path)
            
            # Extract text from the discharge summary
            extracted_data = await self._extract_text_from_image(
                path,
                self.EXTRACTION_PROMPT
            )
            
            if "error" in extracted_data:
                return self._format_error(extracted_data["error"])
            
            # Parse and validate the extracted data
            processed_data = self._parse_extracted_data(extracted_data)
            validation_result = await self.validate_extracted_data(processed_data)
            
            if not validation_result.get("is_valid", False):
                return self._format_error(
                    f"Validation failed: {', '.join(validation_result.get('errors', []))}"
                )
            
            return self._format_success(processed_data)
            
        except Exception as e:
            return self._format_error(f"Failed to process discharge summary: {str(e)}")
    
    async def validate_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the extracted discharge summary data."""
        # First, perform basic validation
        validation_errors = []
        
        # Validate dates
        try:
            admission_date = datetime.strptime(data["admission_date"], "%Y-%m-%d").date()
            discharge_date = datetime.strptime(data["discharge_date"], "%Y-%m-%d").date()
            
            if admission_date > discharge_date:
                validation_errors.append("Admission date is after discharge date")
                
            if not self._validate_dates(admission_date, discharge_date):
                validation_errors.append("Invalid dates detected")
                
        except ValueError:
            validation_errors.append("Invalid date format")
        
        # Validate patient name
        if not self._validate_patient_name(data.get("patient_name", "")):
            validation_errors.append("Invalid patient name format")
        
        # If basic validation fails, return immediately
        if validation_errors:
            return {
                "is_valid": False,
                "errors": validation_errors,
                "warnings": []
            }
        
        # Perform LLM validation for more complex checks
        return await self._validate_with_llm(data, self.VALIDATION_PROMPT)
    
    def _parse_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and normalize the extracted data."""
        try:
            # Parse dates
            admission_date = datetime.strptime(
                data["admission_date"],
                "%Y-%m-%d"
            ).date()
            
            discharge_date = datetime.strptime(
                data["discharge_date"],
                "%Y-%m-%d"
            ).date()
            
            return {
                "type": "discharge_summary",
                "patient_name": data["patient_name"].strip(),
                "diagnosis": data["diagnosis"].strip(),
                "admission_date": admission_date.isoformat(),
                "discharge_date": discharge_date.isoformat()
            }
            
        except (KeyError, ValueError, TypeError) as e:
            raise ValueError(f"Failed to parse extracted data: {str(e)}")
    
    @staticmethod
    def _validate_patient_name(name: str) -> bool:
        """Validate that the patient name is complete."""
        # Check if name has at least two parts (first and last name)
        parts = name.strip().split()
        return len(parts) >= 2 and all(len(part) >= 2 for part in parts)
    
    @staticmethod
    def _validate_dates(admission_date: datetime, discharge_date: datetime) -> bool:
        """Validate admission and discharge dates."""
        today = datetime.now().date()
        return (
            admission_date <= today and
            discharge_date <= today and
            admission_date <= discharge_date
        ) 