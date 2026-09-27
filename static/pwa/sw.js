/* Service worker tối giản cho app "BCVH SVWS" (/chup-anh).
   Mục đích: đủ điều kiện "Cài đặt ứng dụng" trên Android + mở được khung trang khi mất sóng.
   KHÔNG lưu đệm dữ liệu API (số liệu luôn lấy/ghi trực tiếp server). */
const CACHE = "bcvh-svws-v1";
const SHELL = ["/chup-anh", "/chup-anh/icon-192.png"];
self.addEventListener("install", e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())); });
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const u = new URL(e.request.url);
  // Chỉ xử lý mở trang /chup-anh: ưu tiên mạng (luôn bản mới), mất mạng thì dùng bản đã lưu.
  if (e.request.method === "GET" && e.request.mode === "navigate" && u.pathname === "/chup-anh") {
    e.respondWith(fetch(e.request).then(r => { const c = r.clone(); caches.open(CACHE).then(x => x.put("/chup-anh", c)); return r; })
      .catch(() => caches.match("/chup-anh")));
  }
});
