FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /data

ENV DB_PATH=/data/spam.db

EXPOSE 8000

CMD ["sh", "-c", "python init_db.py && python app.py"]
