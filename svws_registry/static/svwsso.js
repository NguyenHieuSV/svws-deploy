/*!
 * SVWSSO — BA SỔ GỐC của một thiết kế: thiết bị · tuyến ống · dụng cụ đo
 * =====================================================================
 * Vì sao có thư viện này: mọi lỗi nặng đã gặp trên các bản vẽ sinh ra đều là
 * lỗi KHAI BÁO chứ không phải lỗi vẽ — thiếu bơm cấp, cụm châm hoá chất khai
 * thành bể nước, cột lọc khai 2 mà dựng 1, cụm bơm 1 chạy 1 dừng tách thành hai
 * thiết bị rồi quên đấu ống, bầu đo gắn nhầm thiết bị. Khai báo lại nằm chìm
 * trong mã JavaScript của tool nên người thiết kế không nhìn thấy, không sửa
 * được, và chỉ phát hiện khi bản vẽ đã ra sai.
 *
 * Thư viện này đưa khai báo lên thành BA CUỐN SỔ đọc được và sửa được — đúng ba
 * sổ mà một hãng thiết kế thật bàn giao:
 *
 *   1. SỔ THIẾT BỊ    (equipment list)   — có gì trong hệ
 *   2. SỔ TUYẾN ỐNG   (line list)        — nối với nhau ra sao
 *   3. SỔ DỤNG CỤ ĐO  (instrument index) — đo cái gì, ở đâu
 *
 * Mọi thứ khác SUY RA từ ba sổ này, không khai lại lần thứ hai:
 *   EQUIP + PIPES cho 3D và P&ID · danh sách tải cho tủ điện · bảng I/O cho PLC.
 * Nhờ vậy KHÔNG THỂ có động cơ trong tủ điện mà không có thiết bị trên bản vẽ,
 * và bảng I/O không thể lệch với P&ID — hai lớp lỗi đó biến mất về cấu trúc chứ
 * không phải nhờ đi kiểm sau.
 *
 * Nguyên tắc khai báo quan trọng nhất:
 *   SONG SONG / DỰ PHÒNG LÀ THUỘC TÍNH CỦA THIẾT BỊ, KHÔNG PHẢI CỦA KẾT NỐI.
 *   Hai cột lọc song song là MỘT dòng sổ thiết bị với sl=2; hai bơm 1 chạy 1
 *   dừng cũng là MỘT dòng với sl=2 và dau='duty'. Chúng dùng chung ống góp nên
 *   trên sơ đồ là một cụm, còn trong tủ điện thì tự sinh ra hai lộ.
 *
 * Dùng:
 *   const SO = SVWSSO.tao({ thietBi:[...], tuyen:[...], dungCu:[...] });
 *   console.log(SO.kiemTra());            // kiểm TRÊN SỔ, trước khi vẽ
 *   el.innerHTML = SVWSSO.CSS_TAG + SO.tatCa();
 *   const EQUIP = SO.EQUIP(), PIPES = SO.PIPES();
 *   SO.taiDien().forEach(t => DL.tai(t));
 *   SO.kenhIO().forEach(m => IO.module(m));
 */
(function (global) {
  'use strict';

  var FONT = '"IBM Plex Sans","Segoe UI",Arial,sans-serif';

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
  function so(v, m) { var n = parseFloat(v); return isFinite(n) ? n : (m || 0); }
  function gonTag(t) { return String(t || '').replace(/[-_\s.]+/g, '').toUpperCase(); }

  /* Loại thiết bị nhận biết được. Khoá là từ dùng trong sổ, giá trị là type mà
     các thư viện dựng hình đang hiểu — một chỗ đổi tên, mọi tab theo. */
  var LOAI = {
    nguon:     { type: 'nguon',     ten: 'Điểm đấu nối nước cấp', dongCo: false, dem: false },
    tank:      { type: 'tank',      ten: 'Bồn / bể chứa',        dongCo: false, dem: false },
    vessel:    { type: 'vessel',    ten: 'Cột lọc áp lực',       dongCo: false, dem: true },
    filter:    { type: 'filter',    ten: 'Thiết bị lọc',         dongCo: false, dem: true },
    mixedbed:  { type: 'mixedbed',  ten: 'Cột trao đổi ion',     dongCo: false, dem: true },
    cartridge: { type: 'cartridge', ten: 'Vỏ lọc tinh / bag',    dongCo: false, dem: true },
    pump:      { type: 'pump',      ten: 'Bơm',                  dongCo: true,  dem: true },
    dosing:    { type: 'dosing',    ten: 'Cụm châm hoá chất',    dongCo: true,  dem: true },
    roskid:    { type: 'roskid',    ten: 'Cụm màng RO',          dongCo: false, dem: false },
    edi:       { type: 'edi',       ten: 'Cụm EDI',              dongCo: false, dem: true },
    uv:        { type: 'uv',        ten: 'Đèn UV',               dongCo: false, dem: false },
    blower:    { type: 'panel',     ten: 'Máy thổi khí',         dongCo: true,  dem: true },
    panel:     { type: 'panel',     ten: 'Tủ điện',              dongCo: false, dem: false }
  };
  /* Cách đấu nối NỘI BỘ của một cụm nhiều đơn vị. */
  var DAU = {
    '':      'Đơn chiếc',
    song:    'Song song — chạy đồng thời',
    duty:    'Song song — 1 chạy 1 dự phòng',
    noitiep: 'Nối tiếp trong cụm'
  };
  var DICHVU = {
    raw: 'Nước thô / nước cấp', filtered: 'Nước sau lọc', ro: 'Nước RO',
    di: 'Nước DI / siêu tinh khiết', chem: 'Hoá chất', air: 'Khí nén',
    waste: 'Nước thải / cô đặc', steam: 'Hơi / nước nóng', drain: 'Xả đáy'
  };
  var TINHIEU = { AI: 'Analog vào', DI: 'Số vào', DO: 'Số ra', AO: 'Analog ra' };

  // =========================================================================
  function tao(o) {
    o = o || {};
    var TB = (o.thietBi || []).map(function (e, i) { return chuanTB(e, i); });
    var TU = (o.tuyen || []).map(function (e, i) { return chuanTU(e, i); });
    var DC = (o.dungCu || []).map(function (e, i) { return chuanDC(e, i); });
    var loi = [], nhac = [], loiDong = {};    // loiDong: khoá dòng → mảng lỗi

    function chuanTB(e, i) {
      var l = String(e.loai || e.type || 'tank').toLowerCase();
      return { tag: e.tag || e.id || ('EQ-' + (i + 1)), ten: e.ten || e.name || '',
               loai: LOAI[l] ? l : l, sl: Math.max(1, so(e.sl, so(e.qty, 1))),
               dau: String(e.dau || '').toLowerCase(),
               d: so(e.d, 0), h: so(e.h, 0), hLop: so(e.hLop, 0),
               kW: so(e.kW, 0), kieuDien: (e.kieuDien || '').toUpperCase(),
               vessels: so(e.vessels, 0), mangMoi: so(e.mangMoi, 0),
               soStack: so(e.soStack, 0), ghi: e.ghi || '', _i: i };
    }
    function chuanTU(e, i) {
      return { ma: e.ma || ('L-' + ('0' + (i + 1)).slice(-2)),
               tu: e.tu || e.from || '', den: e.den || e.to || '',
               congTu: e.congTu || e.fromPort || '', congDen: e.congDen || e.toPort || '',
               dv: String(e.dv || e.service || '').toLowerCase(),
               dn: so(e.dn, 0), vl: e.vl || '', ap: so(e.ap, 0),
               ghi: e.ghi || '', _i: i };
    }
    function chuanDC(e, i) {
      return { tag: e.tag || ('IT-' + (i + 1)), mo: e.mo || e.ten || '',
               gan: e.gan || e.tb || '', tin: (e.tin || 'AI').toUpperCase(),
               dai: e.dai || '', dv: e.dv || '', nguong: e.nguong || '',
               dc: e.dc || '', ghi: e.ghi || '', _i: i };
    }

    function timTB(tag) {
      var g = gonTag(tag);
      for (var i = 0; i < TB.length; i++) if (gonTag(TB[i].tag) === g) return TB[i];
      return null;
    }
    function timTU(ma) {
      var g = gonTag(ma);
      for (var i = 0; i < TU.length; i++) if (gonTag(TU[i].ma) === g) return TU[i];
      return null;
    }
    function themLoi(bang, i, t, nang) {
      var k = bang + ':' + i;
      (loiDong[k] = loiDong[k] || []).push(t);
      (nang === false ? nhac : loi).push('[' + bang + ' ' + (i + 1) + '] ' + t);
    }

    // ------------------------------------------------------------- KIỂM TRA
    /* Kiểm ngay trên SỔ, trước khi vẽ bất cứ thứ gì. Người đọc thấy dòng nào
       sai ngay trong bảng của mình, thay vì đọc một dòng lỗi dưới bản vẽ rồi
       phải tự dò ngược xem nó ứng với thiết bị nào. */
    function kiemTra() {
      loi = []; nhac = []; loiDong = {};
      var da = {};

      // --- sổ thiết bị
      TB.forEach(function (e, i) {
        if (!e.tag) themLoi('TB', i, 'Chưa có tag thiết bị.');
        var g = gonTag(e.tag);
        if (da[g]) themLoi('TB', i, 'Trùng tag với dòng ' + (da[g] + 1) + '.');
        da[g] = i;
        if (!LOAI[e.loai])
          themLoi('TB', i, 'Loại "' + e.loai + '" không có trong danh mục — ' +
                  'thư viện sẽ vẽ tạm bằng ký hiệu bồn. Dùng một trong: ' +
                  Object.keys(LOAI).join(' · '));
        var L = LOAI[e.loai] || {};
        if (e.sl > 1 && !e.dau)
          themLoi('TB', i, 'Khai ' + e.sl + ' đơn vị nhưng chưa nói đấu thế nào — ' +
                  'chọn "song" (chạy đồng thời), "duty" (1 chạy 1 dự phòng) hoặc ' +
                  '"noitiep".');
        if (e.sl > 1 && !L.dem)
          themLoi('TB', i, 'Loại này không nhân bản được theo số lượng — tách ' +
                  'thành các dòng riêng nếu thật sự có nhiều cụm.', false);
        if (L.dongCo && !e.kW)
          themLoi('TB', i, 'Là thiết bị có động cơ nhưng chưa khai kW — tủ điện ' +
                  'sẽ thiếu lộ cho nó.');
        if (!L.dongCo && e.kW)
          themLoi('TB', i, 'Khai kW nhưng loại này không có động cơ — kiểm lại ' +
                  'loại thiết bị.', false);
        if (e.kW && !e.kieuDien)
          themLoi('TB', i, 'Chưa chọn khởi động DOL hay biến tần (VFD).', false);
        if (/vessel|filter|mixedbed/.test(e.loai) && !e.d)
          themLoi('TB', i, 'Cột lọc chưa có đường kính — không tính được vận tốc lọc.');
        if (/vessel|filter/.test(e.loai) && !e.hLop)
          themLoi('TB', i, 'Chưa khai chiều cao lớp vật liệu — không tính được ' +
                  'thời gian tiếp xúc.', false);
      });

      // --- sổ tuyến ống
      var daMa = {};
      TU.forEach(function (t, i) {
        var g = gonTag(t.ma);
        if (daMa[g]) themLoi('TU', i, 'Trùng mã tuyến với dòng ' + (daMa[g] + 1) + '.');
        daMa[g] = i;
        if (!t.tu || !t.den) { themLoi('TU', i, 'Thiếu đầu đi hoặc đầu đến.'); return; }
        if (!timTB(t.tu))
          themLoi('TU', i, 'Không có thiết bị "' + t.tu + '" trong sổ thiết bị.');
        if (!timTB(t.den))
          themLoi('TU', i, 'Không có thiết bị "' + t.den + '" trong sổ thiết bị.');
        if (gonTag(t.tu) === gonTag(t.den))
          themLoi('TU', i, 'Tuyến nối thiết bị với chính nó.');
        if (!t.dv) themLoi('TU', i, 'Chưa khai dịch vụ (nước thô, sau lọc, RO, DI, ' +
                           'hoá chất, thải…) — không chọn được vật liệu và áp thử.');
        else if (!DICHVU[t.dv])
          themLoi('TU', i, 'Dịch vụ "' + t.dv + '" lạ — dùng một trong: ' +
                  Object.keys(DICHVU).join(' · '), false);
        if (!t.dn) themLoi('TU', i, 'Chưa có DN — không bóc được vật tư.');
      });

      // --- liền lạc của dây chuyền
      var vao = {}, ra = {};
      TU.forEach(function (t) {
        if (timTB(t.tu)) ra[gonTag(t.tu)] = (ra[gonTag(t.tu)] || 0) + 1;
        if (timTB(t.den)) vao[gonTag(t.den)] = (vao[gonTag(t.den)] || 0) + 1;
      });
      /* Điểm cấp nước nên khai HẲN thành một dòng loại "nguon" (mặt bích chờ
         của nhà máy). Đoán theo "thiết bị nào không có đường vào" là sai ngay
         khi bể cấp có tuyến tuần hoàn quay về — lúc đó bể có đường vào và hệ
         trông như không có nguồn nào cả. */
      var coNguon = TB.filter(function (e) { return e.loai === 'nguon'; });
      var diemCap = [];
      TB.forEach(function (e, i) {
        var g = gonTag(e.tag);
        if (e.loai === 'panel') return;                 // tủ điện không nằm trên tuyến
        if (!vao[g] && !ra[g]) {
          themLoi('TB', i, 'Không nối vào tuyến ống nào — thiếu dòng trong sổ tuyến.');
          return;
        }
        if (!vao[g]) {
          if (e.loai === 'dosing' || e.loai === 'nguon') return;
          if (coNguon.length)
            themLoi('TB', i, 'Không có đường ống vào, mà hệ đã có điểm cấp riêng (' +
                    coNguon[0].tag + ') — thiếu dòng trong sổ tuyến.');
          else diemCap.push(e.tag);
        }
        if (!ra[g] && e.loai !== 'tank' && e.loai !== 'panel')
          themLoi('TB', i, 'Chỉ có đường vào, không có đường ra — nước vào rồi đi đâu?');
      });
      if (coNguon.length > 1)
        loi.push('[Dây chuyền] Có ' + coNguon.length + ' điểm đấu nối nước cấp (' +
                 coNguon.map(function (e) { return e.tag; }).join(', ') +
                 ') — một dây chuyền chỉ nên có MỘT.');
      if (!coNguon.length && diemCap.length > 1)
        loi.push('[Dây chuyền] Có ' + diemCap.length + ' điểm cấp nước (' +
                 diemCap.join(', ') + ') — một dây chuyền chỉ nên có MỘT. Các thiết ' +
                 'bị còn lại đang thiếu đường ống vào.');
      if (!coNguon.length && !diemCap.length && TB.length)
        loi.push('[Dây chuyền] Không có điểm cấp nước nào — thêm một dòng loại ' +
                 '"nguon" (điểm đấu nối nước cấp của nhà máy) vào sổ thiết bị.');

      // --- sổ dụng cụ đo
      var daDC = {};
      DC.forEach(function (k, i) {
        var g = gonTag(k.tag);
        if (daDC[g]) themLoi('DC', i, 'Trùng tag với dòng ' + (daDC[g] + 1) + '.');
        daDC[g] = i;
        if (!TINHIEU[k.tin])
          themLoi('DC', i, 'Kiểu tín hiệu "' + k.tin + '" lạ — dùng AI · DI · DO · AO.');
        if (!k.gan) themLoi('DC', i, 'Chưa nói gắn vào đâu — điền tag thiết bị hoặc ' +
                            'mã tuyến ống.');
        else if (!timTB(k.gan) && !timTU(k.gan))
          themLoi('DC', i, 'Gắn vào "' + k.gan + '" mà không có thiết bị hay tuyến ' +
                  'nào mang tên đó.');
        if (k.tin === 'AI' && !k.dai)
          themLoi('DC', i, 'Kênh analog chưa có dải đo — không hiệu chuẩn được ở ' +
                  'mục chạy thử.', false);
      });

      // --- đối chiếu chéo: bồn phải có đo mức, cụm màng phải có đo áp hoặc độ dẫn
      TB.forEach(function (e, i) {
        // Dụng cụ nằm trên TUYẾN vào/ra của thiết bị cũng là đo cho thiết bị đó:
        // đồng hồ áp trên đường đẩy bơm cao áp chính là đo cụm màng.
        var keBen = {};
        TU.forEach(function (t) {
          if (gonTag(t.tu) === gonTag(e.tag) || gonTag(t.den) === gonTag(e.tag))
            keBen[gonTag(t.ma)] = 1;
        });
        var coGan = DC.filter(function (k) {
          return gonTag(k.gan) === gonTag(e.tag) || keBen[gonTag(k.gan)];
        });
        if (e.loai === 'tank' && !coGan.some(function (k) { return /^L/i.test(k.tag); }))
          themLoi('TB', i, 'Bồn chưa có dụng cụ đo mức — không biết khi nào bơm ' +
                  'chạy hay dừng.');
        if (/roskid|edi/.test(e.loai) &&
            !coGan.some(function (k) { return /^[PQCA]/i.test(k.tag); }))
          themLoi('TB', i, 'Cụm màng chưa có đo áp suất hoặc chất lượng nước.', false);
      });

      return { loi: loi.slice(), canhBao: nhac.slice(),
               soThietBi: TB.length, soTuyen: TU.length, soDungCu: DC.length,
               dong: loiDong };
    }

    // ------------------------------------------------------------- SUY RA
    /** Sổ thiết bị → EQUIP cho SVWS3D / SVWSPID / SVWSCHE / SVWSVT. */
    function EQUIP() {
      return TB.map(function (e) {
        var L = LOAI[e.loai] || LOAI.tank;
        var r = { id: e.tag, tag: e.tag, name: e.ten, type: L.type,
                  d: e.d || undefined, h: e.h || undefined,
                  hLop: e.hLop || undefined, ghi: e.ghi };
        // Số đơn vị đi vào đúng ô mà từng thư viện đang đọc — cụm bơm dùng
        // soBom, cụm lọc dùng qty. Khai một chỗ, các tab tự hiểu.
        if (L.type === 'pump' || L.type === 'dosing') r.soBom = e.sl;
        else if (L.dem) r.qty = e.sl;
        if (e.vessels) r.vessels = e.vessels;
        if (e.mangMoi) r.mangMoi = e.mangMoi;
        if (e.soStack) r.soStack = e.soStack;
        return r;
      });
    }
    /** Sổ tuyến → PIPES. Mã tuyến giữ nguyên để mục thử áp gọi đúng tên. */
    function PIPES() {
      return TU.map(function (t) {
        var p = { from: t.tu, to: t.den, dn: t.dn, service: t.dv, line: t.ma };
        if (t.congTu) p.fromPort = t.congTu;
        if (t.congDen) p.toPort = t.congDen;
        if (t.vl) p.vl = t.vl;
        if (t.ap) p.ap = t.ap;
        if (t.ghi) p.ghi = t.ghi;
        return p;
      });
    }
    /**
     * Sổ thiết bị → DANH SÁCH TẢI cho tủ điện. Cụm nhiều đơn vị sinh ra đúng
     * bấy nhiêu lộ (P-102A, P-102B) vì tủ có bấy nhiêu khởi động từ thật, dù
     * trên sơ đồ chúng là một cụm. Vì lộ SUY TỪ sổ thiết bị nên không thể có
     * động cơ trong tủ mà không có thiết bị trên bản vẽ.
     */
    function taiDien() {
      var ra = [];
      TB.forEach(function (e) {
        if (!e.kW) return;
        var n = Math.max(1, e.sl);
        for (var i = 0; i < n; i++) {
          ra.push({ tag: e.tag + (n > 1 ? String.fromCharCode(65 + i) : ''),
                    ten: e.ten + (n > 1 ? ' (' + (i === 0 ? 'chạy' :
                         e.dau === 'duty' ? 'dự phòng' : 'chạy') + ')' : ''),
                    kW: e.kW, kieu: e.kieuDien || 'DOL',
                    duPhong: e.dau === 'duty' && i > 0 });
        }
      });
      return ra;
    }
    /**
     * Sổ dụng cụ → BẢNG I/O của PLC, tự cấp địa chỉ theo kiểu tín hiệu.
     * Mỗi kênh mang sẵn tb = thiết bị nó gắn vào, nên P&ID không phải đoán theo
     * số vòng lặp nữa — hai bảng không thể lệch nhau vì chúng là một sổ.
     */
    function kenhIO(opt) {
      opt = opt || {};
      var dem = { DI: 0, DO: 0, AI: 0, AO: 0 };
      var goc = { DI: so(opt.DI, 0), DO: so(opt.DO, 0),
                  AI: so(opt.AI, 64), AO: so(opt.AO, 80) };
      var nhom = { DI: [], DO: [], AI: [], AO: [] };
      DC.forEach(function (k) {
        if (!nhom[k.tin]) return;
        var n = dem[k.tin]++;
        var dc = k.dc;
        if (!dc) {
          if (k.tin === 'DI') dc = 'I' + (goc.DI + Math.floor(n / 8)) + '.' + (n % 8);
          else if (k.tin === 'DO') dc = 'Q' + (goc.DO + Math.floor(n / 8)) + '.' + (n % 8);
          else if (k.tin === 'AI') dc = 'IW' + (goc.AI + n * 2);
          else dc = 'QW' + (goc.AO + n * 2);
        }
        // Dụng cụ gắn trên TUYẾN thì quy về thiết bị ở cuối tuyến — bầu đo phải
        // bám vào một ký hiệu nào đó trên sơ đồ.
        var tb = k.gan;
        var t = timTU(k.gan);
        if (t) tb = t.den || t.tu;
        nhom[k.tin].push({ dc: dc, tag: k.tag, mo: k.mo, tb: tb,
                           dai: k.dai, dv: k.dv, tin: k.nguong });
      });
      var ra = [];
      ['DI', 'AI', 'DO', 'AO'].forEach(function (t) {
        if (nhom[t].length)
          ra.push({ kieu: t, ten: TINHIEU[t] + ' (' + nhom[t].length + ' kênh)',
                    kenh: nhom[t] });
      });
      return ra;
    }

    // -------------------------------------------------------------- BẢNG
    function bang(ma, tieu, cot, dong, ghi) {
      var h = '<h4 class="svws-so-tieu">' + esc(tieu) + '</h4>';
      if (ghi) h += '<div class="svws-so-ghi">' + esc(ghi) + '</div>';
      h += '<div class="svws-so-cuon"><table class="svws-so"><thead><tr>' +
        cot.map(function (t) { return '<th>' + esc(t) + '</th>'; }).join('') +
        '<th>Kiểm</th></tr></thead><tbody>';
      dong.forEach(function (r, i) {
        var e = loiDong[ma + ':' + i] || [];
        h += '<tr class="' + (e.length ? 'svws-so-loi' : '') + '">' +
          r.map(function (c) { return '<td>' + esc(c) + '</td>'; }).join('') +
          '<td class="svws-so-nhac">' +
          (e.length ? e.map(esc).join('<br>') : '<span class="svws-so-ok">✓</span>') +
          '</td></tr>';
      });
      return h + '</tbody></table></div>';
    }

    function bangThietBi() {
      return bang('TB', '1. SỔ THIẾT BỊ — có gì trong hệ',
        ['#', 'Tag', 'Tên thiết bị', 'Loại', 'SL', 'Đấu nối trong cụm',
         'Ø (mm)', 'H (mm)', 'kW', 'Khởi động', 'Ghi chú'],
        TB.map(function (e, i) {
          return [i + 1, e.tag, e.ten, (LOAI[e.loai] || {}).ten || e.loai,
                  e.sl, DAU[e.dau] || e.dau || DAU[''],
                  e.d || '—', e.h || '—', e.kW || '—', e.kieuDien || '—', e.ghi];
        }),
        'Số lượng và cách đấu nối là thuộc tính của THIẾT BỊ, không phải của ' +
        'đường ống: hai cột lọc song song hay hai bơm 1 chạy 1 dừng đều là MỘT ' +
        'dòng ở đây, vì chúng dùng chung ống góp nên trên sơ đồ là một cụm.');
    }
    function bangTuyen() {
      return bang('TU', '2. SỔ TUYẾN ỐNG — nối với nhau ra sao',
        ['#', 'Mã tuyến', 'Từ', 'Đến', 'Dịch vụ', 'DN', 'Vật liệu',
         'Áp làm việc (bar)', 'Ghi chú'],
        TU.map(function (t, i) {
          return [i + 1, t.ma, t.tu, t.den, DICHVU[t.dv] || t.dv || '—',
                  t.dn ? 'DN' + t.dn : '—', t.vl || 'theo dịch vụ',
                  t.ap || '—', t.ghi];
        }),
        'Chiều dài, số co và số van KHÔNG khai ở đây — chúng đo từ bản vẽ 3D. ' +
        'Sổ này chỉ nói nối cái gì với cái gì, chở dịch vụ gì, cỡ bao nhiêu.');
    }
    function bangDungCu() {
      return bang('DC', '3. SỔ DỤNG CỤ ĐO — đo cái gì, ở đâu',
        ['#', 'Tag', 'Mô tả', 'Gắn vào', 'Tín hiệu', 'Dải đo', 'Đơn vị',
         'Ngưỡng / báo động', 'Ghi chú'],
        DC.map(function (k, i) {
          return [i + 1, k.tag, k.mo, k.gan, TINHIEU[k.tin] || k.tin,
                  k.dai || '—', k.dv || '—', k.nguong || '—', k.ghi];
        }),
        'Gắn vào MỘT THIẾT BỊ (đo mức bồn) hoặc MỘT TUYẾN (đo lưu lượng trên ' +
        'đường ống). Bảng I/O của PLC sinh ra từ đây và tự cấp địa chỉ, nên ' +
        'P&ID với bảng I/O không thể lệch nhau.');
    }
    function bangLoi() {
      var kt = kiemTra();
      var h = '<div class="svws-so-tt' + (kt.loi.length ? ' xau' : ' tot') + '">' +
        (kt.loi.length
          ? '✕ Còn ' + kt.loi.length + ' chỗ phải sửa trong sổ trước khi phát hành bản vẽ'
          : '✓ Ba sổ đã sạch lỗi — bản vẽ sinh ra từ đây sẽ khớp nhau') +
        (kt.canhBao.length ? '  ·  ' + kt.canhBao.length + ' khuyến nghị' : '') +
        '</div>';
      if (kt.loi.length) h += '<ul class="svws-so-ds">' +
        kt.loi.map(function (t) { return '<li>' + esc(t) + '</li>'; }).join('') + '</ul>';
      if (kt.canhBao.length) h += '<ul class="svws-so-ds nhac">' +
        kt.canhBao.map(function (t) { return '<li>' + esc(t) + '</li>'; }).join('') + '</ul>';
      return h;
    }
    function tatCa() {
      kiemTra();                       // nạp loiDong trước khi dựng bảng
      return bangLoi() + bangThietBi() + bangTuyen() + bangDungCu();
    }

    return {
      kiemTra: kiemTra, tatCa: tatCa,
      bangThietBi: bangThietBi, bangTuyen: bangTuyen, bangDungCu: bangDungCu,
      bangLoi: bangLoi,
      EQUIP: EQUIP, PIPES: PIPES, taiDien: taiDien, kenhIO: kenhIO,
      soThietBi: function () { return TB.slice(); },
      soTuyen: function () { return TU.slice(); },
      soDungCu: function () { return DC.slice(); }
    };
  }

  var CSS =
    '.svws-so{width:100%;border-collapse:collapse;font-size:11.5px;font-family:' +
    FONT + ';margin:4px 0 14px;min-width:900px}' +
    '.svws-so th{background:#0b2545;color:#fff;padding:6px 8px;text-align:left;' +
    'font-weight:600;border:1px solid #0b2545;white-space:nowrap}' +
    '.svws-so td{padding:5px 8px;border:1px solid #cfd8e3;vertical-align:top}' +
    '.svws-so tbody tr:nth-child(even){background:#f4f8fb}' +
    '.svws-so tr.svws-so-loi td{background:#fdeeec}' +
    '.svws-so-nhac{color:#b3271e;font-size:10.5px;max-width:340px}' +
    '.svws-so-ok{color:#1f9d55;font-weight:700}' +
    '.svws-so-tieu{margin:16px 0 4px;font:700 13.5px ' + FONT + ';color:#0b2545}' +
    '.svws-so-ghi{font-size:11.5px;color:#33475b;font-style:italic;margin:0 0 6px}' +
    '.svws-so-cuon{overflow-x:auto;max-width:100%}' +
    '.svws-so-tt{padding:9px 12px;border-radius:5px;font:700 12.5px ' + FONT + ';' +
    'margin:8px 0}' +
    '.svws-so-tt.tot{background:#eaf7f0;color:#12603a;border-left:4px solid #1f9d55}' +
    '.svws-so-tt.xau{background:#fdeeec;color:#8c1d16;border-left:4px solid #b3271e}' +
    '.svws-so-ds{margin:4px 0 12px 18px;font-size:11.5px;color:#8c1d16}' +
    '.svws-so-ds.nhac{color:#7a5a1e}' +
    '@media print{.svws-so-cuon{overflow:visible}.svws-so{min-width:0}}';

  global.SVWSSO = {
    version: '0.9',
    tao: tao, CSS: CSS, CSS_TAG: '<style>' + CSS + '</style>',
    LOAI: LOAI, DAU: DAU, DICHVU: DICHVU, TINHIEU: TINHIEU
  };
})(window);
