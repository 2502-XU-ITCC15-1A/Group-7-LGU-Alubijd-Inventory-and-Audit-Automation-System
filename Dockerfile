FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install Flask-MySQLdb python-dotenv reportlab

COPY . .

ENV PORT=5000
ENV FLASK_APP=app.py

EXPOSE 5000

CMD ["python", "app.py"]
