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

  /* Khung tên + logo công ty: nới viewBox thêm một dải ở dưới rồi vẽ vào đó.
     Chèn đè lên bản vẽ thì che mất thiết bị, nên phải nới. Không có SVWSKT
     (mở file rời, thiếu thư viện) thì trả nguyên bản vẽ, không vỡ. */
  function _kt(W, H, opt) {
    var K = window.SVWSKT;
    if (!K) return { H: H, g: '' };
    var c = K.cao(W);
    return { H: H + c, g: K.svg(W, H, opt || {}) };
  }


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
    var nhac = [];                // khuyến nghị: hiện cho người đọc, KHÔNG chặn
    var nhanCho = [];             // nhãn CHỜ đặt ở lượt sau (xem ve())
    var hthong = null;            // đồ thị thiết bị/đường ống khi tự xếp
    var mocLoai = {};             // tag → loại thiết bị, để chọn chỗ gắn bầu đo
    var ioDaGan = null;           // kết quả gắn bầu đo từ bảng I/O
    var dsTai = null;             // danh sách tải điện, để đối chiếu thiết bị
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
      var yy = y, xx = x, r = null, xong = false;
      // Thử hướng ưu tiên trước, hết chỗ thì hướng ngược lại; mỗi hướng còn NÉ
      // NGANG vài nấc. Chỉ đẩy theo phương đứng thì nhãn nằm giữa hai hàng thiết
      // bị hết chỗ là rơi đè lên bồn — lỗi "chữ DN40 đè lên DR-101".
      var lechX = [0, 26, -26, 52, -52];
      [uu, -uu].forEach(function (buoc) {
        if (xong) return;
        for (var q = 0; q < lechX.length && !xong; q++) {
          xx = x + lechX[q]; yy = y;
          for (var i = 0; i < 16; i++) {
            r = { x1: xx + dx - 2, y1: yy - h, x2: xx + dx + w + 2, y2: yy + 3 };
            if (coTrong(r, 2) && r.y1 > 52) { xong = true; break; }
            yy += buoc;
          }
        }
      });
      if (!xong) { xx = x; }
      x = xx;
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
      /* ĐIỂM XẢ — lối vẽ quen thuộc trên P&ID: đường ống chạy tới rồi quặt
         xuống một vạch đáy có gạch chéo, nghĩa là nước rời khỏi phạm vi bản
         vẽ. Không vẽ nó thì tuyến xả treo lơ lửng giữa tờ giấy. */
      xa: function (x, y) {
        var cx = x + 26, day = y + 34;
        ln(x, y, cx, y); ln(cx, y, cx, day);
        // muiTen() chỉ vẽ được mũi chỉ sang phải; ở đây nước đi XUỐNG.
        out.push('<path d="M' + (cx - 5) + ' ' + (day - 11) + ' L' + (cx + 5) +
          ' ' + (day - 11) + ' L' + cx + ' ' + (day - 2) + ' Z" fill="' + NAVY + '"/>');
        ln(cx - 22, day, cx + 22, day);
        for (var i = 0; i < 4; i++)
          ln(cx - 18 + i * 12, day + 10, cx - 10 + i * 12, day);
        return { w: 52, h: 92, cx: cx };
      },
      bon: function (x, y, e) {
        var w = 84, h = 92;
        out.push('<rect x="' + x + '" y="' + (y - h / 2) + '" width="' + w + '" height="' + h +
          '" rx="4" fill="#eaf4fb" stroke="' + NAVY + '" stroke-width="1.8"/>');
        out.push('<rect x="' + (x + 4) + '" y="' + (y + 6) + '" width="' + (w - 8) +
          '" height="' + (h / 2 - 10) + '" fill="#bfe0f2" opacity="0.85"/>');
        return { w: w, h: h, cx: x + w / 2 };
      },
      /* CỤM CHÂM HOÁ CHẤT — bồn pha + bơm định lượng, KHÔNG phải bồn nước.
         Trước đây dosing dùng chung ký hiệu bồn nên ba cụm châm trên bản Cụm RO
         30 m³/h trông y như ba bể nước cấp, lại còn tự mọc mũi tên "Nguồn cấp"
         vì chúng không có đường ống vào. Hoá chất đổ vào bằng tay, không có
         tuyến cấp — ký hiệu riêng và không vẽ mũi tên nguồn. */
      hoachat: function (x, y, e) {
        var w = 62, hb = 58, h = 92;
        var yb = y - h / 2;
        out.push('<rect x="' + x + '" y="' + yb + '" width="' + w + '" height="' + hb +
          '" rx="3" fill="#fdf3e2" stroke="' + MAU.chem + '" stroke-width="1.8"/>');
        out.push('<rect x="' + (x + 3) + '" y="' + (yb + hb * 0.42) + '" width="' + (w - 6) +
          '" height="' + (hb * 0.55) + '" fill="#f0d9a8" opacity="0.9"/>');
        // que khuấy
        out.push('<line x1="' + (x + w / 2) + '" y1="' + (yb - 6) + '" x2="' + (x + w / 2) +
          '" y2="' + (yb + hb * 0.75) + '" stroke="' + MAU.chem + '" stroke-width="1.4"/>');
        out.push('<line x1="' + (x + w / 2 - 9) + '" y1="' + (yb + hb * 0.75) + '" x2="' +
          (x + w / 2 + 9) + '" y2="' + (yb + hb * 0.75) + '" stroke="' + MAU.chem +
          '" stroke-width="1.4"/>');
        // bơm định lượng dưới đáy
        var cy = yb + hb + 16;
        out.push('<circle cx="' + (x + w / 2) + '" cy="' + cy + '" r="11" fill="#fff" stroke="' +
          MAU.chem + '" stroke-width="1.7"/>');
        out.push('<path d="M' + (x + w / 2 - 4) + ' ' + (cy - 5) + ' L' + (x + w / 2 + 6) +
          ' ' + cy + ' L' + (x + w / 2 - 4) + ' ' + (cy + 5) + ' Z" fill="' + MAU.chem + '"/>');
        out.push('<line x1="' + (x + w / 2) + '" y1="' + (yb + hb) + '" x2="' + (x + w / 2) +
          '" y2="' + (cy - 11) + '" stroke="' + MAU.chem + '" stroke-width="1.4"/>');
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
    /* Nhãn thiết bị trên P&ID là NHÃN, không phải chỗ chép ghi chú kỹ thuật.
       Ô "ghi" của sổ có thể dài cả đoạn — lý do chọn cỡ, luật áp dụng, việc
       còn treo — và đó là chỗ đúng để viết những thứ ấy. Nhưng đổ nguyên đoạn
       lên bản vẽ thì nhãn của ba thiết bị cạnh nhau đè lên nhau và bộ kiểm báo
       lỗi "đè nhau". Cắt ở đây: bản vẽ lấy phần đầu, sổ giữ nguyên toàn văn. */
    function nhanTB(e) {
      var g = String(e.ghi || '').replace(/\s+/g, ' ').trim();
      /* 16 ký tự. Đo hẳn trên phiếu COA-REJ (13 cột trên khổ 1900 px): cắt 40
         và 24 vẫn để MMF-101 đè ACF-101, phải xuống 18 mới hết — nên lấy 16
         cho có biên. Con số này cũng đúng bằng ví dụ mà chính thư viện nêu ở
         đầu file: "Ø1067 v=18,3 m/h". Nhãn P&ID là cỡ ống, số cụm, một con số
         vận hành; lý do chọn cỡ thì nằm ở sổ, không nằm trên bản vẽ. */
      if (g.length > 16) {
        var c = g.lastIndexOf(' ', 16);
        g = g.slice(0, c > 8 ? c : 16) + '…';
      }
      return e.tag + (g ? ' ' + g : '');
    }

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
                         s: nhanTB(e),
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
      ['nguon', 'xa', 'bon', 'hoachat', 'bom', 'cot', 'loc', 'ro', 'edi', 'uv', 'van']
        .forEach(function (t) {
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
      nguon: 'nguon', xa: 'xa',
      tank: 'bon', be: 'bon', bon: 'bon',
      vessel: 'cot', filter: 'cot', mixedbed: 'cot', cot: 'cot',
      phanung: 'cot',
      cartridge: 'loc', loc: 'loc',
      pump: 'bom', bom: 'bom', blower: 'bom',
      roskid: 'ro', ro: 'ro',
      edi: 'edi',
      uv: 'uv',
      dosing: 'hoachat', hoachat: 'hoachat', chem: 'hoachat'
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
                     s: nhanTB(e),
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

      /* NHẬN DẠNG LẠI CỤM CHÂM HOÁ CHẤT theo DỊCH VỤ ĐƯỜNG ỐNG, không tin vào
         khai báo type. Một nút không có đường vào mà mọi đường ra đều mang hoá
         chất thì đó là bồn pha hoá chất, dù AI khai nhầm là "tank". Không làm
         bước này thì mỗi cụm châm hiện lên như một bể nước cấp có mũi tên
         "Nguồn cấp" — bản Cụm RO 30 m³/h ra tới ba bể nước cấp vì lý do đó. */
      nut.forEach(function (u) {
        if (u.vao.length || !u.ra.length || u.loai === 'hoachat') return;
        var toanHC = u.ra.every(function (ci) {
          return /chem|hoa|hóa/i.test(String(canh[ci].p.service || canh[ci].p.dong || ''));
        });
        if (!toanHC) return;
        u.loai = 'hoachat';
        nhac.push('Thiết bị ' + u.id + ' khai type:"' + (u.e.type || '') +
                  '" nhưng chỉ cấp ra đường hoá chất — đang vẽ bằng ký hiệu cụm ' +
                  'châm. Sửa khai báo thành type:"dosing" cho đúng sổ thiết bị.');
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
        // Đi tới: để bộ định tuyến lo — nó kiểm ĐỦ MỌI ĐOẠN trước khi vẽ nên
        // tuyến không thể xuyên qua thiết bị nằm giữa hai cột.
        dinhTuyen(nut[c.a].e.tag, nut[c.b].e.tag, mau, nhan, 'duoi');
      });

      // ---- mũi tên nguồn cấp cho các nút không có đường vào
      var diemCap = [];
      nut.forEach(function (u) {
        if (u.vao.length) return;
        var m = moc[u.e.tag]; if (!m) return;
        var laThoiKhi = String(u.e.type || '').toLowerCase() === 'blower';
        if (u.loai !== 'hoachat' && !laThoiKhi) diemCap.push(u.id);
        /* Máy thổi khí và quạt HÚT KHÍ TRỜI. Vẽ mũi tên "Nguồn cấp" cho chúng
           là biến máy thổi khí thành một đường nước cấp thứ hai trên bản vẽ —
           cùng một lỗi với cụm châm hoá chất ở ngay dưới đây. */
        if (laThoiKhi) {
          nhanCho.push({ x: m.x + m.w / 2, y: m.y + m.h / 2 + 14,
                         s: u.e.nguon || 'Hút khí trời', fs: 7.6, mau: MO,
                         dam: 0, huong: 'duoi' });
          return;
        }
        // Cụm châm hoá chất KHÔNG có tuyến cấp — hoá chất đổ vào bồn pha bằng
        // tay. Vẽ mũi tên "Nguồn cấp" cho nó là biến cụm châm thành bể nước cấp
        // trên bản vẽ, đúng lỗi thấy trên bản Cụm RO 30 m³/h.
        if (u.loai === 'hoachat') {
          nhanCho.push({ x: m.x + m.w / 2, y: m.y + m.h / 2 + 14,
                         s: u.e.nguon || 'Pha thủ công', fs: 7.6, mau: MAU.chem,
                         dam: 0, huong: 'duoi' });
          return;
        }
        ln(m.x1 - 48, m.y, m.x1 - 10, m.y, MAU.raw, 1.8);
        muiVao(m.x1, m.y, MAU.raw);
        nhanCho.push({ x: m.x1 - 30, y: m.y - 12, s: u.e.nguon || 'Nguồn cấp',
                       fs: 8, mau: MO, dam: 0, huong: 'tren' });
      });

      /* Một dây chuyền xử lý nước có ĐÚNG MỘT điểm cấp. Nhiều mũi tên "Nguồn
         cấp" nghĩa là có thiết bị bị bỏ quên chưa đấu ống vào, chứ không phải
         hệ có nhiều nguồn — người đọc bản vẽ sẽ tưởng phải chuẩn bị mấy đường
         nước cấp. */
      if (diemCap.length > 1)
        vachao.push('Sơ đồ có ' + diemCap.length + ' điểm cấp nước (' +
                    diemCap.join(', ') + ') — một dây chuyền chỉ nên có MỘT. ' +
                    'Các thiết bị còn lại đang thiếu đường ống vào trong PIPES, ' +
                    'hoặc là cụm châm hoá chất khai nhầm loại (phải là type:"dosing").');

      // ---- ghi nhận để kiemTra() soi
      hthong = { nut: nut, canh: canh, cot: cot.length };
      return api2;
    }

    // --------------------------------------------------- bầu đo & ghi chú
    /** Bầu đo ISA gắn vào thiết bị, tự tìm phía còn trống. */
    function dungCu(tag, ten, phia) {
      var m = moc[tag];
      if (!m) { vachao.push('Không thấy thiết bị ' + tag + ' để gắn ' + ten); return; }
      // Một thiết bị thường mang vài dụng cụ (bồn có mức + nhiệt độ; skid RO có
      // áp vào, áp ra, lưu lượng, độ dẫn). Chỉ thử thẳng trên và thẳng dưới thì
      // cái thứ ba hết chỗ — phải NÉ NGANG rồi mới báo hết chỗ.
      var r = 15, thu = phia === 'duoi' ? [1, -1] : [-1, 1];
      var lech = [0, -34, 34, -68, 68];
      for (var t = 0; t < thu.length; t++) {
        for (var d = 30; d <= 112; d += 16) {
          for (var q = 0; q < lech.length; q++) {
            var cx = m.x + lech[q];
            var cy = m.y + thu[t] * (m.h / 2 + d);
            var box = { x1: cx - r - 2, y1: cy - r - 2, x2: cx + r + 2, y2: cy + r + 2 };
            if (!coTrong(box, 3)) continue;
            ln(m.x, m.y + thu[t] * m.h / 2, cx, cy - thu[t] * r, XAM, 0.9, '3 3');
            out.push('<circle cx="' + cx + '" cy="' + cy + '" r="' + r +
              '" fill="#fff" stroke="' + XAM + '" stroke-width="1.3"/>');
            out.push('<text x="' + cx + '" y="' + (cy + 3.5) + '" font-size="7.6" ' +
              'text-anchor="middle" fill="' + MO + '">' + esc(ten) + '</text>');
            themChiem(box.x1, box.y1, box.x2, box.y2, 'bầu ' + ten);
            return;
          }
        }
      }
      vachao.push('Không còn chỗ trống để đặt bầu đo ' + ten + ' cạnh ' + tag +
                  ' — nới khổ giấy (tham số h khi gọi SVWSPID.to) hoặc giãn hàng.');
    }

    /* ==================================================================
     * GẮN BẦU ĐO TỪ CHÍNH BẢNG I/O CỦA TỦ ĐIỆN
     * Mỗi kênh DI/AI là một dụng cụ đo THẬT ngoài hiện trường. Lấy thẳng từ
     * bảng I/O thì P&ID và bảng I/O không thể lệch nhau: thêm một đầu đo vào
     * PLC là bầu đo hiện lên sơ đồ, và kênh nào không gắn được vào thiết bị
     * nào sẽ bị báo lỗi thay vì lặng lẽ thiếu.
     * ================================================================ */
    // Chữ cái đầu của tag ISA → loại thiết bị hay mang dụng cụ đó
    /* So loại thiết bị phải khớp NGUYÊN TỪ. Trước đây dùng /tank|be|bon/ nên
       "mixedbed" cũng khớp (nó chứa "be") — cột trao đổi ion bị đòi phải có đo
       mức như bồn chứa, và bầu đo mức nhảy sang cột lọc. */
    var UU_TB = {
      L: ['tank'],                                        // mức: chỉ bồn bể
      T: ['tank', 'roskid', 'ro'],                        // nhiệt độ
      P: ['pump', 'cartridge', 'vessel', 'filter', 'roskid', 'ro', 'edi'],
      F: ['pump', 'roskid', 'ro', 'edi', 'tank', 'vessel'],
      A: ['roskid', 'ro', 'edi', 'mixedbed', 'tank', 'vessel'],
      C: ['roskid', 'ro', 'edi', 'mixedbed', 'tank', 'vessel'],
      Q: ['edi', 'mixedbed', 'roskid', 'ro', 'tank'],
      S: ['pump'], V: ['pump'], Z: ['pump']
    };
    var LOAI_BON = /^(tank|be|bon|bể|bồn)$/i;
    /* Loại được phép KHÔNG có đường ra: bồn chứa (nước nằm lại) và điểm xả
       (nước rời khỏi phạm vi bản vẽ). */
    var LOAI_CUOI = /^(tank|be|bon|bể|bồn|xa|drain)$/i;
    /* mocLoai lưu "tank bon" — loại thiết bị GHÉP với tên ký hiệu, cách nhau
       khoảng trắng. So cả chuỗi thì không bao giờ khớp, phải so THEO TỪ. */
    function loaiCua(t) { return ' ' + String(mocLoai[t] || '').toLowerCase() + ' '; }
    function hangLoai(t, uu) {
      var s = loaiCua(t);
      for (var i = 0; i < uu.length; i++) if (s.indexOf(' ' + uu[i] + ' ') >= 0) return i;
      return -1;
    }
    function nutCua(t) {
      if (!hthong) return null;
      for (var i = 0; i < hthong.nut.length; i++)
        if (hthong.nut[i].id === t) return hthong.nut[i];
      return null;
    }
    function noiCua(t) { var u = nutCua(t); return !!u && !!(u.vao.length + u.ra.length); }
    function capCua(t) { var u = nutCua(t); return u ? u.cap : 999; }
    function soVongLap(tag) {                  // 'LIT-101' → '101'
      var m = String(tag || '').match(/(\d{2,4})[A-Za-z]?\s*$/);
      return m ? m[1] : '';
    }

    /* Bảng I/O chứa CẢ tín hiệu trạng thái và lệnh, không chỉ dụng cụ đo:
       RUN-P101A (phản hồi bơm đang chạy), FLT (báo lỗi), ES-01 (dừng khẩn cấp),
       SEL-AUTO (chọn chế độ), PNL-DOOR (cửa tủ)… Chúng nằm trong tủ hoặc ngay
       trên động cơ, KHÔNG phải dụng cụ ngoài hiện trường — vẽ thành bầu đo trên
       P&ID là sai chuẩn ISA, làm rối sơ đồ và sinh ra một loạt cảnh báo giả. */
    var TU_TRANGTHAI = new RegExp('^(run|rn|fb|fdbk|flt|fault|loi|alm|alarm|trip|' +
      'cmd|lenh|start|stop|es|estop|sel|auto|man|hand|reset|ack|sms|door|pnl|panel|' +
      'rdy|ready|avl|remote|local|spd|speed|hz|kw|kwh|hour|hrs|ups|mcb|mccb)$', 'i');
    /* Dạng tag ISA: chữ cái BIẾN ĐO + chữ cái CHỈ THỊ, rồi tới số vòng lặp.
       FIT-100 · LIT-101 · PIT-105 · QIT-102 · PSL-105 · TIT-101 · PDT-201… */
    var DANG_ISA = /^[FLPTACQDSWMVZ][IDTRSCAEGVYQ][A-Z]{0,2}$/i;
    var DANG_SO = /^\d{2,4}[A-Z]?$/i;

    function tachTag(t) {
      return String(t || '').split(/[-_\s.]+/).filter(Boolean);
    }
    /** Kênh này có phải DỤNG CỤ ĐO thật ngoài hiện trường không. */
    function laDungCuDo(k) {
      if (k.dungCu === false || k.dungCu === true) return k.dungCu;  // tool tự quyết
      var seg = tachTag(k.tag);
      if (seg.length < 2) return false;
      if (TU_TRANGTHAI.test(seg[0])) return false;
      return DANG_ISA.test(seg[0]) && DANG_SO.test(seg[seg.length - 1]);
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
      var demGan = 0, demBo = 0, demTT = 0;
      (ds || []).forEach(function (k) {
        var kieu = String(k.kieu || '').toUpperCase();
        var doDac = kieu === 'DI' || kieu === 'AI';
        if (!doDac && !opt.caDauRa) return;
        if (!k.tag) { vachao.push('Kênh ' + (k.dc || '?') + ' chưa có tag hiện trường — ' +
                                  'không biết gắn dụng cụ vào thiết bị nào.'); return; }
        // Tín hiệu trạng thái và lệnh nằm trong tủ, không lên P&ID — bỏ qua LẶNG LẼ,
        // báo lỗi cho chúng là báo nhầm và làm người dùng bỏ qua luôn lỗi thật.
        if (!k.tb && !laDungCuDo(k)) { demTT++; return; }

        var dich = '';
        if (k.tb && moc[k.tb]) dich = k.tb;                    // khai rõ thì theo khai
        else if (k.tb) {
          vachao.push('Kênh ' + k.tag + ' khai tb:"' + k.tb + '" nhưng không có thiết bị ' +
                      'nào mang tag đó — kiểm lại danh sách EQUIP.');
          demBo++; return;
        }
        if (!dich) {
          // Tag mang thẳng tag thiết bị (LIT-TK101, PIT-RO101): so theo TỪNG ĐOẠN
          // của tag, không so kiểu chứa chuỗi — 'LIT101' chứa 'T101' sẽ khớp nhầm
          // sang bồn T-101.
          var seg = tachTag(k.tag).map(function (x) { return x.toUpperCase(); });
          for (var i2 = 0; i2 < dsTag.length && !dich; i2++) {
            var gon = dsTag[i2].replace(/[-_\s.]+/g, '').toUpperCase();
            if (seg.indexOf(gon) >= 0) dich = dsTag[i2];
          }
        }
        if (!dich) {
          var so = soVongLap(k.tag);
          if (so) {
            var chu0 = String(k.tag).charAt(0).toUpperCase();
            var uu = UU_TB[chu0] || null;
            var cung = dsTag.filter(function (t) { return soVongLap(t) === so; });
            // Xếp hạng theo HỌ THIẾT BỊ hay mang dụng cụ đó, không lấy bừa thiết bị
            // đầu tiên cùng số: bầu đo áp của bơm P-102 từng nhảy sang cột trao đổi
            // ion MB-102 vì hai cái cùng số 102.
            var hop = uu ? cung.filter(function (t) {
              return hangLoai(t, uu) >= 0;
            }) : cung;
            if (!hop.length) hop = cung;
            // Hoà hạng thì ưu tiên thiết bị THẬT SỰ nằm trên tuyến ống, rồi tới
            // cái ở đầu dòng chảy. Không có tiêu chí phụ thì bầu đo hay rơi vào
            // đúng cái bơm dự phòng chưa đấu ống — chỗ vô nghĩa nhất.
            hop.sort(function (a, b) {
              var d = (uu ? hangLoai(a, uu) - hangLoai(b, uu) : 0);
              if (d) return d;
              d = (noiCua(b) ? 1 : 0) - (noiCua(a) ? 1 : 0);
              if (d) return d;
              return capCua(a) - capCua(b);
            });
            if (hop.length) {
              dich = hop[0];
              // Còn nhiều ứng viên cùng hạng thì vẫn gắn — nhưng NHẮC, không báo
              // lỗi: số vòng lặp không đủ để biết dụng cụ nằm ở đâu trên tuyến.
              if (hop.length > 1 && hangLoai(hop[1], uu || []) === hangLoai(hop[0], uu || []))
                nhac.push('Dụng cụ ' + k.tag + ' hợp với nhiều thiết bị cùng vòng lặp ' +
                          so + ' (' + hop.join(', ') + ') — đang gắn vào ' + dich +
                          '. Khai rõ tb:"<tag thiết bị>" trong kênh I/O cho chắc.');
            }
          }
        }
        if (!dich) {
          demBo++;
          vachao.push('Dụng cụ ' + k.tag + ' (' + kieu + ' ' + (k.dc || '') + ') không ' +
                      'gắn được vào thiết bị nào trên sơ đồ. Cách sửa: đặt số vòng lặp ' +
                      'trùng với thiết bị nó đo (LIT-101 cho bồn T-101), hoặc khai rõ ' +
                      'tb:"<tag thiết bị>" trong kênh I/O.');
          return;
        }
        dungCu(dich, k.tag, opt.phia);
        (daGan[dich] = daGan[dich] || []).push(k.tag);
        demGan++;
      });
      // demTT: tín hiệu trạng thái/lệnh đã bỏ qua có chủ ý — báo ra để người
      // dùng biết P&ID không thiếu dụng cụ, chỉ là chúng không thuộc về P&ID.
      ioDaGan = { gan: demGan, bo: demBo, trangThai: demTT,
                  tong: (ds || []).length };
      return api2;
    }

    function ghiChu(tag, s, phia) {
      var m = moc[tag];
      if (!m) { vachao.push('Không thấy thiết bị ' + tag + ' để ghi chú'); return; }
      chu(m.x, m.y + (phia === 'duoi' ? 1 : -1) * (m.h / 2 + 16), s, 8, MO,
          'middle', 0, phia === 'duoi' ? 'duoi' : 'tren');
    }

    /** Nối hai thiết bị bằng đường gấp khúc VUÔNG GÓC, né mọi ký hiệu. */
    /* ==================================================================
     * ĐỊNH TUYẾN ỐNG — vuông góc và TUYỆT ĐỐI KHÔNG CẮT QUA THIẾT BỊ
     * ------------------------------------------------------------------
     * Bản cũ chỉ kiểm đoạn DỌC ở giữa, còn hai đoạn NGANG thì vẽ thẳng bất kể
     * có gì chắn. Hai thiết bị cách nhau vài cột là tuyến đi xuyên qua tất cả
     * những gì nằm giữa — đúng lỗi thấy trên bản Cụm RO 30 m³/h. Ở đây kiểm ĐỦ
     * MỌI ĐOẠN trước khi vẽ, và ghi lại đoạn đã vẽ để tuyến sau còn né.
     * Ống cắt ống là bình thường trên P&ID; ống cắt THIẾT BỊ thì không.
     * ================================================================ */
    function boxDoan(x1, y1, x2, y2) {
      return { x1: Math.min(x1, x2) - 3, y1: Math.min(y1, y2) - 3,
               x2: Math.max(x1, x2) + 3, y2: Math.max(y1, y2) + 3 };
    }
    function trongDoan(r, bq, neOng) {
      for (var i = 0; i < chiem.length; i++) {
        var c = chiem[i], t = String(c.ten || '');
        if (bq && bq.indexOf(t) >= 0) continue;        // hai đầu của chính tuyến này
        if (t.indexOf('chữ:') === 0) continue;         // nhãn vẽ sau, tự né
        if (t.indexOf('ống ') === 0 && !neOng) continue;
        if (dung(r, c, 0)) return false;
      }
      return true;
    }
    function trongCa(ds, bq, neOng) {
      for (var i = 0; i < ds.length; i++) if (!trongDoan(ds[i], bq, neOng)) return false;
      return true;
    }
    function veTuyen(diem, mau, ten) {
      var i;
      for (i = 0; i < diem.length - 1; i++)
        ln(diem[i][0], diem[i][1], diem[i + 1][0], diem[i + 1][1], mau, 1.6);
      for (i = 0; i < diem.length - 1; i++) {
        var r = boxDoan(diem[i][0], diem[i][1], diem[i + 1][0], diem[i + 1][1]);
        themChiem(r.x1, r.y1, r.x2, r.y2, 'ống ' + ten);
      }
    }
    /** Mép trên và mép dưới của TOÀN BỘ thiết bị — để chọn làn đi vòng. */
    function bienY() {
      var lo = 1e9, hi = -1e9;
      Object.keys(moc).forEach(function (t) {
        var m = moc[t];
        lo = Math.min(lo, m.y - m.h / 2); hi = Math.max(hi, m.y + m.h / 2);
      });
      return lo > hi ? { lo: 90, hi: 300 } : { lo: lo, hi: hi };
    }
    function timTuyen(a, b, bq, phiaUu, neOng) {
      var vao = b.x1 - 9, f, xm, ds;
      // 1) cùng cao độ và đoạn giữa trống → nối thẳng
      if (Math.abs(a.y - b.y) < 5 && a.x2 < vao &&
          trongCa([boxDoan(a.x2, a.y, vao, b.y)], bq, neOng))
        return [[a.x2, a.y], [vao, b.y]];
      // 2) bẻ một nhịp trong khoảng trống giữa hai thiết bị
      var gap = b.x1 - a.x2;
      if (gap > 26) {
        var moc2 = [0.5, 0.44, 0.38, 0.32, 0.26, 0.2, 0.56, 0.62, 0.68, 0.74, 0.8];
        for (var q = 0; q < moc2.length; q++) {
          f = moc2[q]; xm = a.x2 + gap * f;
          ds = [boxDoan(a.x2, a.y, xm, a.y), boxDoan(xm, a.y, xm, b.y),
                boxDoan(xm, b.y, vao, b.y)];
          if (trongCa(ds, bq, neOng))
            return [[a.x2, a.y], [xm, a.y], [xm, b.y], [vao, b.y]];
        }
      }
      // 3) đi vòng: ra khỏi thiết bị theo phương đứng, chạy trên một LÀN NGANG
      //    nằm ngoài toàn bộ khối thiết bị, rồi vào thiết bị đích theo phương đứng
      var bi = bienY();
      var thu = phiaUu === 'tren' ? [-1, 1] : [1, -1];
      for (var i = 0; i < thu.length; i++) {
        var h = thu[i];
        for (var d = 30; d <= 520; d += 13) {
          var yy = h > 0 ? bi.hi + d : bi.lo - d;
          if (yy < 56) break;
          ds = [boxDoan(a.x, a.y + h * a.h / 2, a.x, yy),
                boxDoan(a.x, yy, b.x, yy),
                boxDoan(b.x, yy, b.x, b.y + h * b.h / 2)];
          if (trongCa(ds, bq, neOng)) {
            canH = Math.max(canH, yy + 70);
            return [[a.x, a.y + h * a.h / 2], [a.x, yy], [b.x, yy],
                    [b.x, b.y + h * b.h / 2]];
          }
        }
      }
      // 4) Có thiết bị nằm ngay dưới (hoặc trên) thì tuột thẳng xuống là đâm vào
      //    nó. Ra khỏi thiết bị theo phương NGANG tới một rãnh đứng còn trống
      //    rồi mới đi xuống làn ngang. Thiếu bước này thì cột nào xếp hai ba
      //    thiết bị chồng nhau là mọi tuyến hồi lưu đều bí.
      var biY = bienY();
      for (var t3 = 0; t3 < 2; t3++) {
        var h2 = (phiaUu === 'tren' ? [-1, 1] : [1, -1])[t3];
        for (var e2 = 10; e2 <= 90; e2 += 10) {
          var xA = a.x2 + e2, xB = b.x1 - e2;
          for (var d2 = 30; d2 <= 520; d2 += 13) {
            var y2 = h2 > 0 ? biY.hi + d2 : biY.lo - d2;
            if (y2 < 56) break;
            var ds3 = [boxDoan(a.x2, a.y, xA, a.y), boxDoan(xA, a.y, xA, y2),
                       boxDoan(xA, y2, xB, y2), boxDoan(xB, y2, xB, b.y),
                       boxDoan(xB, b.y, b.x1 - 9, b.y)];
            if (trongCa(ds3, bq, neOng)) {
              canH = Math.max(canH, y2 + 70);
              return [[a.x2, a.y], [xA, a.y], [xA, y2], [xB, y2],
                      [xB, b.y], [b.x1 - 9, b.y]];
            }
          }
        }
      }
      return null;
    }
    /** Mũi tên đặt theo hướng của đoạn cuối, không mặc định nằm ngang. */
    function muiTheo(p1, p2, mau) {
      var dx = p2[0] - p1[0], dy = p2[1] - p1[1];
      if (Math.abs(dx) >= Math.abs(dy)) {
        muiVao(p2[0] + (dx >= 0 ? 9 : -9), p2[1], mau);
        return;
      }
      var s = dy >= 0 ? 1 : -1, x = p2[0], y = p2[1] + s * 9;
      out.push('<path d="M' + (x - 4.5) + ' ' + (y - s * 9) + ' L' + x + ' ' + y +
        ' L' + (x + 4.5) + ' ' + (y - s * 9) + ' Z" fill="' + (mau || NAVY) + '"/>');
    }

    function dinhTuyen(tagA, tagB, mau, nhan, phiaUu) {
      var a = moc[tagA], b = moc[tagB];
      if (!a || !b) { vachao.push('Không nối được ' + tagA + ' → ' + tagB); return; }
      var bq = [tagA, tagB];
      // Lượt 1 né cả thiết bị lẫn ống đã vẽ cho sơ đồ sạch; không được thì lượt 2
      // chấp nhận cắt ống khác — nhưng thiết bị thì không bao giờ.
      var diem = timTuyen(a, b, bq, phiaUu, true) || timTuyen(a, b, bq, phiaUu, false);
      if (!diem) {
        vachao.push('Không tìm được đường nối ' + tagA + ' → ' + tagB +
                    ' mà không cắt qua thiết bị — nới khổ vẽ (tham số h khi gọi ' +
                    'SVWSPID.to) hoặc giãn khoảng cách hàng/cột.');
        return;
      }
      veTuyen(diem, mau, tagA + '→' + tagB);
      var n = diem.length;
      muiTheo(diem[n - 2], diem[n - 1], mau);
      if (nhan) {
        var g = diem[n - 2], c = diem[n - 1];
        nhanCho.push({ x: (g[0] + c[0]) / 2, y: Math.min(g[1], c[1]) - 7, s: nhan,
                       fs: 8, mau: mau, dam: 0, huong: 'tren' });
      }
    }

    function noi(tagA, tagB, e) {
      e = e || {};
      dinhTuyen(tagA, tagB, MAU[e.dong || 'conc'] || MAU.conc, e.nhan, e.phia);
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
      var kt = _kt(W, H, { tenBV: 'P&ID — Sơ đồ công nghệ và điều khiển',
                           soBV: (o.ma || '') + '-PID-001', tyLe: 'NTS',
                           ma: o.ma, ten: o.ten });
      var dau = '<svg viewBox="0 0 ' + W + ' ' + kt.H + '" width="100%" ' +
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
      return dau + tieu + out.join('') + kt.g + '</svg>';
    }

    /** Còn chỗ nào đè nhau không — bắt lỗi trước khi giao bản vẽ. */
    /* Nguyên nhân phổ biến nhất của "thiết bị không nối vào ống nào": cụm bơm
       1 chạy 1 dừng bị khai thành HAI thiết bị P-101A và P-101B, rồi chỉ đấu
       ống cho cái A. Trên thực tế hai bơm chung một góp hút và một góp đẩy, nên
       phải khai MỘT thiết bị có soBom:2 — đúng cách mà 3D và bảng vật tư đang
       hiểu. Chỉ ra thẳng chỗ đó, đừng bắt người dùng tự đoán. */
    function goiYCum(id) {
      var g = String(id).replace(/[A-Za-z]$/, '');
      if (g === String(id)) return '';
      var anh = Object.keys(moc).filter(function (t) {
        return t !== id && t.replace(/[A-Za-z]$/, '') === g;
      });
      if (!anh.length) return '';
      return ' Có vẻ đây là cụm chạy–dự phòng cùng với ' + anh.join(', ') +
             ': khai MỘT thiết bị ' + g.replace(/-$/, '') +
             ' với soBom:' + (anh.length + 1) + ' thay vì tách thành nhiều thiết bị — ' +
             'hai bơm dùng chung góp hút và góp đẩy nên trên P&ID là một cụm.';
    }

    function kiemTra() {
      noiKho();
      xaNhan();
      var loi = vachao.slice();
      /* Phân loại chồng lấn — không phải cái nào cũng là lỗi:
         · ống × ống: hai tuyến cắt nhau là bình thường trên P&ID, bỏ qua;
         · ống × chính hai thiết bị nó nối: đó là cổ ống, bỏ qua;
         · ống × thiết bị KHÁC: đây mới là lỗi "ống cắt ngang thiết bị";
         · thiết bị × thiết bị, hoặc nhãn đè lên vật gì đó: lỗi vẽ như trước. */
      function laOng(t) { return String(t).indexOf('ống ') === 0; }
      function dauOng(t) { return String(t).slice(4).split('→'); }
      for (var i = 0; i < chiem.length; i++) {
        for (var j = i + 1; j < chiem.length; j++) {
          if (!dung(chiem[i], chiem[j], -1)) continue;
          var ta = chiem[i].ten, tb = chiem[j].ten, t;
          if (laOng(ta) && laOng(tb)) continue;
          if (laOng(ta) || laOng(tb)) {
            var o = laOng(ta) ? ta : tb, tb2 = laOng(ta) ? tb : ta;
            if (dauOng(o).indexOf(tb2) >= 0) continue;
            if (String(tb2).indexOf('chữ:') === 0) continue;   // nhãn tự né ở lượt sau
            t = 'Ống ' + String(o).slice(4) + ' cắt ngang thiết bị ' + tb2 +
                ' — nới khổ vẽ hoặc giãn khoảng cách hàng/cột.';
          } else {
            t = 'Đè nhau: ' + ta + '  ×  ' + tb;
          }
          if (loi.indexOf(t) < 0) loi.push(t);
        }
      }
      // Chế độ tự xếp: kiểm luôn tính liền lạc của dây chuyền, không chỉ kiểm vẽ.
      if (hthong) {
        hthong.nut.forEach(function (u) {
          if (!u.vao.length && !u.ra.length)
            loi.push('Thiết bị ' + u.id + ' không nối vào đường ống nào — ' +
                     'thiếu tuyến trong khai báo PIPES.' + goiYCum(u.id));
          // Bồn chứa giữ nước lại, còn điểm xả là chỗ nước RỜI KHỎI hệ — cả hai
          // đều không phải trả lời câu "nước đi đâu".
          else if (!u.ra.length && !LOAI_CUOI.test(String(u.e.type || '').toLowerCase()))
            loi.push('Thiết bị ' + u.id + ' chỉ có đường vào, không có đường ra — ' +
                     'nước vào rồi đi đâu?');
        });
        var luiSo = hthong.canh.filter(function (c) { return c.lui; }).length;
        if (luiSo > hthong.nut.length)
          loi.push('Có ' + luiSo + ' tuyến hồi lưu trên ' + hthong.nut.length +
                   ' thiết bị — kiểm lại chiều dòng chảy trong PIPES, nhiều khả năng ' +
                   'khai ngược from/to.');
      }
      // Động cơ có trong bảng điện mà không có trên sơ đồ = thiếu thiết bị.
      if (dsTai && dsTai.length) {
        var gon = {};
        Object.keys(moc).forEach(function (t) {
          gon[t.replace(/[-_\s.]+/g, '').toUpperCase()] = t;
        });
        var daNhac = {};
        dsTai.forEach(function (t) {
          var g = String(t.tag || '').replace(/[-_\s.]+/g, '').toUpperCase();
          if (!g || gon[g]) return;
          // Cụm 1 chạy 1 dừng khai một thiết bị P-101 nhưng tủ có hai lộ
          // P-101A và P-101B — bỏ hậu tố chữ rồi đối chiếu lại.
          var g2 = g.replace(/[A-Z]$/, '');
          if (gon[g2] || daNhac[g2]) return;
          daNhac[g2] = 1;
          loi.push('Động cơ ' + t.tag + (t.ten ? ' (' + t.ten + ')' : '') +
                   ' có trong bảng chọn thiết bị điện nhưng KHÔNG có trên P&ID — ' +
                   'thiếu thiết bị trong khai báo EQUIP, hoặc thừa một lộ trong ' +
                   'bảng điện. Hai bảng phải cùng một sổ thiết bị.');
        });
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
          if (LOAI_BON.test(t) && !daGanCho(tag, /^L/))
            loi.push('Bồn ' + tag + ' chưa có dụng cụ đo mức trong bảng I/O — ' +
                     'không biết khi nào bơm chạy hay dừng.');
          if (/^(ro|roskid|edi)$/.test(t) && !daGanCho(tag, /^[PA]/))
            loi.push('Cụm ' + tag + ' chưa có đo áp suất hoặc độ dẫn trong bảng I/O — ' +
                     'không giám sát được chất lượng và tình trạng màng.');
        });
      }
      return { loi: loi, canhBao: nhac.slice(), soKhoi: chiem.length,
               soThietBi: hthong ? hthong.nut.length : 0,
               soCot: hthong ? hthong.cot : 0,
               io: ioDaGan };
    }

    /* Đối chiếu P&ID với BẢNG ĐIỆN. Một động cơ có trong bảng chọn thiết bị
       điện mà không có mặt trên sơ đồ nghĩa là thiếu thiết bị trong khai báo —
       đúng lỗi "thiếu bơm cấp" trên bản Cụm RO 30 m³/h: bảng thông số ghi bơm
       cấp MMF 11 kW, tủ điện có lộ cho nó, mà P&ID thì không có cái bơm nào.
       Không đối chiếu thì chẳng ai phát hiện, vì mỗi tab đọc một sổ khác nhau. */
    function napTai(ds) { dsTai = (ds || []).slice(); return api2; }

    api2 = { hang: hang, heThong: heThong, dungCu: dungCu,
             dungCuTuIO: dungCuTuIO, napTai: napTai, ghiChu: ghiChu,
             noi: noi, noiKho: noiKho, chu: chu, ln: ln, ve: ve, kiemTra: kiemTra,
             xaNhan: xaNhan, moc: moc, MAU: MAU, W: W, H: H };
    return api2;
  }

  global.SVWSPID = { version: '1.0', to: to, MAU: MAU, rongChu: rongChu };
})(window);
