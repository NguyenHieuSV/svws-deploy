-- 121: Ghi vet moi khoan ghi 'da tra NCC' KHONG qua lenh chi ngan hang (CEO 18/09/2026 - bat buoc qua Duyet chi)
-- nguon: SUA_DOT_TT | XOA_DOT_TT | AI_NHAP | CAN_TRU (can tru tam ung - tien da tinh o lenh tam ung)
CREATE TABLE IF NOT EXISTS chi_ngoai_lenh (
  id BIGSERIAL PRIMARY KEY,
  don_mua_id BIGINT REFERENCES don_mua(id) ON DELETE SET NULL,
  cong_no_id BIGINT REFERENCES cong_no(id) ON DELETE SET NULL,
  so_tien NUMERIC(18,0) NOT NULL DEFAULT 0,
  ngay DATE NOT NULL DEFAULT CURRENT_DATE,
  nguon VARCHAR(20) NOT NULL,
  ly_do VARCHAR(300),
  nguoi_dung_id BIGINT,
  tao_luc TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_cnl_po ON chi_ngoai_lenh(don_mua_id);
CREATE INDEX IF NOT EXISTS idx_cnl_cn ON chi_ngoai_lenh(cong_no_id);
