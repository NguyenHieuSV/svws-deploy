-- 54: Cho thuê — phân loại tài sản theo hệ thống nước/khí (đồng bộ cấu trúc YTouch)
ALTER TABLE tai_san_cho_thue ADD COLUMN IF NOT EXISTS loai_he_thong VARCHAR(30);
