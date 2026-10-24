FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
# pg_dump/psql phải CÙNG hoặc MỚI HƠN Postgres trên Render (đang là 18) — gói postgresql-client
# của Debian cũ hơn, nên cài từ kho chính thức apt.postgresql.org (PGDG).
ARG PG_MAJOR=18
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl fonts-dejavu-core \
    && install -d /usr/share/postgresql-common/pgdg \
    && curl -fsSL -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc \
         https://www.postgresql.org/media/keys/ACCC4CF8.asc \
    && . /etc/os-release \
    && echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc] https://apt.postgresql.org/pub/repos/apt ${VERSION_CODENAME}-pgdg main" \
         > /etc/apt/sources.list.d/pgdg.list \
    && apt-get update && apt-get install -y --no-install-recommends postgresql-client-${PG_MAJOR} \
    && pg_dump --version | grep -q " ${PG_MAJOR}\." \
    && apt-get purge -y curl && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
RUN sed -i 's/\r$//' start.sh && chmod +x start.sh
EXPOSE 8000
CMD ["bash", "start.sh"]
