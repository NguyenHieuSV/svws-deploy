"""Sinh chứng từ Đơn đặt hàng (PO) dạng PDF theo mẫu SVWS (2 trang).

Trang 1: Đơn đặt hàng. Trang 2: Phiếu xác nhận của nhà cung cấp.
Dùng reportlab + font DejaVu (hỗ trợ tiếng Việt). Không phụ thuộc dịch vụ ngoài.
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
                                TableStyle, Image, PageBreak)

NAVY = HexColor("#1F4E79")
LIGHT = HexColor("#EAF0F7")
GREY = HexColor("#666666")
LINE = HexColor("#BBBBBB")
_FONTS_OK = False
_DEFAULT_SIGN = os.path.join(os.path.dirname(__file__), "assets", "e_sign.png")


def _dang_ky_font(regular, bold):
    global _FONTS_OK
    if _FONTS_OK:
        return ("SV", "SVb")
    reg = regular if os.path.exists(regular) else None
    bd = bold if os.path.exists(bold) else None
    if reg:
        pdfmetrics.registerFont(TTFont("SV", reg))
    if bd:
        pdfmetrics.registerFont(TTFont("SVb", bd))
    _FONTS_OK = True
    return ("SV" if reg else "Helvetica", "SVb" if bd else "Helvetica-Bold")


def _tien(x):
    try:
        return f"{int(round(float(x))):,}".replace(",", ".")
    except Exception:
        return str(x)


def tao_po_pdf(path, d, cong_ty=None,
               font_path="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
               font_bold_path="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
               chu_ky_path="", ky_so=True):
    F, FB = _dang_ky_font(font_path, font_bold_path)
    cong_ty = cong_ty or {}
    W = A4[0] - 30 * mm
    sign = "" if not ky_so else (chu_ky_path or (_DEFAULT_SIGN if os.path.exists(_DEFAULT_SIGN) else ""))

    def _sign_img(wmm, align="CENTER"):
        if sign and os.path.exists(sign):
            try:
                from reportlab.lib.utils import ImageReader
                iw, ih = ImageReader(sign).getSize()
                img = Image(sign, width=wmm * mm, height=wmm * mm * ih / iw)
                img.hAlign = align
                return img
            except Exception:
                return None
        return None

    def P(s, sz=9, fn=None, col=black, al=TA_LEFT, ld=None):
        return Paragraph(s, ParagraphStyle("p", fontName=fn or F, fontSize=sz,
                         textColor=col, alignment=al, leading=ld or (sz + 3)))

    def band(text, width, size=10):
        t = Table([[P(text, size, FB, white)]], colWidths=[width])
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), NAVY),
                               ("LEFTPADDING", (0, 0), (-1, -1), 7),
                               ("TOPPADDING", (0, 0), (-1, -1), 4),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
        return t

    story = []

    # HEADER
    logo = []
    if cong_ty.get("logo_path") and os.path.exists(cong_ty["logo_path"]):
        try:
            logo.append(Image(cong_ty["logo_path"], width=26 * mm, height=14 * mm))
        except Exception:
            pass
    if not logo:
        logo.append(P("<b>Sóng Việt</b>", 16, FB, NAVY))
        logo.append(P("WE HAVE SOLUTIONS", 6.5, F, GREY))
    left = logo + [Spacer(1, 3),
                   P(f"<b>{cong_ty.get('ten','')}</b>", 9.5, FB),
                   P(cong_ty.get("dia_chi", ""), 8, F, GREY),
                   P(f"Tel: {cong_ty.get('tel','')} | Email: {cong_ty.get('email','')}", 8, F, GREY),
                   P(f"Website: {cong_ty.get('website','')}", 8, F, GREY)]

    info = Table([[P("<b>Mã yêu cầu:</b>", 8.5, FB, NAVY), P(f"<b>{d.get('ma_yeu_cau','')}</b>", 8.5, FB, NAVY)],
                  [P("Ngày:", 8.5, FB), P(d.get("ngay", ""), 8.5)],
                  [P("Hiệu lực đến:", 8.5, FB), P(d.get("hieu_luc_den", ""), 8.5)]],
                 colWidths=[26 * mm, 32 * mm])
    info.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                              ("TOPPADDING", (0, 0), (-1, -1), 1), ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]))
    tbox = Table([[P("<b>ĐƠN ĐẶT HÀNG</b>", 15, FB, NAVY, TA_CENTER)],
                  [P("<i>Purchase Order</i>", 8.5, F, GREY, TA_CENTER)]], colWidths=[62 * mm])
    tbox.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 1, NAVY),
                              ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    header = Table([[left, [tbox, Spacer(1, 4), info]]], colWidths=[W * 0.54, W * 0.46])
    header.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("ALIGN", (1, 0), (1, 0), "RIGHT")]))
    story += [header, Spacer(1, 8)]

    # NCC
    story += [band("THÔNG TIN NHÀ CUNG CẤP", W), Spacer(1, 4)]
    ncc = Table([[P(f"<b>Tên NCC:</b> {d.get('ncc_ten','')}", 9),
                  P(f"<b>Email:</b> {d.get('ncc_email','')}", 9)],
                 [P(f"<b>Người liên hệ:</b> {d.get('nguoi_lien_he','')}", 9), ""]],
                colWidths=[W * 0.5, W * 0.5])
    ncc.setStyle(TableStyle([("TOPPADDING", (0, 0), (-1, -1), 1), ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]))
    story += [ncc, Spacer(1, 8)]

    # BẢNG SP/DV
    story += [band("CHI TIẾT SẢN PHẨM / DỊCH VỤ", W)]
    head = ["STT", "Tên sản phẩm", "Mô tả / Spec", "SL", "ĐVT", "Đơn giá", "VAT (%)", "Thành tiền (gồm VAT)"]
    al = [TA_CENTER, TA_LEFT, TA_LEFT, TA_CENTER, TA_CENTER, TA_RIGHT, TA_CENTER, TA_RIGHT]
    rows = [[P(f"<b>{h}</b>", 8, FB, white, al[i]) for i, h in enumerate(head)]]
    tam, tong = 0.0, 0.0
    for i, ln in enumerate(d.get("lines", []), 1):
        sl = float(ln.get("sl", 0)); gia = float(ln.get("don_gia", 0)); vat = float(ln.get("vat", 0))
        truoc = sl * gia; sau = truoc * (1 + vat / 100.0); tam += truoc; tong += sau
        rows.append([P(str(i), 8, F, black, TA_CENTER), P(ln.get("ten", ""), 8),
                     P(ln.get("mo_ta", "") or "", 8, F, GREY), P(f"{sl:g}", 8, F, black, TA_CENTER),
                     P(ln.get("dvt", "") or "", 8, F, black, TA_CENTER), P(_tien(gia), 8, F, black, TA_RIGHT),
                     P(f"{vat:g}%", 8, F, black, TA_CENTER), P(_tien(sau), 8, F, black, TA_RIGHT)])
    colw = [W * x for x in (0.05, 0.20, 0.27, 0.07, 0.07, 0.13, 0.08, 0.13)]
    tbl = Table(rows, colWidths=colw, repeatRows=1)
    tbl.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), NAVY),
                             ("GRID", (0, 0), (-1, -1), 0.5, LINE), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                             ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                             ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, LIGHT])]))
    story += [tbl]
    foot = Table([[P("Tạm tính (chưa VAT):", 9, FB, black, TA_RIGHT), P(_tien(tam) + " VNĐ", 9, FB, black, TA_RIGHT)]],
                 colWidths=[W * 0.74, W * 0.26])
    foot.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.5, LINE),
                              ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    total = Table([[P("<b>TỔNG CỘNG (đã gồm VAT):</b>", 10, FB, white, TA_RIGHT),
                    P(f"<b>{_tien(tong)} VNĐ</b>", 10, FB, white, TA_RIGHT)]], colWidths=[W * 0.74, W * 0.26])
    total.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), NAVY),
                               ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    story += [foot, total, Spacer(1, 10)]

    # ĐIỀU KHOẢN & XÁC NHẬN
    bands = Table([[band("ĐIỀU KHOẢN & GHI CHÚ", W * 0.49, 9), "", band("XÁC NHẬN", W * 0.49, 9)]],
                  colWidths=[W * 0.49, W * 0.02, W * 0.49])
    dk = [P(f"• <b>Thanh toán:</b> {d.get('thanh_toan','')}", 8.5), Spacer(1, 2),
          P(f"• <b>Thời gian giao hàng:</b> {d.get('thoi_gian_giao','')}", 8.5), Spacer(1, 2),
          P(f"• <b>Địa điểm giao hàng:</b> {d.get('dia_diem_giao','')}", 8.5)]
    xn = [P(f"<b>Người đặt hàng:</b> {d.get('nguoi_dat','')}", 8.5),
          Spacer(1, 4), P("<b>Người duyệt:</b>", 8.5, F, black, TA_CENTER)]
    _img1 = _sign_img(40)
    if _img1 is not None:
        xn += [Spacer(1, 2), _img1]
    elif d.get("nguoi_duyet"):
        xn.append(P(d.get("nguoi_duyet"), 8.5, F, black, TA_CENTER))
    body = Table([[dk, "", xn]], colWidths=[W * 0.49, W * 0.02, W * 0.49])
    body.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 6)]))
    story += [bands, body]

    # TRANG 2
    story.append(PageBreak())
    story += [band("PHIẾU XÁC NHẬN CỦA NHÀ CUNG CẤP", W), Spacer(1, 8)]
    story += [P(f"Chúng tôi, <b>{d.get('ncc_ten','')}</b>, xác nhận đã nhận và đồng ý với các điều khoản, "
                f"sản phẩm/dịch vụ, số lượng, đơn giá và tổng giá trị nêu trong đơn đặt hàng số "
                f"<b>{d.get('ma_yeu_cau','')}</b> này. Chúng tôi cam kết cung cấp hàng hóa/dịch vụ đúng chất lượng "
                f"và đúng thời gian giao hàng đã thỏa thuận.", 9, F, black, TA_LEFT, 14), Spacer(1, 8)]
    cb = "\u2610"
    conf = Table([[P("<b>Hình thức xác nhận:</b>", 9), P("<b>Ngày dự kiến giao hàng:</b> ...........................", 9)],
                  [P(f"{cb} Đồng ý toàn bộ đơn hàng", 9), P("<b>Thời hạn bảo hành:</b> ...........................", 9)],
                  [P(f"{cb} Đồng ý kèm điều chỉnh (ghi rõ bên dưới)", 9), ""]],
                 colWidths=[W * 0.5, W * 0.5])
    conf.setStyle(TableStyle([("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    story += [conf, Spacer(1, 8), P("<b>Ghi chú / Điều chỉnh của nhà cung cấp:</b>", 9), Spacer(1, 4),
              P("." * 115, 9, F, GREY), Spacer(1, 2), P("." * 115, 9, F, GREY), Spacer(1, 18)]
    _img2 = _sign_img(38)
    sig = Table([[P("<b>ĐẠI DIỆN BÊN MUA</b>", 9.5, FB, NAVY, TA_CENTER),
                  P("<b>ĐẠI DIỆN NHÀ CUNG CẤP</b>", 9.5, FB, NAVY, TA_CENTER)],
                 [P(f"<i>{cong_ty.get('ten','')}</i>", 8.5, F, GREY, TA_CENTER),
                  P("<i>(Ký, ghi rõ họ tên và đóng dấu)</i>", 8.5, F, GREY, TA_CENTER)],
                 [(_img2 or Spacer(1, 26)), ""]],
                colWidths=[W * 0.5, W * 0.5])
    sig.setStyle(TableStyle([("TOPPADDING", (0, 0), (-1, -1), 4),
                             ("BOTTOMPADDING", (0, 1), (-1, 1), 6 if _img2 else 30),
                             ("ALIGN", (0, 2), (0, 2), "CENTER"), ("VALIGN", (0, 2), (-1, 2), "TOP")]))
    story += [sig, Table([["", P("_______________________________", 9, F, GREY, TA_CENTER)],
                          ["", P("Họ và tên", 8.5, F, GREY, TA_CENTER)]], colWidths=[W * 0.5, W * 0.5]),
              Spacer(1, 16),
              P("<b>Cảm ơn quý công ty đã hợp tác và đồng hành cùng Sóng Việt!</b>", 9, FB, NAVY, TA_CENTER),
              P(f"Ngày in: {d.get('ngay','')} | {cong_ty.get('ten','')}", 8, F, GREY, TA_CENTER)]

    SimpleDocTemplate(path, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm,
                      topMargin=14 * mm, bottomMargin=14 * mm,
                      title=f"PO {d.get('ma_yeu_cau','')}").build(story)
    return path
