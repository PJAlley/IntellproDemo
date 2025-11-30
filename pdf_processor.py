import pymupdf

from pathlib import Path
from multiprocessing import Pool
from typing import Dict, List, Any

def process_pdf_file(file_obj: Dict[str, Any]) -> Dict[str, Any]:
    path = file_obj["local_path"]
    print(f"Extracting text from {path.name}...")
    try:
        text = []
        with pymupdf.open(path) as doc:
            for page in doc:
                text.append(page.get_text())
        full_text = "/n".join(text)
    except Exception as e:
        print(f"Could not process PDF file {path.name}: {e}")
        full_text = ""

    text_file_path = path.with_suffix(".txt")
    with open(text_file_path, "w") as text_file:
        text_file.write(full_text)
    length = len(full_text)
    print(f"Extracted {length} characters from {path.name}.")
    return {
        **file_obj,
        "text": full_text,
        "length": length,
        "text_file_path": text_file_path
    }

class PDFProcessor:
    def __init__(self, workers: int=5):
        self.pdf_workers = int(workers)

    def process_files(self, files: List[ Dict[str, Any] ]) -> List[ Dict[str, Any] ]:
        if not files:
            print("No files to process.")
            return []
        
        print(f"Extracting {len(files)} PDF files...")
        with Pool(processes=self.pdf_workers) as pool:
            processed_files = pool.map(process_pdf_file, files)

        print(f"Processed {len(processed_files)} PDF files.")
        return processed_files 