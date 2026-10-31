FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
# psql / pg_dump bản 18 lấy từ kho PGDG (apt.postgresql.org): gói postgresql-client của Debian trixie
# chỉ là bản 17, không pg_dump được máy chủ PostgreSQL 18 trên Render (app/sao_luu_service.py).
# start.sh vẫn gọi psql như cũ (pg_wrapper của postgresql-client-common đặt psql/pg_dump trên PATH).
# - Khóa PGDG dạng ASCII (.asc) để ở /usr/share/keyrings/, apt đọc thẳng qua signed-by → không cần gnupg.
# - curl + ca-certificates chỉ cần lúc build; curl gỡ sau khi cài xong.
# - Tên bản Debian (trixie / bookworm…) đọc từ /etc/os-release lúc build để chọn đúng suite "<tên>-pgdg".
RUN apt-get update && apt-get install -y --no-install-recommends \
      curl ca-certificates fonts-dejavu-core \
    && install -d -m 0755 /usr/share/keyrings \
    && curl -fsSL -o /usr/share/keyrings/postgresql-archive-keyring.asc \
         https://www.postgresql.org/media/keys/ACCC4CF8.asc \
    && echo "deb [signed-by=/usr/share/keyrings/postgresql-archive-keyring.asc] https://apt.postgresql.org/pub/repos/apt $(. /etc/os-release && echo "$VERSION_CODENAME")-pgdg main" \
         > /etc/apt/sources.list.d/pgdg.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends postgresql-client-18 \
    && apt-get purge -y --auto-remove curl \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
RUN sed -i 's/\r$//' start.sh && chmod +x start.sh
EXPOSE 8000
CMD ["bash", "start.sh"]

