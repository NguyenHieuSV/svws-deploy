-- 53: Dịch vụ kỹ thuật — thêm trường liên hệ (lead) + nạp phiếu mẫu từ YTouch Leads
ALTER TABLE dich_vu_kt ADD COLUMN IF NOT EXISTS khach_ten  VARCHAR(150);
ALTER TABLE dich_vu_kt ADD COLUMN IF NOT EXISTS cong_ty    VARCHAR(200);
ALTER TABLE dich_vu_kt ADD COLUMN IF NOT EXISTS dien_thoai VARCHAR(40);
ALTER TABLE dich_vu_kt ADD COLUMN IF NOT EXISTS email      VARCHAR(150);

-- Phiếu mẫu khớp 6 lead "Dịch vụ kỹ thuật" của YTouch (idempotent theo mã)
INSERT INTO dich_vu_kt (ma, loai_dv, chi_tiet_dv, ten, khach_ten, cong_ty, dien_thoai, email, trang_thai, ngay_hen, ghi_chu)
VALUES
 ('CIP-YT-72','CIP','RO','Yêu cầu CIP RO (nhập từ YTouch Leads)','đởm','lhmt','0947293137','sv-tuan@watersolutions.company','KHAO_SAT','2026-07-07','Nguồn: YTouch Leads #72 · trạng thái gốc: Mới'),
 ('VH-YT-01','OPERATION',NULL,'Yêu cầu vận hành (nhập từ YTouch Leads)','Nguyễn Thị Dinh','Công ty TNHH GPKT Sóng Việt','0333541124','sv-dinh@watersolutions.company','KHAO_SAT','2026-05-12','Nguồn: YTouch Leads · trạng thái gốc: Mới'),
 ('VH-YT-02','OPERATION',NULL,'Yêu cầu vận hành (nhập từ YTouch Leads)','Nguyễn Thị Dinh','Công ty TNHH GPKT Sóng Việt','0333541124','sv-dinh@watersolutions.company','KHAO_SAT','2026-05-12','Nguồn: YTouch Leads · trạng thái gốc: Mới'),
 ('VH-YT-03','OPERATION',NULL,'Yêu cầu vận hành (nhập từ YTouch Leads)','Nguyễn Thị Cẩm Tiên','CTy TNHH GPKT Sóng Việt','0907258691','sv-tien@watersolutions.company','KHAO_SAT','2026-05-12','Nguồn: YTouch Leads · trạng thái gốc: Mới'),
 ('CIP-YT-11','CIP','RO','Yêu cầu CIP RO (nhập từ YTouch Leads)','Nguyễn Thị Dinh','Công ty TNHH GPKT Sóng Việt','0333541124','sv-dinh@watersolutions.company','KHAO_SAT','2026-05-11','Nguồn: YTouch Leads · trạng thái gốc: Mới'),
 ('VH-YT-04','OPERATION',NULL,'Yêu cầu vận hành (nhập từ YTouch Leads)','Mr. Giang','COHETENT D26','3340070873','ultrapure.plus@gmail.com','KHAO_SAT','2026-05-07','Nguồn: YTouch Leads · trạng thái gốc: Mới')
ON CONFLICT (ma) DO NOTHING;
