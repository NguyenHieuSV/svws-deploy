"""
🧭 Xóa PO có dẫn đường (28/10/2026): PO bị chứng từ giữ → liệt kê từng loại + cách gỡ theo thứ tự xử lý
(lệnh đã chi → đợt đã trả → hóa đơn → công nợ → phiếu kho); DELETE trả lỗi 400 có cấu trúc; GET xoa-kiem-tra nêu
thứ sẽ gỡ theo và PO liên quan cùng NCC (cùng số hóa đơn / cùng tổng) kèm cờ xóa được. SQLite trong bộ nhớ.
"""
from datetime import date, datetime

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models as m
from app.routers import ncc


def _raw(con, model, pk="id"):
    """Bảng tối giản cùng tên cột với model (model có kiểu PostgreSQL ENUM)."""
    from sqlalchemy import Integer, Numeric
    kieu = lambda c: ("INTEGER PRIMARY KEY" if c.name == pk else "NUMERIC" if isinstance(c.type, Numeric)   # noqa: E731
                      else "INTEGER" if isinstance(c.type, Integer) else "TEXT")
    cols = ", ".join(f"{c.name} {kieu(c)}" for c in model.__table__.columns)
    con.exec_driver_sql(f"CREATE TABLE {model.__tablename__} ({cols})")


@pytest.fixture()
def db(monkeypatch):
    eng = create_engine("sqlite://")
    for t in (m.DonMua, m.DonMuaCt):
        t.__table__.create(eng)
    with eng.begin() as c:
        for t in (m.NhaCungCap, m.PhieuKho, m.PhieuKhoCt, m.HoaDon, m.CongNo, m.ThanhToan, m.DonMuaDotTt,
                  m.LenhChiBank, m.YeuCauMua, m.TepDinhKem):
            _raw(c, t)
        c.exec_driver_sql("INSERT INTO nha_cung_cap (id, ten) VALUES (5, 'Lọc Miền Nam')")
    monkeypatch.setattr(ncc, "ghi_audit", lambda *a, **k: None)
    return sessionmaker(eng)()


def _po(s, id_, so_hd=None, tong=33_700_000, nhan="CHUA"):
    dm = m.DonMua(id=id_, so=f"PO-{id_}", nha_cung_cap_id=5, trang_thai="DA_DUYET", ngay=date(2026, 10, 20),
                  tien_hang=tong, tien_thue=0, tong_tien=tong, so_hoa_don=so_hd, trang_thai_nhan=nhan)
    s.add(dm); s.flush()
    s.add(m.DonMuaCt(id=id_ * 10 + 1, don_mua_id=id_, hang_hoa_id=1, so_luong=2, don_gia=tong / 2))
    s.commit()
    return dm


class _Nd:
    id = 1


def test_po_sach_xoa_duoc(db):
    _po(db, 101, so_hd="4379")
    db.execute(m.LenhChiBank.__table__.insert().values(id=7, don_mua_id=101, so_tien=10_000_000, trang_thai="CHO_DUYET"))
    db.commit()
    assert ncc._po_chan_xoa(db, db.get(m.DonMua, 101)) == []
    kq = ncc.kiem_tra_xoa_don_mua(101, db, None)
    assert kq["xoa_duoc"] is True and kq["chan"] == [] and kq["po"]["so"] == "PO-101" and kq["po"]["ncc_ten"] == "Lọc Miền Nam"
    assert kq["go_theo"]["dong_hang"] == 1 and kq["go_theo"]["de_xuat"] == 0 and kq["go_theo"]["tep"] == 0
    assert kq["go_theo"]["lenh_chi"] == [{"id": 7, "trang_thai": "CHO_DUYET", "nhan": "chờ duyệt", "so_tien": 10_000_000.0}]
    assert ncc.xoa_don_mua(101, db, _Nd()) == {"ok": True, "so": "PO-101"}
    assert db.get(m.DonMua, 101) is None and db.query(m.LenhChiBank).count() == 0


def _po_bi_giu(db):
    """PO-102: đủ 5 loại chứng từ giữ (ca Lọc Miền Nam HĐ 4379 thật: trùng với PO sạch)."""
    _po(db, 102, so_hd="4379", nhan="DU")
    db.execute(m.PhieuKho.__table__.insert().values(id=1, so="PN-0001", loai="NHAP", don_mua_id=102, ngay=date(2026, 10, 21)))
    db.execute(m.HoaDon.__table__.insert().values(id=30, loai="MUA", so="4379", ngay=date(2026, 10, 21), tong_tien=33_700_000,
                                                  hddt_trang_thai=None, nha_cung_cap_id=5))
    db.execute(m.CongNo.__table__.insert().values(id=40, loai="PHAI_TRA", hoa_don_id=30, nha_cung_cap_id=5, so_tien=33_700_000,
                                                  da_thanh_toan=0, don_mua_id=102, so_ct="4379", trang_thai="CHUA_TRA"))
    db.execute(m.CongNo.__table__.insert().values(id=41, loai="PHAI_TRA", hoa_don_id=None, nha_cung_cap_id=5, so_tien=5_000_000,
                                                  da_thanh_toan=5_000_000, don_mua_id=102, so_ct="4379", trang_thai="DA_TRA",
                                                  ngay_ct=date(2026, 10, 22)))
    db.execute(m.DonMuaDotTt.__table__.insert().values(id=50, don_mua_id=102, ngay=date(2026, 10, 23), so_tien=5_000_000, hinh_thuc="CK"))
    db.execute(m.LenhChiBank.__table__.insert().values(id=60, don_mua_id=102, so_tien=5_000_000, so_tien_dot=5_000_000,
                                                       trang_thai="DA_CHI", chi_luc=datetime(2026, 10, 23, 9, 0)))
    db.commit()
    return db.get(m.DonMua, 102)


def test_chan_theo_thu_tu_xu_ly_va_cach_go(db):
    dm = _po_bi_giu(db)
    chan = ncc._po_chan_xoa(db, dm)
    assert [c["loai"] for c in chan] == ["LENH_CHI", "DOT_TT", "HOA_DON", "CONG_NO", "PHIEU_KHO"]
    assert [c["xoa_duoc"] for c in chan] == [False, False, True, True, False]
    assert all(c["cach"] and c["items"] for c in chan)
    lenh, dot, hd, cn, pk = chan
    assert lenh["ten"] == "1 lệnh chi ĐÃ CHI tiền thật" and lenh["items"][0] == {"id": 60, "so": "Lệnh #60", "ngay": "2026-10-23", "so_tien": 5_000_000.0}
    assert "không xóa PO này" in lenh["cach"] and "xóa PO KIA" in lenh["cach"]
    assert dot["items"][0]["so"] == "Đợt #50" and dot["items"][0]["ghi_chu"] == "CK" and "Thanh toán mua hàng" in dot["cach"]
    assert hd["items"] == [{"id": 30, "so": "4379", "ngay": "2026-10-21", "so_tien": 33_700_000.0, "da_tra": 0.0, "hddt": None, "cong_no_id": 40}]
    assert "Hủy hóa đơn" in hd["cach"]
    assert cn["items"][0]["so"] == "CN-41" and cn["items"][0]["da_tra"] == 5_000_000.0 and cn["items"][0]["so_hd"] == "4379"
    assert "xóa ép" in cn["cach"]
    assert pk["items"] == [{"id": 1, "so": "PN-0001", "ngay": "2026-10-21", "loai": "NHAP"}] and "phiếu xuất trả" in pk["cach"]
    # DELETE: lỗi 400 có cấu trúc, PO còn nguyên
    with pytest.raises(HTTPException) as e:
        ncc.xoa_don_mua(102, db, _Nd())
    d = e.value.detail
    assert e.value.status_code == 400 and d["ma"] == "PO_DANG_GAN" and d["so"] == "PO-102" and len(d["chan"]) == 5
    assert d["msg"].startswith("PO 'PO-102' đang gắn với 1 lệnh chi ĐÃ CHI tiền thật, 1 đợt đã trả")
    assert db.get(m.DonMua, 102) is not None


def test_kiem_tra_neu_po_lien_quan(db):
    _po_bi_giu(db)
    _po(db, 103, so_hd=" 0004379 ", tong=30_000_000)    # cùng số hóa đơn (chuẩn hóa bỏ 0 đầu / khoảng trắng), chưa gì giữ
    _po(db, 104, so_hd=None, tong=33_700_000)           # cùng tổng tiền
    _po(db, 105, so_hd="4284", tong=1_000_000)          # không liên quan
    kq = ncc.kiem_tra_xoa_don_mua(102, db, None)
    assert kq["xoa_duoc"] is False and len(kq["chan"]) == 5 and kq["po"]["da_tra"] == 0.0
    lq = {p["id"]: p for p in kq["po_lien_quan"]}
    assert set(lq) == {103, 104}
    assert lq[103]["ly_do"] == "cùng số hóa đơn" and lq[103]["xoa_duoc"] is True and lq[103]["giu_boi"] == []
    assert lq[104]["ly_do"] == "cùng tổng tiền" and lq[104]["xoa_duoc"] is True
    # nhìn từ PO sạch: PO-102 là bản bị giữ → gợi ý giữ 102, xóa 103
    kq3 = ncc.kiem_tra_xoa_don_mua(103, db, None)
    assert kq3["xoa_duoc"] is True
    p102 = next(p for p in kq3["po_lien_quan"] if p["id"] == 102)
    assert p102["xoa_duoc"] is False and p102["nhan_du"] is True and p102["ly_do"] == "cùng số hóa đơn"
    assert p102["giu_boi"] == ["1 lệnh chi ĐÃ CHI tiền thật", "1 đợt đã trả ghi ở Thanh toán mua hàng", "1 hóa đơn mua",
                               "1 công nợ phải trả", "1 phiếu kho (đã nhận hàng)"]
    with pytest.raises(HTTPException) as e:
        ncc.kiem_tra_xoa_don_mua(999, db, None)
    assert e.value.status_code == 404
