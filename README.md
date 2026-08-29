# SVWS — Lát cắt dọc module Kho

Khuôn mẫu tham chiếu: SQLAlchemy + FastAPI + phân quyền RBAC đọc từ bảng `phan_quyen`.
Dựng xong module này thì **các module khác chỉ việc lặp lại cùng khuôn mẫu**.

## Cấu trúc
```
app/
  config.py      cấu hình (DB, JWT)
  database.py    engine + session + Base
  models.py      ORM khớp SVWS_schema.sql (core + module Kho)
  schemas.py     Pydantic vào/ra
  security.py    băm mật khẩu + JWT
  deps.py        lấy người dùng hiện tại từ token
  rbac.py        ★ yeu_cau("<module>", "<mức>") — trái tim phân quyền
  audit.py       ghi audit_log
  routers/
    auth.py      đăng nhập, /me
    kho.py       ★ endpoints module Kho (mẫu để nhân rộng)
  main.py        lắp ráp app
scripts/tao_user_demo.py   tạo user demo để thử quyền
```

## Chạy
```bash
# 1) CSDL: chạy 2 file SQL đã có trước đó
psql -d svws -f SVWS_schema.sql
psql -d svws -f SVWS_seed_rbac.sql

# 2) Cài & khởi động
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # sửa DATABASE_URL nếu cần
python -m scripts.tao_user_demo
uvicorn app.main:app --reload
# Mở http://localhost:8000/docs
```

## Thử phân quyền (chứng minh RBAC hoạt động)
Mật khẩu demo: `matkhau123`

| Người dùng | Vai trò | Quyền kho | Kỳ vọng |
|---|---|---|---|
| thukho@svws.vn | THUKHO | THAO_TAC | tạo hàng/lập phiếu OK; điều chỉnh tồn → 403 |
| nvkd@svws.vn | NV_KD | XEM | xem OK; tạo/lập phiếu → 403 |
| ceo@svws.vn | CEO | DUYET | làm được tất cả, kể cả điều chỉnh tồn |

```bash
# Lấy token
TOKEN=$(curl -s -X POST localhost:8000/auth/login \
  -d "username=thukho@svws.vn&password=matkhau123" | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

# Tạo hàng hóa (THUKHO: 201) — đặt ton_min để thử tự sinh yêu cầu mua
curl -X POST localhost:8000/kho/hang-hoa -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ma":"PAC-01","ten":"Hóa chất PAC","loai":"VAT_TU","don_vi":"kg","ton_min":100}'

# Nhập 200kg, rồi xuất 150kg -> tồn 50 < min 100 -> tự sinh yeu_cau_mua
curl -X POST localhost:8000/kho/phieu -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"loai":"NHAP","chi_tiet":[{"hang_hoa_id":1,"so_luong":200}]}'
curl -X POST localhost:8000/kho/phieu -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"loai":"XUAT","chi_tiet":[{"hang_hoa_id":1,"so_luong":150}]}'

# THUKHO điều chỉnh tồn -> 403 (cần mức DUYET)
curl -i -X POST localhost:8000/kho/ton-kho/dieu-chinh -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" -d '{"hang_hoa_id":1,"so_luong_moi":80,"ly_do":"kiem ke"}'
```

## Nhân rộng cho module khác (khuôn mẫu)
1. Thêm model còn thiếu vào `models.py` (đa số đã có trong schema).
2. Tạo `routers/<module>.py`, đổi `MODULE = "<ten_module>"`.
3. Mỗi endpoint gắn `Depends(yeu_cau(MODULE, "XEM" | "THAO_TAC" | "DUYET"))`.
4. Thao tác ghi dữ liệu → gọi `ghi_audit(...)` trước `db.commit()`.
5. `include_router` trong `main.py`.

Không sửa logic phân quyền — nó nằm gọn trong `rbac.py` và lấy quyền từ bảng `phan_quyen`.

---

# Module Nhà cung cấp & Mua hàng (NCC)

Lát cắt dọc thứ hai. Dùng lại y nguyên khuôn `yeu_cau("ncc", "<mức>")`, và thêm
**tầng phê duyệt theo hạn mức tiền** đọc bảng `han_muc_duyet` (`rbac.kiem_han_muc`).

### Hai tầng phân quyền khi duyệt đơn mua
1. Tầng module: vai trò phải có `ncc = DUYET` (TP_CU và CEO).
2. Tầng tiền: số tiền đơn phải `<= nguong_den` của vai trò cho `loai='po'`
   (mô hình trần; NULL = vô hạn). TP_CU trần 10tr, CEO vô hạn.

| Vai trò | ncc | Trần duyệt PO | Đơn 8tr | Đơn 15tr |
|---|---|---|---|---|
| NV_MUA | THAO_TAC | — | tạo được, **không duyệt** (403) | — |
| TP_CU | DUYET | 10.000.000 | duyệt OK | **403 vượt hạn mức** |
| CEO | DUYET | vô hạn | duyệt OK | duyệt OK |

### Thử nhanh (mật khẩu demo: matkhau123)
```bash
login(){ curl -s -X POST localhost:8000/auth/login -d "username=$1&password=matkhau123" \
  | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])"; }

T_MUA=$(login nccmua@svws.vn); T_TP=$(login tpcu@svws.vn); T_CEO=$(login ceo@svws.vn)

# NV_MUA tạo NCC + 2 đơn mua (8tr và 15tr) — giả sử đã có hang_hoa id=1
curl -X POST localhost:8000/ncc/nha-cung-cap -H "Authorization: Bearer $T_MUA" \
  -H "Content-Type: application/json" -d '{"ma":"NCC-01","ten":"Cty Hóa chất ABC"}'
curl -X POST localhost:8000/ncc/don-mua -H "Authorization: Bearer $T_MUA" \
  -H "Content-Type: application/json" \
  -d '{"nha_cung_cap_id":1,"chi_tiet":[{"hang_hoa_id":1,"so_luong":80,"don_gia":100000}]}'   # 8tr
curl -X POST localhost:8000/ncc/don-mua -H "Authorization: Bearer $T_MUA" \
  -H "Content-Type: application/json" \
  -d '{"nha_cung_cap_id":1,"chi_tiet":[{"hang_hoa_id":1,"so_luong":150,"don_gia":100000}]}'  # 15tr

# TP_CU duyệt đơn 8tr -> OK ; duyệt đơn 15tr -> 403 (vượt 10tr)
curl -i -X POST localhost:8000/ncc/don-mua/1/duyet -H "Authorization: Bearer $T_TP"
curl -i -X POST localhost:8000/ncc/don-mua/2/duyet -H "Authorization: Bearer $T_TP"
# CEO duyệt đơn 15tr -> OK ; sau duyệt tự "gửi email NCC" (xem log server)
curl -i -X POST localhost:8000/ncc/don-mua/2/duyet -H "Authorization: Bearer $T_CEO"
```

### Nối với module Kho
`GET /ncc/yeu-cau-mua` liệt kê các yêu cầu mua mà module Kho **tự sinh** khi tồn < min
(`ly_do='TON_DUOI_MIN'`) — khép vòng "tồn thấp → đề xuất mua → đơn mua → duyệt".

---

# Module Dự án (dự toán vs thực tế · nối Forecast Cal)

Lát cắt dọc thứ ba. **Bắt buộc chạy thêm migration** sau schema gốc:
```bash
psql -d svws -f SVWS_schema_duan_ext.sql   # thêm du_toan_ct + cột hang_muc
```

### Quy tắc duyệt được làm rõ ở module này
Quyền duyệt **do bảng `han_muc_duyet` quyết định**, mức module chỉ cần `XEM` để nhìn
thấy bản ghi. Nhờ vậy KTT (`du_an = XEM`) vẫn duyệt được chi phí tới 50tr.
Chi phí dự án có **3 cấp** (`loai='chi_phi_du_an'`):

| Vai trò | Trần duyệt | Chi phí 3tr | Chi phí 8tr | Chi phí 60tr |
|---|---|---|---|---|
| NV_DA | — (ghi nhận, không duyệt) | 403 | 403 | 403 |
| TP_DA | 5.000.000 | duyệt OK | **403 vượt trần** | 403 |
| KTT | 50.000.000 | OK | OK | **403 vượt trần** |
| CEO | vô hạn | OK | OK | OK |

Chi phí được duyệt cộng dồn vào `chi_phi_thuc_te`; vượt `du_toan` → trả `vuot_du_toan=true` + cảnh báo GĐ.

### Nối Forecast Cal (2 chiều)
1. **Nhập dự toán** — `POST /du-an/{id}/nhap-du-toan-forecast` nhận đúng JSON export của
   Forecast Cal (`lines: [{hang_muc, mo_ta, so_luong, don_gia}]`), lưu breakdown và đặt `du_toan`.
2. **Vòng phản hồi** — `GET /du-an/{id}/doi-chieu-forecast` trả dự toán vs thực tế **theo hạng mục**
   (`chenh_lech`, `ty_le`). Forecast Cal nạp lại số này để hiệu chỉnh catalog giá → dự toán dự án sau chính xác hơn.

### Thử nhanh
```bash
login(){ curl -s -X POST localhost:8000/auth/login -d "username=$1&password=matkhau123" \
  | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])"; }
T_DA=$(login nvda@svws.vn); T_TPDA=$(login tpda@svws.vn); T_KTT=$(login ktt@svws.vn)

# Trưởng/NV dự án tạo dự án, nhập dự toán từ Forecast Cal
curl -X POST localhost:8000/du-an -H "Authorization: Bearer $T_DA" \
  -H "Content-Type: application/json" -d '{"ma":"DA-01","ten":"Trạm XLNT 200m3","qcvn":"QCVN 40:2011/B"}'
curl -X POST localhost:8000/du-an/1/nhap-du-toan-forecast -H "Authorization: Bearer $T_DA" \
  -H "Content-Type: application/json" -d '{"lines":[
    {"hang_muc":"Thiết bị","mo_ta":"Bơm định lượng","so_luong":2,"don_gia":5000000},
    {"hang_muc":"Vật tư","mo_ta":"Màng MBR","so_luong":1,"don_gia":40000000}]}'

# NV_DA ghi 2 chi phí thực tế (3tr, 8tr) -> chờ duyệt
curl -X POST localhost:8000/du-an/1/chi-phi -H "Authorization: Bearer $T_DA" \
  -H "Content-Type: application/json" -d '{"hang_muc":"Thiết bị","mo_ta":"PG bom","so_tien":3000000}'
curl -X POST localhost:8000/du-an/1/chi-phi -H "Authorization: Bearer $T_DA" \
  -H "Content-Type: application/json" -d '{"hang_muc":"Vật tư","mo_ta":"PG mang","so_tien":8000000}'

# TP_DA duyệt 3tr -> OK ; duyệt 8tr -> 403 (vượt 5tr) ; KTT duyệt 8tr -> OK
curl -i -X POST localhost:8000/du-an/chi-phi/1/duyet -H "Authorization: Bearer $T_TPDA"
curl -i -X POST localhost:8000/du-an/chi-phi/2/duyet -H "Authorization: Bearer $T_TPDA"
curl -i -X POST localhost:8000/du-an/chi-phi/2/duyet -H "Authorization: Bearer $T_KTT"

# Vòng phản hồi cho Forecast Cal
curl -s localhost:8000/du-an/1/doi-chieu-forecast -H "Authorization: Bearer $T_KTT"
```

---

# Module Bán hàng (báo giá → đơn → xuất kho → hóa đơn + công nợ)

Lát cắt dọc thứ tư — minh họa **liên thông** rõ nhất. Phần trừ tồn tách thành
`app/kho_service.py` để Bán hàng và Kho dùng chung một logic (không lặp).

### Luồng & liên thông
```
Báo giá ──duyệt(han_muc 'bao_gia')──► Đơn hàng ──xuất kho──►  • PhieuKho XUAT  (module Kho)
                                                              • trừ tồn + tự sinh yêu cầu mua nếu < min
                                                              • Hóa đơn BAN     (chừa chỗ nối HĐĐT)
                                                              • Công nợ PHẢI THU (bàn giao Kế toán)
```

### Duyệt báo giá (2 cấp, mô hình trần)
| Vai trò | Trần | Báo giá 80tr | Báo giá 150tr |
|---|---|---|---|
| NV_KD | — (soạn, không duyệt) | 403 | 403 |
| TP_KD | 100.000.000 | duyệt OK | **403 vượt trần** |
| CEO | vô hạn | OK | OK |

### Thử nhanh (cần có hàng hóa + tồn từ module Kho trước)
```bash
login(){ curl -s -X POST localhost:8000/auth/login -d "username=$1&password=matkhau123" \
  | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])"; }
T_KD=$(login nvkd@svws.vn); T_TPKD=$(login tpkd@svws.vn); T_CEO=$(login ceo@svws.vn)
T_KHO=$(login thukho@svws.vn)

# (Kho) tạo hàng + nhập tồn 500
curl -X POST localhost:8000/kho/hang-hoa -H "Authorization: Bearer $T_KHO" \
  -H "Content-Type: application/json" -d '{"ma":"BOM-01","ten":"Bơm chìm","loai":"THIET_BI","don_vi":"cái","ton_min":5}'
curl -X POST localhost:8000/kho/phieu -H "Authorization: Bearer $T_KHO" \
  -H "Content-Type: application/json" -d '{"loai":"NHAP","chi_tiet":[{"hang_hoa_id":1,"so_luong":500}]}'

# (Bán hàng) NV_KD tạo KH + báo giá 80tr & 150tr
curl -X POST localhost:8000/ban-hang/khach-hang -H "Authorization: Bearer $T_KD" \
  -H "Content-Type: application/json" -d '{"ma":"KH-01","ten":"Cty Dệt may X"}'
curl -X POST localhost:8000/ban-hang/bao-gia -H "Authorization: Bearer $T_KD" \
  -H "Content-Type: application/json" -d '{"khach_hang_id":1,"chi_tiet":[{"hang_hoa_id":1,"so_luong":8,"don_gia":10000000}]}'  # 80tr
curl -X POST localhost:8000/ban-hang/bao-gia -H "Authorization: Bearer $T_KD" \
  -H "Content-Type: application/json" -d '{"khach_hang_id":1,"chi_tiet":[{"hang_hoa_id":1,"so_luong":15,"don_gia":10000000}]}' # 150tr

# Duyệt: TP_KD 80tr OK; TP_KD 150tr 403; CEO 150tr OK
curl -i -X POST localhost:8000/ban-hang/bao-gia/1/duyet -H "Authorization: Bearer $T_TPKD"
curl -i -X POST localhost:8000/ban-hang/bao-gia/2/duyet -H "Authorization: Bearer $T_TPKD"
curl -i -X POST localhost:8000/ban-hang/bao-gia/2/duyet -H "Authorization: Bearer $T_CEO"

# Tạo đơn từ báo giá đã duyệt rồi xuất kho -> trừ tồn + hóa đơn + công nợ
curl -X POST localhost:8000/ban-hang/bao-gia/1/tao-don -H "Authorization: Bearer $T_KD"
curl -s -X POST localhost:8000/ban-hang/don-hang/1/xuat-kho -H "Authorization: Bearer $T_KD"
```

---

# Module Kế toán & Tài chính (nhận HĐ + công nợ · tích hợp HĐĐT)

Lát cắt dọc thứ năm — phức tạp nhất. Hai phần tách riêng để tái dùng & kiểm thử:
- `app/hddt_gateway.py` — **cổng HĐĐT** trừu tượng. Dev dùng `FakeProvider`;
  khi tích hợp thật chỉ thay bằng SDK MISA meInvoice / VNPT / Viettel (NĐ 70/2025, TT 32/2025).
  **Không tự dựng engine thuế.**
- `app/hach_toan.py` — **hạch toán kép** theo tài khoản VAS (TT 200/133).

### Luồng (tiếp nối Bán hàng)
```
Bán hàng xuất kho ──► Hóa đơn (CHUA_PHAT_HANH) + Công nợ phải thu
       │
Kế toán: phát hành HĐĐT ──► gọi provider, nhận mã tra cứu
       │                    ──► hạch toán:  Nợ 131 / Có 511 (doanh thu)
       │                                    Nợ 131 / Có 3331 (thuế GTGT)
Kế toán: thu tiền công nợ ──► Nợ 112(111) / Có 131 ; tự đóng khi thu đủ
Tài chính: dòng tiền · công nợ quá hạn >30 ngày ──► cảnh báo tự động
```

### Endpoints chính
| Endpoint | Quyền | Việc |
|---|---|---|
| `POST /ke-toan/hoa-don/{id}/phat-hanh-hddt` | ke_toan THAO_TAC | gọi cổng HĐĐT + hạch toán doanh thu |
| `POST /ke-toan/cong-no/{id}/thu-tien` | ke_toan THAO_TAC | ghi thu, hạch toán, tự đóng nợ |
| `GET /ke-toan/so-cai` | ke_toan XEM | sổ cái bút toán |
| `GET /tai-chinh/dong-tien` | tai_chinh XEM | tổng thu, còn phải thu/phải trả |
| `GET /tai-chinh/cong-no-qua-han` | tai_chinh XEM | quá hạn >30 ngày → nhắc |

### Thử nhanh (cần 1 hóa đơn bán từ module Bán hàng trước)
```bash
login(){ curl -s -X POST localhost:8000/auth/login -d "username=$1&password=matkhau123" \
  | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])"; }
T_KT=$(login nvkt@svws.vn)

# Phát hành HĐĐT cho hóa đơn 1 (provider DEMO) -> sinh bút toán doanh thu
curl -s -X POST localhost:8000/ke-toan/hoa-don/1/phat-hanh-hddt -H "Authorization: Bearer $T_KT" \
  -H "Content-Type: application/json" -d '{"provider":"DEMO"}'
curl -s localhost:8000/ke-toan/so-cai -H "Authorization: Bearer $T_KT"

# Thu một phần công nợ 1
curl -s -X POST localhost:8000/ke-toan/cong-no/1/thu-tien -H "Authorization: Bearer $T_KT" \
  -H "Content-Type: application/json" -d '{"so_tien":50000000,"hinh_thuc":"CK"}'

# Bức tranh tài chính
curl -s localhost:8000/tai-chinh/dong-tien -H "Authorization: Bearer $T_KT"
curl -s localhost:8000/tai-chinh/cong-no-qua-han -H "Authorization: Bearer $T_KT"
```

---

# Module Nhân sự / Lương (chấm công → lương → KTT duyệt → CEO ký)

Lát cắt dọc thứ sáu. **Migration bắt buộc**: `psql -d svws -f SVWS_schema_nhansu_ext.sql`
(thêm BHXH/BHYT/BHTN/TNCN + dấu vết duyệt 2 bước).

### Kiểu phân quyền MỚI: quy trình tuần tự (không theo hạn mức tiền)
Dùng primitive thứ ba `chi_vai_tro(...)` trong `rbac.py`:
```
NV_HCNS lập lương ──► KTT duyệt + hạch toán ──► CEO ký cuối
   (THAO_TAC)          (chi_vai_tro KTT,CEO)      (chi_vai_tro CEO; cần KTT xong trước)
```
CEO không ký được nếu chưa qua KTT (endpoint kiểm `nguoi_duyet_ktt`).

### Tính lương (`luong_service.py`) — VN
BHXH 8% · BHYT 1.5% · BHTN 1% (NLĐ) + thuế TNCN lũy tiến 7 bậc; giảm trừ bản thân 11tr,
phụ thuộc 4.4tr/người. Bút toán (`hach_toan_luong`): Nợ 642/Có 334 (tổng thu nhập),
Nợ 334/Có 3383·3384·3389·3335 (các khoản khấu trừ) — phần còn lại ở 334 là thực lĩnh.

| Lương cơ bản | BHXH+BHYT+BHTN | TNCN | Thực lĩnh |
|---|---|---|---|
| 30.000.000 | 3.150.000 | 1.627.500 | 25.222.500 |
| 8.000.000 | 840.000 | 0 | 7.160.000 |

### Thử nhanh
```bash
login(){ curl -s -X POST localhost:8000/auth/login -d "username=$1&password=matkhau123" \
  | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])"; }
T_HC=$(login nvhcns@svws.vn); T_KTT=$(login ktt@svws.vn); T_CEO=$(login ceo@svws.vn)

# NV_HCNS tính lương tháng
curl -s -X POST localhost:8000/nhan-su/tinh-luong -H "Authorization: Bearer $T_HC" \
  -H "Content-Type: application/json" -d '{"thang":"2026-06"}'

# NV_HCNS thử ký (KTT) -> 403 (chỉ KTT/CEO)
curl -i -X POST localhost:8000/nhan-su/bang-luong/2026-06/duyet-ktt -H "Authorization: Bearer $T_HC"
# CEO ký trước khi KTT duyệt -> 400 (sai thứ tự)
curl -i -X POST localhost:8000/nhan-su/bang-luong/2026-06/ky-ceo -H "Authorization: Bearer $T_CEO"
# KTT duyệt + hạch toán, rồi CEO ký
curl -s -X POST localhost:8000/nhan-su/bang-luong/2026-06/duyet-ktt -H "Authorization: Bearer $T_KTT"
curl -s -X POST localhost:8000/nhan-su/bang-luong/2026-06/ky-ceo -H "Authorization: Bearer $T_CEO"
```

---

# Module Dịch vụ cho thuê (HĐ định kỳ · xuất tài sản · nhắc hết hạn · công nợ kỳ)

Lát cắt dọc thứ bảy — gần như **không có hạ tầng mới**, chỉ tái dùng:
- Xuất/nhập tài sản: gọi `kho_service.xuat_ton` / `nhap_ton` (đúng service mà Bán hàng dùng).
- Thu phí: lập hóa đơn `loai=THUE` + công nợ phải thu → module Kế toán phát hành HĐĐT & thu tiền
  (đã bật hạch toán cho hóa đơn THUÊ: Nợ 131 / Có 511 + 3331).

### Luồng
```
Ký HĐ ──► xuất tài sản (HC/VT/TB: trừ kho ; NHAN_SU: điều phối người)
   │
Thu phí kỳ ──► hóa đơn THUÊ + công nợ (hạn 15 ngày) ──► Kế toán phát hành HĐĐT
   │
Sắp hết hạn (≤30 ngày) ──► nhắc CEO + P.Kinh doanh (tự động)
   │
Nhận trả ──► nhập lại kho + kết thúc HĐ
```

### Endpoints
| Endpoint | Quyền | Việc |
|---|---|---|
| `POST /cho-thue/hop-dong` | cho_thue THAO_TAC | ký HĐ + xuất tài sản từ kho |
| `POST /cho-thue/hop-dong/{id}/thu-phi` | cho_thue THAO_TAC | lập hóa đơn THUÊ + công nợ một kỳ |
| `POST /cho-thue/chay-thu-phi-dinh-ky` | cho_thue THAO_TAC | thu phí mọi HĐ đang hiệu lực |
| `POST /cho-thue/hop-dong/{id}/nhan-tra` | cho_thue THAO_TAC | nhập lại kho + kết thúc HĐ |
| `GET /cho-thue/sap-het-han` | cho_thue XEM | HĐ còn ≤30 ngày → nhắc |

### Thử nhanh (cần khách hàng + hàng hóa tồn từ các module trước)
```bash
T_THUE=$(curl -s -X POST localhost:8000/auth/login -d "username=nvthue@svws.vn&password=matkhau123" \
  | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

# Ký HĐ thuê thiết bị (trừ kho hàng_hoa id=1, 2 cái) — chu kỳ tháng, 5tr/kỳ
curl -s -X POST localhost:8000/cho-thue/hop-dong -H "Authorization: Bearer $T_THUE" \
  -H "Content-Type: application/json" -d '{"khach_hang_id":1,"doi_tuong":"THIET_BI","gia_thue":5000000,
       "chu_ky":"THANG","ngay_bat_dau":"2026-06-01","ngay_ket_thuc":"2026-07-05",
       "tai_san":[{"hang_hoa_id":1,"so_luong":2}]}'

curl -s -X POST localhost:8000/cho-thue/hop-dong/1/thu-phi -H "Authorization: Bearer $T_THUE"  # hóa đơn THUÊ
curl -s localhost:8000/cho-thue/sap-het-han -H "Authorization: Bearer $T_THUE"                 # nhắc hết hạn
curl -s -X POST localhost:8000/cho-thue/hop-dong/1/nhan-tra -H "Authorization: Bearer $T_THUE" # nhập lại kho
```

---

# Module CRM (hồ sơ 360° · phân loại ABC · chăm sóc sau bán)

Lát cắt dọc thứ tám (khép bộ). **Migration**: `psql -d svws -f SVWS_schema_crm_ext.sql`
(thêm bảng `cham_soc_kh`). Không thêm primitive phân quyền mới — minh họa **tổng hợp liên module**.

### Tính năng
- `GET /crm/khach-hang/{id}` — **hồ sơ 360°**: gộp số báo giá, đơn hàng, doanh số lũy kế, còn phải thu, lịch sử chăm sóc (đọc từ Bán hàng + Kế toán).
- `POST /crm/phan-loai-abc` — **tự động** xếp A/B/C theo doanh số (A ≥ 500tr, B ≥ 100tr, C còn lại — ngưỡng cấu hình).
- `POST /crm/len-lich-sau-ban/{don_hang_id}` — tạo lịch gọi chăm sóc +7 và +30 ngày từ đơn hàng.
- `GET /crm/cham-soc/den-han` — nhắc việc chăm sóc đến hạn.
- `POST /crm/cham-soc/{id}/hoan-thanh` — hoàn thành + ghi CSAT.
- `GET /crm/khieu-nai/qua-han` — khiếu nại quá SLA 24h.

---

# TỔNG KẾT — Backend hợp nhất SVWS

**9 module nghiệp vụ · 50 endpoint · 1 cơ sở dữ liệu PostgreSQL.**

### Thứ tự chạy SQL (một lần khi khởi tạo)
```bash
psql -d svws -f SVWS_schema.sql            # 31 bảng + enum
psql -d svws -f SVWS_seed_rbac.sql         # 14 vai trò + phân quyền + hạn mức
psql -d svws -f SVWS_schema_duan_ext.sql   # mở rộng Dự án
psql -d svws -f SVWS_schema_nhansu_ext.sql # mở rộng Lương (BH/TNCN)
psql -d svws -f SVWS_schema_crm_ext.sql    # bảng chăm sóc KH
```

### Ba primitive phân quyền tái dùng (app/rbac.py)
| Primitive | Quyết định bởi | Dùng ở |
|---|---|---|
| `yeu_cau(module, mức)` | mức module trong `phan_quyen` | mọi endpoint |
| `kiem_han_muc(loai, tiền)` | trần tiền trong `han_muc_duyet` | PO, chi phí DA, báo giá |
| `chi_vai_tro(...)` | mã vai trò cụ thể | duyệt lương (KTT→CEO) |

### Hạ tầng dùng chung
- `kho_service.py` — xuất/nhập tồn (Kho, Bán hàng, Cho thuê cùng gọi).
- `hach_toan.py` — bút toán kép VAS (bán hàng, cho thuê, lương).
- `hddt_gateway.py` — cổng HĐĐT thay-thế-được (MISA/VNPT/Viettel).
- `audit.py` — mọi thao tác ghi `audit_log`.

### Còn lại để lên production
- Tầng tự động hóa chạy nền (scheduler) gọi: `chay-thu-phi-dinh-ky`, nhắc hết hạn/quá hạn, dashboard 8h sáng.
- Thay `FakeProvider` HĐĐT bằng SDK thật; thuế suất theo mặt hàng; trần BHXH; prorate lương theo công.
- Frontend Next.js (PWA) đọc `phan_quyen` để ẩn/hiện module theo vai trò.
- Module còn lại của bản kế hoạch: Tài liệu (bản vẽ/HĐ có phiên bản), Dashboard CEO real-time.

---

# Bán hàng — Mở rộng: Tệp PO/Hợp đồng & Email chào hàng

**Migration**: `psql -d svws -f SVWS_schema_banhang_ext.sql` (thêm `email` vào khách hàng,
bảng `tep_dinh_kem`, `chien_dich_email`, `email_log`).

### (1) Lưu trữ tệp PO / Hợp đồng
File lưu vào `STORAGE_DIR` (mặc định `./storage`; prod trỏ sang mount S3/MinIO), DB giữ metadata.
| Endpoint | Quyền | Việc |
|---|---|---|
| `POST /ban-hang/don-hang/{id}/tep` | THAO_TAC | upload (form: `file`, `loai`=PO/HOP_DONG/KHAC) |
| `GET /ban-hang/don-hang/{id}/tep` | XEM | liệt kê tệp của đơn |
| `GET /ban-hang/tep/{id}/tai-ve` | XEM | tải tệp về |

### (2) Email chào hàng — nội dung phải được DUYỆT
Gửi qua `email_gateway.py` (DEMO ghi log; prod đặt `EMAIL_PROVIDER=SMTP` + cấu hình SMTP).
Nhắm tới khách hàng đã có, lọc theo hạng ABC; chèn `{ten_kh}` vào tiêu đề/nội dung; ghi `email_log` từng dòng.
```
Soạn (THAO_TAC) ─► CHO_DUYET ─► Duyệt nội dung (DUYỆT: TP_KD/CEO) ─► DA_DUYET ─► Gửi (THAO_TAC) ─► DA_GUI
```
Chốt an toàn: gửi khi chưa `DA_DUYET` → 400; chỉ cấp DUYỆT mới duyệt được nội dung.

| Endpoint | Quyền | Việc |
|---|---|---|
| `POST /ban-hang/chien-dich` | THAO_TAC | soạn chiến dịch (CHO_DUYET) |
| `POST /ban-hang/chien-dich/{id}/duyet` | DUYỆT | duyệt nội dung |
| `POST /ban-hang/chien-dich/{id}/gui` | THAO_TAC | gửi (yêu cầu đã duyệt) |
| `GET /ban-hang/chien-dich/{id}/ket-qua` | XEM | log gửi từng KH |

### Cập nhật: địa chỉ gửi + đính kèm khi gửi
- Địa chỉ gửi mặc định: `sv-sales@watersolutions.company` (`EMAIL_FROM`).
- Đính kèm tệp vào chiến dịch: `POST /ban-hang/chien-dich/{id}/tep` (THAO_TAC, trước khi gửi);
  khi gửi, mọi tệp đính kèm đi kèm email tới từng khách hàng. `GET /ban-hang/chien-dich/{id}/tep` để liệt kê.

### Cấu trúc kênh: mọi liên lạc qua hệ thống (không dùng mail cá nhân)
- `lien_lac` ghi nhận MỌI trao đổi với KH (email 1:1, email chiến dịch, cuộc gọi, ghi chú).
- `POST /ban-hang/khach-hang/{id}/gui-email` — gửi 1:1 từ địa chỉ công ty (server kiểm soát "From"), tự ghi nhật ký + audit.
- `POST /ban-hang/khach-hang/{id}/lien-lac` — ghi cuộc gọi/gặp mặt/ghi chú.
- `GET /ban-hang/khach-hang/{id}/lien-lac` — dòng thời gian liên lạc.
- Giao diện: tab "Khách hàng" với gửi email qua hệ thống + nhật ký; không có liên kết mailto (mở mail cá nhân).

### Giai đoạn 1: Thu thư phản hồi vào hệ thống (inbound)
Cổng thư đến `inbound_gateway.py` (DEMO | IMAP). `lien_lac` mở rộng: cho phép chưa gắn KH, thêm tu_email/message_id/da_xu_ly.
| Endpoint | Quyền | Việc |
|---|---|---|
| `POST /ban-hang/dong-bo-phan-hoi` | THAO_TAC | kéo thư mới về (khớp KH theo email, chống trùng Message-ID) |
| `GET /ban-hang/phan-hoi?chua_xu_ly=true` | XEM | hộp thư phản hồi |
| `POST /ban-hang/phan-hoi/{id}/gan-khach` | THAO_TAC | gắn thư chưa khớp vào KH |
| `POST /ban-hang/phan-hoi/{id}/danh-dau` | THAO_TAC | đánh dấu đã xử lý |
Thư khớp KH hiện trong dòng thời gian (huong=DEN). Prod: đặt `INBOUND_PROVIDER=IMAP` + IMAP_*; nên chạy đồng bộ định kỳ (cron/scheduler).

### Giai đoạn 2: AI phân loại + tự xử lý + giao việc kèm SLA
Cổng AI `ai_gateway.py` (DEMO luật tiếng Việt | ANTHROPIC gọi Claude API). `lien_lac` thêm ai_y_dinh/ai_khan/ai_tom_tat/ai_tra_loi; `khach_hang.khong_nhan_email`; bảng mới `cong_viec` (SLA).

Ý định: QUAN_TAM, HOI_KY_THUAT, HEN_GAP, TU_CHOI, KHIEU_NAI, HUY_NHAN, VANG_MAT, SPAM, KHAC. Khẩn: CAO/TRUNG/THAP → SLA 4h/24h/48h.
Tự xử lý: HUY_NHAN → đặt cờ khong_nhan_email + đánh dấu xong; VANG_MAT/SPAM → đánh dấu xong; còn lại → tạo công việc giao người phụ trách kèm hạn SLA. Chiến dịch email tự **bỏ qua** KH đã hủy nhận.

| Endpoint | Quyền | Việc |
|---|---|---|
| `POST /ban-hang/dong-bo-phan-hoi` | THAO_TAC | đồng bộ + AI phân loại + tự xử lý/giao việc |
| `POST /ban-hang/phan-hoi/{id}/phan-tich` | THAO_TAC | phân loại lại 1 thư |
| `GET /ban-hang/cong-viec?mo=&cua_toi=&qua_han=` | XEM | hàng đợi công việc (tính quá hạn) |
| `POST /ban-hang/cong-viec/{id}/trang-thai` | THAO_TAC | MO/DANG_XU_LY/XONG |

Bật AI thật: `AI_PROVIDER=ANTHROPIC`, `ANTHROPIC_API_KEY=...`, `ANTHROPIC_MODEL=claude-sonnet-4-6` (mặc định rớt về luật nếu lỗi). Nên chạy `dong-bo-phan-hoi` định kỳ (cron) để tự phân loại liên tục.

### Giai đoạn 3: Cơ hội (pipeline) + auto báo giá + dashboard + tự xác nhận
Bảng mới `co_hoi` (MOI/QUAN_TAM/BAO_GIA/DAM_PHAN/THANG/THUA); `cong_viec.hoan_thanh_luc` (đo SLA). Khi phân tích thư:
- **QUAN_TAM** → tạo cơ hội (giai đoạn QUAN_TAM) **+ nháp báo giá** (BaoGia trạng thái NHAP, số BG-N…) gắn vào cơ hội để NV hoàn thiện.
- **HOI_KY_THUAT / HEN_GAP** → tạo cơ hội (không nháp báo giá).
- Tất cả vẫn tạo công việc kèm SLA như Giai đoạn 2.

**Tự gửi xác nhận (an toàn, mặc định TẮT):** `AUTO_TRA_LOI=true` + `AUTO_TRA_LOI_YDINH=QUAN_TAM,HOI_KY_THUAT,HEN_GAP`. Chỉ gửi 1 email *xác nhận đã nhận* nội dung **cố định** (không phải nội dung AID tự do), bỏ qua KH đã hủy nhận, có ghi nhật ký, và **vẫn tạo việc cho người** xử lý thực chất (giữ human-in-the-loop).

| Endpoint | Quyền | Việc |
|---|---|---|
| `GET /ban-hang/co-hoi?giai_doan=&cua_toi=` | XEM | danh sách cơ hội (pipeline) |
| `POST /ban-hang/co-hoi/{id}/giai-doan` | THAO_TAC | chuyển giai đoạn (+giá trị, lý do thua); THẮNG/THUA đóng cơ hội |
| `GET /ban-hang/dashboard` | XEM | phễu phản hồi→cơ hội→báo giá→đơn + chỉ số SLA + cơ hội theo giai đoạn |

Giao diện thêm tab **Cơ hội** (pipeline, tóm tắt theo giai đoạn, chuyển giai đoạn) và **Tổng quan** (phễu chuyển đổi, tỉ lệ, SLA đúng hạn, phân bố giai đoạn).

## MUA HÀNG — Giai đoạn 0: Nền & liên kết Bán hàng (giá vốn / lãi-lỗ theo mã đơn)
NCC mở rộng: email, nguoi_phu_trach, han_muc_cong_no (trần dư nợ), dia_chi, ghi_chu. PO (`don_mua`) thêm: don_hang_id (khóa liên kết sang đơn Bán hàng), ngay_hen_giao, ngay_giao_thuc, trang_thai_nhan. Email 1 đầu mối NCC: `EMAIL_FROM_NCC=inf@watersolutions.company`.
| Endpoint | Quyền | Việc |
|---|---|---|
| `POST /ncc/nha-cung-cap` | THAO_TAC | tạo NCC (email, hạn mức công nợ, người phụ trách) |
| `POST /ncc/don-mua` | THAO_TAC | tạo PO, gắn `don_hang_id` + `ngay_hen_giao` |
| `GET /ban-hang/don-hang/{id}/lai-lo` | XEM | doanh thu − giá vốn (tổng PO liên kết) = lãi/lỗ + tỷ suất |
UI Bán hàng → Đơn hàng & PO/Hợp đồng: thêm cột **Mã Bán hàng** (sau Loại, trước Tên tệp) + dòng **Doanh thu / Giá vốn / Lãi-Lỗ** mỗi đơn. Giá vốn GĐ0 tạm theo PO; GĐ1 chốt theo nhận hàng/hóa đơn.

## MUA HÀNG — Giai đoạn 1: Nhận hàng + Công nợ phải trả + Giá vốn thực nhận
`don_mua_ct.so_luong_nhan` theo dõi SL đã nhận từng dòng. Nhận hàng dùng quyền **kho THAO_TAC** (THUKHO).
| Endpoint | Quyền | Việc |
|---|---|---|
| `GET /ncc/don-mua/{id}` | ncc XEM | chi tiết PO + SL đã nhận từng dòng |
| `POST /ncc/don-mua/{id}/nhan-hang` | kho THAO_TAC | nhập kho (qua kho_service) + cập nhật trạng thái nhận (CHUA/MOT_PHAN/DU) + ngày giao thực + sinh **công nợ phải trả** theo giá trị thực nhận, có hạn thanh toán; chặn nhận vượt; tạo PhieuKho(NHAP) |
| `GET /ncc/cong-no?nha_cung_cap_id=&chua_tra=` | ncc XEM | công nợ phải trả (còn lại, cờ quá hạn) |
PO phải **DA_DUYET** mới nhận được. `GET /ban-hang/don-hang/{id}/lai-lo` nay trả **giá vốn thực nhận** & **cam kết**, **lãi/lỗ thực** & **dự kiến**. UI đơn hàng hiển thị cả hai.

## MUA HÀNG — Màn hình Nhà cung cấp (frontend)
viewNCC nâng cấp thành 3 tab: **Nhà cung cấp** (hồ sơ + tạo + đánh giá, hiển thị email & hạn mức công nợ), **Đơn mua (PO)** (tạo PO gắn mã đơn bán + ngày hẹn giao, duyệt theo hạn mức, **nhận hàng** từng dòng → nhập kho + sinh công nợ), **Công nợ phải trả** (còn lại, hạn, quá hạn tô đỏ). Hoạt động cả chế độ demo lẫn live.

## MUA HÀNG — Giai đoạn 2: Trễ hạn giao · Tuổi nợ · Kiểm soát hạn mức · Thanh toán
Duyệt PO thêm **tầng 3**: chặn nếu (dư nợ NCC + giá trị PO) vượt `han_muc_cong_no`.
| Endpoint | Quyền | Việc |
|---|---|---|
| `GET /ncc/giao-hang/tre-han` | ncc XEM | PO trễ so với hẹn giao (số ngày trễ) |
| `GET /ncc/cong-no/tuoi-no` | ncc XEM | tuổi nợ phải trả: chưa đến hạn / 1–30 / 31–60 / 61–90 / >90 |
| `GET /ncc/kiem-soat-cong-no` | ncc XEM | dư nợ vs hạn mức từng NCC (cảnh báo/vượt) |
| `POST /ncc/cong-no/{id}/thanh-toan` | **ke_toan THAO_TAC** | ghi nhận thanh toán NCC (giảm nợ); chặn vượt còn lại |
UI NCC thêm tab **Kiểm soát** (trễ hạn giao + hạn mức công nợ) và tab Công nợ thêm **thẻ tuổi nợ** + nút **Thanh toán** (kế toán).

## MUA HÀNG — Đề xuất mua hàng (1 đầu mối xét duyệt)
`yeu_cau_mua` mở rộng thành quy trình: trang_thai (MOI/DA_DUYET/TU_CHOI/DA_TAO_PO), nha_cung_cap_id, **don_hang_id (Mã bán hàng)**, don_gia, ngay_can, nguoi_duyet, don_mua_id.
| Endpoint | Quyền | Việc |
|---|---|---|
| `POST /ncc/yeu-cau-mua` | ncc THAO_TAC | tạo đề xuất (gắn Mã bán hàng + NCC) |
| `GET /ncc/yeu-cau-mua?trang_thai=` | ncc XEM | hàng đợi đề xuất (đầu mối) |
| `POST /ncc/yeu-cau-mua/{id}/duyet` | **ncc DUYET** | xét duyệt tập trung (TP_CU/CEO) |
| `POST /ncc/yeu-cau-mua/{id}/tu-choi` | ncc DUYET | từ chối kèm lý do |
| `POST /ncc/yeu-cau-mua/{id}/tao-po` | ncc THAO_TAC | chuyển đề xuất ĐÃ DUYỆT → PO (giữ Mã bán hàng) |
Chuỗi: **Đề xuất → duyệt → PO → duyệt PO (hạn mức tiền + hạn mức công nợ) → nhận hàng → công nợ**, Mã bán hàng xuyên suốt tới giá vốn. UI NCC thêm tab **Đề xuất mua**.

### Phân quyền Mua hàng (tóm tắt)
- Tạo đề xuất / tạo PO / nhận-hàng-trên-PO: **NV Mua hàng** (ncc THAO_TAC); nhận hàng cần **kho THAO_TAC** (Thủ kho).
- Duyệt đề xuất + duyệt PO: **TP Cung ứng / CEO** (ncc DUYET) — PO còn ràng hạn mức tiền 'po' (TP_CU ≤10tr, CEO ∞) và hạn mức công nợ NCC.
- Thanh toán công nợ: **Kế toán** (ke_toan THAO_TAC).
- Thủ kho / Kế toán / Admin: XEM module ncc (không tạo/duyệt đề xuất).

## Đề xuất mua hàng — TÁCH THÀNH MODULE ĐỘC LẬP (frontend)
"Đề xuất mua hàng" giờ là mục riêng trên sidebar (nhóm Cung ứng, giữa Kho và Nhà cung cấp), dùng chung quyền `ncc` qua `MODULES.de_xuat.permKey="ncc"` (không cần seed RBAC mới). Tạo + xét duyệt đề xuất nằm ở đây; khi **DA_DUYET**, đề xuất tự xuất hiện ở **Nhà cung cấp → Đơn mua** trong panel "Đề xuất đã duyệt — chờ tạo PO" để tạo PO (giữ Mã bán hàng). Backend không đổi (endpoint vẫn thuộc module ncc).

## Mua hàng — Tự động hóa chọn NCC khi tạo PO từ đề xuất
`GET /ncc/goi-y-ncc?hang_hoa_id=&so_luong=` chấm điểm & xếp hạng NCC cho 1 mặt hàng:
điểm = 40%×(giá rẻ nhất/giá NCC) + 30%×(đánh giá/5) + 30%×(tỷ lệ giao đúng hạn); trừ 30 nếu PO làm **vượt hạn mức công nợ**; loại NCC blacklist. Trả `goi_y_ncc_id` (khuyến nghị = điểm cao nhất còn trong hạn mức).
Panel "Đề xuất đã duyệt — chờ tạo PO" nay: NCC là **dropdown** mặc định = NCC tối ưu (gắn ⭐, kèm giá/điểm/đúng hạn), cho **đổi NCC + sửa đơn giá + hẹn giao**; đổi NCC tự nạp lại giá gần nhất. `tao-po` nhận override nha_cung_cap_id/don_gia/ngay_hen_giao.

## Mua hàng — AI Sourcing Agent (tự tìm/khuyến nghị NCC sau khi đề xuất được duyệt)
`POST /ncc/yeu-cau-mua/{id}/tim-ncc-ai` (quyền ncc XEM): xếp hạng NCC nội bộ (engine `_xep_hang_ncc`) + lớp AI (`ai_gateway.goi_y_ncc_ai`, Anthropic khi AI_PROVIDER=ANTHROPIC + key, fallback luật offline) trả `{khuyen_nghi_ncc_id, ten_khuyen_nghi, ly_do, rui_ro[], hanh_dong (RFQ), ung_vien_moi[] (nhóm/thương hiệu cần kiểm chứng), nguon}`. AI CHỈ khuyến nghị trong danh sách NCC nội bộ (không bịa id); ung_vien_moi là gợi ý nguồn để mời báo giá, không bịa SĐT/tên cụ thể.
Panel "chờ tạo PO": nút **🤖 AI tìm NCC** → hiện khối phân tích + tự chọn NCC khuyến nghị; người dùng vẫn quyết định trước khi tạo PO.

## Mua hàng — (1) AI tự chạy khi duyệt + (3) Dò NCC trên web
- Cấu hình mới: `AUTO_TIM_NCC` (bool, mặc định false), `WEB_SEARCH_TOOL` (mặc định web_search_20250305).
- Duyệt đề xuất: nếu `AUTO_TIM_NCC=true`, hệ thống tự chạy AI Sourcing, lưu `yeu_cau_mua.ai_ncc_id` + `ai_goi_y` (JSON). UI panel tự hiện phân tích + chọn sẵn NCC khuyến nghị (không cần bấm).
- `POST /ncc/yeu-cau-mua/{id}/tim-ncc-web?khu_vuc=` (ncc XEM): dò NCC mới qua **web_search của Claude** (chỉ khi AI_PROVIDER=ANTHROPIC + key + tài khoản có web search), trả ứng viên {ten,website,nguon_url,ghi_chu,kiem_chung=false}. DEMO/lỗi → trả nhóm nguồn gợi ý + thông báo. UI: nút **🌐 Web** + nút **Thêm vào hồ sơ NCC** (gắn nhãn "cần kiểm chứng").
- AI chỉ khuyến nghị trong NCC nội bộ; NCC từ web luôn cần bộ phận mua kiểm chứng (pháp lý/năng lực/báo giá) trước khi giao dịch.

## Mua hàng — Báo giá NCC (giá chào hiện tại) cho AI & web cùng dùng
Bảng mới `bao_gia_ncc` (nha_cung_cap_id, hang_hoa_id, don_gia, so_luong_toi_thieu, hieu_luc_den, nguon THU_CONG/RFQ/WEB).
| Endpoint | Quyền | Việc |
|---|---|---|
| `POST /ncc/bao-gia` | ncc THAO_TAC | nhập báo giá NCC |
| `GET /ncc/bao-gia?hang_hoa_id=&nha_cung_cap_id=&con_hieu_luc=` | ncc XEM | tra báo giá |
Engine `_xep_hang_ncc` nay **ưu tiên giá báo giá còn hiệu lực** (nguon_gia=BAO_GIA) hơn giá lịch sử (LICH_SU); báo giá hết hạn bị bỏ. Mỗi ứng viên trả thêm gia_dung/gia_bao_gia/gia_lich_su/nguon_gia/hieu_luc_den. AI nêu rõ "báo giá … HL đến …" trong lý do. Panel "chờ tạo PO": dropdown hiện giá BG/LS + HL; nút **💲 Báo giá** nhập giá chào tại chỗ → gợi ý cập nhật ngay; đơn giá PO mặc định theo giá đang dùng.

## Mua hàng — RFQ 1 đầu mối (email + nhật ký) & tab Báo giá
- Bảng mới `rfq` + `rfq_log`. Gửi RFQ qua email provider, đầu mối `email_from_ncc=inf@watersolutions.company`.
| Endpoint | Quyền | Việc |
|---|---|---|
| `POST /ncc/rfq` | ncc THAO_TAC | gửi RFQ tới nhiều NCC (có nhật ký) |
| `POST /ncc/yeu-cau-mua/{id}/gui-rfq` | ncc THAO_TAC | gửi RFQ theo đúng mặt hàng/SL của đề xuất |
| `GET /ncc/rfq`, `GET /ncc/rfq/{id}` | ncc XEM | danh sách & chi tiết nhật ký RFQ |
- UI: panel "chờ tạo PO" thêm nút **✉️ RFQ** (chọn nhiều NCC, mặc định top gợi ý + hạn báo giá) → gửi từ 1 đầu mối, ghi nhật ký. NCC thiếu email → đánh dấu không gửi được.
- Tab **Báo giá**: bảng toàn bộ giá chào theo mặt hàng/NCC + trạng thái (Còn hiệu lực / **Sắp hết hạn ≤7 ngày** / **Hết hạn** tô đỏ) + thẻ cảnh báo; form thêm báo giá; **Nhật ký RFQ** (đầu mối, hạn, số NCC đã gửi).

## Mua hàng — Tách "From" email theo kênh (hoàn thiện 1 đầu mối)
`EmailProvider.gui(..., gui_tu=None)`: nếu truyền `gui_tu` thì dùng làm From (+ Reply-To ở SMTP), mặc định `email_from` (bán hàng) — tương thích ngược.
- RFQ gửi với `gui_tu=email_from_ncc` (inf@watersolutions.company); nhật ký ghi rõ đầu mối gửi.
- `gui_email_ncc(db, don_mua)` nay GỬI THẬT email xác nhận PO tới NCC từ đầu mối mua hàng (trước chỉ print); NCC thiếu email → bỏ qua.
Thật: đặt `EMAIL_PROVIDER=SMTP` + SMTP_* ; đảm bảo mailbox/inf@ là alias hợp lệ để gửi đúng From.

## Mua hàng — Tự chấm điểm NCC sau giao hàng (khép vòng chất lượng)
- Cấu hình `AUTO_CHAM_DIEM_NCC` (mặc định true). Phiếu nhận thêm `dat_qc` (Đạt QC).
- Khi PO nhận **ĐỦ**: tự tính điểm 0–5 = đúng hạn (0–2, trừ 0.2/ngày trễ) + QC (0–2) + đủ lượng (1); ghi `danh_gia_ncc`, cập nhật `nha_cung_cap.diem_danh_gia` = TB các lần; điểm TB<2 và ≥2 lần kém → tự **blacklist**.
- API nhận hàng trả `danh_gia_ncc{diem_giao_hang, diem_danh_gia_moi, so_lan_danh_gia, dung_han, dat_qc}`. `GET /ncc/nha-cung-cap/{id}/lich-su-danh-gia` xem lịch sử.
- Điểm này nuôi trực tiếp **gợi ý NCC + AI Sourcing** (đánh giá 30% trọng số); NCC blacklist bị loại khỏi gợi ý. UI phiếu nhận có ô **Đạt QC**; nhận xong toast điểm giao hàng & điểm TB mới.

## Mua hàng — RFQ nâng cấp: email hỏi giá chuyên nghiệp, đầy đủ
- Cấu hình công ty: `CONG_TY_TEN`, `CONG_TY_SLOGAN` (We Have Solutions), `CONG_TY_DIA_CHI`.
- Trường nội dung RFQ: quy_cach, don_vi, noi_giao, thoi_gian_giao, dieu_kien_thanh_toan, yeu_cau_khac, han_bao_gia; có thể `tieu_de`/`noi_dung` để biên tập tay (override mẫu).
- `POST /ncc/yeu-cau-mua/{id}/rfq-preview` (XEM): dựng email mẫu chuyên nghiệp (THÔNG TIN HÀNG HÓA / YÊU CẦU GIAO HÀNG & THANH TOÁN / NỘI DUNG BÁO GIÁ CẦN CUNG CẤP + chữ ký công ty) để xem trước, không gửi.
- `gui-rfq` & `/rfq`: nếu có `noi_dung` đã biên tập thì gửi đúng nội dung đó; nếu không, tự dựng mẫu. Lưu `rfq.noi_dung` để truy vết; `GET /ncc/rfq/{id}` trả `noi_dung`.
- UI: form RFQ thêm các ô thông tin sản phẩm/điều kiện + chọn tất cả/bỏ chọn NCC (hiện email) + nút **Xem trước email** (đổ ra tiêu đề + nội dung có thể chỉnh) + **Gửi RFQ**. Tab Báo giá: nhật ký RFQ có nút **Xem email** mở nội dung đã gửi.

## Mua hàng — Chứng từ PO gửi NCC (từ báo giá, có chỉnh sửa, gửi email)
- `POST /ncc/don-mua/{id}/po-preview` (XEM): dựng chứng từ PO chuyên nghiệp (Số PO, tham chiếu báo giá còn hiệu lực, bảng hàng hóa: ĐVT/SL/đơn giá/thành tiền, tổng tiền, điều kiện giao-thanh toán, chữ ký công ty). Đơn giá lấy từ dòng PO (đã set từ báo giá).
- `POST /ncc/don-mua/{id}/gui-po` (THAO_TAC): gửi PO tới email NCC từ inf@watersolutions.company; nhận điều kiện + `tieu_de`/`noi_dung` biên tập (override); cập nhật ngay_hen_giao nếu đổi; NCC thiếu email → không gửi. Email xác nhận PO khi duyệt cũng dùng chung mẫu này.
- UI: bấm **Tạo PO** mở **form PO (modal)** đổ sẵn nội dung từ báo giá, cho sửa điều kiện + **Xem trước** + **Gửi PO cho NCC**; danh sách Đơn mua có nút **Gửi PO** để gửi/gửi lại.

## Mua hàng — Chứng từ PO PDF theo mẫu SVWS (tải về / lưu / gửi kèm email)
- Cần `reportlab` (đã thêm vào requirements) + font DejaVu (Ubuntu có sẵn). Thông tin công ty đọc từ cấu hình `CONG_TY_*` (đã cập nhật theo letterhead: CÔNG TY TNHH GPKT SÓNG VIỆT...).
- `app/po_pdf.py`: `tao_po_pdf(path, data, cong_ty)` sinh PO 2 trang đúng mẫu (header logo + ô tiêu đề; THÔNG TIN NCC; bảng SP/DV có VAT & thành tiền gồm VAT; Tạm tính/Tổng cộng; ĐIỀU KHOẢN & XÁC NHẬN; trang 2 PHIẾU XÁC NHẬN NCC với checkbox & chữ ký 2 bên).
- `POST /ncc/don-mua/{id}/po-pdf` (XEM): nhận trường (ma_yeu_cau, hieu_luc_den, vat, specs[], nguoi_lien_he/dat/duyet, điều kiện...) → trả file PDF và **lưu** vào `STORAGE_DIR/po/PO_{so}.pdf`.
- `gui-po`: thêm `dinh_kem_pdf=true` → tự sinh PDF và **đính kèm** vào email gửi NCC từ inf@watersolutions.company.
- UI: form PO có mục chứng từ (mã, hiệu lực, VAT, mô tả/spec từng dòng, người liên hệ/đặt/duyệt) + nút **📄 Tải PDF (lưu chứng từ)** và **✉️ Gửi PO (kèm PDF)**. Ảnh chữ ký/đóng dấu: đặt `PDF_CHU_KY_PATH`.

## Mua hàng — Đề xuất NHIỀU sản phẩm + đính kèm dự toán
- Bảng mới `yeu_cau_mua_ct` (dòng đề xuất) + cột `yeu_cau_mua.dinh_kem_url`, `dinh_kem_file`.
- `POST /ncc/yeu-cau-mua` nhận `items:[{hang_hoa_id,so_luong,don_gia?,ghi_chu?}]` (hoặc 1 sản phẩm như cũ) + `dinh_kem_url` (link Google Sheet). Header lấy dòng đầu (tương thích AI Sourcing/PO).
- `GET /ncc/yeu-cau-mua` & `/{id}` trả `items[]`, `so_dong`, `dinh_kem_url/file`.
- `POST /ncc/yeu-cau-mua/{id}/dinh-kem` (multipart) tải tệp dự toán (xlsx/csv/pdf) → lưu `STORAGE_DIR/de_xuat/`; `GET .../dinh-kem` tải lại.
- `tao-po` nay tạo **PO nhiều dòng** từ toàn bộ dòng đề xuất (đơn giá panel áp cho dòng đầu, các dòng khác giữ giá riêng) → PO PDF nhiều mặt hàng.
- UI: form đề xuất có danh sách sản phẩm (**+ Thêm sản phẩm**, xóa dòng), ô **Link Google Sheet** và **tải tệp**; hàng đợi hiện badge “+N mặt hàng” và link 📊 Sheet / 📎 tệp.

## Mua hàng — Mỗi dòng đề xuất chọn NCC riêng → tách PO theo NCC
- `yeu_cau_mua_ct` thêm cột `nha_cung_cap_id`. Item create nhận `nha_cung_cap_id` mỗi dòng (rỗng = theo NCC đề xuất chung).
- `tao-po` gom các dòng theo NCC: mỗi NCC → 1 PO (cùng NCC gộp 1 PO). Trả `{so_po, po:[{id,so,nha_cung_cap_id,tong_tien}]}`. Đơn giá panel áp cho dòng đầu; các dòng khác giữ giá riêng.
- UI: mỗi dòng sản phẩm có ô **Nhà cung cấp** (mặc định “— theo đề xuất —”). Tạo PO sinh nhiều PO theo NCC; nếu 1 PO thì mở form gửi luôn, nhiều PO thì chuyển sang danh sách Đơn mua để gửi từng PO.

## Mua hàng — Ký số & đóng dấu vào PO PDF
- Ảnh con dấu + chữ ký giám đốc bundled tại `app/assets/e_sign.png` (đã xử lý nền trong suốt). Mặc định `tao_po_pdf` chèn vào ô **Người duyệt** (trang 1) và **Đại diện bên mua** (trang 2). Thay ảnh khác: đặt `PDF_CHU_KY_PATH`.
- Tham số `ky_so` (mặc định True) trong PO PDF; UI form PO có checkbox **“Ký số & đóng dấu”** để bật/tắt (bản nháp gửi nội bộ có thể tắt). Áp dụng cho cả Tải PDF và Gửi PO kèm PDF.

## Kế toán — Quản lý tiền + Phiếu thu/chi (duyệt nhiều cấp) + truy vết mã hàng bán
- Migration `SVWS_schema_ketoan_ext.sql`: bảng `tai_khoan_quy` (quỹ TM/NH), `phieu_thu_chi`; bổ sung `but_toan.don_hang_id/quy_id/nguon/nguon_id`; seed 2 quỹ + hạn mức duyệt loại **thu_chi** (KTT ≤ 50tr, CEO ∞).
- Router `app/routers/ke_toan_quy.py` (đăng ký trong main): 
  - Quỹ & sổ quỹ: `GET /ke-toan/quy`, `POST /ke-toan/quy`, `GET /ke-toan/quy/{id}/so-quy` (số dư lũy kế).
  - Phiếu thu/chi: `POST /ke-toan/phieu` → NHAP/CHO_DUYET; `/trinh`, `/duyet` (kiểm hạn mức nhiều cấp), `/tu-choi`, `/huy`. Khi DUYỆT: cộng/trừ quỹ + sinh **bút toán kép** + **cấn trừ công nợ** + gắn **mã hàng bán**.
  - Truy vết: `GET /ke-toan/the-ma-ban/{don_hang_id}` (DT−GV−CP, PO/phiếu/bút toán), `GET /ke-toan/lai-lo-ma-ban`, `GET /ke-toan/can-doi-phat-sinh` (Nợ=Có), `GET /ke-toan/tong-quan`.
- Phân quyền: NV_KT lập/trình; KTT/CEO duyệt theo trần tiền; ADMIN xem. Định khoản đối ứng tự suy: phải thu→131, phải trả→331, hoặc TK người dùng nhập.
- UI: menu **Kế toán** mở giao diện đa tab (Tổng quan · Quỹ & sổ quỹ · Phiếu thu–chi có duyệt · Lãi/lỗ mã bán + thẻ chi tiết · Cân đối phát sinh).

### Kế toán — Kết nối phiếu thu/chi ↔ công nợ NCC/KH (cấn trừ)
- `GET /ke-toan/cong-no-mo?loai=PHAI_THU|PHAI_TRA`: danh sách công nợ CHƯA tất toán kèm **tên đối tác**, còn lại, hạn, cờ quá hạn — đổ vào ô "Cấn trừ công nợ" của phiếu.
- Lập phiếu: chặn gắn sai loại (THU chỉ cấn trừ PHẢI THU, CHI chỉ cấn trừ PHẢI TRẢ), chặn vượt số còn lại / khoản đã tất toán; **tự gán đối tác** theo công nợ.
- Khi duyệt: cộng `da_thanh_toan` của khoản nợ → trạng thái THU_MOT_PHAN/THU_DU (KH) hoặc TRA_MOT_PHAN/DA_TRA (NCC); bút toán Nợ 111/112·Có 131 (thu) hoặc Nợ 331·Có 111/112 (chi). Khoản tất toán tự rời khỏi danh sách cấn trừ.
- UI: ô công nợ lọc theo loại phiếu, hiện tên đối tác + còn lại + hạn, tự điền số tiền = còn lại.

### Kế toán — Quản lý hóa đơn mua & bán (kiểm soát doanh thu / chi phí)
- Migration bổ sung `hoa_don`: so, khach_hang_id, nha_cung_cap_id, tk_chi_phi, dien_giai, da_hach_toan, trang_thai.
- `hach_toan.py`: HĐ bán gắn `don_hang_id` (Nợ 131/Có 511, 3331); thêm `hach_toan_hoa_don_mua` (Nợ 632/642·1331/Có 331).
- Endpoint: `GET /ke-toan/hoa-don?loai=BAN|MUA` (enrich đối tác/mã bán/công nợ); `POST /ke-toan/hoa-don` (ghi nhận HĐ → tự sinh công nợ + hạch toán doanh thu/chi phí + thuế); `POST /ke-toan/hoa-don/{id}/hach-toan`; `POST .../phat-hanh-hddt` (HĐĐT, đã có).
- **Vòng giao dịch phát sinh**: HĐ bán → phải thu + doanh thu → phiếu THU cấn trừ → giảm nợ + tăng quỹ. HĐ mua → phải trả + chi phí/giá vốn → phiếu CHI cấn trừ → giảm nợ + giảm quỹ. Tất cả gắn mã hàng bán → lên thẻ Lãi/lỗ + Cân đối phát sinh (Nợ=Có).
- Đã gỡ endpoint `GET /ke-toan/hoa-don` cũ (trùng route, chưa enrich) trong ke_toan.py.
- UI: thêm tab **Hóa đơn** (ghi nhận HĐ bán/mua, chọn TK chi phí cho HĐ mua, tạo công nợ + hạch toán, phát hành HĐĐT).

### Giao diện — Mọi droplist là ô gõ-để-tìm
- `_enhanceSelects` tự biến mọi `<select>` thành ô gõ-để-tìm (lọc không dấu, gõ "sai gon" ra "Sài Gòn"); giữ nguyên id/value/onchange của select gốc nên `gv(id)`, repopulate `innerHTML`, đọc theo class đều chạy như cũ. `_initCbxObserver` (gọi trong startApp) theo dõi DOM để tự nâng cấp cả select trong popup và bảng động.
- Chừa control đặc thù bằng thuộc tính `data-nocbx` (vd: select đổi vai trò ở pill demo). Tùy biến placeholder bằng `data-ph`.

### Kế toán — Tạm ứng / Trả trước theo mã hàng bán
- `phieu_thu_chi`: thêm `la_tam_ung` (phiếu là khoản ứng trước) + `da_can_tru` (phần đã cấn trừ vào hóa đơn).
- Lập phiếu THU/CHI tích **"Tạm ứng / Trả trước"** (bắt buộc gắn mã hàng bán, không cấn trừ công nợ): KH ứng trước → Nợ 111/112·Có **131**; trả trước NCC → Nợ **331**·Có 111/112. Tiền vào/ra quỹ ngay.
- Khi lập **hóa đơn** cho mã hàng bán đó: tự **cấn trừ** các khoản tạm ứng cùng chiều (THU↔HĐ bán, CHI↔HĐ mua) vào công nợ vừa sinh → giảm số phải thu/phải trả; tăng `da_can_tru`. Không sinh bút toán thừa (131/331 tự net).
- Endpoint `GET /ke-toan/tam-ung?don_hang_id=&loai=` (khoản còn lại chưa cấn trừ). Thẻ & Lãi/lỗ mã hàng bán bổ sung: KH tạm ứng, trả trước NCC (kèm phần còn lại), đã xuất HĐ bán.
- UI: form phiếu có checkbox tạm ứng + ô NCC (khi trả trước); danh sách phiếu gắn nhãn "Tạm ứng · còn X"; tab Lãi/lỗ thêm 2 cột tạm ứng; thẻ mã bán thêm thẻ KH tạm ứng / Trả trước NCC.

### Kế toán — Cam kết đặt cọc theo đơn hàng + Báo cáo Trả trước
- `don_hang.ty_le_dat_coc` (% cọc dự kiến). `_lai_lo_1` tính `dat_coc_du_kien`, `dat_coc_da_ung` (= tạm ứng thu), `coc_trang_thai` (KHONG/THIEU/DU/VUOT), `coc_chenh_lech`.
- `PUT /ke-toan/ma-ban/{id}/dat-coc {ty_le}` đặt % cọc. `GET /ke-toan/bao-cao-tra-truoc` → khoản còn treo theo từng KH/NCC + tình trạng đặt cọc của các đơn có cam kết.
- UI: tab **Trả trước** — đặt % cọc từng mã hàng bán (ô nhập + Lưu), cảnh báo Thiếu/Đủ/Vượt (đơn thiếu cọc tô đỏ), thẻ tổng (khách treo / NCC treo / số đơn thiếu cọc), và bảng tổng hợp khoản trả trước còn treo theo đối tác.

### Kế toán — Thống kê thu–chi (dòng tiền)
- `GET /ke-toan/thong-ke-thu-chi?tu_ngay=&den_ngay=&quy_id=&don_hang_id=` (phiếu ĐÃ DUYỆT): tổng thu/chi/ròng, theo tháng, theo loại tài khoản đối ứng (lấy từ bút toán), theo quỹ, và **theo mã hàng bán** (kiểm soát tiền dự án). Loại đối ứng đọc từ bút toán đã sinh nên chính xác kể cả khi để hệ thống tự suy.
- UI: tab **Thống kê thu–chi** — lọc theo kỳ (từ/đến) và quỹ; thẻ tổng thu/chi/ròng/số phiếu; biểu đồ cột thu–chi theo tháng; bảng theo mã hàng bán (dự án), theo loại tài khoản, theo quỹ.

## Tài chính — Chỉ số doanh nghiệp + Cảnh báo + Cố vấn AI
- `GET /tai-chinh/chi-so?so_ngay=90`: tính từ sổ cái/công nợ/quỹ/tồn kho:
  - Thanh khoản: thanh toán hiện hành / nhanh / tiền mặt.
  - Sinh lời (theo kỳ): doanh thu, giá vốn, chi phí, biên LN gộp/thuần.
  - Hiệu quả & công nợ: kỳ thu tiền (DSO), kỳ trả tiền (DPO), số ngày tồn kho, phải thu/phải trả (+ quá hạn).
  - Dòng tiền & tài sản: tiền & NH, tồn kho, tiền vào/ra kỳ, dòng tiền ròng, chi BQ/tháng, số tháng tiền mặt còn lại.
  - `canh_bao[]` theo ngưỡng (CAO/TRUNG/THAP) + `diem_suc_khoe` (0–100).
- `POST /tai-chinh/tu-van-ai?so_ngay=90`: cố vấn tài chính AI (CFO ảo) — `ai_gateway.tu_van_tai_chinh` (Fake offline theo quy tắc / Anthropic khi đặt `AI_PROVIDER=ANTHROPIC` + `ANTHROPIC_API_KEY`). Trả `{suc_khoe, danh_gia, nhan_dinh[], uu_tien[]}`.
- UI: menu **Tài chính** — chọn kỳ (30/90/180/365 ngày), thẻ sức khỏe + nhóm chỉ số (màu theo ngưỡng), bảng **Cảnh báo tài chính** kèm gợi ý xử lý, và khu **Cố vấn AI** (nút "Phân tích bằng AI" → đánh giá + khuyến nghị ưu tiên).

### Tài chính — Bảng cân đối rút gọn + ROA/ROE/đòn bẩy
- Bảng `tham_so_tai_chinh` (1 dòng): von_chu_so_huu, tai_san_co_dinh, no_dai_han, chi_co_dinh_thang. `GET/PUT /tai-chinh/tham-so`.
- `GET /tai-chinh/can-doi-ke-toan?so_ngay=90`: tài sản (TSNH tự tính + TSCĐ khai báo) / nguồn vốn (nợ NH+DH + VCSH), chênh lệch (LN giữ lại chưa khai), và ROA, ROE, hệ số nợ, nợ/VCSH, hệ số tự tài trợ (LN quy năm = LN kỳ ×365/so_ngay). Cảnh báo đòn bẩy nợ >70%, ROE âm.

### Tài chính — Dự báo dòng tiền 13 tuần
- `GET /tai-chinh/du-bao-dong-tien?so_tuan=13`: tồn đầu = Σ quỹ; xếp phải thu/phải trả theo **hạn công nợ** vào từng tuần (quá hạn dồn tuần 1), cộng chi phí cố định/tuần (chi_co_dinh_thang×7/30); tính tồn cuối lũy kế mỗi tuần, cờ thiếu hụt, tuần thiếu đầu tiên, tồn thấp nhất. Khoản chưa có hạn báo riêng (chưa đưa vào dự báo).
- UI: menu **Tài chính** chia 3 tab — *Tổng quan & cảnh báo*, *Cân đối & ROA/ROE* (form khai báo + bảng cân đối 2 cột + thẻ ROA/ROE/đòn bẩy), *Dự báo dòng tiền 13 tuần* (biểu đồ số dư theo tuần, tuần âm tô đỏ, bảng chi tiết + cảnh báo thiếu hụt).

## Nhân sự & Lương — quy trình lương tự động
- Migration `SVWS_schema_nhansu_ext.sql`: mở rộng `nhan_vien` (lương đóng BH, người phụ thuộc, 4 phụ cấp, MST, TK ngân hàng, email, tk_chi_phi), `bang_luong` (công chuẩn/thực tế, OT thường/cuối tuần/lễ, lương thực tế, tạm ứng, BH phần DN, chi phí DN, email_sent), bảng `ky_luong` (header theo tháng: công chuẩn, ngày chốt ≤7, trạng thái, tổng chi phí).
- `luong_service.tinh_luong`: prorate theo công; OT ×1,5/×2/×3; BHXH/BHYT/BHTN NLĐ 10,5% & DN 21,5% có **trần đóng** (46,8tr / 99,2tr); TNCN lũy tiến với **miễn thuế cơm trưa ≤730k và phần vượt OT**; trả cả chi phí lương DN.
- `hach_toan_luong`: Nợ CP(642/622/627)/Có 334 (tổng thu nhập) · Nợ CP/Có 3383-3384-3389 (BH phần DN) · Nợ 334/Có 3383-3384-3389-3335 (khấu trừ NLĐ); gắn nguồn 'LUONG'.
- Endpoints `/nhan-su`: `ho-so` + `nhan-vien/{id}/ho-so` (hồ sơ lương); `ky-luong` POST (sinh bảng cho NV đang làm, hạn chốt mặc định ngày 7), GET list/`{thang}` (chi tiết + tổng + cờ trễ hạn); `phieu-luong/{id}` GET/PUT (chấm công/OT/tạm ứng → tính lại); `ky-luong/{thang}/chot` (KTT/CEO: tính lại + hạch toán + khóa); `ky-luong/{thang}/gui-email` (email phiếu lương HTML từng người, đánh dấu đã gửi, cờ trễ hạn).
- UI: menu **Nhân sự & Lương** 2 tab — *Hồ sơ lương* (khai báo, sửa qua modal) và *Bảng lương theo kỳ* (chọn tháng → sinh bảng → chấm công/OT/tạm ứng inline → thẻ tổng chi phí lương DN → Chốt & hạch toán → Gửi email; phiếu lương xem chi tiết qua modal; cảnh báo trễ hạn ngày 7).

## Tài chính — Quản lý tiền vay (lãi vay, kỳ đáo hạn)
- Bảng `khoan_vay` (khế ước: bên cho vay, loại NGAN_HAN/DAI_HAN, gốc, lãi suất %/năm, phương thức, ngày nhận, số kỳ, chu kỳ tháng, đáo hạn, dư nợ, trạng thái) + `lich_tra_no` (lịch từng kỳ: dư nợ đầu, gốc, lãi, tổng, dư nợ cuối, đã trả).
- `vay_service.sinh_lich`: 3 phương thức — **GOC_DEU** (gốc đều, lãi giảm dần), **TRA_DEU** (niên kim, tổng trả đều), **GOC_CUOI** (lãi hàng kỳ, gốc trả cuối). Lãi suất kỳ = lãi năm × số tháng/kỳ ÷ 12.
- Hạch toán tự động: nhận tiền **Nợ 111/112 / Có 341** (+ tăng quỹ); trả nợ **Nợ 341 (gốc) + Nợ 635 (lãi vay) / Có 111/112** (− quỹ).
- Endpoints `/vay`: POST tạo khế ước (+ sinh lịch + hạch toán); GET danh sách / `tong-quan` (dư nợ NH/DH, lãi còn phải trả, quá hạn) / `sap-toi?so_ngay=` (kỳ đến hạn) / `{id}` (lịch đầy đủ); POST `{id}/tra-ky/{ky}` (trả 1 kỳ + hạch toán, cập nhật dư nợ; trả hết → DA_TAT_TOAN).
- Nối Tài chính: dư nợ vay tự cộng vào **nợ ngắn/dài hạn** (bảng cân đối, chỉ số thanh khoản, đòn bẩy); **lãi vay 635** thành chỉ số riêng; lịch trả nợ chưa trả tự đưa vào **dự báo dòng tiền 13 tuần** theo ngày đến hạn.
- UI: Tài chính → tab **Tiền vay** — thẻ tổng (dư nợ, lãi phải trả, kỳ quá hạn), form khế ước vay mới, danh sách khoản vay (kỳ tới + quá hạn), modal lịch trả nợ với nút "Trả kỳ".

### Nhân sự & Lương — phụ cấp phát sinh + khấu trừ nghỉ KP / đi trễ / khác
- `bang_luong` thêm: phu_cap_khac (phụ cấp/thưởng phát sinh trong kỳ), ngay_nghi_kpep, so_phut_di_tre, khau_tru_nghi, khau_tru_tre, khau_tru_khac.
- `tinh_luong`: trừ **nghỉ không phép** theo đơn giá ngày (lương/công chuẩn) và **đi làm trễ** theo đơn giá phút (giảm thu nhập trước thuế); cộng **phụ cấp phát sinh** vào thu nhập; **khấu trừ khác** trừ sau thuế (như tạm ứng). Thuế/BH tính trên thu nhập sau khi đã giảm nghỉ KP/đi trễ.
- UI: nút **Chấm công** mở modal nhập công/OT(3 loại)/phụ cấp phát sinh/nghỉ KP/đi trễ/tạm ứng/khấu trừ khác → tính lại tức thì. Bảng lương thêm cột Phụ cấp (hiện phần phát sinh) và Khấu trừ (nghỉ KP + đi trễ + khác + tạm ứng). Phiếu lương & email phiếu lương hiển thị đầy đủ các dòng này.

### Nhân sự & Lương — Tham số theo luật (cập nhật được) + tiếp nhận chấm công
- Bảng `tham_so_luong` (1 dòng): tỷ lệ BHXH/BHYT/BHTN (NLĐ & DN), trần đóng BHXH/BHYT & BHTN, giảm trừ bản thân/người phụ thuộc, miễn thuế cơm trưa, hệ số OT (thường/cuối tuần/lễ), lương cơ sở, LTT vùng, và **biểu thuế TNCN** (JSON các bậc). Mặc định đúng luật hiện hành.
- `luong_service.tinh_luong(..., cfg=)`: mọi tỷ lệ/ngưỡng/biểu thuế lấy từ `cfg` (thiếu thì dùng mặc định) → đổi luật chỉ cần cập nhật tham số, không sửa code. `tinh_tncn(amount, bieu=)` nhận biểu thuế cấu hình.
- `GET/PUT /nhan-su/tham-so-luong` (DUYET) — cấu hình tham số luật; lương các kỳ **chưa chốt** sẽ tính lại theo tham số mới.
- `POST /nhan-su/ky-luong/{thang}/cham-cong-import` — **điểm tiếp nhận dữ liệu chấm công** cho app chấm công (sẽ làm sau): nhận danh sách {nhan_vien_id|ma, cong_thuc_te, OT thường/cuối tuần/lễ, ngay_nghi_kpep, so_phut_di_tre}; khớp theo id hoặc mã NV, cập nhật bảng lương kỳ chưa chốt và tính lại; trả số bản ghi cập nhật & danh sách không khớp.
- UI: nút **⚖️ Tham số lương theo luật** (tab Hồ sơ lương) mở modal cấu hình đầy đủ (tỷ lệ BH %, trần, giảm trừ, hệ số OT, biểu thuế); ghi chú đồng bộ chấm công trong tab Bảng lương.

## Kế toán — Trích lập quỹ (được trừ / sau thuế) + cảnh báo trần TNDN 2025
- Bảng `quy_trich_lap` (danh mục 9 quỹ, seed): phân loại `ban_chat` TRUOC_THUE (được trừ) / SAU_THUE (không được trừ), tài khoản Nợ/Có, mã giới hạn (KHCN_20 / PHUC_LOI_1THANG). `giao_dich_quy` lưu trích lập / sử dụng.
- Quỹ trước thuế (được trừ): dự phòng nợ phải thu khó đòi (642/2293), giảm giá HTK (632/2294), giảm giá đầu tư (635/2291), bảo hành (641/352), **Quỹ KH&CN (642/356)**. Quỹ sau thuế: khen thưởng (421/3531), phúc lợi (421/3532), đầu tư phát triển (421/414), dự phòng tài chính (421/418).
- Endpoints `/quy-trich-lap`: `danh-muc`, `GET` (tổng quan số dư trước/sau thuế), `trich` (hạch toán Nợ tk_no/Có tk_co + tăng số dư + cảnh báo), `su-dung` (dự phòng→hoàn nhập, quỹ khác→chi tiền 111; chặn vượt số dư), `canh-bao?nam=&thu_nhap_tinh_thue=`, `{ma}/lich-su`.
- Cảnh báo theo Luật TNDN 2025: **Quỹ KH&CN ≤ 20% thu nhập tính thuế** (ước tính lợi nhuận năm từ sổ cái nếu không nhập tay); **chi phúc lợi ≤ 1 tháng lương bình quân** (= Σ quỹ lương năm ÷ 12 từ kỳ lương).
- UI: Kế toán → tab **Trích lập quỹ** — thẻ tổng (quỹ trước/sau thuế, số cảnh báo), panel kiểm soát trần KH&CN & phúc lợi, form trích lập/sử dụng (quỹ nhóm theo tính chất), bảng quỹ với badge "Được trừ"/"Sau thuế" + lịch sử.
