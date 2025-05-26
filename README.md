# Medical Claims Processor

A modern web application for processing and validating medical claims documents using AI-powered document analysis.

## Architecture Overview

### Tech Stack
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Backend**: FastAPI (Python 3.9+)
- **AI/ML**: Google Gemini Pro
- **Document Processing**: PyPDF2, Tesseract OCR
- **Database**: PostgreSQL
- **Caching**: Redis

### System Components
1. **Document Processing Pipeline**:
   - PDF text extraction using PyPDF2 and Tesseract OCR.
   - Document classification and information extraction using Google Gemini Pro.
2. **Agent Orchestration**:
   - ClaimProcessorAgent for document classification and embedding storage.
   - ValidationAgent for cross-document validation.
3. **API Endpoints**:
   - `POST /process-claim`: Processes uploaded documents.

## AI Tools Integration

### Tools Used
1. **Google Gemini Pro**:
   - Document classification and analysis.
   - Information extraction from medical documents.
   - Cross-document validation support.
2. **Vector Store (Weaviate)**:
   - Document embeddings storage.
   - Semantic search capabilities.

### Prompt Examples
#### Document Classification Prompt
```python
prompt = """Analyze this medical document and classify it into one of these categories:
- Medical Bill
- Discharge Summary
- Insurance Claim
- Lab Report
- Prescription

Document text:
{document_text}

Return only the category name."""
```

#### Information Extraction Prompt
```python
prompt = """Extract the following information from this medical document:
- Patient Name
- Date of Service
- Total Amount
- Provider Details
- Insurance ID

Document text:
{document_text}

Return the information in JSON format."""
```

#### Validation Prompt
```python
prompt = """Compare these two medical documents for consistency:
Document 1: {doc1_text}
Document 2: {doc2_text}

Check for:
1. Matching patient information
2. Date consistency
3. Provider details match
4. Amount accuracy

Return discrepancies in JSON format."""
```

## Setup Instructions

### Prerequisites
- Install Tesseract OCR:
  ```bash
  # Windows
  winget install --id=Google.Tesseract-OCR  -e

  # Linux
  sudo apt-get install tesseract-ocr

  # macOS
  brew install tesseract
  ```

### Environment Setup
1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # Linux/macOS
   source venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file:
   ```env
   GOOGLE_API_KEY=your_api_key_here
   DEBUG=True
   ```

### Running the Application
```bash
uvicorn main:app --reload
```
Access the application at [http://localhost:8000](http://localhost:8000).

## Bonus Features

### Docker Support
- **Dockerfile** for containerization:
  ```dockerfile
  FROM python:3.9-slim

  WORKDIR /app
  COPY requirements.txt .
  RUN pip install -r requirements.txt

  COPY . .
  CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
  ```

### Redis Integration
- **Caching and Queue Management**:
  ```bash
  docker run -d --name redis-stack -p 6379:6379 redis/redis-stack:latest
  ```

### PostgreSQL Setup
- **Database for Claims Storage**:
  ```bash
  docker run -d --name postgres -e POSTGRES_PASSWORD=password -p 5432:5432 postgres:latest
  ```