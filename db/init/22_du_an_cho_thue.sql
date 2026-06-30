-- ============================================================
-- SVWS 22 — Cho thuê: Tên dự án + mã bán hàng theo tháng
-- Mã bán hàng tháng = ten_du_an + MMYY (vd RO-STH + 0126).
-- ============================================================
BEGIN;
ALTER TABLE tai_san_cho_thue ADD COLUMN IF NOT EXISTS ten_du_an VARCHAR(120);
UPDATE tai_san_cho_thue SET ten_du_an = ma WHERE ten_du_an IS NULL;
COMMIT;
