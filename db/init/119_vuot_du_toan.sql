-- 119: Kiem soat de xuat / PO theo du toan — "chan va cho duyet" (CEO 13/09/2026)
-- vuot_du_toan: ly do vuot / ngoai du toan (NULL = trong du toan); ban ghi co co chi CEO/ADMIN duyet
ALTER TABLE yeu_cau_mua ADD COLUMN IF NOT EXISTS vuot_du_toan VARCHAR(300);
ALTER TABLE don_mua ADD COLUMN IF NOT EXISTS vuot_du_toan VARCHAR(300);
