from typing import Dict, Any
from pathlib import Path
from .base import BaseAgent
from decimal import Decimal
from datetime import datetime

class BillAgent(BaseAgent):
    """Agent for processing medical bills."""
    
    EXTRACTION_PROMPT = """
    Extract the following information from this medical bill:
    - Hospital Name: Look for the healthcare provider's name in the header
    - Total Amount: Find the final payable amount, usually at the bottom
    - Date of Service: When the medical service was provided

    Format the response as a JSON object with these exact field names:
    {
        "hospital_name": "string",
        "total_amount": "decimal number",
        "date_of_service": "YYYY-MM-DD"
    }
    Return only the JSON object, no additional text.
    """
    
    VALIDATION_PROMPT = """
    Validate the following medical bill information:
    
    Check for:
    1. Hospital name is complete and valid
    2. Total amount is a positive number
    3. Date of service is a valid date
    4. Date of service is not in the future
    
    Return a JSON object with:
    {
        "is_valid": boolean,
        "errors": [list of error messages],
        "warnings": [list of warning messages]
    }
    """
    
    async def process_document(self, file_path: str) -> Dict[str, Any]:
        """Process a medical bill and extract relevant information."""
        try:
            # Convert file path to Path object
            path = Path(file_path)
            
            # Extract text from the bill
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
            return self._format_error(f"Failed to process bill: {str(e)}")
    
    async def validate_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the extracted bill data."""
        return await self._validate_with_llm(data, self.VALIDATION_PROMPT)
    
    def _parse_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and normalize the extracted data."""
        try:
            # Convert total amount to Decimal
            total_amount = Decimal(str(data["total_amount"]).replace("$", "").replace(",", ""))
            
            # Parse date
            date_of_service = datetime.strptime(
                data["date_of_service"],
                "%Y-%m-%d"
            ).date()
            
            return {
                "type": "bill",
                "hospital_name": data["hospital_name"].strip(),
                "total_amount": total_amount,
                "date_of_service": date_of_service.isoformat()
            }
            
        except (KeyError, ValueError, TypeError) as e:
            raise ValueError(f"Failed to parse extracted data: {str(e)}")
    
    @staticmethod
    def _validate_amount(amount: Decimal) -> bool:
        """Validate that the amount is positive and reasonable."""
        return amount > Decimal("0") and amount < Decimal("1000000")
    
    @staticmethod
    def _validate_date(date_str: str) -> bool:
        """Validate that the date is not in the future."""
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
            return date <= datetime.now().date()
        except ValueError:
            return False 