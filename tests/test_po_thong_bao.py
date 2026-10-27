"""
🛒 Báo nhóm Purchasing Team khi có ĐƠN MUA mới (27/10/2026): bắt sự kiện commit, soạn tin có mã dự án + sản phẩm.
Không cần PostgreSQL (SQLite, bảng tối giản theo đúng cột được đọc).
"""
from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models as m
from app import po_thong_bao as pt
from app.config import settings


@pytest.fixture()
def eng():
    e = create_engine("sqlite://")
    for t in (m.DonMua, m.DonMuaCt):
        t.__table__.create(e)
    with e.begin() as c:
        c.exec_driver_sql("CREATE TABLE hang_hoa (id INTEGER PRIMARY KEY, ten VARCHAR(200), don_vi VARCHAR(20))")
        c.exec_driver_sql("CREATE TABLE nha_cung_cap (id INTEGER PRIMARY KEY, ten VARCHAR(200))")
        c.exec_driver_sql("CREATE TABLE don_hang (id INTEGER PRIMARY KEY, so VARCHAR(30))")
        c.exec_driver_sql("CREATE TABLE du_toan_ban (id INTEGER PRIMARY KEY, ma VARCHAR(30))")
        c.exec_driver_sql("CREATE TABLE du_toan_ban_muc (id INTEGER PRIMARY KEY, du_toan_id INTEGER, don_mua_id INTEGER)")
        c.exec_driver_sql("CREATE TABLE du_an (id INTEGER PRIMARY KEY, ma VARCHAR(30))")
        c.exec_driver_sql("CREATE TABLE du_an_du_toan (id INTEGER PRIMARY KEY, du_an_id INTEGER, don_mua_id INTEGER)")
        c.exec_driver_sql("INSERT INTO hang_hoa VALUES (1,'Hóa chất PAC','kg'),(2,'Van bi 60',NULL)")
        c.exec_driver_sql("INSERT INTO nha_cung_cap VALUES (5,'Hóa chất Miền Nam')")
        c.exec_driver_sql("INSERT INTO don_hang VALUES (9,'TM-SIC-1026-01')")
        c.exec_driver_sql("INSERT INTO du_toan_ban VALUES (3,'DV-COA-NT-1026')")
    return e


def _po(s, id_, **kw):
    dm = m.DonMua(id=id_, so=f"PO-{id_}", nha_cung_cap_id=5, trang_thai="CHO_DUYET", ngay=date(2026, 10, 27),
                  tien_hang=0, tien_thue=0, tong_tien=0, **kw)
    s.add(dm); s.flush()
    s.add(m.DonMuaCt(id=id_ * 10 + 1, don_mua_id=id_, hang_hoa_id=1, so_luong=1000, don_gia=9000))
    s.add(m.DonMuaCt(id=id_ * 10 + 2, don_mua_id=id_, hang_hoa_id=2, so_luong=2.5, don_gia=90000))
    return dm


def test_tin_co_ma_du_toan_va_san_pham(eng):
    s = sessionmaker(eng)()
    _po(s, 101, ngay_hen_giao=date(2026, 10, 30)); s.commit()
    with eng.begin() as c:
        c.exec_driver_sql("INSERT INTO du_toan_ban_muc VALUES (1,3,101)")
    t = pt.noi_dung_po(s, 101)
    assert "PO-101 · Chờ duyệt" in t and "Mã dự án: *DV-COA-NT-1026* (lập từ Dự toán hàng bán)" in t
    assert "Nhà cung cấp: Hóa chất Miền Nam" in t
    assert "– Hóa chất PAC — 1.000 kg" in t and "– Van bi 60 — 2,50" in t and "Hẹn giao: 30/10/2026" in t
    _po(s, 102, ma_ban="DV-COA-RO30-0926"); s.commit()
    assert "Mã dự án: *DV-COA-RO30-0926* (lập tay)" in pt.noi_dung_po(s, 102)
    _po(s, 103, don_hang_id=9); s.commit()
    assert "Mã dự án: *TM-SIC-1026-01* (lập tay)" in pt.noi_dung_po(s, 103)
    _po(s, 104); s.commit()
    assert "Mã dự án: — chưa gắn mã" in pt.noi_dung_po(s, 104)
    assert pt.noi_dung_po(s, 999) is None


def test_commit_po_moi_thi_phat_tin_mot_lan(eng, monkeypatch):
    pt.dang_ky()
    phat = []
    monkeypatch.setattr(pt, "_phat", lambda ids: phat.append(list(ids)))
    s = sessionmaker(eng)()
    monkeypatch.setattr(settings, "gchat_webhook_purchasing", "")
    _po(s, 201); s.commit()
    assert phat == []                                            # chưa khai webhook → không gửi
    monkeypatch.setattr(settings, "gchat_webhook_purchasing", "https://chat.example/webhook")
    _po(s, 202); _po(s, 203); s.commit()
    assert phat == [[202, 203]]                                  # một lần commit, đủ 2 PO
    po = s.get(m.DonMua, 202); po.trang_thai = "DA_DUYET"; s.commit()
    assert phat == [[202, 203]]                                  # sửa / duyệt PO cũ không báo lại
    _po(s, 204); s.rollback()
    s.commit()
    assert phat == [[202, 203]]                                  # PO bị hủy (rollback) không báo
