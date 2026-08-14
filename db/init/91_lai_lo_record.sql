-- 91: Lãi/Lỗ Record — hệ thống tự ghi lãi/lỗ tổng mỗi ngày (bản ghi ngày cuối tháng = chốt tháng)
CREATE TABLE IF NOT EXISTS lai_lo_record (
  id BIGSERIAL PRIMARY KEY,
  ngay DATE UNIQUE,
  doanh_thu NUMERIC(18,0) DEFAULT 0,      -- tổng giá trị các đơn hàng bán
  chi_phi_don NUMERIC(18,0) DEFAULT 0,    -- tổng chi phí cho các đơn đó (TT mua + công nợ phải trả)
  lai_gop NUMERIC(18,0) DEFAULT 0,        -- doanh_thu - chi_phi_don
  chi_phi_khac NUMERIC(18,0) DEFAULT 0,   -- nhân sự, vận hành... (chi cố định/tháng x số tháng từ đầu năm)
  lai_lo NUMERIC(18,0) DEFAULT 0,         -- lai_gop - chi_phi_khac
  tao_luc TIMESTAMP
);
