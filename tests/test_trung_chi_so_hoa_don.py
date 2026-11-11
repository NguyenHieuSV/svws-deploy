"""
Chống trùng ở Duyệt chi / Rà trùng (anh Hiếu chốt 11/11/2026): CHỈ bắt khi CÙNG nhà cung cấp + CÙNG số hóa đơn
ở PO / công nợ khác nhau. Các tiêu chí «cùng số tiền» (lệnh cùng đợt, PO cùng tổng) đã bỏ. SQLite trong bộ nhớ.
"""
from datetime import date

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models as m
from app.routers import ncc


def _lenh(id_, ncc_id=5, so_hd=None, tien=10_000_000, po=None, cn=None, tt="CHO_DUYET", ngay="2026-11-10"):
    return {"id": id_, "so": f"PO-{po}" if po else f"CN-{cn}", "ncc_id": ncc_id, "so_hoa_don": so_hd, "so_tien": tien,
            "so_tien_chi": tien, "don_mua_id": po, "cong_no_id": cn, "trang_thai": tt, "de_nghi_luc": ngay}


# ------------------------- nhãn ⚠ nghi trùng ở bảng Duyệt chi -------------------------
def test_cung_so_tien_khong_con_bi_gan_nhan():
    a, b = _lenh(1, so_hd="111", po=10), _lenh(2, so_hd="222", po=11)          # cùng NCC, cùng tiền, cùng ngày, KHÁC hóa đơn
    c, d = _lenh(3, po=12), _lenh(4, po=12)                                    # cùng PO, cùng tiền, chưa có số hóa đơn
    ncc._lcb_gan_nghi_trung([a, b, c, d], [_lenh(9, so_hd="333", po=13, tt="DA_CHI")])
    assert [x["nghi_trung"] for x in (a, b, c, d)] == [[], [], [], []]


def test_cung_ncc_cung_so_hoa_don_o_chung_tu_khac_thi_bat():
    a = _lenh(1, so_hd="HD 4379", po=80, tien=33_700_000)
    da_chi = _lenh(2, so_hd="hd-4379", po=81, tien=20_000_000, tt="DA_CHI")    # khác số tiền, khác hoa/thường + dấu gạch
    ncc._lcb_gan_nghi_trung([a], [da_chi])
    assert len(a["nghi_trung"]) == 1
    t = a["nghi_trung"][0]
    assert t["id"] == 2 and t["manh"] is True and t["trang_thai"] == "DA_CHI" and "cùng số hóa đơn" in t["ly_do"]


def test_khong_bat_khi_khac_ncc_cung_chung_tu_hoac_da_xac_nhan():
    a = _lenh(1, so_hd="4379", po=80)
    ncc._lcb_gan_nghi_trung([a], [_lenh(2, ncc_id=6, so_hd="4379", po=90, tt="DA_CHI")])     # NCC khác trùng số hóa đơn
    assert a["nghi_trung"] == []
    ncc._lcb_gan_nghi_trung([a], [_lenh(3, so_hd="4379", po=80, tt="DA_CHI")])               # cùng PO = trả nhiều đợt
    assert a["nghi_trung"] == []
    ncc._lcb_gan_nghi_trung([a], [_lenh(4, so_hd="4379", po=81, tt="DA_CHI")],
                            bo_qua={("HOA_DON", f"5|{_chuan('4379')}")})
    assert a["nghi_trung"] == []                                                             # CEO đã bấm ✅ Không trùng


def _chuan(s):
    from app.lai_lo_ma import so_hd_chuan
    return so_hd_chuan(s)


# ------------------------- 🔍 Rà trùng toàn bộ -------------------------
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
        for t in (m.NhaCungCap, m.CongNo, m.ThanhToan, m.DonMuaDotTt, m.LenhChiBank, m.NghiTrungBoQua):
            _raw(c, t)
        c.exec_driver_sql("INSERT INTO nha_cung_cap (id, ten) VALUES (5, 'Lọc Miền Nam')")
    monkeypatch.setattr(ncc, "ghi_audit", lambda *a, **k: None)
    return sessionmaker(eng)()


def _po(s, id_, so_hd=None, tong=33_700_000, ngay=date(2026, 11, 1)):
    s.add(m.DonMua(id=id_, so=f"PO-{id_}", nha_cung_cap_id=5, trang_thai="DA_DUYET", ngay=ngay,
                   tien_hang=tong, tien_thue=0, tong_tien=tong, so_hoa_don=so_hd, trang_thai_nhan="CHUA"))
    s.commit()


class _Ceo:
    id = 1


def test_ra_trung_chi_con_nhom_cung_so_hoa_don(db):
    _po(db, 35, tong=794_880_000); _po(db, 36, tong=794_880_000)               # hai PO cùng NCC cùng tổng tiền, cùng ngày, chưa có HĐ
    _po(db, 80, so_hd="4379"); _po(db, 81, so_hd=" 0004379", tong=12_000_000)  # cùng số hóa đơn (khác số 0 đầu), khác tiền
    for i, po in ((1, 35), (2, 36)):                                           # hai lệnh đã chi cùng số tiền ở hai PO khác nhau
        db.execute(m.LenhChiBank.__table__.insert().values(id=i, don_mua_id=po, so_tien=5_400_000, so_tien_dot=5_400_000,
                                                           trang_thai="DA_CHI"))
    db.commit()
    r = ncc.ra_trung(30, db, None)
    assert r["tong"] == {"hoa_don": 1, "po_cung_tien": 0, "lenh_cung_tien": 0}
    assert r["po_cung_tien"] == [] and r["lenh_cung_tien"] == []
    g = r["hoa_don"][0]
    assert g["ncc_ten"] == "Lọc Miền Nam" and sorted(x["so"] for x in g["items"]) == ["PO-80", "PO-81"]


def test_khong_trung_chi_nhan_nhom_hoa_don(db):
    _po(db, 80, so_hd="4379"); _po(db, 81, so_hd="4379")
    khoa = ncc.ra_trung(30, db, None)["hoa_don"][0]["khoa"]
    for loai in ("PO_TIEN", "LENH_TIEN"):                                      # hai loại cũ không còn nhận
        with pytest.raises(HTTPException) as e:
            ncc.ra_trung_bo_qua(ncc.BoQuaTrungVao(loai=loai, khoa="5|100"), db, _Ceo())
        assert e.value.status_code == 400
    db.add(m.NghiTrungBoQua(id=1, loai="PO_TIEN", khoa="5|794880000", mo_ta="dòng cũ"))   # dòng cũ trong bảng: giữ, không hiện
    db.commit()
    assert ncc.ra_trung(30, db, None)["da_bo_qua"] == []
    ncc.ra_trung_bo_qua(ncc.BoQuaTrungVao(loai="HOA_DON", khoa=khoa, ly_do="hai lô hàng"), db, _Ceo())
    r = ncc.ra_trung(30, db, None)
    assert r["tong"]["hoa_don"] == 0 and [x["loai"] for x in r["da_bo_qua"]] == ["HOA_DON"]
