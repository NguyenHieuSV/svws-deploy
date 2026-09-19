-- 124: Don ban duoc CEO / ADMIN / KTT cho BO QUA canh bao "da xuat HD / hoan thanh nhung chua co hoa don ban" (kem ly do)
CREATE TABLE IF NOT EXISTS don_bo_qua_hoa_don (
  don_hang_id BIGINT PRIMARY KEY,
  ly_do VARCHAR(300),
  nguoi_dung_id BIGINT,
  tao_luc TIMESTAMPTZ DEFAULT now()
);
