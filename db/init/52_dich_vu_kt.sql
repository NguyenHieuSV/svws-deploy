-- 52: Module DỊCH VỤ KỸ THUẬT (technical services registry + job tracking)
CREATE TABLE IF NOT EXISTS dich_vu_kt (
  id             BIGSERIAL PRIMARY KEY,
  ma             VARCHAR(40) UNIQUE,
  loai_dv        VARCHAR(30) NOT NULL,            -- SITE_SURVEY/CIP/CLEANING/MEMBRANE/MATERIAL/AUDIT
  chi_tiet_dv    VARCHAR(120),                    -- sub-type: RO/UF/MBR/Boiler/GAC...
  ten            VARCHAR(200),
  khach_hang_id  BIGINT REFERENCES khach_hang(id),
  du_an_id       BIGINT REFERENCES du_an(id),
  dia_diem       VARCHAR(200),
  thiet_bi       VARCHAR(200),
  nguoi_phu_trach VARCHAR(120),
  ngay_hen       DATE,
  ngay_bat_dau   DATE,
  ngay_ket_thuc  DATE,
  gia_tri        NUMERIC(18,0) DEFAULT 0,
  trang_thai     VARCHAR(20) NOT NULL DEFAULT 'KHAO_SAT',
  du_lieu_ky_thuat JSONB,
  bao_cao        TEXT,
  ghi_chu        TEXT,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Phân quyền module mới (idempotent)
INSERT INTO phan_quyen (vai_tro_id, module, muc)
SELECT vt.id, v.module, v.muc::muc_quyen
FROM (VALUES
  ('CEO','dich_vu_kt','DUYET'),
  ('TP_DA','dich_vu_kt','DUYET'),
  ('NV_DA','dich_vu_kt','THAO_TAC'),
  ('NV_KTH','dich_vu_kt','THAO_TAC'),
  ('KTT','dich_vu_kt','XEM'),
  ('NV_KT','dich_vu_kt','XEM'),
  ('ADMIN','dich_vu_kt','QUAN_TRI')
) AS v(ma, module, muc)
JOIN vai_tro vt ON vt.ma = v.ma
ON CONFLICT (vai_tro_id, module) DO UPDATE SET muc = EXCLUDED.muc;
