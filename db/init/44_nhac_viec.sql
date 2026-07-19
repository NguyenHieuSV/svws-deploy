-- 44_nhac_viec.sql — Work Reminder: nhắc việc cho chính mình hoặc cho người khác
-- Mọi nhân viên đều tạo được; quản lý (nhan_su XEM) xem toàn bộ.
CREATE TABLE IF NOT EXISTS nhac_viec (
    id              BIGSERIAL PRIMARY KEY,
    nguoi_tao       BIGINT NOT NULL REFERENCES nhan_vien(id) ON DELETE CASCADE,  -- người đặt lời nhắc
    nhan_vien_id    BIGINT NOT NULL REFERENCES nhan_vien(id) ON DELETE CASCADE,  -- người ĐƯỢC nhắc
    tieu_de         TEXT   NOT NULL,                 -- Cần làm việc gì
    thoi_diem       TIMESTAMP NOT NULL,              -- Khi nào (giờ địa phương, không quy đổi múi giờ)
    ma_lien_quan    VARCHAR(120),                    -- Mã đơn hàng / dự án liên quan
    chuan_bi        TEXT,                            -- Cần chuẩn bị gì
    nguoi_ho_tro_id BIGINT REFERENCES nhan_vien(id) ON DELETE SET NULL,          -- Ai hỗ trợ
    ho_tro_gi       TEXT,                            -- Hỗ trợ ra sao
    muc_do          VARCHAR(20) NOT NULL DEFAULT 'BINH_THUONG',  -- THAP|BINH_THUONG|CAO|KHAN
    trang_thai      VARCHAR(20) NOT NULL DEFAULT 'CHO_LAM',      -- CHO_LAM|DANG_LAM|XONG|HUY
    ghi_chu         TEXT,
    tao_luc         TIMESTAMPTZ NOT NULL DEFAULT now(),
    xong_luc        TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_nhac_viec_nguoi_nhan ON nhac_viec (nhan_vien_id, thoi_diem);
CREATE INDEX IF NOT EXISTS idx_nhac_viec_nguoi_tao  ON nhac_viec (nguoi_tao, thoi_diem);
CREATE INDEX IF NOT EXISTS idx_nhac_viec_thoi_diem  ON nhac_viec (thoi_diem);
