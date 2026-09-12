-- 118: BOQ du an lien ket thang toi hang hoa kho (khop ten mo -> gan id; khong phu thuoc chinh ta ten)
ALTER TABLE du_an_du_toan ADD COLUMN IF NOT EXISTS hang_hoa_id BIGINT REFERENCES hang_hoa(id) ON DELETE SET NULL;
-- backfill: dong BOQ co ten trung dung mot mat hang trong kho
UPDATE du_an_du_toan d SET hang_hoa_id = h.id
FROM hang_hoa h
WHERE d.hang_hoa_id IS NULL AND lower(btrim(h.ten)) = lower(btrim(d.ten))
  AND h.id = (SELECT min(h2.id) FROM hang_hoa h2 WHERE lower(btrim(h2.ten)) = lower(btrim(d.ten)));
