from typing import List, Dict, Any
import asyncio
from app.agents.base import BaseAgent, DocumentType
from fastapi import UploadFile, HTTPException
import tempfile
from pathlib import Path
import os
import uuid
from app.services.redis_service import RedisService
from app.core.config import settings
from app.utils.pdf_validator import validate_pdf, get_pdf_info
from app.utils.redis_test import test_redis_connection
import numpy as np
import logging

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self, api_key: str, redis_url: str = None):
        """Initialize document processor with API key and Redis."""
        if not api_key:
            raise ValueError("API key is required")
        
        self.api_key = api_key
        self.agent = BaseAgent(api_key)
        
        # Initialize Redis service based on configuration
        if settings.USE_REDIS_CLOUD:
            self.redis = RedisService()  # Will use cloud settings
        else:
            self.redis = RedisService(redis_url)  # Will use local Docker

    async def process_documents(self, files: List[UploadFile]) -> Dict[str, Any]:
        """Process multiple documents in parallel."""
        if not files:
            raise HTTPException(status_code=422, detail="No files uploaded")

        # Initialize Redis and test connection
        await self.redis.initialize()
        redis_status = await test_redis_connection(settings.REDIS_URL)
        if redis_status["status"] != "healthy":
            raise HTTPException(
                status_code=500, 
                detail=f"Redis connection failed: {redis_status.get('error', 'Unknown error')}"
            )

        temp_files = []
        try:
            # Save and validate files
            temp_files = await self._save_and_validate_files(files)
            
            # Process files in parallel
            tasks = [
                self._process_single_document(file.filename, temp_path)
                for file, temp_path in zip(files, temp_files)
            ]
            results = await asyncio.gather(*tasks)

            # Extract texts for validation
            bill_text = next((r["text"] for r in results if r["type"] == "bill"), None)
            discharge_text = next((r["text"] for r in results if r["type"] == "discharge"), None)

            # Validate documents
            validation = await self.agent.validate_documents(
                bill_text or "",
                discharge_text or ""
            )

            # Store documents in Redis
            for result in results:
                doc_id = str(uuid.uuid4())
                # Generate embedding (mock for now, replace with actual embedding)
                embedding = np.random.rand(settings.VECTOR_DIMENSION)
                await self.redis.store_document(doc_id, result, embedding)

            return {
                "documents": [
                    {
                        "type": r["type"],
                        "filename": r["filename"],
                        "data": r["data"]
                    }
                    for r in results
                ],
                "validation": validation
            }

        finally:
            # Clean up temp files
            for temp_path in temp_files:
                try:
                    os.unlink(temp_path)
                except (OSError, PermissionError) as e:
                    logger.warning(f"Error cleaning up temp file {temp_path}: {str(e)}")

    async def _save_and_validate_files(self, files: List[UploadFile]) -> List[str]:
        """Save uploaded files to temporary directory and validate them."""
        temp_files = []
        for file in files:
            content = await file.read()
            
            # Validate PDF
            is_valid, error_msg = validate_pdf(content)
            if not is_valid:
                raise HTTPException(
                    status_code=422,
                    detail=f"Invalid PDF file '{file.filename}': {error_msg}"
                )

            # Get PDF info for logging
            pdf_info = get_pdf_info(content)
            logger.info(f"PDF Info for {file.filename}: {pdf_info}")

            # Save to temp file
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
                temp_file.write(content)
                temp_files.append(temp_file.name)
            
            await file.seek(0)

        return temp_files

    async def _process_single_document(self, filename: str, temp_path: str) -> Dict[str, Any]:
        """Process a single document."""
        try:
            # Extract text
            text = await self.agent.extract_text_from_pdf(temp_path)
            if text == "Empty document":
                raise HTTPException(
                    status_code=422,
                    detail=f"Could not extract text from {filename}"
                )

            # Classify document
            doc_type = await self.agent.classify_document(text)
            if doc_type == "unknown":
                raise HTTPException(
                    status_code=422,
                    detail=f"Could not classify document {filename}"
                )
            
            # Extract information
            info = await self.agent.extract_info(text, DocumentType(doc_type))
            if "error" in info:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error extracting information from {filename}: {info['error']}"
                )

            return {
                "type": doc_type,
                "filename": filename,
                "data": info,
                "text": text  # Used for validation
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error processing {filename}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process {filename}: {str(e)}"
            )

    async def search_similar_documents(self, query_text: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents using vector similarity."""
        # Initialize Redis and test connection
        await self.redis.initialize()
        redis_status = await test_redis_connection(settings.REDIS_URL)
        if redis_status["status"] != "healthy":
            raise HTTPException(
                status_code=500, 
                detail=f"Redis connection failed: {redis_status.get('error', 'Unknown error')}"
            )

        # Generate embedding for query (mock for now)
        query_embedding = np.random.rand(settings.VECTOR_DIMENSION)
        return await self.redis.search_similar_documents(query_embedding, k) 