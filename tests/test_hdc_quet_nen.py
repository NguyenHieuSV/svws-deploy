"""
⏳ Quét hóa đơn mua từ email ở LUỒNG NỀN (06/11/2026, app/hdc_quet_nen.py): tạo lượt trả ngay, trạng thái / tiến độ,
không chạy hai lượt song song, tự lặp khi còn thư mới (25 thư mới mỗi lượt), lỗi hộp thư → LOI, dòng kẹt quá hạn → đóng,
và 3 endpoint /ke-toan/hoa-don-cho/quet-nen. SQLite trong bộ nhớ dùng chung một kết nối (StaticPool) cho mọi session;
hộp thư giả qua monkeypatch lay_inbound_provider (không IMAP, thư cổng EasyInvoice đọc theo nhãn nên không gọi AI).
"""
import threading
from datetime import timedelta

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import hdc_quet_nen as hqn
from app import inbound_gateway as ig
from app import models as m
from app.nhac_viec_service import gio_hien_tai

TABLES = (m.VaiTro, m.NguoiDung, m.PhanQuyen, m.AuditLog, m.NhaCungCap, m.CtNccEmail, m.DonMua, m.KtHoaDonCho,
          m.KtHdGuiKhach, m.ViecNen, m.LichQuetMail)
THAN = """Kính gửi Quý khách hàng,
{ten}, Mã số thuế {mst} xin trân trọng cảm ơn Quý khách hàng đã tin dùng dịch vụ, hàng hóa của chúng tôi.
{ten} vừa phát hành hóa đơn điện tử đến Quý khách CÔNG TY TNHH GIẢI PHÁP KỸ THUẬT SÓNG VIỆT, Mã số thuế 0303620066 với thông tin chi tiết như sau:
Ký hiệu mẫu số hóa đơn: 1C26TTT
Số hóa đơn: {so}
Ngày hóa đơn: 05/11/2026
Tiền thuế: 776,000 VND
Tổng tiền thanh toán: 10,476,000 VND
Mã của cơ quan thuế: 00E2D487586D814BA2B561D0497110A6E9
Mã tra cứu: MA{so}
Quý khách vui lòng truy cập link (http://{mst}hd.easyinvoice.com.vn/tra-cuu?ma=MA{so}) để xem và kiểm tra hóa đơn gốc.
Chú ý: Đây là mail tự động từ hệ thống."""


def _thu_hd(so, ten="CÔNG TY TNHH TM - SX CƠ KHÍ TUẤN TÀI", mst="3703058418"):
    return {"tu_email": "hoadon-noreply@easyinvoice.vn",
            "tieu_de": f"Hóa đơn điện tử số: {so} - {ten} kính gửi khách hàng CÔNG TY TNHH GIẢI PHÁP KỸ THUẬT SÓNG VIỆT",
            "noi_dung": THAN.format(ten=ten, mst=mst, so=so), "message_id": f"<hd-{so}@easyinvoice.vn>", "dinh_kem": []}


THU_KHAC = {"tu_email": "ai@do.vn", "tieu_de": "Chào hỏi", "noi_dung": "Hẹn gặp anh tuần sau.", "message_id": "<khac-1@do.vn>"}


class _HopThu:
    """Hộp thư giả: da_vao bật khi lượt bắt đầu lấy thư; cho (nếu có) giữ luồng nền lại cho tới khi test cho đi tiếp."""
    ten = "GIA"

    def __init__(self, thu, cho=None, da_vao=None, loi=None):
        self.thu, self.cho, self.da_vao, self.loi, self.so_lan = thu, cho, da_vao, loi, 0

    def lay_thu(self, tu_ngay=None):
        self.so_lan += 1
        if self.da_vao is not None:
            self.da_vao.set()
        if self.cho is not None:
            assert self.cho.wait(30), "test không cho luồng nền đi tiếp"
        if self.loi:
            raise RuntimeError(self.loi)
        return list(self.thu)


@pytest.fixture()
def moi_truong(monkeypatch):
    """(sessionmaker, NguoiDung) — SessionLocal của luồng nền trỏ vào CSDL thử; id BigInteger tự gán khi flush."""
    eng = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    for t in TABLES:
        t.__table__.create(eng)
    SL = sessionmaker(eng, autoflush=False, expire_on_commit=False)
    n, khoa = {}, threading.Lock()

    @event.listens_for(SL, "before_flush")
    def _ids(sess, _c, _i):
        with khoa:
            for o in sess.new:
                if getattr(o, "id", None) is None:
                    n[type(o)] = n.get(type(o), 0) + 1
                    o.id = n[type(o)]

    monkeypatch.setattr(hqn, "SessionLocal", SL)
    s = SL()
    s.add(m.VaiTro(ma="KTT", ten="Kế toán trưởng")); s.flush()
    s.add(m.PhanQuyen(vai_tro_id=1, module="ke_toan", muc="THAO_TAC"))
    nd = m.NguoiDung(email="kt@svws.vn", mat_khau_hash="x", vai_tro_id=1, trang_thai="HOAT_DONG")
    s.add(nd)
    s.add(m.NhaCungCap(ten="Cơ khí Tuấn Tài", ma_so_thue="3703058418", email="kt@tuantai.vn"))
    s.commit()
    yield SL, nd
    s.close()
    hqn._luong.clear()


def _dat_hop_thu(monkeypatch, prov):
    monkeypatch.setattr(ig, "lay_inbound_provider", lambda: prov)
    return prov


def _xem(SL, vid):
    s = SL()
    try:
        return hqn.to_dict(s.get(m.ViecNen, vid))
    finally:
        s.close()


def test_tao_luot_trang_thai_va_khong_song_song(moi_truong, monkeypatch):
    SL, nd = moi_truong
    cho, da_vao = threading.Event(), threading.Event()
    prov = _dat_hop_thu(monkeypatch, _HopThu([_thu_hd(277), _thu_hd(278), THU_KHAC], cho=cho, da_vao=da_vao))
    moc = (gio_hien_tai() - timedelta(days=8)).date()
    db = SL()
    v, moi = hqn.bat_dau(db, nd, moc)
    assert moi and v.trang_thai == "DANG_CHAY" and v.loai == hqn.LOAI and v.nguoi_dung_id == nd.id
    assert da_vao.wait(10)                                   # luồng nền đã vào lấy thư và đang đứng chờ
    # đang chạy → bấm lần nữa trả đúng lượt đó, không tạo lượt mới
    v2, moi2 = hqn.bat_dau(db, nd, moc)
    assert (v2.id, moi2) == (v.id, False)
    d = _xem(SL, v.id)
    assert d["dang_chay"] and d["trang_thai"] == "DANG_CHAY" and d["tu_ngay"] == str(moc) and not d["gan_day"]
    assert d["tien_do"]["buoc"] == "DANG_LAY_THU" and d["tien_do"]["luot"] == 1 and d["tien_do"]["toi_da_luot"] == hqn.TOI_DA_LUOT
    assert hqn.moi_nhat(db).id == v.id
    db.close()
    cho.set()
    assert hqn.cho_xong(v.id, 60)
    d = _xem(SL, v.id)
    assert d["trang_thai"] == "XONG" and not d["dang_chay"] and d["gan_day"] and d["ket_thuc"]
    kq = d["ket_qua"]
    assert kq["luot"] == 1 and kq["thu_moi"] == 3 and kq["da_them"] == 2 and kq["doc_nhan"] == 2 and kq["ai"] == 0
    assert kq["khong_khop"] == 1 and kq["con_lai"] == 0 and kq["loi"] == [] and kq["che_do"] == "GIA"
    assert d["tien_do"]["buoc"] == "XONG" and d["tien_do"]["so_thu"] == 3 and d["tien_do"]["da_them"] == 2
    s = SL()
    rows = s.query(m.KtHoaDonCho).order_by(m.KtHoaDonCho.so_hoa_don).all()
    assert [r.so_hoa_don for r in rows] == ["277", "278"]
    assert all(r.nguon_doc == "NHAN" and int(r.tong_tien) == 10_476_000 and r.nha_cung_cap_id == 1 for r in rows)
    s.close()
    # lượt sau với cùng hộp thư: thư đã có → trùng, không thêm; vẫn tạo được lượt mới vì lượt cũ đã xong
    prov.cho = None
    db = SL()
    v3, moi3 = hqn.bat_dau(db, nd, moc)
    db.close()
    assert moi3 and v3.id != v.id
    assert hqn.cho_xong(v3.id, 60)
    kq3 = _xem(SL, v3.id)["ket_qua"]
    assert kq3["da_them"] == 0 and kq3["trung_bo_qua"] == 2 and kq3["khong_khop"] == 1 and prov.so_lan == 2


def test_tu_lap_khi_con_thu_moi(moi_truong, monkeypatch):
    SL, nd = moi_truong
    prov = _dat_hop_thu(monkeypatch, _HopThu([_thu_hd(so) for so in range(101, 131)]))     # 30 thư mới > giới hạn 25 / lượt
    db = SL()
    v, moi = hqn.bat_dau(db, nd, (gio_hien_tai() - timedelta(days=30)).date())
    db.close()
    assert moi and hqn.cho_xong(v.id, 120)
    d = _xem(SL, v.id)
    kq = d["ket_qua"]
    assert d["trang_thai"] == "XONG" and prov.so_lan == 2 and kq["luot"] == 2
    assert kq["da_them"] == 30 and kq["doc_nhan"] == 30 and kq["thu_moi"] == 30       # cộng dồn 25 + 5
    assert kq["trung_bo_qua"] == 25 and kq["con_lai"] == 0                              # trạng thái lượt cuối
    s = SL()
    assert s.query(m.KtHoaDonCho).filter_by(trang_thai="CHO_XAC_NHAN").count() == 30
    s.close()


def test_loi_hop_thu_va_dong_kiet(moi_truong, monkeypatch):
    SL, nd = moi_truong
    _dat_hop_thu(monkeypatch, _HopThu([], loi="IMAP timeout"))
    db = SL()
    v, _ = hqn.bat_dau(db, nd, gio_hien_tai().date())
    db.close()
    assert hqn.cho_xong(v.id, 60)
    d = _xem(SL, v.id)
    assert d["trang_thai"] == "LOI" and d["ket_qua"]["luot"] == 0
    assert d["ket_qua"]["loi"] == ["Lượt 1: Không đọc được hộp thư (GIA): IMAP timeout"]
    # dòng DANG_CHAY kẹt từ lần máy chủ khởi động lại (quá 2 giờ) → không chặn, đóng là LOI
    s = SL()
    ket = m.ViecNen(loai=hqn.LOAI, trang_thai="DANG_CHAY", bat_dau=gio_hien_tai() - timedelta(hours=3),
                    ket_qua={"tu_ngay": "2026-10-01"})
    s.add(ket); s.commit()
    assert hqn.dang_chay(s) is None and ket.trang_thai == "LOI" and ket.ket_thuc and "khởi động lại" in ket.ket_qua["loi"][0]
    s.commit()
    # dòng DANG_CHAY còn trong hạn → vẫn là lượt đang chạy
    moi_r = m.ViecNen(loai=hqn.LOAI, trang_thai="DANG_CHAY", bat_dau=gio_hien_tai() - timedelta(minutes=5), ket_qua={})
    s.add(moi_r); s.commit()
    assert hqn.dang_chay(s) is moi_r and hqn.moi_nhat(s) is moi_r
    s.close()


def test_endpoint_quet_nen(moi_truong, monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.database import get_db
    from app.deps import lay_nguoi_dung_hien_tai
    SL, nd = moi_truong

    def _db():
        s = SL()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = _db
    app.dependency_overrides[lay_nguoi_dung_hien_tai] = lambda: nd
    try:
        c = TestClient(app)
        cho, da_vao = threading.Event(), threading.Event()
        _dat_hop_thu(monkeypatch, _HopThu([_thu_hd(301), _thu_hd(302)], cho=cho, da_vao=da_vao))
        assert c.post("/ke-toan/hoa-don-cho/quet-nen?tu_ngay=2099-01-01").status_code == 400     # mốc sau hôm nay
        # 📬 lượt quét thư hàng tuần đang chạy → không cho chạy chồng
        s = SL()
        lq = m.LichQuetMail(nguon="LICH", bat_dau=gio_hien_tai(), trang_thai="DANG_CHAY")
        s.add(lq); s.commit()
        r = c.post("/ke-toan/hoa-don-cho/quet-nen")
        assert r.status_code == 400 and "hàng tuần" in r.json()["detail"]
        lq.trang_thai = "XONG"; s.commit(); s.close()
        assert c.get("/ke-toan/hoa-don-cho/quet-nen").json() is None                             # chưa từng quét nền
        r = c.post("/ke-toan/hoa-don-cho/quet-nen?tu_ngay=2026-10-01").json()
        assert r["moi"] and r["dang_chay"] and r["tu_ngay"] == "2026-10-01" and r["id"]
        assert da_vao.wait(10)
        r2 = c.post("/ke-toan/hoa-don-cho/quet-nen").json()
        assert r2["id"] == r["id"] and not r2["moi"]
        assert c.get(f"/ke-toan/hoa-don-cho/quet-nen/{r['id']}").json()["trang_thai"] == "DANG_CHAY"
        assert c.get("/ke-toan/hoa-don-cho/quet-nen").json()["id"] == r["id"]
        assert c.get("/ke-toan/hoa-don-cho/quet-nen/9999").status_code == 404
        cho.set()
        assert hqn.cho_xong(r["id"], 60)
        d = c.get(f"/ke-toan/hoa-don-cho/quet-nen/{r['id']}").json()
        assert d["trang_thai"] == "XONG" and d["ket_qua"]["da_them"] == 2 and d["gan_day"] and d["tien_do"]["buoc"] == "XONG"
        # endpoint cũ (đồng bộ) vẫn chạy và trả kết quả như trước
        d0 = c.post("/ke-toan/hoa-don-cho/quet?tu_ngay=2026-10-01").json()
        assert d0["ok"] and d0["thu_moi"] == 2 and d0["da_them"] == 0 and d0["trung_bo_qua"] == 2
        s = SL()
        assert s.query(m.AuditLog).filter_by(hanh_dong="HDC_QUET_NEN", ban_ghi_id=r["id"]).count() == 1
        s.close()
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(lay_nguoi_dung_hien_tai, None)
