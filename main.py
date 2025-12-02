import sys

from config import Config
from db_connection import DBConnection
from metadata_extractor import MetadataExtractor
from pdf_processor import PDFProcessor
from slack_client import SlackClient

try:
    config = Config()
    config.validate()

    db_params = {
        "host": config.POSTGRES_HOST,
        "port": config.POSTGRES_PORT,
        "user": config.POSTGRES_USER,
        "password": config.POSTGRES_PASSWORD,
        "database": config.POSTGRES_DB
    }

    print("Setting up database...")
    db = DBConnection(db_params)

    if not db.is_db_ready():
        print("A database connection could not be established")
        raise
    db.create_schema()

    print(f"Connected.")

    print("\nConnecting to Slack...")
    slack_client = SlackClient(config.SLACK_BOT_TOKEN)
    channel_id = slack_client.get_channel_id(config.SLACK_CHANNEL)
    print(f"Retrieved Channel ID associated with {config.SLACK_CHANNEL}: {channel_id}")

    print("\nDownloading PDF files...")
    files = slack_client.get_messages_with_pdfs(channel_id)
    print(f"Retrieved {len(files)} messages with PDF files.")

    downloaded_pdf_files = slack_client.download_pdf_files(config.PDF_PATH, files)
    print(f"{len(downloaded_pdf_files)} PDF files downloaded.")

    print("\nProcessing PDF files...")
    pdf_processor = PDFProcessor(config.PDF_WORKERS)
    pdf_processed_files = pdf_processor.process_files(downloaded_pdf_files)
    print(f"Processed {len(pdf_processed_files)} PDF files.")

    print("\nExtracting metadata...")
    metadata_extractor = MetadataExtractor(config.OPEN_AI_KEY, config.OPEN_AI_MODEL)
    data = metadata_extractor.process_files(pdf_processed_files)
    print(f"Extracted metadata from {len(data)} files.")

    print("\nWriting records to the database...")
    total_records_inserted = db.bulk_insert_documents(data)
    print(f"{total_records_inserted} of {len(data)} records processed.")

    print("\nDone.")
except Exception as e:
    print(f"Program failed with error: {e}")
    sys.exit(1)
