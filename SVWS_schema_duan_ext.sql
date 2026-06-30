-- ============ MỞ RỘNG PHÂN HỆ DỰ ÁN ============
ALTER TABLE du_an ADD COLUMN IF NOT EXISTS chu_dau_tu       VARCHAR(200);
ALTER TABLE du_an ADD COLUMN IF NOT EXISTS dia_diem         VARCHAR(255);
ALTER TABLE du_an ADD COLUMN IF NOT EXISTS loai_du_an       VARCHAR(40);   -- CAP_NUOC / NUOC_THAI / KHI_THAI / KHAC
ALTER TABLE du_an ADD COLUMN IF NOT EXISTS cong_suat        VARCHAR(80);   -- vd "1.200 m³/ngày"
ALTER TABLE du_an ADD COLUMN IF NOT EXISTS gia_tri_hop_dong NUMERIC(18,0) DEFAULT 0;
ALTER TABLE du_an ADD COLUMN IF NOT EXISTS ngay_bat_dau     DATE;
ALTER TABLE du_an ADD COLUMN IF NOT EXISTS ngay_kt_ke_hoach DATE;
ALTER TABLE du_an ADD COLUMN IF NOT EXISTS ngay_kt_thuc_te  DATE;
ALTER TABLE du_an ADD COLUMN IF NOT EXISTS mo_ta            TEXT;
ALTER TABLE du_an ADD COLUMN IF NOT EXISTS tien_do          NUMERIC(5,2) DEFAULT 0;  -- % tổng (tính từ mốc)

-- THIẾT KẾ (1 bản ghi/dự án, có phiên bản)
CREATE TABLE IF NOT EXISTS du_an_thiet_ke (
    du_an_id      BIGINT PRIMARY KEY REFERENCES du_an(id) ON DELETE CASCADE,
    cong_nghe     TEXT,                 -- công nghệ áp dụng
    cong_suat_tk  VARCHAR(80),
    tieu_chuan    VARCHAR(120),         -- QCVN/tiêu chuẩn áp dụng
    thong_so      TEXT,                 -- JSON danh sách thông số thiết kế [{ten,gia_tri,don_vi}]
    nguoi_thiet_ke VARCHAR(120),
    ngay_duyet    DATE,
    phien_ban     VARCHAR(20) DEFAULT 'v1.0',
    trang_thai    VARCHAR(16) DEFAULT 'DU_THAO',  -- DU_THAO / DA_DUYET
    ghi_chu       TEXT,
    cap_nhat      TIMESTAMP DEFAULT now()
);

-- TIẾN ĐỘ (mốc/hạng mục công việc)
CREATE TABLE IF NOT EXISTS du_an_moc (
    id          BIGSERIAL PRIMARY KEY,
    du_an_id    BIGINT NOT NULL REFERENCES du_an(id) ON DELETE CASCADE,
    thu_tu      INT DEFAULT 0,
    ten         VARCHAR(200) NOT NULL,
    giai_doan   VARCHAR(40),            -- KHAO_SAT/THIET_KE/MUA_SAM/THI_CONG/LAP_DAT/CHAY_THU/NGHIEM_THU/BAN_GIAO
    ngay_bd_kh  DATE, ngay_kt_kh DATE, ngay_kt_tt DATE,
    trong_so    NUMERIC(6,2) DEFAULT 1, -- trọng số để tính % tổng
    phan_tram   NUMERIC(5,2) DEFAULT 0,
    trang_thai  VARCHAR(16) DEFAULT 'CHUA_BAT_DAU', -- CHUA_BAT_DAU/DANG_LAM/HOAN_THANH/CHAM_TRE
    phu_trach   VARCHAR(120),
    ghi_chu     TEXT
);

-- ĐÁNH GIÁ AN TOÀN (nhận diện mối nguy & biện pháp - HIRA)
CREATE TABLE IF NOT EXISTS du_an_an_toan (
    id          BIGSERIAL PRIMARY KEY,
    du_an_id    BIGINT NOT NULL REFERENCES du_an(id) ON DELETE CASCADE,
    hang_muc    VARCHAR(200) NOT NULL,  -- công việc/khu vực
    moi_nguy    TEXT,                   -- mối nguy
    muc_rui_ro  VARCHAR(10) DEFAULT 'TRUNG', -- CAO/TRUNG/THAP (người đánh giá chọn)
    bien_phap   TEXT,                   -- biện pháp kiểm soát
    phu_trach   VARCHAR(120),
    han         DATE,
    trang_thai  VARCHAR(16) DEFAULT 'MO', -- MO/DANG_XU_LY/DA_KIEM_SOAT
    nguoi_danh_gia VARCHAR(120),
    ngay_danh_gia  DATE DEFAULT CURRENT_DATE
);

-- NHẬT KÝ TRIỂN KHAI (site diary)
CREATE TABLE IF NOT EXISTS du_an_nhat_ky (
    id          BIGSERIAL PRIMARY KEY,
    du_an_id    BIGINT NOT NULL REFERENCES du_an(id) ON DELETE CASCADE,
    ngay        DATE NOT NULL DEFAULT CURRENT_DATE,
    noi_dung    TEXT,
    nhan_luc    VARCHAR(120),
    thiet_bi    VARCHAR(200),
    thoi_tiet   VARCHAR(60),
    van_de      TEXT,
    nguoi_ghi   VARCHAR(120),
    ngay_tao    TIMESTAMP DEFAULT now()
);

-- TÀI LIỆU (thiết bị/vật tư/bản vẽ/biên bản giao nhận/bàn giao/nghiệm thu/khác)
CREATE TABLE IF NOT EXISTS du_an_tai_lieu (
    id          BIGSERIAL PRIMARY KEY,
    du_an_id    BIGINT NOT NULL REFERENCES du_an(id) ON DELETE CASCADE,
    loai        VARCHAR(20) NOT NULL DEFAULT 'KHAC', -- THIET_BI/VAT_TU/BAN_VE/BB_GIAO_NHAN/BAN_GIAO/NGHIEM_THU/KHAC
    ten         VARCHAR(255) NOT NULL,
    ma_so       VARCHAR(60),
    phien_ban   VARCHAR(20),
    ngay        DATE DEFAULT CURRENT_DATE,
    duong_dan   TEXT,                   -- file lưu trong storage (nếu có)
    kich_thuoc  BIGINT DEFAULT 0,
    trang_thai  VARCHAR(16) DEFAULT 'HIEU_LUC', -- HIEU_LUC/HET_HIEU_LUC/DU_THAO
    nguoi_tao   VARCHAR(120),
    ghi_chu     TEXT,
    ngay_tao    TIMESTAMP DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_dataili_loai ON du_an_tai_lieu(du_an_id, loai);

-- KPI dự án (do người dùng tự định nghĩa mục tiêu/thực tế)
CREATE TABLE IF NOT EXISTS du_an_kpi (
    id          BIGSERIAL PRIMARY KEY,
    du_an_id    BIGINT NOT NULL REFERENCES du_an(id) ON DELETE CASCADE,
    ten         VARCHAR(200) NOT NULL,
    don_vi      VARCHAR(40),
    chieu       VARCHAR(8) DEFAULT 'CAO', -- CAO: càng cao càng tốt / THAP: càng thấp càng tốt
    muc_tieu    NUMERIC(18,2),
    thuc_te     NUMERIC(18,2),
    trong_so    NUMERIC(6,2) DEFAULT 1,
    ky          VARCHAR(7),
    ghi_chu     TEXT
);

-- BÁO CÁO dự án (bản ghi báo cáo theo kỳ, chốt số liệu thực tại thời điểm lập)
CREATE TABLE IF NOT EXISTS du_an_bao_cao (
    id          BIGSERIAL PRIMARY KEY,
    du_an_id    BIGINT NOT NULL REFERENCES du_an(id) ON DELETE CASCADE,
    ky          VARCHAR(20),
    tieu_de     VARCHAR(200),
    tien_do     NUMERIC(5,2),
    noi_dung    TEXT,
    van_de      TEXT,
    ngay        DATE DEFAULT CURRENT_DATE,
    nguoi_tao   VARCHAR(120),
    ngay_tao    TIMESTAMP DEFAULT now()
);
