-- 63: Dot thanh toan mua hang — luu Hinh thuc (ngan hang / tien mat)
ALTER TABLE don_mua_dot_tt ADD COLUMN IF NOT EXISTS hinh_thuc VARCHAR(30);
