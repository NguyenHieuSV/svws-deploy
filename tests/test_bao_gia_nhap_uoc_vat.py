"""
31/10/2026 — rà logic, 3 mục anh Hiếu chốt:
 1. Bản in / PDF báo giá CHƯA DUYỆT đóng dấu BẢN NHÁP (bao_gia_ks.ban_nhap · bao_gia_pdf nhap=True).
 2. Dự toán tạo ngược từ báo giá mang cờ GIÁ VỐN ƯỚC (mig 162): cổng duyệt chỉ CEO, biên chào không so, gỡ cờ khi rà.
 3. Lãi / biên theo mã tính CHƯA VAT ở cả hai vế (lai_lo_ma.chi_phi_ma) — dòng tiền vẫn gồm VAT.
SQLite trong bộ nhớ.
"""
import os
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app import bao_gia_ks as bk
from app import kiem_soat_ln as ks
from app import models as m
from app.bao_gia_pdf import tao_bao_gia_pdf
from app.config import settings


class _Nd:
    def __init__(self, ma="NV_KD"):
        self.id = 1
        self.vai_tro = type("VT", (), {"ma": ma})()


def _bgf(tt, ngay="2026-10-30", items=None, so="TM-T-1026-01"):
    return SimpleNamespace(so=so, trang_thai=tt, noi_dung={"so": so, "ngay": ngay, "vat_pct": 8,
                                                           "items": items or [{"ten": "x", "so_luong": 1, "don_gia": 100e6}]})


def _session(*tables):
    eng = create_engine("sqlite://")
    for t in tables:
        t.__table__.create(eng)
    s = sessionmaker(eng)()
    n = {}

    @event.listens_for(s, "before_flush")
    def _ids(sess, _c, _i):
        for o in sess.new:
            if getattr(o, "id", None) is None:
                n[type(o)] = n.get(type(o), 0) + 1
                o.id = n[type(o)]
    return s, eng


# ---------- mục 1 ----------
def test_ban_nhap(monkeypatch):
    monkeypatch.setattr(settings, "bg_ap_dung_tu", "2026-10-28")
    assert bk.ban_nhap(_bgf("NHAP")) and bk.ban_nhap(_bgf("CHO_DUYET")) and bk.ban_nhap(_bgf("TU_CHOI"))
    assert not bk.ban_nhap(_bgf("DA_DUYET")) and not bk.ban_nhap(_bgf("DA_GUI"))
    assert bk.ban_nhap(_bgf("DA_XUAT", "2026-10-30"))              # xuất PDF sau mốc mà chưa duyệt → nháp
    assert not bk.ban_nhap(_bgf("DA_XUAT", "2026-10-20"))          # xuất PDF trước mốc (gửi tay thời chưa có cổng) → sạch
    hd = _bgf("NHAP"); hd.noi_dung["loai"] = "HOP_DONG"
    assert not bk.ban_nhap(hd)


def test_pdf_dong_dau_nhap(tmp_path):
    d = {"so": "TM-T-1026-01", "ngay": "2026-10-30", "khach_ten": "K", "vat_pct": 8,
         "items": [{"ten": "Bom", "so_luong": 1, "don_gia": 1e6, "vat_pct": 8}]}
    p1 = tao_bao_gia_pdf(str(tmp_path / "a.pdf"), d, font_path="/x", font_bold_path="/x", nhap=True)
    p2 = tao_bao_gia_pdf(str(tmp_path / "b.pdf"), d, font_path="/x", font_bold_path="/x")
    assert os.path.getsize(p1) > 1000 and os.path.getsize(p2) > 1000
    try:
        from pypdf import PdfReader
    except ImportError:
        return
    t1 = "".join(pg.extract_text() for pg in PdfReader(p1).pages)
    t2 = "".join(pg.extract_text() for pg in PdfReader(p2).pages)
    assert "NOT APPROVED" in t1 and "NOT APPROVED" not in t2


# ---------- mục 2 ----------
DT_UOC = {"loai": "DTB", "id": 1, "ma": "TM-T-1026-01", "so_dong": 1, "dong_thieu_gia": [], "tong": 80e6, "gia_uoc": True,
          "so_bo": 0, "dong": [], "ngoai_du_toan": [], "ngoai_chua_uoc": []}


def test_cong_gia_von_uoc(monkeypatch):
    monkeypatch.setattr(bk, "tim_du_toan", lambda db, bgf: DT_UOC)
    monkeypatch.setattr(settings, "bg_bien_toi_thieu", 15.0)
    b = _bgf("NHAP")
    k = bk.kiem_tra(None, b)
    assert k["gia_uoc"] and "GIÁ VỐN ƯỚC" in k["canh_bao_uoc"] and k["bien"] == 20.0 and k["canh_bao_bien"] is None
    bk.cong(None, b, _Nd("NV_KD"), False, "trình duyệt")                      # trình duyệt vẫn qua
    with pytest.raises(HTTPException) as e:
        bk.cong(None, b, _Nd("TP_KD"), True, "duyệt", kiem_bien=True)         # lúc duyệt: người thường bị chặn
    assert e.value.status_code == 403 and "ƯỚC" in e.value.detail
    with pytest.raises(HTTPException) as e:
        bk.cong(None, b, _Nd("CEO"), False, "duyệt", kiem_bien=True)          # CEO: hỏi xác nhận
    assert e.value.status_code == 409
    assert "⚠" in bk.cong(None, b, _Nd("CEO"), True, "duyệt", kiem_bien=True)["vuot"][0]


def test_bien_chao_gop_bo_uoc():
    rows = [{"bien_chao": 20, "tong_chao": 100}, {"bien_chao": 40, "tong_chao": 100, "gia_von_chao_uoc": True}]
    assert ks.bien_chao_gop(rows) == 20.0


@pytest.fixture()
def db_dt(monkeypatch):
    s, eng = _session(m.BaoGiaForm, m.DuToanBan, m.DuToanBanMuc, m.NhaCungCap, m.SanPhamNcc)
    with eng.begin() as c:
        c.exec_driver_sql("CREATE TABLE hang_hoa (id INTEGER PRIMARY KEY, ten VARCHAR(200), don_vi VARCHAR(20))")
        c.exec_driver_sql("CREATE TABLE khach_hang (id INTEGER PRIMARY KEY, ma VARCHAR(20), ten VARCHAR(200))")
    for k, v in (("bg_bien_thiet_bi", 15.0), ("bg_bien_vat_tu", 25.0), ("bg_bien_nhan_cong", 30.0), ("bg_chi_phi_chung", 5.0)):
        monkeypatch.setattr(settings, k, v)
    monkeypatch.setattr(bk, "tim_du_toan", lambda db_, bgf: None)
    import app.audit as au; monkeypatch.setattr(au, "ghi_audit", lambda *a, **k: None)
    import app.ma_code as mc; monkeypatch.setattr(mc, "bat_buoc", lambda ma, nd, ep, nhan="": ma)
    from app.routers import ncc
    monkeypatch.setattr(ncc, "ghi_audit", lambda *a, **k: None)
    return s


def test_tao_nguoc_co_co_uoc_va_go_co(db_dt):
    from app.routers import ncc
    nd = {"so": "TM-U-1026-01", "ngay": "2026-10-29", "vat_pct": 8, "items": [
        {"ten": "Bơm", "so_luong": 1, "don_gia": 10_000_000, "nhom": "THIET_BI"},                        # không giá vốn → ƯỚC
        {"ten": "Ống", "so_luong": 5, "don_gia": 100_000, "gia_von": 60_000, "nhom": "VAT_TU"},            # có giá vốn thật
    ]}
    b = m.BaoGiaForm(so="TM-U-1026-01", noi_dung=nd, trang_thai="NHAP"); db_dt.add(b); db_dt.commit()
    r = bk.tao_du_toan_tu_bao_gia(db_dt, b, _Nd("CEO"))
    assert r["so_uoc"] == 1
    d = db_dt.get(m.DuToanBan, r["du_toan_id"])
    rows = {x.ten: x for x in db_dt.query(m.DuToanBanMuc).filter_by(du_toan_id=d.id).all()}
    assert d.gia_uoc is True
    assert str(rows["Bơm"].ghi_chu).startswith("Giá vốn ƯỚC") and rows["Ống"].ghi_chu is None    # chỉ dòng ước mới có nhãn
    # sửa giá dòng ƯỚC → bỏ nhãn; hết dòng ƯỚC → gỡ cờ dự toán
    bom = rows["Bơm"]; gia_truoc = bom.don_gia; bom.don_gia = Decimal(7_500_000)
    assert ncc._dtb_bo_uoc(db_dt, bom, _Nd("NV_KD"), gia_truoc) is True
    db_dt.commit()
    assert bom.ghi_chu is None and db_dt.get(m.DuToanBan, d.id).gia_uoc is False
    # không đổi giá → không bỏ nhãn
    bom.ghi_chu = "Giá vốn ƯỚC từ giá bán − sàn biên (tạo ngược từ báo giá) — cần rà lại"; d.gia_uoc = True; db_dt.commit()
    assert ncc._dtb_bo_uoc(db_dt, bom, _Nd("NV_KD"), bom.don_gia) is False and d.gia_uoc is True
    # nút ✓ Đã rà giá vốn
    kq = ncc.dtb_ra_gia_von(d.id, db_dt, _Nd("NV_KD"))
    assert kq["so_dong"] == 1 and db_dt.get(m.DuToanBan, d.id).gia_uoc is False and bom.ghi_chu is None


# ---------- mục 3 ----------
def test_lai_lo_theo_ma_chua_vat(monkeypatch):
    from app import dau_tu_cho_thue
    from app.lai_lo_ma import chi_phi_ma, chi_phi_ngoai_ma
    monkeypatch.setattr(dau_tu_cho_thue, "ma_me_dang_dau_tu", lambda db: set())
    s, _ = _session(m.DonHang, m.DonHangCt, m.DonMua, m.DonMuaCt, m.CongNo, m.HoaDon, m.ChiPhiVanHanh, m.PhieuThuChi)
    dh = m.DonHang(so="TM-V-1026-01", khach_hang_id=1, tong_tien=100_000_000, tien_thue=8_000_000); s.add(dh); s.flush()
    s.add(m.DonMua(so="PO-1", nha_cung_cap_id=1, tien_hang=50_000_000, tien_thue=5_000_000, tong_tien=55_000_000,
                   trang_thai="DA_DUYET", don_hang_id=dh.id))
    s.add(m.DonMua(so="PO-2", nha_cung_cap_id=1, tien_hang=0, tien_thue=1_000_000, tong_tien=11_000_000,       # PO cũ chưa tách
                   trang_thai="DA_DUYET", don_hang_id=dh.id))
    s.add(m.CongNo(loai="PHAI_TRA", so_tien=22_000_000, tien_thue=2_000_000, ma_ban_ngoai="TM-V-1026-01", so_ct="CT-9",
                   nha_cung_cap_id=2))
    s.add(m.HoaDon(loai="MUA", don_hang_id=dh.id, tien_truoc_thue=30_000_000, tien_thue=3_000_000, tong_tien=33_000_000,
                   so="HD-5", nha_cung_cap_id=3))
    s.add(m.DonMua(so="PO-LE", nha_cung_cap_id=1, tien_hang=10_000_000, tien_thue=800_000, tong_tien=10_800_000,
                   trang_thai="DA_DUYET", ma_ban="DV-LE-1026"))
    s.commit()
    cp = chi_phi_ma(s, dh)
    assert cp["doanh_thu"] == 100e6 and cp["doanh_thu_gom_vat"] == 108e6 and cp["vat_ban"] == 8e6
    assert cp["gia_von_po"] == 60e6 and cp["chi_ngoai_cn"] == 20e6 and cp["chi_hd_ngoai_po"] == 30e6
    assert cp["tong_chi_phi"] == 110e6 and cp["loi_nhuan"] == -10e6 and cp["ty_suat"] == -10.0
    assert cp["con_phai_thu"] == 108e6                                        # dòng tiền vẫn gồm VAT
    assert chi_phi_ngoai_ma(s)["ma_le"]["dv-le-1026"]["chi"] == 10e6           # PO mã lẻ: chưa VAT
