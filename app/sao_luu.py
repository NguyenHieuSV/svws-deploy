"""
Sao lưu CSDL lên Backblaze B2 — lớp sao lưu THỨ HAI, ngoài Recovery của gói Render (T102 · PR-0).

  • pg_dump (định dạng custom, nén sẵn) toàn bộ DATABASE_URL → đẩy lên bucket B2 qua API
    tương thích S3 (boto3 đã có trong requirements) → giữ BACKUP_KEEP bản mới nhất (mặc định 14).
  • Chạy trong luồng scheduler sẵn có (app/scheduler.py), mỗi ngày một lần từ BACKUP_GIO
    (giờ Việt Nam, mặc định 2h). Mốc "hôm nay đã sao lưu" chính là TÊN TỆP trên B2
    (svws-YYYYMMDD-HHMMSS.dump) nên khởi động lại app không chạy trùng, app ngủ qua giờ hẹn
    thì lần thức đầu tiên chạy bù.
  • Chưa cấu hình đủ biến BACKUP_B2_* → tắt hẳn, không ảnh hưởng gì.

ENV:  BACKUP_B2_ENDPOINT   vd https://s3.us-west-004.backblazeb2.com
      BACKUP_B2_KEY_ID     keyID của Application Key (chỉ cấp quyền cho bucket sao lưu)
      BACKUP_B2_APP_KEY    applicationKey
      BACKUP_B2_BUCKET     bucket RIÊNG cho sao lưu (private), KHÔNG dùng chung bucket tệp R2_*
      BACKUP_B2_REGION     vd us-west-004 (mặc định lấy từ endpoint)
      BACKUP_B2_PREFIX     thư mục trong bucket (mặc định "pg-dump/")
      BACKUP_KEEP          số bản giữ lại (mặc định 14)
      BACKUP_GIO           giờ chạy hằng ngày, giờ VN (mặc định 2)

Chạy tay / thử khôi phục: python -m scripts.sao_luu_b2 --help  (xem HUONG_DAN_SAO_LUU.md)
"""
import os
import re
import subprocess
import tempfile
import threading
import time
from datetime import datetime

_TEN_RE = re.compile(r"svws-(\d{8})-(\d{6})\.dump$")
_khoa = threading.Lock()
_loi_luc = 0.0          # lần lỗi gần nhất — chờ 1 giờ rồi mới thử lại, tránh chạy dồn mỗi 5 phút
_CHO_SAU_LOI = 3600


def _cfg() -> dict:
    g = lambda k, d="": (os.environ.get(k) or d).strip()  # noqa: E731
    endpoint = g("BACKUP_B2_ENDPOINT")
    m = re.search(r"s3\.([a-z0-9-]+)\.backblazeb2\.com", endpoint)
    prefix = g("BACKUP_B2_PREFIX", "pg-dump/")
    if prefix and not prefix.endswith("/"):
        prefix += "/"
    return {
        "endpoint": endpoint,
        "key": g("BACKUP_B2_KEY_ID"),
        "secret": g("BACKUP_B2_APP_KEY"),
        "bucket": g("BACKUP_B2_BUCKET"),
        "region": g("BACKUP_B2_REGION") or (m.group(1) if m else "us-east-1"),
        "prefix": prefix,
        "keep": max(1, int(g("BACKUP_KEEP", "14") or 14)),
        "gio": int(g("BACKUP_GIO", "2") or 2),
    }


def bat() -> bool:
    """True khi đã cấu hình đủ 4 biến BACKUP_B2_ENDPOINT/KEY_ID/APP_KEY/BUCKET."""
    c = _cfg()
    return all([c["endpoint"], c["key"], c["secret"], c["bucket"]])


def _client():
    import boto3  # nạp trễ — chỉ khi bật sao lưu
    from botocore.config import Config
    c = _cfg()
    cli = boto3.client("s3", endpoint_url=c["endpoint"], aws_access_key_id=c["key"],
                       aws_secret_access_key=c["secret"], region_name=c["region"],
                       config=Config(signature_version="s3v4"))
    return cli, c["bucket"]


def db_url() -> str:
    """DATABASE_URL dạng libpq mà pg_dump/pg_restore hiểu (bỏ '+psycopg2', 'postgres://')."""
    url = os.environ.get("DATABASE_URL") or ""
    if not url:
        from .config import settings
        url = settings.database_url
    url = url.replace("postgresql+psycopg2://", "postgresql://", 1)
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    return url


def ten_ban_sao(now: datetime, prefix: str | None = None) -> str:
    prefix = _cfg()["prefix"] if prefix is None else prefix
    return f"{prefix}svws-{now:%Y%m%d-%H%M%S}.dump"


def chay_pg_dump(dich: str) -> None:
    """pg_dump -Fc; lỗi (sai mật khẩu, lệch phiên bản client/server…) → RuntimeError kèm stderr."""
    r = subprocess.run(["pg_dump", "--format=custom", "--no-owner", "--no-acl",
                        "--file", dich, "--dbname", db_url()],
                       capture_output=True, text=True, timeout=3600)
    if r.returncode != 0:
        raise RuntimeError(f"pg_dump lỗi ({r.returncode}): {r.stderr.strip()[:500]}")


def danh_sach(cli, bucket: str, prefix: str | None = None) -> list[str]:
    """Các bản sao lưu trên B2, CŨ → MỚI (tên tệp chứa thời điểm nên sắp theo tên là đủ)."""
    prefix = _cfg()["prefix"] if prefix is None else prefix
    keys, token = [], None
    while True:
        kw = {"Bucket": bucket, "Prefix": prefix}
        if token:
            kw["ContinuationToken"] = token
        r = cli.list_objects_v2(**kw)
        keys += [o["Key"] for o in r.get("Contents", []) if _TEN_RE.search(o["Key"])]
        if not r.get("IsTruncated"):
            break
        token = r.get("NextContinuationToken")
    return sorted(keys, key=lambda k: _TEN_RE.search(k).groups())


def _xoa_han(cli, bucket: str, key: str) -> None:
    """Xóa THẬT mọi phiên bản của tệp. B2 mặc định giữ mọi phiên bản: delete_object thường
    chỉ tạo 'hide marker', dung lượng vẫn tăng — nên xóa theo VersionId."""
    try:
        r = cli.list_object_versions(Bucket=bucket, Prefix=key)
        ds = [v for v in r.get("Versions", []) + r.get("DeleteMarkers", []) if v["Key"] == key]
    except Exception:
        ds = []
    if not ds:
        cli.delete_object(Bucket=bucket, Key=key)
    for v in ds:
        cli.delete_object(Bucket=bucket, Key=key, VersionId=v["VersionId"])


def don_dep(cli, bucket: str, keep: int | None = None, prefix: str | None = None) -> list[str]:
    """Giữ `keep` bản mới nhất, xóa phần còn lại. Trả về danh sách khóa đã xóa."""
    keep = max(1, _cfg()["keep"] if keep is None else keep)
    keys = danh_sach(cli, bucket, prefix)
    cu = keys[:-keep] if len(keys) > keep else []
    for k in cu:
        _xoa_han(cli, bucket, k)
    return cu


def da_sao_luu_ngay(cli, bucket: str, ngay: datetime, prefix: str | None = None) -> bool:
    return any(_TEN_RE.search(k).group(1) == f"{ngay:%Y%m%d}" for k in danh_sach(cli, bucket, prefix))


def sao_luu(now: datetime, cli=None, bucket: str | None = None, dump=chay_pg_dump) -> dict:
    """Một lần sao lưu đầy đủ: dump → tải lên → dọn bản cũ. `now` là giờ Việt Nam."""
    if cli is None:
        cli, bucket = _client()
    key = ten_ban_sao(now)
    fd, tmp = tempfile.mkstemp(suffix=".dump")
    os.close(fd)
    try:
        dump(tmp)
        n = os.path.getsize(tmp)
        if n == 0:
            raise RuntimeError("pg_dump tạo tệp rỗng — hủy, không tải lên.")
        cli.upload_file(tmp, bucket, key)
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass
    return {"key": key, "bytes": n, "da_xoa": don_dep(cli, bucket)}


def den_han(now: datetime) -> bool:
    """Scheduler hỏi mỗi vòng: đã bật, đã qua BACKUP_GIO, hôm nay chưa có bản nào, không vừa lỗi."""
    if not bat() or now.hour < _cfg()["gio"] or _khoa.locked():
        return False
    if time.time() - _loi_luc < _CHO_SAU_LOI:
        return False
    cli, bucket = _client()
    return not da_sao_luu_ngay(cli, bucket, now)


def chay_nen(now: datetime) -> None:
    """Chạy ở luồng riêng (dump có thể mất vài phút) — không chặn vòng scheduler."""
    def _job():
        global _loi_luc
        if not _khoa.acquire(blocking=False):
            return
        try:
            kq = sao_luu(now)
            print(f"[SAO LƯU] ✅ {kq['key']} ({kq['bytes']:,} byte) · xóa {len(kq['da_xoa'])} bản cũ")
        except Exception as e:
            _loi_luc = time.time()
            print(f"[SAO LƯU] ❌ {type(e).__name__}: {e}")
        finally:
            _khoa.release()
    threading.Thread(target=_job, name="svws-sao-luu", daemon=True).start()
