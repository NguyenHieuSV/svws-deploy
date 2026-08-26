-- ============================================================
-- SVWS 111 — Hoàn thiện JD & KPI cho đủ 16 vị trí:
--   (a) TP_QLNB: nâng yeu_cau lên chuẩn "chuyên nghiệp" như 15 vị trí khác
--       (bổ sung chung_chi · dieu_kien · tuan_thu — BLLĐ 45/2019, ATVSLĐ 84/2015).
--       Chỉ chạy khi chưa có (giữ nguyên nếu đã chỉnh tay trong app).
--   (b) NV_KT: bổ sung KPI thứ 4 (đủ 4 KPI · tổng trọng số 100%) — chỉ thay khi
--       vẫn còn bộ 3 KPI gốc, không đè bộ KPI đã chỉnh tay.
-- ============================================================

UPDATE mo_ta_cong_viec SET
 yeu_cau=$jd${"hoc_van":"Đại học chuyên ngành Quản trị kinh doanh, Quản trị nhân lực, Kế toán hoặc Luật.","kinh_nghiem":"≥ 5 năm vận hành nội bộ hoặc hành chính - nhân sự, trong đó ≥ 2 năm quản lý.","ky_nang":["Kiểm soát nội bộ","Xây dựng & giám sát quy chế - quy trình","Quản trị nhân sự","Kiểm soát chi phí","Phối hợp liên phòng ban"],"chung_chi":"Ưu tiên chứng chỉ quản trị nhân sự (HRM) hoặc kiểm soát nội bộ.","dieu_kien":["Thời giờ làm việc theo BLLĐ 2019: 8 giờ/ngày, không quá 48 giờ/tuần.","Địa điểm: trụ sở 448 Võ Văn Tần, P. Bàn Cờ, TP.HCM; đi xưởng An Phú Đông khi kiểm kê, kiểm soát.","Được cấp phương tiện làm việc và tài khoản hệ thống theo phân quyền TP_QLNB.","Tham gia BHXH, BHYT, BHTN đầy đủ; khám sức khỏe định kỳ; nghỉ phép năm theo luật."],"tuan_thu":["Chấp hành BLLĐ 45/2019/QH14 và Luật ATVSLĐ 84/2015/QH13 khi tổ chức lao động, chấm công, nghỉ phép.","Bảo mật dữ liệu nhân sự, lương thưởng và bí mật kinh doanh theo Điều 21 BLLĐ.","Tách vai đề nghị / phê duyệt: không tự duyệt khoản do chính mình đề nghị.","Chấp hành nội quy lao động, quy chế tài chính và hạn mức duyệt được cấp."]}$jd$,
 cap_nhat_luc=now()
WHERE vai_tro='TP_QLNB' AND (yeu_cau IS NULL OR yeu_cau NOT LIKE '%tuan_thu%');

-- (b) NV_KT: thay bộ 3 KPI gốc bằng bộ 4 KPI (tổng 100%) — giữ nguyên nếu đã chỉnh tay
DELETE FROM kpi_vi_tri WHERE vai_tro='NV_KT'
  AND (SELECT COUNT(*) FROM kpi_vi_tri k2 WHERE k2.vai_tro='NV_KT') = 3;
INSERT INTO kpi_vi_tri (vai_tro,ten,don_vi,trong_so,muc_tieu,chieu,chu_ky,mo_ta,thu_tu)
SELECT * FROM (VALUES
  ('NV_KT','Chứng từ hạch toán đúng hạn','%',30,98,'CAO','THANG','Kịp thời ghi sổ hóa đơn, phiếu, bút toán',0),
  ('NV_KT','Sai sót hạch toán bị điều chỉnh','lần',25,1,'THAP','THANG','Độ chính xác số liệu kế toán',1),
  ('NV_KT','Tỷ lệ đối chiếu công nợ hoàn tất','%',25,100,'CAO','THANG','Đối chiếu công nợ khách / NCC đầy đủ',2),
  ('NV_KT','Phiếu thu-chi & lệnh ✔ Đã chi xử lý trong 24h','%',20,95,'CAO','THANG','Tốc độ xử lý dòng tiền, không treo phiếu/lệnh',3)
) AS v(vai_tro,ten,don_vi,trong_so,muc_tieu,chieu,chu_ky,mo_ta,thu_tu)
WHERE NOT EXISTS (SELECT 1 FROM kpi_vi_tri WHERE vai_tro='NV_KT');
