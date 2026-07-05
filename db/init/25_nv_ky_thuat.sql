-- ============================================================
-- SVWS 25 — Vị trí mới: NV Kỹ thuật (NV_KTH)
--   vai_tro + phan_quyen mặc định + Mô tả công việc (JD) + bộ KPI.
-- Idempotent: ON CONFLICT DO NOTHING / WHERE NOT EXISTS.
-- ============================================================
BEGIN;

INSERT INTO vai_tro (ma, ten) VALUES ('NV_KTH', 'NV Kỹ thuật')
ON CONFLICT (ma) DO NOTHING;

-- Quyền mặc định: làm kỹ thuật dự án & trạm cho thuê, xem kho/bán hàng
INSERT INTO phan_quyen (vai_tro_id, module, muc)
SELECT vt.id, v.module, v.muc::muc_quyen
FROM (VALUES
  ('NV_KTH','du_an','THAO_TAC'),
  ('NV_KTH','cho_thue','THAO_TAC'),
  ('NV_KTH','kho','XEM'),
  ('NV_KTH','ban_hang','XEM'),
  ('NV_KTH','tai_lieu','THAO_TAC'),
  ('NV_KTH','dashboard','XEM')
) AS v(ma, module, muc)
JOIN vai_tro vt ON vt.ma = v.ma
ON CONFLICT (vai_tro_id, module) DO NOTHING;

INSERT INTO mo_ta_cong_viec (vai_tro,chuc_danh,cap_bac,bao_cao_cho,muc_dich,trach_nhiem,quyen_han,yeu_cau) VALUES
  ('NV_KTH','Nhân viên Kỹ thuật','Nhân viên','Trưởng dự án / Giám đốc',
   'Thực hiện lắp đặt, vận hành, bảo trì và xử lý sự cố các hệ thống xử lý nước/nước thải tại công trình và các trạm cho thuê; hỗ trợ kỹ thuật cho kinh doanh và dự án.',
   '["Lắp đặt, đấu nối thiết bị hệ thống xử lý nước theo bản vẽ thiết kế.", "Vận hành thử nghiệm, hiệu chỉnh thông số hệ thống (pH, EC, lọc, RO, MBR...).", "Bảo trì định kỳ thiết bị tại công trình và trạm cho thuê theo lịch.", "Xử lý sự cố kỹ thuật, khắc phục nhanh để bảo đảm chất lượng nước đầu ra.", "Ghi nhật ký kỹ thuật, cập nhật tài liệu và bản vẽ hoàn công.", "Hỗ trợ khảo sát hiện trường và tư vấn kỹ thuật cho báo giá của kinh doanh."]',
   '["Đề xuất vật tư, thiết bị thay thế phục vụ bảo trì/sửa chữa.", "Ghi nhận khối lượng thi công, nhật ký công trường (chờ duyệt).", "Tạm dừng vận hành khi phát hiện nguy cơ mất an toàn và báo cáo ngay."]',
   '{"hoc_van": "Cao đẳng/Đại học (Kỹ thuật môi trường, Điện, Cơ khí, Tự động hóa).", "kinh_nghiem": "≥ 1 năm lắp đặt/vận hành hệ thống xử lý nước.", "ky_nang": ["Đọc bản vẽ P&ID", "Điện công nghiệp cơ bản", "Vận hành RO/MBR/EC", "An toàn lao động & PCCC"]}')
ON CONFLICT (vai_tro) DO NOTHING;

INSERT INTO kpi_vi_tri (vai_tro,ten,don_vi,trong_so,muc_tieu,chieu,chu_ky,mo_ta,thu_tu)
SELECT * FROM (VALUES
  ('NV_KTH','Hoàn thành lệnh bảo trì đúng hạn','%',30,95,'CAO','THANG','Số lệnh bảo trì xong đúng lịch / tổng số',0),
  ('NV_KTH','Thời gian xử lý sự cố trung bình','giờ',25,8,'THAP','THANG','Từ lúc tiếp nhận đến khi khắc phục xong',1),
  ('NV_KTH','Chất lượng nước sau xử lý đạt chuẩn','%',30,100,'CAO','THANG','Số mẫu đạt QCVN / tổng số mẫu đo',2),
  ('NV_KTH','Sự cố an toàn lao động','vụ',15,0,'THAP','QUY','Càng ít càng tốt',3)
) AS v(vai_tro,ten,don_vi,trong_so,muc_tieu,chieu,chu_ky,mo_ta,thu_tu)
WHERE NOT EXISTS (SELECT 1 FROM kpi_vi_tri WHERE vai_tro='NV_KTH');

COMMIT;
