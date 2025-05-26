from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from typing import List
import os
from app.agents.base import process_documents
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Medical Claims Processor")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main UI page."""
    with open("app/static/index.html") as f:
        return HTMLResponse(content=f.read(), status_code=200)

@app.post("/process-claim")
async def process_claim(files: List[UploadFile] = File(...)):
    """Process uploaded claim documents."""
    if not files:
        raise HTTPException(status_code=422, detail="No files uploaded")
    
    if not os.getenv("GOOGLE_API_KEY"):
        raise HTTPException(status_code=500, detail="Google API key not configured")
    
    # Validate file types
    for file in files:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=422, detail=f"{file.filename} is not a PDF file")
    
    try:
        result = await process_documents(files)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))