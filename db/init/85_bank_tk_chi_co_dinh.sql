-- 85: Tài khoản ngân hàng (số dư đầu kỳ) + Chi cố định định kỳ — phục vụ Số dư & Lịch dòng tiền (Overall Financial)
CREATE TABLE IF NOT EXISTS bank_tai_khoan (
  id BIGSERIAL PRIMARY KEY,
  ten VARCHAR(60) NOT NULL,
  so_tk VARCHAR(40),
  so_du_dau NUMERIC(18,0) DEFAULT 0,
  ngay_du_dau DATE DEFAULT CURRENT_DATE,
  ghi_chu VARCHAR(200)
);
CREATE TABLE IF NOT EXISTS chi_co_dinh (
  id BIGSERIAL PRIMARY KEY,
  ten VARCHAR(120) NOT NULL,
  so_tien NUMERIC(18,0) DEFAULT 0,
  ngay_trong_thang SMALLINT DEFAULT 5,
  dang_ap_dung BOOLEAN DEFAULT TRUE,
  ghi_chu VARCHAR(200)
);
