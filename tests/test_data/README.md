# Test Data Directory

This directory contains sample PDF files for testing the medical claims processor.

## Files

1. `sample_bill.pdf` - A sample medical bill with typical fields
2. `sample_discharge.pdf` - A sample discharge summary
3. `invalid.pdf` - An invalid PDF file for testing error handling
4. `scanned_bill.pdf` - A scanned medical bill for testing OCR
5. `multi_page.pdf` - A multi-page document for testing page handling

## Usage

These files are used by the test suite to verify:
- Document classification
- Information extraction
- Validation rules
- Error handling
- OCR capabilities

## Adding Test Files

When adding new test files:
1. Keep files small (< 100KB)
2. Include a variety of formats and layouts
3. Document the expected extraction results
4. Test both positive and negative cases 