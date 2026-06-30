from datetime import datetime, date, time
from decimal import Decimal
from sqlalchemy import String, BigInteger, Integer, Numeric, Date, Time, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import ENUM as PGEnum, JSONB
from sqlalchemy import Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

# Các kiểu ENUM đã được tạo bởi SVWS_schema.sql -> create_type=False để ORM không tạo lại
muc_quyen_t = PGEnum("KHONG", "XEM", "THAO_TAC", "DUYET", "QUAN_TRI", name="muc_quyen", create_type=False)
loai_hang_t = PGEnum("SAN_PHAM", "VAT_TU", "THIET_BI", "HOA_CHAT", name="loai_hang", create_type=False)
loai_phieu_kho_t = PGEnum("NHAP", "XUAT", name="loai_phieu_kho", create_type=False)


# ---------- Nền tảng: người dùng & phân quyền ----------
class VaiTro(Base):
    __tablename__ = "vai_tro"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ma: Mapped[str] = mapped_column(String(20), unique=True)
    ten: Mapped[str] = mapped_column(String(120))


class NguoiDung(Base):
    __tablename__ = "nguoi_dung"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    vai_tro_id: Mapped[int] = mapped_column(ForeignKey("vai_tro.id"))
    phong_ban_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    email: Mapped[str] = mapped_column(String(150), unique=True)
    mat_khau_hash: Mapped[str] = mapped_column(String(255))
    trang_thai: Mapped[str] = mapped_column(String(20), default="HOAT_DONG")
    vai_tro: Mapped[VaiTro] = relationship(lazy="joined")


class PhanQuyen(Base):
    __tablename__ = "phan_quyen"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    vai_tro_id: Mapped[int] = mapped_column(ForeignKey("vai_tro.id"))
    module: Mapped[str] = mapped_column(String(40))
    muc: Mapped[str] = mapped_column(muc_quyen_t, default="KHONG")


class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    nguoi_dung_id: Mapped[int | None] = mapped_column(ForeignKey("nguoi_dung.id"), nullable=True)
    hanh_dong: Mapped[str] = mapped_column(String(20))
    bang: Mapped[str] = mapped_column(String(60))
    ban_ghi_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    gia_tri_cu: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    gia_tri_moi: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    thoi_gian: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class NhanVien(Base):
    __tablename__ = "nhan_vien"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    nguoi_dung_id: Mapped[int | None] = mapped_column(ForeignKey("nguoi_dung.id"), nullable=True)
    phong_ban_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    ma: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ho_ten: Mapped[str] = mapped_column(String(120))
    chuc_danh: Mapped[str | None] = mapped_column(String(120), nullable=True)
    luong_co_ban: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    luong_dong_bh: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    so_phu_thuoc: Mapped[int] = mapped_column(Integer, default=0)
    phu_cap_an: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    phu_cap_di_lai: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    phu_cap_dien_thoai: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    phu_cap_trach_nhiem: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    ma_so_thue: Mapped[str | None] = mapped_column(String(20), nullable=True)
    so_tai_khoan: Mapped[str | None] = mapped_column(String(30), nullable=True)
    ngan_hang: Mapped[str | None] = mapped_column(String(80), nullable=True)
    email: Mapped[str | None] = mapped_column(String(120), nullable=True)
    tk_chi_phi: Mapped[str] = mapped_column(String(10), default="642")
    trang_thai: Mapped[str] = mapped_column(String(20), default="DANG_LAM")


# ---------- Module Kho ----------
class HangHoa(Base):
    __tablename__ = "hang_hoa"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ma: Mapped[str | None] = mapped_column(String(40), unique=True, nullable=True)
    ten: Mapped[str] = mapped_column(String(200))
    loai: Mapped[str] = mapped_column(loai_hang_t)
    don_vi: Mapped[str | None] = mapped_column(String(20), nullable=True)
    gia_ban: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    ton: Mapped["TonKho"] = relationship(back_populates="hang_hoa", uselist=False, lazy="joined")


class TonKho(Base):
    __tablename__ = "ton_kho"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    hang_hoa_id: Mapped[int] = mapped_column(ForeignKey("hang_hoa.id"), unique=True)
    so_luong: Mapped[Decimal] = mapped_column(Numeric(15, 3), default=0)
    ton_min: Mapped[Decimal] = mapped_column(Numeric(15, 3), default=0)
    ton_max: Mapped[Decimal | None] = mapped_column(Numeric(15, 3), nullable=True)
    hang_hoa: Mapped[HangHoa] = relationship(back_populates="ton")


class PhieuKho(Base):
    __tablename__ = "phieu_kho"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    so: Mapped[str | None] = mapped_column(String(30), unique=True, nullable=True)
    loai: Mapped[str] = mapped_column(loai_phieu_kho_t)
    don_hang_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    don_mua_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    ngay: Mapped[date] = mapped_column(Date, server_default=func.current_date())
    nguoi_tao: Mapped[int | None] = mapped_column(ForeignKey("nhan_vien.id"), nullable=True)
    chi_tiet: Mapped[list["PhieuKhoCt"]] = relationship(cascade="all, delete-orphan", lazy="selectin")


class PhieuKhoCt(Base):
    __tablename__ = "phieu_kho_ct"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    phieu_kho_id: Mapped[int] = mapped_column(ForeignKey("phieu_kho.id", ondelete="CASCADE"))
    hang_hoa_id: Mapped[int] = mapped_column(ForeignKey("hang_hoa.id"))
    so_luong: Mapped[Decimal] = mapped_column(Numeric(15, 3))


class YeuCauMua(Base):
    __tablename__ = "yeu_cau_mua"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    hang_hoa_id: Mapped[int] = mapped_column(ForeignKey("hang_hoa.id"))
    so_luong: Mapped[Decimal] = mapped_column(Numeric(15, 3))
    ly_do: Mapped[str | None] = mapped_column(String(200), nullable=True)
    nguoi_tao: Mapped[int | None] = mapped_column(ForeignKey("nhan_vien.id"), nullable=True)
    ngay: Mapped[date] = mapped_column(Date, server_default=func.current_date())
    trang_thai: Mapped[str] = mapped_column(String(12), default="MOI")
    nha_cung_cap_id: Mapped[int | None] = mapped_column(ForeignKey("nha_cung_cap.id"), nullable=True)
    don_hang_id: Mapped[int | None] = mapped_column(ForeignKey("don_hang.id", ondelete="SET NULL"), nullable=True)
    don_gia: Mapped[Decimal | None] = mapped_column(Numeric(18, 0), nullable=True)
    ngay_can: Mapped[date | None] = mapped_column(Date, nullable=True)
    nguoi_duyet: Mapped[int | None] = mapped_column(ForeignKey("nhan_vien.id"), nullable=True)
    don_mua_id: Mapped[int | None] = mapped_column(ForeignKey("don_mua.id", ondelete="SET NULL"), nullable=True)
    ghi_chu: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_ncc_id: Mapped[int | None] = mapped_column(ForeignKey("nha_cung_cap.id"), nullable=True)
    ai_goi_y: Mapped[str | None] = mapped_column(Text, nullable=True)
    dinh_kem_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    dinh_kem_file: Mapped[str | None] = mapped_column(Text, nullable=True)
    cho_thue_ma: Mapped[str | None] = mapped_column(String(40), nullable=True)


class YeuCauMuaCt(Base):
    __tablename__ = "yeu_cau_mua_ct"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    yeu_cau_mua_id: Mapped[int] = mapped_column(ForeignKey("yeu_cau_mua.id", ondelete="CASCADE"))
    hang_hoa_id: Mapped[int] = mapped_column(ForeignKey("hang_hoa.id"))
    so_luong: Mapped[Decimal] = mapped_column(Numeric(15, 3), default=0)
    don_gia: Mapped[Decimal | None] = mapped_column(Numeric(18, 0), nullable=True)
    ghi_chu: Mapped[str | None] = mapped_column(Text, nullable=True)
    nha_cung_cap_id: Mapped[int | None] = mapped_column(ForeignKey("nha_cung_cap.id"), nullable=True)


# ---------- Phê duyệt theo hạn mức ----------
trang_thai_duyet_t = PGEnum("NHAP", "CHO_DUYET", "DA_DUYET", "TU_CHOI", name="trang_thai_duyet", create_type=False)


class HanMucDuyet(Base):
    __tablename__ = "han_muc_duyet"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    loai: Mapped[str] = mapped_column(String(40))
    vai_tro_id: Mapped[int] = mapped_column(ForeignKey("vai_tro.id"))
    nguong_tu: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    nguong_den: Mapped[Decimal | None] = mapped_column(Numeric(18, 0), nullable=True)


# ---------- Module Nhà cung cấp & Mua hàng ----------
class NhaCungCap(Base):
    __tablename__ = "nha_cung_cap"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ma: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    ten: Mapped[str] = mapped_column(String(200))
    ma_so_thue: Mapped[str | None] = mapped_column(String(20), nullable=True)
    dien_thoai: Mapped[str | None] = mapped_column(String(30), nullable=True)
    diem_danh_gia: Mapped[Decimal] = mapped_column(Numeric(3, 1), default=0)
    blacklist: Mapped[bool] = mapped_column(default=False)
    email: Mapped[str | None] = mapped_column(String(120), nullable=True)
    nguoi_phu_trach: Mapped[int | None] = mapped_column(ForeignKey("nhan_vien.id"), nullable=True)
    han_muc_cong_no: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    dia_chi: Mapped[str | None] = mapped_column(String(300), nullable=True)
    ghi_chu: Mapped[str | None] = mapped_column(Text, nullable=True)


class DonMua(Base):
    __tablename__ = "don_mua"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    so: Mapped[str | None] = mapped_column(String(30), unique=True, nullable=True)
    nha_cung_cap_id: Mapped[int] = mapped_column(ForeignKey("nha_cung_cap.id"))
    ngay: Mapped[date] = mapped_column(Date, server_default=func.current_date())
    tong_tien: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    trang_thai: Mapped[str] = mapped_column(trang_thai_duyet_t, default="NHAP")
    nguoi_duyet: Mapped[int | None] = mapped_column(ForeignKey("nhan_vien.id"), nullable=True)
    don_hang_id: Mapped[int | None] = mapped_column(ForeignKey("don_hang.id", ondelete="SET NULL"), nullable=True)
    ngay_hen_giao: Mapped[date | None] = mapped_column(Date, nullable=True)
    ngay_giao_thuc: Mapped[date | None] = mapped_column(Date, nullable=True)
    trang_thai_nhan: Mapped[str] = mapped_column(String(12), default="CHUA")
    chi_tiet: Mapped[list["DonMuaCt"]] = relationship(cascade="all, delete-orphan", lazy="selectin")


class Rfq(Base):
    __tablename__ = "rfq"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    hang_hoa_id: Mapped[int] = mapped_column(ForeignKey("hang_hoa.id"))
    so_luong: Mapped[Decimal] = mapped_column(Numeric(15, 3), default=0)
    han_bao_gia: Mapped[date | None] = mapped_column(Date, nullable=True)
    yeu_cau_mua_id: Mapped[int | None] = mapped_column(ForeignKey("yeu_cau_mua.id", ondelete="SET NULL"), nullable=True)
    noi_dung: Mapped[str | None] = mapped_column(Text, nullable=True)
    gui_tu: Mapped[str | None] = mapped_column(String(120), nullable=True)
    nguoi_tao: Mapped[int | None] = mapped_column(ForeignKey("nhan_vien.id"), nullable=True)
    ngay: Mapped[date] = mapped_column(Date, server_default=func.current_date())


class RfqLog(Base):
    __tablename__ = "rfq_log"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    rfq_id: Mapped[int] = mapped_column(ForeignKey("rfq.id", ondelete="CASCADE"))
    nha_cung_cap_id: Mapped[int] = mapped_column(ForeignKey("nha_cung_cap.id"))
    email: Mapped[str | None] = mapped_column(String(160), nullable=True)
    da_gui: Mapped[bool] = mapped_column(default=False)
    ket_qua: Mapped[str | None] = mapped_column(Text, nullable=True)
    ngay: Mapped[date] = mapped_column(Date, server_default=func.current_date())


class BaoGiaNcc(Base):
    __tablename__ = "bao_gia_ncc"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    nha_cung_cap_id: Mapped[int] = mapped_column(ForeignKey("nha_cung_cap.id"))
    hang_hoa_id: Mapped[int] = mapped_column(ForeignKey("hang_hoa.id"))
    don_gia: Mapped[Decimal] = mapped_column(Numeric(18, 0))
    so_luong_toi_thieu: Mapped[Decimal] = mapped_column(Numeric(15, 3), default=0)
    hieu_luc_den: Mapped[date | None] = mapped_column(Date, nullable=True)
    ngay: Mapped[date] = mapped_column(Date, server_default=func.current_date())
    nguon: Mapped[str] = mapped_column(String(12), default="THU_CONG")
    dieu_kien: Mapped[str | None] = mapped_column(Text, nullable=True)
    ghi_chu: Mapped[str | None] = mapped_column(Text, nullable=True)
    nguoi_tao: Mapped[int | None] = mapped_column(ForeignKey("nhan_vien.id"), nullable=True)


class DonMuaCt(Base):
    __tablename__ = "don_mua_ct"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    don_mua_id: Mapped[int] = mapped_column(ForeignKey("don_mua.id", ondelete="CASCADE"))
    hang_hoa_id: Mapped[int] = mapped_column(ForeignKey("hang_hoa.id"))
    so_luong: Mapped[Decimal] = mapped_column(Numeric(15, 3))
    don_gia: Mapped[Decimal] = mapped_column(Numeric(18, 0))
    so_luong_nhan: Mapped[Decimal] = mapped_column(Numeric(15, 3), default=0)


class DanhGiaNcc(Base):
    __tablename__ = "danh_gia_ncc"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    nha_cung_cap_id: Mapped[int] = mapped_column(ForeignKey("nha_cung_cap.id"))
    don_mua_id: Mapped[int | None] = mapped_column(ForeignKey("don_mua.id"), nullable=True)
    diem: Mapped[Decimal] = mapped_column(Numeric(3, 1))
    ngay: Mapped[date] = mapped_column(Date, server_default=func.current_date())


# ---------- Module Dự án ----------
trang_thai_du_an_t = PGEnum("MOI", "DANG_CHAY", "NGHIEM_THU", "HOAN_THANH", "TAM_DUNG",
                            name="trang_thai_du_an", create_type=False)


class DuAn(Base):
    __tablename__ = "du_an"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ma: Mapped[str | None] = mapped_column(String(30), unique=True, nullable=True)
    ten: Mapped[str] = mapped_column(String(200))
    khach_hang_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    truong_du_an: Mapped[int | None] = mapped_column(ForeignKey("nhan_vien.id"), nullable=True)
    du_toan: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    chi_phi_thuc_te: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    qcvn: Mapped[str | None] = mapped_column(String(40), nullable=True)
    trang_thai: Mapped[str] = mapped_column(trang_thai_du_an_t, default="MOI")
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    chu_dau_tu: Mapped[str | None] = mapped_column(String(200), nullable=True)
    dia_diem: Mapped[str | None] = mapped_column(String(255), nullable=True)
    loai_du_an: Mapped[str | None] = mapped_column(String(40), nullable=True)
    cong_suat: Mapped[str | None] = mapped_column(String(80), nullable=True)
    gia_tri_hop_dong: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    ngay_bat_dau: Mapped[date | None] = mapped_column(Date, nullable=True)
    ngay_kt_ke_hoach: Mapped[date | None] = mapped_column(Date, nullable=True)
    ngay_kt_thuc_te: Mapped[date | None] = mapped_column(Date, nullable=True)
    mo_ta: Mapped[str | None] = mapped_column(Text, nullable=True)
    tien_do: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    tieu_chuan_dau_ra: Mapped[str | None] = mapped_column(String(160), nullable=True)


class DuToanCt(Base):
    __tablename__ = "du_toan_ct"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    du_an_id: Mapped[int] = mapped_column(ForeignKey("du_an.id", ondelete="CASCADE"))
    hang_muc: Mapped[str | None] = mapped_column(String(60), nullable=True)
    mo_ta: Mapped[str | None] = mapped_column(String(200), nullable=True)
    so_luong: Mapped[Decimal] = mapped_column(Numeric(15, 3), default=1)
    don_gia: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    thanh_tien: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    nguon: Mapped[str | None] = mapped_column(String(40), default="FORECAST_CAL")


class DuAnChiPhi(Base):
    __tablename__ = "du_an_chi_phi"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    du_an_id: Mapped[int] = mapped_column(ForeignKey("du_an.id", ondelete="CASCADE"))
    hang_muc: Mapped[str | None] = mapped_column(String(60), nullable=True)
    mo_ta: Mapped[str | None] = mapped_column(String(200), nullable=True)
    so_tien: Mapped[Decimal] = mapped_column(Numeric(18, 0))
    trang_thai: Mapped[str] = mapped_column(trang_thai_duyet_t, default="CHO_DUYET")
    ngay: Mapped[date] = mapped_column(Date, server_default=func.current_date())


class NghiemThu(Base):
    __tablename__ = "nghiem_thu"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    du_an_id: Mapped[int] = mapped_column(ForeignKey("du_an.id"))
    ngay: Mapped[date] = mapped_column(Date, server_default=func.current_date())
    ket_qua_qcvn: Mapped[str | None] = mapped_column(String(40), nullable=True)
    khach_ky: Mapped[bool] = mapped_column(default=False)


# ---------- Module Bán hàng / Khách hàng / Hóa đơn ----------
loai_hoa_don_t = PGEnum("BAN", "MUA", "THUE", "DU_AN", name="loai_hoa_don", create_type=False)
loai_cong_no_t = PGEnum("PHAI_THU", "PHAI_TRA", name="loai_cong_no", create_type=False)


class KhachHang(Base):
    __tablename__ = "khach_hang"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ma: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    ten: Mapped[str] = mapped_column(String(200))
    ma_so_thue: Mapped[str | None] = mapped_column(String(20), nullable=True)
    dien_thoai: Mapped[str | None] = mapped_column(String(30), nullable=True)
    phan_loai_abc: Mapped[str | None] = mapped_column(String(1), nullable=True)
    email: Mapped[str | None] = mapped_column(String(120), nullable=True)
    khong_nhan_email: Mapped[bool] = mapped_column(Boolean, default=False)
    nguoi_phu_trach: Mapped[int | None] = mapped_column(ForeignKey("nhan_vien.id"), nullable=True)


class BaoGia(Base):
    __tablename__ = "bao_gia"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    so: Mapped[str | None] = mapped_column(String(30), unique=True, nullable=True)
    khach_hang_id: Mapped[int] = mapped_column(ForeignKey("khach_hang.id"))
    nguoi_tao: Mapped[int | None] = mapped_column(ForeignKey("nhan_vien.id"), nullable=True)
    ngay: Mapped[date] = mapped_column(Date, server_default=func.current_date())
    tong_tien: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    trang_thai: Mapped[str] = mapped_column(trang_thai_duyet_t, default="NHAP")
    nguoi_duyet: Mapped[int | None] = mapped_column(ForeignKey("nhan_vien.id"), nullable=True)
    chi_tiet: Mapped[list["BaoGiaCt"]] = relationship(cascade="all, delete-orphan", lazy="selectin")


class BaoGiaCt(Base):
    __tablename__ = "bao_gia_ct"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    bao_gia_id: Mapped[int] = mapped_column(ForeignKey("bao_gia.id", ondelete="CASCADE"))
    hang_hoa_id: Mapped[int] = mapped_column(ForeignKey("hang_hoa.id"))
    so_luong: Mapped[Decimal] = mapped_column(Numeric(15, 3))
    don_gia: Mapped[Decimal] = mapped_column(Numeric(18, 0))


class DonHang(Base):
    __tablename__ = "don_hang"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    so: Mapped[str | None] = mapped_column(String(30), unique=True, nullable=True)
    khach_hang_id: Mapped[int] = mapped_column(ForeignKey("khach_hang.id"))
    bao_gia_id: Mapped[int | None] = mapped_column(ForeignKey("bao_gia.id"), nullable=True)
    ngay: Mapped[date] = mapped_column(Date, server_default=func.current_date())
    tong_tien: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    trang_thai: Mapped[str] = mapped_column(String(20), default="MOI")
    ty_le_dat_coc: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    chi_tiet: Mapped[list["DonHangCt"]] = relationship(cascade="all, delete-orphan", lazy="selectin")


class DonHangCt(Base):
    __tablename__ = "don_hang_ct"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    don_hang_id: Mapped[int] = mapped_column(ForeignKey("don_hang.id", ondelete="CASCADE"))
    hang_hoa_id: Mapped[int] = mapped_column(ForeignKey("hang_hoa.id"))
    so_luong: Mapped[Decimal] = mapped_column(Numeric(15, 3))
    don_gia: Mapped[Decimal] = mapped_column(Numeric(18, 0))


class HoaDon(Base):
    __tablename__ = "hoa_don"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    loai: Mapped[str] = mapped_column(loai_hoa_don_t)
    don_hang_id: Mapped[int | None] = mapped_column(ForeignKey("don_hang.id"), nullable=True)
    hop_dong_thue_id: Mapped[int | None] = mapped_column(ForeignKey("hop_dong_thue.id"), nullable=True)
    ngay: Mapped[date] = mapped_column(Date, server_default=func.current_date())
    tien_truoc_thue: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    tien_thue: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    tong_tien: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    hddt_provider: Mapped[str | None] = mapped_column(String(40), nullable=True)
    hddt_ma_tra_cuu: Mapped[str | None] = mapped_column(String(60), nullable=True)
    hddt_trang_thai: Mapped[str | None] = mapped_column(String(20), nullable=True)
    so: Mapped[str | None] = mapped_column(String(40), nullable=True)
    khach_hang_id: Mapped[int | None] = mapped_column(ForeignKey("khach_hang.id"), nullable=True)
    nha_cung_cap_id: Mapped[int | None] = mapped_column(ForeignKey("nha_cung_cap.id"), nullable=True)
    tk_chi_phi: Mapped[str | None] = mapped_column(String(20), nullable=True)
    dien_giai: Mapped[str | None] = mapped_column(String(200), nullable=True)
    da_hach_toan: Mapped[bool] = mapped_column(Boolean, default=False)
    trang_thai: Mapped[str] = mapped_column(String(20), default="GHI_NHAN")


class CongNo(Base):
    __tablename__ = "cong_no"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    loai: Mapped[str] = mapped_column(loai_cong_no_t)
    hoa_don_id: Mapped[int | None] = mapped_column(ForeignKey("hoa_don.id"), nullable=True)
    khach_hang_id: Mapped[int | None] = mapped_column(ForeignKey("khach_hang.id"), nullable=True)
    nha_cung_cap_id: Mapped[int | None] = mapped_column(ForeignKey("nha_cung_cap.id"), nullable=True)
    so_tien: Mapped[Decimal] = mapped_column(Numeric(18, 0))
    da_thanh_toan: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    han: Mapped[date | None] = mapped_column(Date, nullable=True)
    trang_thai: Mapped[str] = mapped_column(String(20), default="CHUA_THU")


# ---------- Module Kế toán: thanh toán & sổ cái ----------
class ThanhToan(Base):
    __tablename__ = "thanh_toan"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    cong_no_id: Mapped[int] = mapped_column(ForeignKey("cong_no.id"))
    so_tien: Mapped[Decimal] = mapped_column(Numeric(18, 0))
    ngay: Mapped[date] = mapped_column(Date, server_default=func.current_date())
    hinh_thuc: Mapped[str | None] = mapped_column(String(30), nullable=True)


class ButToan(Base):
    __tablename__ = "but_toan"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ngay: Mapped[date] = mapped_column(Date, server_default=func.current_date())
    tk_no: Mapped[str] = mapped_column(String(20))
    tk_co: Mapped[str] = mapped_column(String(20))
    so_tien: Mapped[Decimal] = mapped_column(Numeric(18, 0))
    dien_giai: Mapped[str | None] = mapped_column(String(200), nullable=True)
    hoa_don_id: Mapped[int | None] = mapped_column(ForeignKey("hoa_don.id"), nullable=True)
    don_hang_id: Mapped[int | None] = mapped_column(ForeignKey("don_hang.id"), nullable=True)
    quy_id: Mapped[int | None] = mapped_column(ForeignKey("tai_khoan_quy.id"), nullable=True)
    nguon: Mapped[str | None] = mapped_column(String(20), nullable=True)
    nguon_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)


class TaiKhoanQuy(Base):
    __tablename__ = "tai_khoan_quy"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ma: Mapped[str] = mapped_column(String(20), unique=True)
    ten: Mapped[str] = mapped_column(String(120))
    loai: Mapped[str] = mapped_column(String(12), default="TIEN_MAT")
    so_tk: Mapped[str | None] = mapped_column(String(40), nullable=True)
    tk_ke_toan: Mapped[str] = mapped_column(String(20), default="111")
    so_du_dau: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    so_du: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    hoat_dong: Mapped[bool] = mapped_column(Boolean, default=True)


class PhieuThuChi(Base):
    __tablename__ = "phieu_thu_chi"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    so: Mapped[str | None] = mapped_column(String(30), unique=True, nullable=True)
    loai: Mapped[str] = mapped_column(String(4))                 # THU | CHI
    ngay: Mapped[date] = mapped_column(Date, server_default=func.current_date())
    quy_id: Mapped[int] = mapped_column(ForeignKey("tai_khoan_quy.id"))
    doi_tac_loai: Mapped[str | None] = mapped_column(String(8), nullable=True)
    khach_hang_id: Mapped[int | None] = mapped_column(ForeignKey("khach_hang.id"), nullable=True)
    nha_cung_cap_id: Mapped[int | None] = mapped_column(ForeignKey("nha_cung_cap.id"), nullable=True)
    so_tien: Mapped[Decimal] = mapped_column(Numeric(18, 0))
    dien_giai: Mapped[str | None] = mapped_column(String(200), nullable=True)
    don_hang_id: Mapped[int | None] = mapped_column(ForeignKey("don_hang.id"), nullable=True)
    cong_no_id: Mapped[int | None] = mapped_column(ForeignKey("cong_no.id"), nullable=True)
    tk_doi_ung: Mapped[str | None] = mapped_column(String(20), nullable=True)
    trang_thai: Mapped[str] = mapped_column(String(12), default="NHAP")
    nguoi_tao: Mapped[int | None] = mapped_column(ForeignKey("nhan_vien.id"), nullable=True)
    nguoi_duyet: Mapped[int | None] = mapped_column(ForeignKey("nhan_vien.id"), nullable=True)
    ngay_duyet: Mapped[date | None] = mapped_column(Date, nullable=True)
    but_toan_id: Mapped[int | None] = mapped_column(ForeignKey("but_toan.id"), nullable=True)
    ghi_chu: Mapped[str | None] = mapped_column(Text, nullable=True)
    la_tam_ung: Mapped[bool] = mapped_column(Boolean, default=False)
    da_can_tru: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)


# ---------- Module Nhân sự / Lương ----------
class ChamCong(Base):
    __tablename__ = "cham_cong"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    nhan_vien_id: Mapped[int] = mapped_column(ForeignKey("nhan_vien.id"))
    ngay: Mapped[date] = mapped_column(Date)
    gio_vao: Mapped[time | None] = mapped_column(Time, nullable=True)
    gio_ra: Mapped[time | None] = mapped_column(Time, nullable=True)


class NghiPhep(Base):
    __tablename__ = "nghi_phep"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    nhan_vien_id: Mapped[int] = mapped_column(ForeignKey("nhan_vien.id"))
    tu_ngay: Mapped[date] = mapped_column(Date)
    den_ngay: Mapped[date] = mapped_column(Date)
    loai: Mapped[str | None] = mapped_column(String(20), nullable=True)
    trang_thai: Mapped[str] = mapped_column(trang_thai_duyet_t, default="CHO_DUYET")
    nguoi_duyet: Mapped[int | None] = mapped_column(ForeignKey("nhan_vien.id"), nullable=True)


class BangLuong(Base):
    __tablename__ = "bang_luong"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    nhan_vien_id: Mapped[int] = mapped_column(ForeignKey("nhan_vien.id"))
    thang: Mapped[str] = mapped_column(String(7))  # 'YYYY-MM'
    luong_co_ban: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    phu_cap: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    ot: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    bhxh: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    bhyt: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    bhtn: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    thue_tncn: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    khau_tru: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    thuc_linh: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    trang_thai: Mapped[str] = mapped_column(trang_thai_duyet_t, default="CHO_DUYET")
    nguoi_duyet_ktt: Mapped[int | None] = mapped_column(ForeignKey("nhan_vien.id"), nullable=True)
    nguoi_ky_ceo: Mapped[int | None] = mapped_column(ForeignKey("nhan_vien.id"), nullable=True)
    cong_chuan: Mapped[Decimal] = mapped_column(Numeric(5, 1), default=26)
    cong_thuc_te: Mapped[Decimal] = mapped_column(Numeric(5, 1), default=26)
    gio_ot_thuong: Mapped[Decimal] = mapped_column(Numeric(6, 1), default=0)
    gio_ot_cuoi_tuan: Mapped[Decimal] = mapped_column(Numeric(6, 1), default=0)
    gio_ot_le: Mapped[Decimal] = mapped_column(Numeric(6, 1), default=0)
    luong_thuc_te: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    tam_ung: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    thu_nhap_chiu_thue: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    bhxh_dn: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    bhyt_dn: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    bhtn_dn: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    chi_phi_dn: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    email_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    ngay_gui_email: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    phu_cap_khac: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    ngay_nghi_kpep: Mapped[Decimal] = mapped_column(Numeric(4, 1), default=0)
    so_phut_di_tre: Mapped[int] = mapped_column(Integer, default=0)
    khau_tru_nghi: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    khau_tru_tre: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    khau_tru_khac: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    thuong_kpi: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)


class CfgThuongKpi(Base):
    __tablename__ = "cfg_thuong_kpi"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    muc_co_so: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=2000000)
    hs_a: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("1.5"))
    hs_b: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("1.0"))
    hs_c: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.5"))
    hs_d: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.0"))


class KyLuong(Base):
    __tablename__ = "ky_luong"
    thang: Mapped[str] = mapped_column(String(7), primary_key=True)
    cong_chuan: Mapped[Decimal] = mapped_column(Numeric(5, 1), default=26)
    ngay_chot: Mapped[date | None] = mapped_column(Date, nullable=True)
    trang_thai: Mapped[str] = mapped_column(String(20), default="NHAP")
    da_gui_email: Mapped[bool] = mapped_column(Boolean, default=False)
    tong_thu_nhap: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    tong_thuc_linh: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    tong_chi_phi_dn: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    nguoi_chot: Mapped[int | None] = mapped_column(BigInteger, nullable=True)


# ---------- Module Dịch vụ cho thuê ----------
doi_tuong_thue_t = PGEnum("NHAN_SU", "HOA_CHAT", "VAT_TU", "THIET_BI",
                          name="doi_tuong_thue", create_type=False)


class HopDongThue(Base):
    __tablename__ = "hop_dong_thue"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    so: Mapped[str | None] = mapped_column(String(30), unique=True, nullable=True)
    khach_hang_id: Mapped[int] = mapped_column(ForeignKey("khach_hang.id"))
    doi_tuong: Mapped[str] = mapped_column(doi_tuong_thue_t)
    gia_thue: Mapped[Decimal] = mapped_column(Numeric(18, 0))
    chu_ky: Mapped[str | None] = mapped_column(String(20), nullable=True)  # THANG / QUY
    ngay_bat_dau: Mapped[date] = mapped_column(Date)
    ngay_ket_thuc: Mapped[date] = mapped_column(Date)
    trang_thai: Mapped[str] = mapped_column(String(20), default="HIEU_LUC")
    tai_san: Mapped[list["TaiSanThue"]] = relationship(cascade="all, delete-orphan", lazy="selectin")


class TaiSanThue(Base):
    __tablename__ = "tai_san_thue"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    hop_dong_thue_id: Mapped[int] = mapped_column(ForeignKey("hop_dong_thue.id", ondelete="CASCADE"))
    hang_hoa_id: Mapped[int | None] = mapped_column(ForeignKey("hang_hoa.id"), nullable=True)
    nhan_vien_id: Mapped[int | None] = mapped_column(ForeignKey("nhan_vien.id"), nullable=True)
    so_luong: Mapped[Decimal] = mapped_column(Numeric(15, 3), default=1)
    ngay_tra: Mapped[date | None] = mapped_column(Date, nullable=True)


# ---------- Module CRM ----------
class ChamSocKH(Base):
    __tablename__ = "cham_soc_kh"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    khach_hang_id: Mapped[int] = mapped_column(ForeignKey("khach_hang.id", ondelete="CASCADE"))
    loai: Mapped[str] = mapped_column(String(20))
    noi_dung: Mapped[str | None] = mapped_column(String(300), nullable=True)
    ngay_hen: Mapped[date | None] = mapped_column(Date, nullable=True)
    ngay_thuc_hien: Mapped[date | None] = mapped_column(Date, nullable=True)
    trang_thai: Mapped[str] = mapped_column(String(20), default="CHO")
    csat: Mapped[Decimal | None] = mapped_column(Numeric(2, 1), nullable=True)
    nguoi_phu_trach: Mapped[int | None] = mapped_column(ForeignKey("nhan_vien.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ---------- Bán hàng mở rộng: tệp đính kèm + email chào hàng ----------
class TepDinhKem(Base):
    __tablename__ = "tep_dinh_kem"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    doi_tuong: Mapped[str] = mapped_column(String(20))
    doi_tuong_id: Mapped[int] = mapped_column(BigInteger)
    loai: Mapped[str] = mapped_column(String(20), default="KHAC")
    ten_file: Mapped[str] = mapped_column(String(255))
    duong_dan: Mapped[str] = mapped_column(String(500))
    kich_thuoc: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    nguoi_tai_len: Mapped[int | None] = mapped_column(ForeignKey("nhan_vien.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ChienDichEmail(Base):
    __tablename__ = "chien_dich_email"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ten: Mapped[str] = mapped_column(String(200))
    tieu_de: Mapped[str] = mapped_column(String(300))
    noi_dung: Mapped[str] = mapped_column(Text)
    bo_loc_abc: Mapped[str | None] = mapped_column(String(3), nullable=True)
    khach_hang_ids: Mapped[str | None] = mapped_column(Text, nullable=True)
    trang_thai: Mapped[str] = mapped_column(String(20), default="CHO_DUYET")
    nguoi_tao: Mapped[int | None] = mapped_column(ForeignKey("nhan_vien.id"), nullable=True)
    nguoi_duyet: Mapped[int | None] = mapped_column(ForeignKey("nhan_vien.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EmailLog(Base):
    __tablename__ = "email_log"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    chien_dich_id: Mapped[int] = mapped_column(ForeignKey("chien_dich_email.id", ondelete="CASCADE"))
    khach_hang_id: Mapped[int | None] = mapped_column(ForeignKey("khach_hang.id"), nullable=True)
    email: Mapped[str | None] = mapped_column(String(120), nullable=True)
    trang_thai: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ghi_chu: Mapped[str | None] = mapped_column(String(255), nullable=True)
    thoi_diem: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ---------- Nhật ký liên lạc khách hàng ----------
class LienLac(Base):
    __tablename__ = "lien_lac"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    khach_hang_id: Mapped[int | None] = mapped_column(ForeignKey("khach_hang.id", ondelete="CASCADE"), nullable=True)
    kenh: Mapped[str] = mapped_column(String(15), default="EMAIL")
    huong: Mapped[str] = mapped_column(String(5), default="DI")
    tieu_de: Mapped[str | None] = mapped_column(String(300), nullable=True)
    noi_dung: Mapped[str | None] = mapped_column(Text, nullable=True)
    lien_quan_loai: Mapped[str | None] = mapped_column(String(15), nullable=True)
    lien_quan_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    gui_tu: Mapped[str | None] = mapped_column(String(120), nullable=True)
    nguoi_xu_ly: Mapped[int | None] = mapped_column(ForeignKey("nhan_vien.id"), nullable=True)
    trang_thai: Mapped[str | None] = mapped_column(String(15), nullable=True)
    tu_email: Mapped[str | None] = mapped_column(String(120), nullable=True)
    message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    da_xu_ly: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_y_dinh: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ai_khan: Mapped[str | None] = mapped_column(String(10), nullable=True)
    ai_tom_tat: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_tra_loi: Mapped[str | None] = mapped_column(Text, nullable=True)
    thoi_diem: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())



class CongViec(Base):
    __tablename__ = "cong_viec"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    lien_lac_id: Mapped[int | None] = mapped_column(ForeignKey("lien_lac.id", ondelete="SET NULL"), nullable=True)
    khach_hang_id: Mapped[int | None] = mapped_column(ForeignKey("khach_hang.id", ondelete="CASCADE"), nullable=True)
    loai: Mapped[str | None] = mapped_column(String(20), nullable=True)
    tieu_de: Mapped[str] = mapped_column(String(300))
    mo_ta: Mapped[str | None] = mapped_column(Text, nullable=True)
    nguoi_phu_trach: Mapped[int | None] = mapped_column(ForeignKey("nhan_vien.id"), nullable=True)
    uu_tien: Mapped[str] = mapped_column(String(10), default="TRUNG")
    han_xu_ly: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    trang_thai: Mapped[str] = mapped_column(String(15), default="MO")
    hoan_thanh_luc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())



class CoHoi(Base):
    __tablename__ = "co_hoi"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    khach_hang_id: Mapped[int | None] = mapped_column(ForeignKey("khach_hang.id", ondelete="CASCADE"), nullable=True)
    lien_lac_id: Mapped[int | None] = mapped_column(ForeignKey("lien_lac.id", ondelete="SET NULL"), nullable=True)
    bao_gia_id: Mapped[int | None] = mapped_column(ForeignKey("bao_gia.id", ondelete="SET NULL"), nullable=True)
    don_hang_id: Mapped[int | None] = mapped_column(ForeignKey("don_hang.id", ondelete="SET NULL"), nullable=True)
    nguon: Mapped[str | None] = mapped_column(String(20), default="EMAIL")
    tieu_de: Mapped[str | None] = mapped_column(String(300), nullable=True)
    giai_doan: Mapped[str] = mapped_column(String(15), default="MOI")
    gia_tri_dk: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    nguoi_phu_trach: Mapped[int | None] = mapped_column(ForeignKey("nhan_vien.id"), nullable=True)
    ly_do_thua: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ThamSoTaiChinh(Base):
    __tablename__ = "tham_so_tai_chinh"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, default=1)
    von_chu_so_huu: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    tai_san_co_dinh: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    no_dai_han: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    chi_co_dinh_thang: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)


class KhoanVay(Base):
    __tablename__ = "khoan_vay"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    so: Mapped[str | None] = mapped_column(String(40), unique=True, nullable=True)
    ben_cho_vay: Mapped[str] = mapped_column(String(160))
    loai: Mapped[str] = mapped_column(String(12), default="NGAN_HAN")
    so_tien_goc: Mapped[Decimal] = mapped_column(Numeric(18, 0))
    lai_suat_nam: Mapped[Decimal] = mapped_column(Numeric(6, 3), default=0)
    phuong_thuc: Mapped[str] = mapped_column(String(16), default="GOC_DEU")
    ngay_nhan: Mapped[date] = mapped_column(Date)
    so_ky: Mapped[int] = mapped_column(Integer, default=12)
    chu_ky_thang: Mapped[int] = mapped_column(Integer, default=1)
    ngay_dao_han: Mapped[date | None] = mapped_column(Date, nullable=True)
    tk_tien: Mapped[str] = mapped_column(String(10), default="112")
    con_lai_goc: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    trang_thai: Mapped[str] = mapped_column(String(16), default="DANG_VAY")
    ghi_chu: Mapped[str | None] = mapped_column(Text, nullable=True)


class LichTraNo(Base):
    __tablename__ = "lich_tra_no"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    khoan_vay_id: Mapped[int] = mapped_column(ForeignKey("khoan_vay.id", ondelete="CASCADE"))
    ky: Mapped[int] = mapped_column(Integer)
    ngay_den_han: Mapped[date] = mapped_column(Date)
    du_no_dau: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    goc_phai_tra: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    lai_phai_tra: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    tong_phai_tra: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    du_no_cuoi: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    da_tra: Mapped[bool] = mapped_column(Boolean, default=False)
    ngay_tra: Mapped[date | None] = mapped_column(Date, nullable=True)


class ThamSoLuong(Base):
    __tablename__ = "tham_so_luong"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    tl_bhxh_nv: Mapped[Decimal] = mapped_column(Numeric(6, 4), default=Decimal("0.08"))
    tl_bhyt_nv: Mapped[Decimal] = mapped_column(Numeric(6, 4), default=Decimal("0.015"))
    tl_bhtn_nv: Mapped[Decimal] = mapped_column(Numeric(6, 4), default=Decimal("0.01"))
    tl_bhxh_dn: Mapped[Decimal] = mapped_column(Numeric(6, 4), default=Decimal("0.175"))
    tl_bhyt_dn: Mapped[Decimal] = mapped_column(Numeric(6, 4), default=Decimal("0.03"))
    tl_bhtn_dn: Mapped[Decimal] = mapped_column(Numeric(6, 4), default=Decimal("0.01"))
    tran_bhxh_bhyt: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=46800000)
    tran_bhtn: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=99200000)
    giam_tru_ban_than: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=11000000)
    giam_tru_phu_thuoc: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=4400000)
    mien_thue_an: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=730000)
    hs_ot_thuong: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=Decimal("1.5"))
    hs_ot_cuoi_tuan: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=Decimal("2.0"))
    hs_ot_le: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=Decimal("3.0"))
    luong_co_so: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=2340000)
    luong_toi_thieu_vung: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=4960000)
    bac_thue: Mapped[str] = mapped_column(Text, default="[]")


class QuyTrichLap(Base):
    __tablename__ = "quy_trich_lap"
    ma: Mapped[str] = mapped_column(String(20), primary_key=True)
    ten: Mapped[str] = mapped_column(String(160))
    ban_chat: Mapped[str] = mapped_column(String(12), default="TRUOC_THUE")
    tk_no: Mapped[str] = mapped_column(String(10))
    tk_co: Mapped[str] = mapped_column(String(10))
    gioi_han: Mapped[str] = mapped_column(String(20), default="NONE")
    so_du: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    hoat_dong: Mapped[bool] = mapped_column(Boolean, default=True)


class GiaoDichQuy(Base):
    __tablename__ = "giao_dich_quy"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ma_quy: Mapped[str] = mapped_column(ForeignKey("quy_trich_lap.ma"))
    loai: Mapped[str] = mapped_column(String(12))
    ky: Mapped[str] = mapped_column(String(7))
    ngay: Mapped[date] = mapped_column(Date, default=date.today)
    so_tien: Mapped[Decimal] = mapped_column(Numeric(18, 0))
    dien_giai: Mapped[str | None] = mapped_column(Text, nullable=True)
    but_toan_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    nguoi_tao: Mapped[int | None] = mapped_column(BigInteger, nullable=True)


class DuAnThietKe(Base):
    __tablename__ = "du_an_thiet_ke"
    du_an_id: Mapped[int] = mapped_column(ForeignKey("du_an.id", ondelete="CASCADE"), primary_key=True)
    cong_nghe: Mapped[str | None] = mapped_column(Text, nullable=True)
    cong_suat_tk: Mapped[str | None] = mapped_column(String(80), nullable=True)
    tieu_chuan: Mapped[str | None] = mapped_column(String(120), nullable=True)
    thong_so: Mapped[str | None] = mapped_column(Text, nullable=True)
    nguoi_thiet_ke: Mapped[str | None] = mapped_column(String(120), nullable=True)
    ngay_duyet: Mapped[date | None] = mapped_column(Date, nullable=True)
    phien_ban: Mapped[str | None] = mapped_column(String(20), default="v1.0")
    trang_thai: Mapped[str] = mapped_column(String(16), default="DU_THAO")
    ghi_chu: Mapped[str | None] = mapped_column(Text, nullable=True)


class DuAnMoc(Base):
    __tablename__ = "du_an_moc"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    du_an_id: Mapped[int] = mapped_column(ForeignKey("du_an.id", ondelete="CASCADE"))
    thu_tu: Mapped[int] = mapped_column(Integer, default=0)
    ten: Mapped[str] = mapped_column(String(200))
    giai_doan: Mapped[str | None] = mapped_column(String(40), nullable=True)
    ngay_bd_kh: Mapped[date | None] = mapped_column(Date, nullable=True)
    ngay_kt_kh: Mapped[date | None] = mapped_column(Date, nullable=True)
    ngay_kt_tt: Mapped[date | None] = mapped_column(Date, nullable=True)
    trong_so: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=1)
    phan_tram: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    trang_thai: Mapped[str] = mapped_column(String(16), default="CHUA_BAT_DAU")
    phu_trach: Mapped[str | None] = mapped_column(String(120), nullable=True)
    ghi_chu: Mapped[str | None] = mapped_column(Text, nullable=True)


class DuAnAnToan(Base):
    __tablename__ = "du_an_an_toan"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    du_an_id: Mapped[int] = mapped_column(ForeignKey("du_an.id", ondelete="CASCADE"))
    hang_muc: Mapped[str] = mapped_column(String(200))
    moi_nguy: Mapped[str | None] = mapped_column(Text, nullable=True)
    muc_rui_ro: Mapped[str] = mapped_column(String(10), default="TRUNG")
    bien_phap: Mapped[str | None] = mapped_column(Text, nullable=True)
    phu_trach: Mapped[str | None] = mapped_column(String(120), nullable=True)
    han: Mapped[date | None] = mapped_column(Date, nullable=True)
    trang_thai: Mapped[str] = mapped_column(String(16), default="MO")
    nguoi_danh_gia: Mapped[str | None] = mapped_column(String(120), nullable=True)
    ngay_danh_gia: Mapped[date | None] = mapped_column(Date, default=date.today)


class DuAnNhatKy(Base):
    __tablename__ = "du_an_nhat_ky"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    du_an_id: Mapped[int] = mapped_column(ForeignKey("du_an.id", ondelete="CASCADE"))
    ngay: Mapped[date] = mapped_column(Date, default=date.today)
    noi_dung: Mapped[str | None] = mapped_column(Text, nullable=True)
    nhan_luc: Mapped[str | None] = mapped_column(String(120), nullable=True)
    thiet_bi: Mapped[str | None] = mapped_column(String(200), nullable=True)
    thoi_tiet: Mapped[str | None] = mapped_column(String(60), nullable=True)
    van_de: Mapped[str | None] = mapped_column(Text, nullable=True)
    nguoi_ghi: Mapped[str | None] = mapped_column(String(120), nullable=True)


class DuAnTaiLieu(Base):
    __tablename__ = "du_an_tai_lieu"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    du_an_id: Mapped[int] = mapped_column(ForeignKey("du_an.id", ondelete="CASCADE"))
    loai: Mapped[str] = mapped_column(String(20), default="KHAC")
    ten: Mapped[str] = mapped_column(String(255))
    ma_so: Mapped[str | None] = mapped_column(String(60), nullable=True)
    phien_ban: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ngay: Mapped[date | None] = mapped_column(Date, default=date.today)
    duong_dan: Mapped[str | None] = mapped_column(Text, nullable=True)
    kich_thuoc: Mapped[int] = mapped_column(BigInteger, default=0)
    trang_thai: Mapped[str] = mapped_column(String(16), default="HIEU_LUC")
    nguoi_tao: Mapped[str | None] = mapped_column(String(120), nullable=True)
    ghi_chu: Mapped[str | None] = mapped_column(Text, nullable=True)


class DuAnKpi(Base):
    __tablename__ = "du_an_kpi"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    du_an_id: Mapped[int] = mapped_column(ForeignKey("du_an.id", ondelete="CASCADE"))
    ten: Mapped[str] = mapped_column(String(200))
    don_vi: Mapped[str | None] = mapped_column(String(40), nullable=True)
    chieu: Mapped[str] = mapped_column(String(8), default="CAO")
    muc_tieu: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    thuc_te: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    trong_so: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=1)
    ky: Mapped[str | None] = mapped_column(String(7), nullable=True)
    ghi_chu: Mapped[str | None] = mapped_column(Text, nullable=True)


class DuAnBaoCao(Base):
    __tablename__ = "du_an_bao_cao"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    du_an_id: Mapped[int] = mapped_column(ForeignKey("du_an.id", ondelete="CASCADE"))
    ky: Mapped[str | None] = mapped_column(String(20), nullable=True)
    tieu_de: Mapped[str | None] = mapped_column(String(200), nullable=True)
    tien_do: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    noi_dung: Mapped[str | None] = mapped_column(Text, nullable=True)
    van_de: Mapped[str | None] = mapped_column(Text, nullable=True)
    ngay: Mapped[date | None] = mapped_column(Date, default=date.today)
    nguoi_tao: Mapped[str | None] = mapped_column(String(120), nullable=True)


class DuAnChiTieu(Base):
    __tablename__ = "du_an_chi_tieu"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    du_an_id: Mapped[int] = mapped_column(ForeignKey("du_an.id", ondelete="CASCADE"))
    thu_tu: Mapped[int] = mapped_column(Integer, default=0)
    ten: Mapped[str] = mapped_column(String(120))
    don_vi: Mapped[str | None] = mapped_column(String(40), nullable=True)
    gia_tri_vao: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    gioi_han_ra: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    ghi_chu: Mapped[str | None] = mapped_column(String(200), nullable=True)


# ---------- Mô tả công việc (JD) & KPI theo vị trí + đánh giá theo kỳ ----------
class MoTaCongViec(Base):
    __tablename__ = "mo_ta_cong_viec"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    vai_tro: Mapped[str] = mapped_column(String(20), unique=True)
    chuc_danh: Mapped[str] = mapped_column(String(150))
    cap_bac: Mapped[str | None] = mapped_column(String(40), nullable=True)
    bao_cao_cho: Mapped[str | None] = mapped_column(String(40), nullable=True)
    muc_dich: Mapped[str | None] = mapped_column(Text, nullable=True)
    trach_nhiem: Mapped[str | None] = mapped_column(Text, nullable=True)
    quyen_han: Mapped[str | None] = mapped_column(Text, nullable=True)
    yeu_cau: Mapped[str | None] = mapped_column(Text, nullable=True)
    cap_nhat_luc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class KpiViTri(Base):
    __tablename__ = "kpi_vi_tri"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    vai_tro: Mapped[str] = mapped_column(String(20))
    ten: Mapped[str] = mapped_column(String(200))
    don_vi: Mapped[str | None] = mapped_column(String(30), nullable=True)
    trong_so: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    muc_tieu: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    chieu: Mapped[str] = mapped_column(String(8), default="CAO")
    chu_ky: Mapped[str] = mapped_column(String(8), default="THANG")
    mo_ta: Mapped[str | None] = mapped_column(String(300), nullable=True)
    thu_tu: Mapped[int] = mapped_column(Integer, default=0)


class DanhGiaKy(Base):
    __tablename__ = "danh_gia_ky"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    nhan_vien_id: Mapped[int] = mapped_column(ForeignKey("nhan_vien.id", ondelete="CASCADE"))
    vai_tro: Mapped[str | None] = mapped_column(String(20), nullable=True)
    loai_ky: Mapped[str] = mapped_column(String(8))
    ky: Mapped[str] = mapped_column(String(12))
    tong_diem: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)
    xep_loai: Mapped[str | None] = mapped_column(String(2), nullable=True)
    nhan_xet: Mapped[str | None] = mapped_column(Text, nullable=True)
    nguoi_danh_gia: Mapped[int | None] = mapped_column(ForeignKey("nhan_vien.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    chi_tiet: Mapped[list["DanhGiaCt"]] = relationship(cascade="all, delete-orphan", lazy="selectin")


class DanhGiaCt(Base):
    __tablename__ = "danh_gia_ct"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    danh_gia_id: Mapped[int] = mapped_column(ForeignKey("danh_gia_ky.id", ondelete="CASCADE"))
    kpi_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    ten: Mapped[str] = mapped_column(String(200))
    trong_so: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    muc_tieu: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    gia_tri_thuc: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    phan_tram_dat: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    diem: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)


# ---------- Cho thuê: tài sản · chi phí vận hành · bảo trì ----------
class TaiSanChoThue(Base):
    __tablename__ = "tai_san_cho_thue"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ma: Mapped[str] = mapped_column(String(40), unique=True)
    ten_du_an: Mapped[str | None] = mapped_column(String(120), nullable=True)
    ten: Mapped[str] = mapped_column(String(200))
    loai: Mapped[str] = mapped_column(String(20), default="THIET_BI")
    nguyen_gia: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    gia_thue_thang: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    khau_hao_thang: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    ngay_mua: Mapped[date | None] = mapped_column(Date, nullable=True)
    tinh_trang: Mapped[str] = mapped_column(String(16), default="SAN_SANG")
    khach_hang_id: Mapped[int | None] = mapped_column(ForeignKey("khach_hang.id"), nullable=True)
    vi_tri: Mapped[str | None] = mapped_column(String(120), nullable=True)
    ghi_chu: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ChiPhiVanHanh(Base):
    __tablename__ = "chi_phi_van_hanh"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    tai_san_id: Mapped[int | None] = mapped_column(ForeignKey("tai_san_cho_thue.id", ondelete="SET NULL"), nullable=True)
    ma_ban_hang: Mapped[str | None] = mapped_column(String(40), nullable=True)
    loai_chi_phi: Mapped[str] = mapped_column(String(16), default="VAT_TU")
    so_tien: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    ngay: Mapped[date] = mapped_column(Date, server_default=func.current_date())
    yeu_cau_mua_id: Mapped[int | None] = mapped_column(ForeignKey("yeu_cau_mua.id", ondelete="SET NULL"), nullable=True)
    mo_ta: Mapped[str | None] = mapped_column(String(300), nullable=True)
    nguon: Mapped[str] = mapped_column(String(16), default="THU_CONG")


class KeHoachBaoTri(Base):
    __tablename__ = "ke_hoach_bao_tri"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    tai_san_id: Mapped[int] = mapped_column(ForeignKey("tai_san_cho_thue.id", ondelete="CASCADE"))
    ten_cong_viec: Mapped[str] = mapped_column(String(200))
    chu_ky_ngay: Mapped[int] = mapped_column(Integer, default=90)
    ngay_ke_tiep: Mapped[date | None] = mapped_column(Date, nullable=True)
    lan_cuoi: Mapped[date | None] = mapped_column(Date, nullable=True)
    trang_thai: Mapped[str] = mapped_column(String(16), default="KE_HOACH")
    chi_phi_du_kien: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    ghi_chu: Mapped[str | None] = mapped_column(Text, nullable=True)


# ---------- Cho thuê: định mức & tiêu hao theo hệ thống/tháng ----------
class DinhMucTieuHao(Base):
    __tablename__ = "dinh_muc_tieu_hao"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    tai_san_id: Mapped[int] = mapped_column(ForeignKey("tai_san_cho_thue.id", ondelete="CASCADE"))
    hang_hoa_id: Mapped[int] = mapped_column(ForeignKey("hang_hoa.id"))
    dinh_muc_thang: Mapped[Decimal] = mapped_column(Numeric(15, 3), default=0)
    ghi_chu: Mapped[str | None] = mapped_column(String(200), nullable=True)


class TieuHaoThucTe(Base):
    __tablename__ = "tieu_hao_thuc_te"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    tai_san_id: Mapped[int] = mapped_column(ForeignKey("tai_san_cho_thue.id", ondelete="CASCADE"))
    hang_hoa_id: Mapped[int] = mapped_column(ForeignKey("hang_hoa.id"))
    thang: Mapped[str] = mapped_column(String(7))
    so_luong: Mapped[Decimal] = mapped_column(Numeric(15, 3), default=0)
    don_gia: Mapped[Decimal] = mapped_column(Numeric(18, 0), default=0)
    ngay_ghi: Mapped[date] = mapped_column(Date, server_default=func.current_date())
    nguon: Mapped[str] = mapped_column(String(16), default="THU_CONG")
    da_ghi_chi_phi: Mapped[bool] = mapped_column(Boolean, default=False)
    ghi_chu: Mapped[str | None] = mapped_column(String(200), nullable=True)
