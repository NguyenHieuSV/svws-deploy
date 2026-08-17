-- 105: nhan don mua DINH KY (xac nhan khi tao don nghi trung)
ALTER TABLE don_mua ADD COLUMN IF NOT EXISTS dinh_ky BOOLEAN DEFAULT FALSE;
