import logging
import sys

from config import Config
from db_connection import DBConnection
from metadata_extractor import MetadataExtractor
from pdf_processor import PDFProcessor
from slack_client import SlackClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s : %(levelname)s : %(name)s : %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    try:
        logger.info("Document Ingestion Pipeline")
        config = Config()
        config.validate()

        db_params = {
            "host": config.POSTGRES_HOST,
            "port": config.POSTGRES_PORT,
            "user": config.POSTGRES_USER,
            "password": config.POSTGRES_PASSWORD,
            "database": config.POSTGRES_DB
        }

        logger.info("================ Setting up database ================")
        db = DBConnection(db_params)

        if not db.is_db_ready():
            logger.error("A database connection could not be established")
            raise
        db.create_schema()

        logger.info(f"Connected.")

        logger.info("================ Connecting to Slack ================")
        slack_client = SlackClient(config.SLACK_BOT_TOKEN)
        channel_id = slack_client.get_channel_id(config.SLACK_CHANNEL)
        logger.info(f"Retrieved Channel ID associated with {config.SLACK_CHANNEL}: {channel_id}")

        logger.info("================ Downloading PDF files ================")
        files = slack_client.get_messages_with_pdfs(channel_id)
        logger.info(f"Retrieved {len(files)} messages with PDF files.")

        downloaded_pdf_files = slack_client.download_pdf_files(config.PDF_PATH, files)
        logger.info(f"{len(downloaded_pdf_files)} PDF files downloaded.")

        logger.info("================ Processing PDF files ================")
        pdf_processor = PDFProcessor(config.PDF_WORKERS)
        pdf_processed_files = pdf_processor.process_files(downloaded_pdf_files)
        logger.info(f"Processed {len(pdf_processed_files)} PDF files.")

        logger.info("================ Extracting metadata ================")
        metadata_extractor = MetadataExtractor(config.OPEN_AI_KEY, config.OPEN_AI_MODEL)
        data = metadata_extractor.process_files(pdf_processed_files)
        logger.info(f"Extracted metadata from {len(data)} files.")

        logger.info("================ Writing records to the database ================")
        total_records_inserted = db.bulk_insert_documents(data)
        logger.info(f"{total_records_inserted} of {len(data)} records processed.")

        logger.info("Done.")
    except Exception as e:
        logger.error(f"Program failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
