from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import os
from typing import List
from pathlib import Path
from app.agents.base import BaseAgent
from app.core.document_processor import DocumentProcessor
import tempfile

app = FastAPI()

# Mount static files
static_dir = Path(__file__).parent.parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Initialize the agent with API key from environment
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY environment variable is required")

agent = BaseAgent(api_key)
processor = DocumentProcessor(api_key)

@app.get("/")
async def root():
    """Serve the main HTML page."""
    html_file = static_dir / "index.html"
    return HTMLResponse(content=html_file.read_text(), status_code=200)

async def process_documents(files: List[UploadFile], contents: List[bytes]) -> dict:
    """Process multiple documents and return structured data."""
    if not files:
        raise HTTPException(status_code=422, detail="No files uploaded")
    
    results = []
    temp_files = []
    try:
        # Save files to disk
        for file, content in zip(files, contents):
            if not file.filename.lower().endswith('.pdf'):
                raise HTTPException(status_code=422, detail=f"{file.filename} is not a PDF file")
            
            if len(content) == 0:
                raise HTTPException(status_code=422, detail="Empty or invalid file")
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(suffix=".pdf", mode="wb", delete=False) as temp_file:
                temp_file.write(content)
                temp_files.append(temp_file.name)
            
        # Process files
        for file, temp_path in zip(files, temp_files):
            try:
                doc_type = await agent.classify_document(await agent.extract_text_from_pdf(temp_path))
                info = await agent.extract_info(await agent.extract_text_from_pdf(temp_path), doc_type)
                results.append({
                    "type": doc_type,
                    "filename": file.filename,
                    "data": info
                })
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
            
        return {
            "documents": results,
            "validation": {"is_valid": True}  # Simplified validation for now
        }
    finally:
        # Clean up temp files
        for temp_path in temp_files:
            try:
                os.unlink(temp_path)
            except (OSError, PermissionError):
                pass

@app.post("/process-claim")
async def process_claim(files: List[UploadFile] = File(...)):
    """Process medical claim documents."""
    try:
        # Read and validate files
        contents = []
        for file in files:
            content = await file.read()
            if len(content) > 5 * 1024 * 1024:  # 5MB limit
                raise HTTPException(status_code=413, detail="File too large")
            if len(content) == 0:
                raise HTTPException(status_code=422, detail="Empty or invalid file")
            contents.append(content)
            await file.seek(0)  # Reset file pointer
            
        return await process_documents(files, contents)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 