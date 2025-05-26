import redis.asyncio as redis
from app.core.config import settings
import asyncio

async def test_redis_connection(url: str = None) -> dict:
    """Test Redis connection and functionality."""
    try:
        # Use provided URL or default configuration
        if url and url.startswith("redis://"):
            redis_client = redis.from_url(url)
        else:
            redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                decode_responses=True,
                username=settings.REDIS_USERNAME,
                password=settings.REDIS_PASSWORD,
            )

        # Test basic operations
        await redis_client.ping()
        
        # Test JSON operations
        test_key = "test:json"
        test_data = {"test": "data"}
        await redis_client.json().set(test_key, "$", test_data)
        retrieved_data = await redis_client.json().get(test_key)
        await redis_client.delete(test_key)

        # Test search index
        try:
            await redis_client.ft("doc_idx").info()
            index_exists = True
        except:
            index_exists = False

        await redis_client.close()

        return {
            "status": "healthy",
            "connection": "successful",
            "operations": {
                "ping": True,
                "json": retrieved_data == test_data,
                "search_index": index_exists
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "connection": "failed",
            "error": str(e)
        }

if __name__ == "__main__":
    # Test the Redis connection
    result = asyncio.run(test_redis_connection())
    print("Redis Connection Test Results:")
    print(f"Status: {result['status']}")
    print(f"Connection: {result['connection']}")
    if 'error' in result:
        print(f"Error: {result['error']}")
    elif 'operations' in result:
        print("\nOperations:")
        for op, success in result['operations'].items():
            print(f"- {op}: {'✓' if success else '✗'}") 