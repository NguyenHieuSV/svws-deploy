-- Nhiều người liên hệ cho một khách hàng: người liên hệ chính vẫn ở
-- nguoi_lien_he/email/dien_thoai; người liên hệ phụ lưu JSONB [{ten,email,dien_thoai}]
ALTER TABLE khach_hang
    ADD COLUMN IF NOT EXISTS lien_he_phu JSONB NOT NULL DEFAULT '[]'::jsonb;
