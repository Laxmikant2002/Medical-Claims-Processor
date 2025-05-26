from typing import Dict, Any
from app.agents.base import BaseAgent

class IDCardAgent(BaseAgent):
    """Specialized agent for processing medical ID cards."""

    async def extract_id_card_info(self, text: str) -> Dict[str, Any]:
        """Extract information from medical ID card."""
        if not text:
            return {
                "member_name": None,
                "member_id": None,
                "group_number": None,
                "plan_type": None,
                "effective_date": None,
                "insurance_provider": None
            }

        prompt = f"""Extract the following information from this medical ID card and return ONLY a JSON object with these exact keys:
- "member_name"
- "member_id"
- "group_number"
- "plan_type"
- "effective_date"
- "insurance_provider"

ID card text:
{text}
"""

        try:
            text_response = await self._generate_content_with_retry(prompt)
            if text_response.startswith('```json'):
                text_response = text_response[7:-3]
            elif text_response.startswith('{'):
                text_response = text_response
            else:
                return self._get_empty_id_card_response()

            result = json.loads(text_response)
            required_keys = [
                "member_name", "member_id", "group_number",
                "plan_type", "effective_date", "insurance_provider"
            ]

            # Add missing keys with None values
            for key in required_keys:
                if key not in result:
                    result[key] = None

            return result
        except Exception as e:
            return self._get_empty_id_card_response()

    def _get_empty_id_card_response(self) -> Dict[str, Any]:
        """Get empty response for ID card data."""
        return {
            "member_name": None,
            "member_id": None,
            "group_number": None,
            "plan_type": None,
            "effective_date": None,
            "insurance_provider": None
        }

    async def validate_id_card(self, id_card_data: Dict[str, Any], patient_name: str) -> Dict[str, Any]:
        """Validate ID card information against patient name."""
        if not id_card_data or not patient_name:
            return {
                "is_valid": False,
                "discrepancies": ["Missing required data"],
                "validation_details": {
                    "name_match": False,
                    "card_expired": None,
                    "required_fields_present": False
                }
            }

        prompt = f"""Compare the ID card member name with the patient name and validate the card information.
Return ONLY a JSON object with these exact keys:
- "is_valid": boolean
- "discrepancies": list of strings describing any inconsistencies
- "validation_details": dictionary with these exact keys:
  - "name_match": boolean
  - "card_expired": boolean or null if date cannot be determined
  - "required_fields_present": boolean

ID card member name: {id_card_data.get('member_name')}
Patient name: {patient_name}
Effective date: {id_card_data.get('effective_date')}
"""

        try:
            text_response = await self._generate_content_with_retry(prompt)
            if text_response.startswith('```json'):
                text_response = text_response[7:-3]
            elif text_response.startswith('{'):
                text_response = text_response
            else:
                return self._get_validation_error_response()

            result = json.loads(text_response)
            required_keys = ["is_valid", "discrepancies", "validation_details"]
            required_detail_keys = ["name_match", "card_expired", "required_fields_present"]

            if not all(key in result for key in required_keys):
                return self._get_validation_error_response()

            if not all(key in result["validation_details"] for key in required_detail_keys):
                return self._get_validation_error_response()

            return result
        except Exception as e:
            return self._get_validation_error_response()

    def _get_validation_error_response(self) -> Dict[str, Any]:
        """Get error response for validation failures."""
        return {
            "is_valid": False,
            "discrepancies": ["Validation failed"],
            "validation_details": {
                "name_match": False,
                "card_expired": None,
                "required_fields_present": False
            }
        } 