"""
📎 Attached file của báo cáo ngày: tải nhiều tệp, giới hạn loại / số lượng / dung lượng, quyền xem / xóa,
xóa báo cáo thì xóa luôn tệp. Không cần PostgreSQL (SQLite) — tệp lưu thư mục tạm.
"""
import asyncio
import io

import pytest
from fastapi import HTTPException, UploadFile
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app import models as m
from app.routers import nhan_su as ns


@pytest.fixture()
def db(monkeypatch, tmp_path):
    monkeypatch.setattr(ns, "ghi_audit", lambda *a, **k: None)
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path))
    for k in ("R2_ENDPOINT", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET"):
        monkeypatch.delenv(k, raising=False)
    eng = create_engine("sqlite://")

    @event.listens_for(eng, "connect")
    def _to_char(con, _r):                     # SQLite thiếu to_char của PostgreSQL ('YYYY-MM' là đủ cho test)
        con.create_function("to_char", 2, lambda d, _fmt: str(d)[:7])
    for t in (m.VaiTro, m.NguoiDung, m.NhanVien, m.GiaoViec, m.BaoCaoNgay, m.TepDinhKem):
        t.__table__.create(eng)
    s = sessionmaker(eng)()
    n = {}

    @event.listens_for(s, "before_flush")
    def _ids(sess, _c, _i):
        for o in sess.new:
            if getattr(o, "id", None) is None:
                n[type(o)] = n.get(type(o), 0) + 1
                o.id = n[type(o)]

    s.add(m.VaiTro(ma="NV_DA", ten="NV Dự án")); s.add(m.VaiTro(ma="CEO", ten="Giám đốc")); s.flush()
    s.add(m.NguoiDung(email="an@x.vn", mat_khau_hash="x", vai_tro_id=1, trang_thai="HOAT_DONG"))
    s.add(m.NguoiDung(email="binh@x.vn", mat_khau_hash="x", vai_tro_id=1, trang_thai="HOAT_DONG"))
    s.add(m.NguoiDung(email="ceo@x.vn", mat_khau_hash="x", vai_tro_id=2, trang_thai="HOAT_DONG")); s.flush()
    s.add(m.NhanVien(ma="NV01", ho_ten="An", trang_thai="DANG_LAM", nguoi_dung_id=1))
    s.add(m.NhanVien(ma="NV02", ho_ten="Bình", trang_thai="DANG_LAM", nguoi_dung_id=2))
    s.commit()
    monkeypatch.setattr(ns, "muc_cua", lambda db_, vt, mod: "KHONG")   # NV thường không có quyền XEM Working time
    return s


def _up(ten, data=b"du-lieu"):
    return UploadFile(file=io.BytesIO(data), filename=ten)


def _tai(db, bc_id, files, nd):
    return asyncio.run(ns.bc_tai_tep(bc_id, files, db, nd=nd))


def test_dinh_kem_xem_xoa(db):
    an, binh, ceo = (db.get(m.NguoiDung, i) for i in (1, 2, 3))
    bc = ns.gui_bao_cao_ngay(ns.BaoCaoNgayVao(tien_do=50, ngay="2026-10-27", da_lam="lắp bơm"), db, nd=an)
    kq = _tai(db, bc["id"], [_up("anh hien truong.jpg"), _up("bien-ban.pdf")], an)
    assert [t["ten_file"] for t in kq["tep"]] == ["anh hien truong.jpg", "bien-ban.pdf"]
    ds = ns.bao_cao_cua_toi("2026-10", db, nd=an)["danh_sach"]
    assert [t["ten_file"] for t in ds[0]["tep"]] == ["anh hien truong.jpg", "bien-ban.pdf"]
    tid = kq["tep"][0]["id"]
    with pytest.raises(HTTPException) as e:                      # người khác không xem được
        ns.bc_tai_ve_tep(tid, db, nd=binh)
    assert e.value.status_code == 403
    assert ns.bc_tai_ve_tep(tid, db, nd=ceo).status_code == 200  # CEO xem được
    with pytest.raises(HTTPException):                           # người khác không đính kèm vào báo cáo của An
        _tai(db, bc["id"], [_up("x.pdf")], binh)
    ns.bc_xoa_tep(tid, db, nd=an)
    assert [t["ten_file"] for t in ns.bao_cao_cua_toi("2026-10", db, nd=an)["danh_sach"][0]["tep"]] == ["bien-ban.pdf"]
    ns.xoa_bao_cao_ngay(bc["id"], db, nd=an)                     # xóa báo cáo → xóa luôn tệp
    assert db.query(m.TepDinhKem).count() == 0


def test_gioi_han_loai_so_luong_dung_luong(db):
    an = db.get(m.NguoiDung, 1)
    bc = ns.gui_bao_cao_ngay(ns.BaoCaoNgayVao(tien_do=50, ngay="2026-10-27", da_lam="x"), db, nd=an)
    with pytest.raises(HTTPException):
        _tai(db, bc["id"], [_up("virus.exe")], an)
    with pytest.raises(HTTPException):
        _tai(db, bc["id"], [_up(f"a{i}.png") for i in range(11)], an)
    with pytest.raises(HTTPException):
        _tai(db, bc["id"], [_up("to.pdf", b"x" * (20 * 1024 * 1024 + 1))], an)
    assert db.query(m.TepDinhKem).count() == 0                   # lỗi thì không lưu tệp nào


def test_ds_bao_cao_theo_khoang_ngay_va_ngay_gan_nhat(db, monkeypatch):
    an = db.get(m.NguoiDung, 1)
    assert ns.ds_bao_cao_ngay(None, None, "2026-10-20", "2026-10-28", None, db, None)["ngay_gan_nhat"] is None
    for d in ("2026-10-26", "2026-10-27"):
        ns.gui_bao_cao_ngay(ns.BaoCaoNgayVao(tien_do=50, ngay=d, da_lam="x"), db, nd=an)
    r = ns.ds_bao_cao_ngay(None, None, "2026-10-22", "2026-10-28", None, db, None)
    assert [x["ngay"] for x in r["danh_sach"]] == ["2026-10-27", "2026-10-26"] and r["ngay_gan_nhat"] == "2026-10-27"
    assert [x["ngay"] for x in ns.ds_bao_cao_ngay(None, None, "2026-10-27", None, None, db, None)["danh_sach"]] == ["2026-10-27"]
