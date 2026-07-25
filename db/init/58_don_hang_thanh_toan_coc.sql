-- 58: Don hang ban — them cot so tien "Thanh toan coc" (tien coc khach da tra)
ALTER TABLE don_hang ADD COLUMN IF NOT EXISTS thanh_toan_coc NUMERIC(18,0) NOT NULL DEFAULT 0;
