import os
import sys
from pypdf import PdfReader
import json
from resumeparser import ats_extractor

sys.path.insert(0, os.path.abspath(os.getcwd()))

UPLOAD_PATH = r"__DATA__"

def ats(file_path):
    doc_path = os.path.join(UPLOAD_PATH, file_path)
    data = _read_file_from_path(doc_path)
    processed_data = ats_extractor(data)
    return json.loads(processed_data)

def _read_file_from_path(path):
    reader = PdfReader(path)
    data = ""

    for page_no in range(len(reader.pages)):
        page = reader.pages[page_no]
        data += page.extract_text()

    return data

if __name__ == "__main__":
    file_name = "/Users/danieldas/Downloads/prajeinresume.pdf"  
    result = ats(file_name)
    print(result)
