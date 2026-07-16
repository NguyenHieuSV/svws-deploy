-- ============================================================
-- SVWS 38 — Rà soát & cải thiện bộ KPI (chuyên gia QTNS):
--   (1) Thêm Biên lợi nhuận gộp cho TP_KD & NV_KD (tránh chạy doanh số bằng giảm giá)
--   (2) NV_KD: đổi "Công nợ quá hạn (triệu)" -> "Tỷ lệ công nợ quá hạn (%)"
--   (3) CEO: thêm "Dòng tiền hoạt động / kế hoạch"
--   (4) NV_THUE: thêm "Tỷ lệ khai thác thiết bị cho thuê"
--   Trọng số cân lại vẫn đủ 100% mỗi vị trí. Lịch sử đánh giá (danh_gia_ct)
--   lưu snapshot riêng nên không bị ảnh hưởng khi thay bộ KPI.
--   Idempotent: chỉ chạy khi chưa có KPI mới (guard theo TP_KD Biên lợi nhuận).
-- ============================================================
BEGIN;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM kpi_vi_tri
                 WHERE vai_tro='TP_KD' AND ten LIKE 'Biên lợi nhuận%') THEN

    DELETE FROM kpi_vi_tri WHERE vai_tro IN ('CEO','TP_KD','NV_KD','NV_THUE');

    INSERT INTO kpi_vi_tri (vai_tro,ten,don_vi,trong_so,muc_tieu,chieu,chu_ky,mo_ta,thu_tu) VALUES
      -- CEO (thêm Dòng tiền; cân lại 30/25/15/20/10)
      ('CEO','Doanh thu thực hiện / kế hoạch','%',30,100,'CAO','NAM','Tỷ lệ hoàn thành doanh thu năm',0),
      ('CEO','Lợi nhuận trước thuế / kế hoạch','%',25,100,'CAO','NAM','Hiệu quả lợi nhuận',1),
      ('CEO','Dòng tiền hoạt động / kế hoạch','%',15,100,'CAO','QUY','Thanh khoản & dòng tiền',2),
      ('CEO','Tỷ lệ hài lòng khách hàng trọng điểm','/5',20,4.5,'CAO','QUY','CSAT nhóm KH lớn',3),
      ('CEO','Sự cố quản trị/tuân thủ nghiêm trọng','vụ',10,0,'THAP','NAM','Càng ít càng tốt',4),

      -- TP_KD (thêm Biên lợi nhuận gộp; cân lại 30/15/25/15/15)
      ('TP_KD','Doanh số phòng / chỉ tiêu','%',30,100,'CAO','QUY','Hoàn thành chỉ tiêu phòng',0),
      ('TP_KD','Biên lợi nhuận gộp bình quân','%',15,25,'CAO','QUY','Chất lượng lợi nhuận đơn hàng (tránh giảm giá)',1),
      ('TP_KD','Tỷ lệ chuyển đổi cơ hội → đơn','%',25,30,'CAO','QUY','Hiệu quả phễu bán hàng',2),
      ('TP_KD','Số khách hàng mới ký hợp đồng','KH',15,8,'CAO','QUY','Mở rộng thị trường',3),
      ('TP_KD','Tỷ lệ báo giá quá hạn phản hồi','%',15,5,'THAP','THANG','Tốc độ phục vụ',4),

      -- NV_KD (thêm Biên lợi nhuận; công nợ -> %; cân lại 35/15/15/15/20)
      ('NV_KD','Doanh số cá nhân / chỉ tiêu','%',35,100,'CAO','THANG','Hoàn thành chỉ tiêu cá nhân',0),
      ('NV_KD','Biên lợi nhuận gộp cá nhân','%',15,25,'CAO','THANG','Chất lượng lợi nhuận đơn bán',1),
      ('NV_KD','Số báo giá gửi đi','báo giá',15,12,'CAO','THANG','Mức độ hoạt động',2),
      ('NV_KD','Số cơ hội mới đưa vào phễu','cơ hội',15,10,'CAO','THANG','Phát triển nguồn',3),
      ('NV_KD','Tỷ lệ công nợ quá hạn KH phụ trách','%',20,5,'THAP','THANG','Quản lý thu hồi (quá hạn / tổng phải thu)',4),

      -- NV_THUE (thêm Tỷ lệ khai thác thiết bị; cân lại 30/20/25/15/10)
      ('NV_THUE','Doanh thu cho thuê / chỉ tiêu','%',30,100,'CAO','THANG','Hoàn thành chỉ tiêu thuê',0),
      ('NV_THUE','Tỷ lệ khai thác thiết bị cho thuê','%',20,85,'CAO','THANG','Thiết bị đang cho thuê / tổng thiết bị',1),
      ('NV_THUE','Tỷ lệ thu đúng hạn tiền thuê','%',25,95,'CAO','THANG','Quản lý công nợ thuê',2),
      ('NV_THUE','Tỷ lệ tái ký hợp đồng','%',15,70,'CAO','QUY','Giữ khách thuê',3),
      ('NV_THUE','Số lần thiết bị hỏng do quản lý kém','lần',10,0,'THAP','QUY','Bảo quản thiết bị',4);

  END IF;
END $$;

COMMIT;
