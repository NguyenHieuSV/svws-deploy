-- ============================================================
-- SVWS 17 — Mô tả công việc (JD) & KPI theo vị trí + đánh giá theo kỳ
-- Idempotent: JD ON CONFLICT DO NOTHING; KPI seed chỉ khi vị trí chưa có.
-- ============================================================
BEGIN;

CREATE TABLE IF NOT EXISTS mo_ta_cong_viec (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  vai_tro VARCHAR(20) UNIQUE NOT NULL,
  chuc_danh VARCHAR(150) NOT NULL,
  cap_bac VARCHAR(40),
  bao_cao_cho VARCHAR(40),
  muc_dich TEXT,
  trach_nhiem TEXT,
  quyen_han TEXT,
  yeu_cau TEXT,
  cap_nhat_luc TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS kpi_vi_tri (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  vai_tro VARCHAR(20) NOT NULL,
  ten VARCHAR(200) NOT NULL,
  don_vi VARCHAR(30),
  trong_so NUMERIC(5,2) DEFAULT 0,
  muc_tieu NUMERIC(18,2),
  chieu VARCHAR(8) DEFAULT 'CAO',
  chu_ky VARCHAR(8) DEFAULT 'THANG',
  mo_ta VARCHAR(300),
  thu_tu INT DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_kpi_vai_tro ON kpi_vi_tri(vai_tro);

CREATE TABLE IF NOT EXISTS danh_gia_ky (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  nhan_vien_id BIGINT NOT NULL REFERENCES nhan_vien(id) ON DELETE CASCADE,
  vai_tro VARCHAR(20),
  loai_ky VARCHAR(8) NOT NULL,
  ky VARCHAR(12) NOT NULL,
  tong_diem NUMERIC(6,2) DEFAULT 0,
  xep_loai VARCHAR(2),
  nhan_xet TEXT,
  nguoi_danh_gia BIGINT REFERENCES nhan_vien(id),
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_dgk_loai ON danh_gia_ky(loai_ky, ky);

CREATE TABLE IF NOT EXISTS danh_gia_ct (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  danh_gia_id BIGINT NOT NULL REFERENCES danh_gia_ky(id) ON DELETE CASCADE,
  kpi_id BIGINT,
  ten VARCHAR(200) NOT NULL,
  trong_so NUMERIC(5,2) DEFAULT 0,
  muc_tieu NUMERIC(18,2),
  gia_tri_thuc NUMERIC(18,2),
  phan_tram_dat NUMERIC(6,2),
  diem NUMERIC(6,2) DEFAULT 0
);


INSERT INTO mo_ta_cong_viec (vai_tro,chuc_danh,cap_bac,bao_cao_cho,muc_dich,trach_nhiem,quyen_han,yeu_cau) VALUES
  ('CEO','Giám đốc điều hành','Điều hành','HĐTV / Chủ sở hữu','Chịu trách nhiệm cao nhất về định hướng chiến lược, kết quả kinh doanh và sự phát triển bền vững của công ty trong lĩnh vực xử lý nước, nước thải và khí thải.','["Hoạch định chiến lược, mục tiêu năm và phân bổ nguồn lực cho các phòng ban.", "Phê duyệt hợp đồng, đầu tư, chính sách giá và các quyết định vượt hạn mức của cấp dưới.", "Phê duyệt phân quyền hệ thống và bổ nhiệm vị trí (Overall Operation).", "Giám sát dòng tiền, hiệu quả tài chính và quản trị rủi ro toàn công ty.", "Phát triển quan hệ đối tác chiến lược, khách hàng trọng điểm và thương hiệu.", "Ký duyệt cuối bảng lương và các báo cáo tài chính trọng yếu."]','["Toàn quyền phê duyệt mọi nghiệp vụ và phân quyền.", "Quyết định tuyển dụng, bổ nhiệm, miễn nhiệm cấp quản lý.", "Đại diện pháp luật của công ty."]','{"hoc_van": "Đại học trở lên (Kỹ thuật môi trường / QTKD).", "kinh_nghiem": "≥ 10 năm, ≥ 5 năm quản lý cấp cao.", "ky_nang": ["Tư duy chiến lược", "Quản trị tài chính", "Lãnh đạo", "Đàm phán cấp cao"]}')
ON CONFLICT (vai_tro) DO NOTHING;

INSERT INTO kpi_vi_tri (vai_tro,ten,don_vi,trong_so,muc_tieu,chieu,chu_ky,mo_ta,thu_tu)
SELECT * FROM (VALUES
  ('CEO','Doanh thu thực hiện / kế hoạch','%',35,100,'CAO','NAM','Tỷ lệ hoàn thành doanh thu năm',0),
  ('CEO','Lợi nhuận trước thuế / kế hoạch','%',30,100,'CAO','NAM','Hiệu quả lợi nhuận',1),
  ('CEO','Tỷ lệ hài lòng khách hàng trọng điểm','/5',20,4.5,'CAO','QUY','CSAT nhóm KH lớn',2),
  ('CEO','Sự cố quản trị/tuân thủ nghiêm trọng','vụ',15,0,'THAP','NAM','Càng ít càng tốt',3)
) AS v(vai_tro,ten,don_vi,trong_so,muc_tieu,chieu,chu_ky,mo_ta,thu_tu)
WHERE NOT EXISTS (SELECT 1 FROM kpi_vi_tri WHERE vai_tro='CEO');

INSERT INTO mo_ta_cong_viec (vai_tro,chuc_danh,cap_bac,bao_cao_cho,muc_dich,trach_nhiem,quyen_han,yeu_cau) VALUES
  ('TP_KD','Trưởng Phòng Kinh doanh','Quản lý','Giám đốc','Dẫn dắt đội ngũ kinh doanh đạt mục tiêu doanh số, phát triển thị trường giải pháp xử lý nước/khí và quản lý phễu cơ hội.','["Lập và triển khai kế hoạch kinh doanh theo quý/năm; phân bổ chỉ tiêu cho nhân viên.", "Phê duyệt báo giá trong hạn mức; kiểm soát chính sách giá và chiết khấu.", "Quản lý phễu cơ hội, dự báo doanh số và tỷ lệ chuyển đổi.", "Phát triển khách hàng lớn, đối tác và kênh phân phối.", "Huấn luyện, kèm cặp và đánh giá đội ngũ kinh doanh & CRM.", "Phối hợp Dự án/Cung ứng bảo đảm khả thi kỹ thuật và tiến độ giao hàng."]','["Duyệt báo giá và đơn hàng trong hạn mức được giao.", "Phân bổ và điều chỉnh chỉ tiêu nội bộ phòng.", "Đề xuất chính sách giá, khuyến mãi."]','{"hoc_van": "Đại học (Kỹ thuật/Kinh tế).", "kinh_nghiem": "≥ 5 năm KD, ≥ 2 năm quản lý đội.", "ky_nang": ["Bán giải pháp B2B", "Quản lý đội ngũ", "Dự báo & phân tích", "Đàm phán hợp đồng"]}')
ON CONFLICT (vai_tro) DO NOTHING;

INSERT INTO kpi_vi_tri (vai_tro,ten,don_vi,trong_so,muc_tieu,chieu,chu_ky,mo_ta,thu_tu)
SELECT * FROM (VALUES
  ('TP_KD','Doanh số phòng / chỉ tiêu','%',40,100,'CAO','QUY','Hoàn thành chỉ tiêu phòng',0),
  ('TP_KD','Tỷ lệ chuyển đổi cơ hội → đơn','%',25,30,'CAO','QUY','Hiệu quả phễu bán hàng',1),
  ('TP_KD','Số khách hàng mới ký hợp đồng','KH',20,8,'CAO','QUY','Mở rộng thị trường',2),
  ('TP_KD','Tỷ lệ báo giá quá hạn phản hồi','%',15,5,'THAP','THANG','Tốc độ phục vụ',3)
) AS v(vai_tro,ten,don_vi,trong_so,muc_tieu,chieu,chu_ky,mo_ta,thu_tu)
WHERE NOT EXISTS (SELECT 1 FROM kpi_vi_tri WHERE vai_tro='TP_KD');

INSERT INTO mo_ta_cong_viec (vai_tro,chuc_danh,cap_bac,bao_cao_cho,muc_dich,trach_nhiem,quyen_han,yeu_cau) VALUES
  ('NV_KD','Nhân viên Kinh doanh','Nhân viên','Trưởng P. Kinh doanh','Tìm kiếm, tư vấn và chốt hợp đồng giải pháp xử lý nước/nước thải/khí thải; chăm sóc danh mục khách hàng được giao.','["Khai thác khách hàng tiềm năng, khảo sát nhu cầu và lập báo giá.", "Tư vấn giải pháp kỹ thuật phù hợp phối hợp bộ phận Dự án.", "Theo dõi cơ hội trên phễu, cập nhật trạng thái và đẩy nhanh chốt đơn.", "Lập hợp đồng, theo dõi thanh toán và công nợ khách hàng phụ trách.", "Cập nhật đầy đủ thông tin khách hàng, liên lạc và phản hồi vào CRM."]','["Lập báo giá, đơn hàng (chờ cấp trên duyệt).", "Đề xuất chiết khấu trong khung cho phép."]','{"hoc_van": "Cao đẳng/Đại học.", "kinh_nghiem": "≥ 1 năm bán hàng kỹ thuật (ưu tiên ngành nước/môi trường).", "ky_nang": ["Tư vấn giải pháp", "Giao tiếp", "Lập báo giá", "Chăm sóc khách hàng"]}')
ON CONFLICT (vai_tro) DO NOTHING;

INSERT INTO kpi_vi_tri (vai_tro,ten,don_vi,trong_so,muc_tieu,chieu,chu_ky,mo_ta,thu_tu)
SELECT * FROM (VALUES
  ('NV_KD','Doanh số cá nhân / chỉ tiêu','%',45,100,'CAO','THANG','Hoàn thành chỉ tiêu cá nhân',0),
  ('NV_KD','Số báo giá gửi đi','báo giá',20,12,'CAO','THANG','Mức độ hoạt động',1),
  ('NV_KD','Số cơ hội mới đưa vào phễu','cơ hội',20,10,'CAO','THANG','Phát triển nguồn',2),
  ('NV_KD','Công nợ quá hạn KH phụ trách','triệu',15,0,'THAP','THANG','Quản lý thu hồi',3)
) AS v(vai_tro,ten,don_vi,trong_so,muc_tieu,chieu,chu_ky,mo_ta,thu_tu)
WHERE NOT EXISTS (SELECT 1 FROM kpi_vi_tri WHERE vai_tro='NV_KD');

INSERT INTO mo_ta_cong_viec (vai_tro,chuc_danh,cap_bac,bao_cao_cho,muc_dich,trach_nhiem,quyen_han,yeu_cau) VALUES
  ('NV_CRM','Nhân viên Chăm sóc Khách hàng / CRM','Nhân viên','Trưởng P. Kinh doanh','Duy trì quan hệ và sự hài lòng của khách hàng sau bán; xử lý phản hồi, khiếu nại và chăm sóc định kỳ.','["Lập và thực hiện lịch chăm sóc sau bán (+7/+30 ngày) cho khách hàng.", "Tiếp nhận, phân loại và xử lý khiếu nại theo SLA 24h.", "Ghi nhận CSAT, tổng hợp phản hồi và đề xuất cải tiến dịch vụ.", "Phân loại khách hàng ABC và cập nhật hồ sơ 360°.", "Phối hợp Dự án/Kỹ thuật xử lý sự cố bảo hành."]','["Tạo và đóng việc chăm sóc, ghi nhận khiếu nại.", "Đề xuất ưu đãi giữ chân khách hàng."]','{"hoc_van": "Cao đẳng/Đại học.", "kinh_nghiem": "≥ 1 năm CSKH.", "ky_nang": ["Lắng nghe & xử lý khiếu nại", "Giao tiếp", "Quản lý thời gian", "CRM"]}')
ON CONFLICT (vai_tro) DO NOTHING;

INSERT INTO kpi_vi_tri (vai_tro,ten,don_vi,trong_so,muc_tieu,chieu,chu_ky,mo_ta,thu_tu)
SELECT * FROM (VALUES
  ('NV_CRM','Điểm hài lòng CSAT','/5',35,4.5,'CAO','THANG','Bình quân CSAT',0),
  ('NV_CRM','Tỷ lệ khiếu nại xử lý đúng SLA 24h','%',30,95,'CAO','THANG','Tuân thủ SLA',1),
  ('NV_CRM','Tỷ lệ hoàn thành lịch chăm sóc','%',20,90,'CAO','THANG','Chuyên cần chăm sóc',2),
  ('NV_CRM','Tỷ lệ khách hàng rời bỏ','%',15,5,'THAP','QUY','Giữ chân khách hàng',3)
) AS v(vai_tro,ten,don_vi,trong_so,muc_tieu,chieu,chu_ky,mo_ta,thu_tu)
WHERE NOT EXISTS (SELECT 1 FROM kpi_vi_tri WHERE vai_tro='NV_CRM');

INSERT INTO mo_ta_cong_viec (vai_tro,chuc_danh,cap_bac,bao_cao_cho,muc_dich,trach_nhiem,quyen_han,yeu_cau) VALUES
  ('TP_CU','Trưởng Phòng Cung ứng & Kho','Quản lý','Giám đốc','Bảo đảm cung ứng vật tư/thiết bị đúng tiến độ, chi phí tối ưu và quản trị tồn kho hiệu quả.','["Lập kế hoạch mua sắm, phê duyệt đề xuất mua và đơn mua (PO) trong hạn mức.", "Đánh giá, lựa chọn và quản lý nhà cung cấp; đàm phán giá và điều khoản.", "Kiểm soát định mức tồn kho min/max, vòng quay tồn và giá trị tồn.", "Phê duyệt điều chỉnh tồn sau kiểm kê.", "Phối hợp Dự án bảo đảm vật tư đúng tiến độ thi công."]','["Duyệt đề xuất mua, PO trong hạn mức.", "Phê duyệt điều chỉnh kiểm kê kho.", "Quyết định lựa chọn NCC trong danh mục."]','{"hoc_van": "Đại học (Kỹ thuật/Logistics/QTKD).", "kinh_nghiem": "≥ 5 năm cung ứng, ≥ 2 năm quản lý.", "ky_nang": ["Đàm phán NCC", "Quản trị tồn kho", "Kiểm soát chi phí", "Lập kế hoạch"]}')
ON CONFLICT (vai_tro) DO NOTHING;

INSERT INTO kpi_vi_tri (vai_tro,ten,don_vi,trong_so,muc_tieu,chieu,chu_ky,mo_ta,thu_tu)
SELECT * FROM (VALUES
  ('TP_CU','Tỷ lệ giao hàng đúng hạn của NCC','%',30,95,'CAO','THANG','Đúng tiến độ cung ứng',0),
  ('TP_CU','Tiết kiệm chi phí mua so với dự toán','%',25,5,'CAO','QUY','Hiệu quả mua sắm',1),
  ('TP_CU','Vòng quay tồn kho','lần/năm',25,6,'CAO','QUY','Hiệu quả tồn kho',2),
  ('TP_CU','Số lần thiếu vật tư gây gián đoạn','lần',20,0,'THAP','THANG','Bảo đảm sẵn sàng',3)
) AS v(vai_tro,ten,don_vi,trong_so,muc_tieu,chieu,chu_ky,mo_ta,thu_tu)
WHERE NOT EXISTS (SELECT 1 FROM kpi_vi_tri WHERE vai_tro='TP_CU');

INSERT INTO mo_ta_cong_viec (vai_tro,chuc_danh,cap_bac,bao_cao_cho,muc_dich,trach_nhiem,quyen_han,yeu_cau) VALUES
  ('NV_MUA','Nhân viên Mua hàng / NCC','Nhân viên','Trưởng P. Cung ứng & Kho','Thực hiện mua sắm vật tư, thiết bị đúng yêu cầu kỹ thuật, tiến độ và chi phí; quản lý hồ sơ nhà cung cấp.','["Xử lý đề xuất mua, phát hành RFQ và so sánh báo giá NCC.", "Lập đơn mua (PO), theo dõi giao hàng và đối chiếu nhận hàng.", "Cập nhật hồ sơ, đánh giá và bảng giá nhà cung cấp.", "Phối hợp Kho nhập hàng và Kế toán đối chiếu công nợ NCC."]','["Phát hành RFQ, lập PO (chờ duyệt).", "Đề xuất NCC mới."]','{"hoc_van": "Cao đẳng/Đại học.", "kinh_nghiem": "≥ 1 năm mua hàng.", "ky_nang": ["So sánh báo giá", "Đàm phán", "Quản lý hồ sơ NCC", "Tin học văn phòng"]}')
ON CONFLICT (vai_tro) DO NOTHING;

INSERT INTO kpi_vi_tri (vai_tro,ten,don_vi,trong_so,muc_tieu,chieu,chu_ky,mo_ta,thu_tu)
SELECT * FROM (VALUES
  ('NV_MUA','Tỷ lệ PO xử lý đúng hạn','%',35,95,'CAO','THANG','Tốc độ xử lý',0),
  ('NV_MUA','Tiết kiệm chi phí qua đàm phán','%',30,4,'CAO','QUY','Hiệu quả đàm phán',1),
  ('NV_MUA','Số NCC mới đạt chuẩn bổ sung','NCC',15,2,'CAO','QUY','Đa dạng nguồn cung',2),
  ('NV_MUA','Sai sót đơn mua','lần',20,0,'THAP','THANG','Chính xác chứng từ',3)
) AS v(vai_tro,ten,don_vi,trong_so,muc_tieu,chieu,chu_ky,mo_ta,thu_tu)
WHERE NOT EXISTS (SELECT 1 FROM kpi_vi_tri WHERE vai_tro='NV_MUA');

INSERT INTO mo_ta_cong_viec (vai_tro,chuc_danh,cap_bac,bao_cao_cho,muc_dich,trach_nhiem,quyen_han,yeu_cau) VALUES
  ('THUKHO','Thủ kho','Nhân viên','Trưởng P. Cung ứng & Kho','Quản lý nhập–xuất–tồn chính xác, an toàn và đúng quy trình; bảo quản hàng hóa trong kho.','["Lập phiếu nhập/xuất kho và cập nhật tồn theo thời gian thực.", "Sắp xếp, bảo quản hàng hóa và bảo đảm an toàn kho.", "Thực hiện kiểm kê định kỳ, đối chiếu sổ sách – thực tế.", "Theo dõi cảnh báo tồn tối thiểu, đề xuất bổ sung kịp thời."]','["Lập phiếu nhập/xuất kho.", "Đề xuất điều chỉnh tồn (chờ duyệt)."]','{"hoc_van": "Trung cấp/Cao đẳng.", "kinh_nghiem": "≥ 1 năm thủ kho.", "ky_nang": ["Quản lý kho", "Cẩn thận chính xác", "Phần mềm kho", "An toàn lao động"]}')
ON CONFLICT (vai_tro) DO NOTHING;

INSERT INTO kpi_vi_tri (vai_tro,ten,don_vi,trong_so,muc_tieu,chieu,chu_ky,mo_ta,thu_tu)
SELECT * FROM (VALUES
  ('THUKHO','Độ chính xác tồn kho (sổ vs thực tế)','%',40,99,'CAO','THANG','Khớp kiểm kê',0),
  ('THUKHO','Tỷ lệ phiếu nhập/xuất kịp thời','%',30,98,'CAO','THANG','Cập nhật đúng lúc',1),
  ('THUKHO','Số lần để hàng dưới min không cảnh báo','lần',15,0,'THAP','THANG','Chủ động cảnh báo',2),
  ('THUKHO','Sự cố mất mát/hư hỏng kho','vụ',15,0,'THAP','QUY','An toàn bảo quản',3)
) AS v(vai_tro,ten,don_vi,trong_so,muc_tieu,chieu,chu_ky,mo_ta,thu_tu)
WHERE NOT EXISTS (SELECT 1 FROM kpi_vi_tri WHERE vai_tro='THUKHO');

INSERT INTO mo_ta_cong_viec (vai_tro,chuc_danh,cap_bac,bao_cao_cho,muc_dich,trach_nhiem,quyen_han,yeu_cau) VALUES
  ('KTT','Kế toán trưởng','Quản lý','Giám đốc','Tổ chức công tác kế toán – tài chính, bảo đảm tuân thủ pháp luật, kiểm soát chi phí và cung cấp thông tin quản trị.','["Tổ chức hạch toán, lập báo cáo tài chính và quyết toán thuế đúng hạn.", "Kiểm soát dòng tiền, công nợ phải thu/phải trả và ngân sách.", "Duyệt và hạch toán bảng lương; kiểm soát chi phí doanh nghiệp.", "Quản lý quỹ, vay vốn và trích lập dự phòng.", "Tham mưu Giám đốc về tài chính, thuế và quản trị rủi ro."]','["Duyệt bút toán, phiếu thu/chi trong hạn mức.", "Duyệt bảng lương (bước KTT) và hạch toán.", "Phê duyệt quyết toán thuế."]','{"hoc_van": "Đại học Kế toán – Tài chính; chứng chỉ KTT.", "kinh_nghiem": "≥ 5 năm kế toán, ≥ 2 năm KTT.", "ky_nang": ["Kế toán tổng hợp", "Thuế", "Phân tích tài chính", "Kiểm soát nội bộ"]}')
ON CONFLICT (vai_tro) DO NOTHING;

INSERT INTO kpi_vi_tri (vai_tro,ten,don_vi,trong_so,muc_tieu,chieu,chu_ky,mo_ta,thu_tu)
SELECT * FROM (VALUES
  ('KTT','Báo cáo tài chính/thuế đúng hạn','%',35,100,'CAO','QUY','Tuân thủ thời hạn',0),
  ('KTT','Sai sót bị cơ quan thuế điều chỉnh','lần',25,0,'THAP','NAM','Chính xác tuân thủ',1),
  ('KTT','Số ngày phải thu bình quân (DSO)','ngày',20,45,'THAP','QUY','Quản lý công nợ',2),
  ('KTT','Chênh lệch ngân sách chi phí','%',20,5,'THAP','QUY','Kiểm soát chi phí',3)
) AS v(vai_tro,ten,don_vi,trong_so,muc_tieu,chieu,chu_ky,mo_ta,thu_tu)
WHERE NOT EXISTS (SELECT 1 FROM kpi_vi_tri WHERE vai_tro='KTT');

INSERT INTO mo_ta_cong_viec (vai_tro,chuc_danh,cap_bac,bao_cao_cho,muc_dich,trach_nhiem,quyen_han,yeu_cau) VALUES
  ('NV_KT','Nhân viên Kế toán (kiêm Tài chính)','Nhân viên','Kế toán trưởng','Thực hiện nghiệp vụ kế toán hằng ngày chính xác, đúng hạn; hỗ trợ quản lý dòng tiền và công nợ.','["Lập chứng từ, hạch toán thu/chi, công nợ và hóa đơn.", "Theo dõi công nợ phải thu/phải trả và nhắc thu hồi.", "Lập bảng kê thuế GTGT, TNCN và hồ sơ liên quan.", "Theo dõi quỹ, ngân hàng và đối chiếu số dư."]','["Lập phiếu thu/chi, bút toán (chờ duyệt).", "Lập bảng kê thuế."]','{"hoc_van": "Cao đẳng/Đại học Kế toán.", "kinh_nghiem": "≥ 1 năm kế toán.", "ky_nang": ["Hạch toán", "Excel/phần mềm KT", "Cẩn thận", "Thuế cơ bản"]}')
ON CONFLICT (vai_tro) DO NOTHING;

INSERT INTO kpi_vi_tri (vai_tro,ten,don_vi,trong_so,muc_tieu,chieu,chu_ky,mo_ta,thu_tu)
SELECT * FROM (VALUES
  ('NV_KT','Chứng từ hạch toán đúng hạn','%',40,98,'CAO','THANG','Kịp thời ghi sổ',0),
  ('NV_KT','Sai sót hạch toán bị điều chỉnh','lần',30,1,'THAP','THANG','Độ chính xác',1),
  ('NV_KT','Tỷ lệ đối chiếu công nợ hoàn tất','%',30,100,'CAO','THANG','Đối chiếu đầy đủ',2)
) AS v(vai_tro,ten,don_vi,trong_so,muc_tieu,chieu,chu_ky,mo_ta,thu_tu)
WHERE NOT EXISTS (SELECT 1 FROM kpi_vi_tri WHERE vai_tro='NV_KT');

INSERT INTO mo_ta_cong_viec (vai_tro,chuc_danh,cap_bac,bao_cao_cho,muc_dich,trach_nhiem,quyen_han,yeu_cau) VALUES
  ('TP_DA','Trưởng Dự án','Quản lý','Giám đốc','Quản lý toàn bộ vòng đời dự án xử lý nước/nước thải/khí thải bảo đảm tiến độ, chất lượng, chi phí và an toàn.','["Lập kế hoạch dự án, phân công nguồn lực và quản lý mốc tiến độ.", "Kiểm soát chất lượng theo QCVN/tiêu chuẩn ngành và chỉ tiêu đầu ra.", "Quản lý chi phí dự án, nghiệm thu và phê duyệt khối lượng.", "Giám sát an toàn lao động (HIRA) và hồ sơ dự án.", "Báo cáo tiến độ, rủi ro và phối hợp các phòng liên quan."]','["Duyệt chi phí, khối lượng dự án trong hạn mức.", "Phê duyệt phương án kỹ thuật và nghiệm thu mốc.", "Điều phối nhân sự dự án."]','{"hoc_van": "Đại học Kỹ thuật môi trường/Cấp thoát nước.", "kinh_nghiem": "≥ 5 năm dự án xử lý nước, ≥ 2 năm quản lý.", "ky_nang": ["Quản lý dự án", "Kỹ thuật xử lý nước", "Kiểm soát chi phí", "Quản lý an toàn"]}')
ON CONFLICT (vai_tro) DO NOTHING;

INSERT INTO kpi_vi_tri (vai_tro,ten,don_vi,trong_so,muc_tieu,chieu,chu_ky,mo_ta,thu_tu)
SELECT * FROM (VALUES
  ('TP_DA','Dự án hoàn thành đúng tiến độ','%',30,90,'CAO','QUY','Đúng hạn mốc chính',0),
  ('TP_DA','Chỉ tiêu đầu ra đạt quy chuẩn','%',30,100,'CAO','QUY','Chất lượng nước/khí sau xử lý',1),
  ('TP_DA','Chênh lệch chi phí so dự toán','%',20,5,'THAP','QUY','Kiểm soát ngân sách dự án',2),
  ('TP_DA','Sự cố an toàn lao động','vụ',20,0,'THAP','QUY','An toàn công trường',3)
) AS v(vai_tro,ten,don_vi,trong_so,muc_tieu,chieu,chu_ky,mo_ta,thu_tu)
WHERE NOT EXISTS (SELECT 1 FROM kpi_vi_tri WHERE vai_tro='TP_DA');

INSERT INTO mo_ta_cong_viec (vai_tro,chuc_danh,cap_bac,bao_cao_cho,muc_dich,trach_nhiem,quyen_han,yeu_cau) VALUES
  ('NV_DA','Nhân viên Dự án (giám sát thực địa)','Nhân viên','Trưởng dự án','Triển khai, giám sát thi công và vận hành thử hệ thống tại hiện trường theo thiết kế và tiêu chuẩn.','["Giám sát thi công, lắp đặt thiết bị theo bản vẽ và tiến độ.", "Theo dõi chỉ tiêu vận hành, lấy mẫu và ghi nhật ký công trường.", "Cập nhật khối lượng, mốc và rủi ro lên hệ thống dự án.", "Thực hiện quy định an toàn lao động tại hiện trường."]','["Ghi nhận nhật ký, khối lượng (chờ duyệt).", "Đề xuất xử lý phát sinh kỹ thuật."]','{"hoc_van": "Cao đẳng/Đại học Kỹ thuật.", "kinh_nghiem": "≥ 1 năm thi công/vận hành hệ thống nước.", "ky_nang": ["Đọc bản vẽ P&ID", "Giám sát thi công", "Lấy mẫu & đo đạc", "An toàn lao động"]}')
ON CONFLICT (vai_tro) DO NOTHING;

INSERT INTO kpi_vi_tri (vai_tro,ten,don_vi,trong_so,muc_tieu,chieu,chu_ky,mo_ta,thu_tu)
SELECT * FROM (VALUES
  ('NV_DA','Tiến độ hạng mục được giao','%',35,95,'CAO','TUAN','Đúng kế hoạch tuần',0),
  ('NV_DA','Chỉ tiêu vận hành đạt yêu cầu','%',30,100,'CAO','THANG','Chất lượng vận hành thử',1),
  ('NV_DA','Đầy đủ nhật ký & hồ sơ hiện trường','%',20,100,'CAO','TUAN','Hồ sơ đầy đủ',2),
  ('NV_DA','Vi phạm an toàn lao động','lần',15,0,'THAP','THANG','Tuân thủ ATLĐ',3)
) AS v(vai_tro,ten,don_vi,trong_so,muc_tieu,chieu,chu_ky,mo_ta,thu_tu)
WHERE NOT EXISTS (SELECT 1 FROM kpi_vi_tri WHERE vai_tro='NV_DA');

INSERT INTO mo_ta_cong_viec (vai_tro,chuc_danh,cap_bac,bao_cao_cho,muc_dich,trach_nhiem,quyen_han,yeu_cau) VALUES
  ('NV_THUE','Nhân viên Dịch vụ Cho thuê','Nhân viên','Giám đốc','Quản lý hợp đồng cho thuê thiết bị/hệ thống xử lý, bảo đảm doanh thu thuê và công nợ thuê.','["Lập và theo dõi hợp đồng cho thuê, lịch thanh toán.", "Theo dõi tình trạng thiết bị cho thuê và bảo trì định kỳ.", "Đôn đốc công nợ thuê và gia hạn hợp đồng.", "Phối hợp Kho/Dự án điều phối thiết bị cho thuê."]','["Lập hợp đồng thuê (chờ duyệt).", "Đề xuất chính sách giá thuê."]','{"hoc_van": "Cao đẳng/Đại học.", "kinh_nghiem": "≥ 1 năm dịch vụ/kinh doanh.", "ky_nang": ["Quản lý hợp đồng", "Theo dõi công nợ", "Chăm sóc khách hàng", "Điều phối thiết bị"]}')
ON CONFLICT (vai_tro) DO NOTHING;

INSERT INTO kpi_vi_tri (vai_tro,ten,don_vi,trong_so,muc_tieu,chieu,chu_ky,mo_ta,thu_tu)
SELECT * FROM (VALUES
  ('NV_THUE','Doanh thu cho thuê / chỉ tiêu','%',40,100,'CAO','THANG','Hoàn thành chỉ tiêu thuê',0),
  ('NV_THUE','Tỷ lệ thu đúng hạn tiền thuê','%',30,95,'CAO','THANG','Quản lý công nợ thuê',1),
  ('NV_THUE','Tỷ lệ tái ký hợp đồng','%',20,70,'CAO','QUY','Giữ khách thuê',2),
  ('NV_THUE','Số lần thiết bị hỏng do quản lý kém','lần',10,0,'THAP','QUY','Bảo quản thiết bị',3)
) AS v(vai_tro,ten,don_vi,trong_so,muc_tieu,chieu,chu_ky,mo_ta,thu_tu)
WHERE NOT EXISTS (SELECT 1 FROM kpi_vi_tri WHERE vai_tro='NV_THUE');

INSERT INTO mo_ta_cong_viec (vai_tro,chuc_danh,cap_bac,bao_cao_cho,muc_dich,trach_nhiem,quyen_han,yeu_cau) VALUES
  ('NV_HCNS','Nhân viên Hành chính - Nhân sự','Nhân viên','Giám đốc','Bảo đảm vận hành hành chính, quản lý nhân sự, chấm công – lương và tuân thủ chính sách lao động.','["Quản lý hồ sơ nhân sự, hợp đồng lao động và bảo hiểm.", "Tổ chức chấm công, tính bảng lương và trình duyệt theo quy trình.", "Hỗ trợ tuyển dụng, onboarding và đào tạo nội bộ.", "Quản lý văn thư, tài sản hành chính và sự kiện nội bộ.", "Theo dõi đánh giá KPI và tổng kết kết quả công việc."]','["Lập bảng lương (chờ KTT duyệt, CEO ký).", "Quản lý hồ sơ nhân sự và chấm công."]','{"hoc_van": "Cao đẳng/Đại học (QTNS/Hành chính).", "kinh_nghiem": "≥ 1 năm HCNS.", "ky_nang": ["Quản trị nhân sự", "Tính lương & BHXH", "Luật lao động cơ bản", "Tổ chức"]}')
ON CONFLICT (vai_tro) DO NOTHING;

INSERT INTO kpi_vi_tri (vai_tro,ten,don_vi,trong_so,muc_tieu,chieu,chu_ky,mo_ta,thu_tu)
SELECT * FROM (VALUES
  ('NV_HCNS','Bảng lương đúng hạn (trước ngày 7)','%',35,100,'CAO','THANG','Đúng hạn chi trả',0),
  ('NV_HCNS','Sai sót tính lương/bảo hiểm','lần',30,0,'THAP','THANG','Chính xác lương',1),
  ('NV_HCNS','Tỷ lệ hồ sơ nhân sự đầy đủ','%',20,100,'CAO','QUY','Hồ sơ chuẩn',2),
  ('NV_HCNS','Thời gian xử lý đề nghị nhân sự','ngày',15,2,'THAP','THANG','Phục vụ nội bộ',3)
) AS v(vai_tro,ten,don_vi,trong_so,muc_tieu,chieu,chu_ky,mo_ta,thu_tu)
WHERE NOT EXISTS (SELECT 1 FROM kpi_vi_tri WHERE vai_tro='NV_HCNS');

INSERT INTO mo_ta_cong_viec (vai_tro,chuc_danh,cap_bac,bao_cao_cho,muc_dich,trach_nhiem,quyen_han,yeu_cau) VALUES
  ('ADMIN','Quản trị hệ thống / IT','Nhân viên','Giám đốc','Bảo đảm hệ thống ERP và hạ tầng CNTT vận hành ổn định, an toàn và bảo mật dữ liệu.','["Quản trị tài khoản, phân quyền kỹ thuật và sao lưu dữ liệu.", "Giám sát vận hành hệ thống ERP, xử lý sự cố CNTT.", "Bảo đảm an toàn, bảo mật thông tin và kiểm soát truy cập.", "Hỗ trợ người dùng và cải tiến quy trình số hóa."]','["Quản trị kỹ thuật hệ thống.", "Cấp/thu hồi tài khoản theo phê duyệt."]','{"hoc_van": "Cao đẳng/Đại học CNTT.", "kinh_nghiem": "≥ 2 năm quản trị hệ thống.", "ky_nang": ["Quản trị hệ thống/DB", "An ninh mạng", "Hỗ trợ người dùng", "Sao lưu & phục hồi"]}')
ON CONFLICT (vai_tro) DO NOTHING;

INSERT INTO kpi_vi_tri (vai_tro,ten,don_vi,trong_so,muc_tieu,chieu,chu_ky,mo_ta,thu_tu)
SELECT * FROM (VALUES
  ('ADMIN','Thời gian hệ thống hoạt động (uptime)','%',40,99.5,'CAO','THANG','Độ ổn định',0),
  ('ADMIN','Thời gian xử lý sự cố bình quân','giờ',25,4,'THAP','THANG','Tốc độ khắc phục',1),
  ('ADMIN','Sự cố mất/an ninh dữ liệu','vụ',20,0,'THAP','NAM','An toàn dữ liệu',2),
  ('ADMIN','Tỷ lệ sao lưu thành công','%',15,100,'CAO','THANG','Backup đầy đủ',3)
) AS v(vai_tro,ten,don_vi,trong_so,muc_tieu,chieu,chu_ky,mo_ta,thu_tu)
WHERE NOT EXISTS (SELECT 1 FROM kpi_vi_tri WHERE vai_tro='ADMIN');


COMMIT;
