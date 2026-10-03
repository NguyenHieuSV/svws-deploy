-- 143: SAN PHAM NCC — noi thang toi FILE BAO GIA (tep_dinh_kem.doi_tuong = 'BAO_GIA_NCC_FILE') ma san pham duoc doc ra,
--      de bang Du toan hien link file bao gia o cot Ghi chu.
ALTER TABLE san_pham_ncc ADD COLUMN IF NOT EXISTS tep_bao_gia_id BIGINT;

-- Backfill: san pham AI nhap tu FILE bao gia — khop NCC + ten file (lay file moi nhat cung ten).
-- San pham doc tu EMAIL duoc do bu luc doc (app/routers/ncc.py _sp_tep_bao_gia).
UPDATE san_pham_ncc s
   SET tep_bao_gia_id = t.id
  FROM (SELECT DISTINCT ON (doi_tuong_id, ten_file) id, doi_tuong_id, ten_file
          FROM tep_dinh_kem
         WHERE doi_tuong = 'BAO_GIA_NCC_FILE'
         ORDER BY doi_tuong_id, ten_file, id DESC) t
 WHERE s.tep_bao_gia_id IS NULL
   AND t.doi_tuong_id = s.nha_cung_cap_id
   AND (position('AI nhập từ file ' || t.ten_file IN coalesce(s.ghi_chu, '')) > 0
        OR s.spec_nguon = left('AI · file ' || t.ten_file, 160));
