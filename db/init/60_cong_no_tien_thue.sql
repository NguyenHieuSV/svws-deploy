-- 60: Cong no — luu tien thue (VAT) de bang cong no tach duoc So tien / VAT / Tong
ALTER TABLE cong_no ADD COLUMN IF NOT EXISTS tien_thue NUMERIC(18,0) NOT NULL DEFAULT 0;
