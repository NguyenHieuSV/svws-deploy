-- ============================================================
-- SVWS — Mô hình dữ liệu hệ thống quản trị hợp nhất
-- PostgreSQL DDL · MỘT cơ sở dữ liệu duy nhất cho mọi module
-- Nguyên tắc: master data tồn tại một bản; mọi giao dịch FK về master.
-- ============================================================

-- ===== Kiểu liệt kê dùng chung =====
CREATE TYPE muc_quyen          AS ENUM ('KHONG','XEM','THAO_TAC','DUYET','QUAN_TRI');
CREATE TYPE trang_thai_duyet   AS ENUM ('NHAP','CHO_DUYET','DA_DUYET','TU_CHOI');
CREATE TYPE loai_hang          AS ENUM ('SAN_PHAM','VAT_TU','THIET_BI');
CREATE TYPE loai_hoa_don       AS ENUM ('BAN','MUA','THUE','DU_AN');
CREATE TYPE loai_phieu_kho     AS ENUM ('NHAP','XUAT');
CREATE TYPE loai_cong_no       AS ENUM ('PHAI_THU','PHAI_TRA');
CREATE TYPE doi_tuong_thue     AS ENUM ('NHAN_SU','HOA_CHAT','VAT_TU','THIET_BI');
CREATE TYPE trang_thai_du_an   AS ENUM ('MOI','DANG_CHAY','NGHIEM_THU','HOAN_THANH','TAM_DUNG');

-- ============================================================
-- 0. NỀN TẢNG: tổ chức, người dùng, phân quyền, audit
-- ============================================================
CREATE TABLE phong_ban (
    id          BIGSERIAL PRIMARY KEY,
    ten         VARCHAR(120) NOT NULL,
    truong_phong_id BIGINT,                          -- gán sau khi có nhan_vien
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE vai_tro (
    id          BIGSERIAL PRIMARY KEY,
    ma          VARCHAR(20)  NOT NULL UNIQUE,         -- CEO, TP_KD, NV_KD...
    ten         VARCHAR(120) NOT NULL
);

CREATE TABLE nguoi_dung (
    id          BIGSERIAL PRIMARY KEY,
    vai_tro_id  BIGINT NOT NULL REFERENCES vai_tro(id),
    phong_ban_id BIGINT REFERENCES phong_ban(id),
    email       VARCHAR(150) NOT NULL UNIQUE,
    mat_khau_hash VARCHAR(255) NOT NULL,
    trang_thai  VARCHAR(20) NOT NULL DEFAULT 'HOAT_DONG',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Ma trận RBAC dạng dữ liệu: (vai trò × module) -> mức truy cập
CREATE TABLE phan_quyen (
    id          BIGSERIAL PRIMARY KEY,
    vai_tro_id  BIGINT NOT NULL REFERENCES vai_tro(id) ON DELETE CASCADE,
    module      VARCHAR(40) NOT NULL,                 -- nhan_su, ban_hang, kho...
    muc         muc_quyen   NOT NULL DEFAULT 'KHONG',
    UNIQUE (vai_tro_id, module)
);

-- Hạn mức phê duyệt theo loại nghiệp vụ và vai trò (ngưỡng tiền là tham số)
CREATE TABLE han_muc_duyet (
    id          BIGSERIAL PRIMARY KEY,
    loai        VARCHAR(40) NOT NULL,                 -- po, chi_phi_du_an, bao_gia...
    vai_tro_id  BIGINT NOT NULL REFERENCES vai_tro(id),
    nguong_tu   NUMERIC(18,0) NOT NULL DEFAULT 0,     -- duyệt khi số tiền trong [tu, den]
    nguong_den  NUMERIC(18,0),                        -- NULL = không giới hạn trên
    UNIQUE (loai, vai_tro_id)
);

CREATE TABLE audit_log (
    id          BIGSERIAL PRIMARY KEY,
    nguoi_dung_id BIGINT REFERENCES nguoi_dung(id),
    hanh_dong   VARCHAR(20) NOT NULL,                 -- TAO, SUA, XOA, DUYET
    bang        VARCHAR(60) NOT NULL,
    ban_ghi_id  BIGINT,
    gia_tri_cu  JSONB,
    gia_tri_moi JSONB,
    thoi_gian   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- 1. DANH MỤC DÙNG CHUNG (master data)
-- ============================================================
CREATE TABLE nhan_vien (
    id          BIGSERIAL PRIMARY KEY,
    nguoi_dung_id BIGINT UNIQUE REFERENCES nguoi_dung(id),
    phong_ban_id BIGINT REFERENCES phong_ban(id),
    ma          VARCHAR(20) UNIQUE,
    ho_ten      VARCHAR(120) NOT NULL,
    chuc_danh   VARCHAR(120),
    ngay_vao    DATE,
    luong_co_ban NUMERIC(18,0) DEFAULT 0,
    trang_thai  VARCHAR(20) NOT NULL DEFAULT 'DANG_LAM'
);

ALTER TABLE phong_ban
    ADD CONSTRAINT fk_phong_ban_tp FOREIGN KEY (truong_phong_id) REFERENCES nhan_vien(id);

CREATE TABLE khach_hang (
    id          BIGSERIAL PRIMARY KEY,
    ma          VARCHAR(20) UNIQUE,
    ten         VARCHAR(200) NOT NULL,
    ma_so_thue  VARCHAR(20),
    dien_thoai  VARCHAR(30),
    dia_chi     TEXT,
    phan_loai_abc CHAR(1),                            -- A / B / C
    nguoi_phu_trach BIGINT REFERENCES nhan_vien(id),  -- record-level scope
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE nha_cung_cap (
    id          BIGSERIAL PRIMARY KEY,
    ma          VARCHAR(20) UNIQUE,
    ten         VARCHAR(200) NOT NULL,
    ma_so_thue  VARCHAR(20),
    dien_thoai  VARCHAR(30),
    diem_danh_gia NUMERIC(3,1) DEFAULT 0,             -- 0..5
    blacklist   BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE hang_hoa (
    id          BIGSERIAL PRIMARY KEY,
    ma          VARCHAR(40) UNIQUE,
    ten         VARCHAR(200) NOT NULL,
    loai        loai_hang NOT NULL,
    don_vi      VARCHAR(20),
    gia_ban     NUMERIC(18,0) DEFAULT 0
);

CREATE TABLE ton_kho (
    id          BIGSERIAL PRIMARY KEY,
    hang_hoa_id BIGINT NOT NULL UNIQUE REFERENCES hang_hoa(id),
    so_luong    NUMERIC(15,3) NOT NULL DEFAULT 0,
    ton_min     NUMERIC(15,3) NOT NULL DEFAULT 0,
    ton_max     NUMERIC(15,3)
);

-- ============================================================
-- 2. BÁN HÀNG
-- ============================================================
CREATE TABLE bao_gia (
    id          BIGSERIAL PRIMARY KEY,
    so          VARCHAR(30) UNIQUE,
    khach_hang_id BIGINT NOT NULL REFERENCES khach_hang(id),
    nguoi_tao   BIGINT REFERENCES nhan_vien(id),
    ngay        DATE NOT NULL DEFAULT CURRENT_DATE,
    tong_tien   NUMERIC(18,0) NOT NULL DEFAULT 0,
    trang_thai  trang_thai_duyet NOT NULL DEFAULT 'NHAP',
    nguoi_duyet BIGINT REFERENCES nhan_vien(id)
);

CREATE TABLE bao_gia_ct (
    id          BIGSERIAL PRIMARY KEY,
    bao_gia_id  BIGINT NOT NULL REFERENCES bao_gia(id) ON DELETE CASCADE,
    hang_hoa_id BIGINT NOT NULL REFERENCES hang_hoa(id),
    so_luong    NUMERIC(15,3) NOT NULL,
    don_gia     NUMERIC(18,0) NOT NULL
);

CREATE TABLE don_hang (
    id          BIGSERIAL PRIMARY KEY,
    so          VARCHAR(30) UNIQUE,
    khach_hang_id BIGINT NOT NULL REFERENCES khach_hang(id),
    bao_gia_id  BIGINT REFERENCES bao_gia(id),
    ngay        DATE NOT NULL DEFAULT CURRENT_DATE,
    tong_tien   NUMERIC(18,0) NOT NULL DEFAULT 0,
    trang_thai  VARCHAR(20) NOT NULL DEFAULT 'MOI'
);

CREATE TABLE don_hang_ct (
    id          BIGSERIAL PRIMARY KEY,
    don_hang_id BIGINT NOT NULL REFERENCES don_hang(id) ON DELETE CASCADE,
    hang_hoa_id BIGINT NOT NULL REFERENCES hang_hoa(id),
    so_luong    NUMERIC(15,3) NOT NULL,
    don_gia     NUMERIC(18,0) NOT NULL
);

-- ============================================================
-- 3. KHO (phiếu nhập / xuất chung một bảng)
-- ============================================================
CREATE TABLE phieu_kho (
    id          BIGSERIAL PRIMARY KEY,
    so          VARCHAR(30) UNIQUE,
    loai        loai_phieu_kho NOT NULL,
    don_hang_id BIGINT REFERENCES don_hang(id),       -- nếu là phiếu xuất bán
    don_mua_id  BIGINT,                               -- nếu là phiếu nhập mua (FK thêm bên dưới)
    ngay        DATE NOT NULL DEFAULT CURRENT_DATE,
    nguoi_tao   BIGINT REFERENCES nhan_vien(id)
);

CREATE TABLE phieu_kho_ct (
    id          BIGSERIAL PRIMARY KEY,
    phieu_kho_id BIGINT NOT NULL REFERENCES phieu_kho(id) ON DELETE CASCADE,
    hang_hoa_id BIGINT NOT NULL REFERENCES hang_hoa(id),
    so_luong    NUMERIC(15,3) NOT NULL
);

-- ============================================================
-- 4. MUA HÀNG
-- ============================================================
CREATE TABLE yeu_cau_mua (
    id          BIGSERIAL PRIMARY KEY,
    hang_hoa_id BIGINT NOT NULL REFERENCES hang_hoa(id),
    so_luong    NUMERIC(15,3) NOT NULL,
    ly_do       VARCHAR(200),                         -- 'TON_DUOI_MIN' (tự động)
    nguoi_tao   BIGINT REFERENCES nhan_vien(id),
    ngay        DATE NOT NULL DEFAULT CURRENT_DATE
);

CREATE TABLE don_mua (
    id          BIGSERIAL PRIMARY KEY,
    so          VARCHAR(30) UNIQUE,
    nha_cung_cap_id BIGINT NOT NULL REFERENCES nha_cung_cap(id),
    ngay        DATE NOT NULL DEFAULT CURRENT_DATE,
    tong_tien   NUMERIC(18,0) NOT NULL DEFAULT 0,
    trang_thai  trang_thai_duyet NOT NULL DEFAULT 'NHAP',
    nguoi_duyet BIGINT REFERENCES nhan_vien(id)
);

CREATE TABLE don_mua_ct (
    id          BIGSERIAL PRIMARY KEY,
    don_mua_id  BIGINT NOT NULL REFERENCES don_mua(id) ON DELETE CASCADE,
    hang_hoa_id BIGINT NOT NULL REFERENCES hang_hoa(id),
    so_luong    NUMERIC(15,3) NOT NULL,
    don_gia     NUMERIC(18,0) NOT NULL
);

ALTER TABLE phieu_kho
    ADD CONSTRAINT fk_phieu_kho_dm FOREIGN KEY (don_mua_id) REFERENCES don_mua(id);

CREATE TABLE danh_gia_ncc (
    id          BIGSERIAL PRIMARY KEY,
    nha_cung_cap_id BIGINT NOT NULL REFERENCES nha_cung_cap(id),
    don_mua_id  BIGINT REFERENCES don_mua(id),
    diem        NUMERIC(3,1) NOT NULL,
    ngay        DATE NOT NULL DEFAULT CURRENT_DATE
);

-- ============================================================
-- 5. DỰ ÁN & DỊCH VỤ CHO THUÊ
-- ============================================================
CREATE TABLE du_an (
    id          BIGSERIAL PRIMARY KEY,
    ma          VARCHAR(30) UNIQUE,
    ten         VARCHAR(200) NOT NULL,
    khach_hang_id BIGINT REFERENCES khach_hang(id),
    truong_du_an BIGINT REFERENCES nhan_vien(id),
    du_toan     NUMERIC(18,0) DEFAULT 0,
    chi_phi_thuc_te NUMERIC(18,0) DEFAULT 0,
    qcvn        VARCHAR(40),                           -- chuẩn xả thải cam kết
    trang_thai  trang_thai_du_an NOT NULL DEFAULT 'MOI',
    deadline    DATE
);

CREATE TABLE du_an_phan_cong (
    id          BIGSERIAL PRIMARY KEY,
    du_an_id    BIGINT NOT NULL REFERENCES du_an(id) ON DELETE CASCADE,
    nhan_vien_id BIGINT NOT NULL REFERENCES nhan_vien(id),
    vai_tro_du_an VARCHAR(60),
    UNIQUE (du_an_id, nhan_vien_id)
);

CREATE TABLE du_an_chi_phi (
    id          BIGSERIAL PRIMARY KEY,
    du_an_id    BIGINT NOT NULL REFERENCES du_an(id) ON DELETE CASCADE,
    mo_ta       VARCHAR(200),
    so_tien     NUMERIC(18,0) NOT NULL,
    trang_thai  trang_thai_duyet NOT NULL DEFAULT 'CHO_DUYET',
    ngay        DATE NOT NULL DEFAULT CURRENT_DATE
);

CREATE TABLE nghiem_thu (
    id          BIGSERIAL PRIMARY KEY,
    du_an_id    BIGINT NOT NULL REFERENCES du_an(id),
    ngay        DATE NOT NULL DEFAULT CURRENT_DATE,
    ket_qua_qcvn VARCHAR(40),                          -- so với chuẩn cam kết (B8)
    khach_ky    BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE hop_dong_thue (
    id          BIGSERIAL PRIMARY KEY,
    so          VARCHAR(30) UNIQUE,
    khach_hang_id BIGINT NOT NULL REFERENCES khach_hang(id),
    doi_tuong   doi_tuong_thue NOT NULL,
    gia_thue    NUMERIC(18,0) NOT NULL,
    chu_ky      VARCHAR(20),                           -- THANG / QUY
    ngay_bat_dau DATE NOT NULL,
    ngay_ket_thuc DATE NOT NULL,
    trang_thai  VARCHAR(20) NOT NULL DEFAULT 'HIEU_LUC'
);

CREATE TABLE tai_san_thue (
    id          BIGSERIAL PRIMARY KEY,
    hop_dong_thue_id BIGINT NOT NULL REFERENCES hop_dong_thue(id) ON DELETE CASCADE,
    hang_hoa_id BIGINT REFERENCES hang_hoa(id),        -- nếu là HC/VT/thiết bị
    nhan_vien_id BIGINT REFERENCES nhan_vien(id),      -- nếu là nhân sự cho thuê
    so_luong    NUMERIC(15,3) DEFAULT 1,
    ngay_tra    DATE
);

-- ============================================================
-- 6. KẾ TOÁN & TÀI CHÍNH (tích hợp HĐĐT, không tự dựng engine thuế)
-- ============================================================
CREATE TABLE hoa_don (
    id          BIGSERIAL PRIMARY KEY,
    loai        loai_hoa_don NOT NULL,
    don_hang_id BIGINT REFERENCES don_hang(id),
    don_mua_id  BIGINT REFERENCES don_mua(id),
    du_an_id    BIGINT REFERENCES du_an(id),
    hop_dong_thue_id BIGINT REFERENCES hop_dong_thue(id),
    ngay        DATE NOT NULL DEFAULT CURRENT_DATE,
    tien_truoc_thue NUMERIC(18,0) NOT NULL DEFAULT 0,
    tien_thue   NUMERIC(18,0) NOT NULL DEFAULT 0,
    tong_tien   NUMERIC(18,0) NOT NULL DEFAULT 0,
    hddt_provider VARCHAR(40),                          -- MISA / VNPT / Viettel
    hddt_ma_tra_cuu VARCHAR(60),                         -- mã tra cứu từ nhà cung cấp HĐĐT
    hddt_trang_thai VARCHAR(20)
);

CREATE TABLE cong_no (
    id          BIGSERIAL PRIMARY KEY,
    loai        loai_cong_no NOT NULL,
    hoa_don_id  BIGINT REFERENCES hoa_don(id),
    khach_hang_id BIGINT REFERENCES khach_hang(id),
    nha_cung_cap_id BIGINT REFERENCES nha_cung_cap(id),
    so_tien     NUMERIC(18,0) NOT NULL,
    da_thanh_toan NUMERIC(18,0) NOT NULL DEFAULT 0,
    han         DATE,
    trang_thai  VARCHAR(20) NOT NULL DEFAULT 'CHUA_THU'
);

CREATE TABLE thanh_toan (
    id          BIGSERIAL PRIMARY KEY,
    cong_no_id  BIGINT NOT NULL REFERENCES cong_no(id),
    so_tien     NUMERIC(18,0) NOT NULL,
    ngay        DATE NOT NULL DEFAULT CURRENT_DATE,
    hinh_thuc   VARCHAR(30)
);

CREATE TABLE but_toan (
    id          BIGSERIAL PRIMARY KEY,
    ngay        DATE NOT NULL DEFAULT CURRENT_DATE,
    tk_no       VARCHAR(20) NOT NULL,                  -- tài khoản theo TT 200/133
    tk_co       VARCHAR(20) NOT NULL,
    so_tien     NUMERIC(18,0) NOT NULL,
    dien_giai   VARCHAR(200),
    hoa_don_id  BIGINT REFERENCES hoa_don(id)
);

-- ============================================================
-- 7. NHÂN SỰ & LƯƠNG
-- ============================================================
CREATE TABLE cham_cong (
    id          BIGSERIAL PRIMARY KEY,
    nhan_vien_id BIGINT NOT NULL REFERENCES nhan_vien(id),
    ngay        DATE NOT NULL,
    gio_vao     TIME,
    gio_ra      TIME,
    UNIQUE (nhan_vien_id, ngay)
);

CREATE TABLE nghi_phep (
    id          BIGSERIAL PRIMARY KEY,
    nhan_vien_id BIGINT NOT NULL REFERENCES nhan_vien(id),
    tu_ngay     DATE NOT NULL,
    den_ngay    DATE NOT NULL,
    loai        VARCHAR(20),                            -- PHEP / OT / KHONG_LUONG
    trang_thai  trang_thai_duyet NOT NULL DEFAULT 'CHO_DUYET',
    nguoi_duyet BIGINT REFERENCES nhan_vien(id)
);

CREATE TABLE bang_luong (
    id          BIGSERIAL PRIMARY KEY,
    nhan_vien_id BIGINT NOT NULL REFERENCES nhan_vien(id),
    thang       CHAR(7) NOT NULL,                       -- 'YYYY-MM'
    luong_co_ban NUMERIC(18,0) NOT NULL DEFAULT 0,
    phu_cap     NUMERIC(18,0) NOT NULL DEFAULT 0,
    ot          NUMERIC(18,0) NOT NULL DEFAULT 0,
    khau_tru    NUMERIC(18,0) NOT NULL DEFAULT 0,
    thuc_linh   NUMERIC(18,0) NOT NULL DEFAULT 0,
    trang_thai  trang_thai_duyet NOT NULL DEFAULT 'CHO_DUYET',
    UNIQUE (nhan_vien_id, thang)
);

CREATE TABLE kpi (
    id          BIGSERIAL PRIMARY KEY,
    nhan_vien_id BIGINT NOT NULL REFERENCES nhan_vien(id),
    thang       CHAR(7) NOT NULL,
    diem        SMALLINT NOT NULL CHECK (diem BETWEEN 1 AND 5),
    ghi_chu     VARCHAR(200),
    UNIQUE (nhan_vien_id, thang)
);

-- ============================================================
-- Chỉ mục cho các khóa ngoại hay truy vấn
-- ============================================================
CREATE INDEX idx_nguoi_dung_vai_tro   ON nguoi_dung(vai_tro_id);
CREATE INDEX idx_phan_quyen_vai_tro   ON phan_quyen(vai_tro_id);
CREATE INDEX idx_audit_thoi_gian      ON audit_log(thoi_gian);
CREATE INDEX idx_khach_hang_phu_trach ON khach_hang(nguoi_phu_trach);
CREATE INDEX idx_bao_gia_kh           ON bao_gia(khach_hang_id);
CREATE INDEX idx_don_hang_kh          ON don_hang(khach_hang_id);
CREATE INDEX idx_don_mua_ncc          ON don_mua(nha_cung_cap_id);
CREATE INDEX idx_cong_no_han          ON cong_no(han);
CREATE INDEX idx_du_an_kh             ON du_an(khach_hang_id);
CREATE INDEX idx_hop_dong_thue_kt     ON hop_dong_thue(ngay_ket_thuc);
CREATE INDEX idx_bang_luong_thang     ON bang_luong(thang);
