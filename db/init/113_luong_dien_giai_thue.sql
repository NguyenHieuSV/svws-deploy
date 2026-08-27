-- 113: snapshot dien giai thue TNCN tren tung phieu luong (doi chieu tung dong)
ALTER TABLE bang_luong ADD COLUMN IF NOT EXISTS mien_thue NUMERIC(18,0) DEFAULT 0;
ALTER TABLE bang_luong ADD COLUMN IF NOT EXISTS giam_tru_gia_canh NUMERIC(18,0) DEFAULT 0;
ALTER TABLE bang_luong ADD COLUMN IF NOT EXISTS so_phu_thuoc_tinh INTEGER DEFAULT 0;
