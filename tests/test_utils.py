from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io

MOCK_BILL_CONTENT = """MEDICAL BILL
Hospital: General Medical Center
Patient Name: John Smith
Date of Service: 2024-03-15
Total Amount: $1,000.00
Insurance Provider: Health Plus
Policy Number: HP123456789
"""

MOCK_DISCHARGE_CONTENT = """DISCHARGE SUMMARY
Hospital: General Medical Center
Patient Name: John Smith
Admission Date: 2024-03-12
Discharge Date: 2024-03-15
Diagnosis: Acute Bronchitis
Treatment Summary: Antibiotic therapy, IV Fluids, Bronchodilators
Follow Up: Follow up with primary care in 1 week
"""

def create_test_pdf(content: str) -> bytes:
    """Create a test PDF file with the given content."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    y = 750  # Starting y position
    
    # Split content into lines and write each line
    for line in content.split('\n'):
        if line.strip():
            c.drawString(72, y, line)
            y -= 20  # Move down 20 points
            
    c.save()
    return buffer.getvalue()

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
