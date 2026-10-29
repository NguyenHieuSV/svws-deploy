"""
Droplist «Mã dự án» (mig 156): mã đơn hàng chưa Hoàn thành + mã dự án đã đặt tên chưa xong; giao việc có mã dự án,
nhân viên chọn việc khi báo cáo → «Mã liên quan» tự lấy mã của việc. Không cần PostgreSQL.
"""
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app import models as m
from app.routers import nhan_su as ns


@pytest.fixture()
def db(monkeypatch):
    monkeypatch.setattr(ns, "ghi_audit", lambda *a, **k: None)
    eng = create_engine("sqlite://")
    # du_an / khach_hang / don_hang có kiểu riêng PostgreSQL (ENUM, JSONB) → SQLite dựng bảng tối giản cùng tên cột
    for t in (m.VaiTro, m.NguoiDung, m.NhanVien, m.GiaoViec, m.BaoCaoNgay):
        t.__table__.create(eng)
    with eng.begin() as c:
        c.exec_driver_sql("CREATE TABLE khach_hang (id INTEGER PRIMARY KEY, ma VARCHAR(20), ten VARCHAR(200))")
        c.exec_driver_sql("INSERT INTO khach_hang (id, ten) VALUES (1, 'Coats Phong Phú')")
        c.exec_driver_sql("CREATE TABLE du_an (id INTEGER PRIMARY KEY, ma VARCHAR(30), ten VARCHAR(200), khach_hang_id INTEGER,"
                          " truong_du_an INTEGER, du_toan NUMERIC, chi_phi_thuc_te NUMERIC, qcvn VARCHAR(40),"
                          " trang_thai VARCHAR(20), deadline DATE, chu_dau_tu VARCHAR(200))")
        c.exec_driver_sql("CREATE TABLE don_hang (id INTEGER PRIMARY KEY, so VARCHAR(30), khach_hang_id INTEGER, bao_gia_id INTEGER,"
                          " ngay DATE, tong_tien NUMERIC, tien_thue NUMERIC, trang_thai VARCHAR(20), ty_le_dat_coc NUMERIC,"
                          " thanh_toan_coc NUMERIC, so_hoa_don VARCHAR(60), loai_don VARCHAR(20), tai_san_cho_thue_id INTEGER)")
    s = sessionmaker(eng)()
    n = {}

    @event.listens_for(s, "before_flush")
    def _ids(sess, _c, _i):
        for o in sess.new:
            if getattr(o, "id", None) is None:
                n[type(o)] = n.get(type(o), 0) + 1
                o.id = n[type(o)]

    s.add(m.VaiTro(ma="CEO", ten="Giám đốc")); s.add(m.VaiTro(ma="NV_DA", ten="NV Dự án")); s.flush()
    s.add(m.NguoiDung(email="ceo@x.vn", mat_khau_hash="x", vai_tro_id=1, trang_thai="HOAT_DONG"))
    s.add(m.NguoiDung(email="an@x.vn", mat_khau_hash="x", vai_tro_id=2, trang_thai="HOAT_DONG")); s.flush()
    s.add(m.NhanVien(ma="NV01", ho_ten="An", trang_thai="DANG_LAM", nguoi_dung_id=2)); s.commit()
    with eng.begin() as c:
        c.exec_driver_sql("INSERT INTO don_hang (id, so, khach_hang_id, trang_thai) VALUES"
                          " (1,'DV-COA-NT-1026',1,'DANG_THUC_HIEN'), (2,'TM-SIC-0726-02',1,'HOAN_THANH'),"
                          " (3,'da-coa-0926',1,'MOI'), (4,NULL,1,'MOI'), (5,'DV-COA-NT-1026',1,'DA_XUAT_HD')")
        c.exec_driver_sql("INSERT INTO du_an (id, ma, ten, trang_thai) VALUES (1,'DA-REJ-1026','Hệ RO Rejuvenating','DANG_CHAY'),"
                          " (2,'DA-OLD-0126','Dự án cũ','HOAN_THANH'), (3,NULL,'Chưa đặt mã','MOI')")
    return s


def test_danh_sach_ma_chi_lay_ma_chua_hoan_thanh(db):
    ds = ns.ds_ma_du_an(db, nd=db.get(m.NguoiDung, 2))
    assert [x["ma"] for x in ds] == ["DA-COA-0926", "DA-REJ-1026", "DV-COA-NT-1026"]   # bỏ HOAN_THANH, bỏ mã trống, gộp trùng
    assert {x["ma"]: x["nguon"] for x in ds}["DA-REJ-1026"] == "DU_AN"
    assert {x["ma"]: x["ten"] for x in ds}["DV-COA-NT-1026"] == "Coats Phong Phú"


def test_giao_viec_co_ma_du_an_tu_dien_vao_bao_cao(db):
    ceo, an = db.get(m.NguoiDung, 1), db.get(m.NguoiDung, 2)
    g = ns.tao_giao_viec(ns.GiaoViecVao(email="an@x.vn", ten_cong_viec="Lắp bơm", ma_du_an="dv-coa-nt-1026"), db, nd=ceo)
    assert g["ma_du_an"] == "DV-COA-NT-1026"
    ok = ns.gui_bao_cao_ngay(ns.BaoCaoNgayVao(tien_do=50, ngay="2026-10-27", da_lam="lắp", giao_viec_id=g["id"]), db, nd=an)
    assert db.get(m.BaoCaoNgay, ok["id"]).ma_lien_quan == "DV-COA-NT-1026"          # trống → lấy mã của việc
    ok2 = ns.gui_bao_cao_ngay(ns.BaoCaoNgayVao(tien_do=50, ngay="2026-10-28", da_lam="x", giao_viec_id=g["id"], ma_lien_quan="DA-REJ-1026"),
                              db, nd=an)
    assert db.get(m.BaoCaoNgay, ok2["id"]).ma_lien_quan == "DA-REJ-1026"           # đã chọn mã khác → giữ
    r = ns.sua_giao_viec(g["id"], ns.GiaoViecVao(email="an@x.vn", ten_cong_viec="Lắp bơm", ma_du_an="DA-REJ-1026"), db, nd=ceo)
    assert r["ma_du_an"] == "DA-REJ-1026"
