-- 144: PHAN TICH DU LIEU (Overall Financial, chi CEO) — luu ban NHAN DINH AI (4 chuyen gia) de mo tab khong phai goi lai AI.
CREATE TABLE IF NOT EXISTS phan_tich_ai (
  id BIGSERIAL PRIMARY KEY,
  tao_luc TIMESTAMP,
  nguoi_dung_id BIGINT,
  mo_hinh VARCHAR(60),
  ket_qua JSONB NOT NULL
);
