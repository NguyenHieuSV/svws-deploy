-- 116: don hang da xuat hoa don BAN nhung o so_hoa_don con trong -> dien tu hoa_don
UPDATE don_hang d SET so_hoa_don = h.so
FROM hoa_don h
WHERE h.loai = 'BAN' AND h.don_hang_id = d.id
  AND (d.so_hoa_don IS NULL OR btrim(d.so_hoa_don) = '')
  AND h.so IS NOT NULL AND btrim(h.so) <> '';
