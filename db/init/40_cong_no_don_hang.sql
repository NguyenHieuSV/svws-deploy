-- Sales gắn công nợ với Mã đơn hàng bán (droplist lấy từ danh sách đơn hàng đã có PO/HĐ).
-- Ưu tiên dùng cột này; nếu trống thì lấy theo đơn hàng của hóa đơn gốc.
ALTER TABLE cong_no
    ADD COLUMN IF NOT EXISTS don_hang_id BIGINT REFERENCES don_hang(id) ON DELETE SET NULL;
