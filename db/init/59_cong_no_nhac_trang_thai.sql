-- 59: Cong no phai thu — trang thai nhac cua Sales (Cho thanh toan / Hoan thanh)
ALTER TABLE cong_no ADD COLUMN IF NOT EXISTS nhac_trang_thai VARCHAR(12) NOT NULL DEFAULT 'CHO';
