/*!
 * SVWSPID — bộ dựng sơ đồ P&ID chuẩn cho tool thiết kế SVWS
 * =========================================================
 * Vì sao có thư viện này: AI vẽ P&ID bằng cách gõ toạ độ SVG mà không nhìn thấy
 * kết quả, nên tự đặt hai con số mâu thuẫn nhau mà không biết. Ví dụ thật đo
 * được trong một tool đã sinh: ký hiệu cột lọc GAC cao 38px nhưng khoảng cách
 * xếp song song lại để 30px → hai cột chồng lên nhau thành một vệt đen. Bước
 * nhảy giữa các cụm cũng để cố định 95px bất kể cụm trước rộng bao nhiêu.
 *
 * Thư viện nhận phần bố cục: nó ĐO ký hiệu và ĐO chữ, tự dịch chuyển cho khỏi
 * đè nhau, tự nối ống vuông góc không cắt qua thiết bị. AI chỉ KHAI BÁO dây
 * chuyền theo thứ tự công nghệ.
 *
 * Dùng:
 *   const D = SVWSPID.to({ w:1560, h:940, ma:'SVWS-...', ten:'...', dong2:'...' });
 *   const h1 = D.hang(175);
 *   h1.nguon({nhan:'Nước cấp nhà máy L-01 DN50'});
 *   h1.bon({tag:'TK-101', ghi:'9 m³ SS304'});
 *   h1.bom({tag:'P-101A/B', ghi:'3 kW', dup:true});
 *   h1.cot({tag:'MMF-101', qty:2, ghi:'Ø1067 v=18,3 m/h'});
 *   h1.ro ({tag:'RO-101', vessels:5, ghi:'5×2 8040'});
 *   D.dungCu('TK-101','LIT-101');          // bầu đo, tự tìm chỗ trống
 *   D.chu('TK-101','LSL/LSH','duoi');
 *   document.getElementById('pid').innerHTML = D.ve();
 *   console.log(D.kiemTra());              // còn chỗ nào đè nhau không
 */
(function (global) {
  'use strict';

  var NAVY = '#0b2545', INK = '#12263a', MO = '#33475b', XAM = '#6c757d';
  var MAU = {
    raw:   '#0b2545',   // nước cấp / RO feed
    di:    '#1f9d55',   // permeate / DI
    conc:  '#c8791a',   // nước cô đặc / xả
    chem:  '#b8860b',   // hoá chất
    cip:   '#8a6aa8',   // CIP
    tin:   '#6c757d'    // tín hiệu SCADA
  };

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
  /* Ước lượng bề rộng chữ. KHÔNG đo được thì không tránh được va chạm — đây là
     mấu chốt: bản cũ đặt nhãn ở khoảng lệch cố định nên nhãn dài là đè lên nhau. */
  function rongChu(s, fs, dam) {
    return String(s || '').length * fs * (dam ? 0.56 : 0.52);
  }

  function to(o) {
    o = o || {};
    var W = o.w || 1560, H = o.h || 940;
    // Khổ giấy TỰ NỚI theo nội dung. Để cố định thì hàng thiết bị đặt ngoài khổ
    // bị cắt mất ký hiệu, còn nhãn bị kéo ngược vào trong rồi chồng thành một
    // đống ở góc — đúng lỗi đã gặp trên bản P&ID hệ DI 168 m³/ngày.
    var canW = W, canH = H;
    var out = [];                 // các mẩu SVG
    var chiem = [];               // hộp đã chiếm chỗ: {x1,y1,x2,y2,ten}
    var moc = {};                 // tag → {x,y,w,h} để nối và gắn bầu đo
    var vachao = [];              // các va chạm còn lại sau khi đã né
    var nhanCho = [];             // nhãn CHỜ đặt ở lượt sau (xem ve())
    var hthong = null;            // đồ thị thiết bị/đường ống khi tự xếp
    var mocLoai = {};             // tag → loại thiết bị, để chọn chỗ gắn bầu đo
    var ioDaGan = null;           // kết quả gắn bầu đo từ bảng I/O
    var api2 = null;              // gán ở cuối, để heThong() trả về chính nó

    function themChiem(x1, y1, x2, y2, ten) {
      chiem.push({ x1: x1, y1: y1, x2: x2, y2: y2, ten: ten || '' });
    }
    function dung(a, b, ho) {
      ho = ho || 0;
      return !(a.x2 + ho < b.x1 || b.x2 + ho < a.x1 ||
               a.y2 + ho < b.y1 || b.y2 + ho < a.y1);
    }
    function coTrong(r, ho) {
      for (var i = 0; i < chiem.length; i++) if (dung(r, chiem[i], ho)) return false;
      return true;
    }

    // ------------------------------------------------------------ vẽ cơ bản
    function ln(x1, y1, x2, y2, mau, w, net) {
      out.push('<line x1="' + x1 + '" y1="' + y1 + '" x2="' + x2 + '" y2="' + y2 +
        '" stroke="' + (mau || NAVY) + '" stroke-width="' + (w || 1.6) + '"' +
        (net ? ' stroke-dasharray="' + net + '"' : '') + ' />');
    }
    /** Đặt chữ, TỰ ĐẨY cho tới khi không đè lên gì — chỗ chữa lỗi chồng nhãn. */
    function chu(x, y, s, fs, mau, neo, dam, huong) {
      fs = fs || 9; neo = neo || 'middle';
      var w = rongChu(s, fs, dam), h = fs * 1.25;
      var dx = neo === 'middle' ? -w / 2 : neo === 'end' ? -w : 0;
      // giữ chữ trong khổ giấy — nhãn dài ở mép trái từng bị đẩy ra ngoài khung
      x = Math.min(W - 8 - (dx + w), Math.max(8 - dx, x));
      var uu = (huong === 'duoi' ? 1 : -1) * (fs + 5);
      var yy = y, r = null, xong = false;
      // thử hướng ưu tiên trước, hết chỗ thì thử hướng ngược lại
      [uu, -uu].forEach(function (buoc) {
        if (xong) return;
        yy = y;
        for (var i = 0; i < 16; i++) {
          r = { x1: x + dx - 2, y1: yy - h, x2: x + dx + w + 2, y2: yy + 3 };
          if (coTrong(r, 2) && r.y1 > 52 && r.y2 < H - 6) { xong = true; return; }
          yy += buoc;
        }
      });
      themChiem(r.x1, r.y1, r.x2, r.y2, 'chữ:' + s);
      out.push('<text x="' + x + '" y="' + yy + '" font-size="' + fs +
        '" fill="' + (mau || INK) + '" text-anchor="' + neo + '"' +
        (dam ? ' font-weight="600"' : '') +
        ' font-family="IBM Plex Sans,Segoe UI,Arial,sans-serif">' + esc(s) + '</text>');
      return yy;
    }

    // ------------------------------------------------------------ ký hiệu
    // Mỗi ký hiệu tự khai báo BỀ RỘNG THẬT để con trỏ nhảy đúng, không đoán.
    var KH = {
      nguon: function (x, y) {
        ln(x, y, x + 46, y); out.push(muiTen(x + 44, y));
        return { w: 52, h: 30, cx: x + 26 };
      },
      bon: function (x, y, e) {
        var w = 84, h = 92;
        out.push('<rect x="' + x + '" y="' + (y - h / 2) + '" width="' + w + '" height="' + h +
          '" rx="4" fill="#eaf4fb" stroke="' + NAVY + '" stroke-width="1.8"/>');
        out.push('<rect x="' + (x + 4) + '" y="' + (y + 6) + '" width="' + (w - 8) +
          '" height="' + (h / 2 - 10) + '" fill="#bfe0f2" opacity="0.85"/>');
        return { w: w, h: h, cx: x + w / 2 };
      },
      /* Bơm đơn, hoặc CỤM BƠM song song 1 chạy 1 dừng. Cụm phải vẽ đủ van chặn
         hai đầu mỗi bơm và VAN MỘT CHIỀU ở đẩy — thiếu van một chiều thì nước
         từ bơm đang chạy vòng ngược qua bơm dừng về góp hút, chạy lòng vòng
         trong cụm chứ không ra hệ thống. Vẽ thiếu là thợ lắp thiếu. */
      bom: function (x, y, e) {
        var r = 13;
        var n = Math.max(1, Math.min(4, +e.soBom || (e.dup ? 2 : 1)));
        function mot(yy, xb) {
          out.push('<circle cx="' + (xb + r) + '" cy="' + yy + '" r="' + r +
            '" fill="#fff" stroke="' + NAVY + '" stroke-width="1.8"/>');
          out.push('<path d="M' + (xb + r - 5) + ' ' + (yy - 6) + ' L' + (xb + r + 7) +
            ' ' + yy + ' L' + (xb + r - 5) + ' ' + (yy + 6) + ' Z" fill="' + NAVY + '"/>');
        }
        function vanNho(cx, cy) {          // van chặn: hai tam giác đối đỉnh
          var s = 6;
          out.push('<path d="M' + (cx - s) + ' ' + (cy - s) + ' L' + (cx + s) + ' ' +
            (cy + s) + ' L' + (cx + s) + ' ' + (cy - s) + ' L' + (cx - s) + ' ' +
            (cy + s) + ' Z" fill="#fff" stroke="' + NAVY + '" stroke-width="1.3"/>');
        }
        function motChieu(cx, cy) {        // van một chiều: tam giác chặn
          out.push('<path d="M' + (cx - 7) + ' ' + (cy - 6) + ' L' + (cx + 6) + ' ' +
            cy + ' L' + (cx - 7) + ' ' + (cy + 6) + ' Z" fill="#fff" stroke="' +
            MAU.di + '" stroke-width="1.5"/>');
          ln(cx + 6, cy - 7, cx + 6, cy + 7, MAU.di, 1.5);
        }
        if (n === 1) { mot(y, x); return { w: r * 2 + 8, h: 30, cx: x + r }; }

        var buoc = 46, xv = x + 22, xb = xv + 22, xm = xb + r * 2 + 18, xr = xm + 30;
        var y0 = y - (n - 1) * buoc / 2;
        for (var i = 0; i < n; i++) {
          var yy = y0 + i * buoc;
          ln(x, yy, xv - 6, yy, NAVY, 1.5);            // nhánh từ góp hút
          vanNho(xv, yy);                              // van chặn hút
          ln(xv + 6, yy, xb, yy, NAVY, 1.5);
          mot(yy, xb);
          ln(xb + r * 2, yy, xm - 7, yy, NAVY, 1.5);
          motChieu(xm, yy);                            // van một chiều
          ln(xm + 7, yy, xr - 6, yy, NAVY, 1.5);
          vanNho(xr, yy);                              // van chặn đẩy
          ln(xr + 6, yy, xr + 22, yy, NAVY, 1.5);
        }
        // hai ống góp chung nối các nhánh lại
        ln(x, y0, x, y0 + (n - 1) * buoc, NAVY, 2);
        ln(xr + 22, y0, xr + 22, y0 + (n - 1) * buoc, NAVY, 2);
        return { w: xr + 22 - x + 8, h: (n - 1) * buoc + 34, cx: (x + xr + 22) / 2 };
      },
      cot: function (x, y, e) {           // cột lọc áp lực (MMF/GAC/MB)
        var w = 30, h = 46, n = Math.max(1, e.qty || 1);
        var buoc = h + 16;                // ← KHOẢNG CÁCH LUÔN LỚN HƠN CHIỀU CAO
        for (var i = 0; i < n; i++) {
          var yy = y + (i - (n - 1) / 2) * buoc;
          out.push('<rect x="' + x + '" y="' + (yy - h / 2) + '" width="' + w +
            '" height="' + h + '" rx="' + (w / 2) + '" fill="' + (e.mau || '#f3ead6') +
            '" stroke="' + NAVY + '" stroke-width="1.6"/>');
        }
        return { w: w + 10, h: (n - 1) * buoc + h, cx: x + w / 2 };
      },
      loc: function (x, y) {              // lọc tinh (cartridge)
        var w = 24, h = 36;
        out.push('<rect x="' + x + '" y="' + (y - h / 2) + '" width="' + w + '" height="' + h +
          '" fill="#fff" stroke="' + NAVY + '" stroke-width="1.6"/>');
        ln(x, y - h / 2, x + w, y + h / 2, NAVY, 1);
        return { w: w + 10, h: h, cx: x + w / 2 };
      },
      ro: function (x, y, e) {            // giàn màng RO / EDI
        var n = Math.max(1, Math.min(8, e.vessels || 3));
        var w = 96, hv = 11, buoc = hv + 7;
        for (var i = 0; i < n; i++) {
          var yy = y + (i - (n - 1) / 2) * buoc;
          out.push('<rect x="' + x + '" y="' + (yy - hv / 2) + '" width="' + w +
            '" height="' + hv + '" rx="' + (hv / 2) + '" fill="#dff1f6" stroke="' +
            NAVY + '" stroke-width="1.3"/>');
        }
        return { w: w + 10, h: (n - 1) * buoc + hv, cx: x + w / 2 };
      },
      edi: function (x, y, e) {           // EDI dạng tấm–khung, KHÔNG phải vỏ màng
        var w = 78, h = 58, n = Math.max(1, Math.min(6, e.stacks || 1));
        var buoc = h + 18;                // luôn lớn hơn chiều cao ký hiệu
        for (var i = 0; i < n; i++) {
          var yy = y + (i - (n - 1) / 2) * buoc;
          out.push('<rect x="' + x + '" y="' + (yy - h / 2) + '" width="' + w +
            '" height="' + h + '" fill="#eef4fb" stroke="' + NAVY + '" stroke-width="1.8"/>');
          for (var k = 1; k < 7; k++) {   // các tấm cell xếp chồng
            ln(x + w * k / 7, yy - h / 2 + 4, x + w * k / 7, yy + h / 2 - 4, NAVY, 0.8);
          }
          // hai cực một chiều
          out.push('<text x="' + (x + 8) + '" y="' + (yy - h / 2 - 3) + '" font-size="9" ' +
            'fill="#b3271e" font-weight="700">+</text>');
          out.push('<text x="' + (x + w - 13) + '" y="' + (yy - h / 2 - 3) + '" font-size="9" ' +
            'fill="#12263a" font-weight="700">−</text>');
        }
        return { w: w + 12, h: (n - 1) * buoc + h + 12, cx: x + w / 2 };
      },
      uv: function (x, y) {
        var w = 54, h = 22;
        out.push('<rect x="' + x + '" y="' + (y - h / 2) + '" width="' + w + '" height="' + h +
          '" rx="11" fill="#fdf5cf" stroke="' + NAVY + '" stroke-width="1.6"/>');
        out.push('<text x="' + (x + w / 2) + '" y="' + (y + 4) + '" font-size="9" ' +
          'text-anchor="middle" fill="' + INK + '">UV</text>');
        return { w: w + 10, h: h, cx: x + w / 2 };
      },
      van: function (x, y) {
        var s = 9;
        out.push('<path d="M' + (x - s) + ' ' + (y - s) + ' L' + (x + s) + ' ' + (y + s) +
          ' L' + (x + s) + ' ' + (y - s) + ' L' + (x - s) + ' ' + (y + s) + ' Z" fill="#fff" stroke="' +
          NAVY + '" stroke-width="1.5"/>');
        return { w: s * 2 + 6, h: s * 2, cx: x };
      }
    };
    function muiTen(x, y) {
      return '<path d="M' + x + ' ' + (y - 5) + ' L' + (x + 9) + ' ' + y +
        ' L' + x + ' ' + (y + 5) + ' Z" fill="' + NAVY + '"/>';
    }

    // ------------------------------------------------------------ một hàng
    function hang(y, opt) {
      opt = opt || {};
      canH = Math.max(canH, y + 170);
      var x = opt.x0 || 40;
      var truoc = null;
      var api = {};

      function dat(loai, e) {
        e = e || {};
        // nối từ thiết bị trước sang thiết bị này (đường ngang, không cắt ký hiệu)
        if (truoc) ln(truoc.x2, y, x, y, MAU[e.dong || 'raw'] || MAU.raw, 1.8);
        var k = KH[loai](x, y, e);
        themChiem(x - 2, y - k.h / 2 - 2, x + k.w + 2, y + k.h / 2 + 2, e.tag || loai);
        // Nhãn KHÔNG vẽ ngay: lúc này thiết bị bên phải chưa được dựng nên
        // chưa biết chỗ nào bận. Xếp hàng, vẽ ở lượt sau khi đã có đủ ký hiệu.
        if (e.tag) {
          moc[e.tag] = { x: k.cx, y: y, w: k.w, h: k.h, x1: x, x2: x + k.w };
          mocLoai[e.tag] = String(e.type || '') + ' ' + loai;
          nhanCho.push({ x: k.cx, y: y - k.h / 2 - 8,
                         s: e.tag + (e.ghi ? ' ' + e.ghi : ''),
                         fs: 9, mau: INK, dam: 1, huong: 'tren' });
        } else if (e.nhan) {
          nhanCho.push({ x: k.cx, y: y - 16, s: e.nhan, fs: 9, mau: MO,
                         dam: 0, huong: 'tren' });
        }
        truoc = { x2: x + k.w };
        x += k.w + (opt.hoHang || 30);    // ← NHẢY THEO BỀ RỘNG THẬT, không phải hằng số
        canW = Math.max(canW, x + 90);
        canH = Math.max(canH, y + k.h / 2 + 130);
        return api;
      }
      ['nguon', 'bon', 'bom', 'cot', 'loc', 'ro', 'edi', 'uv', 'van'].forEach(function (t) {
        api[t] = function (e) { return dat(t, e); };
      });
      api.cuoi = function () { return x; };
      api.y = y;
      return api;
    }

    // ==================================================================
    // SINH P&ID TỪ CHÍNH SỔ EQUIP + PIPES CỦA BẢN VẼ 3D
    // ------------------------------------------------------------------
    // Cách cũ bắt người viết tool gọi tay từng ký hiệu theo thứ tự mình nghĩ
    // ra — nên P&ID hay lộn thứ tự công nghệ và thiếu kết nối so với 3D.
    // Ở đây coi mỗi thiết bị là một NÚT có cổng vào/ra, mỗi đường ống là một
    // CẠNH; xếp cột theo thứ tự dòng chảy (sắp xếp tô-pô), xếp hàng trong cột
    // cho khỏi đè, rồi nối đúng theo tuyến. Thêm thiết bị vào 3D là P&ID có
    // ngay, không ai phải soát chồng lấn bằng mắt.
    // ==================================================================
    var LOAI_KH = {
      tank: 'bon', be: 'bon', bon: 'bon',
      vessel: 'cot', filter: 'cot', mixedbed: 'cot', cot: 'cot',
      cartridge: 'loc', loc: 'loc',
      pump: 'bom', bom: 'bom',
      roskid: 'ro', ro: 'ro',
      edi: 'edi',
      uv: 'uv',
      dosing: 'bon'
    };
    var MAU_DONG = {
      raw: MAU.raw, filtered: MAU.raw, ro: MAU.di, di: MAU.di, permeate: MAU.di,
      conc: MAU.conc, waste: MAU.conc, reject: MAU.conc, drain: MAU.conc,
      chem: MAU.chem, cip: MAU.cip, air: MAU.tin, steam: MAU.conc
    };
    function mauDong(s) { return MAU_DONG[String(s || 'raw').toLowerCase()] || MAU.raw; }

    /** Đo ký hiệu mà KHÔNG vẽ — cần biết kích thước trước mới xếp cột được. */
    function doKT(loai, e) {
      var n = out.length;
      var k = KH[loai](0, 0, e || {});
      out.length = n;                       // xoá phần vừa vẽ thử
      return k;
    }

    /** Đặt một ký hiệu tại đúng toạ độ (dùng cho chế độ tự xếp). */
    function datTai(loai, e, x, y) {
      var k = KH[loai](x, y, e);
      themChiem(x - 2, y - k.h / 2 - 2, x + k.w + 2, y + k.h / 2 + 2, e.tag || loai);
      moc[e.tag] = { x: k.cx, y: y, w: k.w, h: k.h, x1: x, x2: x + k.w };
      mocLoai[e.tag] = String(e.type || '') + ' ' + loai;
      nhanCho.push({ x: k.cx, y: y - k.h / 2 - 8,
                     s: e.tag + (e.ghi ? ' ' + e.ghi : ''),
                     fs: 9, mau: INK, dam: 1, huong: 'tren' });
      canW = Math.max(canW, x + k.w + 90);
      canH = Math.max(canH, y + k.h / 2 + 140);
      return k;
    }

    /** Mũi tên vào thiết bị đích, để nhìn ra chiều dòng chảy. */
    function muiVao(x, y, mau) {
      out.push('<path d="M' + (x - 9) + ' ' + (y - 4.5) + ' L' + x + ' ' + y +
        ' L' + (x - 9) + ' ' + (y + 4.5) + ' Z" fill="' + mau + '"/>');
    }

    /**
     * Dựng cả sơ đồ từ EQUIP + PIPES.
     * o: {hoCot, hoHang, yTam, ghi(e)->chuỗi ghi chú thêm}
     */
    function heThong(EQUIP, PIPES, o2) {
      o2 = o2 || {};
      var hoCot = o2.hoCot || 96, hoHang = o2.hoHang || 40;
      var nut = [], chiSo = {};
      (EQUIP || []).forEach(function (e) {
        var t = String(e.type || '').toLowerCase();
        if (/panel|tu|mcc|plc/.test(t)) return;      // tủ điện không nằm trên P&ID
        var id = e.id || e.tag;
        if (!id) { vachao.push('Có thiết bị chưa đặt id/tag — không đưa lên P&ID được.'); return; }
        chiSo[id] = nut.length;
        nut.push({ id: id, loai: LOAI_KH[t] || 'bon', e: e, cap: 0, ra: [], vao: [] });
      });
      if (!nut.length) { vachao.push('Không có thiết bị nào để vẽ P&ID.'); return api2; }

      var canh = [];
      (PIPES || []).forEach(function (p) {
        var a = chiSo[p.from], b = chiSo[p.to];
        if (a == null || b == null) {
          vachao.push('Đường ống ' + p.from + ' → ' + p.to +
                      ': không tìm thấy thiết bị trong danh sách.');
          return;
        }
        var i = canh.length;
        canh.push({ a: a, b: b, p: p });
        nut[a].ra.push(i); nut[b].vao.push(i);
      });

      /* Tách TUYẾN HỒI LƯU trước, rồi mới xếp cột.
         Dòng hồi lưu (nước cô đặc quay về bể cấp) tạo thành vòng kín; nếu cứ
         nới cấp bậc theo vòng thì mỗi lượt lại đẩy cả vòng sang phải — 13 thiết
         bị ra 85 cột. Ở đây duyệt sâu, cạnh nào quay về nút ĐANG TRÊN ĐƯỜNG
         duyệt thì đánh dấu là hồi lưu và không tính vào thứ tự cột. */
      var n = nut.length, mau = new Array(n).fill(0);   // 0 trắng, 1 đang đi, 2 xong
      (function () {
        function di(u) {
          mau[u] = 1;
          nut[u].ra.forEach(function (ci) {
            var v = canh[ci].b;
            if (mau[v] === 1) canh[ci].lui = true;      // quay về nút đang đi → hồi lưu
            else if (mau[v] === 0) di(v);
          });
          mau[u] = 2;
        }
        nut.forEach(function (u, i) { if (mau[i] === 0 && !u.vao.length) di(i); });
        nut.forEach(function (u, i) { if (mau[i] === 0) di(i); });   // nút còn kẹt trong vòng
      })();

      // Cấp bậc = quãng đường dài nhất từ đầu nguồn, chỉ theo tuyến ĐI TỚI.
      var doi = true, vong = 0;
      while (doi && vong <= n) {
        doi = false; vong++;
        canh.forEach(function (c) {
          if (c.lui) return;
          if (nut[c.b].cap < nut[c.a].cap + 1) { nut[c.b].cap = nut[c.a].cap + 1; doi = true; }
        });
      }

      // ---- gom theo cột, đo kích thước, tính vị trí
      var cot = [];
      nut.forEach(function (u) {
        u.k = doKT(u.loai, u.e);
        (cot[u.cap] = cot[u.cap] || []).push(u);
      });
      var x = o2.x0 || 56;
      var caoNhat = 0;
      cot.forEach(function (ds) {
        if (!ds) return;
        var cao = ds.reduce(function (s, u) { return s + u.k.h + hoHang; }, -hoHang);
        caoNhat = Math.max(caoNhat, cao);
      });
      var yTam = o2.yTam || (90 + caoNhat / 2 + 40);

      cot.forEach(function (ds) {
        if (!ds || !ds.length) return;
        var cao = ds.reduce(function (s, u) { return s + u.k.h + hoHang; }, -hoHang);
        var y = yTam - cao / 2;
        var rong = 0;
        ds.forEach(function (u) {
          u.x = x; u.y = y + u.k.h / 2;
          rong = Math.max(rong, u.k.w);
          y += u.k.h + hoHang;
        });
        ds.forEach(function (u) { datTai(u.loai, u.e, u.x, u.y); });
        x += rong + hoCot;
      });

      // ---- nối theo đúng tuyến ống đã khai
      canh.forEach(function (c) {
        var a = moc[nut[c.a].e.tag], b = moc[nut[c.b].e.tag];
        if (!a || !b) return;
        var mau = mauDong(c.p.service || c.p.dong);
        var nhan = (c.p.dn ? 'DN' + c.p.dn : '') +
                   (c.p.nhan ? ' ' + c.p.nhan : '');
        if (c.lui) {                       // dòng hồi lưu: vòng xuống dưới
          noi(nut[c.a].e.tag, nut[c.b].e.tag,
              { dong: c.p.service || 'conc', nhan: nhan || 'hồi lưu', phia: 'duoi' });
          return;
        }
        // đi tới: ra mép phải nút nguồn, sang cột đích, vào mép trái
        var x1 = a.x2, x2 = b.x1;
        if (Math.abs(a.y - b.y) < 5) {
          ln(x1, a.y, x2 - 9, b.y, mau, 1.8);
        } else {
          var gap = x2 - x1, xm = x1 + gap * 0.55;
          // tránh đoạn dọc cắt qua ký hiệu: dịch dần cho tới khi trống
          for (var t2 = 0; t2 < 8; t2++) {
            var oDoc = { x1: xm - 5, y1: Math.min(a.y, b.y), x2: xm + 5, y2: Math.max(a.y, b.y) };
            if (coTrong(oDoc, 3)) break;
            xm = x1 + gap * (0.55 - 0.06 * (t2 + 1));
            if (xm < x1 + 14) { xm = x1 + gap * 0.5; break; }
          }
          ln(x1, a.y, xm, a.y, mau, 1.8);
          ln(xm, a.y, xm, b.y, mau, 1.8);
          ln(xm, b.y, x2 - 9, b.y, mau, 1.8);
          themChiem(xm - 3, Math.min(a.y, b.y), xm + 3, Math.max(a.y, b.y),
                    'ống ' + nut[c.a].id + '→' + nut[c.b].id);
        }
        muiVao(x2, b.y, mau);
        if (nhan) nhanCho.push({ x: (x1 + x2) / 2, y: Math.min(a.y, b.y) - 7,
                                 s: nhan, fs: 8, mau: mau, dam: 0, huong: 'tren' });
      });

      // ---- mũi tên nguồn cấp cho các nút không có đường vào
      nut.forEach(function (u) {
        if (u.vao.length) return;
        var m = moc[u.e.tag]; if (!m) return;
        ln(m.x1 - 48, m.y, m.x1 - 10, m.y, MAU.raw, 1.8);
        muiVao(m.x1, m.y, MAU.raw);
        nhanCho.push({ x: m.x1 - 30, y: m.y - 12, s: u.e.nguon || 'Nguồn cấp',
                       fs: 8, mau: MO, dam: 0, huong: 'tren' });
      });

      // ---- ghi nhận để kiemTra() soi
      hthong = { nut: nut, canh: canh, cot: cot.length };
      return api2;
    }

    // --------------------------------------------------- bầu đo & ghi chú
    /** Bầu đo ISA gắn vào thiết bị, tự tìm phía còn trống. */
    function dungCu(tag, ten, phia) {
      var m = moc[tag];
      if (!m) { vachao.push('Không thấy thiết bị ' + tag + ' để gắn ' + ten); return; }
      var r = 15, thu = phia === 'duoi' ? [1, -1] : [-1, 1];
      for (var t = 0; t < thu.length; t++) {
        for (var d = 30; d <= 96; d += 16) {
          var cy = m.y + thu[t] * (m.h / 2 + d);
          var box = { x1: m.x - r - 2, y1: cy - r - 2, x2: m.x + r + 2, y2: cy + r + 2 };
          if (coTrong(box, 3)) {
            ln(m.x, m.y + thu[t] * m.h / 2, m.x, cy - thu[t] * r, XAM, 0.9, '3 3');
            out.push('<circle cx="' + m.x + '" cy="' + cy + '" r="' + r +
              '" fill="#fff" stroke="' + XAM + '" stroke-width="1.3"/>');
            out.push('<text x="' + m.x + '" y="' + (cy + 3.5) + '" font-size="7.6" ' +
              'text-anchor="middle" fill="' + MO + '">' + esc(ten) + '</text>');
            themChiem(box.x1, box.y1, box.x2, box.y2, 'bầu ' + ten);
            return;
          }
        }
      }
      vachao.push('Không còn chỗ trống để đặt bầu đo ' + ten + ' cạnh ' + tag);
    }

    /* ==================================================================
     * GẮN BẦU ĐO TỪ CHÍNH BẢNG I/O CỦA TỦ ĐIỆN
     * Mỗi kênh DI/AI là một dụng cụ đo THẬT ngoài hiện trường. Lấy thẳng từ
     * bảng I/O thì P&ID và bảng I/O không thể lệch nhau: thêm một đầu đo vào
     * PLC là bầu đo hiện lên sơ đồ, và kênh nào không gắn được vào thiết bị
     * nào sẽ bị báo lỗi thay vì lặng lẽ thiếu.
     * ================================================================ */
    // Chữ cái đầu của tag ISA → loại thiết bị hay mang dụng cụ đó
    var HOP_TB = {
      L: /tank|be|bon/i,                       // mức: bồn bể
      T: /tank|be|bon/i,                       // nhiệt độ
      P: /pump|bom|vessel|filter|ro|edi|cartridge/i,   // áp suất
      F: /./,                                  // lưu lượng: chỗ nào cũng có thể
      A: /vessel|ro|edi|mixedbed|tank/i,       // phân tích (pH, độ dẫn)
      C: /vessel|ro|edi|mixedbed|tank/i
    };
    function soVongLap(tag) {                  // 'LIT-101' → '101'
      var m = String(tag || '').match(/(\d{2,4})\s*$/);
      return m ? m[1] : '';
    }
    /**
     * ds: mảng từ SVWSDIEN.plc(...).danhSach()
     * opt: {caDauRa: true để gắn cả DO/AO (van điều khiển, lệnh chạy)}
     */
    var daGan = {};       // tag thiết bị → danh sách dụng cụ đã gắn lên nó
    function daGanCho(tag, re) {
      return (daGan[tag] || []).some(function (t) { return re.test(t); });
    }
    function dungCuTuIO(ds, opt) {
      opt = opt || {};
      var dsTag = Object.keys(moc);
      var demGan = 0, demBo = 0;
      (ds || []).forEach(function (k) {
        var kieu = String(k.kieu || '').toUpperCase();
        var doDac = kieu === 'DI' || kieu === 'AI';
        if (!doDac && !opt.caDauRa) return;
        if (!k.tag) { vachao.push('Kênh ' + (k.dc || '?') + ' chưa có tag hiện trường — ' +
                                  'không biết gắn dụng cụ vào thiết bị nào.'); return; }
        var dich = '';
        if (k.tb && moc[k.tb]) dich = k.tb;                    // khai rõ thì theo khai
        else {
          var so = soVongLap(k.tag);
          if (so) {
            var chu0 = String(k.tag).charAt(0).toUpperCase();
            var hop = HOP_TB[chu0] || /./;
            // ưu tiên thiết bị cùng số vòng lặp VÀ đúng họ thiết bị
            var uu = dsTag.filter(function (t) {
              return soVongLap(t) === so && hop.test(String((mocLoai[t] || '')));
            });
            var moi = uu.length ? uu : dsTag.filter(function (t) {
              return soVongLap(t) === so;
            });
            if (moi.length) dich = moi[0];
          }
        }
        if (!dich) {
          demBo++;
          vachao.push('Dụng cụ ' + k.tag + ' (' + kieu + ' ' + (k.dc || '') + ') không ' +
                      'gắn được vào thiết bị nào trên sơ đồ — kiểm lại số vòng lặp, ' +
                      'hoặc khai rõ tb:"<tag thiết bị>" trong kênh I/O.');
          return;
        }
        dungCu(dich, k.tag, opt.phia);
        (daGan[dich] = daGan[dich] || []).push(k.tag);
        demGan++;
      });
      ioDaGan = { gan: demGan, bo: demBo, tong: (ds || []).length };
      return api2;
    }

    function ghiChu(tag, s, phia) {
      var m = moc[tag];
      if (!m) { vachao.push('Không thấy thiết bị ' + tag + ' để ghi chú'); return; }
      chu(m.x, m.y + (phia === 'duoi' ? 1 : -1) * (m.h / 2 + 16), s, 8, MO,
          'middle', 0, phia === 'duoi' ? 'duoi' : 'tren');
    }

    /** Nối hai thiết bị bằng đường gấp khúc VUÔNG GÓC, né mọi ký hiệu. */
    function noi(tagA, tagB, e) {
      e = e || {};
      var a = moc[tagA], b = moc[tagB];
      if (!a || !b) { vachao.push('Không nối được ' + tagA + ' → ' + tagB); return; }
      var mau = MAU[e.dong || 'conc'] || MAU.conc;
      // Tìm một làn ngang còn trống: thử hướng ưu tiên trước, hết chỗ thì thử
      // hướng ngược lại — chỉ thử một hướng thì gặp hàng kế bên là bí.
      var uu = e.phia === 'tren' ? -1 : 1;
      var thu = [uu, -uu], i, huong, d, yy, dai;
      for (i = 0; i < thu.length; i++) {
        huong = thu[i];
        for (d = 46; d <= 420; d += 16) {
          yy = huong > 0 ? Math.max(a.y, b.y) + d : Math.min(a.y, b.y) - d;
          if (yy < 60 || yy > H - 20) break;
          dai = { x1: Math.min(a.x, b.x) - 2, y1: yy - 6, x2: Math.max(a.x, b.x) + 2, y2: yy + 6 };
          if (!coTrong(dai, 4)) continue;
          ln(a.x, a.y + huong * a.h / 2, a.x, yy, mau, 1.5);
          ln(a.x, yy, b.x, yy, mau, 1.5);
          ln(b.x, yy, b.x, b.y + huong * b.h / 2, mau, 1.5);
          themChiem(dai.x1, dai.y1, dai.x2, dai.y2, 'ống ' + tagA + '→' + tagB);
          if (e.nhan) chu((a.x + b.x) / 2, yy - 7, e.nhan, 8, mau, 'middle', 0,
                          huong < 0 ? 'tren' : 'duoi');
          return;
        }
      }
      vachao.push('Không tìm được đường trống để nối ' + tagA + ' → ' + tagB +
                  ' — nới chiều cao khổ vẽ hoặc giãn khoảng cách giữa các hàng.');
    }

    // ------------------------------------------------------------- xuất
    /** Nới khổ giấy cho vừa nội dung TRƯỚC khi đặt nhãn — đặt nhãn xong mới nới
        thì nhãn đã bị ép vào trong rồi. */
    function noiKho() {
      W = Math.max(W, canW);
      H = Math.max(H, canH);
    }

    /** Vẽ hết nhãn đang chờ — gọi khi mọi ký hiệu đã có mặt trong 'chiem'. */
    function xaNhan() {
      nhanCho.forEach(function (n) {
        chu(n.x, n.y, n.s, n.fs, n.mau, 'middle', n.dam, n.huong);
      });
      nhanCho = [];
    }

    function ve() {
      noiKho();
      xaNhan();
      var dau = '<svg viewBox="0 0 ' + W + ' ' + H + '" width="100%" ' +
        'xmlns="http://www.w3.org/2000/svg" style="background:#fdfefe">' +
        '<rect width="' + W + '" height="' + H + '" fill="#fdfefe" stroke="' + NAVY + '"/>';
      var tieu = '';
      if (o.ma || o.ten) {
        tieu += '<text x="20" y="26" font-size="15" font-weight="700" fill="' + NAVY +
          '" font-family="IBM Plex Sans,Segoe UI,Arial,sans-serif">' +
          esc('P&ID — ' + (o.ma || '') + (o.ten ? ' • ' + o.ten : '')) + '</text>';
      }
      if (o.dong2) {
        tieu += '<text x="20" y="46" font-size="10.5" fill="' + MO +
          '" font-family="IBM Plex Sans,Segoe UI,Arial,sans-serif">' + esc(o.dong2) + '</text>';
      }
      return dau + tieu + out.join('') + '</svg>';
    }

    /** Còn chỗ nào đè nhau không — bắt lỗi trước khi giao bản vẽ. */
    function kiemTra() {
      noiKho();
      xaNhan();
      var loi = vachao.slice();
      for (var i = 0; i < chiem.length; i++) {
        for (var j = i + 1; j < chiem.length; j++) {
          if (dung(chiem[i], chiem[j], -1)) {
            var t = 'Đè nhau: ' + chiem[i].ten + '  ×  ' + chiem[j].ten;
            if (loi.indexOf(t) < 0) loi.push(t);
          }
        }
      }
      // Chế độ tự xếp: kiểm luôn tính liền lạc của dây chuyền, không chỉ kiểm vẽ.
      if (hthong) {
        hthong.nut.forEach(function (u) {
          if (!u.vao.length && !u.ra.length)
            loi.push('Thiết bị ' + u.id + ' không nối vào đường ống nào — ' +
                     'thiếu tuyến trong khai báo PIPES.');
          else if (!u.ra.length && !/tank|be|bon/.test(String(u.e.type || '').toLowerCase()))
            loi.push('Thiết bị ' + u.id + ' chỉ có đường vào, không có đường ra — ' +
                     'nước vào rồi đi đâu?');
        });
        var luiSo = hthong.canh.filter(function (c) { return c.lui; }).length;
        if (luiSo > hthong.nut.length)
          loi.push('Có ' + luiSo + ' tuyến hồi lưu trên ' + hthong.nut.length +
                   ' thiết bị — kiểm lại chiều dòng chảy trong PIPES, nhiều khả năng ' +
                   'khai ngược from/to.');
      }
      // Đối chiếu P&ID với bảng I/O: bồn nào cũng phải có đo mức, cụm màng phải
      // có đo áp — thiếu là vận hành mù, không phải lỗi vẽ nhưng phải nhắc.
      if (ioDaGan && hthong) {
        var coDo = {};
        Object.keys(moc).forEach(function (t) { coDo[t] = 0; });
        chiem.forEach(function (c) {
          var m = String(c.ten || '').match(/^bầu (\S+)/);
          if (m) coDo[m[1]] = 1;
        });
        hthong.nut.forEach(function (u) {
          var t = String(u.e.type || '').toLowerCase();
          var tag = u.e.tag;
          if (/tank|be|bon/.test(t) && !daGanCho(tag, /^L/))
            loi.push('Bồn ' + tag + ' chưa có dụng cụ đo mức trong bảng I/O — ' +
                     'không biết khi nào bơm chạy hay dừng.');
          if (/^(ro|roskid|edi)$/.test(t) && !daGanCho(tag, /^[PA]/))
            loi.push('Cụm ' + tag + ' chưa có đo áp suất hoặc độ dẫn trong bảng I/O — ' +
                     'không giám sát được chất lượng và tình trạng màng.');
        });
      }
      return { loi: loi, soKhoi: chiem.length,
               soThietBi: hthong ? hthong.nut.length : 0,
               soCot: hthong ? hthong.cot : 0,
               io: ioDaGan };
    }

    api2 = { hang: hang, heThong: heThong, dungCu: dungCu,
             dungCuTuIO: dungCuTuIO, ghiChu: ghiChu,
             noi: noi, noiKho: noiKho, chu: chu, ln: ln, ve: ve, kiemTra: kiemTra,
             xaNhan: xaNhan, moc: moc, MAU: MAU, W: W, H: H };
    return api2;
  }

  global.SVWSPID = { version: '1.0', to: to, MAU: MAU, rongChu: rongChu };
})(window);
