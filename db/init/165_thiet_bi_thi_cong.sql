-- 165 — 🔧 Thiết bị thi công (anh Hiếu 01/11/2026): sổ thiết bị / dụng cụ CÁ THỂ (có mã · serial · tình trạng),
--       cấp phát ra công trường và thu hồi về kho theo dự án. Khác với tài sản cho thuê (tai_san_cho_thue) và
--       khác với hàng hóa kho đếm số lượng — đây là quản theo từng cái máy/dụng cụ.

-- Sổ thiết bị cá thể
CREATE TABLE IF NOT EXISTS thiet_bi_thi_cong (
    id                BIGSERIAL PRIMARY KEY,
    ma                VARCHAR(40) UNIQUE,
    ten               VARCHAR(200) NOT NULL,
    loai              VARCHAR(20) DEFAULT 'MAY_MOC',   -- MAY_MOC/DUNG_CU/DO_DO/AN_TOAN/KHAC
    model             VARCHAR(120),
    serial            VARCHAR(120),
    nguyen_gia        NUMERIC(18,0) DEFAULT 0,
    ngay_mua          DATE,
    tinh_trang        VARCHAR(16) DEFAULT 'SAN_SANG',  -- SAN_SANG/DANG_CAP_PHAT/BAO_TRI/HONG/THANH_LY
    du_an_hien_tai_id BIGINT REFERENCES du_an(id) ON DELETE SET NULL,  -- NULL = đang ở kho
    ghi_chu           TEXT,
    created_at        TIMESTAMPTZ DEFAULT now()
);

-- Nhật ký cấp phát – thu hồi (1 thiết bị nhiều lần cấp/trả)
CREATE TABLE IF NOT EXISTS cap_phat_thiet_bi (
    id              BIGSERIAL PRIMARY KEY,
    thiet_bi_id     BIGINT NOT NULL REFERENCES thiet_bi_thi_cong(id) ON DELETE CASCADE,
    du_an_id        BIGINT REFERENCES du_an(id) ON DELETE SET NULL,
    nguoi_nhan_id   BIGINT REFERENCES nhan_vien(id) ON DELETE SET NULL,  -- người nhận tại công trường (nhân viên có tài khoản)
    ngay_cap        DATE DEFAULT CURRENT_DATE,
    tinh_trang_cap  TEXT,                                 -- ghi chú tình trạng lúc cấp
    ngay_tra        DATE,                                 -- NULL = đang giữ ngoài công trường
    tinh_trang_tra  TEXT,                                 -- tình trạng lúc trả (nguyên vẹn / hỏng…)
    nguoi_duyet_id  BIGINT REFERENCES nhan_vien(id) ON DELETE SET NULL,
    ghi_chu         TEXT
);
CREATE INDEX IF NOT EXISTS idx_cap_phat_tb   ON cap_phat_thiet_bi(thiet_bi_id);
CREATE INDEX IF NOT EXISTS idx_cap_phat_da   ON cap_phat_thiet_bi(du_an_id);
CREATE INDEX IF NOT EXISTS idx_tbtc_tinh     ON thiet_bi_thi_cong(tinh_trang);
