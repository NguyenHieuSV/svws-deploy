/*!
 * SVWSDIEN — bộ dựng LOGIC VẬN HÀNH & BẢN VẼ ĐIỆN chuẩn cho tool thiết kế SVWS
 * ===========================================================================
 * Mục tiêu: đủ để THI CÔNG TỦ ĐIỆN và LẬP TRÌNH PLC, không phải hình minh hoạ.
 *
 * Vì sao có thư viện này: bản vẽ điện là loại hình học AI làm sai nặng nhất —
 * mạch động lực phải thẳng cột, thang điều khiển phải đều nấc, đầu cốt phải
 * đánh số không trùng. AI gõ toạ độ mà không nhìn thấy kết quả nên nấc thang
 * đè nhau, dây không chạm ray, số đầu cốt trùng. Ở đây AI chỉ KHAI BÁO mạch;
 * thư viện tự đo, tự xếp, tự đánh số, và tự KIỂM.
 *
 * Ngoài phần vẽ, thư viện còn TỰ CHỌN THIẾT BỊ theo công suất: dòng định mức,
 * MCCB/MCB, khởi động từ, rơ-le nhiệt, tiết diện cáp — theo bảng tra sẵn.
 *
 * Dùng (4 bản vẽ + 3 bảng):
 *   var DL = SVWSDIEN.dongLuc({ma:'...', ten:'...', nguon:'3P+N 380/220VAC 50Hz'});
 *   DL.tai({tag:'P-101A', ten:'Bơm cấp', kW:3,   kieu:'DOL'});
 *   DL.tai({tag:'P-201',  ten:'Bơm RO',  kW:7.5, kieu:'VFD'});
 *   el.innerHTML = DL.ve();          bangMotor.innerHTML = DL.bangMotor();
 *
 *   var DK = SVWSDIEN.dieuKhien({ma:'...'});
 *   DK.mach({ten:'Cho phép chạy', pt:[{k:'estop',t:'ES-01'},{k:'nc',t:'F1'},
 *                                     {k:'cuon',t:'KA-01'}]});
 *   var IO = SVWSDIEN.plc({ma:'...', cpu:'S7-1200 CPU1214C'});
 *   IO.module({kieu:'DI', ten:'DI 14ch on-board', kenh:[{dc:'I0.0', tag:'ES-01',
 *              mo:'Nút dừng khẩn cấp', tin:'NC'}]});
 *   var TU = SVWSDIEN.tuDien({W:800, H:1200, D:300});
 *   TU.thiet({ten:'MCCB 100A', r:105, c:165});
 *   var LG = SVWSDIEN.logic({});
 *   LG.thietBi({tag:'P-101A', ten:'Bơm cấp', chay:'AUTO & LSL-101 = 1',
 *               dung:'LSH-101 = 1 hoặc 20 phút', khoa:'LSLL-101', bao:'Quá tải'});
 *   console.log(DL.kiemTra(), DK.kiemTra(), IO.kiemTra(), TU.kiemTra(), LG.kiemTra());
 */
(function (global) {
  'use strict';

  var NAVY = '#0b2545', INK = '#12263a', MO = '#33475b', XAM = '#6c757d';
  var DO = '#b3271e', LUC = '#1f7a4d', VANG = '#b8860b', TIM = '#6f4fa8';
  var FONT = 'IBM Plex Sans,Segoe UI,Arial,sans-serif';

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
  /* Đo bề rộng chữ. Không đo được thì không tránh được va chạm — đây là mấu
     chốt của cả ba thư viện vẽ: bản do AI tự gõ đặt nhãn ở khoảng lệch cố
     định nên nhãn dài là đè lên ký hiệu bên cạnh. */
  function rongChu(s, fs, dam) {
    return String(s || '').length * fs * (dam ? 0.56 : 0.52);
  }
  function so(v, mac_dinh) {
    v = parseFloat(v);
    return isFinite(v) ? v : mac_dinh;
  }
  /** Chọn giá trị nhỏ nhất trong bảng mà ≥ v; hết bảng thì trả phần tử cuối. */
  function chonTren(bang, v) {
    for (var i = 0; i < bang.length; i++) if (bang[i] >= v) return bang[i];
    return bang[bang.length - 1];
  }

  // ==========================================================================
  // BẢNG TRA THIẾT BỊ ĐIỆN  (cơ sở để tự chọn — sửa ở đây là đổi toàn hệ)
  // ==========================================================================
  // Cáp đồng cách điện PVC, đi trong ống/máng, 30 °C, 3 ruột mang tải (A).
  var DAY = [[1.5, 14], [2.5, 18], [4, 24], [6, 31], [10, 42], [16, 56], [25, 73],
             [35, 89], [50, 108], [70, 136], [95, 164], [120, 188], [150, 216],
             [185, 245], [240, 286], [300, 328]];
  // Nấc dòng định mức MCB/MCCB thông dụng (A).
  var NAC_CB = [6, 10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250,
                320, 400, 500, 630, 800];
  // Khởi động từ theo công suất AC-3 ở 400 V (kW).
  var NAC_KM = [4, 5.5, 7.5, 11, 15, 18.5, 22, 30, 37, 45, 55, 75, 90, 110, 132];

  /**
   * Tự chọn thiết bị bảo vệ & cáp cho một tải động cơ.
   * Trả về đủ số liệu để ĐẶT HÀNG và ĐẤU TỦ, không phải ước lượng cảm tính.
   */
  function tinhTai(kW, U, pha, kieu) {
    kW = so(kW, 0); U = so(U, 380);
    // Tải 1 pha lấy điện áp pha, không phải điện áp dây — quên chỗ này là
    // tính dòng thấp đi 1,7 lần rồi chọn thiếu cáp.
    if (pha === 1 && U >= 380) U = 220;
    var cos = 0.85, hs = 0.88;                       // cosφ và hiệu suất động cơ
    var I = pha === 1 ? kW * 1000 / (U * cos * hs)
                      : kW * 1000 / (1.732 * U * cos * hs);
    var vfd = kieu === 'VFD';
    // Biến tần: dòng vào ≈ dòng ra, nhưng chọn CB theo khuyến cáo hãng ~1,5·In.
    var cb = chonTren(NAC_CB, I * (vfd ? 1.5 : 1.25));
    var day = 2.5, i;
    for (i = 0; i < DAY.length; i++) {
      if (DAY[i][1] >= I * 1.25) { day = DAY[i][0]; break; }
      day = DAY[i][0];
    }
    // Cáp phải chịu được nấc CB, không chỉ chịu dòng tải — nếu không, CB nhảy
    // sau khi cáp đã cháy. Đây là lỗi hay gặp khi chọn tay.
    for (i = 0; i < DAY.length; i++) {
      if (DAY[i][0] >= day && DAY[i][1] >= cb * 0.8) { day = DAY[i][0]; break; }
    }
    var r = {
      kW: kW, U: U, pha: pha === 1 ? 1 : 3, kieu: kieu || 'DOL',
      I: Math.round(I * 10) / 10,
      cb: cb,
      cbTen: (cb <= 63 ? 'MCB ' : 'MCCB ') + cb + 'A ' + (pha === 1 ? '1P' : '3P'),
      day: day,
      capTen: (pha === 1 ? '2C+E ' : '4C+E ') + day + ' mm² Cu/PVC'
    };
    if (vfd) {
      r.km = '';                       // biến tần không cần khởi động từ + rơ-le nhiệt
      r.ol = '';
      r.vfd = 'Biến tần ' + (kW < 0.75 ? 0.75 : kW) + ' kW, 3P 380 V, có lọc EMC';
      r.capTen = 'Cáp có LƯỚI CHỐNG NHIỄU ' + (pha === 1 ? '2C+E ' : '4C+E ') +
                 day + ' mm² (bắt buộc cho biến tần)';
    } else {
      r.km = 'Khởi động từ AC-3 ' + chonTren(NAC_KM, kW) + ' kW, cuộn 220 VAC';
      r.ol = 'Rơ-le nhiệt ' + (Math.round(I * 0.75 * 10) / 10) + '–' +
             (Math.round(I * 1.15 * 10) / 10) + ' A (đặt ' +
             (Math.round(I * 1.05 * 10) / 10) + ' A)';
      r.vfd = '';
    }
    return r;
  }

  // ==========================================================================
  // Hộp vẽ dùng chung: đăng ký ô đã chiếm chỗ → kiemTra() bắt được chồng lấn
  // ==========================================================================
  function hopVe(W, H) {
    var out = [], chiem = [], loi = [];
    function themChiem(x1, y1, x2, y2, ten) {
      chiem.push({ x1: x1, y1: y1, x2: x2, y2: y2, ten: ten || '' });
    }
    function dung(a, b, ho) {
      ho = ho || 0;
      return !(a.x2 + ho < b.x1 || b.x2 + ho < a.x1 ||
               a.y2 + ho < b.y1 || b.y2 + ho < a.y1);
    }
    function ln(x1, y1, x2, y2, mau, w, net) {
      out.push('<line x1="' + x1 + '" y1="' + y1 + '" x2="' + x2 + '" y2="' + y2 +
        '" stroke="' + (mau || NAVY) + '" stroke-width="' + (w || 1.5) + '"' +
        (net ? ' stroke-dasharray="' + net + '"' : '') + ' />');
    }
    function hop(x, y, w, h, nen, mau, r) {
      out.push('<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h +
        '" rx="' + (r == null ? 2 : r) + '" fill="' + (nen || '#fff') +
        '" stroke="' + (mau || NAVY) + '" stroke-width="1.4"/>');
    }
    function chu(x, y, s, fs, mau, neo, dam, ghi) {
      fs = fs || 9; neo = neo || 'start';
      var w = rongChu(s, fs, dam);
      var dx = neo === 'middle' ? -w / 2 : neo === 'end' ? -w : 0;
      if (ghi !== false) themChiem(x + dx - 1, y - fs, x + dx + w + 1, y + 2,
                                   'chữ:' + s);
      out.push('<text x="' + x + '" y="' + y + '" font-size="' + fs + '" fill="' +
        (mau || INK) + '" text-anchor="' + neo + '"' + (dam ? ' font-weight="600"' : '') +
        ' font-family="' + FONT + '">' + esc(s) + '</text>');
    }
    /** Chữ tự xuống dòng trong bề rộng cho trước — chống nhãn dài tràn sang cột bên. */
    function chuGoi(x, y, s, fs, mau, rongMax, neo, dam) {
      var tu = String(s || '').split(/\s+/), dong = [], cur = '';
      tu.forEach(function (t) {
        var thu = cur ? cur + ' ' + t : t;
        if (rongChu(thu, fs, dam) > rongMax && cur) { dong.push(cur); cur = t; }
        else cur = thu;
      });
      if (cur) dong.push(cur);
      dong.forEach(function (d, i) { chu(x, y + i * (fs + 2.5), d, fs, mau, neo, dam); });
      return dong.length * (fs + 2.5);
    }
    function khung(tieu, phu) {
      var s = '<svg viewBox="0 0 ' + W + ' ' + H + '" width="100%" ' +
        'xmlns="http://www.w3.org/2000/svg" style="background:#fdfefe">' +
        '<rect width="' + W + '" height="' + H + '" fill="#fdfefe" stroke="' + NAVY + '"/>';
      if (tieu) s += '<text x="20" y="26" font-size="15" font-weight="700" fill="' +
        NAVY + '" font-family="' + FONT + '">' + esc(tieu) + '</text>';
      if (phu) s += '<text x="20" y="46" font-size="10.5" fill="' + MO +
        '" font-family="' + FONT + '">' + esc(phu) + '</text>';
      return s + out.join('') + '</svg>';
    }
    function chongLan() {
      var ds = [];
      for (var i = 0; i < chiem.length; i++)
        for (var j = i + 1; j < chiem.length; j++)
          if (dung(chiem[i], chiem[j], -1)) {
            var t = 'Đè nhau: ' + chiem[i].ten + '  ×  ' + chiem[j].ten;
            if (ds.indexOf(t) < 0) ds.push(t);
          }
      return ds;
    }
    return { out: out, chiem: chiem, loi: loi, themChiem: themChiem, ln: ln,
             hop: hop, chu: chu, chuGoi: chuGoi, khung: khung,
             chongLan: chongLan, W: function (v) { if (v) W = v; return W; },
             H: function (v) { if (v) H = v; return H; } };
  }

  // ==========================================================================
  // 1. SƠ ĐỒ MẠCH ĐỘNG LỰC
  // ==========================================================================
  function dongLuc(o) {
    o = o || {};
    var ds = [];                       // danh sách tải đã khai báo
    var api = {};

    api.tai = function (e) {
      e = e || {};
      var t = tinhTai(e.kW, e.U || o.U || 380, e.pha || 3, (e.kieu || 'DOL').toUpperCase());
      t.tag = e.tag || ('M-' + (ds.length + 1));
      t.ten = e.ten || '';
      t.ghi = e.ghi || '';
      t.duPhong = !!e.duPhong;
      ds.push(t);
      return api;
    };

    /** Tính bố cục TRƯỚC khi vẽ — bề rộng cột lấy theo nhãn dài nhất, không đoán. */
    function boCuc() {
      var rongNhan = 118;
      ds.forEach(function (t) {
        [t.cbTen, t.km || t.vfd, t.ol, t.capTen].forEach(function (s) {
          if (!s) return;
          // nhãn sẽ được gói 2 dòng, nên chỉ cần nửa bề rộng
          rongNhan = Math.max(rongNhan, Math.min(150, rongChu(s, 7.6) / 2));
        });
      });
      var cot = Math.max(168, rongNhan + 58);
      var W = Math.max(1080, 150 + ds.length * cot + 40);
      return { cot: cot, W: W, H: 640, x0: 150, rongNhan: rongNhan };
    }

    function dungHinh() {
      var b = boCuc(), g = hopVe(b.W, b.H);
      var yBus = 172, yCB = 258, yKM = 324, yOL = 386, yM = 476;
      var tongKW = 0, tongI = 0;
      ds.forEach(function (t) { tongKW += t.kW; tongI += t.I; });
      // dòng tính toán có hệ số đồng thời 0,8 — cả nhà máy không chạy cùng lúc
      var Itt = tongI * 0.8;
      var cbTong = chonTren(NAC_CB, Itt * 1.25);

      // ---- nguồn vào + MCCB tổng
      g.chu(24, 76, 'NGUỒN: ' + (o.nguon || '3P+N 380/220 VAC 50 Hz'), 10, INK, 'start', 1);
      g.ln(60, 84, 60, 108, NAVY, 2.2);
      kyCB(g, 60, 108, 'MCCB tổng ' + cbTong + 'A', '25 kA', b.rongNhan);
      g.ln(60, 130, 60, yBus, NAVY, 2.2);
      // ---- thanh cái 3 pha + PE
      ['L1', 'L2', 'L3'].forEach(function (p, i) {
        var y = yBus + i * 9;
        g.ln(46, y, b.W - 30, y, NAVY, 2.2);
        g.chu(30, y + 3, p, 8, MO, 'start', 0, false);
      });
      g.ln(46, yBus + 34, b.W - 30, yBus + 34, LUC, 1.6, '6 4');
      g.chu(30, yBus + 37, 'PE', 8, LUC, 'start', 0, false);
      g.themChiem(28, yBus - 8, b.W - 28, yBus + 40, 'thanh cái');

      // ---- từng lộ ra
      ds.forEach(function (t, i) {
        var x = b.x0 + i * b.cot;
        g.ln(x, yBus, x, yCB - 22, NAVY, 1.8);
        kyCB(g, x, yCB - 22, t.cbTen, '', b.rongNhan);
        g.ln(x, yCB, x, (t.kieu === 'VFD' ? yKM - 16 : yKM - 14), NAVY, 1.8);

        if (t.kieu === 'VFD') {
          g.hop(x - 30, yKM - 16, 60, 44, '#eef4fb', TIM, 3);
          g.chu(x, yKM + 12, 'VFD', 11, TIM, 'middle', 1, false);
          g.themChiem(x - 32, yKM - 18, x + 32, yKM + 30, 'VFD ' + t.tag);
          g.chuGoi(x + 36, yKM - 4, t.vfd, 7.6, MO, b.rongNhan);
          g.ln(x, yKM + 28, x, yM - 22, NAVY, 1.8);
        } else {
          kyKM(g, x, yKM - 14);
          g.chuGoi(x + 22, yKM - 4, t.km, 7.6, MO, b.rongNhan);
          g.ln(x, yKM + 14, x, yOL - 14, NAVY, 1.8);
          kyOL(g, x, yOL - 14);
          g.chuGoi(x + 22, yOL - 2, t.ol, 7.6, MO, b.rongNhan);
          g.ln(x, yOL + 14, x, yM - 22, NAVY, 1.8);
        }
        // cáp + động cơ
        g.chuGoi(x + 12, yM - 58, t.capTen, 7.6, LUC, b.rongNhan);
        g.out.push('<circle cx="' + x + '" cy="' + yM + '" r="22" fill="#fff" stroke="' +
          NAVY + '" stroke-width="1.8"/>');
        g.chu(x, yM - 2, 'M', 13, NAVY, 'middle', 1, false);
        g.chu(x, yM + 12, t.pha === 1 ? '1~' : '3~', 8, MO, 'middle', 0, false);
        g.themChiem(x - 24, yM - 24, x + 24, yM + 24, 'động cơ ' + t.tag);
        g.chu(x, yM + 44, t.tag, 10, NAVY, 'middle', 1);
        g.chuGoi(x - b.cot / 2 + 10, yM + 60, t.ten + (t.duPhong ? ' (dự phòng)' : ''),
                 8.4, INK, b.cot - 20);
        g.chu(x, yM + 92, t.kW + ' kW · ' + t.I + ' A', 8.4, MO, 'middle');
      });

      g.chu(24, b.H - 22, 'Tổng công suất lắp đặt ' + (Math.round(tongKW * 10) / 10) +
        ' kW · dòng tính toán ' + Math.round(Itt) + ' A (hệ số đồng thời 0,8) · ' +
        'MCCB tổng chọn ' + cbTong + ' A', 9, MO, 'start', 0, false);
      return { svg: g.khung('SƠ ĐỒ NGUYÊN LÝ MẠCH ĐỘNG LỰC — ' + (o.ma || ''), o.ten || ''),
               lan: g.chongLan() };
    }
    function ve() { return dungHinh().svg; }
    function veKiem() { return dungHinh().lan; }

    function bangMotor() {
      var h = '<table class="svws-bang"><thead><tr>' +
        ['TT', 'Tag', 'Tên thiết bị', 'kW', 'Pha', 'Kiểu KĐ', 'I (A)', 'CB',
         'Khởi động từ / Biến tần', 'Bảo vệ nhiệt', 'Cáp động lực']
        .map(function (t) { return '<th>' + t + '</th>'; }).join('') +
        '</tr></thead><tbody>';
      ds.forEach(function (t, i) {
        h += '<tr>' + [i + 1, t.tag, t.ten + (t.duPhong ? ' (dự phòng)' : ''), t.kW,
          t.pha + 'P', t.kieu, t.I, t.cbTen, t.km || t.vfd, t.ol || '—', t.capTen]
          .map(function (c) { return '<td>' + esc(c) + '</td>'; }).join('') + '</tr>';
      });
      return h + '</tbody></table>';
    }

    /* loi   = bản vẽ SAI, bắt buộc phải rỗng trước khi giao.
       canhBao = bản vẽ đúng nhưng LỰA CHỌN KỸ THUẬT cần cân nhắc lại. */
    function kiemTra() {
      var loi = veKiem(), canhBao = [];
      if (!ds.length) loi.push('Chưa khai báo tải nào cho mạch động lực.');
      var tag = {};
      ds.forEach(function (t) {
        if (tag[t.tag]) loi.push('Trùng tag động cơ: ' + t.tag);
        tag[t.tag] = 1;
        if (!t.kW) loi.push(t.tag + ': chưa có công suất kW — không chọn được CB và cáp.');
        if (t.kieu !== 'VFD' && t.kW >= 15)
          canhBao.push(t.tag + ' (' + t.kW + ' kW) khởi động trực tiếp DOL — dòng khởi ' +
                       'động ~6·In gây sụt áp lưới; nên dùng sao–tam giác hoặc biến tần.');
      });
      return { loi: loi, canhBao: canhBao, soTai: ds.length };
    }

    api.ve = ve; api.bangMotor = bangMotor; api.kiemTra = kiemTra;
    api.danhSach = function () { return ds.slice(); };
    return api;
  }

  // ký hiệu áp-tô-mát
  function kyCB(g, x, y, ten, phu, rongNhan) {
    g.hop(x - 11, y, 22, 22, '#fff', NAVY, 2);
    g.ln(x, y + 22, x + 9, y + 4, NAVY, 1.6);
    g.themChiem(x - 13, y - 2, x + 13, y + 24, 'CB ' + ten);
    g.chuGoi(x + 17, y + 10, ten + (phu ? ' · ' + phu : ''), 7.8, INK, rongNhan || 120);
  }
  // ký hiệu khởi động từ (contactor)
  function kyKM(g, x, y) {
    g.hop(x - 9, y, 18, 28, '#fff', NAVY, 2);
    g.out.push('<path d="M' + (x - 5) + ' ' + (y + 20) + ' q5 -9 10 -14" fill="none" stroke="' +
      NAVY + '" stroke-width="1.6"/>');
    g.themChiem(x - 11, y - 2, x + 11, y + 30, 'khởi động từ');
  }
  // ký hiệu rơ-le nhiệt
  function kyOL(g, x, y) {
    g.hop(x - 9, y, 18, 26, '#fff', DO, 2);
    g.ln(x - 5, y + 8, x + 5, y + 8, DO, 1.4);
    g.ln(x - 5, y + 17, x + 5, y + 17, DO, 1.4);
    g.themChiem(x - 11, y - 2, x + 11, y + 28, 'rơ-le nhiệt');
  }

  // ==========================================================================
  // 2. SƠ ĐỒ MẠCH ĐIỀU KHIỂN (thang — ladder)
  // ==========================================================================
  /* Phần tử nhận: no (tiếp điểm thường mở) · nc (thường đóng) · nut (nút nhấn) ·
     estop (nút dừng khẩn) · chon (công tắc AUTO/MAN) · cuon (cuộn dây rơ-le/
     khởi động từ) · den (đèn báo) · coi (còi) · tg (rơ-le thời gian) ·
     di (đầu vào PLC) · do (đầu ra PLC) */
  var RONG_PT = { no: 46, nc: 46, nut: 46, estop: 52, chon: 50, tg: 54,
                  di: 54, do: 54, cuon: 44, den: 34, coi: 34 };

  function dieuKhien(o) {
    o = o || {};
    var ds = [], api = {};

    api.mach = function (e) {
      e = e || {};
      ds.push({ ten: e.ten || '', pt: (e.pt || []).slice(), ghi: e.ghi || '' });
      return api;
    };

    function boCuc() {
      var xL = 76, canPhai = 0;
      ds.forEach(function (m) {
        var w = 0;
        m.pt.forEach(function (p) {
          var r = RONG_PT[p.k] || 46;
          w += Math.max(r, rongChu(p.t || '', 8, 1) + 8) + 26;
        });
        canPhai = Math.max(canPhai, w);
      });
      var xR = xL + Math.max(560, canPhai + 40);
      var W = xR + 210;                       // chừa cột tham chiếu chéo bên phải
      var buoc = 86;                          // đủ chỗ cho TÊN NẤC + nhãn phần tử
      var H = 108 + ds.length * buoc + 46;
      return { xL: xL, xR: xR, W: W, H: H, buoc: buoc };
    }

    /** Bảng tham chiếu chéo: cuộn dây nào được dùng lại ở những nấc nào. */
    function thamChieu() {
      var cuon = {}, dung = {};
      ds.forEach(function (m, i) {
        m.pt.forEach(function (p) {
          if (!p.t) return;
          var ten = String(p.t).split(' ')[0];
          if (p.k === 'cuon') cuon[ten] = i + 1;
          else if (p.k === 'no' || p.k === 'nc') {
            (dung[ten] = dung[ten] || []).push(i + 1);
          }
        });
      });
      return { cuon: cuon, dung: dung };
    }

    function dungHinh() {
      var b = boCuc(), g = hopVe(b.W, b.H), tc = thamChieu();
      var y0 = 100;
      // hai ray dọc
      g.ln(b.xL, 84, b.xL, b.H - 30, NAVY, 2.4);
      g.ln(b.xR, 84, b.xR, b.H - 30, NAVY, 2.4);
      g.chu(b.xL - 6, 76, o.duong || 'L (+24 VDC)', 9, MO, 'start', 1, false);
      g.chu(b.xR - 6, 76, o.trung || 'N (0 V)', 9, MO, 'end', 1, false);
      g.chu(b.xR + 14, 76, 'Tham chiếu chéo', 8.6, XAM, 'start', 1, false);

      ds.forEach(function (m, i) {
        var y = y0 + i * b.buoc, nac = i + 1;
        g.chu(b.xL - 14, y + 4, String(nac), 10, NAVY, 'end', 1, false);
        // Tên nấc nằm CAO HƠN nhãn phần tử một tầng — hai loại chữ này cùng
        // trải theo phương ngang nên chỉ tách được bằng chiều đứng.
        if (m.ten) g.chu(b.xL + 4, y - 34, m.ten, 8.6, MO, 'start', 1);

        // xếp phần tử: tiếp điểm chạy từ trái, cuộn dây/đèn ép sát ray phải
        var trai = [], phai = [];
        m.pt.forEach(function (p) {
          (p.k === 'cuon' || p.k === 'den' || p.k === 'coi') ? phai.push(p) : trai.push(p);
        });
        var x = b.xL, day = 1;
        trai.forEach(function (p) {
          var w = Math.max(RONG_PT[p.k] || 46, rongChu(p.t || '', 8, 1) + 8);
          g.ln(x, y, x + 13, y, NAVY, 1.6);
          g.chu(x + 4, y - 7, String(nac * 10 + day), 7, XAM, 'start', 0, false);
          day++;
          veP(g, p, x + 13, y, w);
          x += w + 26;
        });
        var xC = b.xR - (phai.length ? 56 : 0);
        g.ln(x, y, xC, y, NAVY, 1.6);
        phai.forEach(function (p, k) {
          veP(g, p, b.xR - 52, y + k * 0, 44);
          g.ln(b.xR - 8, y, b.xR, y, NAVY, 1.6);
        });
        if (!phai.length) g.ln(x, y, b.xR, y, NAVY, 1.6);

        // tham chiếu chéo bên phải
        var t = '';
        m.pt.forEach(function (p) {
          if (p.k !== 'cuon' || !p.t) return;
          var ten = String(p.t).split(' ')[0], d = tc.dung[ten];
          t = d && d.length ? ten + ' → nấc ' + d.join(', ') : ten + ' → (chưa dùng)';
        });
        if (t) g.chu(b.xR + 14, y + 4, t, 8, XAM, 'start');
        if (m.ghi) g.chu(b.xR + 14, y + 16, m.ghi, 7.6, XAM, 'start');
      });
      return { svg: g.khung('SƠ ĐỒ MẠCH ĐIỀU KHIỂN — ' + (o.ma || ''), o.ten || ''),
               lan: g.chongLan() };
    }
    function ve() { return dungHinh().svg; }

    function kiemTra() {
      var loi = dungHinh().lan, tc = thamChieu();
      if (!ds.length) loi.push('Chưa khai báo nấc thang nào cho mạch điều khiển.');
      var coES = false;
      ds.forEach(function (m, k) {
        if (!m.pt.length) loi.push('Nấc ' + (k + 1) + ' rỗng.');
        var coRa = false;
        m.pt.forEach(function (p) {
          if (p.k === 'estop') coES = true;
          if (p.k === 'cuon' || p.k === 'den' || p.k === 'coi') coRa = true;
        });
        if (!coRa) loi.push('Nấc ' + (k + 1) + ' (' + (m.ten || '?') +
                            ') không có đầu ra — thang hở, mạch không có tác dụng.');
      });
      if (!coES) loi.push('Toàn mạch KHÔNG có nút dừng khẩn cấp (E-Stop) — ' +
                          'không được phép đưa vào thi công.');
      // Cuộn không có tiếp điểm nào trong thang KHÔNG hẳn là sai — nó có thể
      // kéo thẳng khởi động từ bên mạch động lực. Chỉ nhắc, không chặn.
      var canhBao = [];
      for (var ten in tc.cuon) {
        if (!tc.dung[ten]) canhBao.push('Cuộn ' + ten + ' không có tiếp điểm nào trong ' +
          'thang — kiểm tra: nó kéo khởi động từ bên động lực, hay bị bỏ quên?');
      }
      return { loi: loi, canhBao: canhBao, soNac: ds.length };
    }

    /** Vẽ một phần tử; mọi ký hiệu tự khai bề rộng thật để con trỏ nhảy đúng. */
    function veP(g, p, x, y, w) {
      var t = p.t || '';
      switch (p.k) {
        case 'no':
          g.ln(x, y, x + 8, y, NAVY, 1.6); g.ln(x + w - 8, y, x + w, y, NAVY, 1.6);
          g.ln(x + 8, y - 9, x + 8, y + 9, NAVY, 1.8);
          g.ln(x + w - 8, y - 9, x + w - 8, y + 9, NAVY, 1.8);
          break;
        case 'nc':
          g.ln(x, y, x + 8, y, NAVY, 1.6); g.ln(x + w - 8, y, x + w, y, NAVY, 1.6);
          g.ln(x + 8, y - 9, x + 8, y + 9, NAVY, 1.8);
          g.ln(x + w - 8, y - 9, x + w - 8, y + 9, NAVY, 1.8);
          g.ln(x + 4, y + 9, x + w - 4, y - 9, NAVY, 1.5);
          break;
        case 'nut':
          g.ln(x, y, x + 8, y, NAVY, 1.6); g.ln(x + w - 8, y, x + w, y, NAVY, 1.6);
          g.ln(x + 8, y - 9, x + 8, y + 9, NAVY, 1.8);
          g.ln(x + w - 8, y - 9, x + w - 8, y + 9, NAVY, 1.8);
          g.ln(x + w / 2, y - 9, x + w / 2, y - 17, NAVY, 1.4);
          g.ln(x + w / 2 - 6, y - 17, x + w / 2 + 6, y - 17, NAVY, 1.8);
          break;
        case 'estop':
          g.out.push('<circle cx="' + (x + w / 2) + '" cy="' + y + '" r="11" fill="#fdecea" stroke="' +
            DO + '" stroke-width="2"/>');
          g.ln(x, y, x + w / 2 - 11, y, NAVY, 1.6);
          g.ln(x + w / 2 + 11, y, x + w, y, NAVY, 1.6);
          g.ln(x + w / 2 - 6, y - 6, x + w / 2 + 6, y + 6, DO, 1.8);
          break;
        case 'chon':
          g.ln(x, y, x + 10, y, NAVY, 1.6); g.ln(x + w - 10, y, x + w, y, NAVY, 1.6);
          g.ln(x + 10, y, x + w - 12, y - 9, NAVY, 1.8);
          g.out.push('<circle cx="' + (x + 10) + '" cy="' + y + '" r="2.6" fill="' + NAVY + '"/>');
          g.out.push('<circle cx="' + (x + w - 10) + '" cy="' + y + '" r="2.6" fill="' + NAVY + '"/>');
          break;
        case 'tg':
          g.hop(x + 6, y - 12, w - 12, 24, '#fdf6e3', VANG, 2);
          g.chu(x + w / 2, y + 4, 'T', 11, VANG, 'middle', 1, false);
          g.ln(x, y, x + 6, y, NAVY, 1.6); g.ln(x + w - 6, y, x + w, y, NAVY, 1.6);
          break;
        case 'di': case 'do':
          g.hop(x + 4, y - 12, w - 8, 24, '#eef4fb', TIM, 2);
          g.chu(x + w / 2, y + 4, p.k === 'di' ? 'DI' : 'DO', 9.5, TIM, 'middle', 1, false);
          g.ln(x, y, x + 4, y, NAVY, 1.6); g.ln(x + w - 4, y, x + w, y, NAVY, 1.6);
          break;
        case 'cuon':
          g.out.push('<circle cx="' + (x + 22) + '" cy="' + y + '" r="12" fill="#fff" stroke="' +
            NAVY + '" stroke-width="1.8"/>');
          g.ln(x, y, x + 10, y, NAVY, 1.6);
          break;
        case 'den':
          g.out.push('<circle cx="' + (x + 22) + '" cy="' + y + '" r="11" fill="#fdf6e3" stroke="' +
            VANG + '" stroke-width="1.8"/>');
          g.ln(x + 15, y - 7, x + 29, y + 7, VANG, 1.3);
          g.ln(x + 29, y - 7, x + 15, y + 7, VANG, 1.3);
          g.ln(x, y, x + 11, y, NAVY, 1.6);
          break;
        case 'coi':
          g.out.push('<path d="M' + (x + 12) + ' ' + (y - 10) + ' L' + (x + 12) + ' ' +
            (y + 10) + ' A10 10 0 0 0 ' + (x + 12) + ' ' + (y - 10) + ' Z" fill="#fdecea" stroke="' +
            DO + '" stroke-width="1.6"/>');
          g.ln(x, y, x + 12, y, NAVY, 1.6);
          break;
        default:
          g.ln(x, y, x + w, y, NAVY, 1.6);
      }
      g.themChiem(x - 2, y - 14, x + w + 2, y + 14, (p.k || '') + ' ' + t);
      if (t) g.chu(x + w / 2, y - 16, t, 8, INK, 'middle', 1);
    }

    api.ve = ve; api.kiemTra = kiemTra; api.thamChieu = thamChieu;
    return api;
  }

  // ==========================================================================
  // 3. SƠ ĐỒ ĐẤU NỐI PLC (I/O) + BẢNG I/O
  // ==========================================================================
  function plc(o) {
    o = o || {};
    var mods = [], api = {};
    var MAU_KIEU = { DI: TIM, DO: LUC, AI: VANG, AO: DO };

    api.module = function (e) {
      e = e || {};
      mods.push({ kieu: (e.kieu || 'DI').toUpperCase(), ten: e.ten || '',
                  kenh: (e.kenh || []).slice() });
      return api;
    };

    function boCuc() {
      var CAO_D = 21, cot = [], y = 92, ci = 0, x = 60;
      var Hmax = 1180;
      mods.forEach(function (m) {
        var h = 34 + Math.max(1, m.kenh.length) * CAO_D + 10;
        if (y + h > Hmax && y > 92) { ci++; y = 92; }
        m._x = 60 + ci * 470; m._y = y; m._h = h; m._cot = ci;
        y += h + 26;
      });
      var soCot = mods.length ? mods[mods.length - 1]._cot + 1 : 1;
      var caoNhat = 0;
      mods.forEach(function (m) { caoNhat = Math.max(caoNhat, m._y + m._h); });
      return { W: Math.max(1000, 60 + soCot * 470 + 20), H: caoNhat + 60, caoD: CAO_D };
    }

    function dungHinh() {
      var b = boCuc(), g = hopVe(b.W, b.H);
      g.chu(24, 70, 'CPU: ' + (o.cpu || 'PLC (theo lựa chọn)') +
        (o.mang ? ' · Truyền thông: ' + o.mang : ''), 10, INK, 'start', 1, false);
      mods.forEach(function (m) {
        var mau = MAU_KIEU[m.kieu] || NAVY, w = 300;
        g.hop(m._x, m._y, w, m._h, '#fff', mau, 3);
        g.out.push('<rect x="' + m._x + '" y="' + m._y + '" width="' + w +
          '" height="24" rx="3" fill="' + mau + '" opacity="0.14"/>');
        g.chu(m._x + 10, m._y + 16, m.kieu + ' — ' + m.ten, 9.5, mau, 'start', 1, false);
        g.themChiem(m._x - 2, m._y - 2, m._x + w + 2, m._y + m._h + 2,
                    'module ' + m.kieu + ' ' + m.ten);
        m.kenh.forEach(function (k, i) {
          var y = m._y + 34 + i * b.caoD + 13;
          g.out.push('<circle cx="' + (m._x + 18) + '" cy="' + (y - 4) + '" r="4.6" fill="#fff" stroke="' +
            mau + '" stroke-width="1.3"/>');
          g.chu(m._x + 30, y, k.dc || ('CH' + i), 8.4, INK, 'start', 1, false);
          g.chu(m._x + 84, y, k.tag || '', 8.4, NAVY, 'start', 1, false);
          g.ln(m._x + w, y - 4, m._x + w + 22, y - 4, XAM, 1, '3 3');
          g.chu(m._x + w + 26, y, (k.mo || '') + (k.tin ? '  [' + k.tin + ']' : ''),
                7.8, MO, 'start', 0, false);
        });
      });
      return { svg: g.khung('SƠ ĐỒ ĐẤU NỐI PLC — ' + (o.ma || ''), o.ten || ''),
               lan: g.chongLan() };
    }
    function ve() { return dungHinh().svg; }

    function bangIO() {
      var h = '<table class="svws-bang"><thead><tr>' +
        ['TT', 'Địa chỉ', 'Kiểu', 'Tag hiện trường', 'Mô tả', 'Tín hiệu', 'Đầu cốt']
        .map(function (t) { return '<th>' + t + '</th>'; }).join('') + '</tr></thead><tbody>';
      var n = 0;
      mods.forEach(function (m) {
        m.kenh.forEach(function (k) {
          n++;
          h += '<tr>' + [n, k.dc || '', m.kieu, k.tag || '', k.mo || '',
            k.tin || (m.kieu === 'AI' || m.kieu === 'AO' ? '4–20 mA' : '24 VDC'),
            k.cot || ('X' + (n < 10 ? '0' : '') + n)]
            .map(function (c) { return '<td>' + esc(c) + '</td>'; }).join('') + '</tr>';
        });
      });
      return h + '</tbody></table>';
    }

    function kiemTra() {
      var loi = dungHinh().lan, dc = {}, tag = {}, dem = { DI: 0, DO: 0, AI: 0, AO: 0 };
      mods.forEach(function (m) {
        dem[m.kieu] = (dem[m.kieu] || 0) + m.kenh.length;
        m.kenh.forEach(function (k) {
          if (!k.dc) loi.push('Kênh của ' + m.ten + ' thiếu địa chỉ PLC.');
          else if (dc[k.dc]) loi.push('Trùng địa chỉ PLC: ' + k.dc);
          else dc[k.dc] = 1;
          // Một thiết bị được phép có nhiều tín hiệu KHÁC LOẠI (biến tần vừa
          // nhận lệnh chạy DO vừa nhận đặt tần số AO) — chỉ trùng trong cùng
          // một loại tín hiệu mới là đấu nhầm.
          if (k.tag) {
            var kh = k.tag + '|' + m.kieu;
            if (tag[kh]) loi.push('Trùng tag ' + k.tag + ' trong cùng nhóm ' + m.kieu);
            tag[kh] = 1;
          }
        });
      });
      if (!dem.DI) loi.push('Không có đầu vào số (DI) — PLC không nhận được tín hiệu nào.');
      if (!dem.DO) loi.push('Không có đầu ra số (DO) — PLC không điều khiển được gì.');
      // dự phòng 20 % là thông lệ khi đặt hàng module
      ['DI', 'DO', 'AI', 'AO'].forEach(function (k) {
        if (dem[k]) {
          var duPhong = Math.ceil(dem[k] * 0.2);
          if (duPhong < 1) duPhong = 1;
          loi.push('· Gợi ý: ' + k + ' đang dùng ' + dem[k] + ' kênh — đặt thêm ' +
                   duPhong + ' kênh dự phòng khi mua module.');
        }
      });
      return { loi: loi.filter(function (t) { return t.charAt(0) !== '·'; }),
               canhBao: loi.filter(function (t) { return t.charAt(0) === '·'; }),
               dem: dem };
    }

    api.ve = ve; api.bangIO = bangIO; api.kiemTra = kiemTra;
    return api;
  }

  // ==========================================================================
  // 4. BỐ TRÍ THIẾT BỊ TRONG TỦ (mặt trước, tỷ lệ thật)
  // ==========================================================================
  function tuDien(o) {
    o = o || {};
    var Wt = so(o.W, 800), Ht = so(o.H, 1200), Dt = so(o.D, 300);
    var ds = [], api = {};
    var LE = so(o.le, 80);           // lề trong tủ (mm)
    var KHE = so(o.kheRay, 60);      // máng đi dây giữa hai ray (mm)

    api.thiet = function (e) {
      e = e || {};
      ds.push({ ten: e.ten || '', r: so(e.r, 18), c: so(e.c, 90), nhiet: so(e.nhiet, 0) });
      return api;
    };

    /** Xếp thiết bị lên các ray DIN, tự xuống ray khi hết chỗ.
     *  Cao độ mỗi ray tính theo THIẾT BỊ CAO NHẤT của ray trên nó — dùng bước
     *  cố định là biến tần cao 300 mm sẽ đè xuống hàng dưới. */
    function xep() {
      var rong = Wt - 2 * LE, ray = [], cur = [], w = 0, cao = 0;
      ds.forEach(function (d) {
        if (w + d.r > rong && cur.length) {
          ray.push({ dt: cur, w: w, cao: cao }); cur = []; w = 0; cao = 0;
        }
        cur.push(d); w += d.r + 6; cao = Math.max(cao, d.c);
      });
      if (cur.length) ray.push({ dt: cur, w: w, cao: cao });
      var y = LE;
      ray.forEach(function (r) { r.y = y; y += r.cao + KHE; });
      return { ray: ray, cao: y - KHE };
    }

    function dungHinh() {
      var xx = xep(), ray = xx.ray;
      var sc = Math.min(1, 620 / Ht);                 // mm → px
      var W = Math.round(Wt * sc) + 360, H = Math.round(Ht * sc) + 130;
      var g = hopVe(W, H);
      var x0 = 40, y0 = 76;
      function mx(v) { return x0 + v * sc; }
      function my(v) { return y0 + v * sc; }

      g.hop(x0, y0, Wt * sc, Ht * sc, '#f7fafc', NAVY, 2);
      g.out.push('<rect x="' + mx(LE / 2) + '" y="' + my(LE / 2) + '" width="' +
        ((Wt - LE) * sc) + '" height="' + ((Ht - LE) * sc) +
        '" fill="none" stroke="' + XAM + '" stroke-width="0.8" stroke-dasharray="4 4"/>');

      ray.forEach(function (r, i) {
        var yy = r.y, yRay = yy + Math.min(45, r.cao * 0.45);
        g.ln(mx(LE), my(yRay), mx(Wt - LE), my(yRay), XAM, 2.4);
        g.chu(mx(LE) - 8, my(yRay + 4), 'R' + (i + 1), 8, XAM, 'end', 0, false);
        var x = LE;
        r.dt.forEach(function (d) {
          g.out.push('<rect x="' + mx(x) + '" y="' + my(yy) + '" width="' + (d.r * sc) +
            '" height="' + (d.c * sc) + '" fill="#e8eef6" stroke="' + NAVY +
            '" stroke-width="1"/>');
          // đăng ký ô chiếm chỗ để kiemTra() nhìn thấy được thiết bị đè nhau
          g.themChiem(mx(x), my(yy), mx(x + d.r), my(yy + d.c), d.ten);
          x += d.r + 6;
        });
        // chú thích ray đặt bên phải tủ, không đè lên thiết bị
        var ten = r.dt.map(function (d) { return d.ten; }).join(' · ');
        g.chuGoi(mx(Wt) + 16, my(yy + 22), 'R' + (i + 1) + ': ' + ten, 8, INK, 300);
      });

      // cầu đấu dưới cùng
      var yC = Math.max(xx.cao + 40, Ht - 150);
      g.out.push('<rect x="' + mx(LE) + '" y="' + my(yC) + '" width="' + ((Wt - 2 * LE) * sc) +
        '" height="' + (40 * sc) + '" fill="#fdf6e3" stroke="' + VANG + '" stroke-width="1.2"/>');
      g.chu(mx(Wt / 2), my(yC + 26), 'CẦU ĐẤU / TERMINAL', 8.4, VANG, 'middle', 1, false);

      g.chu(24, H - 18, 'Tủ ' + Wt + ' × ' + Ht + ' × ' + Dt + ' mm · ' + ray.length +
        ' ray DIN · ' + ds.length + ' thiết bị · tỷ lệ vẽ 1:' +
        Math.round(1 / sc * 10) / 10, 9, MO, 'start', 0, false);
      return { svg: g.khung('BỐ TRÍ THIẾT BỊ TRONG TỦ — ' + (o.ma || ''),
                            o.ten || 'Mặt trước, đã tháo cánh'),
               lan: g.chongLan() };
    }
    function ve() { return dungHinh().svg; }

    function kiemTra() {
      var loi = dungHinh().lan, canhBao = [], xx = xep(), ray = xx.ray;
      var canCao = xx.cao + 150;                    // + cầu đấu và máng dưới
      if (canCao > Ht) {
        loi.push('Tủ cao ' + Ht + ' mm KHÔNG đủ chỗ: cần ' + Math.ceil(canCao) +
                 ' mm cho ' + ray.length + ' ray DIN + cầu đấu. Tăng chiều cao tủ ' +
                 'hoặc chuyển sang tủ đôi.');
      }
      var nhiet = 0;
      ds.forEach(function (d) { nhiet += d.nhiet; });
      if (nhiet > 0) {
        // Diện tích toả nhiệt tủ kim loại đặt tựa tường ≈ 1,8·(W·H) + 1,4·(W·D)
        var A = (1.8 * Wt * Ht + 1.4 * Wt * Dt) / 1e6;   // m²
        var dT = nhiet / (5.5 * A);                       // k ≈ 5,5 W/m²K
        if (dT > 15) canhBao.push('Nhiệt trong tủ ' + Math.round(nhiet) + ' W làm nóng ' +
          'thêm ~' + Math.round(dT) + ' °C so với môi trường — vượt 15 °C. Cần quạt hút ' +
          'có lọc bụi (' + Math.ceil(nhiet / 8) + ' m³/h) hoặc máy lạnh tủ ' +
          Math.ceil(nhiet / 100) * 100 + ' W.');
      }
      if (!ds.length) loi.push('Chưa khai báo thiết bị nào trong tủ.');
      return { loi: loi, canhBao: canhBao, soRay: ray.length, soThietBi: ds.length };
    }

    api.ve = ve; api.kiemTra = kiemTra; api.xep = xep;
    return api;
  }

  // ==========================================================================
  // 5. BẢNG LOGIC VẬN HÀNH + MA TRẬN KHOÁ LIÊN ĐỘNG
  // ==========================================================================
  function logic(o) {
    o = o || {};
    var ds = [], buoc = [], bao = [], api = {};

    api.thietBi = function (e) {
      e = e || {};
      ds.push({ tag: e.tag || '', ten: e.ten || '', che: e.che || 'AUTO / MAN',
                chay: e.chay || '', dung: e.dung || '', khoa: e.khoa || '',
                bao: e.bao || '', ghi: e.ghi || '' });
      return api;
    };
    /** Một bước trong trình tự khởi động / dừng. */
    api.trinhTu = function (e) {
      e = e || {};
      buoc.push({ b: e.b || (buoc.length + 1), viec: e.viec || '',
                  dk: e.dk || '', t: e.t || '', loi: e.loi || '' });
      return api;
    };
    api.baoDong = function (e) {
      e = e || {};
      bao.push({ ma: e.ma || '', mo: e.mo || '', muc: e.muc || 'Cảnh báo',
                 nguong: e.nguong || '', xuLy: e.xuLy || '', tacDong: e.tacDong || '' });
      return api;
    };

    function bang(tieu, cot, dong) {
      var h = '<h4 class="svws-bang-tieu">' + esc(tieu) + '</h4>' +
        '<table class="svws-bang"><thead><tr>' +
        cot.map(function (t) { return '<th>' + esc(t) + '</th>'; }).join('') +
        '</tr></thead><tbody>';
      dong.forEach(function (r) {
        h += '<tr>' + r.map(function (c) { return '<td>' + esc(c) + '</td>'; }).join('') + '</tr>';
      });
      return h + '</tbody></table>';
    }

    function bangDieuKhien() {
      return bang('Bảng logic điều khiển thiết bị',
        ['Tag', 'Thiết bị', 'Chế độ', 'Điều kiện CHẠY', 'Điều kiện DỪNG',
         'Khoá liên động (cấm chạy)', 'Báo động', 'Ghi chú'],
        ds.map(function (d) {
          return [d.tag, d.ten, d.che, d.chay, d.dung, d.khoa, d.bao, d.ghi];
        }));
    }
    function bangTrinhTu() {
      return bang('Trình tự khởi động / dừng',
        ['Bước', 'Thao tác', 'Điều kiện chuyển bước', 'Thời gian', 'Xử lý khi lỗi'],
        buoc.map(function (b) { return [b.b, b.viec, b.dk, b.t, b.loi]; }));
    }
    function bangBaoDong() {
      return bang('Danh mục báo động',
        ['Mã', 'Mô tả', 'Mức', 'Ngưỡng / điều kiện', 'Tác động của hệ thống', 'Xử lý'],
        bao.map(function (b) { return [b.ma, b.mo, b.muc, b.nguong, b.tacDong, b.xuLy]; }));
    }

    /** Ma trận khoá liên động: hàng = thiết bị, cột = điều kiện cấm chạy. */
    function maTran() {
      var dk = [];
      ds.forEach(function (d) {
        String(d.khoa || '').split(/\s*[;,]\s*|\s+hoặc\s+/).forEach(function (t) {
          t = t.trim();
          if (t && dk.indexOf(t) < 0) dk.push(t);
        });
      });
      if (!dk.length) return '<div class="svws-bang-tieu">Chưa khai báo khoá liên động.</div>';
      var h = '<h4 class="svws-bang-tieu">Ma trận khoá liên động (✕ = cấm chạy)</h4>' +
        '<table class="svws-bang"><thead><tr><th>Thiết bị</th>' +
        dk.map(function (t) { return '<th>' + esc(t) + '</th>'; }).join('') +
        '</tr></thead><tbody>';
      ds.forEach(function (d) {
        h += '<tr><td>' + esc(d.tag + ' ' + d.ten) + '</td>' +
          dk.map(function (t) {
            return '<td style="text-align:center">' +
              (String(d.khoa || '').indexOf(t) >= 0 ? '✕' : '') + '</td>';
          }).join('') + '</tr>';
      });
      return h + '</tbody></table>';
    }

    function kiemTra() {
      var loi = [];
      if (!ds.length) loi.push('Chưa khai báo thiết bị nào trong bảng logic.');
      ds.forEach(function (d) {
        if (!d.chay) loi.push(d.tag + ': thiếu ĐIỀU KIỆN CHẠY — người lập trình ' +
                              'không biết khi nào được phép cấp lệnh.');
        if (!d.dung) loi.push(d.tag + ': thiếu ĐIỀU KIỆN DỪNG.');
        if (!d.khoa) loi.push(d.tag + ': thiếu KHOÁ LIÊN ĐỘNG — thiết bị có thể chạy ' +
                              'khi không đủ điều kiện an toàn (bơm chạy cạn, khuấy ' +
                              'chạy khi bể rỗng…).');
      });
      if (!buoc.length) loi.push('Chưa có trình tự khởi động / dừng.');
      if (!bao.length) loi.push('Chưa có danh mục báo động.');
      var coES = bao.some(function (b) {
        return /khẩn|e-?stop|emergency/i.test(b.ma + ' ' + b.mo);
      });
      if (!coES) loi.push('Danh mục báo động không có mục DỪNG KHẨN CẤP.');
      return { loi: loi, soThietBi: ds.length, soBuoc: buoc.length, soBao: bao.length };
    }

    api.bangDieuKhien = bangDieuKhien;
    api.bangTrinhTu = bangTrinhTu;
    api.bangBaoDong = bangBaoDong;
    api.maTran = maTran;
    api.tatCa = function () {
      return bangDieuKhien() + maTran() + bangTrinhTu() + bangBaoDong();
    };
    api.kiemTra = kiemTra;
    return api;
  }

  /** CSS gợi ý cho các bảng — nhúng một lần vào tool. */
  var CSS = '.svws-bang{width:100%;border-collapse:collapse;font-size:12px;' +
    'font-family:' + FONT + ';margin:6px 0 16px}' +
    '.svws-bang th{background:#0b2545;color:#fff;padding:6px 8px;text-align:left;' +
    'font-weight:600;border:1px solid #0b2545}' +
    '.svws-bang td{padding:5px 8px;border:1px solid #cfd8e3;vertical-align:top}' +
    '.svws-bang tbody tr:nth-child(even){background:#f4f8fb}' +
    '.svws-bang-tieu{margin:14px 0 4px;font:600 13px ' + FONT + ';color:#0b2545}';

  global.SVWSDIEN = {
    version: '1.0',
    dongLuc: dongLuc, dieuKhien: dieuKhien, plc: plc, tuDien: tuDien, logic: logic,
    tinhTai: tinhTai, CSS: CSS,
    BANG: { DAY: DAY, NAC_CB: NAC_CB, NAC_KM: NAC_KM }
  };
})(window);
