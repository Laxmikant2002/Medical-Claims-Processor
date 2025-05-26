from pathlib import Path
from test_utils import create_test_files

def main():
    """Create test PDF files for testing."""
    test_data_dir = Path(__file__).parent / "test_data"
    test_data_dir.mkdir(exist_ok=True)
    create_test_files(test_data_dir)
    print(f"Test files created in {test_data_dir}")

if __name__ == "__main__":
    main()
