-- Ngày nhập hàng vào kho (nhập tay ở form thêm hàng hóa; phiếu nhập thực tế sẽ ưu tiên hơn khi hiển thị)
ALTER TABLE hang_hoa ADD COLUMN IF NOT EXISTS ngay_nhap date;
