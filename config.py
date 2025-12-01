import os

from dotenv import load_dotenv

load_dotenv()

class Config:
    SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
    SLACK_CHANNEL = os.getenv("SLACK_CHANNEL", "")

    OPEN_AI_KEY = os.getenv("OPEN_AI_KEY", "")
    OPEN_AI_MODEL = os.getenv("OPEN_AI_MODEL", "gpt-4.1-mini")

    PDF_PATH = os.getenv("PDF_PATH", "./pdfs")
    PDF_WORKERS = int(os.getenv("PDF_WORKERS", 3))

    def validate(self):
        if not self.SLACK_BOT_TOKEN:
            raise ValueError("SLack Bot Token is required.")
        if not self.SLACK_CHANNEL:
            raise ValueError("SLack Channel is required.")
        if not self.OPEN_AI_KEY:
            raise ValueError("OpenAI key is required.")
