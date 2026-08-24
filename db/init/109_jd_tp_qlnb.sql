-- ============================================================
-- SVWS 109 — Bổ sung Mô tả công việc (JD) + KPI: Trưởng phòng Quản lý nội bộ (TP_QLNB)
-- Idempotent: JD ON CONFLICT DO NOTHING; KPI chỉ seed khi vị trí chưa có.
-- ============================================================
INSERT INTO mo_ta_cong_viec (vai_tro,chuc_danh,cap_bac,bao_cao_cho,muc_dich,trach_nhiem,quyen_han,yeu_cau) VALUES
  ('TP_QLNB','Trưởng phòng Quản lý nội bộ','Quản lý','Giám đốc','Bảo đảm bộ máy nội bộ vận hành đúng quy chế: nhân sự - hành chính, tài liệu, tuân thủ quy trình và kiểm soát chi tiêu trong hạn mức được giao.','["Quản lý nhân sự: duyệt chấm công, nghỉ phép, đăng ký OT; theo dõi hồ sơ lao động và đánh giá KPI định kỳ.", "Giám sát tuân thủ quy chế, quy trình nội bộ ở các phòng ban; phát hiện và đề xuất chấn chỉnh sai phạm.", "Phê duyệt đề xuất mua và đơn mua (PO) trong hạn mức được cấp (bảng hạn mức duyệt).", "Theo dõi, đối soát và điều chỉnh công nợ khách hàng khi phát hiện sai lệch số liệu.", "Quản lý kho tài liệu dùng chung: quy chế, biểu mẫu, hồ sơ pháp lý — cập nhật và phổ biến.", "Phối hợp kế toán trong kiểm kê định kỳ, kiểm soát chi phí hành chính - văn phòng."]','["Duyệt nghỉ phép, chấm công, OT của nhân viên (module Nhân sự).", "Duyệt đề xuất mua, PO trong hạn mức được cấp.", "Sửa số liệu công nợ khách hàng đã ghi (cùng CEO/ADMIN).", "Yêu cầu các phòng ban cung cấp hồ sơ phục vụ kiểm soát nội bộ."]','{"hoc_van": "Đại học (QTKD / Quản trị nhân lực / Kế toán / Luật).", "kinh_nghiem": "≥ 5 năm vận hành nội bộ hoặc HCNS, ≥ 2 năm quản lý.", "ky_nang": ["Kiểm soát nội bộ", "Quy chế - quy trình", "Quản trị nhân sự", "Kiểm soát chi phí", "Phối hợp liên phòng ban"]}')
ON CONFLICT (vai_tro) DO NOTHING;

INSERT INTO kpi_vi_tri (vai_tro,ten,don_vi,trong_so,muc_tieu,chieu,chu_ky,mo_ta,thu_tu)
SELECT * FROM (VALUES
  ('TP_QLNB','Tỷ lệ đề xuất/chứng từ xử lý trong 24h','%',25,95,'CAO','THANG','Tốc độ phê duyệt nghỉ phép, chấm công, đề xuất trong hạn mức',0),
  ('TP_QLNB','Số vi phạm quy chế/quy trình phát hiện muộn','lần',25,0,'THAP','THANG','Hiệu quả giám sát tuân thủ nội bộ',1),
  ('TP_QLNB','Chi phí hành chính so với ngân sách','%',25,100,'THAP','QUY','Kiểm soát chi tiêu nội bộ trong ngân sách',2),
  ('TP_QLNB','Sai lệch công nợ được xử lý dứt điểm trong kỳ','%',25,100,'CAO','THANG','Đối soát và làm sạch số liệu công nợ',3)
) AS v(vai_tro,ten,don_vi,trong_so,muc_tieu,chieu,chu_ky,mo_ta,thu_tu)
WHERE NOT EXISTS (SELECT 1 FROM kpi_vi_tri WHERE vai_tro='TP_QLNB');
