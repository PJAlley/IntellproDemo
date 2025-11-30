import os

from dotenv import load_dotenv

load_dotenv()

class Config:
    SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
    SLACK_CHANNEL = os.getenv("SLACK_CHANNEL", "")

    OPEN_API_KEY = os.getenv("OPEN_API_KEY", "")

    PDF_PATH = os.getenv("PDF_PATH", "./pdfs")
    PDF_WORKERS = int(os.getenv("PDF_WORKERS", 5))

    def validate(self):
        if not self.SLACK_BOT_TOKEN:
            raise ValueError("SLack Bot Token is required.")
        if not self.SLACK_CHANNEL:
            raise ValueError("SLack Channel is required.")
        if not self.OPEN_API_KEY:
            raise ValueError("Open AI key is required.")
