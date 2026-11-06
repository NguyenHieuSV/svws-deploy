"""
📧 Đọc thư cổng HĐĐT theo nhãn (mig 169, app/hddt_doc_nhan.py — anh Hiếu 05/11/2026): thư EasyInvoice như bản thật
(hóa đơn 277 Cơ khí Tuấn Tài 05/11/2026) đọc ra đủ số liệu, không nhầm MST thành tiền, lấy đúng link tra cứu;
thân thư HTML giữ link; hàng chờ trùng gộp lại. SQLite trong bộ nhớ.
"""
from datetime import date
from decimal import Decimal
from email.message import EmailMessage

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app import hddt_doc_nhan as hn
from app import inbound_gateway as ig
from app import models as m
from app.routers import cho_thue_ops as cto
from app.routers import ke_toan_quy as kq

TIEU_DE = "Hóa đơn điện tử số: 277 - CÔNG TY TNHH TM - SX CƠ KHÍ TUẤN TÀI kính gửi khách hàng CÔNG TY TNHH GIẢI PHÁP KỸ THUẬT SÓNG VIỆT"
THU = """Kính gửi Quý khách hàng,
CÔNG TY TNHH TM - SX CƠ KHÍ TUẤN TÀI, Mã số thuế 3703058418 xin trân trọng cảm ơn Quý khách hàng đã tin dùng dịch vụ, hàng hóa của chúng tôi.
CÔNG TY TNHH TM - SX CƠ KHÍ TUẤN TÀI vừa phát hành hóa đơn điện tử đến Quý khách CÔNG TY TNHH GIẢI PHÁP KỸ THUẬT SÓNG VIỆT, Mã số thuế 0303620066 với thông tin chi tiết như sau:
Ký hiệu mẫu số hóa đơn: 1C26TTT
Số hóa đơn: 277
Ngày hóa đơn: 05/11/2026
Tiền thuế: 776,000 VND
Tổng tiền thanh toán: 10,476,000 VND
Mã của cơ quan thuế: 00E2D487586D814BA2B561D0497110A6E9
Mã tra cứu: 7UT2SH9WV
Quý khách vui lòng truy cập link (http://3703058418hd.easyinvoice.com.vn/tra-cuu?ma=7UT2SH9WV) để xem và kiểm tra hóa đơn gốc hoặc link (http://3703058418hd.easyinvoice.com.vn/tai-pdf?ma=7UT2SH9WV) để tải nhanh hóa đơn dạng PDF.
Softdreams ra mắt sản phẩm EasyPIT - Phần mềm kê khai đáp ứng đầy đủ nghiệp vụ lập chứng từ khấu trừ thuế TNCN điện tử. Xem ngay tại https://easy-pit.easyinvoice.com.vn/
Chú ý: Đây là mail tự động từ hệ thống. Quý khách vui lòng không trả lời mail này.
Trân trọng ./.
Website: https://easyinvoice.vn - Tổng đài hỗ trợ: 1900 33 69 - 1900 56 56 53"""


def test_doc_nhan_thu_easyinvoice():
    r = hn.doc_nhan(TIEU_DE, THU)
    assert r["du"] and r["ncc_ten"] == "CÔNG TY TNHH TM - SX CƠ KHÍ TUẤN TÀI" and r["ncc_mst"] == "3703058418"
    assert r["nguoi_mua"] == "CÔNG TY TNHH GIẢI PHÁP KỸ THUẬT SÓNG VIỆT" and r["nguoi_mua_mst"] == "0303620066"
    assert (r["ky_hieu"], r["so_hoa_don"], r["ngay"]) == ("1C26TTT", "277", "2026-11-05")
    assert (r["so_tien"], r["tien_thue"], r["tien_truoc_thue"], r["thue_suat"]) == (10_476_000, 776_000, 9_700_000, 8)
    assert r["ma_cqt"] == "00E2D487586D814BA2B561D0497110A6E9" and r["ma_tra_cuu"] == "7UT2SH9WV"
    assert r["link_tra_cuu"] == "http://3703058418hd.easyinvoice.com.vn/tra-cuu?ma=7UT2SH9WV"      # không phải EasyPIT / trang chủ
    assert r["mo_ta"] == "ký hiệu 1C26TTT · mã CQT 00E2D487586D814BA2B561D0497110A6E9"


def test_doc_nhan_bien_the_va_khong_phai_hddt():
    misa = ("Bên bán: CÔNG TY CỔ PHẦN ABC - MST: 0101234567\nBên mua: CÔNG TY TNHH GIẢI PHÁP KỸ THUẬT SÓNG VIỆT MST: 0303620066\n"
            "Ký hiệu: 1C26AAA\nSố hóa đơn: 0000042\nNgày lập: 03/11/2026\nTiền hàng: 9.700.000 đ\nTiền thuế GTGT: 776.000 đ\n"
            "Tổng tiền thanh toán: 10.476.000 đ\nMã tra cứu: ABCDEF123\nhttps://tracuu.meinvoice.vn/x?id=1")
    r = hn.doc_nhan("Thông báo hóa đơn", misa)
    assert r["du"] and r["ncc_ten"] == "CÔNG TY CỔ PHẦN ABC" and r["ncc_mst"] == "0101234567"
    assert r["nguoi_mua_mst"] == "0303620066" and r["so_hoa_don"] == "42" and r["ngay"] == "2026-11-03"
    assert (r["so_tien"], r["tien_truoc_thue"], r["tien_thue"]) == (10_476_000, 9_700_000, 776_000)
    assert r["link_tra_cuu"] == "https://tracuu.meinvoice.vn/x?id=1" and r["ky_hieu"] == "1C26AAA"
    # thư thường của NCC (đề nghị thanh toán) → không phải thư cổng → None, để AI đọc như cũ
    assert hn.doc_nhan("Đề nghị thanh toán", "Chào anh, tổng tiền 5.000.000 đ, mong anh chuyển sớm.") is None
    # có ký hiệu nhưng thiếu tổng → trả dữ liệu nhưng du=False (AI sẽ đọc tiếp)
    r2 = hn.doc_nhan("Hóa đơn điện tử số: 9", "Ký hiệu: 1C26TTT\nSố hóa đơn: 9\nMã tra cứu: ZZZZZZ99")
    assert r2 and not r2["du"] and r2["so_hoa_don"] == "9" and r2["ma_tra_cuu"] == "ZZZZZZ99"


def test_so_tien_link_va_bo_mst():
    assert hn.so_tien("10,476,000 VND") == 10_476_000 and hn.so_tien("9.700.000,00 đ") == 9_700_000
    assert hn.so_tien("10 476 000,5") == 10_476_000 and hn.so_tien("VND") is None
    assert hn.link_tra_cuu("xem https://easy-pit.easyinvoice.com.vn/ và https://easyinvoice.vn/ rồi http://a.vn/hoa-don/1") == "http://a.vn/hoa-don/1"
    assert hn.link_tra_cuu("chỉ có https://easyinvoice.vn/") is None
    info = {"so_tien": 3701728378, "tien_truoc_thue": "3701728378", "tien_thue": 100}
    assert hn.bo_mst_lam_tien(info, "Mã số thuế 3701728378 … Tổng 1.000") == {"so_tien": None, "tien_truoc_thue": None, "tien_thue": 100}
    assert hn.bo_mst_lam_tien({"so_tien": 10_476_000}, THU)["so_tien"] == 10_476_000
    # bộ đọc regex dự phòng cũng không lấy MST 10 số làm tiền
    r = cto._rut_hd_email("Hóa đơn số 227", "Mã số thuế 3703058418\nTổng tiền thanh toán: 10,476,000 VND")
    assert r["so_tien"] == 10_476_000
    assert cto._rut_hd_email("Hóa đơn", "Mã số thuế 3703058418")["so_tien"] is None


def test_bo_html_giu_link_va_body_uu_tien_html():
    html = ('<html><body><p>Số hóa đơn: <b>277</b></p><p>Truy cập <a href="http://x.vn/tra-cuu?m=1">link</a> để xem '
            'hoặc <a href="http://x.vn/pdf?m=1">link</a> để tải.</p></body></html>')
    t = ig._bo_html(html)
    assert "Số hóa đơn: 277" in t and "link (http://x.vn/tra-cuu?m=1)" in t and "link (http://x.vn/pdf?m=1)" in t
    msg = EmailMessage()
    msg["Subject"] = "Hóa đơn điện tử số: 277"
    msg.set_content("Vui lòng xem bản HTML.")                     # phần chữ thường chỉ một dòng nhắc
    msg.add_alternative(html, subtype="html")
    assert "Số hóa đơn: 277" in ig._body(msg) and "http://x.vn/tra-cuu?m=1" in ig._body(msg)
    msg2 = EmailMessage()
    msg2.set_content("Chào anh,\n" + "nội dung dài " * 10 + "\nTổng tiền 5.000.000 đ")   # chữ thường dài hơn → giữ chữ thường
    msg2.add_alternative("<p>html</p>", subtype="html")
    assert ig._body(msg2).startswith("Chào anh")
    msg3 = EmailMessage()                                           # chữ thường bị cắt gọn (thiếu tiền) → lấy bản HTML dài hơn
    msg3.set_content("Hóa đơn điện tử số: 277 - CÔNG TY TNHH TM - SX CƠ KHÍ TUẤN TÀI. Mã tra cứu: 7UT2SH9WV. Xem bản HTML.")
    msg3.add_alternative("<html><body>" + "".join(f"<p>{d}</p>" for d in THU.splitlines()) + "</body></html>", subtype="html")
    assert "Tổng tiền thanh toán: 10,476,000 VND" in ig._body(msg3)


def _db():
    eng = create_engine("sqlite://")
    for t in (m.NhaCungCap, m.KtHoaDonCho):
        t.__table__.create(eng)
    s = sessionmaker(eng)()
    n = {}

    @event.listens_for(s, "before_flush")
    def _ids(sess, _c, _i):
        for o in sess.new:
            if getattr(o, "id", None) is None:
                n[type(o)] = n.get(type(o), 0) + 1
                o.id = n[type(o)]
    return s


def _hdc(**kw):
    d = dict(trang_thai="CHO_XAC_NHAN", tien_truoc_thue=Decimal(0), thue_suat=Decimal(8), tong_tien=Decimal(0))
    d.update(kw)
    return m.KtHoaDonCho(**d)


def test_hang_cho_trung_va_bo_sung_theo_nhan():
    s = _db()
    s.add(m.NhaCungCap(ten="Cơ khí Tuấn Tài", ma_so_thue="3703058418", email="kt@tuantai.vn"))
    a = _hdc(tu_email="hoadon-noreply@easyinvoice.vn", ncc_ten="CÔNG TY TNHH TM - SX CƠ KHÍ TUẤN TÀI", so_hoa_don="227",
             link_tra_cuu="https://easy-pit.easyinvoice.com.vn/", message_id="<m1>")                  # tiền 0 như bản thật
    b = _hdc(tu_email="hoadon-noreply@softdreams.vn", ncc_ten="CÔNG TY TNHH DỊCH VỤ KỸ THUẬT KHOA NAM", so_hoa_don="424",
             tong_tien=Decimal(4_994_000), tien_truoc_thue=Decimal(4_624_000), message_id="<m2>")
    c = _hdc(tu_email="hoadon-noreply@easyinvoice.vn", ncc_ten="CÔNG TY TNHH DỊCH VỤ KỸ THUẬT KHOA NAM", so_hoa_don="424",
             tong_tien=Decimal(3_701_728_378), tien_truoc_thue=Decimal(3_427_526_276), ngay_hd=date(2026, 10, 29),
             message_id="<m3>")                                                                          # tiền = MST → đáng ngờ
    d = _hdc(ncc_ten="CÔNG TY KHÁC", so_hoa_don="424", tong_tien=Decimal(1_000_000), message_id="<m4>")  # NCC khác → không trùng
    s.add_all([a, b, c, d]); s.commit()
    nhan = hn.doc_nhan(TIEU_DE, THU)
    # cùng bên bán (MST) + số HĐ 227 → tìm ra dòng a dù a chưa có MST; ký hiệu khác → không trùng
    assert kq._hdc_tim_trung(s, None, nhan["ncc_ten"], "3703058418", "227", "1C26TTT") is a
    assert kq._hdc_tim_trung(s, None, nhan["ncc_ten"], "3703058418", "0227", None) is a
    assert kq._hdc_tim_trung(s, None, "Công ty khác hẳn", "", "227", None) is None
    assert kq._hdc_bo_sung_nhan(a, dict(nhan, so_hoa_don="227"), THU, {"3703058418": 1})
    assert (int(a.tong_tien), int(a.tien_truoc_thue), int(a.thue_suat)) == (10_476_000, 9_700_000, 8)
    assert a.ncc_mst == "3703058418" and a.ky_hieu == "1C26TTT" and a.nha_cung_cap_id == 1 and a.nguon_doc == "NHAN"
    assert a.link_tra_cuu.startswith("http://3703058418hd.easyinvoice.com.vn/tra-cuu") and a.ma_tra_cuu == "7UT2SH9WV"
    assert a.mo_ta.startswith("📧 đọc lại theo nhãn")
    assert not kq._hdc_bo_sung_nhan(a, nhan, THU, {})                      # đã đủ → không đổi gì nữa
    assert kq._hdc_tien_nghi(c) and not kq._hdc_tien_nghi(b)
    # gộp trùng: b (tiền hợp lệ) giữ, c → BO_QUA trỏ về b, ngày của c sang b; d khác NCC giữ nguyên
    assert kq._hdc_gop_trung(s) == 1
    s.commit()
    assert c.trang_thai == "BO_QUA" and c.trung_voi_id == b.id and c.mo_ta.startswith("🔁 Trùng với dòng #")
    assert b.trang_thai == "CHO_XAC_NHAN" and b.ngay_hd == date(2026, 10, 29) and int(b.tong_tien) == 4_994_000
    assert d.trang_thai == "CHO_XAC_NHAN" and kq._hdc_gop_trung(s) == 0
    # cùng KÝ HIỆU + số HĐ nhưng một dòng chưa đọc được tên NCC (bản thật 05/11: HĐ 277 thành 2 dòng) → vẫn là một hóa đơn
    e = _hdc(tu_email="hoadon-noreply@easyinvoice.vn", ncc_ten=None, so_hoa_don="277", ky_hieu="1C26TTT", message_id="<m5>")
    f = _hdc(tu_email="hoadon-noreply@easyinvoice.vn", ncc_ten="CÔNG TY TNHH TM - SX CƠ KHÍ TUẤN TÀI", so_hoa_don="277",
             ky_hieu="1C26TTT", tong_tien=Decimal(10_476_000), tien_truoc_thue=Decimal(9_700_000), message_id="<m6>")
    s.add_all([e, f]); s.commit()
    assert kq._hdc_tim_trung(s, None, None, "", "277", "1C26TTT") is e
    assert kq._hdc_gop_trung(s) == 1 and e.trang_thai == "BO_QUA" and e.trung_voi_id == f.id and f.trang_thai == "CHO_XAC_NHAN"
