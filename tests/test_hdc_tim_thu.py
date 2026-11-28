"""
🔎 Tìm thư trong hộp thư nhận hóa đơn (28/11/2026) — soi vì sao một hóa đơn (vd Petrolimex) chưa vào hàng chờ hóa đơn mua:
  • inbound_gateway.tim_thu: máy chủ IMAP giả — tìm ở Hộp thư đến + «Tất cả thư» + «Thư rác», trả CẢ thư tự động;
  • ke_toan_quy._hdc_vi_sao_chua_doc: lý do luồng quét bỏ qua thư;
  • endpoint /ke-toan/hoa-don-cho/tim-thu: gắn dòng hàng chờ đã có theo Message-ID.
"""
import email
from datetime import date
from email.message import EmailMessage

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import inbound_gateway as ig
from app import models as m
from app.routers import ke_toan_quy as kq


def _eml(mid, tu, tieu_de, than, tu_dong=None, tep=None):
    e = EmailMessage()
    e["From"], e["To"], e["Subject"], e["Message-ID"] = tu, "inf@watersolutions.company", tieu_de, mid
    e["Date"] = "Mon, 05 Oct 2026 09:00:00 +0700"
    if tu_dong:
        e["Auto-Submitted"] = tu_dong
    e.set_content(than)
    if tep:
        e.add_attachment(b"%PDF-1.4 x" * 300, maintype="application", subtype="pdf", filename=tep)
    return e.as_bytes()


A = _eml("<a@plx>", "Petrolimex <hoadon@petrolimex.com.vn>", "PETROLIMEX thông báo phát hành hóa đơn điện tử",
         "Kính gửi Quý khách. Tra cứu tại https://hoadon.petrolimex.com.vn/SearchInvoicebycode Mã tra cứu: ABC12345",
         tu_dong="auto-generated", tep="1C26TXD_0001234.pdf")
B = _eml("<b@plx>", "cuahang12@petrolimex.com.vn", "Gửi chứng từ tháng 10", "Petrolimex gửi anh chứng từ")
HOP = {"INBOX": {b"7": A},
       "[Gmail]/All Mail": {b"3": A, b"4": B},                    # «Tất cả thư» chứa lại thư A của Hộp thư đến
       "[Gmail]/Spam": {}}


class _Imap:
    lenh = []

    def __init__(self, host, port, timeout=None):
        self.hop = None

    def login(self, u, p): pass
    def logout(self): pass

    def list(self):
        return "OK", [b'(\\HasNoChildren) "/" "INBOX"', b'(\\All \\HasNoChildren) "/" "[Gmail]/All Mail"',
                      b'(\\HasNoChildren \\Junk) "/" "[Gmail]/Spam"', b'(\\Sent) "/" "[Gmail]/Sent Mail"']

    def select(self, hop, readonly=False):
        assert readonly is True                                   # chỉ đọc — không đổi gì trong hộp thư
        self.hop = hop.strip('"')
        return ("OK", [b"1"]) if self.hop in HOP else ("NO", [b"x"])

    def search(self, cs, *dk):
        _Imap.lenh.append(("search", self.hop, dk))
        return "OK", [b" ".join(HOP[self.hop])]

    def fetch(self, so, phan):
        _Imap.lenh.append(("fetch", self.hop, so, phan))
        assert "PEEK" in phan                                     # không đánh dấu đã đọc
        ra = []
        for n in so.split(b","):
            raw = HOP[self.hop][n]
            if "HEADER.FIELDS" in phan:
                h = f"Message-ID: {email.message_from_bytes(raw)['Message-ID']}\r\n\r\n".encode()
                ra += [(n + b" (BODY[HEADER.FIELDS (MESSAGE-ID)] {%d}" % len(h), h), b")"]
            else:
                ra += [(n + b" (BODY[] {%d}" % len(raw), raw), b")"]
        return "OK", ra


def test_tim_thu_ca_thu_tu_dong_va_hop_khac(monkeypatch):
    _Imap.lenh = []
    monkeypatch.setattr(ig.imaplib, "IMAP4_SSL", _Imap)
    monkeypatch.setattr(ig.settings, "inbound_provider", "IMAP")
    ra = ig.tim_thu("petrolimex", date(2026, 10, 1))
    assert [(x["message_id"], x["hop"]) for x in ra] == [("<a@plx>", "Hộp thư đến"), ("<b@plx>", "Tất cả thư (không ở Hộp thư đến)")]
    a, b = ra
    assert a["tu_email"] == "hoadon@petrolimex.com.vn" and a["tu_dong"] == ["Auto-Submitted: auto-generated"]
    assert a["dinh_kem"][0]["ten"] == "1C26TXD_0001234.pdf" and a["dinh_kem"][0]["kb"] >= 2 and "Mã tra cứu" in a["noi_dung"]
    assert b["tu_dong"] == [] and b["dinh_kem"] == []
    assert _Imap.lenh[0] == ("search", "INBOX", ("SINCE", "01-Oct-2026", "TEXT", '"petrolimex"'))
    # thư A ở «Tất cả thư» bị nhận ra theo Message-ID (một lệnh hỏi header) → không tải thân lần hai
    than = [l for l in _Imap.lenh if l[0] == "fetch" and l[3] == "(BODY.PEEK[])"]
    assert [(l[1], l[2]) for l in than] == [("INBOX", b"7"), ("[Gmail]/All Mail", b"4")]
    with pytest.raises(ValueError):
        ig.tim_thu("pl")                                          # từ khóa quá ngắn
    monkeypatch.setattr(ig.settings, "inbound_provider", "DEMO")
    assert ig.tim_thu("petrolimex") == []                         # không nối hộp thư thật → không gọi IMAP


def test_vi_sao_chua_doc():
    f = lambda **kw: kq._hdc_vi_sao_chua_doc({"hop": "Hộp thư đến", "tu_dong": [], **kw}, {"ncc@abc.vn"}, {"db@duan.vn"},  # noqa: E731
                                             "watersolutions.company")
    assert f(tu_email="la@x.vn", tieu_de="Hóa đơn điện tử số 12") == []                    # tiêu đề có «hóa đơn» → đọc
    assert f(tu_email="NCC@abc.vn", tieu_de="Gửi chứng từ") == [] and f(tu_email="db@duan.vn", tieu_de="x") == []
    assert "chưa có trong hồ sơ NCC" in f(tu_email="la@x.vn", tieu_de="PETROLIMEX thông báo phát hành")[0]
    k = f(tu_email="la@x.vn", tieu_de="Hóa đơn 5", tu_dong=["Auto-Submitted: auto-generated"])
    assert len(k) == 1 and "thư tự động" in k[0] and "auto-generated" in k[0]
    assert "không nằm trong Hộp thư đến" in f(tu_email="la@x.vn", tieu_de="Invoice 5", hop="Thư rác")[0]
    assert "chính công ty gửi" in f(tu_email="sale@watersolutions.company", tieu_de="Hóa đơn 7")[0]
    assert f(tu_email="sale@watersolutions.company", tieu_de="Fwd: Hóa đơn 7") == []        # thư chuyển tiếp vẫn đọc


def _raw(con, model, pk="id"):
    from sqlalchemy import Integer, Numeric
    kieu = lambda c: ("INTEGER PRIMARY KEY" if c.name == pk else "NUMERIC" if isinstance(c.type, Numeric)   # noqa: E731
                      else "INTEGER" if isinstance(c.type, Integer) else "TEXT")
    con.exec_driver_sql(f"CREATE TABLE {model.__tablename__} ({', '.join(f'{c.name} {kieu(c)}' for c in model.__table__.columns)})")


def test_endpoint_tim_thu(monkeypatch):
    eng = create_engine("sqlite://")
    with eng.begin() as c:
        for t in (m.KtHoaDonCho, m.NhaCungCap, m.CtNccEmail, m.KtHdGuiKhach):
            _raw(c, t)
        c.exec_driver_sql("INSERT INTO kt_hoa_don_cho (id, message_id, trang_thai, so_hoa_don, tong_tien) "
                          "VALUES (9, '<b@plx>', 'CHO_XAC_NHAN', '1234', 550000)")
    db = sessionmaker(eng)()
    goi = []
    thu = [{"hop": "Hộp thư đến", "ngay": "x", "tu_email": "hoadon@petrolimex.com.vn", "den_email": "inf@watersolutions.company",
            "tieu_de": "PETROLIMEX thông báo phát hành hóa đơn điện tử", "message_id": "<a@plx>",
            "tu_dong": ["Auto-Submitted: auto-generated"], "dinh_kem": [{"ten": "a.pdf", "kb": 3}],
            "noi_dung": "Tra cứu tại https://hoadon.petrolimex.com.vn/SearchInvoicebycode?x=1 Mã tra cứu: ABC12345 " + "y" * 3000},
           {"hop": "Hộp thư đến", "ngay": "x", "tu_email": "cuahang12@petrolimex.com.vn", "den_email": "", "tieu_de": "Hóa đơn 1234",
            "message_id": "<b@plx>", "tu_dong": [], "dinh_kem": [], "noi_dung": "đã có trong hàng chờ"}]
    monkeypatch.setattr(ig, "tim_thu", lambda tu_khoa, tu_ngay=None, **kw: (goi.append((tu_khoa, tu_ngay)) or thu))
    k = kq.tim_thu_hoa_don(" petrolimex ", date(2026, 10, 1), db, None)
    assert goi == [("petrolimex", date(2026, 10, 1))] and k["so_thu"] == 2
    a, b = k["thu"]
    assert a["trong_hang_cho"] is None and len(a["vi_sao_chua_doc"]) == 1 and "thư tự động" in a["vi_sao_chua_doc"][0]
    assert a["ten_mien_trong_thu"] == ["hoadon.petrolimex.com.vn"] and a["co_ma_tra_cuu"] and len(a["noi_dung"]) == 1500
    assert b["trong_hang_cho"] == {"id": 9, "trang_thai": "CHO_XAC_NHAN", "so_hoa_don": "1234", "tong_tien": 550000.0}
    assert b["vi_sao_chua_doc"] == []
    with pytest.raises(HTTPException) as e:
        kq.tim_thu_hoa_don("pl", None, db, None)
    assert e.value.status_code == 400

    def _hong(*a, **kw):
        raise OSError("mất kết nối")
    monkeypatch.setattr(ig, "tim_thu", _hong)
    with pytest.raises(HTTPException) as e2:
        kq.tim_thu_hoa_don("petrolimex", None, db, None)
    assert e2.value.status_code == 400 and "Không đọc được hộp thư" in e2.value.detail
