"""
Sao lưu / tải bản sao lưu CSDL trên Backblaze B2 bằng tay (cùng cấu hình BACKUP_B2_* với scheduler).

  python -m scripts.sao_luu_b2 chay                 # sao lưu ngay + dọn bản cũ
  python -m scripts.sao_luu_b2 danh-sach            # liệt kê bản sao lưu trên B2 (cũ → mới)
  python -m scripts.sao_luu_b2 tai-ve [KHOA] [DICH] # tải về (mặc định bản mới nhất) để thử khôi phục

Khôi phục thử vào một CSDL TRỐNG (không phải CSDL đang chạy):
  pg_restore --no-owner --no-acl --dbname "$DB_THU" svws-YYYYMMDD-HHMMSS.dump
"""
import os
import sys
from datetime import datetime, timedelta, timezone

from app import sao_luu


def _gio_vn() -> datetime:
    off = int(os.environ.get("TZ_OFFSET_GIO") or 7)
    return datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=off)


def main(argv: list[str]) -> int:
    lenh = argv[0] if argv else "--help"
    if lenh in ("-h", "--help"):
        print(__doc__)
        return 0
    if not sao_luu.bat():
        print("Chưa cấu hình đủ BACKUP_B2_ENDPOINT / BACKUP_B2_KEY_ID / BACKUP_B2_APP_KEY / BACKUP_B2_BUCKET.")
        return 2
    cli, bucket = sao_luu._client()
    if lenh == "chay":
        kq = sao_luu.sao_luu(_gio_vn(), cli, bucket)
        print(f"Đã tải lên {kq['key']} ({kq['bytes']:,} byte); xóa {len(kq['da_xoa'])} bản cũ: {kq['da_xoa']}")
    elif lenh == "danh-sach":
        for k in sao_luu.danh_sach(cli, bucket):
            print(k)
    elif lenh == "tai-ve":
        keys = sao_luu.danh_sach(cli, bucket)
        khoa = argv[1] if len(argv) > 1 else (keys[-1] if keys else "")
        if not khoa:
            print("Chưa có bản sao lưu nào trên B2.")
            return 1
        dich = argv[2] if len(argv) > 2 else os.path.basename(khoa)
        cli.download_file(bucket, khoa, dich)
        print(f"Đã tải {khoa} → {dich} ({os.path.getsize(dich):,} byte)")
    else:
        print(f"Lệnh không hợp lệ: {lenh}\n{__doc__}")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
