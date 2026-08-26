-- 112: Bang luong theo MAU phan bo (T07.2026):
--   nhan_vien: loai_luong (THANG|NGAY - cong nhat), thuong_chuyen_can, pc_doc_hai (phan bo co dinh)
--   bang_luong: nghi_huong_luong, thuong_chuyen_can, pc_doc_hai, pc_cong_tac, thuong_htcv (theo ky)
--   tham_so_luong: tru_bh_nv (FALSE = khong tru BH vao luong NV - theo mau, DN ganh phan NV)
ALTER TABLE nhan_vien ADD COLUMN IF NOT EXISTS loai_luong VARCHAR(8) DEFAULT 'THANG';
ALTER TABLE nhan_vien ADD COLUMN IF NOT EXISTS thuong_chuyen_can NUMERIC(18,0) DEFAULT 0;
ALTER TABLE nhan_vien ADD COLUMN IF NOT EXISTS pc_doc_hai NUMERIC(18,0) DEFAULT 0;
ALTER TABLE bang_luong ADD COLUMN IF NOT EXISTS nghi_huong_luong NUMERIC(5,1) DEFAULT 0;
ALTER TABLE bang_luong ADD COLUMN IF NOT EXISTS thuong_chuyen_can NUMERIC(18,0) DEFAULT 0;
ALTER TABLE bang_luong ADD COLUMN IF NOT EXISTS pc_doc_hai NUMERIC(18,0) DEFAULT 0;
ALTER TABLE bang_luong ADD COLUMN IF NOT EXISTS pc_cong_tac NUMERIC(18,0) DEFAULT 0;
ALTER TABLE bang_luong ADD COLUMN IF NOT EXISTS thuong_htcv NUMERIC(18,0) DEFAULT 0;
ALTER TABLE tham_so_luong ADD COLUMN IF NOT EXISTS tru_bh_nv BOOLEAN DEFAULT FALSE;
