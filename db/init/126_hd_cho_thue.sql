-- 126: Thong so HOP DONG cho thue tren du an (form dien moi khi co hop dong moi): so hop dong, ngay ky
ALTER TABLE tai_san_cho_thue ADD COLUMN IF NOT EXISTS so_hop_dong VARCHAR(60);
ALTER TABLE tai_san_cho_thue ADD COLUMN IF NOT EXISTS ngay_ky_hd DATE;
