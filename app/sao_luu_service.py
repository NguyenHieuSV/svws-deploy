"""💾 Sao lưu CSDL hàng ngày lên kho tệp dùng chung (B2 / S3 qua app/luu_tru.py) — anh Hiếu 31/10/2026 (mục C1 rà app).

Bản sao lưu là MỘT file ZIP tự chứa:
  manifest.json      thời điểm (giờ VN), bản app, dialect CSDL, migration đã áp (_migrations), bảng + số dòng, ghi chú pg_dump
  schema/*.sql       bản chép db/init (tạo lại schema khi không còn repo)
  data/<bảng>.csv    toàn bộ dữ liệu từng bảng — UTF-8, dòng đầu là tên cột, NULL ghi \\N, JSON ghi chuỗi JSON, bytes ghi base64:
  pg_dump.dump       (nếu máy chủ có pg_dump đúng phiên bản) bản dump custom của PostgreSQL → pg_restore --no-owner
Khôi phục: `python -m scripts.khoi_phuc_sao_luu <file.zip> --database-url ...` (tạo schema từ schema/*.sql rồi nap_zip()).
Lịch: scheduler gọi den_han() mỗi 5 phút — từ `sao_luu_gio` (giờ VN) mỗi ngày MỘT bản THANH_CONG; mốc nằm trong bảng
sao_luu_log nên khởi động lại không chạy trùng. Dọn bản cũ (don_dep): giữ `sao_luu_giu_ngay` ngày gần nhất + bản đầu mỗi tháng
trong `sao_luu_giu_thang` tháng.
"""
from __future__ import annotations

import base64
import csv
import io
import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import inspect, text

from . import luu_tru
from .config import settings

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NULL = "\\N"
_LO = 500               # số dòng mỗi lần INSERT khi nạp lại


def _gio_vn() -> datetime:
    from .nhac_viec_service import gio_hien_tai
    return gio_hien_tai()


def _build_app() -> str:
    try:
        with open(os.path.join(GOC, "svws_app.html"), encoding="utf-8") as f:
            for _ in range(8):
                line = f.readline()
                if "<!-- build:" in line:
                    return line.split("build:", 1)[1].split("-->")[0].strip()
    except OSError:
        pass
    return ""


def _url_pg() -> str:
    u = settings.database_url
    for a, b in (("postgresql+psycopg2://", "postgresql://"), ("postgres://", "postgresql://")):
        if u.startswith(a):
            u = b + u[len(a):]
    return u


# ---------------- XUẤT ----------------
def _ma_hoa(v) -> str:
    """Giá trị ô → chuỗi CSV (đọc lại bằng _giai_ma theo kiểu cột)."""
    if v is None:
        return NULL
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, Decimal):
        return format(v, "f")
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, memoryview):
        v = v.tobytes()
    if isinstance(v, (bytes, bytearray)):
        return "base64:" + base64.b64encode(bytes(v)).decode("ascii")
    return str(v)


def _ds_bang(engine) -> list[str]:
    return sorted(inspect(engine).get_table_names())


def _pg_dump(engine, zf) -> str:
    """Thêm pg_dump.dump vào ZIP nếu máy chủ có pg_dump và phiên bản khớp; trả ghi chú kết quả (không ném lỗi)."""
    if engine.dialect.name != "postgresql" or not shutil.which("pg_dump"):
        return "không có pg_dump"
    fd, path = tempfile.mkstemp(suffix=".dump")
    os.close(fd)
    try:
        p = subprocess.run(["pg_dump", "--format=custom", "--no-owner", "--no-privileges", "-d", _url_pg(), "-f", path],
                           capture_output=True, text=True, timeout=900)
        if p.returncode != 0:
            return "pg_dump lỗi: " + (p.stderr or "").strip().replace("\n", " ")[:300]
        zf.write(path, "pg_dump.dump")
        return f"pg_dump custom {os.path.getsize(path)} bytes"
    except Exception as e:                                           # noqa: BLE001
        return f"pg_dump lỗi: {type(e).__name__}: {str(e)[:200]}"
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def xuat_zip(engine, duong_dan_zip: str) -> dict:
    """Ghi bản sao lưu toàn bộ CSDL ra file ZIP. Trả {bang: {tên: số dòng}, so_bang, so_dong, pg_dump, kich_thuoc}."""
    bang = _ds_bang(engine)
    so_dong: dict[str, int] = {}
    with zipfile.ZipFile(duong_dan_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        with engine.connect() as conn:
            for t in bang:
                rs = conn.execution_options(stream_results=True).execute(text(f'SELECT * FROM "{t}"'))
                cols = list(rs.keys())
                n = 0
                with zf.open(f"data/{t}.csv", "w") as raw:
                    tw = io.TextIOWrapper(raw, encoding="utf-8", newline="")
                    w = csv.writer(tw, lineterminator="\n")
                    w.writerow(cols)
                    for row in rs:
                        w.writerow([_ma_hoa(v) for v in row])
                        n += 1
                    tw.flush()
                    tw.detach()
                so_dong[t] = n
            mig = ([r[0] for r in conn.execute(text("SELECT ten FROM _migrations ORDER BY ten")).fetchall()]
                   if "_migrations" in bang else [])
        sd = os.path.join(GOC, "db", "init")
        if os.path.isdir(sd):
            for f in sorted(os.listdir(sd)):
                if f.endswith(".sql"):
                    zf.write(os.path.join(sd, f), f"schema/{f}")
        pg = _pg_dump(engine, zf)
        manifest = {"phien_ban": 1, "tao_luc": _gio_vn().isoformat(timespec="seconds"), "app_build": _build_app(),
                    "dialect": engine.dialect.name, "migrations": mig, "bang": so_dong, "so_bang": len(bang),
                    "so_dong": sum(so_dong.values()), "pg_dump": pg, "null": NULL}
        zf.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=1))
    return {"bang": so_dong, "so_bang": len(bang), "so_dong": sum(so_dong.values()), "pg_dump": pg,
            "kich_thuoc": os.path.getsize(duong_dan_zip)}


# ---------------- NẠP LẠI ----------------
def _giai_ma(v: str, col):
    """Chuỗi CSV → giá trị theo kiểu cột (col có thể None → giữ chuỗi)."""
    from sqlalchemy import JSON, Boolean, Date, DateTime, Float, Integer, LargeBinary, Numeric
    if v == NULL:
        return None
    if col is None:
        return v
    t = col.type
    try:
        if isinstance(t, Boolean):
            return v.strip().lower() in ("true", "t", "1")
        if isinstance(t, Integer):
            return int(v)
        if isinstance(t, Float):
            return float(v)
        if isinstance(t, Numeric):
            return Decimal(v)
        if isinstance(t, DateTime):
            return datetime.fromisoformat(v)
        if isinstance(t, Date):
            return date.fromisoformat(v)
        if isinstance(t, JSON) or type(t).__name__ in ("JSONB", "JSON"):
            return json.loads(v) if v != "" else None
        if isinstance(t, LargeBinary):
            return base64.b64decode(v[7:]) if v.startswith("base64:") else v.encode("utf-8")
    except (ValueError, TypeError, json.JSONDecodeError):
        return v
    return v


def nap_zip(engine, duong_dan_zip: str, xoa_du_lieu_cu: bool = True, metadata=None) -> dict:
    """Nạp dữ liệu từ ZIP sao lưu vào CSDL ĐÃ CÓ SCHEMA. PostgreSQL: tắt kiểm FK trong lúc nạp, chỉnh lại sequence id.
    xoa_du_lieu_cu=True: xóa sạch các bảng có trong ZIP trước khi nạp. Cột không còn trong CSDL → bỏ qua; bảng không có → bo_qua.
    Trả {bang: {tên: số dòng}, bo_qua: [...]}."""
    from sqlalchemy import MetaData
    if metadata is None:
        from . import models  # noqa: F401 — nạp đủ bảng vào Base.metadata
        from .database import Base
        metadata = Base.metadata
    md_db = MetaData()
    md_db.reflect(bind=engine, resolve_fks=False)       # không đòi bảng đích của FK phải có (CSDL thiếu bảng vẫn nạp được)
    ket_qua, bo_qua = {}, []
    with zipfile.ZipFile(duong_dan_zip) as zf:
        ten_csv = [n for n in zf.namelist() if n.startswith("data/") and n.endswith(".csv")]
        co = {n[len("data/"):-4] for n in ten_csv}
        with engine.begin() as conn:
            if engine.dialect.name == "postgresql":
                conn.execute(text("SET session_replication_role = replica"))
            if xoa_du_lieu_cu:
                try:
                    thu_tu = list(reversed(md_db.sorted_tables))      # con trước cha
                except Exception:                                     # noqa: BLE001 — FK trỏ tới bảng không có trong CSDL
                    thu_tu = list(md_db.tables.values())
                for t in thu_tu:
                    if t.name in co:
                        conn.execute(t.delete())
            for n in ten_csv:
                ten = n[len("data/"):-4]
                t_db = md_db.tables.get(ten)
                if t_db is None:
                    bo_qua.append(ten)
                    continue
                t_app = metadata.tables.get(ten)
                with zf.open(n) as raw:
                    r = csv.reader(io.TextIOWrapper(raw, encoding="utf-8", newline=""))
                    cols = next(r, None)
                    if not cols:
                        ket_qua[ten] = 0
                        continue
                    def _cot(c):                                   # kiểu cột lấy từ model app (đúng JSON/Decimal), thiếu thì theo CSDL
                        col = t_app.columns.get(c) if t_app is not None else None
                        return col if col is not None else t_db.columns.get(c)
                    idx = [(i, c, _cot(c)) for i, c in enumerate(cols) if c in t_db.columns]
                    lo, dem = [], 0
                    for row in r:
                        lo.append({c: _giai_ma(row[i], col) for i, c, col in idx})
                        if len(lo) >= _LO:
                            conn.execute(t_db.insert(), lo)
                            dem += len(lo)
                            lo = []
                    if lo:
                        conn.execute(t_db.insert(), lo)
                        dem += len(lo)
                    ket_qua[ten] = dem
            if engine.dialect.name == "postgresql":
                for ten in ket_qua:
                    t_db = md_db.tables.get(ten)
                    if t_db is not None and "id" in t_db.columns:
                        sp = conn.begin_nested()
                        try:
                            conn.execute(text(f"SELECT setval(pg_get_serial_sequence('\"{ten}\"', 'id'), "
                                              f"COALESCE((SELECT MAX(id) FROM \"{ten}\"), 0) + 1, false)"))
                            sp.commit()
                        except Exception:                                # noqa: BLE001 — bảng không có sequence
                            sp.rollback()
    return {"bang": ket_qua, "bo_qua": bo_qua}


# ---------------- LỊCH · NHẬT KÝ · DỌN ----------------
def _log_ra(x) -> dict:
    return {"id": x.id, "ten_file": x.ten_file, "co_file": bool(x.duong_dan), "kich_thuoc": x.kich_thuoc,
            "so_bang": x.so_bang, "so_dong": x.so_dong,
            "bat_dau": x.bat_dau.strftime("%d/%m/%Y %H:%M") if x.bat_dau else None,
            "ket_thuc": x.ket_thuc.strftime("%d/%m/%Y %H:%M") if x.ket_thuc else None,
            "trang_thai": x.trang_thai, "nguon": x.nguon, "loi": x.loi, "ghi_chu": x.ghi_chu}


def danh_sach(db, n: int = 20) -> list[dict]:
    from .models import SaoLuuLog
    return [_log_ra(x) for x in db.query(SaoLuuLog).order_by(SaoLuuLog.id.desc()).limit(n).all()]


def den_han(db, now: datetime) -> bool:
    """Đến giờ sao lưu và hôm nay chưa có bản THANH_CONG (hoặc bản DANG_CHAY còn mới dưới 2 giờ)."""
    if not settings.sao_luu_bat or now.hour < settings.sao_luu_gio:
        return False
    from sqlalchemy import and_, or_
    from .models import SaoLuuLog
    dau = datetime(now.year, now.month, now.day)
    co = (db.query(SaoLuuLog.id)
          .filter(SaoLuuLog.bat_dau >= dau,
                  or_(SaoLuuLog.trang_thai == "THANH_CONG",
                      and_(SaoLuuLog.trang_thai == "DANG_CHAY", SaoLuuLog.bat_dau >= now - timedelta(hours=2))))
          .first())
    return co is None


def don_dep(db) -> int:
    """Dọn bản cũ: giữ mọi bản trong `sao_luu_giu_ngay` ngày + bản ĐẦU mỗi tháng trong `sao_luu_giu_thang` tháng; còn lại xóa file."""
    from .models import SaoLuuLog
    now = _gio_vn()
    logs = (db.query(SaoLuuLog).filter(SaoLuuLog.trang_thai == "THANH_CONG", SaoLuuLog.duong_dan.isnot(None))
            .order_by(SaoLuuLog.bat_dau, SaoLuuLog.id).all())
    moc_ngay = now - timedelta(days=int(settings.sao_luu_giu_ngay))
    moc_thang = now - timedelta(days=31 * int(settings.sao_luu_giu_thang))
    giu, dau_thang = set(), {}
    for x in logs:
        if x.bat_dau >= moc_ngay:
            giu.add(x.id)
            continue
        k = x.bat_dau.strftime("%Y-%m")
        if k not in dau_thang and x.bat_dau >= moc_thang:
            dau_thang[k] = x.id
            giu.add(x.id)
    n = 0
    for x in logs:
        if x.id in giu:
            continue
        luu_tru.xoa(x.duong_dan)
        x.duong_dan, x.trang_thai = None, "DA_XOA"
        n += 1
    if n:
        db.commit()
    return n


def tao_ban_sao(db, nguon: str = "TU_DONG", nguoi_dung_id=None) -> dict:
    """Tạo một bản sao lưu: xuất ZIP → đẩy lên kho tệp → ghi nhật ký → dọn bản cũ. Không ném lỗi (ghi LOI vào nhật ký)."""
    from .database import engine
    from .models import SaoLuuLog
    now = _gio_vn()
    log = SaoLuuLog(ten_file=f"svws-{now:%Y%m%d-%H%M%S}.zip", bat_dau=now, trang_thai="DANG_CHAY", nguon=nguon,
                    nguoi_dung_id=nguoi_dung_id)
    db.add(log)
    db.commit()
    fd, path = tempfile.mkstemp(suffix=".zip")
    os.close(fd)
    try:
        kq = xuat_zip(engine, path)
        with open(path, "rb") as f:
            data = f.read()
        ref = luu_tru.luu(data, "sao_luu", now.strftime("%Y-%m-%d"), log.ten_file, "application/zip")
        log.duong_dan, log.kich_thuoc, log.so_bang, log.so_dong = ref, len(data), kq["so_bang"], kq["so_dong"]
        log.ghi_chu, log.ket_thuc, log.trang_thai = kq["pg_dump"], _gio_vn(), "THANH_CONG"
        db.commit()
        da_xoa = don_dep(db)
        return {"ok": True, **_log_ra(log), "da_xoa": da_xoa, "duong_dan": ref}
    except Exception as e:                                           # noqa: BLE001
        db.rollback()
        log = db.get(SaoLuuLog, log.id) or log
        log.trang_thai, log.loi, log.ket_thuc = "LOI", f"{type(e).__name__}: {str(e)[:500]}", _gio_vn()
        db.commit()
        return {"ok": False, **_log_ra(log)}
    finally:
        try:
            os.remove(path)
        except OSError:
            pass
