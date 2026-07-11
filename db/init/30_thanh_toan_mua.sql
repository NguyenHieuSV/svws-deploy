-- ============================================================
-- SVWS 30 — Thanh toán mua hàng: theo dõi đề nghị thanh toán từng PO
--   • don_mua thêm: de_nghi_tt (số tiền đề nghị thanh toán lũy kế),
--     ngay_tt_tiep (ngày thanh toán tiếp theo), tt_du (đã thanh toán 100%),
--     ngay_tt_du (ngày hoàn tất thanh toán).
--   • cong_no thêm don_mua_id để công nợ phải trả truy về đúng PO.
-- ============================================================
BEGIN;

ALTER TABLE don_mua ADD COLUMN IF NOT EXISTS de_nghi_tt   NUMERIC(18,0) NOT NULL DEFAULT 0;
ALTER TABLE don_mua ADD COLUMN IF NOT EXISTS ngay_tt_tiep DATE;
ALTER TABLE don_mua ADD COLUMN IF NOT EXISTS tt_du        BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE don_mua ADD COLUMN IF NOT EXISTS ngay_tt_du   DATE;

ALTER TABLE cong_no ADD COLUMN IF NOT EXISTS don_mua_id BIGINT REFERENCES don_mua(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_cong_no_don_mua ON cong_no(don_mua_id);

COMMIT;
