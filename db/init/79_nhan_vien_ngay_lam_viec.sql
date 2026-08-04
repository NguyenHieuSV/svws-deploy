-- Ho so nhan vien: ngay vao lam + ngay nghi viec (phuc vu Resign list)
ALTER TABLE nhan_vien ADD COLUMN IF NOT EXISTS ngay_vao_lam DATE;
ALTER TABLE nhan_vien ADD COLUMN IF NOT EXISTS ngay_nghi_viec DATE;
