-- 115: de xuat mua tao tu du toan du an — gan lai ma don hang ban trung voi ma du an
UPDATE yeu_cau_mua y SET don_hang_id = d.id
FROM don_hang d
WHERE y.don_hang_id IS NULL
  AND y.ly_do LIKE 'Dự toán dự án %'
  AND lower(trim(substring(y.ly_do from 15))) = lower(trim(d.so));
