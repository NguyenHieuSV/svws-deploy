-- 62: Don mua — luu So hoa don (nhap o form Thanh toan theo dot) de gan sang cong no phai tra
ALTER TABLE don_mua ADD COLUMN IF NOT EXISTS so_hoa_don VARCHAR(60);
