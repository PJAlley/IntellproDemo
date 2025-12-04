# IntellproDemo
Loads and extracts PDFs from a Slack channel and loads text in a database

## Overview

The Document Ingestion Pipeline process financial and research PDF files and extracts metadata.
1. Fetches and downloads PDF files from a Slack channel
2. Extracts the text from the PDF to a text file using PyMuPDF
3. Extracts the metadata (title and publication date) from the text using OpenAI
4. Writes the metadata into a database table in Postgres

## Requirements
- Slack Bot token
- OpenAI key
- Docker
- Docker Compose

## Slack App Setup
1. Go to [https://api.slack.com/apps](https://api.slack.com/apps).
2. Click on “Create App”, and choose “From Scratch”.
3. In **App Name**, give it a name and in the workspace, choose Intellpro Demo.
4. The page should lead you to the bot’s Basic Information.
5. On the left, there are a list of features. Click on **Scopes**.
6. The bot only needs to view and download files. Add the following to Bot Token Scopes:
   - `channels:history` - to read messages
   - `channels:read` - to get channel information such as Channel IDs
   - `files:read` - to download the PDF files
7. Click on Install to IntellPro Demo. You should see a new tab with the link to Allow install. Click on Allow.
8. Back to the Oauth & Permissions page, you should see a Bot User OAuth token (starting with `xoxb-`). Note that token and save it. You will place it in an .env file.
9. Go to the IntellPro Demo Slack channel. You should see the app installed.
10. Lastly, go to the research channel and type `/invite <name of bot>`.

## Setting up the Application
1. Download the files locally
```
git clone https://github.com/PJAlley/IntellproDemo.git
cd IntellproDemo

cp .env.example .env
```
2. Set environment variables. The default database credentials will work with Docker Compose. The Open AI model can be blank as it will use the model `gpt-4.1-mini`.
```
# Slack variables
SLACK_BOT_TOKEN=slack-bot-token
SLACK_CHANNEL=research

# OpenAI variables
OPEN_AI_KEY=open-api-key
OPEN_AI_MODEL=open-api-model

PDF_PATH=./pdfs
PDF_WORKERS=4

POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=postgres
```
3. Run the app
```
# Build and run the app
docker compose up --build
```
The logs will be placed in `stdout` and in a file called `app.log`.
It can be run many times, as it is idempotent. Files with the same file ID (see DB Schema below) will have their information updated.

## Architecture Decisions

### Database Schema
```sql
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
```
- `file_id` is the Slack File ID. It's a unique key.
- `file_name` is the name of the file.
- `title` is the title that OpenAI extracted
- `publication_date` is a string and not a datetime object. 
- `url` - the Slack URL
- `pdf_path` and `text_path` - the paths of the PDF and text files, respectively
- `created_at` and `modified_at` for bookkeeping

### Multiprocessing strategy
Use the `multiprocessing` module with its process pooling
```python
from multiprocessing import Pool

with Pool(processes=4) as pool:
    processed_files = pool.map(process_pdf_file, files)
```
- Extracting text from PDF is CPU-intensive
- We use 4 workers (configurable in .env file under `PDF_WORKERS`)
- Each worker is its own process with its own GIL
- extracts text from one PDF file using PyMuPDF
- Speeds up PDF processing time by using concurrency, however adds more memory

### Error Handling
#### DB Connection
- Fail if the DB is not ready after 10 attempts as the DB conncetion is critical.
- Fail if the DB schema cannot be created, which is critical to insert records.
- Warn if the record cannot be inserted. Log it and go to the next record.

#### Slack Client
- Fail if the Slack Channel is not found. The Slack channel is required to download PDFs.
- Warn if a download fails.

#### PDF Processor
- Warn if a PDF file cannot be processed into text.

#### Metadata Extractor
- Most failures to extract data result in a retry, up to the default of 3 attempts.
- If the rate limit has been reached, the program waits in successive 2-second increments (2 seconds after 1st attempt, 4 secs. after 2nd, 6 secs., etc.)
- If the API cannot be reached, it waits one second before attempting to connect again.
- If an API error, wait for at least 2 seconds before trying again.
- Unexpected errors are automatic failures.

### Trade-offs
- Using 4 workers for PDF extraction into text as it is a balance between time and memory. Most CPUs have 4 cores.
- The `publication_date` field in the `pdf_data` table is a string instead of a datatime object. There are many different varieties of dates in the publications and creating datetime objects would be too complicated.

### Future Improvements

#### What would I do with more time?
1. Create an endpoint to query processed files
2. Imcremental processing (only process new files from the channel)
3. Pagination (the supplied channel has a few messages. Other channels can have histories going back months if not years.)
4. Unit tests

#### Scaling to 10,000 PDFs
1. Using a task queue such as Celery
2. Saving PDF files into S3
3. Bulk inserts into database table for faster inserts
4. Batch processing

#### Monitoring
1. Datadog for easier log management
2. Dashboards for visualization
