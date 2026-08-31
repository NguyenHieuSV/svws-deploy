/*!
 * SVWSGA — bộ dựng bản vẽ GA (mặt bằng bố trí) chuẩn cho tool thiết kế SVWS
 * =========================================================================
 * Điểm khác biệt quan trọng: GA dùng CHUNG bố cục với mô hình 3D. Trước đây
 * mặt bằng và 3D là hai lần AI tự đoán toạ độ độc lập nên hai bản vẽ lệch nhau;
 * nay cùng ăn một bộ vị trí từ SVWS3D.layout() và cùng một hàm chân đế
 * SVWS3D.chanDe(), nên kích thước và vị trí luôn khớp.
 *
 * Thư viện lo: chọn tỷ lệ cho vừa khổ A3, vẽ đúng tỷ lệ, đặt nhãn không đè,
 * tự sinh chuỗi kích thước theo vị trí thật, và KIỂM KHE VẬN HÀNH — chỗ này
 * bắt được lỗi thiết kế thật (thiết bị đặt sát nhau không vào bảo trì được),
 * chứ không chỉ là lỗi vẽ.
 *
 * Dùng:
 *   const pos = SVWS3D.layout(EQUIP);            // cùng bố cục với tab 3D
 *   const G = SVWSGA.to({ma:'SVWS-...', ten:'...', hoVanHanh:800});
 *   G.datCum(EQUIP, pos);
 *   G.rack('nước +300 / hồi lưu & hoá chất +900 / châm +1200');
 *   G.kichThuoc();
 *   el.innerHTML = G.ve();
 *   console.log(G.kiemTra());   // khe vận hành thiếu · nhãn đè nhau
 */
(function (global) {
  'use strict';

  var NAVY = '#0b2545', INK = '#12263a', MO = '#33475b', DO = '#c9184a';

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
  function rongChu(s, fs, dam) {
    return String(s || '').length * fs * (dam ? 0.56 : 0.52);
  }
  function so(n) {                       // 38000 → "38 000"
    return String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
  }

  function to(o) {
    o = o || {};
    var W = o.w || 420, H = o.h || 297;            // khổ A3 nằm ngang (mm giấy)
    var LE = 12, TOP = 26, DUOI = 34;              // chừa lề cho tiêu đề & kích thước
    var hoVanHanh = o.hoVanHanh || 800;            // khe vận hành tối thiểu (mm thật)
    var out = [], nhanCho = [], chiem = [], canhBao = [];
    var may = [];                                  // {id,tag,x,z,w,d,tron,D}
    var tyLe = 50, bb = null, X = null, Y = null, mm = null;

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
    function ln(x1, y1, x2, y2, mau, w, net) {
      out.push('<line x1="' + x1.toFixed(2) + '" y1="' + y1.toFixed(2) +
        '" x2="' + x2.toFixed(2) + '" y2="' + y2.toFixed(2) +
        '" stroke="' + (mau || NAVY) + '" stroke-width="' + (w || 0.7) + '"' +
        (net ? ' stroke-dasharray="' + net + '"' : '') + '/>');
    }
    /** Đặt chữ, tự đẩy cho tới khi không đè — nhãn GA cũ đè lên ký hiệu bên cạnh. */
    function chu(x, y, s, fs, mau, neo, dam, huong) {
      fs = fs || 3.4; neo = neo || 'middle';
      var w = rongChu(s, fs, dam), h = fs * 1.2;
      var dx = neo === 'middle' ? -w / 2 : neo === 'end' ? -w : 0;
      x = Math.min(W - 3 - (dx + w), Math.max(3 - dx, x));
      var uu = (huong === 'duoi' ? 1 : -1) * (fs + 1.4), yy = y, r = null, xong = false;
      [uu, -uu].forEach(function (buoc) {
        if (xong) return;
        yy = y;
        for (var i = 0; i < 18; i++) {
          r = { x1: x + dx - 0.6, y1: yy - h, x2: x + dx + w + 0.6, y2: yy + 1 };
          if (coTrong(r, 0.5) && r.y1 > TOP - 4 && r.y2 < H - 4) { xong = true; return; }
          yy += buoc;
        }
      });
      themChiem(r.x1, r.y1, r.x2, r.y2, 'chữ:' + s);
      out.push('<text x="' + x.toFixed(2) + '" y="' + yy.toFixed(2) + '" font-size="' + fs +
        '" fill="' + (mau || INK) + '" text-anchor="' + neo + '"' +
        (dam ? ' font-weight="700"' : '') +
        ' font-family="IBM Plex Sans,Arial,sans-serif">' + esc(s) + '</text>');
    }

    /** Nhận EQUIP + vị trí từ SVWS3D.layout, tự chọn tỷ lệ rồi vẽ đúng tỷ lệ. */
    function datCum(EQUIP, pos) {
      var cd = (global.SVWS3D && global.SVWS3D.chanDe) || function (e) {
        var d = +e.d || 2000; return { w: d + 160, d: d + 160, tron: true, D: d };
      };
      may = (EQUIP || []).map(function (e) {
        var f = cd(e), p = (pos && pos[e.id]) || { x: 0, z: 0 };
        return { id: e.id, tag: e.tag || e.id, ten: e.name || '',
                 x: p.x, z: p.z, w: f.w, d: f.d, tron: !!f.tron, D: f.D || f.w };
      });
      if (!may.length) { canhBao.push('Chưa có thiết bị nào để vẽ mặt bằng.'); return; }

      // hộp bao thật (mm) + chừa khe vận hành quanh cụm
      var x1 = Infinity, x2 = -Infinity, z1 = Infinity, z2 = -Infinity;
      may.forEach(function (m) {
        x1 = Math.min(x1, m.x - m.w / 2); x2 = Math.max(x2, m.x + m.w / 2);
        z1 = Math.min(z1, m.z - m.d / 2); z2 = Math.max(z2, m.z + m.d / 2);
      });
      x1 -= hoVanHanh; x2 += hoVanHanh; z1 -= hoVanHanh; z2 += hoVanHanh;
      bb = { x1: x1, x2: x2, z1: z1, z2: z2, w: x2 - x1, d: z2 - z1 };

      // chọn tỷ lệ chuẩn nhỏ nhất mà vẫn lọt khổ giấy
      var cW = W - LE * 2, cH = H - TOP - DUOI;
      var cac = [20, 25, 50, 75, 100, 150, 200, 250, 500];
      tyLe = cac[cac.length - 1];
      for (var i = 0; i < cac.length; i++) {
        if (bb.w / cac[i] <= cW && bb.d / cac[i] <= cH) { tyLe = cac[i]; break; }
      }
      mm = function (v) { return v / tyLe; };
      var ox = LE + (cW - mm(bb.w)) / 2, oy = TOP + (cH - mm(bb.d)) / 2;
      X = function (v) { return ox + mm(v - bb.x1); };
      Y = function (v) { return oy + mm(v - bb.z1); };

      // ranh khu đất
      out.push('<rect x="' + X(bb.x1).toFixed(2) + '" y="' + Y(bb.z1).toFixed(2) +
        '" width="' + mm(bb.w).toFixed(2) + '" height="' + mm(bb.d).toFixed(2) +
        '" fill="#f6f9fc" stroke="#5c677d" stroke-width="0.5" stroke-dasharray="3,2"/>');
      nhanCho.push({ x: X((bb.x1 + bb.x2) / 2), y: Y(bb.z1) - 2.5,
                     s: 'Khu đặt hệ ≈ ' + so(bb.w) + ' × ' + so(bb.d) +
                        ' mm (bệ BTCT + mương thu)', fs: 3.4, mau: MO, dam: 0, huong: 'tren' });

      // từng thiết bị, vẽ đúng tỷ lệ
      may.forEach(function (m) {
        var cx = X(m.x), cy = Y(m.z);
        if (m.tron) {
          out.push('<circle cx="' + cx.toFixed(2) + '" cy="' + cy.toFixed(2) +
            '" r="' + (mm(m.D) / 2).toFixed(2) + '" fill="#e8f2fa" stroke="' + NAVY +
            '" stroke-width="0.7"/>');
        } else {
          out.push('<rect x="' + (cx - mm(m.w) / 2).toFixed(2) + '" y="' +
            (cy - mm(m.d) / 2).toFixed(2) + '" width="' + mm(m.w).toFixed(2) +
            '" height="' + mm(m.d).toFixed(2) + '" fill="#fdf3e0" stroke="' + NAVY +
            '" stroke-width="0.7"/>');
        }
        themChiem(cx - mm(m.w) / 2, cy - mm(m.d) / 2, cx + mm(m.w) / 2, cy + mm(m.d) / 2, m.tag);
        // nhãn: đặt ở lượt sau, khi đã có đủ ký hiệu (nếu không sẽ đè lên thiết bị bên phải)
        nhanCho.push({ x: cx, y: cy - mm(m.d) / 2 - 1.5,
                       s: m.tag + (m.ten ? ' · ' + m.ten : ''),
                       fs: 3.4, mau: NAVY, dam: 1, huong: 'tren' });
      });
    }

    /** Đường giá đỡ ống chạy dọc cụm, kèm ghi chú cao độ. */
    function rack(ghi) {
      if (!bb) return;
      var y = Y(bb.z1) + 3.5;
      ln(X(bb.x1) + 2, y, X(bb.x2) - 2, y, NAVY, 1.1);
      themChiem(X(bb.x1) + 2, y - 1, X(bb.x2) - 2, y + 1, 'pipe rack');
      // Nhãn đặt NGOÀI ranh khu đất, canh trái — để giữa thì bị đẩy xuống đè
      // lên thiết bị (bộ kiểm đã bắt đúng lỗi này).
      out.push('<text x="' + (X(bb.x1) + 2).toFixed(2) + '" y="' + (Y(bb.z1) - 6.5).toFixed(2) +
        '" font-size="3.2" fill="' + MO + '" font-family="IBM Plex Sans,Arial">' +
        esc('PIPE RACK — ' + (ghi || 'nước +300 / hoá chất +900')) + '</text>');
    }

    /** Chuỗi kích thước sinh TỪ VỊ TRÍ THẬT của thiết bị, không gõ tay. */
    function kichThuoc() {
      if (!bb || !may.length) return;
      var y = Y(bb.z2) + 8;
      var sx = may.slice().sort(function (a, b) { return a.x - b.x; });
      var moc = [bb.x1];
      sx.forEach(function (m) {
        if (moc[moc.length - 1] < m.x - 1) moc.push(m.x);
      });
      moc.push(bb.x2);
      for (var i = 0; i < moc.length - 1; i++) {
        var a = X(moc[i]), b = X(moc[i + 1]);
        if (b - a < 6) continue;                    // quá hẹp thì bỏ, khỏi chồng số
        ln(a, y, b, y, DO, 0.4);
        ln(a, y - 1.4, a, y + 1.4, DO, 0.4);
        ln(b, y - 1.4, b, y + 1.4, DO, 0.4);
        out.push('<text x="' + ((a + b) / 2).toFixed(2) + '" y="' + (y - 1.2).toFixed(2) +
          '" font-size="3" fill="' + DO + '" text-anchor="middle" ' +
          'font-family="IBM Plex Sans,Arial,sans-serif">' + so(moc[i + 1] - moc[i]) + '</text>');
      }
      var yy = y + 7;
      ln(X(bb.x1), yy, X(bb.x2), yy, DO, 0.5);
      out.push('<text x="' + X((bb.x1 + bb.x2) / 2).toFixed(2) + '" y="' + (yy - 1.3).toFixed(2) +
        '" font-size="3.4" font-weight="700" fill="' + DO + '" text-anchor="middle" ' +
        'font-family="IBM Plex Sans,Arial,sans-serif">' + so(bb.w) + '</text>');
    }

    function huongBac() {
      var x = W - 22, y = TOP + 10;
      out.push('<circle cx="' + x + '" cy="' + y + '" r="7" fill="#fff" stroke="' + NAVY + '" stroke-width="0.6"/>');
      out.push('<path d="M' + x + ' ' + (y - 6) + ' L' + (x + 3) + ' ' + (y + 5) +
        ' L' + x + ' ' + (y + 2) + ' L' + (x - 3) + ' ' + (y + 5) + ' Z" fill="' + NAVY + '"/>');
      out.push('<text x="' + x + '" y="' + (y - 8.5) + '" font-size="4" font-weight="700" fill="' +
        NAVY + '" text-anchor="middle" font-family="Arial">N</text>');
    }

    function xaNhan() {
      nhanCho.forEach(function (n) { chu(n.x, n.y, n.s, n.fs, n.mau, 'middle', n.dam, n.huong); });
      nhanCho = [];
    }

    function ve() {
      xaNhan(); huongBac();
      var d = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ' + W + ' ' + H +
        '" style="width:100%;background:#fff;font-family:IBM Plex Sans,Arial">' +
        '<rect x="2" y="2" width="' + (W - 4) + '" height="' + (H - 4) +
        '" fill="none" stroke="' + NAVY + '" stroke-width="1.2"/>' +
        '<text x="10" y="13" font-size="6.5" font-weight="700" fill="' + NAVY +
        '" font-family="IBM Plex Sans,Arial">' +
        esc('GA — MẶT BẰNG BỐ TRÍ ' + (o.ma || '') + ' • Tỷ lệ 1:' + tyLe +
            ' (A3) • kích thước mm') + '</text>';
      if (o.ten) d += '<text x="10" y="21" font-size="4" fill="' + MO +
        '" font-family="IBM Plex Sans,Arial">' + esc(o.ten) + '</text>';
      return d + out.join('') + '</svg>';
    }

    /**
     * Kiểm hai thứ: nhãn còn đè nhau không, VÀ khe vận hành giữa các thiết bị
     * có đủ không. Cái sau là lỗi THIẾT KẾ chứ không phải lỗi vẽ — đặt sát quá
     * thì không có chỗ đứng bảo trì.
     */
    function kiemTra() {
      xaNhan();
      var loi = canhBao.slice(), i, j;
      for (i = 0; i < chiem.length; i++)
        for (j = i + 1; j < chiem.length; j++)
          if (dung(chiem[i], chiem[j], -0.4)) {
            var t = 'Đè nhau: ' + chiem[i].ten + '  ×  ' + chiem[j].ten;
            if (loi.indexOf(t) < 0) loi.push(t);
          }
      for (i = 0; i < may.length; i++) {
        for (j = i + 1; j < may.length; j++) {
          var a = may[i], b = may[j];
          var kx = Math.abs(a.x - b.x) - (a.w + b.w) / 2;
          var kz = Math.abs(a.z - b.z) - (a.d + b.d) / 2;
          var khe = Math.max(kx, kz);            // rời nhau theo trục nào cũng được
          if (khe < hoVanHanh) {
            loi.push('Khe vận hành ' + a.tag + ' ↔ ' + b.tag + ' chỉ ' +
                     Math.max(0, Math.round(khe)) + ' mm (cần ≥ ' + hoVanHanh + ' mm)');
          }
        }
      }
      return { loi: loi, tyLe: tyLe, khuDat: bb ? (so(bb.w) + ' × ' + so(bb.d) + ' mm') : '' };
    }

    return { datCum: datCum, rack: rack, kichThuoc: kichThuoc, huongBac: huongBac,
             ve: ve, kiemTra: kiemTra, chu: chu, ln: ln,
             get tyLe() { return tyLe; }, get khuDat() { return bb; } };
  }

  global.SVWSGA = { version: '1.0', to: to, rongChu: rongChu };
})(window);
