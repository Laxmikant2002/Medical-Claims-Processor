import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import UploadFile, HTTPException
import numpy as np
import os
from app.services.document_processor import DocumentProcessor
from app.core.config import settings

@pytest.fixture
def mock_redis_service():
    with patch('app.services.document_processor.RedisService') as mock:
        redis_instance = AsyncMock()
        redis_instance.initialize = AsyncMock()
        redis_instance.test_connection = AsyncMock(return_value=True)
        redis_instance.store_document = AsyncMock(return_value=True)
        redis_instance.search_similar_documents = AsyncMock(return_value=[])
        mock.return_value = redis_instance
        yield mock

@pytest.fixture
def mock_base_agent():
    with patch('app.services.document_processor.BaseAgent') as mock:
        agent_instance = AsyncMock()
        agent_instance.extract_text_from_pdf = AsyncMock(return_value="Sample text")
        agent_instance.classify_document = AsyncMock(return_value="bill")
        agent_instance.extract_info = AsyncMock(return_value={"amount": 100})
        agent_instance.validate_documents = AsyncMock(return_value={
            "is_valid": True,
            "discrepancies": [],
            "validation_details": {
                "patient_name_match": True,
                "hospital_match": True,
                "dates_consistent": True
            }
        })
        mock.return_value = agent_instance
        yield mock

@pytest.fixture
def sample_pdf_file():
    content = b"%PDF-1.4 sample content"
    file = AsyncMock(spec=UploadFile)
    file.filename = "test.pdf"
    file.read = AsyncMock(return_value=content)
    file.seek = AsyncMock()
    return file

@pytest.mark.asyncio
async def test_process_documents_success(mock_redis_service, mock_base_agent, sample_pdf_file):
    """Test successful document processing flow."""
    processor = DocumentProcessor(api_key="test_key")
    
    result = await processor.process_documents([sample_pdf_file])
    
    assert result["documents"][0]["type"] == "bill"
    assert "validation" in result
    assert result["validation"]["is_valid"] == True
    
    # Verify Redis operations
    redis_instance = mock_redis_service.return_value
    assert redis_instance.initialize.called
    assert redis_instance.test_connection.called
    assert redis_instance.store_document.called

@pytest.mark.asyncio
async def test_process_documents_redis_connection_failure(mock_redis_service, mock_base_agent, sample_pdf_file):
    """Test handling of Redis connection failure."""
    redis_instance = mock_redis_service.return_value
    redis_instance.test_connection.return_value = False
    
    processor = DocumentProcessor(api_key="test_key")
    
    with pytest.raises(HTTPException) as exc_info:
        await processor.process_documents([sample_pdf_file])
    
    assert exc_info.value.status_code == 500
    assert "Redis connection failed" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_process_documents_invalid_file(mock_redis_service, mock_base_agent):
    """Test handling of invalid file type."""
    invalid_file = AsyncMock(spec=UploadFile)
    invalid_file.filename = "test.txt"
    
    processor = DocumentProcessor(api_key="test_key")
    
    with pytest.raises(HTTPException) as exc_info:
        await processor.process_documents([invalid_file])
    
    assert exc_info.value.status_code == 422
    assert "is not a PDF file" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_process_documents_empty_file(mock_redis_service, mock_base_agent):
    """Test handling of empty file."""
    empty_file = AsyncMock(spec=UploadFile)
    empty_file.filename = "test.pdf"
    empty_file.read = AsyncMock(return_value=b"")
    empty_file.seek = AsyncMock()
    
    processor = DocumentProcessor(api_key="test_key")
    
    with pytest.raises(HTTPException) as exc_info:
        await processor.process_documents([empty_file])
    
    assert exc_info.value.status_code == 422
    assert "is empty" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_search_similar_documents(mock_redis_service, mock_base_agent):
    """Test document similarity search."""
    processor = DocumentProcessor(api_key="test_key")
    
    await processor.search_similar_documents("sample query")
    
    redis_instance = mock_redis_service.return_value
    assert redis_instance.initialize.called
    assert redis_instance.test_connection.called
    assert redis_instance.search_similar_documents.called

@pytest.mark.asyncio
async def test_process_documents_extraction_failure(mock_redis_service, mock_base_agent, sample_pdf_file):
    """Test handling of text extraction failure."""
    agent_instance = mock_base_agent.return_value
    agent_instance.extract_text_from_pdf.return_value = "Empty document"
    
    processor = DocumentProcessor(api_key="test_key")
    
    with pytest.raises(HTTPException) as exc_info:
        await processor.process_documents([sample_pdf_file])
    
    assert exc_info.value.status_code == 422
    assert "Could not extract text" in str(exc_info.value.detail) 