import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
import tempfile
import os
from pathlib import Path
from app.api.endpoints import app
from app.agents.base import BaseAgent
from .test_utils import create_test_pdf, MOCK_BILL_CONTENT, MOCK_DISCHARGE_CONTENT

@pytest.fixture
def test_client():
    """Create a test client."""
    return TestClient(app)

@pytest.fixture
def base_agent():
    """Create a BaseAgent instance for testing."""
    return BaseAgent("test-api-key")

@pytest.fixture
def mock_successful_gemini_agent(mocker):
    """Mock successful Gemini agent responses."""
    mock_classify = mocker.patch('app.agents.base.BaseAgent.classify_document', new_callable=AsyncMock)
    mock_classify.return_value = "bill"
    
    mock_extract = mocker.patch('app.agents.base.BaseAgent.extract_info', new_callable=AsyncMock)
    mock_extract.return_value = {
        "Patient Name": "John Smith",
        "Hospital": "General Medical Center",
        "Total Amount": 1000,
        "Date of Service": "2024-03-15"
    }
    
    mock_text = mocker.patch('app.agents.base.BaseAgent.extract_text_from_pdf', new_callable=AsyncMock)
    mock_text.return_value = MOCK_BILL_CONTENT
    
    return {
        "classify": mock_classify,
        "extract": mock_extract,
        "text": mock_text
    }

@pytest.fixture
def mock_failed_gemini_agent(mocker):
    """Mock failed Gemini agent responses."""
    mock_classify = mocker.patch('app.agents.base.BaseAgent.classify_document', new_callable=AsyncMock)
    mock_classify.side_effect = Exception("Test error")
    
    mock_extract = mocker.patch('app.agents.base.BaseAgent.extract_info', new_callable=AsyncMock)
    mock_extract.side_effect = Exception("Test error")
    
    return {
        "classify": mock_classify,
        "extract": mock_extract
    }

@pytest.fixture
def mock_pdf_files(tmp_path):
    """Create mock PDF files for testing."""
    bill_pdf = tmp_path / "bill.pdf"
    discharge_pdf = tmp_path / "discharge.pdf"
    
    # Create test PDF files
    bill_pdf.write_bytes(create_test_pdf(MOCK_BILL_CONTENT))
    discharge_pdf.write_bytes(create_test_pdf(MOCK_DISCHARGE_CONTENT))
    
    return [bill_pdf, discharge_pdf]

@pytest.fixture
def sample_invalid_file(tmp_path):
    """Create an invalid PDF file."""
    invalid_file = tmp_path / "invalid.pdf"
    invalid_file.write_bytes(b"Not a PDF file")
    return invalid_file

@pytest.fixture
def test_data_dir(tmp_path):
    """Create a test data directory."""
    return tmp_path

@pytest.fixture(autouse=True)
def setup_environment():
    """Set up environment variables for testing."""
    os.environ["GOOGLE_API_KEY"] = "test-api-key"
    yield
    if "GOOGLE_API_KEY" in os.environ:
        del os.environ["GOOGLE_API_KEY"]

@pytest.fixture
def mock_gemini_response():
    """Mock Gemini API response."""
    class MockResponse:
        def __init__(self, text):
            self.text = text
    return lambda text: MockResponse(text)