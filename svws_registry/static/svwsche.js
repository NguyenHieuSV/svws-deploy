/*!
 * SVWSCHE — bộ dựng BẢN VẼ CHẾ TẠO (SD Fabrication) chuẩn cho tool thiết kế SVWS
 * =============================================================================
 * Vì sao có thư viện này: đo được trong tool đã sinh, "3 hình chiếu" thực chất là
 * ba ô chữ nhật rỗng ở toạ độ cố định —
 *     drawBox(ctx, 10,20,70,110);  drawBox(ctx,100,20,70,110);  drawBox(ctx,190,60,90,40);
 * — GIỐNG HỆT NHAU cho mọi thiết bị, dù là bồn Ø600×H1800, vỏ lọc Ø300×H900 hay
 * móng bê tông. Không tỷ lệ, không kích thước, không nozzle. Thợ không chế tạo
 * được từ bản vẽ đó, và tờ in A3 còn không kèm hình.
 *
 * Thư viện dựng hình theo KÍCH THƯỚC THẬT, tự chọn tỷ lệ, tự ghi chuỗi kích
 * thước, tự đặt nozzle theo cao độ và góc quay. Ngoài ra nó TÍNH những thứ
 * xưởng cần: bề dày yêu cầu theo áp suất/cột nước, khai triển tôn để cắt, trọng
 * lượng chay–vận hành–thử thuỷ lực, bảng mối hàn, bảng sơn phủ.
 *
 * Dùng — mỗi thiết bị một tờ:
 *   var T = SVWSCHE.to({
 *     ma:'SVWS-DWS-1000', tag:'TK-101', ten:'Bể chứa nước thô',
 *     kieu:'bon', d:1800, h:2400, day:'chom', chan:'chande',
 *     vatLieu:'SS304', dayThan:4, dayDay:5, ap:0, mucNuoc:2200,
 *     nozzle:[{ma:'N1', dv:'Nước vào', dn:50, cao:2300, goc:0,   nho:150},
 *             {ma:'N2', dv:'Nước ra',  dn:65, cao:250,  goc:180, nho:150}]
 *   });
 *   elVe.innerHTML   = T.ve();      // tờ A3: 3 hình chiếu + kích thước + nozzle
 *   elBang.innerHTML = T.bang();    // nozzle · vật liệu · khai triển · hàn · sơn
 *   console.log(T.kiemTra());       // {loi, canhBao} — loi PHẢI rỗng
 */
(function (global) {
  'use strict';

  var NAVY = '#0b2545', INK = '#12263a', MO = '#33475b', XAM = '#6c757d';
  var DO = '#b3271e', LUC = '#1f7a4d', VANG = '#b8860b';
  var FONT = 'IBM Plex Sans,Segoe UI,Arial,sans-serif';

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
  function rongChu(s, fs, dam) {
    return String(s || '').length * fs * (dam ? 0.56 : 0.52);
  }
  function so(v, md) { v = parseFloat(v); return isFinite(v) ? v : md; }
  function lam(v, n) { var k = Math.pow(10, n || 0); return Math.round(v * k) / k; }

  // ==========================================================================
  // BẢNG TRA VẬT LIỆU — ứng suất cho phép (MPa) và khối lượng riêng (kg/m³)
  // Ứng suất lấy ở nhiệt độ thường; thiết kế nóng phải tra lại theo tiêu chuẩn.
  // ==========================================================================
  var VL = {
    SS304:  { S: 138, ro: 7930, an: 0,   ten: 'SS304 (ASTM A240 TP304)' },
    SS304L: { S: 115, ro: 7930, an: 0,   ten: 'SS304L' },
    SS316:  { S: 138, ro: 7980, an: 0,   ten: 'SS316 (ASTM A240 TP316)' },
    SS316L: { S: 115, ro: 7980, an: 0,   ten: 'SS316L' },
    CS:     { S: 118, ro: 7850, an: 2,   ten: 'Thép cacbon SS400 / A36' },
    Q235:   { S: 113, ro: 7850, an: 2,   ten: 'Thép Q235' },
    FRP:    { S: 30,  ro: 1800, an: 0,   ten: 'FRP composite (cuốn sợi)' },
    PP:     { S: 8,   ro: 910,  an: 0,   ten: 'PP tấm (hàn đùn)' },
    PE:     { S: 6,   ro: 950,  an: 0,   ten: 'HDPE tấm' },
    BTCT:   { S: 0,   ro: 2500, an: 0,   ten: 'Bê tông cốt thép' }
  };
  function traVL(m) {
    var k = String(m || 'SS304').toUpperCase().replace(/[^A-Z0-9]/g, '');
    if (VL[k]) return VL[k];
    if (/316L/.test(k)) return VL.SS316L;
    if (/316/.test(k)) return VL.SS316;
    if (/304L/.test(k)) return VL.SS304L;
    if (/304|INOX|SUS/.test(k)) return VL.SS304;
    if (/FRP|COMPOSITE|GRP/.test(k)) return VL.FRP;
    if (/HDPE|PE/.test(k)) return VL.PE;
    if (/PP/.test(k)) return VL.PP;
    if (/BTCT|BETONG|CONCRETE/.test(k)) return VL.BTCT;
    return VL.CS;
  }
  function laNhua(m) { return /FRP|PP|PE|COMPOSITE|GRP|NHUA/i.test(String(m || '')); }
  function laInox(m) { return /SS3|INOX|SUS|STAINLESS/i.test(String(m || '')); }

  // Khối lượng mặt bích ước tính theo DN (JIS 10K / PN10, kg) — dùng cho BOM,
  // thay bằng khối lượng thật của nhà cung cấp trước khi đặt hàng.
  function nangBich(dn) { return lam(0.9 + 0.0009 * dn * dn, 1); }
  // Bề dày ống nozzle thông dụng theo DN (Sch10S/Sch40 tuỳ cỡ, mm)
  function dayOng(dn) {
    return dn <= 25 ? 2.8 : dn <= 50 ? 3.0 : dn <= 100 ? 3.4 :
           dn <= 200 ? 4.0 : dn <= 300 ? 5.0 : 6.0;
  }
  // Đường kính ngoài ống theo DN (mm)
  var DN_OD = { 15: 21.3, 20: 26.7, 25: 33.4, 32: 42.2, 40: 48.3, 50: 60.3,
                65: 76.1, 80: 88.9, 100: 114.3, 125: 139.8, 150: 168.3,
                200: 219.1, 250: 273.0, 300: 323.9, 350: 355.6, 400: 406.4,
                450: 457.2, 500: 508.0, 600: 610.0 };
  function odDN(dn) { return DN_OD[dn] || (dn * 1.15 + 10); }

  // ==========================================================================
  var TY_LE = [1, 2, 2.5, 5, 10, 15, 20, 25, 40, 50, 75, 100];

  function to(o) {
    o = o || {};
    var tag = o.tag || o.id || 'EQ-01';
    var ten = o.ten || o.name || '';
    var kieu = (o.kieu || mapKieu(o.type) || 'bon').toLowerCase();
    var D = so(o.d, 1000);                     // đường kính trong / bề rộng
    var Bd = so(o.b, D);                       // bề sâu (thiết bị hình hộp)
    var H = so(o.h, 1500);                     // chiều cao thân
    var dangDay = o.day || (kieu === 'cot' ? 'chom' : 'phang');
    var chan = o.chan || (kieu === 'cot' ? 'vay' : 'chande');
    var caoChan = so(o.caoChan, chan === 'vay' ? 300 : 200);
    var vatLieu = o.vatLieu || o.material || 'SS304';
    var vl = traVL(vatLieu);
    var anMon = so(o.anMon, vl.an);
    var tThan = so(o.dayThan, 0);
    var tDay = so(o.dayDay, tThan);
    var ap = so(o.ap, 0);                      // áp suất thiết kế, bar (0 = hở)
    var mucNuoc = so(o.mucNuoc, H * 0.9);      // cột nước tính bền, mm
    var roLuu = so(o.roLuuChat, 1000);         // khối lượng riêng lưu chất
    var E = so(o.heSoMoiHan, 0.85);            // hệ số mối hàn (0,85 = RT điểm)

    var noz = (o.nozzle || o.nozzles || []).map(function (n, i) {
      return {
        ma: n.ma || n.tag || ('N' + (i + 1)),
        dv: n.dv || n.svc || n.service || '',
        dn: so(n.dn, 50),
        cao: so(n.cao, null),                  // cao độ tâm so với đáy, mm
        goc: so(n.goc, 0),                     // góc quay, độ (0 = trục +X)
        nho: so(n.nho, 150),                   // độ nhô mặt bích khỏi thành
        chuan: n.chuan || (laNhua(vatLieu) ? 'PN10 FF' : 'JIS 10K RF'),
        tren: !!n.tren                         // đặt trên nắp
      };
    });
    if (!noz.length) noz = nozMacDinh(kieu, D, H);
    noz.forEach(function (n) {
      if (n.cao === null) n.cao = H * 0.5;
    });

    // ---------------------------------------------------------------- tính bền
    /** Bề dày yêu cầu — nguồn số liệu để KIỂM, không phải để trang trí. */
    function benThan() {
      if (vl.S <= 0) return null;              // bê tông: không dùng công thức vỏ
      // Áp suất thiết kế lấy giá trị lớn hơn giữa áp trong và cột nước tĩnh.
      var pAp = ap * 0.1;                                        // bar → MPa
      var pNuoc = roLuu * 9.81 * (mucNuoc / 1000) / 1e6;         // MPa
      var P = Math.max(pAp, pNuoc);
      var t;
      if (ap > 0) t = P * (D / 2) / (vl.S * E - 0.6 * P);        // vỏ chịu áp
      else        t = P * D / (2 * vl.S * E);                    // bể hở, cột nước
      t += anMon;
      // Bề dày TỐI THIỂU theo thực tế xưởng: tôn quá mỏng không cuốn tròn nổi
      // và cong vênh khi hàn, nên công thức ra 1,2 mm cũng không dùng được.
      var toiThieu = laNhua(vatLieu) ? (D >= 1500 ? 8 : D >= 800 ? 6 : 4)
                                     : (D >= 1500 ? 5 : D >= 800 ? 4 : 3);
      return { P: P, tinh: lam(t, 2), toiThieu: toiThieu,
               canDung: lam(Math.max(t, toiThieu), 2) };
    }
    var ben = benThan();
    if (!tThan) tThan = ben ? Math.ceil(ben.canDung) : 5;
    if (!tDay) tDay = Math.ceil(tThan * 1.2);

    // ------------------------------------------------------------ trọng lượng
    function trongLuong() {
      var m3 = 1e9;                            // mm³ → m³
      var vThan = Math.PI * D * H * tThan / m3;
      var aDay = dangDay === 'chom' ? Math.PI / 4 * Math.pow(1.22 * D, 2)
                                    : Math.PI / 4 * D * D;
      var vDay = aDay * tDay / m3;
      var vNap = (kieu === 'cot' ? aDay * tDay : Math.PI / 4 * D * D * tThan) / m3;
      var kgVo = (vThan + vDay + vNap) * vl.ro;
      var kgNoz = 0;
      noz.forEach(function (n) {
        var od = odDN(n.dn), tn = dayOng(n.dn);
        kgNoz += Math.PI * od * (n.nho + 60) * tn / m3 * vl.ro + nangBich(n.dn);
      });
      var kgChan = so(o.nangChan, kgVo * 0.12);          // chân/váy ≈ 12 % vỏ
      var chay = kgVo + kgNoz + kgChan;
      var nuoc = Math.PI / 4 * D * D * mucNuoc / m3 * roLuu;
      var day = Math.PI / 4 * D * D * H / m3 * 1000;     // thử thuỷ lực: đầy nước
      return { vo: lam(kgVo, 0), nozzle: lam(kgNoz, 0), chan: lam(kgChan, 0),
               chay: lam(chay, 0), vanHanh: lam(chay + nuoc, 0),
               thuThuyLuc: lam(chay + day, 0), nuoc: lam(nuoc, 0) };
    }

    // ------------------------------------------------------------ khai triển
    /** Kích thước phôi tôn để CẮT — thứ xưởng cần nhất mà bản cũ không có. */
    function khaiTrien() {
      var ds = [];
      // Chiều dài phôi lấy theo ĐƯỜNG TRUNG BÌNH (D + t), không phải D trong:
      // lấy D trong là thiếu π·t, cuốn xong hụt mép, thợ phải kéo hoặc chêm.
      var dai = Math.PI * (D + tThan);
      ds.push({ ct: 'Thân (cuốn tròn)', pt: lam(dai, 0) + ' × ' + H + ' × ' + tThan +
                ' mm', sl: 1,
                ghi: 'Chiều dài = π×(D+t) = π×(' + D + '+' + tThan + '). Chừa 2×3 mm ' +
                     'mép vát hàn dọc.' });
      if (dangDay === 'chom') {
        ds.push({ ct: 'Đáy chỏm cầu', pt: 'Ø' + lam(1.22 * D, 0) + ' × ' + tDay + ' mm',
                  sl: 1, ghi: 'Phôi tròn Ø1,22×D cho chỏm tiêu chuẩn (R≈D, r≈0,1D). ' +
                              'Dập nóng hoặc miết.' });
      } else if (dangDay === 'con') {
        var Lcon = Math.sqrt(Math.pow(D / 2, 2) + Math.pow(so(o.caoCon, D * 0.4), 2));
        ds.push({ ct: 'Đáy côn (khai triển quạt)',
                  pt: 'R = ' + lam(Lcon, 0) + ' mm, cung = ' +
                      lam(180 * D / Lcon, 1) + '°', sl: 1,
                  ghi: 'Cắt hình quạt bán kính bằng đường sinh côn.' });
      } else {
        ds.push({ ct: 'Đáy phẳng', pt: 'Ø' + lam(D + 2 * tThan + 20, 0) + ' × ' +
                  tDay + ' mm', sl: 1, ghi: 'Chừa 10 mm mép hàn góc quanh chu vi.' });
      }
      if (kieu === 'cot') {
        ds.push({ ct: 'Nắp chỏm cầu', pt: 'Ø' + lam(1.22 * D, 0) + ' × ' + tDay + ' mm',
                  sl: 1, ghi: 'Như đáy.' });
      }
      noz.forEach(function (n) {
        ds.push({ ct: 'Ống nozzle ' + n.ma + ' DN' + n.dn,
                  pt: 'Ø' + odDN(n.dn) + ' × ' + lam(n.nho + 60, 0) + ' mm, dày ' +
                      dayOng(n.dn) + ' mm', sl: 1,
                  ghi: 'Cắt vát yên ngựa theo Ø' + D + '. Lỗ khoét thành: Ø' +
                       lam(odDN(n.dn) + 2, 0) + ' mm.' });
      });
      return ds;
    }

    // ------------------------------------------------------------ mối hàn
    function moiHan() {
      if (laNhua(vatLieu)) {
        return [{ ky: 'H1', vt: 'Mối nối thân', kieuH: 'Hàn đùn / hàn nhiệt kép',
                  kt: 'Theo DVS 2207', ktr: 'Thử kéo mẫu 1 mối/ca' },
                { ky: 'H2', vt: 'Nozzle vào thân', kieuH: 'Hàn đùn quanh cổ',
                  kt: '2 lớp', ktr: 'Thử kín bằng nước' }];
      }
      var kv = laInox(vatLieu) ? 'TIG (GTAW) que ER308L' : 'MIG/MAG (GMAW) ER70S-6';
      return [
        { ky: 'H1', vt: 'Mối hàn DỌC thân', kieuH: 'Giáp mối vát V đôi, ngấu hoàn toàn',
          kt: kv, ktr: '100 % thẩm thấu (PT) + chụp phim RT 10 % chiều dài' },
        { ky: 'H2', vt: 'Mối hàn VÒNG thân – đáy', kieuH: 'Giáp mối vát V, ngấu hoàn toàn',
          kt: kv, ktr: '100 % PT + RT 10 %' },
        { ky: 'H3', vt: 'Nozzle vào thành (set-in)',
          kieuH: 'Vát mép + hàn góc ngoài, chân hàn a = ' + lam(0.7 * tThan, 1) + ' mm',
          kt: kv, ktr: '100 % PT, thử kín' },
        { ky: 'H4', vt: 'Chân đỡ / váy vào vỏ',
          kieuH: 'Hàn góc liên tục a = ' + lam(0.7 * Math.min(tThan, 8), 1) + ' mm',
          kt: kv, ktr: 'Kiểm tra bằng mắt (VT) 100 %' },
        { ky: '—', vt: 'Sau khi hàn', kieuH: laInox(vatLieu)
            ? 'Tẩy mối hàn bằng gel axit, rửa sạch, thụ động hoá'
            : 'Làm sạch xỉ, mài phẳng mối hàn lộ',
          kt: '—', ktr: 'Thử thuỷ lực toàn bồn ' +
               lam(Math.max(1.5 * ap, 0.1), 2) + ' MPa giữ 30 phút, không rò' }
      ];
    }

    function sonPhu() {
      if (laInox(vatLieu)) {
        return ['Không sơn. Xử lý bề mặt: tẩy axit (pickling) toàn bộ mối hàn và ' +
                'vùng nhiệt ảnh hưởng, rửa nước sạch, thụ động hoá (passivation).',
                'Bề mặt trong tiếp xúc nước: đánh bóng cơ khí đến Ra ≤ 1,6 µm.'];
      }
      if (laNhua(vatLieu)) return ['Không sơn. Bảo vệ tránh tia UV khi đặt ngoài trời.'];
      return ['Làm sạch bề mặt bằng phun hạt đến cấp Sa 2.5 (ISO 8501-1).',
              'Trong lòng (tiếp xúc nước): sơn epoxy gốc nước 2 lớp, tổng ≥ 250 µm khô, ' +
              'đạt chứng nhận tiếp xúc nước sinh hoạt.',
              'Ngoài: epoxy lót 80 µm + phủ polyurethane 60 µm, tổng ≥ 140 µm khô.',
              'Đo chiều dày màng khô bằng máy, kiểm tra độ bám dính theo ISO 2409.'];
    }

    // ==================================================================== VẼ
    /**
     * Chọn tỷ lệ VÀ vị trí ba hình chiếu bằng cách ĐO chỗ thật sự cần: nozzle
     * nhô ra bao xa, chuỗi kích thước chiếm mấy làn. Tính kiểu ước lượng thì
     * chuỗi kích thước của bồn nhiều nozzle sẽ chạy ra ngoài mép giấy.
     */
    function boCuc() {
      var W = 1580, Hs = 1120;
      var vungTren = 118, vungDuoi = 928;
      var soNoz = noz.filter(function (n) { return !n.tren; }).length;
      var chuoi = 34 * (soNoz + 1) + 30;       // các làn kích thước bên trái
      var napNho = (kieu === 'cot' ? D * 0.25 : 0);
      var chonI = TY_LE.length - 1, kq = null;
      for (var i = 0; i < TY_LE.length; i++) {
        var sc = 1 / TY_LE[i], R = D / 2;
        var caoGiay = (H + napNho + caoChan) * sc + 70;   // + chú thích hình chiếu
        if (caoGiay > vungDuoi - vungTren) continue;
        // Nozzle nhô xa nhất, kể cả bề rộng nhãn của nó
        var ext = 40;
        noz.forEach(function (n) {
          if (n.tren) return;
          ext = Math.max(ext, (n.nho + odDN(n.dn)) * sc + rongChu(n.ma, 8.6, 1) + 24);
        });
        var rC = Math.min(200, Math.max(88, R * sc * 1.6));
        var xA = 46 + ext + chuoi + R * sc;
        var xB = xA + R * sc + ext + 56 + ext + R * sc;
        var xC = xB + R * sc + ext + 70 + rC;
        // chú thích nozzle ở hình chiếu bằng còn cần rC+110 nữa về bên phải
        if (xC + rC + 110 > W - 30) continue;
        kq = { sc: sc, R: R, ext: ext, chuoi: chuoi, rC: rC,
               xA: xA, xB: xB, xC: xC, caoGiay: caoGiay };
        chonI = i;
        break;
      }
      if (!kq) {                                // khổ A3 không chứa nổi
        var scc = 1 / TY_LE[TY_LE.length - 1], Rc = D / 2;
        kq = { sc: scc, R: Rc, ext: 60, chuoi: chuoi,
               rC: 120, xA: 300, xB: 760, xC: 1230,
               caoGiay: (H + napNho + caoChan) * scc };
      }
      var yDay = vungTren +
                 Math.max(0, (vungDuoi - vungTren - kq.caoGiay) / 2) +
                 (H + napNho) * kq.sc;
      kq.W = W; kq.H = Hs; kq.tyLe = lam(1 / kq.sc, 1);
      kq.yDay = yDay; kq.vungTren = vungTren; kq.vungDuoi = vungDuoi;
      kq.napNho = napNho;
      return kq;
    }

    function dungHinh() {
      var b = boCuc(), sc = b.sc;
      var out = [], chiem = [];
      function push(s) { out.push(s); }
      function chiemO(x1, y1, x2, y2, t, loai) {
        chiem.push({ x1: x1, y1: y1, x2: x2, y2: y2, ten: t, loai: loai || '' });
      }
      function ln(x1, y1, x2, y2, mau, w, net) {
        push('<line x1="' + lam(x1, 1) + '" y1="' + lam(y1, 1) + '" x2="' + lam(x2, 1) +
          '" y2="' + lam(y2, 1) + '" stroke="' + (mau || NAVY) + '" stroke-width="' +
          (w || 1.4) + '"' + (net ? ' stroke-dasharray="' + net + '"' : '') + '/>');
      }
      function trong(r) {
        for (var i = 0; i < chiem.length; i++) {
          var c = chiem[i];
          if (!(r.x2 + 2 < c.x1 || c.x2 + 2 < r.x1 ||
                r.y2 + 2 < c.y1 || c.y2 + 2 < r.y1)) return false;
        }
        return true;
      }
      /** Đặt chữ; ne = [dx,dy] thì TỰ ĐẨY theo hướng đó cho tới khi hết đè. */
      function chu(x, y, s, fs, mau, neo, dam, ghi, ne) {
        fs = fs || 9; neo = neo || 'middle';
        var w = rongChu(s, fs, dam), dx = neo === 'middle' ? -w / 2 : neo === 'end' ? -w : 0;
        if (ne) {
          for (var k = 0; k < 12; k++) {
            var r = { x1: x + dx - 1, y1: y - fs, x2: x + dx + w + 1, y2: y + 2 };
            if (trong(r)) break;
            x += ne[0]; y += ne[1];
          }
        }
        if (ghi !== false) chiemO(x + dx - 1, y - fs, x + dx + w + 1, y + 2, 'chữ:' + s);
        push('<text x="' + lam(x, 1) + '" y="' + lam(y, 1) + '" font-size="' + fs +
          '" fill="' + (mau || INK) + '" text-anchor="' + neo + '"' +
          (dam ? ' font-weight="600"' : '') + ' font-family="' + FONT + '">' +
          esc(s) + '</text>');
      }
      /** Đường kích thước có hai mũi tên và số đo THẬT (mm). */
      function kt(x1, y1, x2, y2, giaTri, lech, doc) {
        var m = DO;
        if (doc) {
          var xx = x1 + lech;
          ln(x1, y1, xx + 6, y1, m, 0.7); ln(x2, y2, xx + 6, y2, m, 0.7);
          ln(xx, y1, xx, y2, m, 1);
          muiTen(xx, y1, 0, 1); muiTen(xx, y2, 0, -1);
          push('<text x="' + lam(xx - 5, 1) + '" y="' + lam((y1 + y2) / 2, 1) +
            '" font-size="9.5" fill="' + m + '" text-anchor="middle" transform="rotate(-90 ' +
            lam(xx - 5, 1) + ',' + lam((y1 + y2) / 2, 1) + ')" font-family="' + FONT + '">' +
            esc(String(giaTri)) + '</text>');
          chiemO(xx - 16, Math.min(y1, y2), xx + 8, Math.max(y1, y2), 'kt ' + giaTri);
        } else {
          var yy = y1 + lech;
          ln(x1, y1, x1, yy + 6, m, 0.7); ln(x2, y2, x2, yy + 6, m, 0.7);
          ln(x1, yy, x2, yy, m, 1);
          muiTen(x1, yy, 1, 0); muiTen(x2, yy, -1, 0);
          chu((x1 + x2) / 2, yy - 4, String(giaTri), 9.5, m, 'middle', 0, false);
          chiemO(Math.min(x1, x2), yy - 15, Math.max(x1, x2), yy + 8, 'kt ' + giaTri);
        }
      }
      function muiTen(x, y, dx, dy) {
        var s = 5;
        push('<path d="M' + lam(x, 1) + ' ' + lam(y, 1) + ' L' + lam(x + dx * s - dy * 2.2, 1) +
          ' ' + lam(y + dy * s - dx * 2.2, 1) + ' L' + lam(x + dx * s + dy * 2.2, 1) + ' ' +
          lam(y + dy * s + dx * 2.2, 1) + ' Z" fill="' + DO + '"/>');
      }

      // ---------------------------------------------------- khung tờ + tiêu đề
      push('<rect width="' + b.W + '" height="' + b.H + '" fill="#fdfefe"/>');
      push('<rect x="12" y="12" width="' + (b.W - 24) + '" height="' + (b.H - 24) +
        '" fill="none" stroke="' + NAVY + '" stroke-width="2"/>');
      chu(30, 42, 'BẢN VẼ CHẾ TẠO — ' + tag + (ten ? ' · ' + ten : ''), 16, NAVY,
          'start', 1, false);
      chu(30, 64, 'Vật liệu ' + vl.ten + ' · thân dày ' + tThan + ' mm · đáy dày ' +
          tDay + ' mm · tỷ lệ 1:' + b.tyLe + ' · đơn vị mm', 10.5, MO, 'start', 0, false);

      // ------------------------------------------------------- HÌNH CHIẾU ĐỨNG
      // Cao độ đáy tính để vật thể NẰM GIỮA vùng vẽ — để cố định thì thiết bị
      // thấp bị dồn xuống mép dưới, chừa mảng trắng lớn phía trên.
      var napNho = b.napNho, vungTren = b.vungTren, vungDuoi = b.vungDuoi;
      var yDay = b.yDay, xA = b.xA;
      function mx(v) { return xA + v * sc; }
      function my(caoMm) { return yDay - caoMm * sc; }   // cao độ mm → y giấy
      var R = D / 2;

      // chân đỡ / váy
      if (chan === 'vay') {
        ln(mx(-R), my(0), mx(-R), my(-caoChan), NAVY, 1.6);
        ln(mx(R), my(0), mx(R), my(-caoChan), NAVY, 1.6);
        ln(mx(-R * 1.15), my(-caoChan), mx(R * 1.15), my(-caoChan), NAVY, 2.2);
      } else {
        [-0.72, 0.72].forEach(function (k) {
          ln(mx(R * k), my(0), mx(R * k), my(-caoChan), NAVY, 2.4);
          ln(mx(R * k - 60), my(-caoChan), mx(R * k + 60), my(-caoChan), NAVY, 2.4);
        });
      }

      // đáy
      if (dangDay === 'chom') {
        var sag = D * 0.25;
        push('<path d="M' + lam(mx(-R), 1) + ' ' + lam(my(0), 1) + ' Q' + lam(mx(0), 1) +
          ' ' + lam(my(-sag * 1.9), 1) + ' ' + lam(mx(R), 1) + ' ' + lam(my(0), 1) +
          '" fill="#eef4fb" stroke="' + NAVY + '" stroke-width="1.8"/>');
      } else if (dangDay === 'con') {
        var hc = so(o.caoCon, D * 0.4);
        push('<path d="M' + lam(mx(-R), 1) + ' ' + lam(my(0), 1) + ' L' + lam(mx(0), 1) +
          ' ' + lam(my(-hc), 1) + ' L' + lam(mx(R), 1) + ' ' + lam(my(0), 1) +
          ' Z" fill="#eef4fb" stroke="' + NAVY + '" stroke-width="1.8"/>');
      } else {
        ln(mx(-R), my(0), mx(R), my(0), NAVY, 2.2);
      }
      // thân
      push('<rect x="' + lam(mx(-R), 1) + '" y="' + lam(my(H), 1) + '" width="' +
        lam(D * sc, 1) + '" height="' + lam(H * sc, 1) +
        '" fill="#f4f8fb" stroke="' + NAVY + '" stroke-width="1.8"/>');
      // KHÔNG đăng ký thân/đáy/chân làm vật cản: nozzle BẮT BUỘC phải chạm thành,
      // nhãn mực nước nằm trong lòng bồn là đúng. Đăng ký chúng thì mọi tiếp xúc
      // hợp lệ đều bị báo là lỗi. Chỉ ký hiệu nozzle và CHỮ mới là vật cản.
      // nắp
      if (kieu === 'cot') {
        var sagN = D * 0.25;
        push('<path d="M' + lam(mx(-R), 1) + ' ' + lam(my(H), 1) + ' Q' + lam(mx(0), 1) +
          ' ' + lam(my(H + sagN * 1.9), 1) + ' ' + lam(mx(R), 1) + ' ' + lam(my(H), 1) +
          '" fill="#eef4fb" stroke="' + NAVY + '" stroke-width="1.8"/>');
      } else {
        ln(mx(-R), my(H), mx(R), my(H), NAVY, 1.8);
      }
      // Mực nước vẽ SAU nozzle (xem cuối khối) — vẽ trước thì lúc đặt nhãn chưa
      // biết nozzle nằm đâu để mà né.
      if (mucNuoc > 0 && mucNuoc < H) {
        ln(mx(-R) + 3, my(mucNuoc), mx(R) - 3, my(mucNuoc), '#2f9fd0', 1, '7 4');
      }

      // nozzle trên hình chiếu đứng: chiếu theo cos(góc)
      noz.forEach(function (n) {
        var od = odDN(n.dn), c = Math.cos(n.goc * Math.PI / 180);
        var y = my(n.cao);
        if (n.tren) {                              // nozzle trên nắp: nhô lên
          var xo = mx(so(n.lech, 0));
          push('<rect x="' + lam(xo - od / 2 * sc, 1) + '" y="' + lam(my(H) - n.nho * sc, 1) +
            '" width="' + lam(od * sc, 1) + '" height="' + lam(n.nho * sc, 1) +
            '" fill="#fff" stroke="' + NAVY + '" stroke-width="1.4"/>');
          ln(xo - od * 0.85 * sc, my(H) - n.nho * sc, xo + od * 0.85 * sc,
             my(H) - n.nho * sc, NAVY, 3);
          chu(xo, my(H) - n.nho * sc - 8, n.ma, 8.6, DO, 'middle', 1);
          return;
        }
        if (Math.abs(c) < 0.35) {                  // gần vuông góc mặt giấy → thấy tròn
          push('<circle cx="' + lam(mx(R * 0.55), 1) + '" cy="' + lam(y, 1) + '" r="' +
            lam(od / 2 * sc, 1) + '" fill="none" stroke="' + NAVY +
            '" stroke-width="1.3" stroke-dasharray="4 3"/>');
          chiemO(mx(R * 0.55) - od / 2 * sc, y - od / 2 * sc, mx(R * 0.55) + od / 2 * sc,
                 y + od / 2 * sc, n.ma + ' (xoay vào hình)', 'noz');
          chu(mx(R * 0.55), y - od / 2 * sc - 6, n.ma, 8.6, DO, 'middle', 1,
              true, [0, -12]);
          return;
        }
        var dau = c > 0 ? 1 : -1;
        var x0 = mx(dau * R), x1 = mx(dau * (R + n.nho));
        push('<rect x="' + lam(Math.min(x0, x1), 1) + '" y="' + lam(y - od / 2 * sc, 1) +
          '" width="' + lam(Math.abs(x1 - x0), 1) + '" height="' + lam(od * sc, 1) +
          '" fill="#fff" stroke="' + NAVY + '" stroke-width="1.4"/>');
        ln(x1, y - od * 0.85 * sc, x1, y + od * 0.85 * sc, NAVY, 3);   // mặt bích
        chiemO(Math.min(x0, x1), y - od / 2 * sc - 2, Math.max(x0, x1) + 4,
               y + od / 2 * sc + 2, n.ma, 'noz');
        chu(x1 + dau * 14, y + 3, n.ma, 8.6, DO, dau > 0 ? 'start' : 'end', 1,
            true, [0, -13]);
      });

      if (mucNuoc > 0 && mucNuoc < H) {
        chu(mx(R) - 8, my(mucNuoc) - 4, 'MỰC NƯỚC TK ' + mucNuoc, 7.6, '#2f9fd0',
            'end', 0, true, [0, 12]);
      }

      // Chuỗi kích thước: khoảng lệch ĐO theo nozzle nhô ra xa nhất về mỗi phía,
      // không dùng hằng số — để hằng số thì nozzle dài là đường kích thước cắt
      // ngang qua mặt bích.
      var lechT = -(b.ext + 20);
      kt(mx(-R), my(0), mx(-R), my(H), H, lechT, true);
      kt(mx(R), my(0), mx(R), my(-caoChan), caoChan, b.ext + 20, true);
      kt(mx(-R), my(0), mx(R), my(0), 'Ø' + D + ' (trong)', 74, false);
      // cao độ từng nozzle — thợ khoét lỗ theo con số này
      noz.filter(function (n) { return !n.tren; })
         .sort(function (a, b) { return a.cao - b.cao; })
         .forEach(function (n, i) {
        kt(mx(-R), my(0), mx(-R), my(n.cao), n.ma + ' +' + n.cao, lechT - 34 * (i + 1), true);
      });
      chu(mx(0), yDay + Math.max(caoChan * sc + 46, 112), 'HÌNH CHIẾU ĐỨNG', 11, NAVY, 'middle', 1);

      // -------------------------------------------------------- HÌNH CHIẾU CẠNH
      var xB = b.xB;
      function mxB(v) { return xB + v * sc; }
      push('<rect x="' + lam(mxB(-R), 1) + '" y="' + lam(my(H), 1) + '" width="' +
        lam(D * sc, 1) + '" height="' + lam(H * sc, 1) +
        '" fill="#f4f8fb" stroke="' + NAVY + '" stroke-width="1.8"/>');
      if (dangDay === 'chom') {
        var s2 = D * 0.25;
        push('<path d="M' + lam(mxB(-R), 1) + ' ' + lam(my(0), 1) + ' Q' + lam(mxB(0), 1) +
          ' ' + lam(my(-s2 * 1.9), 1) + ' ' + lam(mxB(R), 1) + ' ' + lam(my(0), 1) +
          '" fill="#eef4fb" stroke="' + NAVY + '" stroke-width="1.8"/>');
      } else ln(mxB(-R), my(0), mxB(R), my(0), NAVY, 2.2);
      if (kieu === 'cot') {
        var s3 = D * 0.25;
        push('<path d="M' + lam(mxB(-R), 1) + ' ' + lam(my(H), 1) + ' Q' + lam(mxB(0), 1) +
          ' ' + lam(my(H + s3 * 1.9), 1) + ' ' + lam(mxB(R), 1) + ' ' + lam(my(H), 1) +
          '" fill="#eef4fb" stroke="' + NAVY + '" stroke-width="1.8"/>');
      } else ln(mxB(-R), my(H), mxB(R), my(H), NAVY, 1.8);
      if (chan === 'vay') {
        ln(mxB(-R), my(0), mxB(-R), my(-caoChan), NAVY, 1.6);
        ln(mxB(R), my(0), mxB(R), my(-caoChan), NAVY, 1.6);
        ln(mxB(-R * 1.15), my(-caoChan), mxB(R * 1.15), my(-caoChan), NAVY, 2.2);
      } else {
        [-0.72, 0.72].forEach(function (k) {
          ln(mxB(R * k), my(0), mxB(R * k), my(-caoChan), NAVY, 2.4);
          ln(mxB(R * k - 60), my(-caoChan), mxB(R * k + 60), my(-caoChan), NAVY, 2.4);
        });
      }
      // nozzle chiếu theo sin(góc) — nhìn từ cạnh
      noz.forEach(function (n) {
        if (n.tren) return;
        var od = odDN(n.dn), s = Math.sin(n.goc * Math.PI / 180), y = my(n.cao);
        if (Math.abs(s) < 0.35) {
          push('<circle cx="' + lam(mxB(R * 0.55), 1) + '" cy="' + lam(y, 1) + '" r="' +
            lam(od / 2 * sc, 1) + '" fill="none" stroke="' + NAVY +
            '" stroke-width="1.3" stroke-dasharray="4 3"/>');
          return;
        }
        var dau = s > 0 ? 1 : -1;
        var x0 = mxB(dau * R), x1 = mxB(dau * (R + n.nho));
        push('<rect x="' + lam(Math.min(x0, x1), 1) + '" y="' + lam(y - od / 2 * sc, 1) +
          '" width="' + lam(Math.abs(x1 - x0), 1) + '" height="' + lam(od * sc, 1) +
          '" fill="#fff" stroke="' + NAVY + '" stroke-width="1.4"/>');
        ln(x1, y - od * 0.85 * sc, x1, y + od * 0.85 * sc, NAVY, 3);
        chiemO(Math.min(x0, x1), y - od / 2 * sc - 2, Math.max(x0, x1) + 4,
               y + od / 2 * sc + 2, n.ma + '(cạnh)', 'noz');
        chu(x1 + dau * 14, y + 3, n.ma, 8.6, DO, dau > 0 ? 'start' : 'end', 1,
            true, [0, -13]);
      });
      chu(mxB(0), yDay + Math.max(caoChan * sc + 46, 112), 'HÌNH CHIẾU CẠNH', 11, NAVY, 'middle', 1);

      // ---------------------------------- HÌNH CHIẾU BẰNG — sơ đồ định vị nozzle
      var xC = b.xC, rC = b.rC;
      // Hình chiếu bằng canh giữa theo chính vùng vẽ, không để số cố định.
      var yC = vungTren + 60 + rC;
      push('<circle cx="' + xC + '" cy="' + yC + '" r="' + lam(rC, 1) +
        '" fill="#f4f8fb" stroke="' + NAVY + '" stroke-width="1.8"/>');
      ln(xC - rC - 26, yC, xC + rC + 26, yC, XAM, 0.8, '9 4 3 4');
      ln(xC, yC - rC - 26, xC, yC + rC + 26, XAM, 0.8, '9 4 3 4');
      // Mốc góc đặt ở 45/135/225/315° — để ở 0/90/180/270 thì đúng chỗ nozzle
      // hay nằm nhất, chú thích nozzle sẽ đè lên mốc góc.
      [[45, '0° ↔'], [135, '90°'], [225, '180°'], [315, '270°']].forEach(function (g, i) {
        var a = g[0] * Math.PI / 180;
        var nhan = ['45°', '135°', '225°', '315°'][i];
        chu(xC + Math.cos(a) * (rC + 22), yC - Math.sin(a) * (rC + 22) + 4,
            nhan, 8, XAM, 'middle', 0, false);
      });
      ['0°', '90°', '180°', '270°'].forEach(function (t, i) {
        var a = i * 90 * Math.PI / 180;
        chu(xC + Math.cos(a) * (rC + 15), yC - Math.sin(a) * (rC + 15) + 3.5,
            t, 8.6, XAM, 'middle', 1, false);
      });
      chu(xC, yC - rC - 62, 'BẮC ↑ (chuẩn định hướng lắp)', 8.6, MO, 'middle', 0, false);
      noz.forEach(function (n) {
        if (n.tren) {
          push('<circle cx="' + xC + '" cy="' + yC + '" r="' +
            lam(odDN(n.dn) / 2 * sc, 1) + '" fill="#fff" stroke="' + NAVY + '"/>');
          chu(xC, yC + 4, n.ma, 8, DO, 'middle', 1);
          return;
        }
        var a = n.goc * Math.PI / 180, ca = Math.cos(a), sa = Math.sin(a);
        var x1 = xC + ca * rC, y1 = yC - sa * rC;
        var x2 = xC + ca * (rC + 34), y2 = yC - sa * (rC + 34);
        ln(x1, y1, x2, y2, NAVY, Math.max(2, odDN(n.dn) * sc * 0.5));
        ln(x2 + sa * 9, y2 + ca * 9, x2 - sa * 9, y2 - ca * 9, NAVY, 3);
        // Chú thích đẩy RA XA TÂM khi vướng — hai nozzle cùng góc khác cao độ là
        // chuyện bình thường, nhưng chú thích của chúng thì không được chồng.
        chu(xC + ca * (rC + 62), yC - sa * (rC + 62) + 3,
            n.ma + ' DN' + n.dn + ' @' + n.goc + '°', 8.4, DO, 'middle', 1,
            true, [ca * 15, -sa * 15]);
      });
      chu(xC, yC + rC + 96, 'HÌNH CHIẾU BẰNG — ĐỊNH VỊ NOZZLE', 11, NAVY, 'middle', 1);

      // --------------------------------------------------------- ghi chú chung
      // Tờ A3 phải ĐỌC ĐƯỢC ĐỘC LẬP: thợ cầm tờ in ra xưởng, không mở app.
      var gx = 46, gy = Math.max(yDay + caoChan * sc + 150, 660);
      var ghi = [
        'VẬT LIỆU: ' + vl.ten + ' · thân dày ' + tThan + ' mm · đáy dày ' + tDay +
          ' mm · dự phòng ăn mòn ' + anMon + ' mm.',
        ben ? ('BỀ DÀY YÊU CẦU: ' + ben.canDung + ' mm (tính ' + ben.tinh +
               ' mm, tối thiểu xưởng ' + ben.toiThieu + ' mm) — chọn dùng ' + tThan +
               ' mm: ' + (tThan >= ben.canDung ? 'ĐẠT.' : 'CHƯA ĐẠT, phải tăng.')) : '',
        'HÀN: theo bảng mối hàn kèm bản vẽ. Thử thuỷ lực ' +
          lam(Math.max(1.5 * ap, 0.1), 2) + ' MPa, giữ 30 phút, không rò rỉ.',
        'BỀ MẶT: ' + sonPhu()[0],
        'KHỐI LƯỢNG: chay ' + trongLuong().chay + ' kg · vận hành ' +
          trongLuong().vanHanh + ' kg · thử thuỷ lực ' + trongLuong().thuThuyLuc +
          ' kg (dùng để tính móng).',
        'DUNG SAI CHẾ TẠO: đường kính ±0,5 % D · chiều cao ±5 mm · độ thẳng đứng ' +
          '≤ 3 mm/m · độ phẳng mặt bích ≤ 0,5 mm.',
        'Kích thước tính bằng mm. Cao độ nozzle đo từ MẶT TRONG ĐÁY. Góc quay đo ' +
          'ngược chiều kim đồng hồ nhìn từ trên xuống, mốc 0° theo hình chiếu bằng.'
      ].filter(Boolean);
      chu(gx, gy, 'GHI CHÚ CHẾ TẠO', 11, NAVY, 'start', 1, false);
      ln(gx, gy + 6, gx + 700, gy + 6, NAVY, 1);
      ghi.forEach(function (t, i) {
        chu(gx + 10, gy + 26 + i * 17, '• ' + t, 8.6, INK, 'start', 0, false);
      });
      chiemO(gx - 4, gy - 14, gx + 706, gy + 26 + ghi.length * 17, 'khối ghi chú');

      // ------------------------------------------------------------- khung tên
      var kx = b.W - 520, ky = b.H - 132;
      push('<rect x="' + kx + '" y="' + ky + '" width="500" height="112" fill="#fff" stroke="' +
        NAVY + '" stroke-width="1.6"/>');
      var hang = [
        ['Công ty', o.congTy || 'CÔNG TY TNHH GIẢI PHÁP KỸ THUẬT SÓNG VIỆT'],
        ['Dự án / Mã', (o.duAn || '') + (o.ma ? '  ·  ' + o.ma : '')],
        ['Tên bản vẽ', 'Chế tạo ' + tag + (ten ? ' — ' + ten : '')],
        ['Tỷ lệ · Khổ', '1:' + b.tyLe + '  ·  A3  ·  đơn vị mm'],
        ['Người lập · Ngày · Rev', (o.nguoiLap || '') + '  ·  ' + (o.ngay || '') +
                                   '  ·  ' + (o.rev || 'Rev.A')]
      ];
      hang.forEach(function (r, i) {
        var y = ky + 20 + i * 21;
        chu(kx + 10, y, r[0], 8.4, XAM, 'start', 0, false);
        chu(kx + 128, y, r[1], 9, INK, 'start', 1, false);
        if (i) ln(kx, y - 15, kx + 500, y - 15, '#dde5ee', 0.8);
      });
      chu(b.W / 2, b.H - 22, 'BẢN THAM KHẢO — CHƯA DUYỆT THI CÔNG', 13,
          'rgba(179,39,30,0.30)', 'middle', 1, false);

      // Va chạm còn lại. Hai NOZZLE đè nhau trên hình chiếu là chuyện bình
      // thường của phép chiếu (hai đầu nối lệch góc nhau vẫn chiếu về một chỗ)
      // — va chạm THẬT giữa chúng đã kiểm riêng bằng độ dài cung trên thành, nên
      // ở đây chỉ nhắc phải ghi chú "xoay vào mặt phẳng hình vẽ".
      var lan = [], nhac = [];
      for (var i2 = 0; i2 < chiem.length; i2++)
        for (var j2 = i2 + 1; j2 < chiem.length; j2++) {
          var a2 = chiem[i2], b2 = chiem[j2];
          if (!(a2.x2 - 1 < b2.x1 || b2.x2 - 1 < a2.x1 ||
                a2.y2 - 1 < b2.y1 || b2.y2 - 1 < a2.y1)) {
            if (a2.loai === 'noz' && b2.loai === 'noz') {
              var t3 = 'Trên hình chiếu, ' + a2.ten + ' và ' + b2.ten + ' chồng lên ' +
                       'nhau — ghi chú "xoay vào mặt phẳng hình vẽ" để thợ không ' +
                       'hiểu nhầm là hai lỗ cùng chỗ.';
              if (nhac.indexOf(t3) < 0) nhac.push(t3);
              continue;
            }
            var t2 = 'Đè nhau: ' + a2.ten + '  ×  ' + b2.ten;
            if (lan.indexOf(t2) < 0) lan.push(t2);
          }
        }
      return {
        svg: '<svg viewBox="0 0 ' + b.W + ' ' + b.H + '" width="100%" ' +
             'xmlns="http://www.w3.org/2000/svg" style="background:#fdfefe">' +
             out.join('') + '</svg>',
        lan: lan, nhac: nhac, tyLe: b.tyLe
      };
    }

    // ==================================================================== BẢNG
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

    function bangNozzle() {
      return bangHTML('Bảng nozzle — ' + tag,
        ['Mã', 'Dịch vụ', 'DN', 'Ø ngoài ống', 'Dày ống', 'Cao độ tâm (từ đáy)',
         'Góc quay', 'Độ nhô', 'Mặt bích', 'Lỗ khoét thành'],
        noz.map(function (n) {
          return [n.ma, n.dv, 'DN' + n.dn, 'Ø' + odDN(n.dn), dayOng(n.dn) + ' mm',
            n.tren ? 'Trên nắp' : '+' + n.cao + ' mm',
            n.tren ? '—' : n.goc + '°', n.nho + ' mm', n.chuan,
            'Ø' + lam(odDN(n.dn) + 2, 0) + ' mm'];
        }));
    }

    function bangVatLieu() {
      var tl = trongLuong();
      var ds = [
        ['Thân', vl.ten, 'Tấm ' + tThan + ' mm', 'Ø' + D + ' × H' + H, '1',
         lam(Math.PI * D * H * tThan / 1e9 * vl.ro, 0) + ' kg'],
        [dangDay === 'chom' ? 'Đáy chỏm cầu' : dangDay === 'con' ? 'Đáy côn' : 'Đáy phẳng',
         vl.ten, 'Tấm ' + tDay + ' mm', 'Ø' + D, '1', '—'],
        [kieu === 'cot' ? 'Nắp chỏm cầu' : 'Nắp', vl.ten, 'Tấm ' + tDay + ' mm',
         'Ø' + D, '1', '—'],
        [chan === 'vay' ? 'Váy đỡ' : 'Chân đế', vl.ten,
         chan === 'vay' ? 'Tấm ' + tThan + ' mm cuốn' : 'Thép hình',
         'Cao ' + caoChan + ' mm', chan === 'vay' ? '1' : '4',
         lam(tl.chan, 0) + ' kg']
      ];
      noz.forEach(function (n) {
        ds.push(['Nozzle ' + n.ma + ' (' + n.dv + ')', vl.ten,
          'Ống Ø' + odDN(n.dn) + '×' + dayOng(n.dn), 'Nhô ' + n.nho + ' mm', '1',
          lam(Math.PI * odDN(n.dn) * (n.nho + 60) * dayOng(n.dn) / 1e9 * vl.ro +
              nangBich(n.dn), 1) + ' kg']);
        ds.push(['Mặt bích ' + n.ma, vl.ten, n.chuan, 'DN' + n.dn, '1',
          nangBich(n.dn) + ' kg']);
        ds.push(['Gioăng + bộ bu lông ' + n.ma, 'EPDM / SS304', n.chuan, 'DN' + n.dn,
          '1 bộ', '—']);
      });
      return bangHTML('Bảng vật liệu chế tạo — ' + tag,
        ['Chi tiết', 'Vật liệu', 'Quy cách', 'Kích thước', 'SL', 'Khối lượng'], ds);
    }

    function bangKhaiTrien() {
      return bangHTML('Khai triển tôn — kích thước phôi để CẮT',
        ['Chi tiết', 'Kích thước phôi', 'SL', 'Ghi chú gia công'],
        khaiTrien().map(function (r) { return [r.ct, r.pt, r.sl, r.ghi]; }));
    }
    function bangMoiHan() {
      return bangHTML('Bảng mối hàn & kiểm tra',
        ['Ký hiệu', 'Vị trí', 'Kiểu mối hàn', 'Phương pháp / que', 'Kiểm tra'],
        moiHan().map(function (r) { return [r.ky, r.vt, r.kieuH, r.kt, r.ktr]; }));
    }
    function bangTrongLuong() {
      var t = trongLuong();
      return bangHTML('Khối lượng & tải trọng lên móng',
        ['Hạng mục', 'Khối lượng'],
        [['Vỏ (thân + đáy + nắp)', t.vo + ' kg'],
         ['Nozzle + mặt bích', t.nozzle + ' kg'],
         ['Chân / váy đỡ', t.chan + ' kg'],
         ['TỔNG KHỐI LƯỢNG CHAY', t.chay + ' kg'],
         ['Lưu chất khi vận hành', t.nuoc + ' kg'],
         ['TỔNG KHI VẬN HÀNH (tính móng)', t.vanHanh + ' kg'],
         ['TỔNG KHI THỬ THUỶ LỰC (đầy nước)', t.thuThuyLuc + ' kg']]);
    }
    function bangSon() {
      return '<h4 class="svws-bang-tieu">Xử lý bề mặt &amp; sơn phủ</h4><ul class="svws-ds">' +
        sonPhu().map(function (s) { return '<li>' + esc(s) + '</li>'; }).join('') + '</ul>';
    }
    function bangBen() {
      if (!ben) return '';
      return bangHTML('Kiểm tra bề dày theo áp lực',
        ['Thông số', 'Giá trị'],
        [['Áp suất tính toán', lam(ben.P, 3) + ' MPa' +
            (ap > 0 ? ' (áp thiết kế ' + ap + ' bar)'
                    : ' (cột nước ' + mucNuoc + ' mm, ρ ' + roLuu + ' kg/m³)')],
         ['Ứng suất cho phép', vl.S + ' MPa · hệ số mối hàn ' + E],
         ['Bề dày tính toán + ăn mòn', ben.tinh + ' mm (ăn mòn ' + anMon + ' mm)'],
         ['Bề dày tối thiểu theo xưởng', ben.toiThieu + ' mm'],
         ['BỀ DÀY YÊU CẦU', ben.canDung + ' mm'],
         ['Bề dày chọn dùng', tThan + ' mm' +
            (tThan >= ben.canDung ? ' — ĐẠT' : ' — KHÔNG ĐẠT')]]);
    }

    function bang() {
      return bangNozzle() + bangBen() + bangVatLieu() + bangKhaiTrien() +
             bangMoiHan() + bangTrongLuong() + bangSon();
    }

    // ================================================================== KIỂM
    function kiemTra() {
      var h = dungHinh();
      var loi = h.lan, canhBao = h.nhac.slice();
      // --- bề dày
      if (ben && tThan < ben.canDung) {
        loi.push(tag + ': thân dày ' + tThan + ' mm KHÔNG ĐỦ — cần ≥ ' + ben.canDung +
                 ' mm (tính toán ' + ben.tinh + ' mm, tối thiểu xưởng ' +
                 ben.toiThieu + ' mm).');
      }
      if (!tThan || !tDay) loi.push(tag + ': thiếu bề dày thân hoặc đáy.');
      // --- nozzle
      var ma = {};
      noz.forEach(function (n) {
        if (ma[n.ma]) loi.push(tag + ': trùng mã nozzle ' + n.ma);
        ma[n.ma] = 1;
        if (!n.tren && (n.cao < 0 || n.cao > H))
          loi.push(tag + ' / ' + n.ma + ': cao độ ' + n.cao + ' mm nằm NGOÀI thân ' +
                   '(0…' + H + ' mm) — không khoét được lỗ.');
        if (!n.tren && n.cao - odDN(n.dn) / 2 < 0)
          loi.push(tag + ' / ' + n.ma + ': mép dưới lỗ khoét thấp hơn đường hàn đáy.');
        if (odDN(n.dn) > D / 2)
          canhBao.push(tag + ' / ' + n.ma + ': lỗ Ø' + odDN(n.dn) + ' vượt 1/2 đường ' +
                       'kính thân — phải tính gia cường miệng lỗ riêng.');
        if (!n.dv) canhBao.push(tag + ' / ' + n.ma + ': chưa ghi dịch vụ.');
      });
      // --- nozzle đè nhau trên thành (khoảng cách theo cung + theo cao độ)
      for (var i = 0; i < noz.length; i++) {
        for (var j = i + 1; j < noz.length; j++) {
          var a = noz[i], b = noz[j];
          if (a.tren || b.tren) continue;
          var dCao = Math.abs(a.cao - b.cao);
          // Chênh góc quy về 0…180°, rồi đổi ra ĐỘ DÀI CUNG trên thành bồn.
          // (Trước đây viết (180 − dGoc) là ngược dấu: hai nozzle CÙNG một góc
          //  sẽ ra khoảng cách 180° tức xa nhất, đúng lúc chúng chồng lên nhau.)
          var dGoc = Math.abs(((a.goc - b.goc) % 360 + 540) % 360 - 180);
          var dCung = dGoc * Math.PI / 180 * (D / 2);
          var can = odDN(a.dn) / 2 + odDN(b.dn) / 2 + 2.5 * tThan + 25;  // + vành gia cường
          if (dCao < can && dCung < can) {
            loi.push(tag + ': nozzle ' + a.ma + ' và ' + b.ma + ' quá sát nhau (cách ' +
                     lam(Math.max(dCao, dCung), 0) + ' mm, cần ≥ ' + lam(can, 0) +
                     ' mm) — hai lỗ khoét chồng vùng gia cường, không hàn được.');
          }
        }
      }
      // --- tiện ích vận hành
      var coXa = noz.some(function (n) { return /xả|drain|đáy/i.test(n.dv) || n.cao <= 200; });
      if (!coXa) canhBao.push(tag + ': không có đường xả đáy — không vệ sinh được bồn.');
      if (D >= 1000 && !noz.some(function (n) { return /man|thăm|người/i.test(n.dv); }))
        canhBao.push(tag + ': đường kính ' + D + ' mm nhưng chưa có cửa thăm (manhole) — ' +
                     'người không vào vệ sinh / thay vật liệu lọc được.');
      if (mucNuoc >= H)
        canhBao.push(tag + ': mực nước thiết kế bằng chiều cao thân — không có khoảng ' +
                     'trống an toàn, nên chừa tối thiểu 150 mm và bố trí ống tràn.');
      if (laNhua(vatLieu) && ap > 0)
        canhBao.push(tag + ': vật liệu ' + vatLieu + ' chịu áp ' + ap + ' bar — phải có ' +
                     'chứng chỉ của nhà sản xuất, không tự chế tạo.');
      return { loi: loi, canhBao: canhBao, tyLe: dungHinh().tyLe,
               benThan: ben, trongLuong: trongLuong() };
    }

    return {
      ve: function () { return dungHinh().svg; },
      bang: bang,
      bangNozzle: bangNozzle, bangVatLieu: bangVatLieu, bangKhaiTrien: bangKhaiTrien,
      bangMoiHan: bangMoiHan, bangTrongLuong: bangTrongLuong, bangSon: bangSon,
      bangBen: bangBen,
      kiemTra: kiemTra, khaiTrien: khaiTrien, moiHan: moiHan,
      trongLuong: trongLuong, benThan: function () { return ben; },
      nozzle: function () { return noz.slice(); },
      thongSo: function () {
        return { tag: tag, ten: ten, kieu: kieu, d: D, h: H, dayThan: tThan,
                 dayDay: tDay, vatLieu: vatLieu, chan: chan, day: dangDay };
      }
    };
  }

  /** Ánh xạ type của SVWS3D sang kiểu chế tạo — để hai tab dùng chung khai báo. */
  function mapKieu(t) {
    t = String(t || '').toLowerCase();
    if (/tank|be|bon/.test(t)) return 'bon';
    if (/vessel|cot|filter|mixedbed|cartridge/.test(t)) return 'cot';
    if (/skid|frame|khung|roskid|edi/.test(t)) return 'khung';
    if (/panel|tu/.test(t)) return 'hop';
    return '';
  }

  /** Bộ nozzle mặc định khi đề bài chưa khai — đặt theo thông lệ chế tạo. */
  function nozMacDinh(kieu, D, H) {
    var dn = D >= 1500 ? 80 : D >= 900 ? 65 : 50;
    if (kieu === 'cot') {
      return [
        { ma: 'N1', dv: 'Nước vào', dn: dn, cao: H - 80, goc: 0, nho: 150, chuan: 'JIS 10K RF' },
        { ma: 'N2', dv: 'Nước ra', dn: dn, cao: 120, goc: 180, nho: 150, chuan: 'JIS 10K RF' },
        { ma: 'N3', dv: 'Rửa ngược ra', dn: dn, cao: H - 220, goc: 90, nho: 150, chuan: 'JIS 10K RF' },
        { ma: 'N4', dv: 'Xả đáy', dn: 40, cao: 80, goc: 270, nho: 130, chuan: 'JIS 10K RF' },
        // Cửa thăm đặt lệch 135° chứ không cùng góc với N1: vành gia cường của
        // lỗ DN400 rất rộng, cùng góc là hai lỗ khoét chồng vùng gia cường.
        { ma: 'M1', dv: 'Cửa thăm nạp vật liệu', dn: 400, cao: H - 350, goc: 135, nho: 120, chuan: 'JIS 10K RF' }
      ];
    }
    return [
      { ma: 'N1', dv: 'Nước vào', dn: dn, cao: H - 150, goc: 0, nho: 150, chuan: 'JIS 10K RF' },
      { ma: 'N2', dv: 'Nước ra', dn: dn, cao: 200, goc: 180, nho: 150, chuan: 'JIS 10K RF' },
      { ma: 'N3', dv: 'Ống tràn', dn: dn, cao: H - 100, goc: 90, nho: 150, chuan: 'JIS 10K RF' },
      { ma: 'N4', dv: 'Xả đáy', dn: 50, cao: 100, goc: 270, nho: 130, chuan: 'JIS 10K RF' },
      { ma: 'M1', dv: 'Cửa thăm', dn: 500, cao: H - 400, goc: 45, nho: 120, chuan: 'JIS 10K RF' }
    ];
  }

  var CSS = '.svws-bang{width:100%;border-collapse:collapse;font-size:12px;font-family:' +
    FONT + ';margin:6px 0 16px}' +
    '.svws-bang th{background:#0b2545;color:#fff;padding:6px 8px;text-align:left;' +
    'font-weight:600;border:1px solid #0b2545}' +
    '.svws-bang td{padding:5px 8px;border:1px solid #cfd8e3;vertical-align:top}' +
    '.svws-bang tbody tr:nth-child(even){background:#f4f8fb}' +
    '.svws-bang-tieu{margin:14px 0 4px;font:600 13px ' + FONT + ';color:#0b2545}' +
    '.svws-ds{margin:4px 0 14px 18px;font-size:12.5px;line-height:1.55}';

  global.SVWSCHE = {
    version: '1.0', to: to, VL: VL, traVL: traVL, odDN: odDN, dayOng: dayOng,
    mapKieu: mapKieu, CSS: CSS
  };
})(window);
