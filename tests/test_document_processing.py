import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import json
from datetime import datetime, timedelta
import os
from app.api.endpoints import app
from app.agents.base import BaseAgent, DocumentType
from .test_utils import MOCK_BILL_CONTENT, MOCK_DISCHARGE_CONTENT
from unittest.mock import AsyncMock, patch
import tempfile

client = TestClient(app)

@pytest.mark.asyncio
async def test_document_classification(base_agent, mock_pdf_files, mock_gemini_response):
    """Test document classification functionality."""
    with open(mock_pdf_files[0], 'rb') as f:
        text = await base_agent.extract_text_from_pdf(str(mock_pdf_files[0]))
        
        # Test bill classification
        mock_response = mock_gemini_response("bill")
        with patch.object(base_agent.model, 'generate_content_async', 
                         new_callable=AsyncMock, 
                         return_value=mock_response):
            doc_type = await base_agent.classify_document(text)
            assert doc_type == "bill"
        
        # Test discharge classification
        mock_response = mock_gemini_response("discharge")
        with patch.object(base_agent.model, 'generate_content_async', 
                         new_callable=AsyncMock, 
                         return_value=mock_response):
            doc_type = await base_agent.classify_document(text)
            assert doc_type == "discharge"

@pytest.mark.asyncio
async def test_bill_information_extraction(base_agent, mock_pdf_files, mock_gemini_response):
    """Test bill information extraction."""
    bill_text = await base_agent.extract_text_from_pdf(str(mock_pdf_files[0]))
    
    mock_json = '''{
        "Patient Name": "John Smith",
        "Hospital": "General Medical Center",
        "Total Amount": 1000,
        "Date of Service": "2024-03-15",
        "Insurance Provider": "Health Plus",
        "Policy Number": "HP123456789"
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
        assert bill_info["Insurance Provider"] == "Health Plus"

@pytest.mark.asyncio
async def test_discharge_information_extraction(base_agent, mock_pdf_files, mock_gemini_response):
    """Test discharge information extraction."""
    discharge_text = await base_agent.extract_text_from_pdf(str(mock_pdf_files[1]))
    
    mock_json = '''{
        "Patient Name": "John Smith",
        "Hospital": "General Medical Center",
        "Admission Date": "2024-03-12",
        "Discharge Date": "2024-03-15",
        "Diagnosis": "Acute Bronchitis",
        "Treatment Summary": "Antibiotic therapy, IV Fluids, Bronchodilators",
        "Follow Up": "Follow up with primary care in 1 week"
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
        assert "Follow up with primary care" in discharge_info["Follow Up"]

@pytest.mark.asyncio
async def test_validation_rules(base_agent, mock_pdf_files, mock_gemini_response):
    """Test document validation rules."""
    bill_text = await base_agent.extract_text_from_pdf(str(mock_pdf_files[0]))
    discharge_text = await base_agent.extract_text_from_pdf(str(mock_pdf_files[1]))
    
    # Test valid case
    mock_json = '''{
        "is_valid": true,
        "discrepancies": [],
        "validation_details": {
            "patient_name_match": true,
            "hospital_match": true,
            "dates_consistent": true,
            "insurance_info_present": true
        }
    }'''
    mock_response = mock_gemini_response(mock_json)
    
    with patch.object(base_agent.model, 'generate_content_async', 
                     new_callable=AsyncMock, 
                     return_value=mock_response):
        result = await base_agent.validate_documents(bill_text, discharge_text)
        assert result["is_valid"] is True
        assert len(result["discrepancies"]) == 0
        assert result["validation_details"]["patient_name_match"] is True
        
    # Test invalid case
    mock_json = '''{
        "is_valid": false,
        "discrepancies": ["Patient names do not match", "Date inconsistency"],
        "validation_details": {
            "patient_name_match": false,
            "hospital_match": true,
            "dates_consistent": false,
            "insurance_info_present": true
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

@pytest.mark.asyncio
async def test_pdf_processing(base_agent, mock_pdf_files):
    """Test PDF processing functionality."""
    # Test bill PDF
    bill_text = await base_agent.extract_text_from_pdf(str(mock_pdf_files[0]))
    assert "MEDICAL BILL" in bill_text
    assert "Hospital: General Medical Center" in bill_text
    assert "Patient Name: John Smith" in bill_text
    
    # Test discharge PDF
    discharge_text = await base_agent.extract_text_from_pdf(str(mock_pdf_files[1]))
    assert "DISCHARGE SUMMARY" in discharge_text
    assert "Hospital: General Medical Center" in discharge_text
    assert "Patient Name: John Smith" in discharge_text

@pytest.mark.asyncio
async def test_process_claim_endpoint(test_client, mock_successful_gemini_agent):
    """Test the process-claim endpoint."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", mode="wb", delete=True) as f:
        f.write(b"%PDF-1.7\nTest content")
        f.seek(0)
        files = {"files": ("test.pdf", f, "application/pdf")}
        response = test_client.post(
            "/process-claim",
            files=files
        )
        print(f"Response: {response.status_code} - {response.text}")  # Print response details
        assert response.status_code == 200
        result = response.json()
        assert "documents" in result
        assert "validation" in result
        assert result["documents"][0]["type"] == "bill"
        assert "Patient Name" in result["documents"][0]["data"]

def test_error_handling():
    """Test error handling."""
    # Test invalid request format
    response = client.post("/process-claim", json={"invalid": "data"})
    assert response.status_code in [400, 422]