-- 171 — Hàng chờ hóa đơn mua: TỰ TẢI hóa đơn từ link / mã tra cứu của cổng hóa đơn điện tử (26/11/2026).
-- File tải về (XML / PDF) lưu ở tep_dinh_kem với doi_tuong = 'KT_HDC', doi_tuong_id = kt_hoa_don_cho.id.
ALTER TABLE kt_hoa_don_cho ADD COLUMN IF NOT EXISTS tai_tt VARCHAR(12);                  -- OK | LOI | KHONG_HT (cổng chưa hỗ trợ)
ALTER TABLE kt_hoa_don_cho ADD COLUMN IF NOT EXISTS tai_lan INTEGER NOT NULL DEFAULT 0;  -- số lần đã thử tự tải
ALTER TABLE kt_hoa_don_cho ADD COLUMN IF NOT EXISTS tai_luc TIMESTAMP;
ALTER TABLE kt_hoa_don_cho ADD COLUMN IF NOT EXISTS tai_ghi_chu VARCHAR(300);
CREATE INDEX IF NOT EXISTS ix_tep_dinh_kem_doi_tuong ON tep_dinh_kem (doi_tuong, doi_tuong_id);
