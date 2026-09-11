-- 117: Du toan -> De xuat mua; ma chuoi (ma_ban) tren de xuat va PO
ALTER TABLE du_toan_ban_muc ADD COLUMN IF NOT EXISTS hang_hoa_id BIGINT REFERENCES hang_hoa(id) ON DELETE SET NULL;
ALTER TABLE du_toan_ban_muc ADD COLUMN IF NOT EXISTS yeu_cau_mua_id BIGINT REFERENCES yeu_cau_mua(id) ON DELETE SET NULL;
ALTER TABLE yeu_cau_mua ADD COLUMN IF NOT EXISTS ma_ban VARCHAR(40);
ALTER TABLE don_mua ADD COLUMN IF NOT EXISTS ma_ban VARCHAR(40);
-- de xuat sinh tu du toan DU AN truoc day: ly_do 'Du toan du an <MA>' -> ma chuoi (chi ma, khong lay ten co dau cach)
UPDATE yeu_cau_mua SET ma_ban = left(btrim(substring(ly_do from 15)), 40)
WHERE ma_ban IS NULL AND ly_do LIKE 'Dự toán dự án %'
  AND substring(ly_do from 15) NOT LIKE '#%'
  AND position(' ' in btrim(substring(ly_do from 15))) = 0;
-- PO ke thua ma chuoi tu de xuat da sinh ra no
UPDATE don_mua d SET ma_ban = y.ma_ban
FROM yeu_cau_mua y
WHERE y.don_mua_id = d.id AND y.ma_ban IS NOT NULL AND d.ma_ban IS NULL;
