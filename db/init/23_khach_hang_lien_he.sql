-- Người liên hệ phía khách hàng (tên người đại diện làm việc trực tiếp)
ALTER TABLE khach_hang ADD COLUMN IF NOT EXISTS nguoi_lien_he VARCHAR(120);
