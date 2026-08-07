-- 83: Bảng THANH TOÁN (Kế toán → Thống kê thu–chi) — hàng đợi chờ lệnh ngân hàng
-- Tick hộp "Thanh toán" ở Các đơn hàng cần thanh toán → PO vào hàng đợi;
-- bấm "Cập nhật" sau khi ngân hàng chi thật → đổ vào form Biến động ngân hàng.
ALTER TABLE don_mua ADD COLUMN IF NOT EXISTS cho_lenh_bank BOOLEAN DEFAULT FALSE;
ALTER TABLE don_mua ADD COLUMN IF NOT EXISTS lenh_bank_tien NUMERIC(18,0) DEFAULT 0;
ALTER TABLE don_mua ADD COLUMN IF NOT EXISTS lenh_bank_luc TIMESTAMP;
