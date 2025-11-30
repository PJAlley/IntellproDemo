import requests

from pathlib import Path
from typing import Dict, List, Any
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


class SlackClient:
    def __init__(self, slack_token: str):
        self.client = WebClient(token=slack_token)
        self.token = slack_token
    
    def get_channel_id(self, channel) -> str:
        print(f"Retrieving ID associated with the {channel} channel...")
        try:
            channels = self.client.conversations_list()

            for channel in channels["channels"]:
                if channel["name"] == "research":
                    return channel["id"]
                    break
        except SlackApiError as e:
            print(f"Slack channel not found: {channel}")
            raise
    
    def get_messages_with_pdfs(self, channel_id: str) -> List[ Dict[str, Any] ]:
        messages = self.client.conversations_history(channel=channel_id)
        files = []

        for message in messages["messages"]:
            if "files" in message:
                for data in message["files"]:
                    if data.get("filetype", None) == "pdf":
                        files.append(data)
        return files
    
    def download_pdf_files(self, directory: str, files: List[ Dict[str, Any] ]) -> List[ Dict[str, Any] ]:
        pdf_path = Path(directory)
        pdf_path.mkdir(parents=True, exist_ok=True)

        processing_files = []

        for file_obj in files:
            try:
                link = file_obj["url_private"]
                file_id = file_obj["id"]
                name = file_obj["name"]

                headers = {"Authorization": f"Bearer {self.token}"}
                pdf_req = requests.get(link, headers=headers, timeout=5)

                file_name = Path(f"{directory}/{file_id}_{name}")
                if file_name.exists():
                    print(f"Skipping existing download: {file_name.name}")
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
            except Exception as e:
                print(f"Failed to download file {name}: {e}")
                continue
        return processing_files

