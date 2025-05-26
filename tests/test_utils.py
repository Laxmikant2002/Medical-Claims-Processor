import tempfile
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io

MOCK_BILL_CONTENT = """
MEDICAL BILL

Patient Name: John Doe
Service Date: 2024-03-15
Total Amount: $1,500.00

Services:
1. Consultation - $200
2. X-Ray - $300
3. Laboratory Tests - $1,000
"""

MOCK_DISCHARGE_CONTENT = """
DISCHARGE SUMMARY

Patient: John Doe
Admission Date: 2024-03-14
Discharge Date: 2024-03-16

Diagnosis:
- Acute bronchitis
- Mild dehydration

Treatment:
- Antibiotics
- IV Fluids
"""

def create_test_pdf(content: str) -> str:
    """Create a test PDF file with the given content."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
        # Create a simple PDF file with the content
        pdf_content = f"%PDF-1.4\n{content}\n%%EOF"
        temp_file.write(pdf_content.encode())
        return temp_file.name

def create_test_files(output_dir):
    """Create test PDF files in the specified directory."""
    # Create bill PDF
    bill_path = output_dir / "sample_bill.pdf"
    bill_path.write_bytes(create_test_pdf(MOCK_BILL_CONTENT))
    
    # Create discharge PDF
    discharge_path = output_dir / "sample_discharge.pdf"
    discharge_path.write_bytes(create_test_pdf(MOCK_DISCHARGE_CONTENT))
    
    # Create invalid PDF
    invalid_path = output_dir / "invalid.pdf"
    invalid_path.write_bytes(b"Not a valid PDF")
