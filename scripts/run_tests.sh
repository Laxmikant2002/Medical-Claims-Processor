#!/bin/bash

# Create test data if it doesn't exist
python tests/create_test_pdfs.py

# Run tests with coverage
pytest tests/ -v --cov=app --cov-report=term-missing 