-- ============================================================
-- Mở rộng cho module Nhân sự/Lương (chạy SAU SVWS_schema.sql)
--   - tách khoản khấu trừ: BHXH/BHYT/BHTN/TNCN
--   - dấu vết quy trình duyệt 2 bước: KTT duyệt -> CEO ký
-- ============================================================
ALTER TABLE bang_luong ADD COLUMN IF NOT EXISTS bhxh           NUMERIC(18,0) NOT NULL DEFAULT 0;
ALTER TABLE bang_luong ADD COLUMN IF NOT EXISTS bhyt           NUMERIC(18,0) NOT NULL DEFAULT 0;
ALTER TABLE bang_luong ADD COLUMN IF NOT EXISTS bhtn           NUMERIC(18,0) NOT NULL DEFAULT 0;
ALTER TABLE bang_luong ADD COLUMN IF NOT EXISTS thue_tncn      NUMERIC(18,0) NOT NULL DEFAULT 0;
ALTER TABLE bang_luong ADD COLUMN IF NOT EXISTS nguoi_duyet_ktt BIGINT REFERENCES nhan_vien(id);
ALTER TABLE bang_luong ADD COLUMN IF NOT EXISTS nguoi_ky_ceo    BIGINT REFERENCES nhan_vien(id);
CREATE INDEX IF NOT EXISTS idx_bang_luong_nv ON bang_luong(nhan_vien_id);
