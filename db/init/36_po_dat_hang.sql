-- Xác nhận đặt hàng PO: sau khi xác nhận, PO vào danh sách CHỜ NHẬP KHO
-- (Kho hàng → Nhập/Xuất) để thủ kho tạo phiếu nhập khi hàng về
ALTER TABLE don_mua ADD COLUMN IF NOT EXISTS da_dat_hang BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE don_mua ADD COLUMN IF NOT EXISTS ngay_dat_hang DATE;
