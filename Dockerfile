FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt *.py .env .

RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/pdfs

CMD ["python", "main.py"]
