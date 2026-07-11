-- ============================================================
-- SVWS 31 — don_mua.ngay_tt: ngày ghi nhận thanh toán gần nhất
-- (phục vụ mục "Các đơn hàng cần thanh toán" trong tab Thanh toán mua hàng)
-- ============================================================
BEGIN;
ALTER TABLE don_mua ADD COLUMN IF NOT EXISTS ngay_tt DATE;
COMMIT;
