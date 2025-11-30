
from config import Config
from slack_client import SlackClient
from pdf_processor import PDFProcessor


config = Config()
config.validate()

slack_client = SlackClient(config.SLACK_BOT_TOKEN)
channel_id = slack_client.get_channel_id(config.SLACK_CHANNEL)
files = slack_client.get_messages_with_pdfs(channel_id)
processing_files = slack_client.download_pdf_files(config.PDF_PATH, files)

pdf_processor = PDFProcessor(config.PDF_WORKERS)
processed_files = pdf_processor.process_files(processing_files)


