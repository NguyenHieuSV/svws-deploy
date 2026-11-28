-- 172 — Tự tải hóa đơn (mig 171): trả lại lượt thử cho các dòng hàng chờ bị ghi «lỗi» CHỈ vì cổng MISA meInvoice giới hạn
-- số lần gọi (HTTP 429) trong đợt chạy hàng loạt 28/11/2026. Đây không phải lỗi của hóa đơn: các dòng này chưa tải được
-- file nào, số liệu (tiền, số hóa đơn, NCC) không hề bị đổi; chỉ 3 cột theo dõi việc tải bị ghi sai nên app thôi không thử nữa.
-- Từ bản này app không tính lượt thử khi cổng trả 429 / 502 / 503 / 504 (app/hddt_tai_ve.py · TamNgung).
UPDATE kt_hoa_don_cho
   SET tai_lan = 0, tai_tt = NULL, tai_ghi_chu = NULL
 WHERE tai_tt = 'LOI' AND tai_ghi_chu LIKE '%HTTP 429%';
