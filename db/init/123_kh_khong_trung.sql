-- 123: Ghi nho cac cap KHACH HANG da duoc ket luan KHONG PHAI cung mot cong ty (cong cu Ra khach hang trung khong bao lai)
CREATE TABLE IF NOT EXISTS kh_khong_trung (
  a_id BIGINT NOT NULL,
  b_id BIGINT NOT NULL,
  nguoi_dung_id BIGINT,
  tao_luc TIMESTAMPTZ DEFAULT now(),
  PRIMARY KEY (a_id, b_id)
);
