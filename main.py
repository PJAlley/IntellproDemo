import os
import requests

import pymupdf

from pathlib import Path
from multiprocessing import Pool

from dotenv import load_dotenv
from slack_sdk import WebClient

load_dotenv()

slack_token = os.environ["SLACK_BOT_TOKEN"]
pdf_files = os.environ["PDF_PATH"]

# extract text
def process_pdf_file(file_obj):
    path = file_obj["local_path"]
    print(f"Extracting text from {path.name} ")
    text = []
    with pymupdf.open(path) as doc:
        for page in doc:
            text.append(page.get_text())
    full_text = chr(12).join(text)

    text_file_path = path.with_suffix(".txt")
    with open(text_file_path, "w") as text_file:
        text_file.write(full_text)
    return

client = WebClient(token=slack_token)
channels = client.conversations_list()

channel_id = None
# get channel id
for channel in channels["channels"]:
    if channel["name"] == "research":
        channel_id = channel["id"]
        break

print(channel_id)

# get messages with pdfs
messages = client.conversations_history(channel=channel_id)

files = []

for message in messages["messages"]:
    if "files" in message:
        for data in message["files"]:
            if data.get("filetype", None) == "pdf":
                files.append(data)

# download files
Path(pdf_files).mkdir(parents=True, exist_ok=True)

processing_files = []

for file_obj in files:
    link = file_obj["url_private"]
    file_id = file_obj["id"]
    name = file_obj["name"]
    headers = {'Authorization': f'Bearer {slack_token}'}
    pdf_req = requests.get(link, headers=headers, timeout=5)
    file_name = Path(f"{pdf_files}/{file_id}_{name}")
    if file_name.exists():
        print(f"skipping existing download: {file_name}")
    else:
        print(f"Downloading {file_name.name}")
        pdf = pdf_req.content
        with open(file_name, "wb") as out_file:
            out_file.write(pdf)
    
    obj = {
        "id": file_obj["id"],
        "name": file_obj["name"],
        "url": file_obj["url_private"],
        "size": file_obj["size"],
        "timestamp": file_obj["timestamp"],
        "local_path": file_name,

    }
    processing_files.append(obj)

with Pool(processes=5) as pool:
    processed_files = pool.map(process_pdf_file, processing_files)

print(processed_files)

