import pytest
import tempfile
import os
from fastapi.testclient import TestClient
from app.api.endpoints import app
from pathlib import Path
from unittest.mock import patch, AsyncMock

client = TestClient(app)

@pytest.fixture
def sample_pdf_files():
    """Get paths to sample PDF files."""
    test_data_dir = Path("tests/test_data")
    bill_path = test_data_dir / "sample_bill.pdf"
    discharge_path = test_data_dir / "sample_discharge.pdf"
    
    if not (bill_path.exists() and discharge_path.exists()):
        pytest.skip("Test PDF files not found. Run create_test_pdfs.py first.")
    
    return [bill_path, discharge_path]

def test_process_claim_endpoint(sample_pdf_files):
    """Test successful claim processing."""
    files = []
    file_handles = []
    try:
        for f in sample_pdf_files:
            handle = open(f, "rb")
            file_handles.append(handle)
            files.append(("files", (f.name, handle, "application/pdf")))
        
        with patch('app.agents.base.BaseAgent.classify_document', new_callable=AsyncMock) as mock_classify:
            mock_classify.return_value = "bill"
            with patch('app.agents.base.BaseAgent.extract_info', new_callable=AsyncMock) as mock_extract:
                mock_extract.return_value = {
                    "Patient Name": "John Smith",
                    "Hospital": "General Medical Center",
                    "Total Amount": 1000,
                    "Date of Service": "2024-03-15"
                }
                
                response = client.post("/process-claim", files=files)
                assert response.status_code == 200
                result = response.json()
                assert "documents" in result
                assert "validation" in result
                
    finally:
        for handle in file_handles:
            handle.close()

def test_process_claim_invalid_file_type():
    """Test the process-claim endpoint with an invalid file type."""
    with tempfile.NamedTemporaryFile(suffix=".txt", mode="w+", delete=True) as f:
        f.write("test content")
        f.seek(0)
        response = client.post(
            "/process-claim",
            files={"files": ("test.txt", f, "text/plain")}
        )
        assert response.status_code == 422
        assert "is not a PDF file" in response.json()["detail"]

def test_empty_file():
    """Test handling of empty files."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", mode="wb", delete=True) as f:
        f.write(b"")  # Empty file
        f.seek(0)
        response = client.post(
            "/process-claim",
            files={"files": ("empty.pdf", f, "application/pdf")}
        )
        assert response.status_code == 400
        assert "There was an error parsing the body" in response.json()["detail"]

def test_file_upload_validation():
    """Test file upload validation."""
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

def test_ui_error_handling():
    """Test handling of UI errors."""
    # Test invalid request format
    response = client.post("/process-claim", json={"invalid": "data"})
    assert response.status_code in [400, 422]
    
    # Test server error handling
    with patch('app.agents.base.BaseAgent.classify_document', new_callable=AsyncMock) as mock_classify:
        mock_classify.side_effect = Exception("Test error")
        with tempfile.NamedTemporaryFile(suffix=".pdf", mode="wb") as f:
            f.write(b"%PDF-1.7\n")
            f.seek(0)
            response = client.post(
                "/process-claim",
                files={"files": ("test.pdf", f, "application/pdf")}
            )
            assert response.status_code == 400
            assert "There was an error parsing the body" in response.json()["detail"]

@pytest.mark.asyncio
class TestProcessClaim:
    """Test cases for the process-claim endpoint."""
    
    async def test_successful_claim(self, test_client, mock_successful_gemini_agent):
        """Test successful claim processing."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", mode="wb", delete=True) as f:
            f.write(b"%PDF-1.7\nTest content")
            f.seek(0)
            files = {"files": ("test.pdf", f, "application/pdf")}
            response = test_client.post(
                "/process-claim",
                files=files
            )
            assert response.status_code == 200
            result = response.json()
            assert "documents" in result
            assert "validation" in result
            assert result["documents"][0]["type"] == "bill"
            assert "Patient Name" in result["documents"][0]["data"]
    
    async def test_multiple_files(self, test_client, mock_successful_gemini_agent):
        """Test processing multiple files."""
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
            
            response = test_client.post("/process-claim", files=files)
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
    
    async def test_large_file_handling(self, test_client, mock_successful_gemini_agent):
        """Test handling of large files."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", mode="wb", delete=True) as f:
            f.write(b"%PDF-1.7\n" + b"0" * (10 * 1024 * 1024))  # 10MB file
            f.seek(0)
            response = test_client.post(
                "/process-claim",
                files={"files": ("large.pdf", f, "application/pdf")}
            )
            assert response.status_code == 400
            assert "There was an error parsing the body" in response.json()["detail"]
    
    async def test_empty_file(self, test_client, mock_failed_gemini_agent):
        """Test handling of empty files."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", mode="wb", delete=True) as f:
            f.write(b"")  # Empty file
            f.seek(0)
            response = test_client.post(
                "/process-claim",
                files={"files": ("empty.pdf", f, "application/pdf")}
            )
            assert response.status_code == 400
            assert "There was an error parsing the body" in response.json()["detail"]