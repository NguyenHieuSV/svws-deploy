-- ============================================================
-- SVWS 20 — Thêm loại hàng HOA_CHAT (hóa chất) + seed hóa chất mẫu
-- Lưu ý: ALTER TYPE ... ADD VALUE phải chạy ngoài transaction dùng nó.
-- ============================================================

ALTER TYPE loai_hang ADD VALUE IF NOT EXISTS 'HOA_CHAT';

BEGIN;
INSERT INTO hang_hoa (ma,ten,loai,don_vi,gia_ban)
SELECT v.ma, v.ten, v.loai::loai_hang, v.don_vi, v.gia_ban FROM (VALUES
  ('HC-PAC','Hóa chất keo tụ PAC','HOA_CHAT','kg',18000),
  ('HC-NAOH','Xút NaOH 32%','HOA_CHAT','lít',9500),
  ('HC-ANTI','Antiscalant chống cáu cặn RO','HOA_CHAT','lít',85000),
  ('HC-CLO','Chlorine 70%','HOA_CHAT','kg',32000),
  ('HC-POLYMER','Polymer trợ lắng','HOA_CHAT','kg',62000)
) AS v(ma,ten,loai,don_vi,gia_ban)
WHERE NOT EXISTS (SELECT 1 FROM hang_hoa WHERE ma='HC-PAC');

INSERT INTO ton_kho (hang_hoa_id, so_luong, ton_min, ton_max)
SELECT h.id,
       CASE h.ma WHEN 'HC-PAC' THEN 320 WHEN 'HC-NAOH' THEN 60 WHEN 'HC-ANTI' THEN 25
                 WHEN 'HC-CLO' THEN 140 ELSE 0 END,
       CASE h.ma WHEN 'HC-PAC' THEN 100 WHEN 'HC-NAOH' THEN 80 WHEN 'HC-ANTI' THEN 40
                 WHEN 'HC-CLO' THEN 50 ELSE 30 END,
       1000
FROM hang_hoa h
WHERE h.loai='HOA_CHAT' AND NOT EXISTS (SELECT 1 FROM ton_kho t WHERE t.hang_hoa_id=h.id);
COMMIT;
