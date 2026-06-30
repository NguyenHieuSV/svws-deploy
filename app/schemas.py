from decimal import Decimal
from datetime import date, time, datetime
from pydantic import BaseModel, ConfigDict, Field


class TokenRa(BaseModel):
    access_token: str
    token_type: str = "bearer"


class NguoiDungRa(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    vai_tro_id: int


class HangHoaVao(BaseModel):
    ma: str | None = None
    ten: str
    loai: str = Field(pattern="^(SAN_PHAM|VAT_TU|THIET_BI|HOA_CHAT)$")
    don_vi: str | None = None
    gia_ban: Decimal = 0
    ton_min: Decimal = 0
    ton_max: Decimal | None = None


class HangHoaRa(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ma: str | None
    ten: str
    loai: str
    don_vi: str | None
    so_luong: Decimal = 0
    ton_min: Decimal = 0
    gia_ban: Decimal = 0
    ton_max: Decimal | None = None


class HangHoaSua(BaseModel):
    ten: str | None = None
    loai: str | None = Field(default=None, pattern="^(SAN_PHAM|VAT_TU|THIET_BI)$")
    don_vi: str | None = None
    gia_ban: Decimal | None = None
    ton_min: Decimal | None = None
    ton_max: Decimal | None = None


class PhieuCtVao(BaseModel):
    hang_hoa_id: int
    so_luong: Decimal = Field(gt=0)


class PhieuKhoVao(BaseModel):
    loai: str = Field(pattern="^(NHAP|XUAT)$")
    so: str | None = None
    chi_tiet: list[PhieuCtVao] = Field(min_length=1)


class PhieuKhoRa(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    so: str | None
    loai: str
    ngay: date


class DieuChinhVao(BaseModel):
    hang_hoa_id: int
    so_luong_moi: Decimal = Field(ge=0)
    ly_do: str


# ---------- Nhà cung cấp & Mua hàng ----------
class NccVao(BaseModel):
    ma: str | None = None
    ten: str
    ma_so_thue: str | None = None
    dien_thoai: str | None = None
    email: str | None = None
    dia_chi: str | None = None
    han_muc_cong_no: Decimal | None = None
    nguoi_phu_trach: int | None = None
    ghi_chu: str | None = None


class NccRa(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ma: str | None
    ten: str
    email: str | None = None
    diem_danh_gia: Decimal
    han_muc_cong_no: Decimal = 0
    nguoi_phu_trach: int | None = None
    blacklist: bool


class DanhGiaVao(BaseModel):
    diem: Decimal = Field(ge=0, le=5)
    don_mua_id: int | None = None


class DonMuaCtVao(BaseModel):
    hang_hoa_id: int
    so_luong: Decimal = Field(gt=0)
    don_gia: Decimal = Field(ge=0)


class DonMuaVao(BaseModel):
    nha_cung_cap_id: int
    so: str | None = None
    don_hang_id: int | None = None
    ngay_hen_giao: date | None = None
    chi_tiet: list[DonMuaCtVao] = Field(min_length=1)


class DonMuaRa(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    so: str | None
    nha_cung_cap_id: int
    don_hang_id: int | None = None
    tong_tien: Decimal
    trang_thai: str
    trang_thai_nhan: str = "CHUA"
    ngay_hen_giao: date | None = None
    ngay_giao_thuc: date | None = None


class YeuCauMuaItemVao(BaseModel):
    hang_hoa_id: int
    so_luong: Decimal = Field(gt=0)
    don_gia: Decimal | None = None
    ghi_chu: str | None = None
    nha_cung_cap_id: int | None = None


class YeuCauMuaVao(BaseModel):
    # Tương thích cũ: 1 sản phẩm
    hang_hoa_id: int | None = None
    so_luong: Decimal | None = None
    don_gia: Decimal | None = None
    ghi_chu: str | None = None
    # Nhiều sản phẩm
    items: list[YeuCauMuaItemVao] | None = None
    ly_do: str | None = None
    nha_cung_cap_id: int | None = None
    don_hang_id: int | None = None
    ngay_can: date | None = None
    dinh_kem_url: str | None = None


class TaoPoTuDeXuatVao(BaseModel):
    nha_cung_cap_id: int | None = None
    don_gia: Decimal | None = None
    ngay_hen_giao: date | None = None


class LyDoVao(BaseModel):
    ly_do: str | None = None


class YeuCauMuaRa(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    hang_hoa_id: int
    so_luong: Decimal
    ly_do: str | None
    trang_thai: str = "MOI"
    nha_cung_cap_id: int | None = None
    don_hang_id: int | None = None
    don_gia: Decimal | None = None
    ngay_can: date | None = None
    don_mua_id: int | None = None
    ai_ncc_id: int | None = None
    ai_goi_y: str | None = None
    dinh_kem_url: str | None = None
    dinh_kem_file: str | None = None


# ---------- Dự án ----------
class DuAnVao(BaseModel):
    ma: str | None = None
    ten: str
    khach_hang_id: int | None = None
    qcvn: str | None = None
    deadline: str | None = None


class DuAnRa(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ma: str | None
    ten: str
    du_toan: Decimal
    chi_phi_thuc_te: Decimal
    trang_thai: str
    tien_do: Decimal | None = None
    loai_du_an: str | None = None
    chu_dau_tu: str | None = None
    cong_suat: str | None = None
    gia_tri_hop_dong: Decimal | None = None
    ngay_kt_ke_hoach: date | None = None


class ForecastLine(BaseModel):
    hang_muc: str | None = None
    mo_ta: str | None = None
    so_luong: Decimal = 1
    don_gia: Decimal = 0


class NhapDuToanVao(BaseModel):
    """Payload xuất ra từ Forecast Cal."""
    nguon: str = "FORECAST_CAL"
    lines: list[ForecastLine] = Field(min_length=1)


class ChiPhiVao(BaseModel):
    hang_muc: str | None = None
    mo_ta: str | None = None
    so_tien: Decimal = Field(gt=0)


class ChiPhiRa(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    du_an_id: int
    hang_muc: str | None
    so_tien: Decimal
    trang_thai: str


class NghiemThuVao(BaseModel):
    ket_qua_qcvn: str | None = None
    khach_ky: bool = False


# ---------- Bán hàng ----------
class KhachHangVao(BaseModel):
    ma: str | None = None
    ten: str
    ma_so_thue: str | None = None
    dien_thoai: str | None = None
    email: str | None = None
    phan_loai_abc: str | None = None
    khong_nhan_email: bool = False


class KhachHangRa(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ma: str | None
    ten: str
    email: str | None = None
    phan_loai_abc: str | None = None
    khong_nhan_email: bool = False


class BaoGiaCtVao(BaseModel):
    hang_hoa_id: int
    so_luong: Decimal = Field(gt=0)
    don_gia: Decimal = Field(ge=0)


class PoNoiDungVao(BaseModel):
    """Điều kiện để dựng chứng từ PO gửi NCC (xem trước)."""
    noi_giao: str | None = None
    dieu_kien_giao_hang: str | None = None
    dieu_kien_thanh_toan: str | None = None
    ghi_chu: str | None = None
    ngay_hen_giao: date | None = None


class PoPdfVao(BaseModel):
    """Trường để dựng chứng từ PO (PDF) theo mẫu SVWS."""
    ma_yeu_cau: str | None = None
    hieu_luc_den: str | None = None
    nguoi_lien_he: str | None = None
    nguoi_dat: str | None = None
    nguoi_duyet: str | None = None
    vat: float = 0
    specs: list[str] | None = None
    noi_giao: str | None = None
    thoi_gian_giao: str | None = None
    dieu_kien_thanh_toan: str | None = None
    ngay_hen_giao: date | None = None
    ghi_chu: str | None = None
    ky_so: bool = True


class GuiPoVao(PoPdfVao):
    dieu_kien_giao_hang: str | None = None
    tieu_de: str | None = None
    noi_dung: str | None = None
    dinh_kem_pdf: bool = True


class RfqNoiDungVao(BaseModel):
    """Các trường mô tả sản phẩm/điều kiện để dựng email hỏi giá (xem trước)."""
    quy_cach: str | None = None
    don_vi: str | None = None
    noi_giao: str | None = None
    thoi_gian_giao: str | None = None
    dieu_kien_thanh_toan: str | None = None
    yeu_cau_khac: str | None = None
    han_bao_gia: date | None = None


class RfqVao(RfqNoiDungVao):
    hang_hoa_id: int
    so_luong: Decimal = Decimal(0)
    nha_cung_cap_ids: list[int] = Field(min_length=1)
    yeu_cau_mua_id: int | None = None
    tieu_de: str | None = None
    noi_dung: str | None = None      # nội dung đã biên tập (override mẫu)


class GuiRfqVao(RfqNoiDungVao):
    nha_cung_cap_ids: list[int] = Field(min_length=1)
    tieu_de: str | None = None
    noi_dung: str | None = None      # nội dung đã biên tập (override mẫu)


class RfqLogRa(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nha_cung_cap_id: int
    email: str | None
    da_gui: bool
    ket_qua: str | None


class RfqRa(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    hang_hoa_id: int
    so_luong: Decimal
    han_bao_gia: date | None
    gui_tu: str | None
    ngay: date


class BaoGiaVao(BaseModel):
    khach_hang_id: int
    so: str | None = None
    chi_tiet: list[BaoGiaCtVao] = Field(min_length=1)


class BaoGiaRa(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    so: str | None
    khach_hang_id: int
    tong_tien: Decimal
    trang_thai: str


class DonHangRa(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    so: str | None
    khach_hang_id: int
    tong_tien: Decimal
    trang_thai: str


# ---------- Kế toán & Tài chính ----------
class HoaDonRa(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    loai: str
    tong_tien: Decimal
    hddt_provider: str | None
    hddt_ma_tra_cuu: str | None
    hddt_trang_thai: str | None


class CongNoRa(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    loai: str
    so_tien: Decimal
    da_thanh_toan: Decimal
    han: date | None
    trang_thai: str


class ButToanRa(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ngay: date
    tk_no: str
    tk_co: str
    so_tien: Decimal
    dien_giai: str | None


class PhatHanhVao(BaseModel):
    provider: str | None = None   # DEMO | MISA | VNPT | VIETTEL


class ThuTienVao(BaseModel):
    so_tien: Decimal = Field(gt=0)
    hinh_thuc: str = "CK"          # CK = chuyển khoản, TM = tiền mặt


# ---------- Nhân sự / Lương ----------
class NhanVienRa(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ho_ten: str
    chuc_danh: str | None
    luong_co_ban: Decimal


class ChamCongVao(BaseModel):
    nhan_vien_id: int
    ngay: date
    gio_vao: time | None = None
    gio_ra: time | None = None


class NghiPhepVao(BaseModel):
    nhan_vien_id: int
    tu_ngay: date
    den_ngay: date
    loai: str = "PHEP"


class TinhLuongVao(BaseModel):
    thang: str = Field(pattern=r"^\d{4}-\d{2}$")   # YYYY-MM


class HoSoLuongVao(BaseModel):
    luong_co_ban: Decimal = Decimal(0)
    luong_dong_bh: Decimal = Decimal(0)
    so_phu_thuoc: int = 0
    phu_cap_an: Decimal = Decimal(0)
    phu_cap_di_lai: Decimal = Decimal(0)
    phu_cap_dien_thoai: Decimal = Decimal(0)
    phu_cap_trach_nhiem: Decimal = Decimal(0)
    ma_so_thue: str | None = None
    so_tai_khoan: str | None = None
    ngan_hang: str | None = None
    email: str | None = None
    tk_chi_phi: str = "642"
    chuc_danh: str | None = None


class KyLuongVao(BaseModel):
    thang: str = Field(pattern=r"^\d{4}-\d{2}$")
    cong_chuan: Decimal = Decimal(26)
    ngay_chot: date | None = None


class ChamCongLuongVao(BaseModel):
    cong_thuc_te: Decimal | None = None
    gio_ot_thuong: Decimal | None = None
    gio_ot_cuoi_tuan: Decimal | None = None
    gio_ot_le: Decimal | None = None
    tam_ung: Decimal | None = None
    phu_cap_khac: Decimal | None = None
    ngay_nghi_kpep: Decimal | None = None
    so_phut_di_tre: int | None = None
    khau_tru_khac: Decimal | None = None


class BangLuongRa(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nhan_vien_id: int
    thang: str
    bhxh: Decimal
    thue_tncn: Decimal
    khau_tru: Decimal
    thuc_linh: Decimal
    trang_thai: str


# ---------- Cho thuê ----------
class TaiSanVao(BaseModel):
    hang_hoa_id: int | None = None      # với HC/VT/TB
    nhan_vien_id: int | None = None     # với NHAN_SU
    so_luong: Decimal = 1


class HopDongThueVao(BaseModel):
    khach_hang_id: int
    doi_tuong: str = Field(pattern="^(NHAN_SU|HOA_CHAT|VAT_TU|THIET_BI)$")
    gia_thue: Decimal = Field(gt=0)
    chu_ky: str = "THANG"               # THANG / QUY
    ngay_bat_dau: date
    ngay_ket_thuc: date
    so: str | None = None
    tai_san: list[TaiSanVao] = Field(min_length=1)


class HopDongThueRa(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    so: str | None
    khach_hang_id: int
    doi_tuong: str
    gia_thue: Decimal
    ngay_ket_thuc: date
    trang_thai: str


# ---------- CRM ----------
class ChamSocVao(BaseModel):
    khach_hang_id: int
    loai: str = Field(pattern="^(GOI|EMAIL|KHIEU_NAI|SINH_NHAT)$")
    noi_dung: str | None = None
    ngay_hen: date | None = None


class ChamSocRa(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    khach_hang_id: int
    loai: str
    noi_dung: str | None
    ngay_hen: date | None
    trang_thai: str
    csat: Decimal | None


class HoanThanhVao(BaseModel):
    csat: Decimal | None = Field(default=None, ge=1, le=5)
    noi_dung: str | None = None


# ---------- Bán hàng mở rộng: tệp & email ----------
class TepRa(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    loai: str
    ten_file: str
    kich_thuoc: int | None
    content_type: str | None


class ChienDichVao(BaseModel):
    ten: str
    tieu_de: str
    noi_dung: str = Field(min_length=1)
    bo_loc_abc: str | None = None            # A/B/C hoặc None = tất cả
    khach_hang_ids: list[int] | None = None  # nếu có: chỉ gửi các KH này (ưu tiên hơn ABC)


class ChienDichRa(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ten: str
    tieu_de: str
    bo_loc_abc: str | None
    khach_hang_ids: str | None = None
    trang_thai: str


# ---------- Liên lạc khách hàng ----------
class GuiEmailKHVao(BaseModel):
    tieu_de: str = Field(min_length=1)
    noi_dung: str = Field(min_length=1)
    lien_quan_loai: str | None = None       # BAO_GIA / DON_HANG / HOP_DONG
    lien_quan_id: int | None = None


class GhiLienLacVao(BaseModel):
    kenh: str = Field(pattern="^(GOI|GAP|GHI_CHU)$")
    noi_dung: str = Field(min_length=1)
    huong: str = "DI"


class LienLacRa(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    kenh: str
    huong: str
    tieu_de: str | None
    noi_dung: str | None
    gui_tu: str | None
    trang_thai: str | None
    thoi_diem: datetime


class GanKhachVao(BaseModel):
    khach_hang_id: int


class TrangThaiCVVao(BaseModel):
    trang_thai: str = Field(pattern="^(MO|DANG_XU_LY|XONG)$")


class GiaiDoanVao(BaseModel):
    giai_doan: str = Field(pattern="^(MOI|QUAN_TAM|BAO_GIA|DAM_PHAN|THANG|THUA)$")
    gia_tri_dk: Decimal | None = None
    ly_do_thua: str | None = None


class BaoGiaVao(BaseModel):
    nha_cung_cap_id: int
    hang_hoa_id: int
    don_gia: Decimal = Field(gt=0)
    so_luong_toi_thieu: Decimal = Decimal(0)
    hieu_luc_den: date | None = None
    nguon: str = "THU_CONG"
    dieu_kien: str | None = None
    ghi_chu: str | None = None


class BaoGiaRa(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nha_cung_cap_id: int
    hang_hoa_id: int
    don_gia: Decimal
    so_luong_toi_thieu: Decimal
    hieu_luc_den: date | None
    ngay: date
    nguon: str


class NhanHangCtVao(BaseModel):
    don_mua_ct_id: int
    so_luong: Decimal = Field(gt=0)


class NhanHangVao(BaseModel):
    chi_tiet: list[NhanHangCtVao] = Field(min_length=1)
    han_thanh_toan: date | None = None
    tao_cong_no: bool = True
    dat_qc: bool = True


class DonMuaCtRa(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    hang_hoa_id: int
    so_luong: Decimal
    don_gia: Decimal
    so_luong_nhan: Decimal


class DonMuaChiTietRa(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    so: str | None
    nha_cung_cap_id: int
    don_hang_id: int | None = None
    tong_tien: Decimal
    trang_thai: str
    trang_thai_nhan: str
    ngay_hen_giao: date | None = None
    ngay_giao_thuc: date | None = None
    chi_tiet: list[DonMuaCtRa]


# ---------- Kế toán: Quỹ tiền + Phiếu thu/chi ----------
class QuyVao(BaseModel):
    ma: str | None = None
    ten: str
    loai: str = "TIEN_MAT"
    so_tk: str | None = None
    tk_ke_toan: str = "111"
    so_du_dau: Decimal = Decimal(0)


class PhieuVao(BaseModel):
    loai: str                       # THU | CHI
    quy_id: int
    so_tien: Decimal = Field(gt=0)
    ngay: date | None = None
    doi_tac_loai: str | None = None  # KH | NCC | KHAC
    khach_hang_id: int | None = None
    nha_cung_cap_id: int | None = None
    don_hang_id: int | None = None
    cong_no_id: int | None = None
    tk_doi_ung: str | None = None
    dien_giai: str | None = None
    ghi_chu: str | None = None
    la_tam_ung: bool = False
    trinh_luon: bool = False


class DuyetPhieuVao(BaseModel):
    ghi_chu: str | None = None


class HoaDonVao(BaseModel):
    loai: str                              # BAN | MUA
    khach_hang_id: int | None = None
    nha_cung_cap_id: int | None = None
    don_hang_id: int | None = None
    so: str | None = None
    ngay: date | None = None
    tien_truoc_thue: Decimal = Field(ge=0)
    thue_suat: Decimal = Decimal(8)        # % VAT
    tk_chi_phi: str | None = None          # cho HĐ mua: 632/642/641/627
    dien_giai: str | None = None
    tao_cong_no: bool = True
    hach_toan_luon: bool = True
    han_ngay: int = 30


class DatCocVao(BaseModel):
    ty_le: Decimal = Field(ge=0, le=100)


class ThamSoTaiChinhVao(BaseModel):
    von_chu_so_huu: Decimal = Decimal(0)
    tai_san_co_dinh: Decimal = Decimal(0)
    no_dai_han: Decimal = Decimal(0)
    chi_co_dinh_thang: Decimal = Decimal(0)


class KhoanVayVao(BaseModel):
    so: str | None = None
    ben_cho_vay: str
    loai: str = Field(default="NGAN_HAN", pattern="^(NGAN_HAN|DAI_HAN)$")
    so_tien_goc: Decimal = Field(gt=0)
    lai_suat_nam: Decimal = Field(ge=0, le=100)
    phuong_thuc: str = Field(default="GOC_DEU", pattern="^(GOC_DEU|TRA_DEU|GOC_CUOI)$")
    ngay_nhan: date
    so_ky: int = Field(default=12, ge=1, le=600)
    chu_ky_thang: int = Field(default=1, ge=1, le=12)
    tk_tien: str = "112"
    ghi_chu: str | None = None


class ThamSoLuongVao(BaseModel):
    tl_bhxh_nv: Decimal | None = None
    tl_bhyt_nv: Decimal | None = None
    tl_bhtn_nv: Decimal | None = None
    tl_bhxh_dn: Decimal | None = None
    tl_bhyt_dn: Decimal | None = None
    tl_bhtn_dn: Decimal | None = None
    tran_bhxh_bhyt: Decimal | None = None
    tran_bhtn: Decimal | None = None
    giam_tru_ban_than: Decimal | None = None
    giam_tru_phu_thuoc: Decimal | None = None
    mien_thue_an: Decimal | None = None
    hs_ot_thuong: Decimal | None = None
    hs_ot_cuoi_tuan: Decimal | None = None
    hs_ot_le: Decimal | None = None
    luong_co_so: Decimal | None = None
    luong_toi_thieu_vung: Decimal | None = None
    bac_thue: list | None = None


class ChamCongRecord(BaseModel):
    nhan_vien_id: int | None = None
    ma: str | None = None
    cong_thuc_te: Decimal | None = None
    gio_ot_thuong: Decimal | None = None
    gio_ot_cuoi_tuan: Decimal | None = None
    gio_ot_le: Decimal | None = None
    ngay_nghi_kpep: Decimal | None = None
    so_phut_di_tre: int | None = None


class ChamCongImportVao(BaseModel):
    ban_ghi: list[ChamCongRecord]


class TrichQuyVao(BaseModel):
    ma_quy: str
    ky: str = Field(pattern=r"^\d{4}(-\d{2})?$")   # YYYY hoặc YYYY-MM
    so_tien: Decimal = Field(gt=0)
    dien_giai: str | None = None
    ngay: date | None = None


class SuDungQuyVao(BaseModel):
    ma_quy: str
    ky: str = Field(pattern=r"^\d{4}(-\d{2})?$")
    so_tien: Decimal = Field(gt=0)
    dien_giai: str | None = None
    ngay: date | None = None


class DuAnThongTinVao(BaseModel):
    ten: str | None = None
    ma: str | None = None
    khach_hang_id: int | None = None
    truong_du_an: int | None = None
    chu_dau_tu: str | None = None
    dia_diem: str | None = None
    loai_du_an: str | None = None
    cong_suat: str | None = None
    gia_tri_hop_dong: Decimal | None = None
    qcvn: str | None = None
    ngay_bat_dau: date | None = None
    ngay_kt_ke_hoach: date | None = None
    ngay_kt_thuc_te: date | None = None
    deadline: date | None = None
    trang_thai: str | None = None
    mo_ta: str | None = None
    tieu_chuan_dau_ra: str | None = None


class ChiTieuVao(BaseModel):
    thu_tu: int | None = None
    ten: str | None = None
    don_vi: str | None = None
    gia_tri_vao: Decimal | None = None
    gioi_han_ra: Decimal | None = None
    ghi_chu: str | None = None


class PhanTichVao(BaseModel):
    mo_ta: str | None = None


class NapChiTieuVao(BaseModel):
    danh_sach: list[ChiTieuVao] = []


class ThietKeVao(BaseModel):
    cong_nghe: str | None = None
    cong_suat_tk: str | None = None
    tieu_chuan: str | None = None
    thong_so: list | str | None = None
    nguoi_thiet_ke: str | None = None
    ngay_duyet: date | None = None
    phien_ban: str | None = None
    trang_thai: str | None = None
    ghi_chu: str | None = None


class MocVao(BaseModel):
    thu_tu: int | None = None
    ten: str
    giai_doan: str | None = None
    ngay_bd_kh: date | None = None
    ngay_kt_kh: date | None = None
    ngay_kt_tt: date | None = None
    trong_so: Decimal | None = None
    phan_tram: Decimal | None = None
    trang_thai: str | None = None
    phu_trach: str | None = None
    ghi_chu: str | None = None


class MocSuaVao(BaseModel):
    thu_tu: int | None = None
    ten: str | None = None
    giai_doan: str | None = None
    ngay_bd_kh: date | None = None
    ngay_kt_kh: date | None = None
    ngay_kt_tt: date | None = None
    trong_so: Decimal | None = None
    phan_tram: Decimal | None = None
    trang_thai: str | None = None
    phu_trach: str | None = None
    ghi_chu: str | None = None


class AnToanVao(BaseModel):
    hang_muc: str
    moi_nguy: str | None = None
    muc_rui_ro: str | None = "TRUNG"
    bien_phap: str | None = None
    phu_trach: str | None = None
    han: date | None = None
    trang_thai: str | None = None
    nguoi_danh_gia: str | None = None
    ngay_danh_gia: date | None = None


class NhatKyVao(BaseModel):
    ngay: date | None = None
    noi_dung: str | None = None
    nhan_luc: str | None = None
    thiet_bi: str | None = None
    thoi_tiet: str | None = None
    van_de: str | None = None
    nguoi_ghi: str | None = None


class TaiLieuMetaVao(BaseModel):
    loai: str | None = None
    ten: str | None = None
    ma_so: str | None = None
    phien_ban: str | None = None
    ngay: date | None = None
    trang_thai: str | None = None
    ghi_chu: str | None = None


class KpiVao(BaseModel):
    ten: str
    don_vi: str | None = None
    chieu: str | None = "CAO"
    muc_tieu: Decimal | None = None
    thuc_te: Decimal | None = None
    trong_so: Decimal | None = None
    ky: str | None = None
    ghi_chu: str | None = None


class BaoCaoVao(BaseModel):
    ky: str | None = None
    tieu_de: str | None = None
    noi_dung: str | None = None
    van_de: str | None = None
