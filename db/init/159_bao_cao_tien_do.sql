-- 159 — % TIẾN ĐỘ công việc trong báo cáo ngày (Working time & Report — anh Hiếu 29/10/2026).
--  • bao_cao_ngay.tien_do: % tiến độ (0–100) BẮT BUỘC nhập mỗi báo cáo.
--  • giao_viec.tien_do: % mới nhất của việc = tiến độ của báo cáo có NGÀY gần nhất gắn việc.
--  • giao_viec.hoan_thanh_luc: lúc đạt 100% lần đầu (app nhắn người giao việc qua Google Chat).
--  • giao_viec.nhac_lech_ngay: ngày gần nhất đã nhắc «chậm tiến độ so với thời gian» (mỗi việc mỗi ngày một tin).
ALTER TABLE bao_cao_ngay ADD COLUMN IF NOT EXISTS tien_do NUMERIC(5,1);
ALTER TABLE giao_viec    ADD COLUMN IF NOT EXISTS tien_do NUMERIC(5,1);
ALTER TABLE giao_viec    ADD COLUMN IF NOT EXISTS hoan_thanh_luc TIMESTAMP;
ALTER TABLE giao_viec    ADD COLUMN IF NOT EXISTS nhac_lech_ngay DATE;
