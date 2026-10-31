"""💾 KHÔI PHỤC CSDL SVWS từ file ZIP sao lưu (tạo bởi app/sao_luu_service.py — tải ở Cấu hình → 💾 Sao lưu dữ liệu, chỉ CEO).

Chạy trên máy có Python (cài requirements.txt) và psql, ví dụ laptop anh Hiếu hoặc một service tạm trên Render:
  python -m scripts.khoi_phuc_sao_luu svws-20261031-020000.zip --database-url postgresql://user:pass@host:5432/db --yes

Các bước:
  1) Tạo schema bằng các file schema/*.sql trong ZIP (thứ tự sort -V, ghi bảng _migrations) — bỏ qua với --khong-tao-schema
     (dùng khi CSDL đích đã chạy start.sh).
  2) XÓA dữ liệu hiện có của các bảng có trong ZIP rồi nạp lại từ CSV (tắt kiểm FK, chỉnh lại sequence id).
  3) In số dòng từng bảng để đối chiếu với manifest.
Có pg_dump.dump trong ZIP và máy có pg_restore cùng phiên bản thì cách nhanh hơn:  pg_restore --no-owner -d <url> pg_dump.dump
CẢNH BÁO: lệnh này GHI ĐÈ dữ liệu trong CSDL đích — chỉ trỏ vào CSDL mới hoặc CSDL muốn khôi phục.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile


def _sort_v(ten: str):
    m = re.match(r"(\d+)", ten)
    return (int(m.group(1)) if m else 10 ** 9, ten)


def tao_schema(url_pg: str, thu_muc_sql: str) -> int:
    """Chạy từng file .sql theo sort -V bằng psql (như start.sh) và ghi _migrations. Trả số file đã áp."""
    psql = shutil.which("psql")
    if not psql:
        raise SystemExit("Không tìm thấy psql — cài PostgreSQL client hoặc chạy với --khong-tao-schema sau khi start.sh đã tạo schema")
    subprocess.run([psql, url_pg, "-v", "ON_ERROR_STOP=1", "-c",
                    "CREATE TABLE IF NOT EXISTS _migrations(ten text primary key, ap timestamptz default now())"],
                   check=True, capture_output=True, text=True)
    n = 0
    for f in sorted(os.listdir(thu_muc_sql), key=_sort_v):
        if not f.endswith(".sql"):
            continue
        da = subprocess.run([psql, url_pg, "-tA", "-c", f"SELECT 1 FROM _migrations WHERE ten='{f}'"],
                            capture_output=True, text=True).stdout.strip()
        if da == "1":
            continue
        print(f"    áp dụng {f}")
        subprocess.run([psql, url_pg, "-v", "ON_ERROR_STOP=1", "-f", os.path.join(thu_muc_sql, f)], check=True,
                       capture_output=True, text=True)
        subprocess.run([psql, url_pg, "-c", f"INSERT INTO _migrations(ten) VALUES ('{f}')"], check=True,
                       capture_output=True, text=True)
        n += 1
    return n


def main():
    ap = argparse.ArgumentParser(description="Khôi phục CSDL SVWS từ ZIP sao lưu")
    ap.add_argument("zip")
    ap.add_argument("--database-url", default=os.environ.get("DATABASE_URL", ""))
    ap.add_argument("--khong-tao-schema", action="store_true", help="CSDL đích đã có schema (đã chạy start.sh)")
    ap.add_argument("--giu-du-lieu-cu", action="store_true", help="không xóa dữ liệu đang có trước khi nạp (dễ trùng khóa)")
    ap.add_argument("--yes", action="store_true", help="không hỏi xác nhận")
    a = ap.parse_args()
    if not a.database_url:
        raise SystemExit("Thiếu --database-url (hoặc biến môi trường DATABASE_URL)")
    url = a.database_url
    for x, y in (("postgresql+psycopg2://", "postgresql://"), ("postgres://", "postgresql://")):
        if url.startswith(x):
            url = y + url[len(x):]
    with zipfile.ZipFile(a.zip) as zf:
        mf = json.loads(zf.read("manifest.json"))
        print(f"Bản sao lưu: tạo lúc {mf.get('tao_luc')} · app {mf.get('app_build')} · {mf.get('so_bang')} bảng · "
              f"{mf.get('so_dong')} dòng · {mf.get('pg_dump')}")
        if not a.yes:
            tl = input(f"GHI ĐÈ dữ liệu trong CSDL đích {url.split('@')[-1]} ? gõ 'co' để tiếp tục: ")
            if tl.strip().lower() != "co":
                raise SystemExit("Đã hủy")
        tmp = tempfile.mkdtemp(prefix="svws_khoi_phuc_")
        try:
            if not a.khong_tao_schema:
                zf.extractall(tmp, [n for n in zf.namelist() if n.startswith("schema/") and n.endswith(".sql")])
                n = tao_schema(url, os.path.join(tmp, "schema"))
                print(f"==> Schema: đã áp {n} file migration")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    os.environ["DATABASE_URL"] = url
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from sqlalchemy import create_engine
    from app.sao_luu_service import nap_zip
    eng = create_engine(url.replace("postgresql://", "postgresql+psycopg2://"), future=True)
    kq = nap_zip(eng, a.zip, xoa_du_lieu_cu=not a.giu_du_lieu_cu)
    print("==> Đã nạp:")
    for ten, n in sorted(kq["bang"].items()):
        goc = mf.get("bang", {}).get(ten)
        print(f"    {ten:40s} {n:>8d}" + ("" if goc == n else f"   (manifest {goc})"))
    if kq["bo_qua"]:
        print("==> Bảng trong ZIP nhưng CSDL đích không có (bỏ qua):", ", ".join(kq["bo_qua"]))
    print("XONG — khởi động lại app để chắc chắn mọi kết nối dùng dữ liệu mới.")


if __name__ == "__main__":
    main()
