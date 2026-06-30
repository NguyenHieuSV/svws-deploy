FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
# psql để chạy migration .sql; font DejaVu cho xuất PDF (reportlab)
RUN apt-get update && apt-get install -y --no-install-recommends \
      postgresql-client fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
RUN chmod +x start.sh
EXPOSE 8000
CMD ["./start.sh"]
