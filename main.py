
from config import Config
from metadata_extractor import MetadataExtractor
from pdf_processor import PDFProcessor
from slack_client import SlackClient


config = Config()
config.validate()

slack_client = SlackClient(config.SLACK_BOT_TOKEN)
channel_id = slack_client.get_channel_id(config.SLACK_CHANNEL)
files = slack_client.get_messages_with_pdfs(channel_id)
downloaded_pdf_files = slack_client.download_pdf_files(config.PDF_PATH, files)

pdf_processor = PDFProcessor(config.PDF_WORKERS)
pdf_processed_files = pdf_processor.process_files(downloaded_pdf_files)

metadata_extractor = MetadataExtractor(config.OPEN_AI_KEY, config.OPEN_AI_MODEL)
data = metadata_extractor.process_files(pdf_processed_files)
