import logging
import time

from openai import OpenAI, APIConnectionError, RateLimitError, APIError
from pydantic import BaseModel
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

"""
    The Metadata class is a data class where the results from the OpenAI prompt
    will place the result in.
"""
class Metadata(BaseModel):
    title: str
    publication_date: str

class MetadataExtractor:
    def __init__(self, ai_key: str, ai_model: str):
        """
        Initiialize the object with the OpenAI key and the AI model.
        """
        self.client = OpenAI(api_key=ai_key)
        self.key = ai_key
        self.model = ai_model

    def extract_metadata(self, text: str, retries: int = 3) -> Dict[str, Any]:
        """
            Extracts metadata from the supplied text using OpenAI. Places its findings
            in the Metadata class defined above. Returns the dictionary version of the object.
        """
        text_prompt = f"""
        Your job is to extract the document title and the publication date from provided text.

        Return an object with the following fields: "title" and "publication_date". If not found, return null.
        """
        user_prompt = f"""
        Extract the title and publication date from the provided text: {text}
        """

        for attempt in range(retries):
            try:
                response = self.client.responses.parse(
                    model=self.model,
                    input=[
                        {
                            "role": "system",
                            "content": text_prompt
                        },
                        {
                            "role": "user",
                            "content": user_prompt
                        }
                    ],
                    text_format=Metadata,
                )
                output = response.output_parsed

                parsed_data = {
                    "title": output.title,
                    "publication_date": output.publication_date
                }
                return parsed_data
            except APIConnectionError as e:
                logger.error(f"The server could not be reached: {e}")
                time.sleep(1)
            except RateLimitError:
                # For each time the rate limit is reached, add 2
                # seconds to the wait time
                logger.warning("Rate limit reached.")
                sleep_time = (attempt + 1) * 2
                logger.info(f"Sleeping for {sleep_time} seconds...")
                time.sleep(sleep_time)
            except APIError as e:
                logger.error(f"Error in API: {e}")
                time.sleep(attempt + 2)
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                return { "title": None, "publication_date": None }

        return { "title": None, "publication_date": None }

    def process_files(self, files: List[ Dict[str, Any] ]):
        """
            Process the text files by calling extract_metadata for each file.
            Returns added metadata fields for each file record.
        """
        processed_files = []

        for file_data in files:
            filename = file_data["text_file_path"].name
            logger.info(f"Extracting metadata from {filename}...")
            text = file_data["text"]
            if not text:
                logger.info(f"No text in {filename}")
                metadata = {
                    "title": None,
                    "publication_date": None,
                }
            else:
                metadata = self.extract_metadata(text)
                if not metadata["title"]:
                    logger.warning(f"Could not extract metadata from {filename}.")
                else:
                    logger.info(f"Extracted metadata from {filename}.")
            processed = {
                **file_data,
                **metadata
            }
            processed_files.append(processed)
            
            # To prevent hitting the rate limit, sleep for one second.
            time.sleep(1)
            
        return processed_files
