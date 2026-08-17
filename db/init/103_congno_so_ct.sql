-- 103: cong no sinh tu hoa don — chep so hoa don + ngay chung tu sang cong no (backfill idempotent)
UPDATE cong_no SET so_ct = hd.so
FROM hoa_don hd
WHERE cong_no.hoa_don_id = hd.id AND hd.so IS NOT NULL
  AND (cong_no.so_ct IS NULL OR cong_no.so_ct = '');
UPDATE cong_no SET ngay_ct = hd.ngay
FROM hoa_don hd
WHERE cong_no.hoa_don_id = hd.id AND hd.ngay IS NOT NULL AND cong_no.ngay_ct IS NULL;
