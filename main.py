from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
import os
from app.core.config import settings
from app.services.document_processor import DocumentProcessor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
document_processor = DocumentProcessor(
    api_key=settings.GOOGLE_API_KEY,
    redis_url=settings.REDIS_URL
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main UI page."""
    try:
        with open("app/static/index.html") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="UI template not found")

@app.post(f"{settings.API_V1_STR}/process-claim")
async def process_claim(files: List[UploadFile] = File(...)) -> Dict[str, Any]:
    """Process uploaded claim documents."""
    if not files:
        raise HTTPException(status_code=422, detail="No files uploaded")
    
    # Validate file types
    for file in files:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=422,
                detail=f"{file.filename} is not a PDF file"
            )
    
    try:
        result = await document_processor.process_documents(files)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get(f"{settings.API_V1_STR}/similar-documents")
async def search_similar_documents(query: str, k: int = 5) -> List[Dict[str, Any]]:
    """Search for similar documents."""
    try:
        results = await document_processor.search_similar_documents(query, k)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))