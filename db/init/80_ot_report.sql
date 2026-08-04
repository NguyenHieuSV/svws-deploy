-- Overtime Report: bao cao gio tang ca THUC TE sau khi OT duoc duyet
ALTER TABLE ngay_nghi_ot ADD COLUMN IF NOT EXISTS tt_tu VARCHAR(5);
ALTER TABLE ngay_nghi_ot ADD COLUMN IF NOT EXISTS tt_den VARCHAR(5);
ALTER TABLE ngay_nghi_ot ADD COLUMN IF NOT EXISTS so_gio_dang_ky NUMERIC(5,2);
ALTER TABLE ngay_nghi_ot ADD COLUMN IF NOT EXISTS ket_qua_cv TEXT;
ALTER TABLE ngay_nghi_ot ADD COLUMN IF NOT EXISTS bc_ot_ghi_chu TEXT;
ALTER TABLE ngay_nghi_ot ADD COLUMN IF NOT EXISTS bc_ot_luc TIMESTAMP;
