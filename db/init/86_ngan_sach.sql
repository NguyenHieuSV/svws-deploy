-- 86: Ngân sách thu/chi theo tháng (kế hoạch CEO đặt, so với thực tế) — Overall Financial
CREATE TABLE IF NOT EXISTS ngan_sach (
  id BIGSERIAL PRIMARY KEY,
  thang VARCHAR(7) NOT NULL UNIQUE,      -- 'YYYY-MM'
  thu_ke_hoach NUMERIC(18,0) DEFAULT 0,
  chi_ke_hoach NUMERIC(18,0) DEFAULT 0,
  ghi_chu VARCHAR(200)
);
