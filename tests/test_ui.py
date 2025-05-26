import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import json
from app.api.endpoints import app
from .test_utils import create_test_pdf, MOCK_BILL_CONTENT
import tempfile
from unittest.mock import patch, AsyncMock
import os

client = TestClient(app)

def test_index_page():
    """Test that the index page loads correctly."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    
    # Check for required elements
    content = response.text
    assert "Medical Claims Processor" in content
    assert 'class="dropzone"' in content
    assert 'id="fileInput"' in content
    assert 'id="processBtn"' in content

def test_static_files():
    """Test that static files are served correctly."""
    css = client.get("/static/styles.css")
    js = client.get("/static/script.js")
    assert css.status_code == 200
    assert js.status_code == 200

def test_file_upload_validation():
    """Test file upload validation in the UI."""
    # Test with no files
    response = client.post("/process-claim")
    assert response.status_code == 422
    assert "Field required" in response.json()["detail"][0]["msg"]
    
    # Test with file too large
    with tempfile.NamedTemporaryFile(suffix=".pdf", mode="wb", delete=True) as f:
        f.write(b"%PDF-1.7\n" + b"0" * (10 * 1024 * 1024))  # 10MB file
        f.seek(0)
        response = client.post(
            "/process-claim",
            files={"files": ("large.pdf", f, "application/pdf")}
        )
        assert response.status_code == 400
        assert "There was an error parsing the body" in response.json()["detail"]
    
    # Test with invalid file type
    with tempfile.NamedTemporaryFile(suffix=".txt", mode="w+", delete=True) as f:
        f.write("test content")
        f.seek(0)
        response = client.post(
            "/process-claim",
            files={"files": ("test.txt", f, "text/plain")}
        )
        assert response.status_code == 422
        assert "is not a PDF file" in response.json()["detail"]

def test_ui_error_handling():
    """Test UI error handling."""
    # Test invalid request format
    response = client.post("/process-claim", json={"invalid": "data"})
    assert response.status_code in [400, 422]
    
    # Test server error handling
    with patch('app.agents.base.BaseAgent.classify_document', new_callable=AsyncMock) as mock_classify:
        mock_classify.side_effect = Exception("Test error")
        with tempfile.NamedTemporaryFile(suffix=".pdf", mode="wb", delete=True) as f:
            f.write(b"%PDF-1.7\n")
            f.seek(0)
            response = client.post(
                "/process-claim",
                files={"files": ("test.pdf", f, "application/pdf")}
            )
            assert response.status_code == 400
            assert "There was an error parsing the body" in response.json()["detail"]

def test_ui_success_response(mock_successful_gemini_agent):
    """Test successful UI response."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", mode="wb", delete=True) as f:
        f.write(b"%PDF-1.7\nTest content")
        f.seek(0)
        files = {"files": ("test.pdf", f, "application/pdf")}
        response = client.post(
            "/process-claim",
            files=files
        )
        assert response.status_code == 200
        result = response.json()
        assert "documents" in result
        assert "validation" in result
        assert result["documents"][0]["type"] == "bill"
        assert "Patient Name" in result["documents"][0]["data"]
        assert result["documents"][0]["data"]["Patient Name"] == "John Smith"

def test_ui_multiple_files(mock_successful_gemini_agent):
    """Test handling multiple file uploads."""
    files = []
    file_handles = []
    try:
        for i in range(2):
            f = tempfile.NamedTemporaryFile(suffix=".pdf", mode="wb", delete=False)
            f.write(b"%PDF-1.7\nTest content")
            f.seek(0)
            handle = open(f.name, "rb")
            file_handles.append(handle)
            files.append(("files", (f"test{i}.pdf", handle, "application/pdf")))
        
        response = client.post("/process-claim", files=files)
        assert response.status_code == 200
        result = response.json()
        assert len(result["documents"]) == 2
        for doc in result["documents"]:
            assert doc["type"] == "bill"
            assert "Patient Name" in doc["data"]
            
    finally:
        for handle in file_handles:
            handle.close()
            try:
                os.unlink(handle.name)
            except (OSError, PermissionError):
                pass

def test_ui_validation_feedback(mock_successful_gemini_agent):
    """Test validation feedback in UI response."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", mode="wb", delete=True) as f:
        f.write(b"%PDF-1.7\nTest content")
        f.seek(0)
        files = {"files": ("test.pdf", f, "application/pdf")}
        response = client.post(
            "/process-claim",
            files=files
        )
        assert response.status_code == 200
        result = response.json()
        assert "validation" in result
        assert isinstance(result["validation"], dict)
        assert "is_valid" in result["validation"]