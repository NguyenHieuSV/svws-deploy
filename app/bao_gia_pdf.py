"""Sinh PDF Báo giá (QUOTATION) theo mẫu SVWS — dùng khi gửi email cho khách.

Bố cục khớp bản in trên trình duyệt: header logo + công ty, tiêu đề QUOTATION,
Quote No/Date/Valid until, Customer/ATTN, bảng sản phẩm (VAT theo dòng),
Subtotal/Total VAT/Grand Total, Additional information, chữ ký.
Dùng reportlab + font DejaVu (tiếng Việt).
"""
from __future__ import annotations
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, Image)

TEAL = HexColor("#0E7C86")
GREY = HexColor("#5B7186")
LINE = HexColor("#C9D8E0")
LIGHT = HexColor("#F2F7F9")
_FONTS = {}
_LOGO = os.path.join(os.path.dirname(__file__), "assets", "sv_logo.jpg")


def _fonts(regular, bold):
    if _FONTS:
        return _FONTS["F"], _FONTS["FB"]
    F, FB = "Helvetica", "Helvetica-Bold"
    if os.path.exists(regular):
        pdfmetrics.registerFont(TTFont("SVq", regular)); F = "SVq"
    if os.path.exists(bold):
        pdfmetrics.registerFont(TTFont("SVqb", bold)); FB = "SVqb"
    _FONTS.update(F=F, FB=FB)
    return F, FB


def _money(x):
    try:
        return f"{int(round(float(x))):,}"
    except Exception:
        return str(x)


def _ngay_vn(iso):
    p = (iso or "").split("-")
    return f"{p[2]}/{p[1]}/{p[0]}" if len(p) == 3 else (iso or "")


def tinh_bao_gia(d: dict):
    sub = 0.0; vat = 0.0
    for it in (d.get("items") or []):
        tt = float(it.get("so_luong") or 0) * float(it.get("don_gia") or 0)
        sub += tt
        p = it.get("vat_pct")
        p = float(d.get("vat_pct") or 0) if p in (None, "") else float(p)
        vat += tt * p / 100
    return sub, vat, sub + vat


def tao_bao_gia_pdf(path, d, cong_ty=None,
                    font_path="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    font_bold_path="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
    F, FB = _fonts(font_path, font_bold_path)
    ct = cong_ty or {}
    W = A4[0] - 24 * mm

    def P(s, sz=9, fn=None, col=black, al=TA_LEFT, ld=None):
        return Paragraph(str(s), ParagraphStyle("p", fontName=fn or F, fontSize=sz,
                         textColor=col, alignment=al, leading=ld or (sz + 3)))

    story = []

    # HEADER: logo + công ty
    left = []
    if os.path.exists(_LOGO):
        try:
            left.append(Image(_LOGO, width=30 * mm, height=30 * mm * 0.62))
        except Exception:
            pass
    right = [P(f"<b>{ct.get('ten', 'Song Viet Technical Solutions Co., Ltd')}</b>", 12, FB),
             P(ct.get('dia_chi', 'Address: 448 Vo Van Tan St., Ban Co Ward, HCMC'), 8.5, F, GREY),
             P(f"Email: {ct.get('email','sv-sales@watersolutions.company')} · Tel: {ct.get('tel','(084) 937 120 039')}", 8.5, F, GREY)]
    hd = Table([[left or "", right]], colWidths=[W * 0.24, W * 0.76])
    hd.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                            ("LINEBELOW", (0, 0), (-1, -1), 1.6, TEAL),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    story += [hd, Spacer(1, 10),
              P("<b>QUOTATION</b>", 21, FB, TEAL, TA_CENTER), Spacer(1, 4),
              P("Song Viet Technical Solutions appreciates your interest. "
                "We are pleased to send you our quotation as requested:", 9), Spacer(1, 6)]

    # META
    meta = Table([[P("<b>QUOTE NO.</b>", 9, FB, TEAL), P(d.get("so") or "", 9),
                   P("<b>QUOTE DATE</b>", 9, FB, TEAL), P(_ngay_vn(d.get("ngay")), 9)],
                  [P("<b>VALID UNTIL</b>", 9, FB, TEAL), P(d.get("hieu_luc") or "", 9), "", ""]],
                 colWidths=[26 * mm, 62 * mm, 28 * mm, W - 116 * mm])
    meta.setStyle(TableStyle([("TOPPADDING", (0, 0), (-1, -1), 2),
                              ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
    story += [meta, Spacer(1, 4)]
    if d.get("tieu_de"):
        story += [P(f"<b>{d['tieu_de']}</b>", 10.5, FB), Spacer(1, 4)]
    kh = Table([[P("<b>CUSTOMER:</b>", 9, FB, TEAL), P((d.get("khach_ten") or "").upper(), 9, FB)],
                [P("<b>ATTN:</b>", 9, FB, TEAL), P((d.get("attn") or "").upper(), 9)]],
               colWidths=[24 * mm, W - 24 * mm])
    kh.setStyle(TableStyle([("TOPPADDING", (0, 0), (-1, -1), 1.5),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5)]))
    story += [kh, Spacer(1, 8)]

    # ITEMS
    head = ["No.", "Product Name", "Description", "Qty", "Unit", "Unit Price (VND)", "VAT", "Amount (VND)"]
    al = [TA_CENTER, TA_LEFT, TA_LEFT, TA_CENTER, TA_CENTER, TA_RIGHT, TA_CENTER, TA_RIGHT]
    rows = [[P(f"<b>{h}</b>", 8, FB, white, al[i]) for i, h in enumerate(head)]]
    for i, it in enumerate((d.get("items") or []), 1):
        if not (it.get("ten") or it.get("mo_ta")):
            continue
        sl = float(it.get("so_luong") or 0); gia = float(it.get("don_gia") or 0)
        p = it.get("vat_pct")
        p = float(d.get("vat_pct") or 0) if p in (None, "") else float(p)
        rows.append([P(str(i), 8, F, black, TA_CENTER), P(it.get("ten") or "", 8),
                     P(it.get("mo_ta") or "", 8, F, GREY), P(f"{sl:g}", 8, F, black, TA_CENTER),
                     P(it.get("don_vi") or "", 8, F, black, TA_CENTER),
                     P(_money(gia), 8, F, black, TA_RIGHT),
                     P(f"{p:g}%", 8, F, black, TA_CENTER),
                     P(_money(sl * gia), 8, F, black, TA_RIGHT)])
    colw = [W * x for x in (0.05, 0.21, 0.26, 0.06, 0.07, 0.14, 0.06, 0.15)]
    tbl = Table(rows, colWidths=colw, repeatRows=1)
    tbl.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), TEAL),
                             ("GRID", (0, 0), (-1, -1), 0.5, LINE),
                             ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                             ("TOPPADDING", (0, 0), (-1, -1), 4),
                             ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                             ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, LIGHT])]))
    story += [tbl, Spacer(1, 6)]

    sub, vat, tong = tinh_bao_gia(d)
    tot = Table([[P("Subtotal (excl. VAT):", 9, F, black, TA_RIGHT), P(_money(sub) + " VND", 9, F, black, TA_RIGHT)],
                 [P("Total VAT:", 9, F, black, TA_RIGHT), P(_money(vat) + " VND", 9, F, black, TA_RIGHT)],
                 [P("<b>Grand Total (incl. VAT):</b>", 10, FB, TEAL, TA_RIGHT),
                  P(f"<b>{_money(tong)} VND</b>", 10, FB, TEAL, TA_RIGHT)]],
                colWidths=[W * 0.72, W * 0.28])
    tot.setStyle(TableStyle([("TOPPADDING", (0, 0), (-1, -1), 3),
                             ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                             ("LINEABOVE", (0, 2), (-1, 2), 1.2, TEAL)]))
    story += [tot, Spacer(1, 10)]

    # ADDITIONAL INFORMATION
    story += [P("<b>ADDITIONAL INFORMATION</b>", 10, FB, TEAL), Spacer(1, 3)]
    for lb, key in (("Payment terms", "tt"), ("Delivery time", "giao"),
                    ("Delivery location", "dia_diem"), ("Quoted by", "nguoi_bg"),
                    ("For any inquiry", "email_lh")):
        if d.get(key):
            story.append(P(f"•  <b>{lb}:</b> {d[key]}", 9))
    story += [Spacer(1, 16),
              P("<b>SONG VIET TECHNICAL SOLUTIONS CO., LTD</b>", 9.5, FB, black, TA_RIGHT),
              P("Signature and stamp:", 9, F, GREY, TA_RIGHT), Spacer(1, 26),
              P("Thank you for your interest in our products and services!", 8.5, F, GREY, TA_CENTER),
              P(f"Created on: {_ngay_vn(d.get('ngay'))} - Song Viet Technical Solutions", 8, F, GREY, TA_CENTER)]

    SimpleDocTemplate(path, pagesize=A4, leftMargin=12 * mm, rightMargin=12 * mm,
                      topMargin=12 * mm, bottomMargin=12 * mm,
                      title=f"Quotation {d.get('so') or ''}").build(story)
    return path
