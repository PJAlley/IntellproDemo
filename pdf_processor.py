import logging
import pymupdf

from pathlib import Path
from multiprocessing import Pool
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

def process_pdf_file(file_obj: Dict[str, Any]) -> Dict[str, Any]:
    """
        Using PyMuPDF, opens the PDF file and extracts the text from it.
    """
    path = file_obj["local_path"]
    logger.info(f"Extracting text from {path.name}...")
    try:
        text = []
        with pymupdf.open(path) as doc:
            for page in doc:
                text.append(page.get_text())
        full_text = "/n".join(text)
    except Exception as e:
        logger.warning(f"Could not process PDF file {path.name}: {e}")
        full_text = ""

    # Write the resulting text to a text file with the same name.
    # Save the path and the resulting length of the text in addition
    # to the text itself for metadata extraction.
    text_file_path = path.with_suffix(".txt")
    with open(text_file_path, "w") as text_file:
        text_file.write(full_text)

    length = len(full_text)
    logger.info(f"Extracted {length} characters from {path.name}.")
    return {
        **file_obj,
        "text": full_text,
        "length": length,
        "text_file_path": text_file_path
    }

class PDFProcessor:
    """
        Processes PDF files using PyMuPDF.
    """
    def __init__(self, workers: int=4):
        self.pdf_workers = workers

    def process_files(self, files: List[ Dict[str, Any] ]) -> List[ Dict[str, Any] ]:
        """
            Takes a list of objects containing the PDF paths and processes them.
            There are workers that do the processing because it is CPU-intensive
            and processing them sequentially can take a very long time. Returns
            additional data about the document.
        """
        if not files:
            logger.info("No files to process.")
            return []
        
        logger.info(f"Extracting {len(files)} PDF files...")
        with Pool(processes=self.pdf_workers) as pool:
            processed_files = pool.map(process_pdf_file, files)

        return processed_files
