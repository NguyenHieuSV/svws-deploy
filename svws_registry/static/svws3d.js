/*!
 * SVWS3D — bộ dựng hình 3D chuẩn cho tool thiết kế SVWS
 * =====================================================
 * Vì sao có thư viện này: AI viết hình học "trong bóng tối" (gõ toạ độ mà không
 * nhìn thấy kết quả) nên bố cục hay ra một đường thẳng, ống đi chéo, màu loang
 * lổ, tỷ lệ sai. Thư viện nhận phần việc đó; AI chỉ còn KHAI BÁO thiết bị và
 * đường nối — đúng phần nó làm tốt.
 *
 * Quy ước: đơn vị mm, trục Y hướng lên, mặt sàn y = 0.
 * Cần Three.js r128 (biến toàn cục THREE) nạp trước.
 *
 * Dùng tối thiểu:
 *   const S = SVWS3D.scene(document.getElementById('view3d'));
 *   const pos = SVWS3D.layout(EQUIP);           // xếp hàng, có lối đi
 *   EQUIP.forEach(e => S.addEquip(SVWS3D.build(e), pos[e.id], e));
 *   PIPES.forEach(p => S.addPipe(p, pos, EQUIP));
 *   S.fit();                                     // camera tự căn khung hình
 */
(function (global) {
  'use strict';
  if (typeof THREE === 'undefined') {
    console.error('SVWS3D: cần nạp Three.js trước.');
    return;
  }

  // ---------------------------------------------------------------- bảng màu
  // Màu theo LƯU CHẤT, không phải theo ý thích từng chỗ — để mọi tool cùng một họ.
  var PALETTE = {
    raw:      0x6b8fa8,  // nước thô / nước cấp
    filtered: 0x3aa6c9,  // sau lọc
    ro:       0x1fc8d8,  // nước RO
    di:       0x7ee8f2,  // nước DI / siêu tinh khiết
    chem:     0xe0902f,  // hoá chất
    air:      0xb0b7bd,  // khí / khí nén
    waste:    0x8a6a4f,  // nước thải / reject
    steam:    0xd94f4f,  // hơi / nước nóng
    drain:    0x5a6b7d   // xả đáy
  };
  var MAT = {
    ss:      { color: 0xcfd8dd, metalness: 0.75, roughness: 0.32 },  // inox
    frp:     { color: 0xe3d9b8, metalness: 0.05, roughness: 0.75 },  // FRP / composite
    pvc:     { color: 0xdfe6ea, metalness: 0.02, roughness: 0.55 },
    paint:   { color: 0x2f6f9e, metalness: 0.25, roughness: 0.55 },  // sơn xanh SVWS
    frame:   { color: 0x24506f, metalness: 0.55, roughness: 0.45 },  // khung thép
    panel:   { color: 0xd8dde1, metalness: 0.45, roughness: 0.45 },  // tủ điện
    concrete:{ color: 0xbfc4c7, metalness: 0.0,  roughness: 0.95 }
  };

  // --------------------------------------------- chuẩn hoá tham số AI gửi vào
  // AI viết theo lối tự nhiên của kỹ sư ("level: 60" nghĩa là 60%, "material:
  // 'SS304'"), không theo đúng kiểu nội bộ. Thư viện phải chịu được — một lần
  // hiểu sai đơn vị là dựng ra cột nước cao 156 m, kéo camera lùi tít, cả cảnh
  // teo lại (đã vấp đúng lỗi này).
  function frac(v, mac_dinh) {
    if (v == null || isNaN(v)) return mac_dinh;
    v = +v;
    if (v > 1) v = v / 100;                 // 60 → 0.6
    return Math.min(1, Math.max(0, v));
  }
  function kt(v, mac_dinh, lo, hi) {        // kích thước mm, chặn giá trị vô lý
    v = +v;
    if (!v || isNaN(v) || v <= 0) return mac_dinh;
    return Math.min(hi || 40000, Math.max(lo || 20, v));
  }
  function laInox(m) {
    return /ss|inox|stainless|30[46]|316|thep/i.test(String(m || ''));
  }
  function coMang(s) {                      // '8040' | 8040 | '8"' đều nhận
    s = String(s || '8040');
    return /4040|4"/.test(s) ? '4040' : /2540|2\.5/.test(s) ? '2540' : '8040';
  }

  function mat(kind, over) {
    var b = MAT[kind] || MAT.ss, o = {};
    for (var k in b) o[k] = b[k];
    if (over) for (var j in over) o[j] = over[j];
    return new THREE.MeshStandardMaterial(o);
  }
  function glass(color) {
    return new THREE.MeshPhysicalMaterial({
      color: color || 0xbfe3ea, transparent: true, opacity: 0.28,
      metalness: 0.0, roughness: 0.12, side: THREE.DoubleSide,
      depthWrite: false                    // tránh viền đen khi chồng lớp
    });
  }

  // ------------------------------------------------------------ tiện ích nhỏ
  function grp(name) { var g = new THREE.Group(); g.name = name || ''; return g; }
  function cyl(d, h, m, seg) {
    return new THREE.Mesh(new THREE.CylinderGeometry(d / 2, d / 2, h, seg || 28), m);
  }
  function box(w, h, dp, m) { return new THREE.Mesh(new THREE.BoxGeometry(w, h, dp), m); }
  function dome(d, m, down) {
    var g = new THREE.SphereGeometry(d / 2, 28, 14, 0, Math.PI * 2, 0, Math.PI / 2);
    var s = new THREE.Mesh(g, m);
    if (down) s.rotation.x = Math.PI;
    return s;
  }
  /** Ống nối 2 điểm bằng hình trụ (dùng cho cả nozzle lẫn đường ống). */
  function tube(a, b, dia, m) {
    var va = new THREE.Vector3().fromArray(a), vb = new THREE.Vector3().fromArray(b);
    var len = va.distanceTo(vb);
    if (len < 1e-6) return null;
    var s = new THREE.Mesh(new THREE.CylinderGeometry(dia / 2, dia / 2, len, 14), m);
    s.position.copy(va).add(vb).multiplyScalar(0.5);
    s.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0),
      vb.clone().sub(va).normalize());
    return s;
  }

  // ------------------------------------------------------------- đầu nối
  /* Mỗi đầu nối có VỊ TRÍ và HƯỚNG RA. Có hướng thì ống rời thiết bị vuông góc
     với mặt bích rồi mới lên giá — nhìn đúng kiểu đấu nối thật, thay vì cắm
     thẳng vào giữa thân bồn như trước. */
  function P(x, y, z, dx, dy, dz, dn) {
    return { p: [x, y, z], dir: [dx || 0, dy || 0, dz || 0], dn: dn || 0 };
  }
  /** Chấp nhận cả dạng cũ [x,y,z] lẫn dạng mới {p,dir}. */
  function chuanPort(v) {
    if (!v) return null;
    if (Array.isArray(v)) return { p: v.slice(), dir: [0, 1, 0], dn: 0 };
    return { p: (v.p || [0, 0, 0]).slice(), dir: (v.dir || [0, 1, 0]).slice(), dn: v.dn || 0 };
  }
  /** Vẽ cổ ống + mặt bích tại đầu nối, để nhìn là biết ống cắm vào đâu. */
  function veNozzle(g, port, dn) {
    const q = chuanPort(port); if (!q) return;
    dn = Math.max(40, q.dn || dn || 80);
    const L = dn * 1.6 + 90;
    const d = new THREE.Vector3().fromArray(q.dir);
    if (d.lengthSq() < 1e-6) d.set(0, 1, 0);
    d.normalize();
    const a = new THREE.Vector3().fromArray(q.p);
    const b = a.clone().addScaledVector(d, L);
    const m = mat('ss', { color: 0xb9c4cb });
    const co = tube(a.toArray(), b.toArray(), dn * 1.15, m);
    if (co) g.add(co);
    const bich = new THREE.Mesh(new THREE.CylinderGeometry(dn * 0.95, dn * 0.95, 26, 18), m);
    bich.position.copy(b);
    bich.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), d);
    g.add(bich);
    q.p = b.toArray();          // ống nối vào MẶT BÍCH, không phải vào vỏ
    return q;
  }
  /** Vẽ hết các đầu nối đã khai báo và dời điểm nối ra mặt bích. */
  function veCacNozzle(g, dnMacDinh) {
    const ra = {};
    Object.keys(g.userData.ports || {}).forEach(function (k) {
      ra[k] = veNozzle(g, g.userData.ports[k], dnMacDinh) || chuanPort(g.userData.ports[k]);
    });
    g.userData.ports = ra;
    return g;
  }

  /** Nhãn chữ luôn quay về phía camera (sprite), cỡ chữ theo mm thực. */
  function label(text, hmm) {
    hmm = hmm || 260;
    var pad = 12, fs = 64;
    var cv = document.createElement('canvas');
    var cx = cv.getContext('2d');
    cx.font = '600 ' + fs + 'px "IBM Plex Sans", Segoe UI, Arial, sans-serif';
    var w = Math.ceil(cx.measureText(text).width) + pad * 2;
    cv.width = w; cv.height = fs + pad * 2;
    cx = cv.getContext('2d');
    cx.font = '600 ' + fs + 'px "IBM Plex Sans", Segoe UI, Arial, sans-serif';
    cx.fillStyle = 'rgba(255,255,255,0.92)';
    cx.strokeStyle = 'rgba(11,43,74,0.85)'; cx.lineWidth = 4;
    if (cx.roundRect) { cx.beginPath(); cx.roundRect(2, 2, cv.width - 4, cv.height - 4, 10); cx.fill(); cx.stroke(); }
    else { cx.fillRect(0, 0, cv.width, cv.height); cx.strokeRect(2, 2, cv.width - 4, cv.height - 4); }
    cx.fillStyle = '#0b2b4a'; cx.textBaseline = 'middle';
    cx.fillText(text, pad, cv.height / 2);
    var tx = new THREE.CanvasTexture(cv);
    tx.minFilter = THREE.LinearFilter;
    var sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: tx, depthTest: false, transparent: true }));
    sp.scale.set(hmm * cv.width / cv.height, hmm, 1);
    sp.renderOrder = 999;
    return sp;
  }

  // ------------------------------------------------------- dựng từng thiết bị
  // Mỗi hàm trả về Group, gắn userData.foot = {w, d} (chỗ chiếm mặt bằng, mm)
  // và userData.ports = {in:[x,y,z], out:[x,y,z]} tính theo gốc của Group.

  function tank(o) {
    var d = kt(o.d, 2000, 200, 20000), h = kt(o.h, 2500, 300, 20000);
    var g = grp('tank');
    var wall = cyl(d, h, glass(), 32); wall.position.y = h / 2; g.add(wall);
    // mực nước bên trong — chuẩn đòi "thành bể trong suốt thấy nội thất"
    var lv = frac(o.level, 0.72) * h;
    var water = cyl(d - 90, lv, new THREE.MeshPhysicalMaterial({
      color: PALETTE[o.service] || PALETTE.raw, transparent: true, opacity: 0.55,
      roughness: 0.15, metalness: 0.0
    }), 32);
    water.position.y = lv / 2; g.add(water);
    // đai và chân đế thép
    [0.08, 0.5, 0.94].forEach(function (t) {
      var r = cyl(d + 40, 60, mat('frame'), 32); r.position.y = h * t; g.add(r);
    });
    var base = cyl(d + 120, 120, mat('frame'), 32); base.position.y = 60; g.add(base);
    g.userData.foot = { w: d + 160, d: d + 160 };
    g.userData.h = h;
    g.userData.ports = {
      in:   P(0, h + 40, 0, 0, 1, 0),                 // vào: đỉnh
      out:  P(0, 260, d / 2, 0, 0, 1),                // ra: thành, cách đáy 260
      tran: P(0, h - 300, -d / 2, 0, 0, -1),          // tràn: dưới đỉnh 300
      xa:   P(d * 0.3, 60, 0, 0, -1, 0)               // xả đáy
    };
    veCacNozzle(g, 80);
    return g;
  }

  function vessel(o) {   // cột lọc áp lực: thân trụ + 2 chỏm cầu + chân váy
    var d = kt(o.d, 1000, 150, 8000), h = kt(o.h, 2000, 400, 12000);
    var skirt = kt(o.skirt, 350, 0, 2000);
    var g = grp('vessel');
    var m = mat(laInox(o.material) ? 'ss' : 'frp');
    var body = h - d * 0.5;
    var bd = cyl(d, body, m); bd.position.y = skirt + body / 2; g.add(bd);
    var top = dome(d, m); top.position.y = skirt + body; g.add(top);
    var bot = dome(d, m, true); bot.position.y = skirt; g.add(bot);
    var sk = cyl(d * 0.82, skirt, mat('frame')); sk.position.y = skirt / 2; g.add(sk);
    // lớp vật liệu lọc nhìn thấy qua thân (nếu khai báo)
    if (o.media) {
      var mh = body * 0.62;
      var md = cyl(d - 60, mh, new THREE.MeshStandardMaterial(
        { color: o.mediaColor || 0x6b5537, roughness: 0.95 }));
      md.position.y = skirt + mh / 2; g.add(md);
    }
    var hh = skirt + body + d / 2;
    g.userData.foot = { w: d + 120, d: d + 120 };
    g.userData.h = hh;
    g.userData.ports = {
      in:    P(0, hh + 30, 0, 0, 1, 0),               // nước vào: đỉnh, tâm
      out:   P(0, skirt * 0.55, 0, 0, -1, 0),         // nước ra: đáy, qua đầu thu
      bw_in: P(0, skirt * 0.8, d / 2, 0, 0, 1),       // rửa ngược vào: đáy bên
      bw_out:P(0, hh - d * 0.45, -d / 2, 0, 0, -1),   // rửa ngược ra: đỉnh bên
      xa:    P(d * 0.28, skirt * 0.35, 0, 0, -1, 0)   // xả đáy
    };
    veCacNozzle(g, 80);
    return g;
  }

  function cartridge(o) {  // lọc tinh dạng ống, thường cụm nhiều lõi
    var d = kt(o.d, 300, 80, 2000), h = kt(o.h, 900, 200, 4000);
    var g = grp('cartridge');
    var m = mat('ss');
    var b = cyl(d, h, m); b.position.y = h / 2 + 250; g.add(b);
    g.add(dome(d, m).translateY(h + 250));
    var leg = box(d * 0.7, 250, d * 0.7, mat('frame')); leg.position.y = 125; g.add(leg);
    g.userData.foot = { w: d + 200, d: d + 200 };
    g.userData.h = h + 250 + d / 2;
    g.userData.ports = {
      in:  P(0, 400, d / 2, 0, 0, 1),                 // vào: đáy bên
      out: P(0, h + 250 + d / 2, 0, 0, 1, 0),         // ra: đỉnh
      xa:  P(0, 260, -d / 2, 0, 0, -1)                // xả
    };
    veCacNozzle(g, 65);
    return g;
  }

  function pump(o) {   // bơm ly tâm trên bệ: động cơ + buồng bơm
    var g = grp('pump');
    var L = kt(o.L, 900, 200, 4000), W = kt(o.W, 420, 150, 3000), H = kt(o.H, 380, 150, 3000);
    var base = box(L, 90, W, mat('frame')); base.position.y = 45; g.add(base);
    var mo = cyl(H, L * 0.5, mat('paint'), 24);
    mo.rotation.z = Math.PI / 2; mo.position.set(L * 0.18, 90 + H / 2, 0); g.add(mo);
    var cs = cyl(H * 0.95, W * 0.55, mat('ss'), 24);
    cs.rotation.z = Math.PI / 2; cs.position.set(-L * 0.28, 90 + H / 2, 0); g.add(cs);
    g.userData.foot = { w: L + 250, d: W + 250 };
    g.userData.h = 90 + H;
    g.userData.ports = {
      in:  P(-L * 0.28 - W * 0.32, 90 + H / 2, 0, -1, 0, 0),   // hút: đầu trục
      out: P(-L * 0.28, 90 + H * 0.95, 0, 0, 1, 0)             // đẩy: đỉnh buồng bơm
    };
    veCacNozzle(g, 80);
    return g;
  }

  function roSkid(o) {  // khung RO: vessel màng nằm ngang xếp tầng
    var n = Math.min(40, Math.max(1, +o.vessels || 4));
    var per = Math.min(12, Math.max(1, +o.memPerVessel || 6));
    var sz = coMang(o.size);
    var vd = (sz === '4040' ? 130 : sz === '2540' ? 85 : 220);
    var vl = per * (sz === '4040' ? 1020 : sz === '2540' ? 640 : 1020);
    var rows = Math.min(n, o.rows || Math.ceil(n / 2));
    var cols = Math.ceil(n / rows);
    var W = vl + 700, D = Math.max(900, cols * (vd + 130) + 260), H = rows * (vd + 130) + 500;
    var g = grp('roSkid');
    // khung thép
    var fm = mat('frame'), t = 90;
    [[-W / 2, -D / 2], [W / 2, -D / 2], [-W / 2, D / 2], [W / 2, D / 2]].forEach(function (p) {
      var c = box(t, H, t, fm); c.position.set(p[0], H / 2, p[1]); g.add(c);
    });
    [0, H].forEach(function (y) {
      var a = box(W, t, t, fm); a.position.set(0, y || t / 2, -D / 2); g.add(a);
      var b = box(W, t, t, fm); b.position.set(0, y || t / 2, D / 2); g.add(b);
      var c = box(t, t, D, fm); c.position.set(-W / 2, y || t / 2, 0); g.add(c);
      var e = box(t, t, D, fm); e.position.set(W / 2, y || t / 2, 0); g.add(e);
    });
    // vỏ màng
    var vm = mat('frp', { color: 0xe8e2cd });
    var k = 0;
    for (var r = 0; r < rows; r++) {
      for (var c2 = 0; c2 < cols && k < n; c2++, k++) {
        var v = cyl(vd, vl, vm, 20);
        v.rotation.z = Math.PI / 2;
        v.position.set(0, 320 + r * (vd + 130), -D / 2 + 180 + c2 * (vd + 130));
        g.add(v);
        var cap = cyl(vd * 1.12, 70, mat('ss'), 20);
        cap.rotation.z = Math.PI / 2;
        cap.position.set(vl / 2, v.position.y, v.position.z); g.add(cap);
        var cap2 = cap.clone(); cap2.position.x = -vl / 2; g.add(cap2);
      }
    }
    g.userData.foot = { w: W + 300, d: D + 300 };
    g.userData.h = H;
    var yTren = 320 + (rows - 1) * (vd + 130);
    g.userData.ports = {
      in:   P(-vl / 2 - 120, 320, -D / 2 + 180, -1, 0, 0),     // nước cấp: một đầu vỏ
      out:  P(vl / 2 + 120, yTren, -D / 2 + 180, 1, 0, 0),     // nước thấm: nắp đầu kia
      conc: P(vl / 2 + 120, 320, D / 2 - 180, 1, 0, 0),        // nước cô đặc
      cip:  P(-vl / 2 - 120, yTren, D / 2 - 180, -1, 0, 0)     // đường CIP
    };
    veCacNozzle(g, 65);
    return g;
  }

  function panel(o) {   // tủ điện / tủ điều khiển
    var W = kt(o.W, 800, 200, 6000), H = kt(o.H, 1800, 400, 4000), D = kt(o.D, 400, 150, 2000);
    var g = grp('panel');
    var b = box(W, H, D, mat('panel')); b.position.y = H / 2 + 100; g.add(b);
    var base = box(W + 60, 100, D + 60, mat('frame')); base.position.y = 50; g.add(base);
    var door = box(W * 0.86, H * 0.8, 20, mat('panel', { color: 0xeef1f3 }));
    door.position.set(0, H * 0.52 + 100, D / 2 + 5); g.add(door);
    var hmi = box(W * 0.3, H * 0.12, 24, new THREE.MeshStandardMaterial({ color: 0x123a52 }));
    hmi.position.set(0, H * 0.78 + 100, D / 2 + 12); g.add(hmi);
    g.userData.foot = { w: W + 300, d: D + 500 };
    g.userData.h = H + 100;
    g.userData.ports = {
      in:  P(-W * 0.25, 120, -D / 2, 0, 0, -1),       // cáp vào: đáy sau
      out: P(W * 0.25, 120, -D / 2, 0, 0, -1)         // cáp ra: đáy sau
    };
    veCacNozzle(g, 50);
    return g;
  }

  function dosing(o) {  // cụm châm hoá chất: bồn nhỏ + bơm định lượng
    var d = kt(o.d, 700, 200, 4000), h = kt(o.h, 1100, 300, 4000);
    var g = grp('dosing');
    var t = cyl(d, h, glass(0xf0e2c8), 24); t.position.y = h / 2 + 150; g.add(t);
    var liq = cyl(d - 60, h * 0.6, new THREE.MeshPhysicalMaterial(
      { color: PALETTE.chem, transparent: true, opacity: 0.6, roughness: 0.2 }), 24);
    liq.position.y = h * 0.3 + 150; g.add(liq);
    var pl = box(d + 500, 150, d + 300, mat('frame')); pl.position.y = 75; g.add(pl);
    var pmp = box(340, 300, 240, mat('paint')); pmp.position.set(d * 0.75, 300, 0); g.add(pmp);
    g.userData.foot = { w: d + 700, d: d + 400 };
    g.userData.h = h + 150;
    g.userData.ports = {
      in:  P(0, h + 190, 0, 0, 1, 0),                 // nạp hoá chất: đỉnh
      out: P(d * 0.75, 470, 0, 0, 1, 0)              // ra: đầu đẩy bơm định lượng
    };
    veCacNozzle(g, 32);
    return g;
  }

  function uvUnit(o) {  // đèn UV dạng ống nằm ngang
    var d = kt(o.d, 260, 80, 1500), L = kt(o.L, 1400, 300, 8000);
    var g = grp('uv');
    var b = cyl(d, L, mat('ss'), 24); b.rotation.z = Math.PI / 2;
    b.position.y = 700; g.add(b);
    [-1, 1].forEach(function (s) {
      var leg = box(120, 700, 200, mat('frame'));
      leg.position.set(s * L * 0.32, 350, 0); g.add(leg);
    });
    g.userData.foot = { w: L + 300, d: d + 400 };
    g.userData.h = 700 + d / 2;
    g.userData.ports = {
      in:  P(-L / 2 - 20, 700, 0, -1, 0, 0),
      out: P(L / 2 + 20, 700, 0, 1, 0, 0)
    };
    veCacNozzle(g, 65);
    return g;
  }

  var BUILDERS = {
    tank: tank, vessel: vessel, filter: vessel, cartridge: cartridge,
    pump: pump, roskid: roSkid, ro: roSkid, panel: panel, dosing: dosing,
    uv: uvUnit, edi: roSkid, mixedbed: vessel
  };

  /** Dựng một thiết bị từ khai báo {type, ...}. Kiểu lạ thì về bồn cho an toàn. */
  function build(e) {
    var f = BUILDERS[(e.type || 'tank').toLowerCase()] || tank;
    var g = f(e);
    g.userData.decl = e;
    return g;
  }

  // ----------------------------------------------------------------- bố trí
  /**
   * Xếp thiết bị THÀNH HÀNG có lối đi, theo thứ tự dòng công nghệ, kiểu rắn bò
   * (hàng 1 trái→phải, hàng 2 phải→trái) để đường ống giữa hai hàng ngắn nhất.
   * Đây là chỗ chữa lỗi nặng nhất: trước đây mọi thiết bị nằm trên MỘT đường
   * thẳng dài mấy chục mét nên góc nhìn nào cũng xấu.
   */
  function layout(items, opt) {
    opt = opt || {};
    var built = items.map(function (e) {
      var g = build(e);
      return { id: e.id, w: g.userData.foot.w, d: g.userData.foot.d };
    });
    var aisle = opt.aisle || 1800;                 // lối đi giữa hai hàng
    var gap = opt.gap || 700;                      // khe giữa 2 thiết bị cùng hàng
    var total = built.reduce(function (s, b) { return s + b.w + gap; }, 0);
    // chọn số hàng sao cho mặt bằng gần vuông (dễ nhìn, giống nhà máy thật)
    var rows = opt.rows || Math.max(1, Math.round(Math.sqrt(total / 2600)));
    rows = Math.min(rows, Math.max(1, Math.ceil(built.length / 2)));
    var perRow = Math.ceil(built.length / rows);

    var pos = {}, rowDepth = [], z = 0, idx = 0;
    for (var r = 0; r < rows; r++) {
      var slice = built.slice(idx, idx + perRow); idx += perRow;
      if (!slice.length) break;
      var maxD = Math.max.apply(null, slice.map(function (b) { return b.d; }));
      var wsum = slice.reduce(function (s, b) { return s + b.w + gap; }, -gap);
      var x = -wsum / 2;
      var order = (r % 2 === 1) ? slice.slice().reverse() : slice;   // rắn bò
      order.forEach(function (b) {
        pos[b.id] = { x: x + b.w / 2, y: 0, z: z + maxD / 2 };
        x += b.w + gap;
      });
      rowDepth.push(maxD);
      z += maxD + aisle;
    }
    var depth = z - aisle;
    // dời về giữa gốc toạ độ
    Object.keys(pos).forEach(function (k) { pos[k].z -= depth / 2; });
    pos.__size = { w: Math.max.apply(null, rowDepth.map(function () { return 0; }).concat([0])), d: depth };
    return pos;
  }

  // ------------------------------------------------------------- đường ống
  /**
   * Đi ống VUÔNG GÓC (Manhattan): lên cao trình → chạy X → chạy Z → xuống đích.
   * Chuẩn Rev.E bắt ống rẽ 90°; trước đây AI kéo ống chéo xuyên qua thiết bị.
   */
  function bo1(pts) {                               // bỏ điểm trùng liền kề
    return pts.filter(function (p, i, arr) {
      return i === 0 || Math.abs(p[0] - arr[i - 1][0]) > 1 ||
        Math.abs(p[1] - arr[i - 1][1]) > 1 || Math.abs(p[2] - arr[i - 1][2]) > 1;
    });
  }
  function routeOrtho(a, b, elev) {                 // giữ cho tương thích ngược
    return bo1([[a[0], a[1], a[2]], [a[0], elev, a[2]],
                [b[0], elev, a[2]], [b[0], elev, b[2]], [b[0], b[1], b[2]]]);
  }

  /* ---------------------------------------------------- GIÁ ĐỠ ỐNG (pipe rack)
     Trước đây MỌI đường ống đều nằm ở cùng một cao trình, nên ống nào cùng chạy
     theo một trục là lồng vào nhau. Nhà máy thật giải quyết bằng giá đỡ nhiều
     TẦNG, và hai hướng chạy khác nhau thì đặt ở tầng khác nhau. Làm y như vậy:

       - đoạn chạy theo X ở cao trình  base + i*BUOC
       - đoạn chạy theo Z ở cao trình  base + i*BUOC + BUOC/2   (lệch nửa tầng)
         → ống ngang và ống dọc không bao giờ cùng mặt phẳng
       - trong cùng một tầng, chỉ xếp thêm ống nếu KHÔNG đè lên ống đã có
         (song song, cùng toạ độ vuông góc, và khoảng chạy giao nhau)
  */
  var BUOC_TANG = 320;

  function _giao(a1, a2, b1, b2, ho) {              // hai khoảng có giao nhau?
    return Math.min(a2, b2) - Math.max(a1, b1) > -(ho || 0);
  }
  function xepGia(tuyen, base) {
    var tang = [];                                  // tầng i: {ngang:[], doc:[]}
    return tuyen.map(function (t) {
      var x1 = Math.min(t.ax, t.bx), x2 = Math.max(t.ax, t.bx);
      var z1 = Math.min(t.az, t.bz), z2 = Math.max(t.az, t.bz);
      for (var i = 0; ; i++) {
        if (!tang[i]) tang[i] = { ngang: [], doc: [] };
        var T = tang[i];
        var ho = t.dn + 140;                        // khoảng hở tối thiểu giữa 2 ống
        var dungNgang = T.ngang.some(function (o) {
          return Math.abs(o.z - t.az) < ho && _giao(o.x1, o.x2, x1, x2);
        });
        var dungDoc = T.doc.some(function (o) {
          return Math.abs(o.x - t.bx) < ho && _giao(o.z1, o.z2, z1, z2);
        });
        if (!dungNgang && !dungDoc) {
          T.ngang.push({ z: t.az, x1: x1, x2: x2 });
          T.doc.push({ x: t.bx, z1: z1, z2: z2 });
          return { yX: base + i * BUOC_TANG, yZ: base + i * BUOC_TANG + BUOC_TANG / 2, tang: i };
        }
      }
    });
  }

  /** Ống rời mặt bích theo đúng hướng nozzle rồi mới lên giá. */
  function routeRack(pa, pb, yX, yZ) {
    var STUB = 260;
    var a = pa.p, b = pb.p;
    var a2 = [a[0] + pa.dir[0] * STUB, a[1] + pa.dir[1] * STUB, a[2] + pa.dir[2] * STUB];
    var b2 = [b[0] + pb.dir[0] * STUB, b[1] + pb.dir[1] * STUB, b[2] + pb.dir[2] * STUB];
    return bo1([
      a, a2,
      [a2[0], yX, a2[2]],          // lên tầng ngang
      [b2[0], yX, a2[2]],          // chạy theo X
      [b2[0], yZ, a2[2]],          // đổi sang tầng dọc
      [b2[0], yZ, b2[2]],          // chạy theo Z
      [b2[0], b2[1], b2[2]], b     // hạ xuống mặt bích đích
    ]);
  }

  function pipeMesh(pts, dn, service) {
    var g = grp('pipe');
    var dia = Math.max(40, dn || 80);
    var m = mat('pvc', { color: PALETTE[service] || PALETTE.raw, roughness: 0.35, metalness: 0.2 });
    for (var i = 0; i < pts.length - 1; i++) {
      var t = tube(pts[i], pts[i + 1], dia, m);
      if (t) g.add(t);
      if (i > 0) {                                  // co 90° tại điểm gãy
        var el = new THREE.Mesh(new THREE.SphereGeometry(dia * 0.62, 14, 10), m);
        el.position.fromArray(pts[i]); g.add(el);
      }
    }
    g.userData.pts = pts;
    return g;
  }

  // ------------------------------------------------------------------ cảnh
  function scene(container, opt) {
    opt = opt || {};
    var sc = new THREE.Scene();
    sc.background = new THREE.Color(opt.bg || 0xeef3f8);

    var cam = new THREE.PerspectiveCamera(38, 1, 10, 400000);
    var rd = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    rd.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    rd.shadowMap.enabled = false;
    container.appendChild(rd.domElement);
    rd.domElement.style.display = 'block';
    rd.domElement.style.width = '100%';
    rd.domElement.style.height = '100%';

    // đèn: một hướng chính + bù sáng, đủ thấy khối mà không cháy sáng
    sc.add(new THREE.HemisphereLight(0xffffff, 0x8a97a3, 0.85));
    var dl = new THREE.DirectionalLight(0xffffff, 0.65);
    dl.position.set(1, 2, 1.2); sc.add(dl);
    var dl2 = new THREE.DirectionalLight(0xffffff, 0.25);
    dl2.position.set(-1.2, 0.8, -1); sc.add(dl2);

    var groups = {
      equip: grp('equip'), pipe: grp('pipe'), label: grp('label'),
      ground: grp('ground'), fx: grp('fx')
    };
    Object.keys(groups).forEach(function (k) { sc.add(groups[k]); });

    var canhBao = [], soTang = 0;
    var st = {
      target: new THREE.Vector3(0, 800, 0),
      radius: 20000, theta: Math.PI * 0.28, phi: Math.PI * 0.34,
      bbox: new THREE.Box3()
    };

    function place() {
      cam.position.set(
        st.target.x + st.radius * Math.sin(st.phi) * Math.cos(st.theta),
        st.target.y + st.radius * Math.cos(st.phi),
        st.target.z + st.radius * Math.sin(st.phi) * Math.sin(st.theta)
      );
      cam.lookAt(st.target);
    }

    function resize() {
      var w = container.clientWidth || 800, h = container.clientHeight || 500;
      if (w === lastW && h === lastH) return;
      lastW = w; lastH = h;
      cam.aspect = w / h; cam.updateProjectionMatrix(); rd.setSize(w, h, false);
    }
    var lastW = 0, lastH = 0;

    /** Sàn bê tông + lưới 1m, vừa khít cụm thiết bị — cho cảm giác tỷ lệ thật. */
    function ground(w, d) {
      groups.ground.clear();
      var pw = Math.max(4000, w + 4000), pd = Math.max(4000, d + 4000);
      var slab = box(pw, 120, pd, mat('concrete'));
      slab.position.y = -60; groups.ground.add(slab);
      var gh = new THREE.GridHelper(Math.max(pw, pd), Math.round(Math.max(pw, pd) / 1000),
        0x9fb0bd, 0xc7d2da);
      gh.position.y = 5; groups.ground.add(gh);
    }

    var api = {
      scene: sc, camera: cam, renderer: rd, groups: groups, state: st,

      addEquip: function (g, p, decl) {
        g.position.set(p.x, p.y || 0, p.z);
        groups.equip.add(g);
        if (decl && decl.tag !== false) {
          var txt = (decl.tag ? decl.tag + ' · ' : '') + (decl.name || decl.id || '');
          var sp = label(txt);
          sp.position.set(p.x, (g.userData.h || 2000) + 420, p.z);
          groups.label.add(sp);
        }
        return g;
      },

      /** Tìm thiết bị theo id và lấy toạ độ THẬT của một đầu nối. */
      _port: function (id, ten, pos) {
        var G = groups.equip.children.filter(function (g) {
          return g.userData.decl && g.userData.decl.id === id;
        })[0];
        if (!G) return null;
        var ports = G.userData.ports || {};
        var q = chuanPort(ports[ten] || ports[ten === 'in' ? 'out' : 'in'] ||
                          ports[Object.keys(ports)[0]]);
        if (!q) return null;
        var o = pos[id] || { x: 0, z: 0 };
        return { p: [o.x + q.p[0], q.p[1], o.z + q.p[2]], dir: q.dir, thietBi: G };
      },

      /**
       * Vẽ TẤT CẢ đường ống một lượt — phải làm cả loạt mới xếp được giá đỡ
       * (biết hết các tuyến mới chia tầng/làn cho khỏi đè nhau).
       * p: {from, to, fromPort, toPort, dn, service}
       */
      addPipes: function (pipes, pos) {
        var self = this;
        var top = 0;
        groups.equip.children.forEach(function (g) { top = Math.max(top, g.userData.h || 0); });
        var base = top + 700;                       // chạy trên đầu mọi thiết bị

        var tuyen = [], hopLe = [];
        (pipes || []).forEach(function (p) {
          var A = self._port(p.from, p.fromPort || 'out', pos);
          var B = self._port(p.to, p.toPort || 'in', pos);
          if (!A || !B) { canhBao.push('Không tìm thấy thiết bị: ' + p.from + ' → ' + p.to); return; }
          hopLe.push({ p: p, A: A, B: B });
          tuyen.push({ ax: A.p[0], az: A.p[2], bx: B.p[0], bz: B.p[2],
                       dn: Math.max(40, p.dn || 80) });
        });
        var gia = xepGia(tuyen, base);
        var ra = [];
        hopLe.forEach(function (h, i) {
          var g = pipeMesh(routeRack(h.A, h.B, gia[i].yX, gia[i].yZ), h.p.dn, h.p.service);
          g.userData.tuyen = h.p.from + '→' + h.p.to;
          g.userData.noi = [h.p.from, h.p.to];      // bỏ qua khi tự kiểm va chạm
          groups.pipe.add(g); ra.push(g);
        });
        soTang = gia.reduce(function (m, x) { return Math.max(m, x.tang + 1); }, 0);
        return ra;
      },

      /** Giữ cho tương thích ngược: gọi từng ống một (không xếp được giá). */
      addPipe: function (p, pos) { return (this.addPipes([p], pos) || [])[0]; },

      /**
       * Tự kiểm: ống có cắt qua thiết bị nào không. Bắt lỗi trước khi giao file
       * thay vì để người dùng phát hiện lúc mở tool.
       */
      kiemTra: function () {
        var loi = canhBao.slice();
        var hop = groups.equip.children.map(function (g) {
          return { id: (g.userData.decl || {}).id || '?',
                   box: new THREE.Box3().setFromObject(g) };
        });
        groups.pipe.children.forEach(function (pg) {
          // Ống LUÔN đi xuyên hộp bao của chính hai thiết bị nó nối vào (cổ ống
          // nằm trong đó) — không bỏ qua thì báo nhầm hết, che mất lỗi thật.
          var boQua = pg.userData.noi || [];
          var pts = pg.userData.pts || [];
          for (var i = 0; i < pts.length - 1; i++) {
            var a = new THREE.Vector3().fromArray(pts[i]);
            var b = new THREE.Vector3().fromArray(pts[i + 1]);
            for (var k = 1; k < 6; k++) {            // lấy vài điểm giữa đoạn
              var m2 = a.clone().lerp(b, k / 6);
              for (var j = 0; j < hop.length; j++) {
                if (boQua.indexOf(hop[j].id) >= 0) continue;
                if (hop[j].box.containsPoint(m2)) {
                  var t = 'Ống ' + (pg.userData.tuyen || '?') + ' cắt qua ' + hop[j].id;
                  if (loi.indexOf(t) < 0) loi.push(t);
                }
              }
            }
          }
        });
        return { loi: loi, soTang: soTang };
      },

      /** Camera tự căn khung: tính hộp bao rồi lùi đủ xa — hết cảnh "vệt chéo". */
      fit: function (margin) {
        var bb = new THREE.Box3();
        [groups.equip, groups.pipe].forEach(function (g) {
          if (g.children.length) bb.union(new THREE.Box3().setFromObject(g));
        });
        // nhãn nhô ra ngoài khối thiết bị — không tính vào thì mép khung bị cắt cụt
        groups.label.children.forEach(function (sp) {
          bb.expandByPoint(new THREE.Vector3(
            sp.position.x + sp.scale.x / 2, sp.position.y + sp.scale.y, sp.position.z));
          bb.expandByPoint(new THREE.Vector3(
            sp.position.x - sp.scale.x / 2, sp.position.y, sp.position.z));
        });
        if (bb.isEmpty()) return;
        st.bbox = bb;
        var size = bb.getSize(new THREE.Vector3());
        var c = bb.getCenter(new THREE.Vector3());
        st.target.set(c.x, Math.max(600, c.y * 0.85), c.z);
        // Lùi camera theo HÌNH CẦU BAO, không theo cạnh hộp: nhìn xiên thì đường
        // chéo mới là chiều rộng thật trên màn hình — tính theo cạnh sẽ cắt mép.
        var vFov = THREE.MathUtils.degToRad(cam.fov);
        var hFov = 2 * Math.atan(Math.tan(vFov / 2) * Math.max(0.4, cam.aspect));
        var sph = bb.getBoundingSphere(new THREE.Sphere());
        var dist = sph.radius / Math.sin(Math.min(vFov, hFov) / 2);
        st.radius = dist * (margin || 1.06);
        ground(size.x, size.z);
        place();
      },

      setView: function (name) {
        var v = {
          iso:   [Math.PI * 0.28, Math.PI * 0.34],
          front: [Math.PI * 0.5,  Math.PI * 0.5],
          side:  [0,              Math.PI * 0.5],
          top:   [Math.PI * 0.28, 0.06]
        }[name] || [Math.PI * 0.28, Math.PI * 0.34];
        st.theta = v[0]; st.phi = v[1]; place();
      },

      layer: function (name, on) { if (groups[name]) groups[name].visible = !!on; },
      clear: function () {
        ['equip', 'pipe', 'label', 'fx'].forEach(function (k) { groups[k].clear(); });
        canhBao = []; soTang = 0;
      },
      render: function () { rd.render(sc, cam); },
      resize: resize,
      /** Dừng vòng lặp vẽ (khi ẩn tab để đỡ tốn máy). */
      stop: function () { running = false; },
      start: function () { if (!running) { running = true; loop(); } }
    };

    // Vòng lặp vẽ liên tục: bắt buộc phải có, vì kích thước khung chỉ biết được
    // SAU khi trình duyệt dàn trang. Vẽ một lần rồi thôi thì đổi cỡ cửa sổ hay
    // chuyển tab là hình kẹt ở khung cũ (đúng lỗi đã gặp).
    var running = true;
    function loop() {
      if (!running) return;
      requestAnimationFrame(loop);
      resize();
      if (opt.onFrame) opt.onFrame();
      rd.render(sc, cam);
    }
    requestAnimationFrame(loop);

    // ------- điều khiển chuột: kéo xoay, lăn zoom, chuột phải rê ngang
    var drag = null;
    rd.domElement.addEventListener('mousedown', function (e) {
      drag = { x: e.clientX, y: e.clientY, b: e.button }; e.preventDefault();
    });
    window.addEventListener('mouseup', function () { drag = null; });
    window.addEventListener('mousemove', function (e) {
      if (!drag) return;
      var dx = e.clientX - drag.x, dy = e.clientY - drag.y;
      drag.x = e.clientX; drag.y = e.clientY;
      if (drag.b === 2) {
        var k = st.radius * 0.0012;
        var right = new THREE.Vector3().subVectors(cam.position, st.target)
          .cross(new THREE.Vector3(0, 1, 0)).normalize();
        st.target.addScaledVector(right, -dx * k);
        st.target.y += dy * k;
      } else {
        st.theta -= dx * 0.006;
        st.phi = Math.min(Math.PI * 0.495, Math.max(0.05, st.phi - dy * 0.005));
      }
      place();
    });
    rd.domElement.addEventListener('contextmenu', function (e) { e.preventDefault(); });
    rd.domElement.addEventListener('wheel', function (e) {
      st.radius = Math.min(400000, Math.max(1200, st.radius * (e.deltaY > 0 ? 1.11 : 0.9)));
      place(); e.preventDefault();
    }, { passive: false });

    window.addEventListener('resize', function () { resize(); api.render(); });
    resize(); place();
    return api;
  }

  global.SVWS3D = {
    version: '1.0',
    PALETTE: PALETTE, MAT: MAT,
    scene: scene, build: build, layout: layout, label: label,
    tank: tank, vessel: vessel, cartridge: cartridge, pump: pump,
    roSkid: roSkid, panel: panel, dosing: dosing, uv: uvUnit,
    pipeMesh: pipeMesh, routeOrtho: routeOrtho, routeRack: routeRack,
    xepGia: xepGia, P: P, mat: mat, glass: glass
  };
})(window);
