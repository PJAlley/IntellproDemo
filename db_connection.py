import logging
import psycopg2
import time

logger = logging.getLogger(__name__)

from typing import Any, Dict, List, Optional

class DBConnection:
    def __init__(self, db_params: Dict[str, Any]):
        self.db_params = {
            "host": db_params.get("host", "localhost"),
            "port": db_params.get("port", 5432),
            "user": db_params.get("user", "postgres"),
            "password": db_params.get("password", "postgres"),
            "database": db_params.get("database", "postgres")
        }

        self.conn = psycopg2.connect(**self.db_params)
    
    def is_db_ready(self, max_attempts: int = 10, delay: int = 2):
        """
            Polls the database with a select statement.
        """
        for attempt in range(max_attempts):
            try:
                with self.conn.cursor() as cur:
                    cur.execute("SELECT VERSION()")
                return True
            except Exception as e:
                if attempt < max_attempts:
                    logger.warning(f"Database not ready yet (attempt {attempt + 1}/{max_attempts}).")
                    time.sleep(2)
                else:
                    logger.error("Failed to connect to database.")
                    return False

    
    def create_schema(self):
        """
            Creates the pdf_data table if it doesn't exist.
        """
        sql = """
        CREATE TABLE IF NOT EXISTS pdf_data (
            id SERIAL PRIMARY KEY,
            file_id varchar(20) UNIQUE NOT NULL,
            file_name varchar(100) NOT NULL,
            title varchar(500),
            publication_date varchar(50),
            url varchar(200),
            pdf_size INTEGER,
            pdf_path TEXT,
            text_length INTEGER,
            text_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql)
                self.conn.commit()
        except Exception as e:
            logger.error("Error creating schema: {e}")
            raise
        return
    
    def insert_pdf_record(self, data: Dict[str, Any]) -> Optional[int]:
        record = {
            "file_id": data["id"],
            "file_name": data["name"],
            "title": data["title"],
            "publication_date": data["publication_date"],
            "url": data["url"],
            "pdf_size": data["pdf_size"],
            "pdf_path": str(data["local_path"]),
            "text_length": data["length"],
            "text_path": str(data["text_file_path"]),
        }
        sql = """
        INSERT INTO pdf_data (
            file_id, file_name, title, publication_date, url,
            pdf_size, pdf_path, text_length, text_path
        ) VALUES (
            %(file_id)s, %(file_name)s, %(title)s, %(publication_date)s, %(url)s,
            %(pdf_size)s, %(pdf_path)s, %(text_length)s, %(text_path)s
        ) ON CONFLICT (file_id) DO UPDATE
            SET title = EXCLUDED.title,
            publication_date = EXCLUDED.publication_date,
            pdf_size = EXCLUDED.pdf_size,
            text_length = EXCLUDED.text_length,
            modified_at = CURRENT_TIMESTAMP
        RETURNING id
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, record)
                result = cur.fetchone()
                self.conn.commit()
                doc_id = result[0] if result else None
                logger.info(f"Successfully inserted/updated document {data["id"]} with id {doc_id}")
                return doc_id
        except Exception as e:
            logger.warning(f"Could not insert record: {e}")
            return None
        
    def bulk_insert_documents(self, data: List[ Dict[str, Any] ]):
        success = 0

        for rec in data:
            doc_id = self.insert_pdf_record(rec)
            if doc_id:
                success += 1
        return success
