/*!
 * SVWSVT — PHÂN TÁCH THI CÔNG & VẬT TƯ lấy số từ HÌNH HỌC THẬT
 * ============================================================
 * Vì sao có thư viện này: đo được trong tool đã sinh, toàn bộ bảng vật tư là
 * hằng số gõ cứng —
 *     items.push({item:'Ống', qty: 6, unit:'m'});      // MỌI công đoạn đều 6 m
 *     items.push({item:'Co 90°', qty: 2, unit:'cái'}); // MỌI công đoạn đều 2 co
 * — nên đoạn nối dài 2 m và đoạn dài 30 m ra cùng một số. Chỉ mỗi DN là tính
 * thật (lưu lượng ÷ vận tốc). Hệ 9 công đoạn luôn ra 54 m ống dù mặt bằng bố
 * trí thế nào, và tab BOQ lấy số từ đây nên giá sai theo.
 *
 * Nguồn số liệu ĐÚNG là bản vẽ 3D, không phải diện tích mặt bằng: diện tích chỉ
 * cho biết khu đất rộng bao nhiêu, không cho biết ống chạy đường nào. Bộ dựng
 * 3D đã tự đi ống vuông góc và tự chia tầng giá đỡ, nên chiều dài thật, số co
 * 90° thật và cao trình rack đều có sẵn — thư viện này chỉ việc đọc ra.
 *
 * Dùng (sau khi đã dựng xong tab 3D):
 *   const S  = SVWS3D.scene(el);  const pos = SVWS3D.layout(EQUIP);
 *   EQUIP.forEach(e => S.addEquip(SVWS3D.build(e), pos[e.id], e));
 *   S.addPipes(PIPES, pos);
 *
 *   const V = SVWSVT.to({ong:'UPVC', heSoHao:0.07});
 *   V.nap(S.thongKeOng(), EQUIP, pos, PIPES);
 *   elCongDoan.innerHTML = V.bangCongDoan();   // từng công đoạn + vật tư của nó
 *   elTong.innerHTML     = V.bangTongHop();    // gộp toàn hệ để đặt hàng
 *   console.log(V.kiemTra());
 */
(function (global) {
  'use strict';

  var FONT = 'IBM Plex Sans,Segoe UI,Arial,sans-serif';
  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
  function so(v, md) { v = parseFloat(v); return isFinite(v) ? v : md; }
  function lam(v, n) { var k = Math.pow(10, n || 0); return Math.round(v * k) / k; }

  // Bước giá đỡ ống theo vật liệu và DN (mm) — nhựa võng nhiều nên phải dày hơn.
  function buocGia(vl, dn) {
    if (/upvc|cpvc|ppr|pvc|hdpe|pe|nhua/i.test(vl)) {
      return dn <= 32 ? 800 : dn <= 50 ? 1000 : dn <= 90 ? 1400 : dn <= 160 ? 1800 : 2200;
    }
    return dn <= 50 ? 1800 : dn <= 100 ? 2400 : dn <= 200 ? 3000 : 3600;
  }
  // Chiều dài một cây ống thương phẩm (m) — để quy ra SỐ CÂY phải mua.
  function daiCay(vl) { return /upvc|cpvc|ppr|pvc/i.test(vl) ? 4 : 6; }

  var TEN_DV = {
    raw: 'nước thô', filtered: 'nước sau lọc', ro: 'nước RO', di: 'nước DI',
    chem: 'hoá chất', air: 'khí', waste: 'nước thải', drain: 'xả', steam: 'hơi'
  };

  function to(o) {
    o = o || {};
    var vlOng = o.ong || 'UPVC';
    var hao = so(o.heSoHao, 0.07);          // hao hụt cắt nối
    var duTru = so(o.duTru, 0.05);          // dự trù thi công
    var tuyen = [], eq = [], pos = {}, khai = [];
    var api = {};

    /** Nạp dữ liệu THẬT từ bản vẽ 3D. */
    api.nap = function (thongKe, EQUIP, viTri, PIPES) {
      tuyen = (thongKe || []).slice();
      eq = (EQUIP || []).slice();
      pos = viTri || {};
      khai = (PIPES || []).slice();
      return api;
    };

    function tenTB(id) {
      for (var i = 0; i < eq.length; i++) {
        if (eq[i].id === id || eq[i].tag === id) return eq[i].tag || eq[i].name || id;
      }
      return id;
    }
    function khaiCua(t) {
      for (var i = 0; i < khai.length; i++) {
        if (khai[i].from === t.from && khai[i].to === t.to) return khai[i];
      }
      return {};
    }
    function timTB(id) {
      for (var i = 0; i < eq.length; i++) {
        if (eq[i].id === id || eq[i].tag === id) return eq[i];
      }
      return null;
    }
    function laBom(id) {
      var e = timTB(id);
      return !!e && /pump|bom|bơm/i.test(String(e.type || '') + ' ' + String(e.tag || ''));
    }
    /** Số bơm trong cụm — cụm 1 chạy 1 dừng cần bộ van riêng cho TỪNG bơm. */
    function soBomCua(id) {
      var e = timTB(id);
      if (!e) return 1;
      return Math.max(1, Math.min(6, +e.soBom || (e.dup ? 2 : 1)));
    }

    /** Đếm số nhánh cùng xuất phát từ một đầu nối → chỗ đó phải có tê/ống góp. */
    function demNhanh() {
      var d = {};
      tuyen.forEach(function (t) {
        var k = t.from + '|' + (khaiCua(t).fromPort || 'out');
        d[k] = (d[k] || 0) + 1;
      });
      return d;
    }

    // ---------------------------------------------------------------- công đoạn
    /**
     * Mỗi tuyến ống trong bản vẽ 3D là MỘT công đoạn thi công. Không gõ tay
     * danh sách công đoạn nữa: gõ tay thì thêm thiết bị vào 3D mà quên thêm
     * công đoạn là thiếu vật tư, không ai phát hiện.
     */
    function congDoan() {
      var nhanh = demNhanh();
      // Van và ống góp của cụm bơm thuộc về CHÍNH CỤM BƠM, không thuộc đoạn ống
      // nào — tính ở cả đoạn vào lẫn đoạn ra là nhân đôi. Quy ước: tính ở đoạn
      // mà cụm bơm là ĐIỂM ĐẾN; cụm nào không có đoạn nào dẫn tới thì tính ở
      // đoạn đi ra của nó.
      var laDich = {};
      tuyen.forEach(function (t) { laDich[t.to] = 1; });
      return tuyen.map(function (t, i) {
        var k = khaiCua(t);
        var daiM = t.dai / 1000;
        var vl = k.vatLieu || vlOng;
        var buoc = buocGia(vl, t.dn);
        var soNhanh = nhanh[t.from + '|' + (k.fromPort || 'out')] || 1;
        return {
          stt: i + 1,
          from: t.from, to: t.to, pts: t.pts || [],
          tenFrom: tenTB(t.from), tenTo: tenTB(t.to),
          mo: 'Lắp tuyến ' + (TEN_DV[t.service] || t.service || '') +
              ' từ ' + tenTB(t.from) + ' đến ' + tenTB(t.to),
          dn: t.dn, service: t.service, vl: vl,
          dai: t.dai, daiM: lam(daiM, 2), soCo: t.soCo,
          caoNhat: t.caoNhat,
          soGia: Math.max(2, Math.ceil(t.dai / buoc)),
          buocGia: buoc,
          soTe: soNhanh > 1 ? 1 : 0,
          // Bơm ĐƠN mới cần van một chiều riêng ở đoạn đẩy; cụm nhiều bơm đã
          // tính mỗi bơm một cái trong bộ van của cụm rồi.
          coMotChieu: laBom(t.from) && soBomCua(t.from) === 1,
          // chỉ ĐÚNG MỘT đoạn được tính vật tư của cụm bơm
          cumBom: laBom(t.to) ? soBomCua(t.to)
                : (laBom(t.from) && !laDich[t.from]) ? soBomCua(t.from) : 0,
          van: k.van == null ? 1 : so(k.van, 1)
        };
      });
    }

    /** Vật tư của MỘT công đoạn — mọi số đều suy từ hình học, không hằng số. */
    function bom(c) {
      var ds = [];
      var daiMua = c.daiM * (1 + hao);
      var cay = daiCay(c.vl);
      ds.push({ vt: 'Ống ' + c.vl, qc: 'DN' + c.dn, sl: lam(daiMua, 2), dv: 'm',
                ghi: 'Đo trên tuyến 3D ' + c.daiM + ' m + hao ' +
                     Math.round(hao * 100) + '% · ≈ ' + Math.ceil(daiMua / cay) +
                     ' cây ' + cay + ' m' });
      if (c.soCo) ds.push({ vt: 'Co 90°', qc: 'DN' + c.dn, sl: c.soCo, dv: 'cái',
                            ghi: 'Đếm theo khúc gãy thật của tuyến' });
      if (c.soTe) ds.push({ vt: 'Tê / cút chia', qc: 'DN' + c.dn, sl: c.soTe, dv: 'cái',
                            ghi: 'Đầu nối này có nhiều nhánh cùng xuất phát' });
      // Cụm bơm 1 chạy 1 dừng: MỖI BƠM cần 2 van chặn (hút và đẩy) để cô lập
      // bơm mà không dừng hệ, và 1 van một chiều ở đẩy — thiếu van một chiều
      // thì nước từ bơm đang chạy vòng ngược qua bơm dừng về góp hút, chạy
      // lòng vòng trong cụm chứ không ra hệ thống.
      var nBom = c.cumBom || 0;
      var vanCum = nBom > 1 ? nBom * 2 : 0;
      var mcCum = nBom > 1 ? nBom : (c.coMotChieu ? 1 : 0);
      if (c.van) ds.push({ vt: 'Van chặn (bi/bướm)', qc: 'DN' + c.dn, sl: c.van,
                           dv: 'cái', ghi: 'Cô lập để bảo trì' });
      if (vanCum) ds.push({ vt: 'Van chặn cụm bơm', qc: 'DN' + c.dn, sl: vanCum,
                            dv: 'cái',
                            ghi: 'Cụm ' + nBom + ' bơm song song — 2 van mỗi bơm ' +
                                 '(hút và đẩy) để cô lập từng bơm' });
      if (mcCum) ds.push({ vt: 'Van một chiều', qc: 'DN' + c.dn, sl: mcCum, dv: 'cái',
                           ghi: nBom > 1
                             ? 'Mỗi bơm một cái — chặn nước chạy vòng qua bơm dừng'
                             : 'Đầu đẩy bơm — chống chảy ngược' });
      if (nBom > 1) {
        ds.push({ vt: 'Ống góp hút + góp đẩy', qc: 'DN' + Math.round(c.dn * 1.25),
                  sl: 2, dv: 'tuyến',
                  ghi: 'Hai góp chung gom về một đầu nối (dạng chữ U)' });
        ds.push({ vt: 'Tê góp bơm', qc: 'DN' + c.dn, sl: nBom * 2, dv: 'cái',
                  ghi: 'Điểm rẽ nhánh vào và ra từng bơm' });
      }
      // Mặt bích: 2 đầu nối thiết bị + 2 cho mỗi van (tháo được để bảo trì)
      var soBich = 2 + 2 * (c.van + vanCum + mcCum);
      ds.push({ vt: 'Mặt bích + gioăng + bộ bu lông', qc: 'DN' + c.dn, sl: soBich,
                dv: 'bộ', ghi: '2 đầu thiết bị + 2 mỗi van' });
      ds.push({ vt: 'Rắc co / khớp nối tháo được', qc: 'DN' + c.dn, sl: 2, dv: 'bộ',
                ghi: 'Đầu vào và đầu ra công đoạn' });
      ds.push({ vt: 'Giá đỡ / kẹp ống', qc: 'DN' + c.dn, sl: c.soGia, dv: 'cái',
                ghi: 'Bước ' + c.buocGia + ' mm theo vật liệu ' + c.vl +
                     ' — tính từ chiều dài thật' });
      if (/upvc|cpvc|pvc/i.test(c.vl))
        ds.push({ vt: 'Keo dán ống + giẻ lau', qc: '-', sl: lam(c.daiM / 30, 2),
                  dv: 'hộp', ghi: '≈1 hộp cho 30 m ống' });
      else
        ds.push({ vt: 'Que hàn / băng tan ren', qc: '-', sl: lam(c.daiM / 25, 2),
                  dv: 'bộ', ghi: '≈1 bộ cho 25 m ống' });
      if (c.service === 'chem') {
        ds.push({ vt: 'Đầu phun hoá chất (injection quill)', qc: 'DN' + c.dn, sl: 1,
                  dv: 'cái', ghi: 'Điểm châm vào đường ống chính' });
      }
      return ds;
    }

    // ============================================ BẢN VẼ SƠ ĐỒ ĐOẠN THI CÔNG
    /* Vẽ ĐÚNG tuyến ống thật, không phải hai ô vuông và một đường thẳng. Hai
       hình: MẶT BẰNG (nhìn từ trên, thấy ống đi vòng thế nào) và TRẮC DỌC
       TUYẾN (trải phẳng theo chiều đi, thấy ống lên giá cao bao nhiêu rồi hạ
       xuống đâu). Trắc dọc dùng tỷ lệ đứng khác tỷ lệ ngang — chuẩn của bản vẽ
       tuyến ống, vì tuyến dài 15 m mà chỉ cao 4 m thì cùng tỷ lệ sẽ bẹt dí. */
    var NAVY = '#0b2545', INK = '#12263a', MO = '#33475b', XAM = '#8b98a8';
    var DO = '#b3271e', LUC = '#1f7a4d', NUOC = '#2f7fb8';

    function hinhTB(id) {
      for (var i = 0; i < eq.length; i++) {
        var e = eq[i];
        if (e.id === id || e.tag === id) {
          var cd = (global.SVWS3D && SVWS3D.chanDe) ? SVWS3D.chanDe(e) : null;
          var p = pos[id] || pos[e.id] || { x: 0, z: 0 };
          return { x: so(p.x, 0), z: so(p.z, 0),
                   w: so(cd && cd.w, 800), d: so(cd && cd.d, 800),
                   h: so(e.h, 1500), tag: e.tag || id, tron: !!(cd && cd.tron) };
        }
      }
      return null;
    }
    function tyLeDep(v) {                       // quy về nấc tỷ lệ quen thuộc
      var nac = [10, 20, 25, 50, 75, 100, 150, 200, 250, 500];
      for (var i = 0; i < nac.length; i++) if (nac[i] >= v) return nac[i];
      return nac[nac.length - 1];
    }

    function veCongDoan(c) {
      var pts = c.pts || [];
      if (pts.length < 2) return '<div class="svws-ghi">Chưa có toạ độ tuyến ống.</div>';
      var W = 1180, H = 590, o2 = [];
      function P(s) { o2.push(s); }
      function ln(x1, y1, x2, y2, m, w, net) {
        P('<line x1="' + lam(x1, 1) + '" y1="' + lam(y1, 1) + '" x2="' + lam(x2, 1) +
          '" y2="' + lam(y2, 1) + '" stroke="' + (m || NAVY) + '" stroke-width="' +
          (w || 1.3) + '"' + (net ? ' stroke-dasharray="' + net + '"' : '') + '/>');
      }
      function tx(x, y, s, fs, m, neo, dam) {
        P('<text x="' + lam(x, 1) + '" y="' + lam(y, 1) + '" font-size="' + (fs || 9) +
          '" fill="' + (m || INK) + '" text-anchor="' + (neo || 'middle') + '"' +
          (dam ? ' font-weight="600"' : '') + ' font-family="' + FONT + '">' +
          esc(s) + '</text>');
      }
      var A = hinhTB(c.from), B = hinhTB(c.to);

      // ------------------------------------------------------------ MẶT BẰNG
      var vx1 = 46, vy1 = 64, vw = 500, vh = 250;
      var xs = pts.map(function (p) { return p[0]; });
      var zs = pts.map(function (p) { return p[2]; });
      [A, B].forEach(function (t) {
        if (!t) return;
        xs.push(t.x - t.w / 2, t.x + t.w / 2);
        zs.push(t.z - t.d / 2, t.z + t.d / 2);
      });
      var x0 = Math.min.apply(null, xs), x1 = Math.max.apply(null, xs);
      var z0 = Math.min.apply(null, zs), z1 = Math.max.apply(null, zs);
      var tlMB = tyLeDep(Math.max((x1 - x0) / vw, (z1 - z0) / vh) * 1.12 || 10);
      var sMB = 1 / tlMB;
      var ox = vx1 + (vw - (x1 - x0) * sMB) / 2 - x0 * sMB;
      var oz = vy1 + (vh - (z1 - z0) * sMB) / 2 - z0 * sMB;
      function mbx(x) { return ox + x * sMB; }
      function mbz(z) { return oz + z * sMB; }

      P('<rect x="' + vx1 + '" y="' + vy1 + '" width="' + vw + '" height="' + vh +
        '" fill="#f7fafc" stroke="#dde5ee"/>');
      [A, B].forEach(function (t, i) {
        if (!t) return;
        P('<rect x="' + lam(mbx(t.x - t.w / 2), 1) + '" y="' + lam(mbz(t.z - t.d / 2), 1) +
          '" width="' + lam(t.w * sMB, 1) + '" height="' + lam(t.d * sMB, 1) +
          '" rx="' + (t.tron ? Math.min(t.w, t.d) * sMB / 2 : 3) +
          '" fill="#e3ecf5" stroke="' + NAVY + '" stroke-width="1.4"/>');
        tx(mbx(t.x), mbz(t.z) + 3.5, t.tag, 9, NAVY, 'middle', 1);
      });
      // tuyến ống nhìn từ trên
      var dMB = pts.map(function (p) { return lam(mbx(p[0]), 1) + ',' + lam(mbz(p[2]), 1); });
      P('<polyline points="' + dMB.join(' ') + '" fill="none" stroke="' + NUOC +
        '" stroke-width="3" stroke-linejoin="round"/>');
      // đánh dấu co 90° nhìn trên mặt bằng
      for (var i = 1; i < pts.length - 1; i++) {
        var a1 = Math.abs(pts[i][0] - pts[i - 1][0]) > 1 ? 'x'
               : Math.abs(pts[i][2] - pts[i - 1][2]) > 1 ? 'z' : 'y';
        var a2 = Math.abs(pts[i + 1][0] - pts[i][0]) > 1 ? 'x'
               : Math.abs(pts[i + 1][2] - pts[i][2]) > 1 ? 'z' : 'y';
        if (a1 !== a2 && a1 !== 'y' && a2 !== 'y') {
          P('<circle cx="' + lam(mbx(pts[i][0]), 1) + '" cy="' + lam(mbz(pts[i][2]), 1) +
            '" r="3.6" fill="#fff" stroke="' + DO + '" stroke-width="1.5"/>');
        }
      }
      tx(vx1 + vw / 2, vy1 + vh + 20, 'MẶT BẰNG TUYẾN — tỷ lệ 1:' + tlMB, 10.5,
         NAVY, 'middle', 1);
      // mũi tên Bắc
      ln(vx1 + vw - 26, vy1 + 40, vx1 + vw - 26, vy1 + 14, MO, 1.4);
      P('<path d="M' + (vx1 + vw - 26) + ' ' + (vy1 + 10) + ' l-4.5 9 l9 0 Z" fill="' +
        MO + '"/>');
      tx(vx1 + vw - 26, vy1 + 52, 'B', 9, MO, 'middle', 1);

      // ------------------------------------------------------- TRẮC DỌC TUYẾN
      // Trải phẳng: trục ngang = quãng đường NGANG đã đi, trục đứng = cao độ.
      var moc = [{ s: 0, y: pts[0][1] }], S = 0;
      for (var k = 1; k < pts.length; k++) {
        var dx = pts[k][0] - pts[k - 1][0], dz = pts[k][2] - pts[k - 1][2];
        S += Math.sqrt(dx * dx + dz * dz);
        moc.push({ s: S, y: pts[k][1] });
      }
      var yMax = Math.max.apply(null, moc.map(function (m) { return m.y; }));
      var tMax = Math.max(yMax, (A ? A.h : 0), (B ? B.h : 0)) * 1.12 + 200;
      var px1 = 620, py1 = 64, pw = 508, ph = 250;
      // Chừa lề hai bên để hình thiết bị ở đầu và cuối tuyến không tràn ra
      // ngoài khung — tuyến bắt đầu tại s=0 nên vẽ sát mép là mất nửa thiết bị.
      var le = 46, pwT = pw - le * 2;
      var tlN = tyLeDep((S || 1) / pwT);                // tỷ lệ NGANG
      var tlD = tyLeDep(tMax / ph);                     // tỷ lệ ĐỨNG
      function tdx(s) { return px1 + le + s / tlN; }
      function tdy(y) { return py1 + ph - y / tlD; }

      P('<rect x="' + px1 + '" y="' + py1 + '" width="' + pw + '" height="' + ph +
        '" fill="#f7fafc" stroke="#dde5ee"/>');
      ln(px1, tdy(0), px1 + pw, tdy(0), '#7a5c3a', 2.2);          // mặt nền
      tx(px1 + 4, tdy(0) + 14, 'CAO ĐỘ ±0.000 (mặt nền)', 8, '#7a5c3a', 'start');
      // thiết bị hai đầu
      [[A, 0], [B, S]].forEach(function (t) {
        if (!t[0]) return;
        var e = t[0], wpx = Math.min(le * 1.6, Math.max(18, e.w / tlN));
        var ex = Math.min(px1 + pw - wpx - 3, Math.max(px1 + 3, tdx(t[1]) - wpx / 2));
        P('<rect x="' + lam(ex, 1) + '" y="' + lam(tdy(e.h), 1) +
          '" width="' + lam(wpx, 1) + '" height="' + lam(e.h / tlD, 1) +
          '" fill="#e3ecf5" stroke="' + NAVY + '" stroke-width="1.4"/>');
        tx(ex + wpx / 2, Math.max(py1 + 11, tdy(e.h) - 7), e.tag, 9, NAVY, 'middle', 1);
      });
      // cao trình giá đỡ
      var caoRack = Math.max.apply(null, moc.map(function (m) { return m.y; }));
      ln(px1, tdy(caoRack), px1 + pw, tdy(caoRack), LUC, 1, '7 4');
      // Nhãn cao trình đặt ở khoảng 1/3 tuyến, KHÔNG đặt sát mép phải: hai đầu
      // tuyến là chỗ đứng của thiết bị, nhãn ở đó sẽ đè lên tag thiết bị.
      tx(px1 + le + pwT * 0.34, tdy(caoRack) - 17,
         'CAO TRÌNH GIÁ ĐỠ +' + Math.round(caoRack) + ' mm', 8.4, LUC, 'middle', 1);
      // tuyến ống trải phẳng
      P('<polyline points="' + moc.map(function (m) {
          return lam(tdx(m.s), 1) + ',' + lam(tdy(m.y), 1);
        }).join(' ') + '" fill="none" stroke="' + NUOC +
        '" stroke-width="3.4" stroke-linejoin="round"/>');
      // co 90° + giá đỡ + chiều dài từng đoạn
      for (var j = 0; j < moc.length - 1; j++) {
        var m1 = moc[j], m2 = moc[j + 1];
        var ngang = Math.abs(m2.s - m1.s) > 1, dung = Math.abs(m2.y - m1.y) > 1;
        if (j > 0) P('<circle cx="' + lam(tdx(m1.s), 1) + '" cy="' + lam(tdy(m1.y), 1) +
          '" r="4" fill="#fff" stroke="' + DO + '" stroke-width="1.6"/>');
        if (ngang) {
          var dai = m2.s - m1.s;
          tx((tdx(m1.s) + tdx(m2.s)) / 2, tdy(m1.y) - 9, lam(dai / 1000, 2) + ' m',
             8.2, MO, 'middle');
          // giá đỡ đặt theo bước chuẩn — vẽ đúng chỗ sẽ đóng kẹp
          var n = Math.max(1, Math.floor(dai / c.buocGia));
          for (var g = 1; g <= n; g++) {
            var sx = tdx(m1.s + dai * g / (n + 1));
            ln(sx, tdy(m1.y) + 2, sx, tdy(m1.y) + 11, XAM, 1.2);
            P('<path d="M' + lam(sx - 4, 1) + ' ' + lam(tdy(m1.y) + 11, 1) + ' l8 0 l-4 -5 Z" fill="' +
              XAM + '"/>');
          }
        } else if (dung) {
          tx(tdx(m1.s) + 6, (tdy(m1.y) + tdy(m2.y)) / 2,
             lam(Math.abs(m2.y - m1.y) / 1000, 2) + ' m', 8.2, MO, 'start');
        }
      }
      P('<circle cx="' + lam(tdx(moc[moc.length - 1].s), 1) + '" cy="' +
        lam(tdy(moc[moc.length - 1].y), 1) + '" r="3" fill="' + NUOC + '"/>');
      tx(px1 + pw / 2, py1 + ph + 20,
         'TRẮC DỌC TUYẾN (trải phẳng) — ngang 1:' + tlN + ' · đứng 1:' + tlD,
         10.5, NAVY, 'middle', 1);

      // ------------------------------------------------------------ chú giải
      var cy = 372;
      P('<rect x="46" y="' + cy + '" width="1082" height="176" fill="#fff" stroke="#dde5ee"/>');
      tx(60, cy + 22, 'CÔNG ĐOẠN ' + c.stt + ': ' + c.tenFrom + ' → ' + c.tenTo,
         12.5, NAVY, 'start', 1);
      var dong = [
        'Đường ống: ' + c.vl + ' DN' + c.dn + ' · ' + (TEN_DV[c.service] || c.service) +
          ' · tổng dài ' + c.daiM + ' m đo trên tuyến 3D',
        'Co 90°: ' + c.soCo + ' cái (đếm theo khúc gãy thật) · Giá đỡ: ' + c.soGia +
          ' cái, bước ' + c.buocGia + ' mm' + (c.soTe ? ' · Tê: ' + c.soTe + ' cái' : ''),
        'Cao trình giá đỡ: +' + Math.round(caoRack) + ' mm so với mặt nền' +
          (c.van ? ' · Van chặn: ' + c.van + ' cái' : '') +
          (c.coMotChieu ? ' · Van một chiều ở đầu đẩy bơm' : ''),
        'Trình tự lắp: định vị hai thiết bị → dựng cột và giá đỡ theo cao trình → ' +
          'lắp ống nhánh đứng tại hai đầu → nối tuyến ngang trên giá → lắp van và ' +
          'rắc co → thử kín trước khi bọc bảo ôn.'
      ];
      dong.forEach(function (t, i2) {
        tx(60, cy + 46 + i2 * 19, '• ' + t, 9.2, INK, 'start');
      });
      // ký hiệu
      P('<circle cx="812" cy="' + (cy + 128) + '" r="4" fill="#fff" stroke="' + DO +
        '" stroke-width="1.6"/>');
      tx(824, cy + 131, 'co 90°', 8.6, MO, 'start');
      P('<path d="M880 ' + (cy + 131) + ' l8 0 l-4 -5 Z" fill="' + XAM + '"/>');
      tx(894, cy + 131, 'giá đỡ ống', 8.6, MO, 'start');
      ln(962, cy + 128, 986, cy + 128, LUC, 1, '7 4');
      tx(992, cy + 131, 'cao trình giá', 8.6, MO, 'start');
      tx(W / 2, H - 12, 'BẢN THAM KHẢO — CHƯA DUYỆT THI CÔNG', 11,
         'rgba(179,39,30,0.28)', 'middle', 1);

      return '<svg viewBox="0 0 ' + W + ' ' + H + '" width="100%" ' +
        'xmlns="http://www.w3.org/2000/svg" style="background:#fdfefe">' +
        '<rect width="' + W + '" height="' + H + '" fill="#fdfefe" stroke="' + NAVY +
        '" stroke-width="1.4"/>' + o2.join('') + '</svg>';
    }

    // ====================== CÔNG ĐOẠN LẮP BỂ & CHẠY THỬ NGHIỆM THU ==========
    /* Hồ sơ thi công thật không chỉ có ống: còn công đoạn LẮP BỂ (cẩu đặt, neo
       bu lông, grout, lắp đo mức, ống tràn, xả đáy, thang thao tác) và công
       đoạn CHẠY THỬ NGHIỆM THU (lập trình PLC, SCADA, hiệu chuẩn dụng cụ, chạy
       thử, hồ sơ). Thiếu hai công đoạn này là thiếu tiền và thiếu việc. */
    function laBe(e) {
      return /tank|be|bon/i.test(String(e.type || ''));
    }
    function lapBe() {
      var ds = [], be = eq.filter(laBe);
      if (!be.length) return ds;
      var soThang = 0;
      be.forEach(function (e) {
        var d = so(e.d, 0), h = so(e.h, 0);
        var v = (d && h) ? m3(d, h) : 0;
        ds.push({ vt: (e.tag || e.id) + ' ' + (e.name || 'Bể chứa'),
                  qc: 'Ø' + d + ' × H' + h + ' mm' + (v ? ' · ' + v + ' m³' : '') +
                      ' · ' + (e.vatLieu || e.material || 'SS304'),
                  sl: 1, dv: 'bể', ghi: 'Thiết bị trong bản vẽ 3D' });
        if (d >= 1500) soThang++;
      });
      ds.push({ vt: 'Đo mức liên tục (LIT)', qc: 'siêu âm 4–20 mA', sl: be.length,
                dv: 'bộ', ghi: '1 bộ mỗi bể' });
      ds.push({ vt: 'Phao báo mức LSL / LSH', qc: '', sl: be.length * 2, dv: 'bộ',
                ghi: '2 phao mỗi bể (thấp và cao)' });
      ds.push({ vt: 'Ống tràn + xả đáy', qc: 'uPVC DN80', sl: be.length * 6, dv: 'm',
                ghi: '≈6 m mỗi bể: tràn xuống mương + xả đáy' });
      ds.push({ vt: 'Van xả đáy', qc: 'bi uPVC DN40', sl: be.length, dv: 'cái',
                ghi: '1 van mỗi bể' });
      if (soThang) ds.push({ vt: 'Thang + sàn thao tác', qc: 'SS304', sl: soThang,
                             dv: 'bộ', ghi: 'Bể Ø ≥ 1500 mm phải có chỗ đứng thao tác' });
      ds.push({ vt: 'Bu lông neo + grout chân bể', qc: 'M16 + vữa không co ngót',
                sl: be.length * 4, dv: 'bộ', ghi: '4 bu lông mỗi bể' });
      return ds;
    }

    var dsIO = [];
    /** Nạp bảng I/O của tủ điện — để đưa DỤNG CỤ ĐO vào BOQ và tính hiệu chuẩn. */
    api.napIO = function (ds) { dsIO = (ds || []).slice(); return api; };

    function dungCuDo() {
      var ds = [], nhom = {};
      dsIO.forEach(function (k) {
        var kieu = String(k.kieu || '').toUpperCase();
        if (kieu !== 'DI' && kieu !== 'AI') return;      // DO/AO là lệnh, không phải dụng cụ
        var loai = kieu === 'AI' ? 'Dụng cụ đo analog (4–20 mA)'
                                 : 'Công tắc / phao báo (tiếp điểm)';
        (nhom[loai] = nhom[loai] || []).push(k.tag || k.dc);
      });
      Object.keys(nhom).forEach(function (t) {
        ds.push({ vt: t, qc: nhom[t].join(', '), sl: nhom[t].length, dv: 'bộ',
                  ghi: 'Đếm từ bảng I/O của tủ điện — mỗi kênh một thiết bị thật' });
      });
      return ds;
    }

    function chayThu() {
      var soKenh = dsIO.length;
      var soDo = dsIO.filter(function (k) {
        var t = String(k.kieu || '').toUpperCase();
        return t === 'DI' || t === 'AI';
      }).length;
      var ds = [
        { vt: 'Lập trình PLC theo bảng logic vận hành', qc: 'gồm khoá liên động và báo động',
          sl: 1, dv: 'gói', ghi: soKenh ? soKenh + ' kênh I/O theo bảng I/O' : '' },
        { vt: 'Cấu hình HMI / SCADA', qc: 'màn hình vận hành, xu hướng, cảnh báo',
          sl: 1, dv: 'gói', ghi: '' },
        { vt: 'Hiệu chuẩn dụng cụ đo', qc: 'có giấy hiệu chuẩn', sl: soDo || 1,
          dv: 'bộ', ghi: 'Mỗi dụng cụ đo một lần hiệu chuẩn trước nghiệm thu' },
        { vt: 'Thử kín và thử áp đường ống', qc: '1,5 × áp làm việc, giữ 30 phút',
          sl: tuyen.length || 1, dv: 'tuyến', ghi: 'Mỗi tuyến ống một lần thử' },
        { vt: 'Súc rửa, khử trùng và xả nước đầu', qc: '', sl: 1, dv: 'gói', ghi: '' },
        { vt: 'Chạy thử không tải và có tải', qc: '72 giờ liên tục', sl: 1, dv: 'gói',
          ghi: '' },
        { vt: 'Hồ sơ nghiệm thu', qc: 'CO/CQ, bản vẽ hoàn công, tài liệu vận hành, ' +
              'biên bản chạy thử, bảo hành', sl: 1, dv: 'bộ', ghi: '' },
        { vt: 'Đào tạo vận hành', qc: 'cho nhân sự nhà máy', sl: 1, dv: 'gói', ghi: '' }
      ];
      return ds;
    }

    // ------------------------------------------------- móng & điện theo vị trí
    /** Móng tính từ CHÂN ĐẾ THẬT của thiết bị, không phải con số ước chừng. */
    function mong() {
      var ds = [], tongDT = 0, chuVi = 0, soTB = 0;
      eq.forEach(function (e) {
        var cd = (global.SVWS3D && SVWS3D.chanDe) ? SVWS3D.chanDe(e) : null;
        if (!cd) return;
        var w = so(cd.w, 0), d = so(cd.d, 0);
        if (!w || !d) return;
        soTB++;
        tongDT += (w + 200) * (d + 200) / 1e6;          // + 100 mm mỗi bên bệ
        chuVi += 2 * ((w + 200) + (d + 200)) / 1000;
      });
      if (!soTB) return ds;
      ds.push({ vt: 'Bê tông bệ móng M250', qc: 'dày 200 mm',
                sl: lam(tongDT * 0.2, 2), dv: 'm³',
                ghi: 'Tổng diện tích bệ ' + lam(tongDT, 2) + ' m² của ' + soTB +
                     ' thiết bị, lấy theo chân đế thật' });
      ds.push({ vt: 'Thép cốt bệ móng', qc: 'D10 a200 hai lớp',
                sl: lam(tongDT * 0.2 * 90, 0), dv: 'kg',
                ghi: '≈90 kg thép cho 1 m³ bê tông bệ' });
      ds.push({ vt: 'Bu lông neo', qc: 'M16 chôn sẵn', sl: soTB * 4, dv: 'cái',
                ghi: '4 bu lông cho mỗi thiết bị' });
      ds.push({ vt: 'Vữa grout không co ngót', qc: 'dày 30 mm',
                sl: lam(chuVi * 0.03 * 0.1 * 2200, 0), dv: 'kg',
                ghi: 'Chèn chân đế theo tổng chu vi bệ ' + lam(chuVi, 1) + ' m' });
      ds.push({ vt: 'Sơn nền epoxy', qc: '2 lớp', sl: lam(tongDT * 1.6, 1), dv: 'm²',
                ghi: 'Diện tích bệ + lối đi quanh bệ' });
      return ds;
    }

    /**
     * Cáp điện đo theo KHOẢNG CÁCH MANHATTAN từ tủ tới từng động cơ (cáp đi
     * theo máng, không đi chéo), cộng đoạn lên xuống máng và 15% chùng.
     */
    function dien() {
      var tu = null;
      eq.forEach(function (e) {
        if (/panel|tu|mcc|plc/i.test(String(e.type || '') + ' ' + String(e.tag || '')))
          tu = e;
      });
      // Bơm định lượng và đèn UV cũng là tải điện — bỏ sót là thiếu cáp.
      var dsDC = eq.filter(function (e) {
        return /pump|bom|bơm|blower|thoi khi|mixer|khuay|motor|dosing|uv/i.test(
          String(e.type || '') + ' ' + String(e.tag || '') + ' ' + String(e.name || ''));
      });
      if (!dsDC.length) return [];
      var pTu = tu ? (pos[tu.id] || { x: 0, z: 0 }) : { x: 0, z: 0 };
      var tongCap = 0, xa = 0;
      dsDC.forEach(function (e) {
        var p = pos[e.id] || { x: 0, z: 0 };
        var d = (Math.abs(p.x - pTu.x) + Math.abs(p.z - pTu.z)) / 1000;   // m
        var len = (d + 3.5) * 1.15;      // + lên máng và xuống động cơ, + 15% chùng
        tongCap += len;
        xa = Math.max(xa, d);
      });
      var mang = xa * 1.3;               // máng chính chạy dọc tuyến xa nhất
      return [
        { vt: 'Cáp động lực', qc: 'theo bảng motor list', sl: lam(tongCap, 1), dv: 'm',
          ghi: 'Đo Manhattan từ tủ tới ' + dsDC.length + ' động cơ + 3,5 m lên/xuống + 15% chùng' },
        { vt: 'Cáp điều khiển/tín hiệu', qc: '2×1,5 mm² có lưới',
          sl: lam(tongCap * 0.8, 1), dv: 'm', ghi: 'Theo cùng tuyến máng' },
        { vt: 'Máng cáp', qc: '200×100 mm', sl: lam(mang, 1), dv: 'm',
          ghi: 'Tuyến xa nhất ' + lam(xa, 1) + ' m × 1,3 cho rẽ nhánh' },
        { vt: 'Cáp gland', qc: 'M20/M25', sl: dsDC.length * 2, dv: 'bộ',
          ghi: '2 đầu cho mỗi động cơ' },
        { vt: 'Dây tiếp địa', qc: 'Cu 16 mm²', sl: lam(tongCap * 0.35, 1), dv: 'm',
          ghi: 'Nối đất vỏ thiết bị và máng cáp' }
      ];
    }

    // ======================================= DANH MỤC THIẾT BỊ CHÍNH (cho BOQ)
    /* Bảng vật tư ở trên chỉ suy từ ĐƯỜNG ỐNG nên có ống, phụ kiện, móng, cáp —
       KHÔNG có thiết bị chính. BOQ mà thiếu bồn, bơm, cột lọc, giàn RO thì
       thiếu đúng phần lớn tiền. Ở đây sinh danh mục thiết bị từ CHÍNH khai báo
       EQUIP đã dùng dựng 3D, nên không thể lệch với bản vẽ. */
    function m3(d, h) { return lam(Math.PI / 4 * d * d * h / 1e9, 1); }

    function quyCach(e) {
      var t = String(e.type || '').toLowerCase();
      var d = so(e.d, 0), h = so(e.h, 0);
      var vl = e.vatLieu || e.material || '';
      var ds = [];
      if (t === 'tank') {
        ds.push('Ø' + d + ' × H' + h + ' mm');
        if (d && h) ds.push('dung tích ' + m3(d, h) + ' m³');
        if (vl) ds.push(vl);
        if (e.dayThan) ds.push('dày thân ' + e.dayThan + ' mm');
      } else if (t === 'vessel' || t === 'filter' || t === 'mixedbed') {
        ds.push('Ø' + d + ' × H' + h + ' mm');
        if (e.media) ds.push('vật liệu lọc: ' + e.media);
        if (vl) ds.push('vỏ ' + vl);
        if (e.ap) ds.push('áp làm việc ' + e.ap + ' bar');
      } else if (t === 'cartridge') {
        ds.push('Ø' + d + ' × H' + h + ' mm');
        if (e.micron || e.um) ds.push('lõi ' + (e.micron || e.um) + ' µm');
        if (e.soLoi) ds.push(e.soLoi + ' lõi');
      } else if (t === 'pump') {
        if (e.kW) ds.push(e.kW + ' kW');
        if (e.Q) ds.push('Q ' + e.Q + ' m³/h');
        if (e.cot) ds.push('cột áp ' + e.cot + ' m');
        ds.push(soBomCua(e.id || e.tag) > 1 ? '1 chạy 1 dự phòng' : 'một bơm');
      } else if (t === 'roskid' || t === 'ro') {
        var nv = Math.max(1, +e.vessels || 4), per = Math.max(1, +e.memPerVessel || 6);
        ds.push(nv + ' vỏ màng × ' + per + ' màng ' + (e.size || '8040'));
        ds.push('tổng ' + (nv * per) + ' màng');
        if (e.bom) ds.push('kèm ' + (e.bom === true ? 1 : e.bom) + ' bơm cao áp');
        if (e.loc || e.cartridge) ds.push('kèm vỏ lọc tinh');
        if (e.tu || e.panel) ds.push('kèm tủ điều khiển');
      } else if (t === 'edi') {
        var moiS = so(e.moiStack, 5);
        var ns = Math.max(1, +e.stacks ||
          ((+e.q || +e.congSuat) ? Math.ceil((+e.q || +e.congSuat) / moiS) : 1));
        ds.push(ns + ' stack × ' + moiS + ' m³/h');
        ds.push('module tấm–khung');
      } else if (t === 'uv') {
        if (e.lieu) ds.push('liều ' + e.lieu + ' mJ/cm²');
        if (e.kW) ds.push(e.kW + ' kW');
        if (e.d && e.L) ds.push('Ø' + e.d + ' × L' + e.L + ' mm');
      } else if (t === 'panel') {
        ds.push((so(e.W, 800)) + ' × ' + (so(e.H, 1800)) + ' × ' + (so(e.D, 400)) + ' mm');
        ds.push('vỏ sơn tĩnh điện, IP54');
      } else if (t === 'dosing') {
        ds.push('bồn Ø' + d + ' × H' + h + ' mm');
        if (d && h) ds.push(m3(d, h) + ' m³');
        ds.push('kèm bơm định lượng');
      } else {
        if (d) ds.push('Ø' + d + (h ? ' × H' + h : '') + ' mm');
        if (vl) ds.push(vl);
      }
      return ds.join(' · ');
    }

    /** Số lượng đặt hàng của một thiết bị (cụm bơm đôi = 2 cái). */
    function soLuong(e) {
      var t = String(e.type || '').toLowerCase();
      if (t === 'pump') return soBomCua(e.id || e.tag);
      if (t === 'vessel' || t === 'filter') return Math.max(1, +e.qty || 1);
      return 1;
    }

    var NHOM_TB = {
      tank: 'Bồn bể', vessel: 'Thiết bị lọc', filter: 'Thiết bị lọc',
      mixedbed: 'Thiết bị lọc', cartridge: 'Thiết bị lọc', pump: 'Bơm',
      roskid: 'Cụm màng', ro: 'Cụm màng', edi: 'Cụm màng', uv: 'Khử trùng',
      panel: 'Điện & điều khiển', dosing: 'Hoá chất'
    };

    function thietBiChinh() {
      return eq.map(function (e) {
        var t = String(e.type || '').toLowerCase();
        return {
          nhom: NHOM_TB[t] || 'Thiết bị khác',
          tag: e.tag || e.id || '',
          ten: e.name || e.ten || '',
          quyCach: quyCach(e),
          dv: 'bộ',
          sl: soLuong(e)
        };
      });
    }

    /** BOQ đầy đủ: thiết bị chính + vật tư suy từ hình học, gộp một danh mục. */
    function boq() {
      var ds = [];
      thietBiChinh().forEach(function (x) {
        ds.push({ nhom: 'A. Thiết bị chính — ' + x.nhom,
                  ten: (x.tag ? x.tag + ' — ' : '') + x.ten,
                  qc: x.quyCach, dv: x.dv, sl: x.sl });
      });
      dungCuDo().forEach(function (x) {
        ds.push({ nhom: 'A. Thiết bị chính — Dụng cụ đo', ten: x.vt, qc: x.qc,
                  dv: x.dv, sl: x.sl });
      });
      tongHop().forEach(function (g) {
        var nhom = /Bê tông|Thép cốt|Bu lông neo|grout|epoxy/i.test(g.vt)
                     ? 'C. Móng & kết cấu'
                 : /Cáp|Máng|gland|tiếp địa/i.test(g.vt)
                     ? 'D. Điện & điều khiển'
                     : 'B. Đường ống & phụ kiện';
        ds.push({ nhom: nhom, ten: g.vt, qc: g.qc, dv: g.dv, sl: g.slMua });
      });
      return ds;
    }

    function bangThietBi() {
      return bangHTML('Danh mục thiết bị chính',
        ['TT', 'Nhóm', 'Tag', 'Tên thiết bị', 'Quy cách kỹ thuật', 'ĐVT', 'SL'],
        thietBiChinh().map(function (x, i) {
          return [i + 1, x.nhom, x.tag, x.ten, x.quyCach, x.dv, x.sl];
        }));
    }

    /** Bảng BOQ để dán đơn giá vào — cột đơn giá và thành tiền để trống. */
    function bangBOQ() {
      var ds = boq(), nhom = '', h = '';
      var cot = ['TT', 'Hạng mục', 'Quy cách', 'ĐVT', 'SL', 'Đơn giá (VND)',
                 'Thành tiền (VND)'];
      h += '<h4 class="svws-bang-tieu">BẢNG KHỐI LƯỢNG (BOQ) — ' + ds.length +
           ' hạng mục</h4><table class="svws-bang"><thead><tr>' +
           cot.map(function (t) { return '<th>' + esc(t) + '</th>'; }).join('') +
           '</tr></thead><tbody>';
      ds.forEach(function (r, i) {
        if (r.nhom !== nhom) {
          nhom = r.nhom;
          h += '<tr><td colspan="7" style="background:#e8eff7;font-weight:600">' +
               esc(nhom) + '</td></tr>';
        }
        h += '<tr>' + [i + 1, r.ten, r.qc, r.dv, r.sl, '', ''].map(function (c) {
          return '<td>' + esc(c) + '</td>';
        }).join('') + '</tr>';
      });
      return h + '</tbody></table>';
    }

    // ------------------------------------------------------------------ tổng hợp
    function tongHop() {
      var gom = {};
      function cong(x) {
        var k = x.vt + '|' + x.qc + '|' + x.dv;
        if (!gom[k]) gom[k] = { vt: x.vt, qc: x.qc, dv: x.dv, sl: 0, tu: [] };
        gom[k].sl += so(x.sl, 0);
      }
      congDoan().forEach(function (c) { bom(c).forEach(cong); });
      mong().forEach(cong);
      dien().forEach(cong);
      var ra = [];
      for (var k in gom) {
        var g = gom[k];
        g.sl = lam(g.sl, 2);
        g.slMua = lam(g.sl * (1 + duTru), 2);     // + dự trù thi công
        ra.push(g);
      }
      ra.sort(function (a, b) { return a.vt.localeCompare(b.vt) || a.qc.localeCompare(b.qc); });
      return ra;
    }

    function tongQuan() {
      var cd = congDoan(), dai = 0, co = 0, gia = 0;
      cd.forEach(function (c) { dai += c.dai; co += c.soCo; gia += c.soGia; });
      return { soCongDoan: cd.length, tongDaiM: lam(dai / 1000, 2), tongCo: co,
               tongGia: gia,
               caoRack: cd.reduce(function (m, c) { return Math.max(m, c.caoNhat); }, 0) };
    }

    // --------------------------------------------------------------------- bảng
    function bangHTML(tieu, cot, dong) {
      var h = '<h4 class="svws-bang-tieu">' + esc(tieu) + '</h4>' +
        '<table class="svws-bang"><thead><tr>' +
        cot.map(function (t) { return '<th>' + esc(t) + '</th>'; }).join('') +
        '</tr></thead><tbody>';
      dong.forEach(function (r) {
        h += '<tr>' + r.map(function (c) { return '<td>' + esc(c) + '</td>'; }).join('') + '</tr>';
      });
      return h + '</tbody></table>';
    }

    /**
     * TOÀN BỘ công đoạn thi công, ĐÁNH SỐ theo đúng thứ tự hồ sơ thật:
     *   CĐ-01 móng → CĐ-02 lắp bể → các tuyến ống → điện → chạy thử nghiệm thu.
     * Trước đây chỉ sinh công đoạn ống, còn móng và điện là hai bảng rời không
     * đánh số, thiếu hẳn công đoạn lắp bể và công đoạn nghiệm thu.
     */
    function congDoanDayDu() {
      var ra = [], stt = 0;
      function them(kind, ten, mats, kem) {
        if (!mats || !mats.length) return;
        stt++;
        var c = { stt: stt, ma: 'CĐ-' + (stt < 10 ? '0' : '') + stt,
                  kind: kind, ten: ten, mats: mats };
        if (kem) for (var k in kem) c[k] = kem[k];
        ra.push(c);
      }
      them('civil', 'Móng, bệ thiết bị & mương thu', mong());
      them('tank', 'Lắp đặt bồn bể, đo mức và phụ kiện', lapBe());
      congDoan().forEach(function (c) {
        them('pipe', 'Tuyến ' + c.tenFrom + ' → ' + c.tenTo, bom(c), { ong: c });
      });
      them('elec', 'Điện động lực, tín hiệu và tủ điều khiển',
           dien().concat(dungCuDo()));
      them('tc', 'Lập trình, hiệu chuẩn, chạy thử và nghiệm thu', chayThu());
      return ra;
    }

    function bangCongDoan() {
      var ds = congDoanDayDu(), tq = tongQuan();
      var dem = {};
      ds.forEach(function (c) { dem[c.kind] = (dem[c.kind] || 0) + 1; });
      var h = '<div class="svws-tq">Tổng ' + ds.length + ' công đoạn (' +
        (dem.civil || 0) + ' móng · ' + (dem.tank || 0) + ' lắp bể · ' +
        (dem.pipe || 0) + ' tuyến ống · ' + (dem.elec || 0) + ' điện · ' +
        (dem.tc || 0) + ' nghiệm thu) · ' + tq.tongDaiM +
        ' m ống đo trên tuyến 3D · ' + tq.tongCo + ' co 90° · ' + tq.tongGia +
        ' giá đỡ · cao trình rack ' + tq.caoRack + ' mm</div>';
      ds.forEach(function (c) {
        h += '<h4 class="svws-bang-tieu">' + c.ma + ' · ' + esc(c.ten) + '</h4>';
        if (c.ong) {
          h += '<div class="svws-ghi">' + esc(c.ong.mo) + ' · DN' + c.ong.dn +
            ' · dài ' + c.ong.daiM + ' m · ' + c.ong.soCo + ' co 90° · cao trình ' +
            c.ong.caoNhat + ' mm</div>' +
            '<div class="svws-ve">' + veCongDoan(c.ong) + '</div>';
        }
        h += bangHTML('', ['Vật tư', 'Quy cách', 'SL', 'ĐVT', 'Căn cứ tính'],
          c.mats.map(function (b) { return [b.vt, b.qc, b.sl, b.dv, b.ghi]; }));
      });
      return h;
    }

    /* ==================================================================
     * FILE CẤU HÌNH JSON — MỘT ĐỊNH DẠNG DUY NHẤT CHO MỌI TOOL
     * Mỗi tool tự nghĩ ra một kiểu lưu thì file không dùng chéo được và sổ
     * đăng ký không đọc nổi. Dùng đúng hàm này để lưu, và nhận lại bằng
     * SVWSVT.docCauHinh() khi mở file.
     * ================================================================ */
    function xuatCauHinh(design, params) {
      return {
        type: 'svws-3d-design',
        design: design || {},
        params: params || {},
        stages: congDoanDayDu().map(function (c) {
          var s = { t: c.ma + ' · ' + c.ten, kind: c.kind,
                    mats: c.mats.map(function (b) {
                      return { name: b.vt, spec: b.qc, unit: b.dv,
                               qty: so(b.sl, 0), basis: b.ghi || '' };
                    }) };
          if (c.ong) {
            s.from = c.ong.tenFrom; s.to = c.ong.tenTo; s.dn = c.ong.dn;
            s.d = c.ong.mo;
            s.stats = { len: c.ong.dai / 1000, elbows: c.ong.soCo, tees: c.ong.soTe,
                        supports: c.ong.soGia, span: c.ong.buocGia / 1000,
                        valves: c.ong.van, maxY: c.ong.caoNhat / 1000 };
          }
          return s;
        }),
        thietBi: thietBiChinh(),
        boq: boq(),
        boqEdits: {},
        saved: new Date().toISOString()
      };
    }

    function bangTongHop() {
      return bangHTML('Tổng hợp vật tư toàn hệ (để đặt hàng)',
        ['Vật tư', 'Quy cách', 'SL tính toán', 'SL đặt hàng (+' +
         Math.round(duTru * 100) + '% dự trù)', 'ĐVT'],
        tongHop().map(function (g) { return [g.vt, g.qc, g.sl, g.slMua, g.dv]; }));
    }

    // -------------------------------------------------------------------- kiểm
    function kiemTra() {
      var loi = [], canhBao = [], cd = congDoan();
      if (!tuyen.length) {
        loi.push('Chưa nạp tuyến ống từ bản vẽ 3D — gọi V.nap(S.thongKeOng(), ' +
                 'EQUIP, pos, PIPES) SAU khi đã S.addPipes().');
        return { loi: loi, canhBao: canhBao, tongQuan: tongQuan() };
      }
      cd.forEach(function (c) {
        if (!c.dn) loi.push('Công đoạn ' + c.stt + ' (' + c.tenFrom + ' → ' + c.tenTo +
                            '): chưa có DN — không chọn được ống và phụ kiện.');
        if (c.dai < 200) loi.push('Công đoạn ' + c.stt + ': tuyến chỉ dài ' + c.dai +
                                  ' mm — hai thiết bị gần như trùng vị trí, kiểm tra ' +
                                  'lại bố cục 3D.');
        if (c.dai > 60000) canhBao.push('Công đoạn ' + c.stt + ': tuyến dài ' + c.daiM +
                                        ' m — kiểm tra lại bố cục, có thể đặt thiết bị ' +
                                        'quá xa nhau.');
        if (c.soCo > 12) canhBao.push('Công đoạn ' + c.stt + ': ' + c.soCo +
                                      ' co 90° — tổn thất áp lớn, nên nắn lại tuyến.');
      });
      // Thiết bị không nối vào đâu → chắc chắn thiếu vật tư
      var noi = {};
      tuyen.forEach(function (t) { noi[t.from] = 1; noi[t.to] = 1; });
      eq.forEach(function (e) {
        var id = e.id || e.tag;
        if (/panel|tu|mcc|plc/i.test(String(e.type || ''))) return;   // tủ điện không có ống
        if (!noi[id]) loi.push('Thiết bị ' + (e.tag || id) + ' không nối vào tuyến ống ' +
                               'nào — thiếu công đoạn và thiếu vật tư cho nó.');
      });
      // Đối chiếu với mặt bằng: tổng chiều dài ống phải hợp lý so với khu đất
      var tq = tongQuan();
      var maxX = 0, maxZ = 0;
      for (var k in pos) {
        maxX = Math.max(maxX, Math.abs(pos[k].x || 0));
        maxZ = Math.max(maxZ, Math.abs(pos[k].z || 0));
      }
      var chuViKhu = 2 * (maxX + maxZ) * 2 / 1000;      // m, ước lượng thô
      if (chuViKhu > 0 && tq.tongDaiM < chuViKhu * 0.25) {
        canhBao.push('Tổng ống ' + tq.tongDaiM + ' m nhỏ bất thường so với khu đất ' +
                     '(chu vi ≈ ' + lam(chuViKhu, 0) + ' m) — có thể thiếu tuyến.');
      }
      if (!eq.length) canhBao.push('Chưa nạp danh sách thiết bị — không tính được móng ' +
                                   'và cáp điện.');
      // BOQ thiếu thiết bị chính là thiếu phần lớn tiền — kiểm luôn ở đây.
      var tb = thietBiChinh();
      if (!tb.length) loi.push('BOQ không có thiết bị chính nào — kiểm tra lại việc nạp ' +
                               'EQUIP vào V.nap().');
      tb.forEach(function (x) {
        if (!x.quyCach) loi.push('Thiết bị ' + (x.tag || x.ten) + ' chưa có quy cách kỹ ' +
                                 'thuật — không đặt hàng và không báo giá được.');
        if (!x.tag) canhBao.push('Có thiết bị chưa đặt tag — BOQ khó đối chiếu với bản vẽ.');
      });
      return { loi: loi, canhBao: canhBao, tongQuan: tq, soThietBi: tb.length };
    }

    api.congDoan = congDoan;
    api.veCongDoan = veCongDoan;
    api.bom = bom;
    api.congDoanDayDu = congDoanDayDu;
    api.lapBe = lapBe; api.chayThu = chayThu; api.dungCuDo = dungCuDo;
    api.xuatCauHinh = xuatCauHinh;
    api.thietBiChinh = thietBiChinh;
    api.bangThietBi = bangThietBi;
    api.boq = boq;
    api.bangBOQ = bangBOQ;
    api.mong = mong;
    api.dien = dien;
    api.tongHop = tongHop;
    api.tongQuan = tongQuan;
    api.bangCongDoan = bangCongDoan;
    api.bangTongHop = bangTongHop;
    api.kiemTra = kiemTra;
    return api;
  }

  var CSS = '.svws-bang{width:100%;border-collapse:collapse;font-size:12px;font-family:' +
    FONT + ';margin:6px 0 16px}' +
    '.svws-bang th{background:#0b2545;color:#fff;padding:6px 8px;text-align:left;' +
    'font-weight:600;border:1px solid #0b2545}' +
    '.svws-bang td{padding:5px 8px;border:1px solid #cfd8e3;vertical-align:top}' +
    '.svws-bang tbody tr:nth-child(even){background:#f4f8fb}' +
    '.svws-bang-tieu{margin:14px 0 4px;font:600 13px ' + FONT + ';color:#0b2545}' +
    '.svws-ghi{font-size:12px;color:#33475b;margin:2px 0 4px}' +
    '.svws-tq{background:#eef4fb;border-left:4px solid #0b2545;padding:8px 12px;' +
    'font:600 12.5px ' + FONT + ';color:#0b2545;margin:8px 0 14px}' +
    '.svws-ve{margin:6px 0 10px}' +
    '@media print{.svws-ve{page-break-inside:avoid}}';

  global.SVWSVT = { version: '1.0', to: to, buocGia: buocGia, daiCay: daiCay, CSS: CSS };

  /* ======================================================================
   * SVWSWM — watermark dùng chung
   * Vì sao ở đây: chuẩn bắt buộc có nút Ẩn/Hiện watermark, nhưng khi AI tự
   * viết thì nút hay không ăn — nó chỉ ẩn lớp phủ của riêng nó mà bỏ sót
   * watermark vẽ CHÌM TRONG SVG của các bản vẽ, hoặc gắn sự kiện sai chỗ.
   * Dùng bộ này thì một lệnh ẩn được tất cả, và trạng thái nhớ theo máy.
   * ==================================================================== */
  var WM_KHOA = 'svws_wm_an';
  function wmCss() {
    if (document.getElementById('svws-wm-css')) return;
    var st = document.createElement('style');
    st.id = 'svws-wm-css';
    st.textContent =
      '#svws-wm{position:fixed;inset:0;z-index:9998;pointer-events:none;' +
      'display:flex;align-items:center;justify-content:center;overflow:hidden}' +
      '#svws-wm span{font:700 clamp(28px,6vw,84px) ' + FONT + ';color:rgba(179,39,30,.14);' +
      'transform:rotate(-24deg);white-space:nowrap;letter-spacing:.06em;text-align:center}' +
      'body.svws-an-wm #svws-wm{display:none}' +
      'body.svws-an-wm .svws-wm{display:none}' +
      '@media print{body.svws-an-wm #svws-wm{display:none}}';
    document.head.appendChild(st);
  }
  function wmGan(chu) {
    wmCss();
    var el = document.getElementById('svws-wm');
    if (!el) {
      el = document.createElement('div');
      el.id = 'svws-wm';
      el.innerHTML = '<span></span>';
      document.body.appendChild(el);
    }
    el.firstChild.textContent = chu || 'BẢN THAM KHẢO — CHƯA DUYỆT THI CÔNG';
    var an = false;
    try { an = localStorage.getItem(WM_KHOA) === '1'; } catch (e) {}
    wmDat(!an);
    return el;
  }
  /** hien = true để hiện, false để ẩn. Ẩn cả lớp phủ LẪN chữ chìm trong SVG. */
  function wmDat(hien) {
    wmCss();
    document.body.classList.toggle('svws-an-wm', !hien);
    // chữ chìm vẽ bằng <text> trong SVG: gắn class để CSS ở trên ẩn được
    var ds = document.querySelectorAll('svg text');
    for (var i = 0; i < ds.length; i++) {
      if (/BẢN THAM KHẢO|CHƯA DUYỆT/i.test(ds[i].textContent || ''))
        ds[i].classList.add('svws-wm');
    }
    try { localStorage.setItem(WM_KHOA, hien ? '0' : '1'); } catch (e) {}
    return hien;
  }
  function wmDao() { return wmDat(document.body.classList.contains('svws-an-wm')); }
  function wmDangHien() { return !document.body.classList.contains('svws-an-wm'); }

  global.SVWSWM = { gan: wmGan, dat: wmDat, dao: wmDao, dangHien: wmDangHien };
})(window);
