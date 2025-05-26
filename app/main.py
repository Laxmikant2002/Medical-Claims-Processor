from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from typing import List
import os
import logging
import traceback

from app.core.config import settings
from app.services.document_processor import DocumentProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Initialize document processor
processor = DocumentProcessor(
    api_key=settings.GOOGLE_API_KEY,
    redis_url=settings.REDIS_URL
)

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main UI page."""
    try:
        with open("app/static/index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="""
        <html>
            <head>
                <title>Medical Claims Processor</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        max-width: 800px;
                        margin: 0 auto;
                        padding: 20px;
                    }
                    .upload-form {
                        border: 2px dashed #ccc;
                        padding: 20px;
                        text-align: center;
                        margin: 20px 0;
                    }
                </style>
            </head>
            <body>
                <h1>Medical Claims Processor</h1>
                <div class="upload-form">
                    <h2>Upload Documents</h2>
                    <form action="/process-documents" method="post" enctype="multipart/form-data">
                        <input type="file" name="files" multiple accept=".pdf" required>
                        <br><br>
                        <button type="submit">Process Documents</button>
                    </form>
                </div>
            </body>
        </html>
        """)

@app.post("/process-documents")
async def process_documents(files: List[UploadFile] = File(...)):
    """Process multiple medical documents."""
    try:
        # Log the request
        logger.info(f"Processing {len(files)} documents")
        for file in files:
            logger.info(f"File: {file.filename}, Size: {file.size} bytes")

        # Check if Google API key is set
        if not settings.GOOGLE_API_KEY or settings.GOOGLE_API_KEY == "your_api_key_here":
            raise HTTPException(
                status_code=500,
                detail="Google API key not configured. Please set GOOGLE_API_KEY in .env file."
            )

        result = await processor.process_documents(files)
        return result
    except HTTPException as e:
        logger.error(f"HTTP Exception: {str(e)}")
        raise e
    except Exception as e:
        # Log the full error with traceback
        logger.error(f"Error processing documents: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Error processing documents: {str(e)}"
        )

@app.post("/search-similar")
async def search_similar_documents(query: str, k: int = 5):
    """Search for similar documents."""
    try:
        results = await processor.search_similar_documents(query, k)
        return {"results": results}
    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check Redis connection
        redis_ok = await processor.redis.test_connection()
        if not redis_ok:
            return {
                "status": "unhealthy",
                "details": "Redis connection failed"
            }
        
        return {
            "status": "healthy",
            "redis": "connected",
            "google_api": "configured" if settings.GOOGLE_API_KEY else "not configured"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        } 