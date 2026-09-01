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
    function laBom(id) {
      for (var i = 0; i < eq.length; i++) {
        if ((eq[i].id === id || eq[i].tag === id))
          return /pump|bom|bơm/i.test(String(eq[i].type || '') + ' ' + String(eq[i].tag || ''));
      }
      return false;
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
      return tuyen.map(function (t, i) {
        var k = khaiCua(t);
        var daiM = t.dai / 1000;
        var vl = k.vatLieu || vlOng;
        var buoc = buocGia(vl, t.dn);
        var soNhanh = nhanh[t.from + '|' + (k.fromPort || 'out')] || 1;
        return {
          stt: i + 1,
          from: t.from, to: t.to,
          tenFrom: tenTB(t.from), tenTo: tenTB(t.to),
          mo: 'Lắp tuyến ' + (TEN_DV[t.service] || t.service || '') +
              ' từ ' + tenTB(t.from) + ' đến ' + tenTB(t.to),
          dn: t.dn, service: t.service, vl: vl,
          dai: t.dai, daiM: lam(daiM, 2), soCo: t.soCo,
          caoNhat: t.caoNhat,
          soGia: Math.max(2, Math.ceil(t.dai / buoc)),
          buocGia: buoc,
          soTe: soNhanh > 1 ? 1 : 0,
          coMotChieu: laBom(t.from),
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
      if (c.van) ds.push({ vt: 'Van chặn (bi/bướm)', qc: 'DN' + c.dn, sl: c.van,
                           dv: 'cái', ghi: 'Cô lập để bảo trì' });
      if (c.coMotChieu) ds.push({ vt: 'Van một chiều', qc: 'DN' + c.dn, sl: 1, dv: 'cái',
                                  ghi: 'Đầu đẩy bơm — chống chảy ngược' });
      // Mặt bích: 2 đầu nối thiết bị + 2 cho mỗi van (tháo được để bảo trì)
      var soBich = 2 + 2 * (c.van + (c.coMotChieu ? 1 : 0));
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

    function bangCongDoan() {
      var cd = congDoan(), tq = tongQuan();
      var h = '<div class="svws-tq">Tổng ' + tq.soCongDoan + ' công đoạn · ' +
        tq.tongDaiM + ' m ống đo trên tuyến 3D · ' + tq.tongCo + ' co 90° · ' +
        tq.tongGia + ' giá đỡ · cao trình rack ' + tq.caoRack + ' mm</div>';
      cd.forEach(function (c) {
        h += '<h4 class="svws-bang-tieu">Công đoạn ' + c.stt + ': ' + esc(c.tenFrom) +
          ' → ' + esc(c.tenTo) + '</h4>' +
          '<div class="svws-ghi">' + esc(c.mo) + ' · DN' + c.dn + ' · dài ' + c.daiM +
          ' m · ' + c.soCo + ' co 90° · cao trình ' + c.caoNhat + ' mm</div>' +
          bangHTML('', ['Vật tư', 'Quy cách', 'SL', 'ĐVT', 'Căn cứ tính'],
            bom(c).map(function (b) { return [b.vt, b.qc, b.sl, b.dv, b.ghi]; }));
      });
      var m = mong(), d = dien();
      if (m.length) h += bangHTML('Công đoạn: Móng & bệ thiết bị',
        ['Vật tư', 'Quy cách', 'SL', 'ĐVT', 'Căn cứ tính'],
        m.map(function (b) { return [b.vt, b.qc, b.sl, b.dv, b.ghi]; }));
      if (d.length) h += bangHTML('Công đoạn: Điện & tín hiệu điều khiển',
        ['Vật tư', 'Quy cách', 'SL', 'ĐVT', 'Căn cứ tính'],
        d.map(function (b) { return [b.vt, b.qc, b.sl, b.dv, b.ghi]; }));
      return h;
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
      return { loi: loi, canhBao: canhBao, tongQuan: tq };
    }

    api.congDoan = congDoan;
    api.bom = bom;
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
    'font:600 12.5px ' + FONT + ';color:#0b2545;margin:8px 0 14px}';

  global.SVWSVT = { version: '1.0', to: to, buocGia: buocGia, daiCay: daiCay, CSS: CSS };
})(window);
