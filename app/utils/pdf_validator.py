from typing import Tuple, Optional
import PyPDF2
from io import BytesIO

def validate_pdf(content: bytes) -> Tuple[bool, Optional[str]]:
    """
    Validate if the content is a valid PDF file.
    Returns (is_valid, error_message)
    """
    if not content:
        return False, "Empty file"

    # Check PDF header
    if not content.startswith(b'%PDF-'):
        return False, "Not a PDF file (invalid header)"

    # Try parsing with PyPDF2
    try:
        pdf_file = BytesIO(content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        # Check if PDF has pages
        if len(pdf_reader.pages) == 0:
            return False, "PDF file has no pages"

        # Try to read first page
        first_page = pdf_reader.pages[0]
        text = first_page.extract_text()

        # Check if PDF is encrypted
        if pdf_reader.is_encrypted:
            return False, "PDF is encrypted"

        return True, None

    except PyPDF2.PdfReadError as e:
        return False, f"Invalid PDF structure: {str(e)}"
    except Exception as e:
        return False, f"Error validating PDF: {str(e)}"

def get_pdf_info(content: bytes) -> dict:
    """
    Get information about a PDF file.
    Returns a dictionary with PDF metadata.
    """
    try:
        pdf_file = BytesIO(content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        info = {
            "num_pages": len(pdf_reader.pages),
            "is_encrypted": pdf_reader.is_encrypted,
            "file_size": len(content),
            "metadata": pdf_reader.metadata or {},
            "has_text": any(page.extract_text().strip() for page in pdf_reader.pages)
        }
        
        return info
    except Exception as e:
        return {
            "error": str(e)
        } 