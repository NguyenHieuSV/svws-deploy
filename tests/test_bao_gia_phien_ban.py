"""
Bước 3 báo giá (28/10/2026): ⭐ tùy chọn ngoài tổng chính; phiên bản Rev.A/B lưu khi gửi khách; so sánh với lần gửi trước.
SQLite trong bộ nhớ, dự toán thay bằng dữ liệu giả.
"""
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app import bao_gia_ks as bk
from app import models as m
from app.bao_gia_pdf import tinh_bao_gia, tinh_tuy_chon


@pytest.fixture()
def db(monkeypatch):
    eng = create_engine("sqlite://")
    for t in (m.VaiTro, m.NguoiDung, m.NhanVien, m.BaoGiaForm, m.BaoGiaPhienBan):
        t.__table__.create(eng)
    s = sessionmaker(eng)()
    n = {}

    @event.listens_for(s, "before_flush")
    def _ids(sess, _c, _i):
        for o in sess.new:
            if getattr(o, "id", None) is None:
                n[type(o)] = n.get(type(o), 0) + 1
                o.id = n[type(o)]

    monkeypatch.setattr(bk, "tim_du_toan", lambda db_, bgf: {"loai": "DTB", "id": 1, "ma": "DA-X-1026", "so_dong": 2,
                                                             "dong_thieu_gia": [], "tong": 80e6, "so_bo": 0, "dong": [],
                                                             "ngoai_du_toan": [], "ngoai_chua_uoc": []})
    return s


def _nd(gia_bom, them_tuy_chon=True):
    its = [{"dt_muc_id": 1, "ten": "Bơm", "so_luong": 1, "don_gia": gia_bom, "gia_von": 60e6, "vat_pct": 8},
           {"dt_muc_id": 2, "ten": "Ống", "so_luong": 10, "don_gia": 2e6, "gia_von": 1e6, "vat_pct": 8}]
    if them_tuy_chon:
        its.append({"ten": "Bộ lọc dự phòng", "so_luong": 1, "don_gia": 15e6, "gia_von": 10e6, "tuy_chon": True, "vat_pct": 8})
    return {"so": "DA-X-1026", "items": its, "vat_pct": 8}


def test_tuy_chon_ngoai_tong_chinh():
    nd = _nd(100e6)
    assert tinh_bao_gia(nd)[0] == 120e6 and tinh_tuy_chon(nd) == 15e6        # 100 + 20, tùy chọn 15 để ngoài


def test_phien_ban_va_so_sanh(db):
    b = m.BaoGiaForm(so="DA-X-1026", noi_dung=_nd(100e6), trang_thai="DA_DUYET")
    db.add(b); db.commit()
    assert bk.so_sanh_lan_truoc(db, b) is None                               # chưa gửi lần nào
    r1 = bk.luu_phien_ban(db, b, 1, "kh@x.vn"); db.commit()
    assert r1["rev"] == "A" and r1["tong_chua_vat"] == 120e6
    ds = bk.ds_phien_ban(db, b.id)
    assert ds[0]["rev"] == "A" and ds[0]["tong_tuy_chon"] == 15e6 and ds[0]["gia_von"] == 80e6 and ds[0]["so_dong"] == 3
    assert ds[0]["bien"] == round((120e6 - 80e6) / 120e6 * 100, 1)
    # khách ép giá: hạ bơm 100 → 90, bớt dòng tùy chọn, thêm dòng vận chuyển
    nd2 = _nd(90e6, them_tuy_chon=False)
    nd2["items"].append({"ten": "Vận chuyển", "so_luong": 1, "don_gia": 3e6, "gia_von": 2e6, "ngoai_du_toan": True})
    b.noi_dung = nd2; db.commit()
    ss = bk.so_sanh_lan_truoc(db, b)
    assert ss["rev"] == "A" and ss["tong_truoc"] == 120e6 and ss["tong_nay"] == 113e6 and ss["chenh_tong"] == -7e6
    assert ss["them"] == ["Vận chuyển"] and ss["bot"] == ["Bộ lọc dự phòng"]
    assert ss["doi_gia"] == [{"ten": "Bơm", "cu": 100e6, "moi": 90e6}]
    r2 = bk.luu_phien_ban(db, b, 1, "kh@x.vn"); db.commit()
    assert r2["rev"] == "B" and len(bk.ds_phien_ban(db, b.id)) == 2


def test_tao_du_toan_tu_bao_gia_va_mien_truoc_moc(db, monkeypatch):
    from app.config import settings
    monkeypatch.setattr(bk, "tim_du_toan", lambda db_, bgf: None)           # chưa có dự toán
    for k, v in (("bg_bien_thiet_bi", 15.0), ("bg_bien_vat_tu", 25.0), ("bg_bien_nhan_cong", 30.0), ("bg_chi_phi_chung", 5.0),
                 ("bg_ap_dung_tu", "2026-10-28")):
        monkeypatch.setattr(settings, k, v)
    monkeypatch.setattr(bk, "ghi_audit", lambda *a, **k: None, raising=False)
    import app.audit as au; monkeypatch.setattr(au, "ghi_audit", lambda *a, **k: None)
    import app.ma_code as mc; monkeypatch.setattr(mc, "bat_buoc", lambda ma, nd, ep, nhan="": ma)
    for tbl in (m.DuToanBan, m.DuToanBanMuc, m.AuditLog):
        tbl.__table__.create(db.get_bind())
    # bảng hang_hoa / khach_hang tối giản (model có kiểu PostgreSQL)
    with db.get_bind().begin() as c:
        c.exec_driver_sql("CREATE TABLE hang_hoa (id INTEGER PRIMARY KEY, ten VARCHAR(200), don_vi VARCHAR(20))")
        c.exec_driver_sql("CREATE TABLE khach_hang (id INTEGER PRIMARY KEY, ma VARCHAR(20), ten VARCHAR(200))")
    nd = {"so": "TM-CU-0826-01", "ngay": "2026-08-20", "tieu_de": "Hóa chất", "vat_pct": 8, "items": [
        {"ten": "PAC", "so_luong": 100, "don_gia": 14000, "don_vi": "kg", "nhom": "VAT_TU"},
        {"ten": "Bơm định lượng", "so_luong": 1, "don_gia": 12000000, "nhom": "THIET_BI"},
        {"ten": "Phụ kiện dự phòng", "so_luong": 1, "don_gia": 2000000, "tuy_chon": True},     # tùy chọn → bỏ
    ]}
    b = m.BaoGiaForm(so="TM-CU-0826-01", noi_dung=nd, trang_thai="DA_GUI"); db.add(b); db.commit()
    class _Nd: id = 1; vai_tro = type("VT", (), {"ma": "NV_KD"})()
    assert bk.mien_truoc_moc(db, b) is True                                   # tạo 20/08, đã gửi → miễn cổng 📋
    b.trang_thai = "NHAP"; assert bk.mien_truoc_moc(db, b) is False           # nháp thì không miễn
    b.trang_thai = "DA_GUI"
    r = bk.tao_du_toan_tu_bao_gia(db, b, _Nd())
    assert r["so_dong"] == 2 and r["co_von"] == 2 and r["ma"] == "TM-CU-0826-01"
    mucs = db.query(m.DuToanBanMuc).filter_by(du_toan_id=r["du_toan_id"]).all()
    gia = {x.ten: float(x.don_gia) for x in mucs}
    assert gia["PAC"] == round(14000 * 0.75 / 1.05 / 1000) * 1000              # vật tư: sàn 25%, chi phí chung 5%
    assert gia["Bơm định lượng"] == round(12000000 * 0.85 / 1.05 / 1000) * 1000
    nd2 = b.noi_dung
    assert nd2["du_toan_id"] == r["du_toan_id"] and nd2["items"][0]["dt_muc_id"] and nd2["items"][0]["gia_von"] == gia["PAC"]
    assert "dt_muc_id" not in nd2["items"][2]                                 # dòng tùy chọn không vào dự toán
    import pytest as _pt
    from fastapi import HTTPException
    monkeypatch.setattr(bk, "tim_du_toan", lambda db_, bgf: {"ma": "TM-CU-0826-01"})
    with _pt.raises(HTTPException):                                          # đã có dự toán → không tạo lại
        bk.tao_du_toan_tu_bao_gia(db, b, _Nd())
