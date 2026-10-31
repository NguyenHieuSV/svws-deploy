"""
💾 Sao lưu CSDL (31/10/2026, mig 164): xuất ZIP (manifest + schema + CSV từng bảng) → nạp lại đúng kiểu dữ liệu
(Decimal, ngày, bool, JSON, xuống dòng / dấu phẩy); tạo bản + nhật ký + mốc «hôm nay đã sao lưu»; dọn bản cũ theo quy tắc giữ.
SQLite trong bộ nhớ, kho tệp giả bằng thư mục tạm.
"""
import json
import os
import zipfile
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import luu_tru
from app import models as m
from app import sao_luu_service as sl
from app.config import settings
from app.database import Base

TABLES = (m.NhaCungCap, m.SanPhamNcc, m.DuToanBan, m.DuToanBanMuc, m.BaoGiaForm, m.SaoLuuLog)
NOW = datetime(2026, 10, 31, 12, 0, 0)


def _eng():
    eng = create_engine("sqlite://")
    for t in TABLES:
        t.__table__.create(eng)
    return eng


def _ss(eng):
    """Session SQLite: BigInteger id không tự tăng → gán id tăng dần khi flush (như các test khác)."""
    from sqlalchemy import event
    s = sessionmaker(eng)()
    n = {}

    @event.listens_for(s, "before_flush")
    def _ids(sess, _c, _i):
        for o in sess.new:
            if getattr(o, "id", None) is None:
                n[type(o)] = n.get(type(o), 0) + 1
                o.id = n[type(o)]
    return s


def test_xuat_zip_va_nap_lai(tmp_path, monkeypatch):
    monkeypatch.setattr(sl, "_gio_vn", lambda: NOW)
    eng = _eng()
    s = sessionmaker(eng)()
    s.add(m.NhaCungCap(id=1, ten="NCC A"))
    s.add(m.SanPhamNcc(id=1, nha_cung_cap_id=1, ten="Bơm", don_gia=Decimal("1500000"), spec="x\ny,z \"q\""))
    s.add(m.DuToanBan(id=1, ma="DT-1", ngay=date(2026, 10, 31), gia_uoc=True))
    s.add(m.DuToanBanMuc(id=1, du_toan_id=1, ten="Ống", so_luong=Decimal("2.5"), don_gia=1000))
    s.add(m.BaoGiaForm(id=1, so="BG-1", noi_dung={"items": [{"ten": "a", "sl": 1}], "x": "ă"}, trang_thai="NHAP"))
    s.commit()
    z = str(tmp_path / "a.zip")
    kq = sl.xuat_zip(eng, z)
    assert kq["so_bang"] == len(TABLES) and kq["bang"]["san_pham_ncc"] == 1 and kq["so_dong"] == 5 and kq["kich_thuoc"] > 0
    with zipfile.ZipFile(z) as zf:
        names = zf.namelist()
        mf = json.loads(zf.read("manifest.json"))
        assert "data/bao_gia_form.csv" in names and any(n.startswith("schema/") and n.endswith(".sql") for n in names)
        assert mf["bang"]["du_toan_ban"] == 1 and mf["dialect"] == "sqlite" and mf["tao_luc"].startswith("2026-10-31")
        assert mf["pg_dump"] == "không có pg_dump"
    # nạp vào CSDL trống khác → đúng kiểu
    eng2 = _eng()
    kq2 = sl.nap_zip(eng2, z, metadata=Base.metadata)
    assert kq2["bang"]["san_pham_ncc"] == 1 and kq2["bang"]["bao_gia_form"] == 1 and kq2["bo_qua"] == []
    s2 = sessionmaker(eng2)()
    sp = s2.get(m.SanPhamNcc, 1)
    assert sp.don_gia == Decimal("1500000") and sp.spec == "x\ny,z \"q\"" and sp.nha_cung_cap_id == 1
    d = s2.get(m.DuToanBan, 1)
    assert d.gia_uoc is True and d.ngay == date(2026, 10, 31) and d.ma == "DT-1"
    assert s2.get(m.DuToanBanMuc, 1).so_luong == Decimal("2.5")
    assert s2.get(m.BaoGiaForm, 1).noi_dung == {"items": [{"ten": "a", "sl": 1}], "x": "ă"}
    # nạp lần 2 (xóa dữ liệu cũ) không bị trùng khóa
    kq3 = sl.nap_zip(eng2, z, metadata=Base.metadata)
    assert kq3["bang"]["san_pham_ncc"] == 1 and s2.query(m.SanPhamNcc).count() == 1


def test_tao_ban_sao_nhat_ky_va_don_dep(tmp_path, monkeypatch):
    monkeypatch.setattr(sl, "_gio_vn", lambda: NOW)
    eng = _eng()
    import app.database as dbm
    monkeypatch.setattr(dbm, "engine", eng)

    def _luu(data, nhom, oid, ten, ct=None):
        p = tmp_path / ten
        p.write_bytes(data)
        return str(p)
    xoa = []
    monkeypatch.setattr(luu_tru, "luu", _luu)
    monkeypatch.setattr(luu_tru, "xoa", lambda ref: xoa.append(ref))
    monkeypatch.setattr(settings, "sao_luu_bat", True)
    monkeypatch.setattr(settings, "sao_luu_gio", 2)
    monkeypatch.setattr(settings, "sao_luu_giu_ngay", 30)
    monkeypatch.setattr(settings, "sao_luu_giu_thang", 12)
    s = _ss(eng)
    assert sl.den_han(s, NOW) is True                                        # 12h > 2h, chưa có bản nào
    assert sl.den_han(s, NOW.replace(hour=1)) is False                       # chưa đến giờ
    kq = sl.tao_ban_sao(s, "TAY", 1)
    assert kq["ok"] and kq["trang_thai"] == "THANH_CONG" and kq["so_bang"] == len(TABLES) and os.path.exists(kq["duong_dan"])
    assert kq["ten_file"] == "svws-20261031-120000.zip" and kq["nguon"] == "TAY"
    assert sl.den_han(s, NOW.replace(hour=23)) is False                      # hôm nay đã có bản thành công
    assert sl.danh_sach(s)[0]["co_file"] is True
    # dọn bản cũ: giữ 30 ngày gần nhất + bản ĐẦU mỗi tháng trong 12 tháng
    for d in (3, 40, 45, 70, 400):
        t = NOW - timedelta(days=d)
        s.add(m.SaoLuuLog(ten_file=f"cu-{d}.zip", duong_dan=f"/x/cu-{d}.zip", bat_dau=t, ket_thuc=t,
                          trang_thai="THANH_CONG", nguon="TU_DONG"))
    s.commit()
    n = sl.don_dep(s)
    # 3 ngày → giữ; 40 (21/09) và 45 (16/09) cùng tháng 9 → giữ bản sớm nhất (45), xóa 40; 70 (22/08) → giữ; 400 → quá 12 tháng → xóa
    assert n == 2 and sorted(x.split("/")[-1] for x in xoa) == ["cu-40.zip", "cu-400.zip"]
    tt = {x.ten_file: x.trang_thai for x in s.query(m.SaoLuuLog).all()}
    assert tt["cu-40.zip"] == "DA_XOA" and tt["cu-45.zip"] == "THANH_CONG" and tt["cu-70.zip"] == "THANH_CONG"


def test_tao_ban_sao_loi_ghi_nhat_ky(monkeypatch):
    monkeypatch.setattr(sl, "_gio_vn", lambda: NOW)
    eng = _eng()
    import app.database as dbm
    monkeypatch.setattr(dbm, "engine", eng)

    def _hong(*a, **k):
        raise RuntimeError("kho tệp từ chối")
    monkeypatch.setattr(luu_tru, "luu", _hong)
    s = _ss(eng)
    kq = sl.tao_ban_sao(s, "TU_DONG")
    assert kq["ok"] is False and kq["trang_thai"] == "LOI" and "kho tệp từ chối" in kq["loi"]
    assert sl.den_han(s, NOW) is True                                        # lỗi → vẫn đến hạn để thử lại
