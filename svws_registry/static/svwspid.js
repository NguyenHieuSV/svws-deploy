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
    var out = [];                 // các mẩu SVG
    var chiem = [];               // hộp đã chiếm chỗ: {x1,y1,x2,y2,ten}
    var moc = {};                 // tag → {x,y,w,h} để nối và gắn bầu đo
    var vachao = [];              // các va chạm còn lại sau khi đã né
    var nhanCho = [];             // nhãn CHỜ đặt ở lượt sau (xem ve())

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
      bom: function (x, y, e) {
        var r = 13, dup = !!e.dup;
        function mot(yy) {
          out.push('<circle cx="' + (x + r) + '" cy="' + yy + '" r="' + r +
            '" fill="#fff" stroke="' + NAVY + '" stroke-width="1.8"/>');
          out.push('<path d="M' + (x + r - 5) + ' ' + (yy - 6) + ' L' + (x + r + 7) +
            ' ' + yy + ' L' + (x + r - 5) + ' ' + (yy + 6) + ' Z" fill="' + NAVY + '"/>');
        }
        if (dup) { mot(y - 20); mot(y + 20); } else mot(y);
        return { w: r * 2 + 8, h: dup ? 66 : 30, cx: x + r };
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
          nhanCho.push({ x: k.cx, y: y - k.h / 2 - 8,
                         s: e.tag + (e.ghi ? ' ' + e.ghi : ''),
                         fs: 9, mau: INK, dam: 1, huong: 'tren' });
        } else if (e.nhan) {
          nhanCho.push({ x: k.cx, y: y - 16, s: e.nhan, fs: 9, mau: MO,
                         dam: 0, huong: 'tren' });
        }
        truoc = { x2: x + k.w };
        x += k.w + (opt.hoHang || 30);    // ← NHẢY THEO BỀ RỘNG THẬT, không phải hằng số
        return api;
      }
      ['nguon', 'bon', 'bom', 'cot', 'loc', 'ro', 'uv', 'van'].forEach(function (t) {
        api[t] = function (e) { return dat(t, e); };
      });
      api.cuoi = function () { return x; };
      api.y = y;
      return api;
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
    /** Vẽ hết nhãn đang chờ — gọi khi mọi ký hiệu đã có mặt trong 'chiem'. */
    function xaNhan() {
      nhanCho.forEach(function (n) {
        chu(n.x, n.y, n.s, n.fs, n.mau, 'middle', n.dam, n.huong);
      });
      nhanCho = [];
    }

    function ve() {
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
      return { loi: loi, soKhoi: chiem.length };
    }

    return { hang: hang, dungCu: dungCu, ghiChu: ghiChu, noi: noi,
             chu: chu, ln: ln, ve: ve, kiemTra: kiemTra, xaNhan: xaNhan,
             moc: moc, MAU: MAU, W: W, H: H };
  }

  global.SVWSPID = { version: '1.0', to: to, MAU: MAU, rongChu: rongChu };
})(window);
