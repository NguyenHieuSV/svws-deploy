-- ============ MUA HÀNG — Giai đoạn 0: NCC mở rộng + liên kết PO ↔ đơn Bán hàng ============
-- Mục tiêu: 1 đầu mối email NCC, kiểm soát công nợ, và tính GIÁ VỐN / LÃI-LỖ theo mã đơn Bán hàng.
ALTER TABLE nha_cung_cap ADD COLUMN IF NOT EXISTS email           VARCHAR(120);
ALTER TABLE nha_cung_cap ADD COLUMN IF NOT EXISTS nguoi_phu_trach BIGINT REFERENCES nhan_vien(id);
ALTER TABLE nha_cung_cap ADD COLUMN IF NOT EXISTS han_muc_cong_no NUMERIC(18,0) NOT NULL DEFAULT 0;  -- trần dư nợ phải trả
ALTER TABLE nha_cung_cap ADD COLUMN IF NOT EXISTS dia_chi         VARCHAR(300);
ALTER TABLE nha_cung_cap ADD COLUMN IF NOT EXISTS ghi_chu         TEXT;

ALTER TABLE don_mua ADD COLUMN IF NOT EXISTS don_hang_id     BIGINT REFERENCES don_hang(id) ON DELETE SET NULL;  -- khóa liên kết sang Bán hàng
ALTER TABLE don_mua ADD COLUMN IF NOT EXISTS ngay_hen_giao   DATE;
ALTER TABLE don_mua ADD COLUMN IF NOT EXISTS ngay_giao_thuc  DATE;
ALTER TABLE don_mua ADD COLUMN IF NOT EXISTS trang_thai_nhan VARCHAR(12) NOT NULL DEFAULT 'CHUA';  -- CHUA/MOT_PHAN/DU
CREATE INDEX IF NOT EXISTS idx_donmua_dh ON don_mua(don_hang_id);

-- Mua hàng — Giai đoạn 1: nhận hàng (nhập kho) + công nợ phải trả + giá vốn thực nhận
ALTER TABLE don_mua_ct ADD COLUMN IF NOT EXISTS so_luong_nhan NUMERIC(15,3) NOT NULL DEFAULT 0;

-- Mua hàng — Đề xuất mua hàng (1 đầu mối xét duyệt) + liên kết NCC & mã bán hàng
ALTER TABLE yeu_cau_mua ADD COLUMN IF NOT EXISTS trang_thai      VARCHAR(12) NOT NULL DEFAULT 'MOI';  -- MOI/DA_DUYET/TU_CHOI/DA_TAO_PO
ALTER TABLE yeu_cau_mua ADD COLUMN IF NOT EXISTS nha_cung_cap_id BIGINT REFERENCES nha_cung_cap(id);
ALTER TABLE yeu_cau_mua ADD COLUMN IF NOT EXISTS don_hang_id     BIGINT REFERENCES don_hang(id) ON DELETE SET NULL;  -- mã bán hàng
ALTER TABLE yeu_cau_mua ADD COLUMN IF NOT EXISTS don_gia         NUMERIC(18,0);
ALTER TABLE yeu_cau_mua ADD COLUMN IF NOT EXISTS ngay_can        DATE;
ALTER TABLE yeu_cau_mua ADD COLUMN IF NOT EXISTS nguoi_duyet     BIGINT REFERENCES nhan_vien(id);
ALTER TABLE yeu_cau_mua ADD COLUMN IF NOT EXISTS don_mua_id      BIGINT REFERENCES don_mua(id) ON DELETE SET NULL;
ALTER TABLE yeu_cau_mua ADD COLUMN IF NOT EXISTS ghi_chu         TEXT;
CREATE INDEX IF NOT EXISTS idx_ycm_tt ON yeu_cau_mua(trang_thai);

-- Mua hàng — lưu kết quả AI Sourcing tự chạy khi duyệt đề xuất
ALTER TABLE yeu_cau_mua ADD COLUMN IF NOT EXISTS ai_ncc_id BIGINT REFERENCES nha_cung_cap(id);
ALTER TABLE yeu_cau_mua ADD COLUMN IF NOT EXISTS ai_goi_y  TEXT;

-- Mua hàng — BÁO GIÁ NCC (giá chào hiện tại) cho AI & web cùng dùng
CREATE TABLE IF NOT EXISTS bao_gia_ncc (
    id              BIGSERIAL PRIMARY KEY,
    nha_cung_cap_id BIGINT NOT NULL REFERENCES nha_cung_cap(id),
    hang_hoa_id     BIGINT NOT NULL REFERENCES hang_hoa(id),
    don_gia         NUMERIC(18,0) NOT NULL,
    so_luong_toi_thieu NUMERIC(15,3) NOT NULL DEFAULT 0,
    hieu_luc_den    DATE,
    ngay            DATE NOT NULL DEFAULT CURRENT_DATE,
    nguon           VARCHAR(12) NOT NULL DEFAULT 'THU_CONG',  -- THU_CONG/RFQ/WEB
    dieu_kien       TEXT,
    ghi_chu         TEXT,
    nguoi_tao       BIGINT REFERENCES nhan_vien(id)
);
CREATE INDEX IF NOT EXISTS idx_bgncc_hh ON bao_gia_ncc(hang_hoa_id);

-- Mua hàng — RFQ (gửi yêu cầu báo giá 1 đầu mối) + nhật ký
CREATE TABLE IF NOT EXISTS rfq (
    id            BIGSERIAL PRIMARY KEY,
    hang_hoa_id   BIGINT NOT NULL REFERENCES hang_hoa(id),
    so_luong      NUMERIC(15,3) NOT NULL DEFAULT 0,
    han_bao_gia   DATE,
    yeu_cau_mua_id BIGINT REFERENCES yeu_cau_mua(id) ON DELETE SET NULL,
    noi_dung      TEXT,
    gui_tu        VARCHAR(120),
    nguoi_tao     BIGINT REFERENCES nhan_vien(id),
    ngay          DATE NOT NULL DEFAULT CURRENT_DATE
);
CREATE TABLE IF NOT EXISTS rfq_log (
    id            BIGSERIAL PRIMARY KEY,
    rfq_id        BIGINT NOT NULL REFERENCES rfq(id) ON DELETE CASCADE,
    nha_cung_cap_id BIGINT NOT NULL REFERENCES nha_cung_cap(id),
    email         VARCHAR(160),
    da_gui        BOOLEAN NOT NULL DEFAULT FALSE,
    ket_qua       TEXT,
    ngay          DATE NOT NULL DEFAULT CURRENT_DATE
);
CREATE INDEX IF NOT EXISTS idx_rfqlog_rfq ON rfq_log(rfq_id);

-- Mua hàng — đề xuất NHIỀU sản phẩm + đính kèm dự toán (link/file)
CREATE TABLE IF NOT EXISTS yeu_cau_mua_ct (
    id              BIGSERIAL PRIMARY KEY,
    yeu_cau_mua_id  BIGINT NOT NULL REFERENCES yeu_cau_mua(id) ON DELETE CASCADE,
    hang_hoa_id     BIGINT NOT NULL REFERENCES hang_hoa(id),
    so_luong        NUMERIC(15,3) NOT NULL DEFAULT 0,
    don_gia         NUMERIC(18,0),
    ghi_chu         TEXT
);
CREATE INDEX IF NOT EXISTS idx_ycmct_ycm ON yeu_cau_mua_ct(yeu_cau_mua_id);
ALTER TABLE yeu_cau_mua ADD COLUMN IF NOT EXISTS dinh_kem_url  TEXT;
ALTER TABLE yeu_cau_mua ADD COLUMN IF NOT EXISTS dinh_kem_file TEXT;

-- Mua hàng — mỗi dòng đề xuất có thể chọn NCC riêng
ALTER TABLE yeu_cau_mua_ct ADD COLUMN IF NOT EXISTS nha_cung_cap_id BIGINT REFERENCES nha_cung_cap(id);
