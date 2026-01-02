
FROM python:3.10-slim

WORKDIR /app

COPY ./common /app/common

COPY ./backend/readers_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./backend/readers_service/ .

EXPOSE 5000

CMD ["python", "app.py"]
