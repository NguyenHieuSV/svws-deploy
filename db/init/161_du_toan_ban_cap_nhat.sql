-- 161 — 🕒 Dự toán hàng bán: giờ tạo + giờ sửa gần nhất (anh Hiếu 29/10/2026: Bảng lưu dự toán thêm cột «Cập nhật»,
--       dự toán vừa làm xếp lên trên). Từ nay app tự ghi cap_nhat_luc mỗi khi thêm / sửa / xóa dòng hoặc sửa tiêu đề
--       (SQLAlchemy before_flush trong app/models.py). Dữ liệu cũ: lấy từ audit_log (TAO / SUA / NAP… của du_toan_ban và
--       các dòng du_toan_ban_muc), không có thì theo cột ngay. Giờ quy về Việt Nam (naive) cho khớp với app.
ALTER TABLE du_toan_ban ADD COLUMN IF NOT EXISTS tao_luc      TIMESTAMP;
ALTER TABLE du_toan_ban ADD COLUMN IF NOT EXISTS cap_nhat_luc TIMESTAMP;

UPDATE du_toan_ban d SET tao_luc = COALESCE(
        (SELECT MIN(a.thoi_gian) AT TIME ZONE 'Asia/Ho_Chi_Minh' FROM audit_log a
          WHERE a.bang = 'du_toan_ban' AND a.ban_ghi_id = d.id),
        d.ngay::timestamp)
  WHERE d.tao_luc IS NULL;

UPDATE du_toan_ban d SET cap_nhat_luc = GREATEST(
        COALESCE((SELECT MAX(a.thoi_gian) AT TIME ZONE 'Asia/Ho_Chi_Minh' FROM audit_log a
                   WHERE a.bang = 'du_toan_ban' AND a.ban_ghi_id = d.id), d.tao_luc),
        COALESCE((SELECT MAX(a.thoi_gian) AT TIME ZONE 'Asia/Ho_Chi_Minh' FROM audit_log a
                   JOIN du_toan_ban_muc m ON m.id = a.ban_ghi_id
                   WHERE a.bang = 'du_toan_ban_muc' AND m.du_toan_id = d.id), d.tao_luc),
        d.tao_luc)
  WHERE d.cap_nhat_luc IS NULL;

CREATE INDEX IF NOT EXISTS ix_du_toan_ban_cap_nhat_luc ON du_toan_ban (cap_nhat_luc DESC);
