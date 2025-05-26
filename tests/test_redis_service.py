import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import numpy as np
from app.services.redis_service import RedisService
from redis.commands.search.field import VectorField, TextField
from redis.commands.search.indexDefinition import IndexDefinition

@pytest.fixture
def mock_redis_client():
    with patch('redis.asyncio.Redis') as mock:
        redis_instance = AsyncMock()
        # Mock ft() method for search operations
        ft_instance = AsyncMock()
        ft_instance.create_index = AsyncMock()
        ft_instance.search = AsyncMock(return_value=MagicMock(docs=[]))
        redis_instance.ft = MagicMock(return_value=ft_instance)
        
        # Mock json() method for document operations
        json_instance = AsyncMock()
        json_instance.set = AsyncMock(return_value=True)
        json_instance.get = AsyncMock(return_value={"test": "data"})
        redis_instance.json = MagicMock(return_value=json_instance)
        
        # Mock basic Redis operations
        redis_instance.ping = AsyncMock(return_value=True)
        redis_instance.delete = AsyncMock(return_value=True)
        
        mock.return_value = redis_instance
        yield mock

@pytest.fixture
def redis_service(mock_redis_client):
    return RedisService(redis_url="redis://localhost:6379")

@pytest.mark.asyncio
async def test_initialization(redis_service):
    """Test Redis service initialization."""
    assert not redis_service.is_initialized
    await redis_service.initialize()
    assert redis_service.is_initialized

@pytest.mark.asyncio
async def test_ensure_index(redis_service, mock_redis_client):
    """Test index creation."""
    await redis_service.initialize()
    
    redis_instance = mock_redis_client.return_value
    ft_instance = redis_instance.ft.return_value
    
    assert ft_instance.create_index.called
    # Verify the schema was created with correct fields
    call_args = ft_instance.create_index.call_args
    assert len(call_args[0][0]) == 3  # Should have 3 fields: type, filename, embedding

@pytest.mark.asyncio
async def test_test_connection_success(redis_service):
    """Test successful Redis connection."""
    result = await redis_service.test_connection()
    assert result == True

@pytest.mark.asyncio
async def test_test_connection_failure(redis_service, mock_redis_client):
    """Test Redis connection failure."""
    redis_instance = mock_redis_client.return_value
    redis_instance.ping.side_effect = Exception("Connection failed")
    
    result = await redis_service.test_connection()
    assert result == False

@pytest.mark.asyncio
async def test_store_document(redis_service):
    """Test document storage."""
    doc_id = "test_id"
    doc_data = {
        "type": "bill",
        "filename": "test.pdf",
        "data": {"amount": 100}
    }
    embedding = np.random.rand(768)  # Assuming VECTOR_DIMENSION = 768
    
    result = await redis_service.store_document(doc_id, doc_data, embedding)
    assert result == True

@pytest.mark.asyncio
async def test_search_similar_documents(redis_service):
    """Test document similarity search."""
    query_embedding = np.random.rand(768)
    
    results = await redis_service.search_similar_documents(query_embedding, k=5)
    assert isinstance(results, list)

@pytest.mark.asyncio
async def test_get_document(redis_service):
    """Test document retrieval."""
    doc_id = "test_id"
    result = await redis_service.get_document(doc_id)
    assert result == {"test": "data"}

@pytest.mark.asyncio
async def test_delete_document(redis_service):
    """Test document deletion."""
    doc_id = "test_id"
    result = await redis_service.delete_document(doc_id)
    assert result == True

@pytest.mark.asyncio
async def test_store_document_failure(redis_service, mock_redis_client):
    """Test document storage failure."""
    redis_instance = mock_redis_client.return_value
    json_instance = redis_instance.json.return_value
    json_instance.set.side_effect = Exception("Storage failed")
    
    doc_id = "test_id"
    doc_data = {
        "type": "bill",
        "filename": "test.pdf",
        "data": {"amount": 100}
    }
    embedding = np.random.rand(768)
    
    result = await redis_service.store_document(doc_id, doc_data, embedding)
    assert result == False 