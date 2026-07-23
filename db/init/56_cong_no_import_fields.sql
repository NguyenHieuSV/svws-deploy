-- 56: Cong no nhap ngoai (AI Upload) — luu ngay chung tu & ma hang ban dang text
ALTER TABLE cong_no ADD COLUMN IF NOT EXISTS ngay_ct DATE;
ALTER TABLE cong_no ADD COLUMN IF NOT EXISTS ma_ban_ngoai VARCHAR(60);
