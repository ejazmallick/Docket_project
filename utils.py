import sys
from pathlib import Path
import logging
from PIL import Image
from pypdf import PdfReader

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent


INPUT_DIR = BASE_DIR / "input_pdfs"

STAMPS_DIR = BASE_DIR / "stamps"


OUTPUT_DIR = BASE_DIR / "Stamped Docs"


REPORTS_DIR = BASE_DIR / "reports"


LOGS_DIR = BASE_DIR / "logs"


LOG_FILE = LOGS_DIR / "app.log"



def ensure_directories():
    """
    Create all required project directories if they do not exist.
    """
    directories = [
        INPUT_DIR,
        STAMPS_DIR,
        OUTPUT_DIR,
        REPORTS_DIR,
        LOGS_DIR,
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def setup_logging():
    """
    Configure logging to:
    1. Console (CMD/Terminal)
    2. logs/app.log file
    """
   
    root_logger = logging.getLogger()
    if root_logger.handlers:
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )



def validate_stamp(stamp_path: Path):
    """
    Validate the stamp file.

    Supported formats:
    - PNG
    - JPG / JPEG
    - PDF

    Returns:
        (True, "Success") if valid
        (False, "Reason") if invalid
    """
    if not stamp_path.exists():
        return False, "Stamp missing"

    if not stamp_path.is_file():
        return False, "Invalid stamp path"

    extension = stamp_path.suffix.lower()

    if extension not in [".png", ".jpg", ".jpeg", ".pdf"]:
        return False, "Unsupported format"

    try:
        # Validate image files
        if extension in [".png", ".jpg", ".jpeg"]:
            with Image.open(stamp_path) as img:
                img.verify()

        # Validate PDF stamp
        elif extension == ".pdf":
            reader = PdfReader(str(stamp_path))
            if len(reader.pages) == 0:
                return False, "Corrupted stamp"

    except PermissionError:
        return False, "Permission denied"
    except Exception:
        return False, "Corrupted stamp"

    return True, "Success"



def validate_pdf(pdf_path: Path):
    """
    Validate a PDF file.

    Checks:
    - File exists
    - File is readable
    - Not encrypted
    - Not empty
    - Not corrupted

    Returns:
        (True, "Success") if valid
        (False, "Reason") if invalid
    """
    if not pdf_path.exists():
        return False, "File not found"

    if not pdf_path.is_file():
        return False, "Invalid path"

    try:
        reader = PdfReader(str(pdf_path))

        if reader.is_encrypted:
            return False, "Encrypted PDF"

        if len(reader.pages) == 0:
            return False, "Empty PDF"

    except PermissionError:
        return False, "Permission denied"
    except Exception:
        return False, "Corrupted PDF"

    return True, "Success"



def get_input_pdfs():
    """
    Return a list of all PDF files in the input_pdfs folder.
    Non-PDF files are ignored.
    """
    return sorted(
        [
            file
            for file in INPUT_DIR.iterdir()
            if file.is_file() and file.suffix.lower() == ".pdf"
        ]
    )