
FROM python:3.10-slim

WORKDIR /app

COPY ./common /app/common

COPY ./frontend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./frontend/ .

EXPOSE 8080

CMD ["python", "app.py"]
