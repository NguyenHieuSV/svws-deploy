-- 82: Ngày duyệt thực tế của đề xuất mua hàng
ALTER TABLE yeu_cau_mua ADD COLUMN IF NOT EXISTS ngay_duyet DATE;
-- Truy hồi cho đề xuất đã duyệt trước đây: lấy ngày DUYỆT gần nhất trong nhật ký audit
UPDATE yeu_cau_mua y SET ngay_duyet = a.ngay
FROM (SELECT ban_ghi_id, MAX(thoi_gian)::date AS ngay
      FROM audit_log WHERE bang = 'yeu_cau_mua' AND hanh_dong = 'DUYET'
      GROUP BY ban_ghi_id) a
WHERE y.id = a.ban_ghi_id AND y.ngay_duyet IS NULL
  AND y.trang_thai IN ('DA_DUYET', 'DA_TAO_PO');
