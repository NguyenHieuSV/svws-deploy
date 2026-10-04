"""
Test sao lưu CSDL lên B2 (T102 · PR-0). Không gọi B2 thật: thay boto3 client bằng bộ nhớ giả.
Phần pg_dump thật chỉ chạy khi có Postgres (make db-up) và lệnh pg_dump.
"""
import os
import shutil
from datetime import datetime

import pytest
import yaml

from app import sao_luu


class FakeS3:
    """Đủ các hàm sao_luu dùng: list_objects_v2 (có phân trang), list_object_versions,
    delete_object, upload_file, download_file."""

    def __init__(self, page=1000):
        self.obj, self.page, self.deleted = {}, page, []

    def list_objects_v2(self, Bucket, Prefix, ContinuationToken=None):
        keys = sorted(k for k in self.obj if k.startswith(Prefix))
        i = int(ContinuationToken or 0)
        part = keys[i:i + self.page]
        r = {"Contents": [{"Key": k} for k in part], "IsTruncated": i + self.page < len(keys)}
        if r["IsTruncated"]:
            r["NextContinuationToken"] = str(i + self.page)
        return r

    def list_object_versions(self, Bucket, Prefix):
        return {"Versions": [{"Key": k, "VersionId": "v-" + k} for k in self.obj if k.startswith(Prefix)]}

    def delete_object(self, Bucket, Key, VersionId=None):
        assert VersionId == "v-" + Key, "phải xóa theo VersionId để B2 giải phóng dung lượng"
        self.deleted.append(Key)
        self.obj.pop(Key, None)

    def upload_file(self, path, Bucket, Key):
        with open(path, "rb") as f:
            self.obj[Key] = f.read()

    def download_file(self, Bucket, Key, dest):
        with open(dest, "wb") as f:
            f.write(self.obj[Key])


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    for k, v in {"BACKUP_B2_ENDPOINT": "https://s3.us-west-004.backblazeb2.com",
                 "BACKUP_B2_KEY_ID": "k", "BACKUP_B2_APP_KEY": "s", "BACKUP_B2_BUCKET": "b",
                 "BACKUP_B2_PREFIX": "pg-dump/", "BACKUP_KEEP": "3", "BACKUP_GIO": "2"}.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setattr(sao_luu, "_loi_luc", 0.0)


def _gia_dump(dich):
    with open(dich, "wb") as f:
        f.write(b"PGDMP-gia")


def test_cau_hinh_va_ten_tep(monkeypatch):
    assert sao_luu.bat()
    assert sao_luu._cfg()["region"] == "us-west-004"
    assert sao_luu.ten_ban_sao(datetime(2026, 10, 4, 2, 5, 9)) == "pg-dump/svws-20261004-020509.dump"
    monkeypatch.delenv("BACKUP_B2_BUCKET")
    assert not sao_luu.bat()
    assert not sao_luu.den_han(datetime(2026, 10, 4, 9))    # chưa cấu hình → không bao giờ chạy


def test_db_url_chuan_hoa(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg2://u:p@h:5432/d")
    assert sao_luu.db_url() == "postgresql://u:p@h:5432/d"
    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@h/d")
    assert sao_luu.db_url() == "postgresql://u:p@h/d"


def test_giu_dung_so_ban_moi_nhat():
    s3 = FakeS3(page=2)                            # phân trang nhỏ để chạy qua ContinuationToken
    s3.obj["pg-dump/ghi-chu.txt"] = b"x"            # tệp lạ trong thư mục: không đụng tới
    s3.obj["khac/svws-20200101-000000.dump"] = b"x"  # ngoài prefix: không đụng tới
    for d in range(1, 6):
        sao_luu.sao_luu(datetime(2026, 10, d, 2, 0, 0), s3, "b", dump=_gia_dump)
    con = sao_luu.danh_sach(s3, "b")
    assert con == [f"pg-dump/svws-202610{d:02d}-020000.dump" for d in (3, 4, 5)]
    assert s3.deleted == ["pg-dump/svws-20261001-020000.dump", "pg-dump/svws-20261002-020000.dump"]
    assert "pg-dump/ghi-chu.txt" in s3.obj and "khac/svws-20200101-000000.dump" in s3.obj
    assert s3.obj[con[-1]] == b"PGDMP-gia"


def test_dump_rong_hoac_loi_thi_khong_tai_len():
    s3 = FakeS3()
    with pytest.raises(RuntimeError):
        sao_luu.sao_luu(datetime(2026, 10, 4, 2), s3, "b", dump=lambda p: None)  # tệp rỗng
    with pytest.raises(RuntimeError):
        sao_luu.sao_luu(datetime(2026, 10, 4, 2), s3, "b",
                        dump=lambda p: (_ for _ in ()).throw(RuntimeError("pg_dump lỗi")))
    assert s3.obj == {}


def test_den_han_moi_ngay_mot_lan(monkeypatch):
    s3 = FakeS3()
    monkeypatch.setattr(sao_luu, "_client", lambda: (s3, "b"))
    assert not sao_luu.den_han(datetime(2026, 10, 4, 1, 59))   # trước BACKUP_GIO
    assert sao_luu.den_han(datetime(2026, 10, 4, 2, 0))
    sao_luu.sao_luu(datetime(2026, 10, 4, 2, 0), s3, "b", dump=_gia_dump)
    assert not sao_luu.den_han(datetime(2026, 10, 4, 23, 0))   # hôm nay đã có bản
    assert sao_luu.den_han(datetime(2026, 10, 5, 7, 30))       # ngủ qua 2h → chạy bù
    monkeypatch.setattr(sao_luu, "_loi_luc", __import__("time").time())
    assert not sao_luu.den_han(datetime(2026, 10, 5, 7, 30))   # vừa lỗi → chờ 1 giờ


def test_render_yaml_khop_tai_nguyen_thuc_te():
    with open(os.path.join(os.path.dirname(__file__), "..", "render.yaml"), encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    db = cfg["databases"][0]
    web = cfg["services"][0]
    assert (db["name"], db["plan"], db["databaseName"]) == ("svws-db-iit7", "basic-256mb", "svws_gu1s")
    assert (web["name"], web["plan"]) == ("svws-app-iit7", "starter")
    env = {e["key"]: e for e in web["envVars"]}
    assert env["DATABASE_URL"]["fromDatabase"]["name"] == db["name"]
    for k in ("BACKUP_B2_ENDPOINT", "BACKUP_B2_KEY_ID", "BACKUP_B2_APP_KEY", "BACKUP_B2_BUCKET"):
        assert env[k].get("sync") is False, f"{k} là bí mật — đặt trên Dashboard, không ghi vào repo"


def _co_postgres():
    url = os.environ.get("DATABASE_URL", "postgresql+psycopg2://svws:svws@localhost:5432/svws")
    if not url.startswith("postgres") or not shutil.which("pg_dump"):
        return False
    try:
        from sqlalchemy import create_engine
        create_engine(url).connect().close()
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _co_postgres(), reason="Cần Postgres đang chạy và lệnh pg_dump")
def test_pg_dump_that_tai_len_va_khoi_phuc_duoc(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", os.environ.get(
        "DATABASE_URL", "postgresql+psycopg2://svws:svws@localhost:5432/svws"))
    s3 = FakeS3()
    kq = sao_luu.sao_luu(datetime(2026, 10, 4, 2), s3, "b")
    assert kq["bytes"] > 0 and s3.obj[kq["key"]].startswith(b"PGDMP")
    dich = tmp_path / "ban.dump"
    s3.download_file("b", kq["key"], str(dich))
    if shutil.which("pg_restore"):                       # đọc được mục lục = tệp khôi phục được
        import subprocess
        toc = subprocess.run(["pg_restore", "--list", str(dich)], capture_output=True, text=True)
        assert toc.returncode == 0 and "TABLE public khach_hang" in toc.stdout
