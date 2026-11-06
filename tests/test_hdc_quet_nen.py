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
    """Hộp thư giả: da_vao bật khi lượt bắt đầu lấy thư; cho (nếu có) giữ luồng nền lại cho tới khi test cho đi tiếp.
    chi_mo=True: chỉ trả thư ở cửa sổ MỞ (den_ngay=None — cửa sổ cuối của quét nền, và endpoint cũ); cửa sổ kín trả rỗng.
    goi: các (tu_ngay, den_ngay) đã được hỏi; bo_qua: tập bo_qua_mid nhận ở mỗi lần gọi (None = tải đủ mọi thư);
    tai_du: Message-ID các thư đã TẢI ĐỦ thân ở lần gọi gần nhất — thư có Message-ID trong bo_qua_mid trả bản rút gọn
    như _imap_lay_thu (không thân, không đính kèm)."""
    ten = "GIA"

    def __init__(self, thu, cho=None, da_vao=None, loi=None, chi_mo=True):
        self.thu, self.cho, self.da_vao, self.loi, self.chi_mo, self.so_lan, self.goi = thu, cho, da_vao, loi, chi_mo, 0, []
        self.bo_qua, self.tai_du = [], []

    def lay_thu(self, tu_ngay=None, den_ngay=None, bao=None, bo_qua_mid=None):
        self.so_lan += 1
        self.goi.append((tu_ngay, den_ngay))
        self.bo_qua.append(None if bo_qua_mid is None else set(bo_qua_mid))
        if self.da_vao is not None:
            self.da_vao.set()
        if self.cho is not None:
            assert self.cho.wait(30), "test không cho luồng nền đi tiếp"
        if self.loi:
            raise RuntimeError(self.loi)
        thu, self.tai_du, rut_gon = [], [], 0
        for t in (list(self.thu) if (den_ngay is None or not self.chi_mo) else []):
            mid = (t.get("message_id") or "").strip()[:250]
            if bo_qua_mid and mid in bo_qua_mid:
                rut_gon += 1
                thu.append({"message_id": t.get("message_id"), "rut_gon": True, "tu_email": None, "tieu_de": None,
                            "noi_dung": "", "dinh_kem": []})
            else:
                self.tai_du.append(mid)
                thu.append(dict(t))
        if bao is not None and thu:
            bao(len(thu), len(thu), rut_gon) if bo_qua_mid is not None else bao(len(thu), len(thu))
        return thu


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
    moc = (gio_hien_tai() - timedelta(days=3)).date()           # < 7 ngày → một cửa sổ mở
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
    assert kq["so_cua_so"] == 1 and kq["cua_so_xong"] == 1 and prov.goi == [(moc, None)]
    assert d["tien_do"]["buoc"] == "XONG" and d["tien_do"]["so_thu"] == 3 and d["tien_do"]["da_them"] == 2
    assert d["tien_do"]["da_lay"] == 3 and d["tien_do"]["cua_so"] == 1            # tiến độ lúc lấy thư cũng ghi
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
    v, moi = hqn.bat_dau(db, nd, (gio_hien_tai() - timedelta(days=5)).date())            # một cửa sổ
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
    assert d["trang_thai"] == "LOI" and d["ket_qua"]["luot"] == 0 and d["ket_qua"]["cua_so_xong"] == 0
    assert d["ket_qua"]["loi"] == ["Cửa sổ 1 lượt 1: Không đọc được hộp thư (GIA): IMAP timeout"]
    # dòng DANG_CHAY của TIẾN TRÌNH CŨ (bắt đầu trước mốc nạp module, luồng không còn — Render deploy giữa lượt)
    # hoặc quá 2 giờ → không chặn, đóng là LOI ngay
    s = SL()
    ket = m.ViecNen(loai=hqn.LOAI, trang_thai="DANG_CHAY", bat_dau=gio_hien_tai() - timedelta(hours=3),
                    ket_qua={"tu_ngay": "2026-10-01"})
    cu = m.ViecNen(loai=hqn.LOAI, trang_thai="DANG_CHAY", bat_dau=hqn.KHOI_DONG - timedelta(seconds=1), ket_qua={})
    s.add_all([ket, cu]); s.commit()
    assert hqn.dang_chay(s) is None
    assert ket.trang_thai == "LOI" and ket.ket_thuc and "khởi động lại" in ket.ket_qua["loi"][0]
    assert cu.trang_thai == "LOI" and cu.ket_thuc
    s.commit()
    # dòng DANG_CHAY bắt đầu sau mốc nạp module mà luồng không ở tiến trình này (worker khác) → vẫn coi là đang chạy
    moi_r = m.ViecNen(loai=hqn.LOAI, trang_thai="DANG_CHAY", bat_dau=gio_hien_tai(), ket_qua={})
    s.add(moi_r); s.commit()
    assert hqn.dang_chay(s) is moi_r and hqn.moi_nhat(s) is moi_r
    s.close()


def test_cua_so_7_ngay(moi_truong, monkeypatch):
    from datetime import date
    # chia mốc → hôm nay thành cửa sổ kín 7 ngày [tu, den) + cửa sổ cuối mở
    assert hqn.cua_so(date(2026, 10, 7), date(2026, 11, 6)) == [
        (date(2026, 10, 7), date(2026, 10, 14)), (date(2026, 10, 14), date(2026, 10, 21)), (date(2026, 10, 21), date(2026, 10, 28)),
        (date(2026, 10, 28), date(2026, 11, 4)), (date(2026, 11, 4), None)]
    assert hqn.cua_so(date(2026, 11, 1), date(2026, 11, 6)) == [(date(2026, 11, 1), None)]
    assert hqn.cua_so(date(2026, 10, 30), date(2026, 11, 6)) == [(date(2026, 10, 30), date(2026, 11, 6)), (date(2026, 11, 6), None)]
    # chạy nền 20 ngày → 3 cửa sổ; hộp thư trả cùng 3 thư ở mọi cửa sổ → cửa sổ 1 thêm, cửa sổ 2–3 trùng; số liệu cộng theo cửa sổ
    SL, nd = moi_truong
    prov = _dat_hop_thu(monkeypatch, _HopThu([_thu_hd(401), _thu_hd(402), THU_KHAC], chi_mo=False))
    hom_nay = gio_hien_tai().date()
    moc = hom_nay - timedelta(days=20)
    db = SL()
    v, _ = hqn.bat_dau(db, nd, moc)
    db.close()
    assert hqn.cho_xong(v.id, 120)
    d = _xem(SL, v.id)
    kq = d["ket_qua"]
    assert prov.goi == hqn.cua_so(moc, hom_nay) == [(moc, moc + timedelta(days=7)), (moc + timedelta(days=7), moc + timedelta(days=14)),
                                                    (moc + timedelta(days=14), None)]
    assert d["trang_thai"] == "XONG" and kq["so_cua_so"] == 3 and kq["cua_so_xong"] == 3 and kq["luot"] == 3
    assert kq["da_them"] == 2 and kq["thu_moi"] == 9 and kq["trung_bo_qua"] == 4 and kq["khong_khop"] == 3 and kq["con_lai"] == 0
    assert kq["tu_ngay"] == str(moc) and "den_ngay" not in kq
    assert d["tien_do"]["cua_so"] == 3 and d["tien_do"]["so_cua_so"] == 3 and d["tien_do"]["da_them_tong"] == 2
    s = SL()
    assert s.query(m.KtHoaDonCho).count() == 2
    s.close()


def test_bo_qua_mid_thu_da_biet(moi_truong, monkeypatch):
    """⏩ Quét nền đưa cho cổng thư tập Message-ID ĐÃ BIẾT để khỏi tải thân: dòng đã ghi / bỏ qua, dòng chờ đã ĐỦ, hóa đơn bán;
    dòng chờ còn THIẾU tiền / link vẫn tải đủ và được «✎ bổ sung»; endpoint cũ (đồng bộ) không đưa tập này."""
    from decimal import Decimal
    from app.routers.ke_toan_quy import hdc_quet_lo, _hdc_mid_da_biet
    SL, nd = moi_truong
    moc = (gio_hien_tai() - timedelta(days=3)).date()
    prov = _dat_hop_thu(monkeypatch, _HopThu([_thu_hd(501), _thu_hd(502), _thu_hd(503), THU_KHAC]))
    db = SL()
    v, _ = hqn.bat_dau(db, nd, moc)
    db.close()
    assert hqn.cho_xong(v.id, 60)
    kq = _xem(SL, v.id)["ket_qua"]
    assert kq["da_them"] == 3 and kq["bo_qua_header"] == 0 and prov.bo_qua == [set()]       # chưa biết thư nào → tải đủ
    s = SL()
    r501, r502, r503 = [s.query(m.KtHoaDonCho).filter_by(so_hoa_don=str(so)).one() for so in (501, 502, 503)]
    assert all(int(r.tong_tien) == 10_476_000 and r.link_tra_cuu and r.ngay_hd for r in (r501, r502, r503))
    # 502: tiền về 0 + mất link (như 13 dòng EasyInvoice bản thật 05/11) → còn THIẾU; 503: đã ghi sổ; thêm một HĐ bán đã nhận
    r502.tong_tien, r502.tien_truoc_thue, r502.link_tra_cuu = Decimal(0), Decimal(0), None
    r503.trang_thai = "DA_GHI"
    s.add(m.KtHdGuiKhach(message_id="<gk-1@meinvoice.vn>", tieu_de="HĐ bán", trang_thai="CHUA_KHOP"))
    s.commit()
    assert _hdc_mid_da_biet(s) == {"<hd-501@easyinvoice.vn>", "<hd-503@easyinvoice.vn>", "<gk-1@meinvoice.vn>"}
    s.close()
    prov.thu = prov.thu + [{"tu_email": "noreply@meinvoice.vn", "tieu_de": "HĐ bán", "noi_dung": "x",
                            "message_id": "<gk-1@meinvoice.vn>", "dinh_kem": []}]
    db = SL()
    v2, _ = hqn.bat_dau(db, nd, moc)
    db.close()
    assert hqn.cho_xong(v2.id, 60)
    d2 = _xem(SL, v2.id)
    kq2 = d2["ket_qua"]
    assert prov.bo_qua[-1] == {"<hd-501@easyinvoice.vn>", "<hd-503@easyinvoice.vn>", "<gk-1@meinvoice.vn>"}
    assert prov.tai_du == ["<hd-502@easyinvoice.vn>", "<khac-1@do.vn>"]                    # chỉ dòng thiếu + thư lạ tải đủ
    assert kq2["thu_moi"] == 5 and kq2["bo_qua_header"] == 3 and kq2["trung_bo_qua"] == 4   # 3 rút gọn + 502 vẫn đếm «đã xử lý»
    assert kq2["da_them"] == 0 and kq2["sua_cu"] == 1 and kq2["khong_khop"] == 1 and kq2["loi"] == []
    assert d2["tien_do"]["bo_qua_header"] == 3 and d2["tien_do"]["so_thu"] == 5 and d2["tien_do"]["da_lay"] == 5
    s = SL()
    r502 = s.query(m.KtHoaDonCho).filter_by(so_hoa_don="502").one()
    assert int(r502.tong_tien) == 10_476_000 and r502.link_tra_cuu and r502.mo_ta.startswith("📧 đọc lại theo nhãn")
    assert s.query(m.KtHoaDonCho).count() == 3
    # lượt 3: 502 đã đủ → vào tập đã biết, không tải lại nữa
    assert "<hd-502@easyinvoice.vn>" in _hdc_mid_da_biet(s)
    # endpoint cũ / quét tuần (không bao_tien_do, không den_ngay) → không đưa bo_qua_mid, tải đủ như trước
    k0 = hdc_quet_lo(s, nd, moc)
    assert prov.bo_qua[-1] is None and k0["trung_bo_qua"] == 4 and k0["bo_qua_header"] == 0 and len(prov.tai_du) == 5
    s.close()


def test_imap_lay_thu_rut_gon(monkeypatch):
    """_imap_lay_thu với máy chủ IMAP giả: hỏi Message-ID hàng loạt (một FETCH / 100 thư, trả lời dạng imaplib), thư trong
    bo_qua_mid trả bản rút gọn không FETCH thân; thư thiếu Message-ID hay không trong tập → tải đủ; bao(i, n, bo_qua)."""
    import email
    from datetime import date
    from email.message import EmailMessage

    def _eml(mid, so):
        e = EmailMessage()
        e["From"] = f"ncc{so}@x.vn"
        e["Subject"] = f"Hóa đơn {so}"
        if mid:
            e["Message-ID"] = mid
        e.set_content(f"Thân thư {so}")
        return e.as_bytes()

    thu = {b"1": _eml("<a@x.vn>", 1), b"2": _eml("<b@x.vn>", 2), b"3": _eml(None, 3), b"4": _eml("  <c@x.vn>  ", 4)}
    lenh = []

    class _Imap:
        def __init__(self, host, port, timeout=None):
            pass

        def login(self, u, p): pass
        def select(self, hop): pass
        def logout(self): pass

        def search(self, cs, dk):
            lenh.append(("search", dk))
            return "OK", [b" ".join(thu)]

        def fetch(self, so, phan):
            lenh.append(("fetch", so, phan))
            ra = []
            for n in so.split(b","):
                if "HEADER.FIELDS" in phan:
                    msg = email.message_from_bytes(thu[n])
                    h = (f"Message-ID: {msg['Message-ID']}\r\n\r\n" if msg["Message-ID"] else "\r\n").encode()
                    ra += [(n + b" (BODY[HEADER.FIELDS (MESSAGE-ID)] {%d}" % len(h), h), b")"]
                else:
                    ra += [(n + b" (BODY[] {%d}" % len(thu[n]), thu[n]), b")"]
            return "OK", ra

    monkeypatch.setattr(ig.imaplib, "IMAP4_SSL", _Imap)
    monkeypatch.setattr(ig, "MID_MOI_LENH", 3)
    tien_do = []
    out = ig._imap_lay_thu(date(2026, 11, 1), date(2026, 11, 8), bao=lambda *a: tien_do.append(a),
                           bo_qua_mid={"<a@x.vn>", "<c@x.vn>"})
    assert lenh[0] == ("search", "(SINCE 01-Nov-2026 BEFORE 08-Nov-2026)")
    assert lenh[1] == ("fetch", b"1,2,3", "(BODY.PEEK[HEADER.FIELDS (MESSAGE-ID)])")       # hàng loạt, 3 thư / lệnh
    assert lenh[2] == ("fetch", b"4", "(BODY.PEEK[HEADER.FIELDS (MESSAGE-ID)])")
    assert [l[1] for l in lenh[3:]] == [b"2", b"3"] and all(l[2] == "(BODY.PEEK[])" for l in lenh[3:])   # chỉ tải thân 2 + 3
    assert [(m.get("message_id") or "").strip() for m in out] == ["<a@x.vn>", "<b@x.vn>", "", "<c@x.vn>"]
    assert out[0]["rut_gon"] and out[3]["rut_gon"] and out[0]["noi_dung"] == "" and out[0]["dinh_kem"] == []
    assert not out[1].get("rut_gon") and "Thân thư 2" in out[1]["noi_dung"] and out[1]["tu_email"] == "ncc2@x.vn"
    assert not out[2].get("rut_gon") and "Thân thư 3" in out[2]["noi_dung"]
    assert tien_do == [(4, 4, 1)]                      # thư cuối: 4/4, lúc đó mới bỏ qua 1 (thư 4 xét sau khi báo)
    # không có bo_qua_mid → không hỏi header, tải đủ mọi thư, bao(i, n) hai tham số như cũ
    lenh.clear(); tien_do.clear()
    out0 = ig._imap_lay_thu(date(2026, 11, 1), bao=lambda *a: tien_do.append(a))
    assert lenh[0] == ("search", "(SINCE 01-Nov-2026)") and [l[1] for l in lenh[1:]] == [b"1", b"2", b"3", b"4"]
    assert all(l[2] == "(BODY.PEEK[])" for l in lenh[1:]) and not any(m.get("rut_gon") for m in out0)
    assert tien_do == [(4, 4)]


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
        from datetime import date
        so_cs = len(hqn.cua_so(date(2026, 10, 1), gio_hien_tai().date()))          # 01/10 → nay: nhiều cửa sổ, thư chỉ ở cửa sổ mở cuối
        assert d["ket_qua"]["so_cua_so"] == so_cs == d["ket_qua"]["cua_so_xong"] and d["ket_qua"]["luot"] == so_cs
        # endpoint cũ (đồng bộ) vẫn chạy và trả kết quả như trước
        d0 = c.post("/ke-toan/hoa-don-cho/quet?tu_ngay=2026-10-01").json()
        assert d0["ok"] and d0["thu_moi"] == 2 and d0["da_them"] == 0 and d0["trung_bo_qua"] == 2
        s = SL()
        assert s.query(m.AuditLog).filter_by(hanh_dong="HDC_QUET_NEN", ban_ghi_id=r["id"]).count() == 1
        s.close()
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(lay_nguoi_dung_hien_tai, None)
