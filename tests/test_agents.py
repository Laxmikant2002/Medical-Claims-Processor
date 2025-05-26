import pytest
import asyncio
import random
from unittest.mock import AsyncMock, patch
from app.agents.base import BaseAgent, DocumentType
from google.api_core.exceptions import ResourceExhausted
import os
from pathlib import Path

async def handle_rate_limit(func, *args, max_retries=3, base_delay=2):
    """Helper function to handle rate limiting with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return await func(*args)
        except ResourceExhausted as e:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt) + (random.random() * 0.1)
            await asyncio.sleep(delay)

@pytest.fixture
def mock_gemini_response():
    """Mock Gemini API response."""
    class MockResponse:
        def __init__(self, text):
            self.text = text
    return MockResponse

@pytest.fixture
def base_agent():
    """Create a BaseAgent instance for testing."""
    return BaseAgent("test-api-key")

@pytest.fixture
def sample_pdf_files():
    """Get paths to sample PDF files."""
    test_data_dir = Path("tests/test_data")
    bill_path = test_data_dir / "sample_bill.pdf"
    discharge_path = test_data_dir / "sample_discharge.pdf"
    
    if not (bill_path.exists() and discharge_path.exists()):
        pytest.skip("Test PDF files not found. Run create_test_pdfs.py first.")
    
    return [bill_path, discharge_path]

@pytest.fixture
def sample_invalid_file():
    """Get path to invalid PDF file."""
    return Path("tests/test_data/invalid.pdf")

@pytest.mark.asyncio
async def test_document_classification_bill(base_agent, sample_pdf_files, mock_gemini_response):
    """Test bill document classification."""
    with open(sample_pdf_files[0], 'rb') as f:
        text = await base_agent.extract_text_from_pdf(str(sample_pdf_files[0]))
        print("\nExtracted text from bill:")
        print(text)
        
        # Mock the Gemini API response
        mock_response = mock_gemini_response("bill")
        with patch.object(base_agent.model, 'generate_content_async', 
                         new_callable=AsyncMock, 
                         return_value=mock_response):
            doc_type = await base_agent.classify_document(text)
            assert doc_type == "bill"

@pytest.mark.asyncio
async def test_document_classification_discharge(base_agent, sample_pdf_files, mock_gemini_response):
    """Test discharge document classification."""
    with open(sample_pdf_files[1], 'rb') as f:
        text = await base_agent.extract_text_from_pdf(str(sample_pdf_files[1]))
        
        # Mock the Gemini API response
        mock_response = mock_gemini_response("discharge")
        with patch.object(base_agent.model, 'generate_content_async', 
                         new_callable=AsyncMock, 
                         return_value=mock_response):
            doc_type = await base_agent.classify_document(text)
            assert doc_type == "discharge"

@pytest.mark.asyncio
async def test_bill_information_extraction(base_agent, sample_pdf_files, mock_gemini_response):
    """Test bill information extraction."""
    bill_text = await base_agent.extract_text_from_pdf(str(sample_pdf_files[0]))
    
    # Mock the Gemini API response
    mock_json = '''{
        "Patient Name": "John Smith",
        "Hospital": "General Medical Center",
        "Total Amount": 1000,
        "Date of Service": "2024-03-15"
    }'''
    mock_response = mock_gemini_response(mock_json)
    
    with patch.object(base_agent.model, 'generate_content_async', 
                     new_callable=AsyncMock, 
                     return_value=mock_response):
        bill_info = await base_agent.extract_info(bill_text, DocumentType.BILL)
        
        assert isinstance(bill_info, dict)
        assert bill_info["Patient Name"] == "John Smith"
        assert bill_info["Hospital"] == "General Medical Center"
        assert bill_info["Total Amount"] == 1000
        assert bill_info["Date of Service"] == "2024-03-15"

@pytest.mark.asyncio
async def test_discharge_information_extraction(base_agent, sample_pdf_files, mock_gemini_response):
    """Test discharge information extraction."""
    discharge_text = await base_agent.extract_text_from_pdf(str(sample_pdf_files[1]))
    
    # Mock the Gemini API response
    mock_json = '''{
        "Patient Name": "John Smith",
        "Hospital": "General Medical Center",
        "Admission Date": "2024-03-12",
        "Discharge Date": "2024-03-15",
        "Diagnosis": "Acute Bronchitis",
        "Treatment Summary": "Antibiotic therapy, IV Fluids, Bronchodilators"
    }'''
    mock_response = mock_gemini_response(mock_json)
    
    with patch.object(base_agent.model, 'generate_content_async', 
                     new_callable=AsyncMock, 
                     return_value=mock_response):
        discharge_info = await base_agent.extract_info(discharge_text, DocumentType.DISCHARGE)
        
        assert isinstance(discharge_info, dict)
        assert discharge_info["Patient Name"] == "John Smith"
        assert discharge_info["Hospital"] == "General Medical Center"
        assert discharge_info["Admission Date"] == "2024-03-12"
        assert discharge_info["Discharge Date"] == "2024-03-15"
        assert discharge_info["Diagnosis"] == "Acute Bronchitis"
        assert "Antibiotic therapy" in discharge_info["Treatment Summary"]

@pytest.mark.asyncio
async def test_document_validation(base_agent, sample_pdf_files, mock_gemini_response):
    """Test document validation."""
    bill_text = await base_agent.extract_text_from_pdf(str(sample_pdf_files[0]))
    discharge_text = await base_agent.extract_text_from_pdf(str(sample_pdf_files[1]))
    
    # Mock the Gemini API response
    mock_json = '''{
        "is_valid": true,
        "discrepancies": [],
        "validation_details": {
            "patient_name_match": true,
            "hospital_match": true,
            "dates_consistent": true
        }
    }'''
    mock_response = mock_gemini_response(mock_json)
    
    with patch.object(base_agent.model, 'generate_content_async', 
                     new_callable=AsyncMock, 
                     return_value=mock_response):
        result = await base_agent.validate_documents(bill_text, discharge_text)
        
        assert isinstance(result, dict)
        assert result["is_valid"] is True
        assert len(result["discrepancies"]) == 0
        assert result["validation_details"]["patient_name_match"] is True

@pytest.mark.asyncio
async def test_api_key_validation():
    """Test API key validation."""
    with pytest.raises(ValueError, match="API key cannot be empty"):
        agent = BaseAgent("")  # Empty API key should raise an error

@pytest.mark.asyncio
async def test_empty_document_handling(base_agent, sample_invalid_file, mock_gemini_response):
    """Test handling of empty or invalid documents."""
    text = await base_agent.extract_text_from_pdf(str(sample_invalid_file))
    assert text == "Empty document"
    
    # Mock the Gemini API response
    mock_json = '{}'  # Empty response for invalid document
    mock_response = mock_gemini_response(mock_json)
    
    with patch.object(base_agent.model, 'generate_content_async', 
                     new_callable=AsyncMock, 
                     return_value=mock_response):
        result = await base_agent.extract_info(text, DocumentType.BILL)
        assert isinstance(result, dict)
        assert all(key in result for key in ["Patient Name", "Hospital", "Total Amount", "Date of Service"])

@pytest.mark.asyncio
async def test_validation_rules(base_agent, sample_pdf_files, mock_gemini_response):
    """Test document validation rules."""
    bill_text = await base_agent.extract_text_from_pdf(str(sample_pdf_files[0]))
    discharge_text = await base_agent.extract_text_from_pdf(str(sample_pdf_files[1]))
    
    # Test case 1: Valid documents with matching information
    mock_json = '''{
        "is_valid": true,
        "discrepancies": [],
        "validation_details": {
            "patient_name_match": true,
            "hospital_match": true,
            "dates_consistent": true
        }
    }'''
    mock_response = mock_gemini_response(mock_json)
    
    with patch.object(base_agent.model, 'generate_content_async', 
                     new_callable=AsyncMock, 
                     return_value=mock_response):
        result = await base_agent.validate_documents(bill_text, discharge_text)
        assert result["is_valid"] is True
        assert len(result["discrepancies"]) == 0
        
    # Test case 2: Documents with discrepancies
    mock_json = '''{
        "is_valid": false,
        "discrepancies": ["Patient names do not match", "Date inconsistency"],
        "validation_details": {
            "patient_name_match": false,
            "hospital_match": true,
            "dates_consistent": false
        }
    }'''
    mock_response = mock_gemini_response(mock_json)
    
    with patch.object(base_agent.model, 'generate_content_async', 
                     new_callable=AsyncMock, 
                     return_value=mock_response):
        result = await base_agent.validate_documents(bill_text, discharge_text)
        assert result["is_valid"] is False
        assert len(result["discrepancies"]) == 2
        assert "Patient names do not match" in result["discrepancies"]
        
    # Test case 3: Missing documents
    result = await base_agent.validate_documents("", discharge_text)
    assert result["is_valid"] is False
    assert "Missing required documents" in result["discrepancies"]
    
    result = await base_agent.validate_documents(bill_text, "")
    assert result["is_valid"] is False
    assert "Missing required documents" in result["discrepancies"]