-- 57: Cong no — luu so hoa don/chung tu (so_ct) de phat hien TRUNG khi AI upload
ALTER TABLE cong_no ADD COLUMN IF NOT EXISTS so_ct VARCHAR(60);

-- Backfill so_ct tu ghi_chu dang "HĐ <so> · ..." (du lieu da nhap truoc do)
UPDATE cong_no
SET so_ct = NULLIF(trim(replace(split_part(ghi_chu, ' · ', 1), 'HĐ ', '')), '')
WHERE so_ct IS NULL AND ghi_chu LIKE 'HĐ %';
