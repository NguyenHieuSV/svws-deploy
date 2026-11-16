"""
🪪 CEO tự tạo vị trí / chức danh (mig 170, app/vi_tri.py — anh Hiếu 16/11/2026): đặt mã từ tên, chép quyền từ vị trí mẫu,
khung JD, đổi tên, xóa có điều kiện; API chỉ CEO. SQLite trong bộ nhớ, audit tắt.
"""
import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app import models as m
from app import vi_tri as vt
from app.routers import cau_hinh as ch


@pytest.fixture()
def db(monkeypatch):
    monkeypatch.setattr(vt, "ghi_audit", lambda *a, **k: None)
    eng = create_engine("sqlite://")
    for t in (m.VaiTro, m.NguoiDung, m.PhanQuyen, m.HanMucDuyet, m.MoTaCongViec, m.KpiViTri, m.NhanVien, m.DanhGiaKy):
        t.__table__.create(eng)
    s = sessionmaker(eng)()
    n = {}

    @event.listens_for(s, "before_flush")
    def _ids(sess, _c, _i):
        for o in sess.new:
            if getattr(o, "id", None) is None:
                n[type(o)] = n.get(type(o), 0) + 1
                o.id = n[type(o)]

    s.add_all([m.VaiTro(ma="CEO", ten="Giám đốc"), m.VaiTro(ma="ADMIN", ten="Admin / IT"),
               m.VaiTro(ma="NV_KTH", ten="NV Kỹ thuật")])
    s.flush()
    s.add_all([m.PhanQuyen(vai_tro_id=1, module="dieu_hanh", muc="QUAN_TRI"),
               m.PhanQuyen(vai_tro_id=3, module="du_an", muc="THAO_TAC"),
               m.PhanQuyen(vai_tro_id=3, module="kho", muc="XEM"),
               m.PhanQuyen(vai_tro_id=3, module="cho_thue", muc="THAO_TAC")])
    s.add(m.NguoiDung(email="ceo@x.vn", mat_khau_hash="x", vai_tro_id=1, trang_thai="HOAT_DONG"))
    s.commit()
    return s


def test_ma_tu_ten():
    assert vt.ma_tu_ten("Trưởng phòng Kỹ thuật") == "TP_KY_THUAT"
    assert vt.ma_tu_ten("Kỹ sư vận hành") == "KS_VAN_HANH"
    assert vt.ma_tu_ten("Nhân viên Điện – Tự động hóa") == "NV_DIEN_TU_DONG_HOA"
    assert vt.ma_tu_ten("Trưởng phòng Kỹ thuật Công nghệ") == "TP_KTCN"                 # quá 20 ký tự → chữ cái đầu
    assert vt.ma_tu_ten("Phó Giám đốc") == "PGD" and vt.ma_tu_ten("Thủ quỹ") == "THU_QUY"
    assert vt.ma_tu_ten("Chuyên viên phân tích dữ liệu kinh doanh quốc tế") == "CV_PTDLKDQT"
    assert vt.ma_tu_ten("2 ca") == "VT_2_CA" and vt.ma_tu_ten("!!!") == "VI_TRI"
    assert all(vt.ma_hop_le(vt.ma_tu_ten(t)) for t in ("Trưởng nhóm thi công", "Lái xe", "Kế toán kho", "QA/QC", "x y"))
    assert vt.ma_hop_le("KS_VAN_HANH") and not vt.ma_hop_le("ks") and not vt.ma_hop_le("1AB") and not vt.ma_hop_le("A" * 21)
    assert vt.ten_chuan("  Kỹ  sư   Vận hành ") == "ky su van hanh"


def test_tao_chep_quyen_va_khung_jd(db):
    r = vt.tao(db, 1, "Kỹ sư vận hành", sao_chep_tu="NV_KTH", ghi_chu="trạm Coats")
    db.commit()
    assert (r["ma"], r["ten"], r["tu_tao"], r["so_quyen_chep"], r["sao_chep_tu"]) == ("KS_VAN_HANH", "Kỹ sư vận hành", True, 3, "NV_KTH")
    assert r["so_quyen"] == 3 and r["so_nguoi_dung"] == 0 and r["xoa_duoc"] and r["sua_duoc"] and r["co_jd"]
    v = db.query(m.VaiTro).filter_by(ma="KS_VAN_HANH").one()
    assert v.tu_tao and v.ghi_chu == "trạm Coats" and v.tao_luc is not None
    assert {(p.module, p.muc) for p in db.query(m.PhanQuyen).filter_by(vai_tro_id=v.id)} == {
        ("du_an", "THAO_TAC"), ("kho", "XEM"), ("cho_thue", "THAO_TAC")}
    assert db.query(m.MoTaCongViec).filter_by(vai_tro="KS_VAN_HANH").one().chuc_danh == "Kỹ sư vận hành"
    # không chép: chưa có quyền; trùng mã tự đặt → thêm _2; mã tự gõ
    r2 = vt.tao(db, 1, "Trưởng nhóm thi công")
    assert r2["ma"] == "TN_THI_CONG" and r2["so_quyen"] == 0 and r2["so_quyen_chep"] == 0
    r3 = vt.tao(db, 1, "Kỹ sư – vận hành 2", ma=" ks van-hanh b ")
    assert r3["ma"] == "KS_VAN_HANH_B"
    db.add(m.VaiTro(ma="THU_QUY", ten="Quỹ")); db.commit()
    assert vt.tao(db, 1, "Thủ quỹ")["ma"] == "THU_QUY_2"
    db.commit()
    ds = {x["ma"]: x for x in vt.danh_sach(db)}
    assert not ds["CEO"]["tu_tao"] and not ds["CEO"]["sua_duoc"] and not ds["CEO"]["xoa_duoc"] and not ds["CEO"]["lam_mau_duoc"]
    assert ds["CEO"]["so_nguoi_dung"] == 1 and ds["NV_KTH"]["lam_mau_duoc"] and ds["KS_VAN_HANH"]["so_quyen"] == 3
    assert [x["ma"] for x in vt.ten_vai_tro(db)][:3] == ["CEO", "ADMIN", "NV_KTH"]


def test_tao_chan_sai(db):
    for ten in ("", " a ", "x" * 121):
        with pytest.raises(ValueError):
            vt.tao(db, 1, ten)
    with pytest.raises(ValueError, match="Đã có vị trí «NV Kỹ thuật»"):
        vt.tao(db, 1, "nv  ky thuat")                                  # trùng tên (không phân biệt dấu / hoa thường)
    with pytest.raises(ValueError, match="Không chép quyền từ CEO"):
        vt.tao(db, 1, "Phó Giám đốc", sao_chep_tu="CEO")
    with pytest.raises(LookupError):
        vt.tao(db, 1, "Phó Giám đốc", sao_chep_tu="KHONG_CO")
    with pytest.raises(ValueError, match="đã có"):
        vt.tao(db, 1, "Kỹ thuật 2", ma="nv_kth")
    with pytest.raises(ValueError, match="Mã vị trí"):
        vt.tao(db, 1, "Kỹ thuật 3", ma="1-KT")
    db.rollback()
    assert db.query(m.VaiTro).count() == 3


def test_sua_va_xoa(db):
    vt.tao(db, 1, "Kỹ sư vận hành", sao_chep_tu="NV_KTH"); db.commit()
    with pytest.raises(ValueError, match="có sẵn của hệ thống"):
        vt.sua(db, 1, "NV_KTH", ten="Kỹ thuật viên")
    with pytest.raises(ValueError, match="có sẵn của hệ thống"):
        vt.xoa(db, 1, "CEO")
    with pytest.raises(LookupError):
        vt.sua(db, 1, "KHONG_CO", ten="abc")
    with pytest.raises(ValueError, match="Đã có vị trí"):
        vt.sua(db, 1, "KS_VAN_HANH", ten="Giám đốc")
    r = vt.sua(db, 1, "ks_van_hanh", ten="Kỹ sư vận hành trạm", ghi_chu=""); db.commit()
    assert r["ten"] == "Kỹ sư vận hành trạm" and r["ma"] == "KS_VAN_HANH" and r["ghi_chu"] is None
    assert db.query(m.MoTaCongViec).filter_by(vai_tro="KS_VAN_HANH").one().chuc_danh == "Kỹ sư vận hành trạm"   # JD đổi theo
    assert vt.sua(db, 1, "KS_VAN_HANH", ten="Kỹ sư vận hành trạm")["ten"] == "Kỹ sư vận hành trạm"                # giữ tên: không báo trùng chính nó
    # còn tài khoản dùng → không xóa
    v = db.query(m.VaiTro).filter_by(ma="KS_VAN_HANH").one()
    db.add(m.NguoiDung(email="ks@x.vn", mat_khau_hash="x", vai_tro_id=v.id, trang_thai="HOAT_DONG")); db.commit()
    assert not vt.mot(db, v)["xoa_duoc"]
    with pytest.raises(ValueError, match="Còn 1 tài khoản đang ở vị trí .*ks@x.vn"):
        vt.xoa(db, 1, "KS_VAN_HANH")
    db.query(m.NguoiDung).filter_by(email="ks@x.vn").delete(); db.commit()
    # có kỳ đánh giá KPI → giữ lại
    db.add(m.DanhGiaKy(nhan_vien_id=1, vai_tro="KS_VAN_HANH", loai_ky="THANG", ky="2026-11")); db.commit()
    with pytest.raises(ValueError, match="đã có kỳ đánh giá KPI"):
        vt.xoa(db, 1, "KS_VAN_HANH")
    db.query(m.DanhGiaKy).delete()
    db.add(m.KpiViTri(vai_tro="KS_VAN_HANH", ten="Tỉ lệ vận hành ổn định")); db.commit()
    kq = vt.xoa(db, 1, "KS_VAN_HANH"); db.commit()
    assert (kq["so_quyen"], kq["so_kpi"], kq["so_jd"]) == (3, 1, 1)
    assert db.query(m.VaiTro).filter_by(ma="KS_VAN_HANH").first() is None
    assert db.query(m.PhanQuyen).count() == 4 and db.query(m.MoTaCongViec).count() == 0 and db.query(m.KpiViTri).count() == 0


def test_api_doi_loi_va_commit(db):
    nd = db.get(m.NguoiDung, 1)
    r = ch.tao_vi_tri(ch.TaoViTri(ten="Trưởng nhóm thi công", sao_chep_tu="NV_KTH"), nd=nd, db=db)
    assert r["ma"] == "TN_THI_CONG" and r["so_quyen_chep"] == 3
    assert [x["ma"] for x in ch.danh_sach_vi_tri(nd=nd, db=db)] == ["CEO", "ADMIN", "NV_KTH", "TN_THI_CONG"]
    with pytest.raises(HTTPException) as e:
        ch.tao_vi_tri(ch.TaoViTri(ten="Trưởng nhóm thi công"), nd=nd, db=db)
    assert e.value.status_code == 400 and "Đã có vị trí" in e.value.detail
    with pytest.raises(HTTPException) as e:
        ch.sua_vi_tri("KHONG_CO", ch.SuaViTri(ten="abc"), nd=nd, db=db)
    assert e.value.status_code == 404
    assert ch.sua_vi_tri("TN_THI_CONG", ch.SuaViTri(ten="Tổ trưởng thi công"), nd=nd, db=db)["ten"] == "Tổ trưởng thi công"
    assert ch.xoa_vi_tri("TN_THI_CONG", nd=nd, db=db)["ok"] and db.query(m.VaiTro).count() == 3
    with pytest.raises(HTTPException) as e:
        ch.xoa_vi_tri("ADMIN", nd=nd, db=db)
    assert e.value.status_code == 400
