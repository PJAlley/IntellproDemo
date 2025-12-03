FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY *.py .env .

RUN mkdir -p /app/pdfs

CMD ["python", "main.py"]
