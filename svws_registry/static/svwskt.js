/*!
 * SVWSKT — KHUNG TÊN & LOGO dùng chung cho mọi bản vẽ, mọi tab, mọi tờ in
 * =====================================================================
 * Vì sao có thư viện này: chuẩn công ty bắt buộc mọi bản vẽ khi in phải có
 * khung tên kèm LOGO Sóng Việt, nhưng không thư viện nào cung cấp — mỗi bộ
 * dựng tự vẽ một dòng tiêu đề riêng ở góc trên trái, mỗi bộ một kiểu. Còn AI
 * thì KHÔNG THỂ tự nhúng logo: ảnh base64 của logo dài gần 19.000 ký tự, vượt
 * xa mức nó gõ được, nên nó hoặc bỏ trống, hoặc vẽ một hình vuông giả rồi ghi
 * chữ "LOGO". Kết quả là hồ sơ gửi khách không có nhận diện công ty.
 *
 * Cách làm: logo thật được server chèn vào biến window.SVWS_LOGO lúc sinh tool
 * (giống cách chèn Three.js), thư viện này đọc biến đó và dựng khung tên cho
 * CẢ HAI dạng: <g> SVG dán vào bản vẽ, và thanh HTML dán vào tab hoặc tờ in
 * bảng biểu. Đổi logo trong sổ đăng ký là mọi tool sinh sau đó đổi theo.
 *
 * Dùng tối thiểu — khai MỘT LẦN ở đầu tool:
 *   SVWSKT.dat({ duAn:'VSIP1 D10', ma:'SVWS-DIW-168', ten:'Hệ nước DI 168 m³/ngày',
 *                rev:'0', nguoiLap:'NVH', ngay:'2026-09-01' });
 * Sau đó mọi thư viện SVWS tự đóng khung tên vào bản vẽ của mình, không phải
 * gọi gì thêm. Tab và bảng in thì dán SVWSKT.html({tenBV:'…', soBV:'…'}).
 */
(function (global) {
  'use strict';

  var FONT = 'IBM Plex Sans,Segoe UI,Arial,sans-serif';
  var NAVY = '#0b2545', MO = '#5b6b7d', DO = '#b3271e', VIEN = '#94a7bb';

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  /* Thông tin pháp nhân — tên đúng theo đăng ký kinh doanh, đừng viết tắt tuỳ ý
     trên hồ sơ gửi khách. Tool có thể ghi đè bằng SVWSKT.dat(). */
  var D = {
    cty: 'CÔNG TY TNHH GIẢI PHÁP KỸ THUẬT SÓNG VIỆT',
    ctyEn: 'SONG VIET WATER SOLUTIONS CO., LTD.',
    diaChi: '',
    duAn: '', khach: '',
    ma: '', ten: '', tenEn: '',
    rev: '0', nguoiLap: '', kiemTra: '', ngay: '',
    trangThai: 'BẢN THAM KHẢO — CHƯA DUYỆT THI CÔNG',
    trangThaiEn: 'FOR REFERENCE ONLY — NOT FOR CONSTRUCTION',
    logo: '', en: false
  };

  function dat(o) {
    o = o || {};
    for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) D[k] = o[k];
    return api;
  }
  function en(v) { if (v !== undefined) D.en = !!v; return D.en; }

  /**
   * Ảnh logo dạng data URI. Ưu tiên logo tool tự khai, sau đó tới biến toàn cục
   * do server chèn. Trả chuỗi rỗng nếu không có — lúc đó dựng dấu hiệu chữ để
   * khung tên vẫn kín, không để lỗ trống hay chữ "LOGO".
   */
  function logo() {
    return D.logo || global.SVWS_LOGO || '';
  }
  function coLogo() { return !!logo(); }

  /* Tỷ lệ khung tên theo bề rộng bản vẽ: các thư viện dùng viewBox rất khác nhau
     (GA vẽ theo mm khổ A3 nên W≈420, còn sơ đồ điện W≈2000). Cùng một khối chữ
     cố định thì hoặc bé như hạt vừng, hoặc che mất nửa bản vẽ. */
  function heSo(W) {
    var k = (W || 1000) / 1000;
    return k < 0.34 ? 0.34 : k > 2.4 ? 2.4 : k;
  }
  /** Chiều cao dải khung tên cần chừa thêm dưới bản vẽ, theo bề rộng W. */
  function cao(W) { return Math.round(96 * heSo(W)); }

  function chu(x, y, t, fs, mau, dam, neo) {
    return '<text x="' + x + '" y="' + y + '" font-size="' + fs + '" fill="' + mau +
      '" font-family="' + FONT + '"' + (dam ? ' font-weight="700"' : '') +
      (neo ? ' text-anchor="' + neo + '"' : '') + '>' + esc(t) + '</text>';
  }
  function o(x, y, w, h, nen) {
    return '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h +
      '" fill="' + (nen || '#fff') + '" stroke="' + VIEN + '" stroke-width="' +
      (w > 400 ? 1.1 : 0.7) + '"/>';
  }

  /** Dấu hiệu SV vẽ bằng vector — dùng khi không có ảnh logo (mở file rời). */
  function dauSV(x, y, w, h) {
    var r = Math.min(w, h) * 0.42, cx = x + w / 2, cy = y + h / 2;
    return '<circle cx="' + cx + '" cy="' + cy + '" r="' + r + '" fill="none" stroke="' +
      NAVY + '" stroke-width="' + (r * 0.16) + '"/>' +
      '<path d="M' + (cx - r * 0.55) + ' ' + (cy + r * 0.1) +
      ' q ' + (r * 0.28) + ' ' + (-r * 0.42) + ' ' + (r * 0.55) + ' 0' +
      ' q ' + (r * 0.28) + ' ' + (r * 0.42) + ' ' + (r * 0.55) + ' 0"' +
      ' fill="none" stroke="' + DO + '" stroke-width="' + (r * 0.16) +
      '" stroke-linecap="round"/>' +
      chu(cx, cy + r * 0.78, 'SV', r * 0.62, NAVY, 1, 'middle');
  }

  /**
   * Khung tên dạng SVG — trả về một <g> vẽ trong dải cao cao(W) bắt đầu tại y.
   * Các thư viện dựng hình nới viewBox thêm đúng dải này rồi dán vào, nên khung
   * tên KHÔNG BAO GIỜ đè lên nội dung bản vẽ.
   *
   * opt: {tenBV, tenBVen, soBV, tyLe, ma, ten, duAn}
   */
  function svg(W, y, opt) {
    opt = opt || {};
    var k = heSo(W), H = cao(W);
    var x0 = Math.round(6 * k), w = W - 2 * x0;
    var h1 = Math.round(H * 0.46), h2 = H - h1 - Math.round(4 * k);
    var f1 = 13 * k, f2 = 10 * k, f3 = 8.2 * k, f4 = 7 * k;
    var yy = y + Math.round(2 * k);
    var s = '<g class="svws-kt">';

    s += '<rect x="' + x0 + '" y="' + yy + '" width="' + w + '" height="' + (h1 + h2) +
      '" fill="#ffffff" stroke="' + NAVY + '" stroke-width="' + (1.3 * k) + '"/>';

    // ---- hàng trên: logo · pháp nhân · dự án
    var wl = Math.round(h1 * 1.5);
    s += o(x0, yy, wl, h1, '#f6f9fc');
    var pad = Math.round(h1 * 0.14);
    if (coLogo()) {
      s += '<image href="' + esc(logo()) + '" xlink:href="' + esc(logo()) +
        '" x="' + (x0 + pad) + '" y="' + (yy + pad) + '" width="' + (wl - 2 * pad) +
        '" height="' + (h1 - 2 * pad) + '" preserveAspectRatio="xMidYMid meet"/>';
    } else {
      s += dauSV(x0 + pad, yy + pad, wl - 2 * pad, h1 - 2 * pad);
    }

    var wd = Math.round(w * 0.3);
    var xc = x0 + wl, wc = w - wl - wd;
    s += o(xc, yy, wc, h1);
    s += chu(xc + 6 * k, yy + h1 * 0.42, D.en ? D.ctyEn : D.cty, f1, NAVY, 1);
    s += chu(xc + 6 * k, yy + h1 * 0.72, D.en ? D.cty : D.ctyEn, f3, MO, 0);
    if (D.diaChi) s += chu(xc + 6 * k, yy + h1 * 0.93, D.diaChi, f4, MO, 0);

    var xd = xc + wc;
    s += o(xd, yy, wd, h1, '#f6f9fc');
    s += chu(xd + 6 * k, yy + h1 * 0.34, D.en ? 'PROJECT' : 'DỰ ÁN', f4, MO, 0);
    s += chu(xd + 6 * k, yy + h1 * 0.68, D.duAn || D.khach || '—', f2, NAVY, 1);
    if (D.khach && D.duAn)
      s += chu(xd + 6 * k, yy + h1 * 0.93, D.khach, f4, MO, 0);

    // ---- hàng dưới: các ô thông tin bản vẽ
    var y2 = yy + h1;
    var oS = [
      [D.en ? 'DRAWING TITLE' : 'TÊN BẢN VẼ',
       opt.tenBV || (D.en ? D.tenEn || D.ten : D.ten) || '—', 2.6],
      [D.en ? 'DRAWING No.' : 'SỐ BẢN VẼ', opt.soBV || opt.ma || D.ma || '—', 1.5],
      ['REV', D.rev || '0', 0.5],
      [D.en ? 'SCALE' : 'TỶ LỆ', opt.tyLe || 'NTS', 0.7],
      [D.en ? 'DRAWN' : 'NGƯỜI LẬP', D.nguoiLap || '—', 0.9],
      [D.en ? 'DATE' : 'NGÀY', D.ngay || '—', 0.9]
    ];
    var tong = 0, i;
    for (i = 0; i < oS.length; i++) tong += oS[i][2];
    var cx2 = x0;
    for (i = 0; i < oS.length; i++) {
      var wi = (i === oS.length - 1) ? (x0 + w - cx2) : Math.round(w * oS[i][2] / tong);
      s += o(cx2, y2, wi, h2);
      s += chu(cx2 + 5 * k, y2 + h2 * 0.36, oS[i][0], f4, MO, 0);
      s += chu(cx2 + 5 * k, y2 + h2 * 0.82, oS[i][1], f2, NAVY, 1);
      cx2 += wi;
    }

    // Trạng thái duyệt in chìm ngay trong khung tên — người cầm tờ giấy rời vẫn
    // biết đây chưa phải bản thi công, kể cả khi watermark bị ẩn để chụp màn hình.
    if (D.trangThai)
      s += '<text x="' + (x0 + w - 6 * k) + '" y="' + (yy + h1 * 0.34) +
        '" font-size="' + f4 + '" fill="' + DO + '" font-family="' + FONT +
        '" text-anchor="end" class="svws-wm">' +
        esc(D.en ? D.trangThaiEn : D.trangThai) + '</text>';
    return s + '</g>';
  }

  /**
   * Khung tên dạng HTML — cho tab trên màn hình và cho tờ in bảng biểu (BOQ,
   * O&M, chạy thử…). Cùng nội dung với khung tên SVG để hai loại tờ không nói
   * hai kiểu.
   */
  function html(opt) {
    opt = opt || {};
    var l = logo();
    var h = '<div class="svws-kt-bar">' +
      '<div class="svws-kt-logo">' +
      (l ? '<img src="' + esc(l) + '" alt="' + esc(D.cty) + '">'
         : '<svg viewBox="0 0 60 60">' + dauSV(2, 2, 56, 56) + '</svg>') +
      '</div><div class="svws-kt-cty"><b>' + esc(D.en ? D.ctyEn : D.cty) + '</b>' +
      '<span>' + esc(D.en ? D.cty : D.ctyEn) + (D.diaChi ? ' · ' + esc(D.diaChi) : '') +
      '</span></div><div class="svws-kt-o">';
    function ok(nhan, gt) {
      h += '<div><i>' + esc(nhan) + '</i><b>' + esc(gt || '—') + '</b></div>';
    }
    ok(D.en ? 'Project' : 'Dự án', D.duAn || D.khach);
    ok(D.en ? 'Drawing title' : 'Tên bản vẽ', opt.tenBV || D.ten);
    ok(D.en ? 'Drawing No.' : 'Số bản vẽ', opt.soBV || D.ma);
    ok('Rev', D.rev);
    ok(D.en ? 'Drawn' : 'Người lập', D.nguoiLap);
    ok(D.en ? 'Date' : 'Ngày', D.ngay);
    h += '</div>';
    if (D.trangThai)
      h += '<div class="svws-kt-tt svws-wm">' +
        esc(D.en ? D.trangThaiEn : D.trangThai) + '</div>';
    return h + '</div>';
  }

  /** Dải đầu trang gọn cho tab trên màn hình (chỉ logo + tên công ty + tên tab). */
  function dauTrang(tenTab) {
    var l = logo();
    return '<div class="svws-kt-dau">' +
      (l ? '<img src="' + esc(l) + '" alt="' + esc(D.cty) + '">'
         : '<svg viewBox="0 0 44 44">' + dauSV(1, 1, 42, 42) + '</svg>') +
      '<div><b>' + esc(D.en ? D.ctyEn : D.cty) + '</b>' +
      '<span>' + esc((D.ma ? D.ma + ' · ' : '') + (tenTab || D.ten || '')) +
      '</span></div></div>';
  }

  var CSS =
    // Chừa sẵn dải trên cùng cho dòng trạng thái duyệt: đặt chồng lên các ô thì
    // nó che mất tên bản vẽ — thứ người ta tìm đầu tiên khi cầm tờ giấy.
    '.svws-kt-bar{display:flex;align-items:stretch;gap:0;border:1.4px solid #0b2545;' +
    'background:#fff;margin:0 0 10px;font-family:' + FONT + ';font-size:11px;' +
    'position:relative;overflow:hidden;padding-top:14px}' +
    '.svws-kt-logo{flex:0 0 96px;display:flex;align-items:center;justify-content:center;' +
    'padding:6px;background:#f6f9fc;border-right:1px solid #94a7bb}' +
    '.svws-kt-logo img,.svws-kt-logo svg{max-width:100%;max-height:48px;display:block}' +
    '.svws-kt-cty{flex:1 1 200px;padding:7px 10px;border-right:1px solid #94a7bb;' +
    'display:flex;flex-direction:column;justify-content:center;min-width:0}' +
    '.svws-kt-cty b{color:#0b2545;font-size:12.5px;line-height:1.25}' +
    '.svws-kt-cty span{color:#5b6b7d;font-size:10px;line-height:1.3}' +
    '.svws-kt-o{flex:2 1 420px;display:flex;flex-wrap:wrap}' +
    '.svws-kt-o>div{flex:1 1 120px;padding:5px 9px;border-left:1px solid #cfd8e3;' +
    'display:flex;flex-direction:column;justify-content:center;min-width:0}' +
    '.svws-kt-o i{font-style:normal;color:#5b6b7d;font-size:8.6px;' +
    'text-transform:uppercase;letter-spacing:.04em}' +
    '.svws-kt-o b{color:#0b2545;font-size:11.5px;line-height:1.3;' +
    'overflow:hidden;text-overflow:ellipsis}' +
    '.svws-kt-tt{position:absolute;left:0;right:0;top:0;height:14px;line-height:14px;' +
    'text-align:right;padding:0 8px;box-sizing:border-box;background:#fff7f6;' +
    'border-bottom:1px solid #f0d5d2;color:#b3271e;font-size:8.8px;' +
    'font-weight:700;letter-spacing:.03em}' +
    '.svws-kt-dau{display:flex;align-items:center;gap:10px;margin:0 0 10px;' +
    'padding:6px 0;border-bottom:2px solid #b3271e;font-family:' + FONT + '}' +
    '.svws-kt-dau img,.svws-kt-dau svg{height:38px;width:auto;display:block}' +
    '.svws-kt-dau b{display:block;color:#0b2545;font-size:12.5px}' +
    '.svws-kt-dau span{display:block;color:#5b6b7d;font-size:10.5px}' +
    '@media print{.svws-kt-bar{page-break-inside:avoid}}';

  var api = {
    version: '1.0',
    dat: dat, en: en, logo: logo, coLogo: coLogo,
    svg: svg, html: html, dauTrang: dauTrang,
    cao: cao, heSo: heSo, CSS: CSS,
    CSS_TAG: '<style>' + CSS + '</style>',
    duLieu: function () { var r = {}, k; for (k in D) r[k] = D[k]; return r; }
  };
  global.SVWSKT = api;
})(window);
