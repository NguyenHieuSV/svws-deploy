-- 99: Hoa don cho — link + ma tra cuu HDDT trich tu than thu
ALTER TABLE kt_hoa_don_cho ADD COLUMN IF NOT EXISTS link_tra_cuu VARCHAR(300);
ALTER TABLE kt_hoa_don_cho ADD COLUMN IF NOT EXISTS ma_tra_cuu VARCHAR(40);
