"""Địa chỉ trụ sở công ty (đổi 19/10/2026) phải thống nhất ở mọi nơi in/gửi ra ngoài."""
import os
import re

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _doc(rel):
    with open(os.path.join(GOC, rel), encoding="utf-8") as f:
        return f.read()


def test_mac_dinh_cau_hinh_la_dia_chi_moi():
    from app.config import Settings
    dc = Settings.model_fields["cong_ty_dia_chi"].default
    assert "412 Nguyễn Thị Minh Khai" in dc and "HM Town" in dc
    assert "Võ Văn Tần" not in dc


def test_bao_gia_pdf_mac_dinh_dia_chi_moi():
    s = _doc("app/bao_gia_pdf.py")
    assert "412 Nguyen Thi Minh Khai" in s
    assert "Vo Van Tan" not in s


def test_giao_dien_khong_con_dia_chi_tru_so_cu():
    s = _doc("svws_app.html")
    assert "448 Võ Văn Tần" not in s
    assert "448 Vo Van Tan" not in s
    # tiêu đề thư tín (letterhead) không còn dùng địa chỉ xưởng làm địa chỉ công ty
    assert not re.search(r"SONG VIET WATER SOLUTIONS<small>275 An Phú Đông", s)


def test_nguoi_bao_gia_mac_dinh_la_nguyen_thuong():
    s = _doc("svws_app.html")
    assert s.count('nguoi_bg:"Nguyễn Thương"') == 2
    assert 'nguoi_bg:"Nguyen Nghi"' not in s


def test_xuong_va_noi_giao_hang_van_giu_dia_chi_xuong():
    # xưởng / nơi giao hàng mặc định là kho An Phú Đông, không phải trụ sở — không được đổi nhầm
    from app.routers.ncc import DIA_CHI_GIAO_HANG
    assert "An Phú Đông" in DIA_CHI_GIAO_HANG
