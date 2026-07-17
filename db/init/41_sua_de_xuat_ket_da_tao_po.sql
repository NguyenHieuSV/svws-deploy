-- Sửa dữ liệu kẹt: đề xuất mua có trạng thái DA_TAO_PO nhưng PO đã bị xóa
-- (cột don_mua_id đã về NULL do ON DELETE SET NULL, nhưng trang_thai vẫn kẹt
--  khiến đề xuất không xóa được và không tạo lại PO được).
-- Trả các đề xuất mồ côi này về DA_DUYET — đúng trạng thái "đã duyệt, chờ tạo PO".
UPDATE yeu_cau_mua
   SET trang_thai = 'DA_DUYET'
 WHERE trang_thai = 'DA_TAO_PO'
   AND don_mua_id IS NULL;
