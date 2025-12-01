
import time

from openai import OpenAI, APIConnectionError, RateLimitError, APIError
from pydantic import BaseModel
from typing import Any, Dict, List

class Metadata(BaseModel):
    title: str
    publication_date: str

class MetadataExtractor:
    """Extracts document metadata using the Open AI API."""

    def __init__(self, ai_key: str, ai_model: str):
        self.client = OpenAI(api_key=ai_key)
        self.key = ai_key
        self.model = ai_model
    
    def extract_metadata(self, text: str, retries: int = 3) -> Dict[str, Any]:
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
                print(parsed_data)
                return parsed_data
            except APIConnectionError as e:
                print(f"The server could not be reached: {e}")
                time.sleep(1)
            except RateLimitError:
                print("Rate limit reached.")
                sleep_time = (attempt + 1) * 2
                print(f"Sleeping for {sleep_time} seconds...")
                time.sleep(sleep_time)
            except APIError as e:
                print(f"Error in API: {e}")
                time.sleep(attempt + 2)

        return {
            "title": None,
            "publication_date": None,
        }

    def process_files(self, files: List[ Dict[str, Any] ]):
        """
            Process the text files by calling extract_metadata for each file.
        """
        processed_files = []

        for file_data in files:
            filename = file_data["text_file_path"].name
            print(f"Extracting metadata from {filename}...")
            text = file_data["text"]
            if not text:
                print(f"No text in {filename}")
                metadata = {
                    "title": None,
                    "publication_date": None,
                }
            else:
                metadata = self.extract_metadata(text)
                if not metadata["title"]:
                    print(f"Could not extract metadata from {filename}.")
                else:
                    print(f"Extracted data from {filename}.")
            processed = {
                **file_data,
                **metadata
            }
            processed_files.append(processed)
            
            time.sleep(1)
            
        return processed_files