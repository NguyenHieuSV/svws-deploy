#!/usr/bin/env bash
set -e
DBURL=$(echo "${DATABASE_URL:-postgresql://svws:svws@localhost:5432/svws}" \
  | sed 's#postgresql+psycopg2://#postgresql://#; s#^postgres://#postgresql://#')

echo "==> Áp dụng migrations (db/init/*.sql)"
psql "$DBURL" -c "CREATE TABLE IF NOT EXISTS _migrations(ten text primary key, ap timestamptz default now())" >/dev/null
for f in $(ls db/init/*.sql | sort); do
  name=$(basename "$f")
  applied=$(psql "$DBURL" -tA -c "SELECT 1 FROM _migrations WHERE ten='$name'")
  if [ "$applied" = "1" ]; then
    echo "    bỏ qua  $name"
  else
    echo "    áp dụng $name"
    psql "$DBURL" -v ON_ERROR_STOP=1 -f "$f"
    psql "$DBURL" -c "INSERT INTO _migrations(ten) VALUES ('$name')" >/dev/null
  fi
done

echo "==> Khởi động API + giao diện trên cổng ${PORT:-8000}"
if [ "${SEED_DEMO:-1}" != "0" ]; then
  echo "==> Tạo 13 tài khoản demo (mật khẩu: matkhau123) — đặt SEED_DEMO=0 để tắt"
  python -m scripts.tao_user_demo || true
fi
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
