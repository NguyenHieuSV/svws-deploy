-- 125: DAU TU - CHO THUE. Don ban loai 'DAU_TU' (noi ma me du an cho thue): PO / chi phi = VON DAU TU, khong vao gia von.
--      Du an cho thue giu thong so hop dong: so thang (= thoi gian khau hao), ngay bat dau, san luong toi thieu / du kien.
ALTER TABLE don_hang ADD COLUMN IF NOT EXISTS loai_don VARCHAR(20) DEFAULT 'THUONG';
ALTER TABLE don_hang ADD COLUMN IF NOT EXISTS tai_san_cho_thue_id BIGINT;
ALTER TABLE tai_san_cho_thue ADD COLUMN IF NOT EXISTS so_thang_hd INTEGER;
ALTER TABLE tai_san_cho_thue ADD COLUMN IF NOT EXISTS ngay_bat_dau_hd DATE;
ALTER TABLE tai_san_cho_thue ADD COLUMN IF NOT EXISTS san_luong_toi_thieu NUMERIC(15,1) DEFAULT 0;
ALTER TABLE tai_san_cho_thue ADD COLUMN IF NOT EXISTS san_luong_du_kien NUMERIC(15,1) DEFAULT 0;
UPDATE don_hang SET loai_don = 'THUONG' WHERE loai_don IS NULL;
