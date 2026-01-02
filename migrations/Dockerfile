
FROM python:3.10-slim

WORKDIR /app

COPY ./migrations/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./migrations/migrator.py .
COPY ./migrations/scripts/ ./scripts/

CMD ["python", "migrator.py"]
