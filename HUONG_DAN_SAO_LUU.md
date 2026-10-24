# Sao lưu CSDL lên Backblaze B2 (T102 · PR-0)

Lớp sao lưu thứ hai, bổ sung cho Recovery của gói Postgres Basic-256mb trên Render.
Mã nguồn: `app/sao_luu.py` (chạy trong scheduler của app), lệnh tay: `scripts/sao_luu_b2.py`.

## 1. Cài đặt một lần
1. Backblaze B2 → **Create a Bucket**: tên vd `svws-pg-backup`, **Private**.
   *Lifecycle Settings*: "Keep only the last version of the file" (app tự xóa bản thứ 15 trở đi).
2. **Application Keys → Add a New Application Key**: chỉ cho bucket trên, quyền *Read and Write*.
3. Render → `svws-app-iit7` → **Environment**, thêm:

| Biến | Giá trị |
|---|---|
| `BACKUP_B2_ENDPOINT` | Endpoint S3 của bucket, vd `https://s3.us-west-004.backblazeb2.com` |
| `BACKUP_B2_KEY_ID` | keyID |
| `BACKUP_B2_APP_KEY` | applicationKey |
| `BACKUP_B2_BUCKET` | `svws-pg-backup` |
| `BACKUP_KEEP` | `14` (số bản giữ lại) |
| `BACKUP_GIO` | `2` (giờ Việt Nam bắt đầu chạy mỗi ngày) |

Sau khi lưu, app khởi động lại; từ 2h sáng (hoặc lần thức đầu tiên sau 2h) log Render có dòng
`[SAO LƯU] ✅ pg-dump/svws-YYYYMMDD-HHMMSS.dump (… byte)`. Lỗi in `[SAO LƯU] ❌ …` và thử lại sau 1 giờ.

## 2. Chạy tay (Render → Shell)
```bash
python -m scripts.sao_luu_b2 chay        # sao lưu ngay
python -m scripts.sao_luu_b2 danh-sach   # liệt kê bản trên B2
```

## 3. Thử khôi phục (làm một lần, ghi biên bản)
Khôi phục vào CSDL **trống** (Postgres local hoặc một DB tạm trên Render), không bao giờ vào `svws_gu1s` đang chạy.
```bash
python -m scripts.sao_luu_b2 tai-ve                    # tải bản mới nhất
createdb svws_thu
pg_restore --no-owner --no-acl --dbname postgresql://.../svws_thu svws-YYYYMMDD-HHMMSS.dump
psql postgresql://.../svws_thu -c "select count(*) from trn_results" -c "select count(*) from _migrations"
```

**Biên bản thử khôi phục**

| Mục | Ghi |
|---|---|
| Ngày thử / người thử | |
| Tệp sao lưu (khóa trên B2), dung lượng | |
| Nơi khôi phục | |
| Thời gian khôi phục | |
| Đối chiếu số dòng (`trn_results`, `khach_hang`, `_migrations`) với DB đang chạy | |
| Lỗi gặp phải / cách xử lý | |
| Kết luận | Đạt / Không đạt |

## Lưu ý
- `pg_dump` trong image phải cùng hoặc mới hơn Postgres của server (Render đang chạy **18**).
  `Dockerfile` cài `postgresql-client-18` từ kho PGDG (`ARG PG_MAJOR=18`) và tự dừng build nếu
  `pg_dump --version` không đúng bản 18. Khi Render nâng Postgres lên bản mới, đổi `PG_MAJOR` theo.
