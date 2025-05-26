# Medical Claims Processor

A modern web application for processing and validating medical claims documents using AI-powered document analysis.

## Features

- 🚀 Modern drag-and-drop interface for file uploads
- 📄 PDF text extraction with OCR support
- 🤖 AI-powered document classification and information extraction
- ✅ Comprehensive validation rules
- 📊 Detailed processing results
- 🎯 Cross-document consistency checks
- 📱 Responsive design for all devices

## Architecture

### Tech Stack
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Backend**: FastAPI (Python 3.9+)
- **AI/ML**: Google Gemini Pro
- **Document Processing**: PyPDF2, Tesseract OCR
- **Testing**: pytest, pytest-asyncio

### Component Overview

1. **Document Processing Pipeline**
   - PDF text extraction (PyPDF2 + Tesseract OCR)
   - Document classification (Gemini AI)
   - Information extraction (Gemini AI)
   - Validation and cross-checking

2. **Agent Architecture**
   - Base agent with common functionality
   - Document-specific processing logic
   - Validation rules engine
   - Error handling and logging

3. **API Endpoints**
   - `GET /`: Serves the web interface
   - `POST /process-claim`: Processes uploaded documents
   - Static file serving for UI assets

4. **Validation System**
   - Patient information consistency
   - Date sequence validation
   - Provider information matching
   - Insurance details verification
   - Amount and charges validation

## Setup Instructions

1. **Prerequisites**
   ```bash
   # Windows
   winget install --id=Google.Tesseract-OCR  -e

   # Linux
   sudo apt-get install tesseract-ocr

   # macOS
   brew install tesseract
   ```

2. **Environment Setup**
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   # Windows
   .\venv\Scripts\activate
   # Linux/macOS
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Configuration**
   Create a `.env` file in the project root:
   ```env
   GOOGLE_API_KEY=your_api_key_here
   DEBUG=True
   ```

4. **Running the Application**
   ```bash
   uvicorn main:app --reload
   ```
   Access the application at http://localhost:8000

## API Documentation

### POST /process-claim
Process medical claim documents.

**Request**:
- Method: POST
- Content-Type: multipart/form-data
- Body: List of PDF files

**Response**:
```json
{
  "documents": [
    {
      "type": "bill",
      "filename": "medical_bill.pdf",
      "data": {
        "Total Amount": 1500.00,
        "Service Date": "2024-03-15",
        "Provider Name": "Example Hospital",
        ...
      }
    },
    {
      "type": "discharge",
      "filename": "discharge_summary.pdf",
      "data": {
        "Discharge Date": "2024-03-16",
        "Patient Name": "John Doe",
        ...
      }
    }
  ],
  "validation": {
    "is_valid": true,
    "missing_documents": [],
    "discrepancies": [],
    "warnings": [],
    "validation_details": {
      "patient_info": {...},
      "dates": {...},
      "provider_info": {...},
      "insurance_info": {...},
      "amounts": {...}
    }
  }
}
```

## Validation Rules

1. **Patient Information**
   - Name matching across documents
   - Patient ID consistency
   - Insurance information presence

2. **Dates**
   - Service date within admission period
   - Admission before discharge
   - Date format validation

3. **Provider Information**
   - Provider name matching
   - Address verification
   - Facility consistency

4. **Financial Information**
   - Total amount validation
   - Itemized charges sum
   - Payment status verification

## Error Handling

The application implements comprehensive error handling:
- PDF processing errors
- OCR failures
- AI model errors
- Validation failures
- File format issues

## Testing

Run the test suite:
```bash
pytest
```

## Limitations and Future Improvements

1. **Current Limitations**
   - PDF-only support
   - English language documents
   - Single-page processing
   - Basic OCR capabilities

2. **Planned Improvements**
   - Support for more document formats
   - Multi-language support
   - Advanced OCR with layout analysis
   - Machine learning for improved accuracy
   - Real-time processing status
   - Document storage integration
   - Batch processing capabilities

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - see LICENSE file for details 