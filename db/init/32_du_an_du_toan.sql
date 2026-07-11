-- Danh mục thiết bị - vật tư - nhân sự... phục vụ lập dự toán dự án
CREATE TABLE IF NOT EXISTS du_an_du_toan (
    id BIGSERIAL PRIMARY KEY,
    du_an_id BIGINT NOT NULL REFERENCES du_an(id) ON DELETE CASCADE,
    loai TEXT NOT NULL DEFAULT 'THIET_BI',          -- THIET_BI | VAT_TU | NHAN_SU | CHI_PHI_KHAC
    ten VARCHAR(250) NOT NULL,
    quy_cach VARCHAR(300),
    don_vi VARCHAR(40),
    so_luong NUMERIC(18,3) DEFAULT 1,
    don_gia NUMERIC(18,0) DEFAULT 0,
    ghi_chu VARCHAR(300),
    thu_tu INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_du_an_du_toan_da ON du_an_du_toan(du_an_id);
