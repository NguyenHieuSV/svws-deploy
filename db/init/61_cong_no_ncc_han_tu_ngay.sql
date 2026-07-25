-- 61: Cong no phai tra nhap ngoai — backfill "Ngay thanh toan" (han) tu ngay chung tu (cot Ngay thanh toan cua file)
UPDATE cong_no
SET han = ngay_ct
WHERE loai = 'PHAI_TRA'
  AND han IS NULL
  AND ngay_ct IS NOT NULL
  AND hoa_don_id IS NULL
  AND don_mua_id IS NULL;
