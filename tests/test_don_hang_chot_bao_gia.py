"""
🧾 Đơn hàng nhớ báo giá lúc chốt (28/10/2026, mig 158): «→ Tạo đơn hàng» từ báo giá gửi khách ghi dự toán · Rev · tổng ·
biên lúc chào; đơn lập tay trùng mã tự nối; Kiểm soát lợi nhuận so biên lúc chào với biên thực.
SQLite trong bộ nhớ; dự toán thay bằng dữ liệu giả.
"""
from datetime import date

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app import bao_gia_ks as bk
from app import kiem_soat_ln as ks
from app import models as m


def _raw(con, model, pk="id"):
    """Bảng tối giản cùng tên cột với model (model có kiểu PostgreSQL ENUM / quan hệ joined)."""
    from sqlalchemy import Integer, Numeric
    kieu = lambda c: ("INTEGER PRIMARY KEY" if c.name == pk else "NUMERIC" if isinstance(c.type, Numeric)   # noqa: E731
                      else "INTEGER" if isinstance(c.type, Integer) else "TEXT")
    cols = ", ".join(f"{c.name} {kieu(c)}" for c in model.__table__.columns)
    con.exec_driver_sql(f"CREATE TABLE {model.__tablename__} ({cols})")


@pytest.fixture()
def db(monkeypatch):
    eng = create_engine("sqlite://")
    for t in (m.VaiTro, m.NguoiDung, m.NhanVien, m.BaoGiaForm, m.BaoGiaPhienBan, m.DonHang, m.DonHangCt):
        t.__table__.create(eng)
    with eng.begin() as c:
        for t in (m.HangHoa, m.TonKho, m.KhachHang):
            _raw(c, t)
        c.exec_driver_sql("INSERT INTO khach_hang (id, ma, ten) VALUES (7, 'KH7', 'Công ty Samil')")
        c.exec_driver_sql("INSERT INTO hang_hoa (id, ten, loai, don_vi, gia_ban) VALUES (3, 'Bơm định lượng', 'THIET_BI', 'cái', 0)")
    s = sessionmaker(eng)()
    n = {}

    @event.listens_for(s, "before_flush")
    def _ids(sess, _c, _i):
        for o in sess.new:
            if getattr(o, "id", None) is None:
                n[type(o)] = n.get(type(o), 0) + 1
                o.id = n[type(o)] + 100

    monkeypatch.setattr(bk, "tim_du_toan", lambda db_, bgf: {"loai": "DTB", "id": 1, "ma": "TM-SAMIL-1026-HY", "so_dong": 2,
                                                             "dong_thieu_gia": [], "tong": 80e6, "so_bo": 0, "dong": [],
                                                             "ngoai_du_toan": [], "ngoai_chua_uoc": []})
    import app.audit as au
    monkeypatch.setattr(au, "ghi_audit", lambda *a, **k: None)
    return s


class _Nd:
    def __init__(self, ma="NV_KD"):
        self.id = 1
        self.vai_tro = type("VT", (), {"ma": ma})()


def _bgf(db, so="TM-SAMIL-1026-HY", tt="DA_GUI", kh=7):
    nd = {"so": so, "vat_pct": 8, "items": [
        {"dt_muc_id": 1, "ten": "Bơm định lượng", "so_luong": 1, "don_gia": 100e6, "gia_von": 60e6, "don_vi": "cái"},
        {"dt_muc_id": 2, "ten": "Ống PVC D60", "so_luong": 10, "don_gia": 2e6, "gia_von": 1e6, "vat_pct": 10},
        {"ten": "Bộ lọc dự phòng", "so_luong": 1, "don_gia": 15e6, "tuy_chon": True},
        {"dt_muc_id": 3, "ten": "Vật tư không chào", "so_luong": 1, "don_gia": 5e6, "khong_chao": True},
    ]}
    b = m.BaoGiaForm(so=so, khach_hang_id=kh, noi_dung=nd, trang_thai=tt)
    db.add(b); db.commit()
    return b


def test_tao_don_tu_bao_gia_ghi_so_lieu_chot(db):
    b = _bgf(db)
    bk.luu_phien_ban(db, b, 1, "kh@samil.vn"); db.commit()                  # Rev.A đã gửi khách
    r = bk.tao_don_tu_bao_gia_form(db, b, _Nd())
    assert r["da_co"] is False and r["so"] == "TM-SAMIL-1026-HY" and r["so_dong"] == 2 and r["hang_moi"] == ["Ống PVC D60"]
    dh = db.get(m.DonHang, r["don_hang_id"])
    assert float(dh.tong_tien) == 120e6 and float(dh.tien_thue) == 8e6 + 2e6     # VAT từng dòng: 8% bơm, 10% ống
    assert dh.bao_gia_form_id == b.id and dh.bao_gia_rev == "A" and dh.du_toan_ma == "TM-SAMIL-1026-HY"
    assert float(dh.tong_chao) == 120e6 and float(dh.gia_von_chao) == 80e6 and float(dh.bien_chao) == round(40 / 120 * 100, 1)
    assert dh.chot_luc is not None and dh.khach_hang_id == 7 and dh.ngay == date.today()
    cts = db.query(m.DonHangCt).filter_by(don_hang_id=dh.id).all()
    assert {int(c.hang_hoa_id) for c in cts} == {3, 101} and len(cts) == 2     # bơm khớp hàng có sẵn, ống tự thêm
    with pytest.raises(HTTPException) as e:                                   # đã có đơn → không tạo lại
        bk.tao_don_tu_bao_gia_form(db, b, _Nd())
    assert "đã có đơn hàng" in e.value.detail


def test_trang_thai_va_ep(db):
    b = _bgf(db, so="TM-SAMIL-1026-B", tt="DA_XUAT")
    with pytest.raises(HTTPException) as e:
        bk.tao_don_tu_bao_gia_form(db, b, _Nd())                              # mới xuất PDF → chưa được
    assert e.value.status_code == 400 and "DA_XUAT" in e.value.detail
    with pytest.raises(HTTPException):
        bk.tao_don_tu_bao_gia_form(db, b, _Nd(), ep=True)                     # nhân viên ép cũng không
    r = bk.tao_don_tu_bao_gia_form(db, b, _Nd("CEO"), ep=True)                # CEO ép → tạo
    assert r["so"] == "TM-SAMIL-1026-B" and r["rev"] is None                  # chưa gửi khách lần nào → không Rev


def test_don_lap_tay_trung_ma_tu_noi(db):
    b = _bgf(db, so="TM-SAMIL-1026-C", tt="DA_DUYET")
    dh = m.DonHang(so="tm-samil-1026-c", khach_hang_id=7, ngay=date.today(), tong_tien=118e6, trang_thai="MOI")
    db.add(dh); db.commit()
    assert bk.noi_bao_gia_theo_ma(db, dh)["nguon"] == "THEO_MA"               # đơn lập tay / AI đọc PO → tự nối
    assert dh.bao_gia_form_id == b.id and float(dh.bien_chao) == 33.3
    assert bk.noi_bao_gia_theo_ma(db, dh) is None                             # đã nối → thôi
    # «→ Tạo đơn hàng» khi đã có đơn cùng mã (chưa nối) → chỉ nối, không tạo trùng
    b2 = _bgf(db, so="TM-SAMIL-1026-D", tt="DA_GUI")
    dh2 = m.DonHang(so="TM-SAMIL-1026-D", khach_hang_id=7, ngay=date.today(), tong_tien=100e6, trang_thai="MOI")
    db.add(dh2); db.commit()
    r = bk.tao_don_tu_bao_gia_form(db, b2, _Nd())
    assert r["da_co"] is True and r["don_hang_id"] == dh2.id and dh2.bao_gia_form_id == b2.id
    assert db.query(m.DonHang).count() == 2
    # báo giá nháp / hợp đồng không được nối theo mã
    _bgf(db, so="TM-SAMIL-1026-E", tt="NHAP")
    assert bk.tim_bgf_theo_ma(db, "TM-SAMIL-1026-E") is None


def test_kiem_soat_so_bien_chao(monkeypatch):
    from app.routers import ncc
    rows = [
        {"ma_ban": "TM-SAMIL-1026-HY", "nhom": "TM-SAMIL-1026", "doanh_thu": 130e6, "tong_chi_phi": 100e6,
         "bien_chao": 33.3, "tong_chao": 120e6},                                        # thực 23,1% ≥ 15 nhưng tụt 10 điểm
        {"ma_ban": "TM-SIC-1026-A", "nhom": "TM-SIC-1026", "doanh_thu": 100e6, "tong_chi_phi": 75e6,
         "bien_chao": 27.0, "tong_chao": 90e6},                                         # thực 25% — tụt 2 điểm < 3 → không nhắc
        {"ma_ban": "TM-SAMIL-1026-02", "nhom": "TM-SAMIL-1026", "doanh_thu": 0, "tong_chi_phi": 0},   # không có số chào
        {"ma_ban": "DV-D10-0826", "nhom": "DV-D10-0826", "doanh_thu": 61e6, "tong_chi_phi": 100e6, "bien_chao": 20.0, "tong_chao": 55e6},
        {"ma_ban": "TM-SIC-0726-UP", "nhom": "TM-SIC-0726", "doanh_thu": 100e6, "tong_chi_phi": 96e6},
    ]
    monkeypatch.setattr(ncc, "chi_phi_theo_don", lambda db, _: rows)
    monkeypatch.setattr(ks.settings, "po_bien_ln_toi_thieu", 15.0)
    bc = ks.bao_cao_tuan(None, date(2026, 10, 28))
    assert [o["nhom"] for o in bc["tut_bien"]] == ["TM-SAMIL-1026"] and bc["tut_bien"][0]["bien_chao"] == 33.3 and bc["tut_bien_diem"] == 3.0
    assert [o["nhom"] for o in bc["lo"]] == ["DV-D10-0826"] and bc["lo"][0]["bien_chao"] == 20.0
    assert bc["bien_thap"][0]["nhom"] == "TM-SIC-0726" and bc["bien_thap"][0]["bien_chao"] is None
    t = ks.noi_dung_tuan(bc)
    assert "🔵" in t and "chào 33,3% → thực 23,1%" in t and "lỗ 39,0 tr · chào 20,0%" in t
    # cờ lúc duyệt PO ghi kèm biên lúc chào
    monkeypatch.setattr(ks, "so_lieu_nhom", lambda db, nh: {"dt": 100e6, "cp": 80e6, "dau_tu": False, "ma": [], "bien_chao": 30.0})
    k = ks.danh_gia(None, "TM-SIC-1026-01", 10e6)
    assert k["muc"] == "BIEN_THAP" and k["bien_chao"] == 30.0 and "Lúc chào biên 30,0%" in k["ly_do"]
    # cổng TỤT BIÊN: còn trên ngưỡng 15% nhưng thấp hơn biên lúc chào ≥ 3 điểm (TUT_BIEN_DIEM) → cờ 📉 (chỉ CEO, phải xác nhận)
    assert ks.TUT_BIEN_DIEM == 3.0
    monkeypatch.setattr(ks, "so_lieu_nhom", lambda db, nh: {"dt": 100e6, "cp": 70e6, "dau_tu": False, "ma": [], "bien_chao": 33.3})
    k = ks.danh_gia(None, "TM-SIC-1026-01", 5e6)                                  # 75/100 → biên 25% — tụt 8,3 điểm
    assert k["muc"] == "TUT_BIEN" and k["bien"] == 25.0 and "TỤT 8,3 điểm so với lúc chào 33,3% (ngưỡng tụt 3 điểm)" in k["ly_do"]
    assert ks.danh_gia(None, "TM-SIC-1026-01", 0)["muc"] == "TUT_BIEN"            # 70/100 → 30% — tụt 3,3 điểm ≥ 3 → cờ
    monkeypatch.setattr(ks, "so_lieu_nhom", lambda db, nh: {"dt": 100e6, "cp": 70e6, "dau_tu": False, "ma": [], "bien_chao": 32.0})
    assert ks.danh_gia(None, "TM-SIC-1026-01", 0) is None                          # 30% — tụt 2,0 điểm < 3 → ổn
    monkeypatch.setattr(ks, "so_lieu_nhom", lambda db, nh: {"dt": 100e6, "cp": 70e6, "dau_tu": False, "ma": []})
    assert ks.danh_gia(None, "TM-SIC-1026-01", 5e6) is None                        # chưa có biên lúc chào → không cổng tụt
    assert ks.bien_chao_gop([{"bien_chao": 20, "tong_chao": 100}, {"bien_chao": 40, "tong_chao": 300}, {"bien_chao": None, "tong_chao": 5}]) == 35.0
