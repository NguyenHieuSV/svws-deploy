services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: svws
      POSTGRES_PASSWORD: svws
      POSTGRES_DB: svws
    ports: ["5432:5432"]
    volumes:
      - ./db/init:/docker-entrypoint-initdb.d:ro   # tự chạy 01..05 khi tạo mới
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U svws -d svws"]
      interval: 5s
      timeout: 3s
      retries: 10
volumes:
  pgdata:
