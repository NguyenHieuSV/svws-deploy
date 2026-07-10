"""
Lưu trữ tệp đính kèm — TỰ CHỌN nơi lưu:

  • Nếu có cấu hình R2/S3 (các biến môi trường R2_ENDPOINT, R2_ACCESS_KEY_ID,
    R2_SECRET_ACCESS_KEY, R2_BUCKET) → lưu lên object storage (BỀN VĨNH VIỄN,
    không mất khi service khởi động lại).
  • Nếu KHÔNG có cấu hình → lưu xuống ổ đĩa cục bộ như cũ (chạy local / dev).

Cột `duong_dan` trong DB trở thành "tham chiếu":
  • "r2:<key>"      → tệp nằm trên R2/S3
  • đường dẫn thường → tệp nằm trên đĩa (tương thích ngược dữ liệu cũ)

KHÔNG cần sửa schema. boto3 chỉ được nạp khi thật sự dùng R2.
"""
import os
import uuid
from urllib.parse import quote

from fastapi import HTTPException, status
from fastapi.responses import FileResponse, StreamingResponse

_R2 = "r2:"


def _cfg():
    return {
        "endpoint": (os.environ.get("R2_ENDPOINT") or "").strip(),
        "key": (os.environ.get("R2_ACCESS_KEY_ID") or "").strip(),
        "secret": (os.environ.get("R2_SECRET_ACCESS_KEY") or "").strip(),
        "bucket": (os.environ.get("R2_BUCKET") or "").strip(),
    }


def dung_r2() -> bool:
    """True nếu đã cấu hình đủ 4 biến môi trường R2/S3."""
    c = _cfg()
    return all([c["endpoint"], c["key"], c["secret"], c["bucket"]])


def _client():
    import boto3  # nạp trễ — chỉ khi dùng R2/B2
    from botocore.config import Config
    c = _cfg()
    # R2 dùng "auto"; Backblaze B2 cần đúng region trong endpoint (vd "us-west-004").
    region = (os.environ.get("R2_REGION") or "auto").strip()
    cli = boto3.client(
        "s3",
        endpoint_url=c["endpoint"],
        aws_access_key_id=c["key"],
        aws_secret_access_key=c["secret"],
        region_name=region,
        config=Config(signature_version="s3v4"),
    )
    return cli, c["bucket"]


def _khoa_moi(nhom: str, doi_tuong_id, ten_file: str) -> str:
    safe = os.path.basename(ten_file or "file").replace("\\", "_")
    return f"{nhom}/{doi_tuong_id}/{uuid.uuid4().hex}_{safe}"


def _ten_goc(ref: str) -> str:
    """Suy ra tên tệp gốc từ tham chiếu (bỏ tiền tố uuid)."""
    base = ref[len(_R2):] if ref.startswith(_R2) else ref
    base = os.path.basename(base)
    return base.split("_", 1)[-1] if "_" in base else base


def luu(data: bytes, nhom: str, doi_tuong_id, ten_file: str, content_type=None) -> str:
    """Lưu bytes; trả về CHUỖI THAM CHIẾU để ghi vào cột duong_dan."""
    key = _khoa_moi(nhom, doi_tuong_id, ten_file)
    if dung_r2():
        cli, bucket = _client()
        extra = {"ContentType": content_type} if content_type else {}
        cli.put_object(Bucket=bucket, Key=key, Body=data, **extra)
        return _R2 + key
    base = os.environ.get("STORAGE_DIR") or "/tmp/svws_storage"
    path = os.path.join(base, key)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)
    return path


def doc(ref: str) -> bytes:
    """Đọc lại nội dung tệp từ tham chiếu (R2 hoặc đĩa). Ném FileNotFoundError nếu mất tệp."""
    if not ref:
        raise FileNotFoundError("Thiếu tham chiếu tệp")
    if ref.startswith(_R2):
        cli, bucket = _client()
        try:
            obj = cli.get_object(Bucket=bucket, Key=ref[len(_R2):])
            return obj["Body"].read()
        except Exception as e:
            raise FileNotFoundError(f"Không đọc được tệp trên kho lưu trữ ({type(e).__name__})")
    with open(ref, "rb") as f:
        return f.read()


def ton_tai(ref: str) -> bool:
    if not ref:
        return False
    if ref.startswith(_R2):
        return True  # tin rằng đã có trên R2 (tránh 1 lần gọi mạng thừa)
    return os.path.exists(ref)


def xoa(ref: str):
    if not ref:
        return
    if ref.startswith(_R2):
        try:
            cli, bucket = _client()
            cli.delete_object(Bucket=bucket, Key=ref[len(_R2):])
        except Exception:
            pass
        return
    try:
        os.remove(ref)
    except OSError:
        pass


def phan_hoi_tai(ref: str, ten_file: str = None, content_type=None):
    """Trả response tải tệp cho FastAPI.
       - R2  → StreamingResponse (tải thẳng từ object storage)
       - đĩa → FileResponse
    """
    media = content_type or "application/octet-stream"
    ten = ten_file or _ten_goc(ref or "")
    if ref and ref.startswith(_R2):
        cli, bucket = _client()
        try:
            obj = cli.get_object(Bucket=bucket, Key=ref[len(_R2):])
        except Exception:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy tệp")

        def _iter(body, size=1024 * 64):
            for chunk in body.iter_chunks(size):
                yield chunk

        headers = {"Content-Disposition": f"attachment; filename*=UTF-8''{quote(ten)}"}
        return StreamingResponse(_iter(obj["Body"]), media_type=media, headers=headers)

    if not ref or not os.path.exists(ref):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy tệp")
    return FileResponse(ref, filename=ten, media_type=media)
