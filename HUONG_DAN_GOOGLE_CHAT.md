# Hướng dẫn kết nối Google Chat cho tính năng Nhắc việc (SVWS)

Tài liệu này dành cho **người quản trị Google Workspace** của công ty.
Sau khi làm xong, hệ thống SVWS sẽ tự nhắn tin nhắc việc cho nhân viên qua Google Chat.

Hiện hệ thống đang ở chế độ **DEMO** (chưa gửi thật). Chọn **một** trong hai cách dưới.

---

## Cách A — Nhắn riêng từng người (đầy đủ nhất, ~30–45 phút, CẦN quyền admin)

### Bước 1. Tạo project trên Google Cloud
1. Vào https://console.cloud.google.com
2. Tạo project mới, đặt tên: `SVWS Bot`

### Bước 2. Bật Google Chat API
1. Trong project vừa tạo, vào **APIs & Services → Library**
2. Tìm **Google Chat API** → bấm **Enable**

### Bước 3. Tạo Service Account và lấy khóa
1. Vào **APIs & Services → Credentials → Create Credentials → Service account**
2. Đặt tên: `svws-nhac-viec` → **Create and continue** → **Done**
3. Bấm vào service account vừa tạo → tab **Keys** → **Add key → Create new key**
4. Chọn định dạng **JSON** → **Create** → máy sẽ tải về một file `.json`
5. **Giữ file này cẩn thận** — nó là chìa khóa, ai có cũng gửi tin được

### Bước 4. Cấu hình Chat app
1. Vào **Google Chat API → Configuration** (trong cùng project)

2. ⚠️ **TẮT công tắc "Enable Interactive features"** (ở đầu trang)

   > Bot này **chỉ gửi tin, không nhận tin**. Mục *Functionality / Connection settings /
   > Triggers* là dành cho bot NHẬN tin nhắn — ta không cần.
   > Nếu để bật, Google bắt buộc điền các ô `App command *` và `Added to space *`
   > (có dấu sao = bắt buộc), mà ta không có endpoint nào để điền.
   > **Tắt công tắc là toàn bộ các mục đó biến mất.**

3. Điền phần thông tin app:
   - **App name**: `Nhắc việc SVWS`
   - **Avatar URL**: *bắt buộc*, phải là link ảnh công khai. Chưa có thì tạm dùng
     `https://www.gstatic.com/images/branding/product/2x/chat_48dp.png`
   - **Description**: `Nhắc việc tự động từ hệ thống SVWS`

4. Mục **Visibility**: chọn cho miền `watersolutions.company` (hoặc toàn miền)

5. **Save**

### Bước 5. Cài Chat app cho toàn công ty  ⚠️ BẮT BUỘC
> Thiếu bước này thì bot **không nhắn riêng cho ai được**.

1. Vào **Google Admin console** (admin.google.com)
2. **Apps → Google Workspace → Google Chat → Manage Chat apps**
3. Tìm app `Nhắc việc SVWS` → đặt trạng thái **Allowed / ON for everyone**

> **Có thể cần thêm một lần "chào" bot.** Google chỉ cho bot nhắn riêng với người
> **đã có cuộc trò chuyện** với bot. Cài cho toàn miền giúp mọi người *tìm thấy* bot,
> nhưng có thể vẫn cần mỗi nhân viên mở Google Chat → tìm `Nhắc việc SVWS` →
> gửi một tin bất kỳ (chữ "hi" là đủ) để tạo cuộc trò chuyện.
>
> Dấu hiệu nhận biết: bấm **Gửi tin thử** báo lỗi **HTTP 404 — không tìm thấy người nhận**
> dù email đã đúng. Đó là do chưa có cuộc trò chuyện, không phải cấu hình sai.

### Bước 6. Khai báo vào hệ thống SVWS
1. Vào https://dashboard.render.com → dịch vụ **svws-app** → tab **Environment**
2. Thêm 2 biến:

   | Tên biến | Giá trị |
   |---|---|
   | `CHAT_PROVIDER` | `APP` |
   | `GCHAT_SERVICE_ACCOUNT` | Dán **nguyên văn toàn bộ nội dung** file `.json` ở Bước 3 |

3. Bấm **Save changes** — Render sẽ tự khởi động lại (~2 phút)

> **Lưu ý khi dán JSON**: dán nguyên văn, không xuống dòng thêm, không xóa bớt ký tự.
> Hệ thống có tự sửa lỗi mất xuống dòng trong `private_key`, nhưng dán đúng vẫn tốt hơn.

---

## Cách B — Gửi vào một Phòng chung (nhanh, 5 phút, KHÔNG cần quyền admin)

Dùng khi chưa làm được Cách A. Tin nhắc sẽ đăng vào một Phòng chat chung,
mọi người trong phòng đều thấy (không nhắn riêng).

1. Mở Google Chat → tạo **Space** mới tên `Nhắc việc SVWS` → mời nhân viên vào
2. Trong Space đó, bấm tên Space → **Apps & integrations → Webhooks → Add webhook**
3. Đặt tên `SVWS` → **Save** → **copy đường link webhook**
4. Vào Render → **svws-app → Environment**, thêm 2 biến:

   | Tên biến | Giá trị |
   |---|---|
   | `CHAT_PROVIDER` | `WEBHOOK` |
   | `GCHAT_WEBHOOK_URL` | đường link vừa copy |

5. **Save changes**

Sau này làm xong Cách A thì chỉ cần đổi `CHAT_PROVIDER` thành `APP` — **không phải sửa code**.

---

## Kiểm tra sau khi cấu hình

1. Đăng nhập SVWS bằng tài khoản **CEO hoặc Admin**
2. Vào **Working time & Report → tab Work Reminder**
3. Kéo xuống panel **⚙️ Kết nối Google Chat** — phải thấy chế độ đã đổi từ `DEMO`
4. Bấm **📨 Gửi tin thử cho tôi** → mở Google Chat kiểm tra
5. Bấm **📰 Xem thử bản tin đầu ngày** để xem thử nội dung bản tin tổng hợp

Nếu lỗi, hệ thống báo bằng tiếng Việt chỉ rõ nguyên nhân (chưa bật API, chưa cài
app cho người nhận, email không khớp, khóa JSON sai…).

---

## Điều kiện quan trọng

**Email nhân viên trong SVWS phải trùng email Google Workspace** thì mới nhắn riêng được.
Kiểm tra tại: **Nhân sự & Lương → Hồ sơ lương → cột Email**.

---

## Các biến cấu hình khác (tùy chọn)

| Tên biến | Mặc định | Ý nghĩa |
|---|---|---|
| `NHAC_VIEC_GUI_KHI_TAO` | `true` | Gửi tin ngay khi vừa đặt lời nhắc |
| `NHAC_VIEC_BAN_TIN` | `true` | Bật bản tin tổng hợp đầu ngày |
| `NHAC_VIEC_GIO_BAN_TIN` | `8` | Giờ gửi bản tin (0–23, **giờ Việt Nam**) |
| `TZ_OFFSET_GIO` | `7` | Múi giờ (UTC+7). Chỉ đổi nếu công ty ở múi giờ khác |

> Hệ thống đã tự quy đổi múi giờ: để `8` là bản tin đến vào **8h sáng giờ Việt Nam**,
> không cần cộng trừ gì thêm (máy chủ Render chạy giờ UTC nhưng app đã xử lý sẵn).
