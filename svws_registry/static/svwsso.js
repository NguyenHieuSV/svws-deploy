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
    var TB, TU, DC;
    var loi = [], nhac = [], loiDong = {};    // loiDong: khoá dòng → mảng lỗi
    var suaDuoc = !!o.suaDuoc;                // cho sửa ngay trong bảng?
    var khiDoi = typeof o.khiDoi === 'function' ? o.khiDoi : null;
    var cho = null;                           // phần tử đang chứa ba bảng
    var hen = null;                           // hẹn giờ gọi khiDoi
    var api = null;

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
    TB = (o.thietBi || []).map(function (e, i) { return chuanTB(e, i); });
    TU = (o.tuyen || []).map(function (e, i) { return chuanTU(e, i); });
    DC = (o.dungCu || []).map(function (e, i) { return chuanDC(e, i); });

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
    /**
     * ĐIỂM CHÂM: tuyến hoá chất nối vào MỘT TUYẾN ỐNG khác, không phải vào một
     * thiết bị. Ngoài hiện trường đây là chuyện thường — antiscalant châm vào
     * đường ống ngay trước bơm cao áp, SBS châm vào đường sau lọc. Bắt phải nối
     * vào thiết bị là ép người vẽ khai sai vị trí thật của điểm châm.
     */
    function diemCham(t) {
      if (String(t.dv || '').toLowerCase() !== 'chem') return null;
      var d = timTU(t.den);
      return (d && d !== t && String(d.dv || '').toLowerCase() !== 'chem') ? d : null;
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
          themLoi('TU', i, 'Không có thiết bị "' + t.tu + '" trong sổ thiết bị — ' +
                  'sửa ô "Từ" của dòng này, hoặc thêm thiết bị đó vào sổ 1.');
        if (!timTB(t.den) && !diemCham(t))
          themLoi('TU', i, 'Không có thiết bị "' + t.den + '" trong sổ thiết bị — ' +
                  'sửa ô "Đến" của dòng này. Nếu đây là ĐIỂM CHÂM vào một tuyến ' +
                  'ống thì dịch vụ của dòng phải là "Hoá chất" và ô "Đến" điền ' +
                  'MÃ TUYẾN có thật (ví dụ L-03).');
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
        // Điểm châm tính là một đường vào của thiết bị ở CUỐI tuyến bị châm —
        // hoá chất đi cùng dòng nước vào đúng thiết bị đó.
        var dch = diemCham(t);
        var den = dch ? dch.den : t.den;
        if (timTB(den)) vao[gonTag(den)] = (vao[gonTag(den)] || 0) + 1;
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
        // Điểm châm quy về thiết bị cuối tuyến bị châm: trên bản vẽ, hoá chất
        // vào cùng chỗ với dòng nước nó châm vào, và ghi rõ châm ở tuyến nào.
        var dch = diemCham(t);
        var p = { from: t.tu, to: dch ? dch.den : t.den,
                  dn: t.dn, service: t.dv, line: t.ma };
        if (dch) p.ghi = 'Điểm châm trên tuyến ' + dch.ma +
                         (t.ghi ? ' · ' + t.ghi : '');
        if (t.congTu) p.fromPort = t.congTu;
        if (t.congDen) p.toPort = t.congDen;
        if (t.vl) p.vl = t.vl;
        if (t.ap) p.ap = t.ap;
        else if (t.ghi) p.ghi = t.ghi;
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
    /* Mỗi sổ khai bằng một BẢNG CỘT: khoá dữ liệu, nhãn, kiểu ô. Nhờ có bảng
       cột nên phần dựng ô đọc và phần dựng ô SỬA dùng chung một nguồn — thêm
       một trường thì cả hai chế độ tự có, không phải nhớ sửa hai chỗ. */
    function chonTu(bang2) {
      var r = [['', '—']];
      Object.keys(bang2).forEach(function (k) { if (k) r.push([k, bang2[k]]); });
      return r;
    }
    var COT = {
      TB: [
        { k: 'tag', t: 'Tag', kieu: 'chu', r: 96 },
        { k: 'ten', t: 'Tên thiết bị', kieu: 'chu', r: 178 },
        { k: 'loai', t: 'Loại', kieu: 'chon', r: 152, chon: function () {
            return Object.keys(LOAI).map(function (k) { return [k, LOAI[k].ten]; }); } },
        { k: 'sl', t: 'SL', kieu: 'so', r: 46, min: 1 },
        { k: 'dau', t: 'Đấu nối trong cụm', kieu: 'chon', r: 166, chon: function () {
            return Object.keys(DAU).map(function (k) { return [k, DAU[k]]; }); } },
        { k: 'd', t: 'Ø (mm)', kieu: 'so', r: 68 },
        { k: 'h', t: 'H (mm)', kieu: 'so', r: 68 },
        { k: 'hLop', t: 'Cao lớp VL', kieu: 'so', r: 74 },
        { k: 'kW', t: 'kW', kieu: 'so', r: 56 },
        { k: 'kieuDien', t: 'Khởi động', kieu: 'chon', r: 92, chon: function () {
            return [['', '—'], ['DOL', 'DOL'], ['VFD', 'VFD']]; } },
        { k: 'ghi', t: 'Ghi chú', kieu: 'chu', r: 138 }
      ],
      TU: [
        { k: 'ma', t: 'Mã tuyến', kieu: 'chu', r: 84 },
        { k: 'tu', t: 'Từ', kieu: 'goi', ds: 'tb', r: 108 },
        { k: 'den', t: 'Đến', kieu: 'goi', ds: 'gan', r: 108 },
        { k: 'dv', t: 'Dịch vụ', kieu: 'chon', r: 162, chon: function () {
            return chonTu(DICHVU); } },
        { k: 'dn', t: 'DN', kieu: 'so', r: 56 },
        { k: 'vl', t: 'Vật liệu', kieu: 'chu', r: 128 },
        { k: 'ap', t: 'Áp (bar)', kieu: 'so', r: 72 },
        { k: 'ghi', t: 'Ghi chú', kieu: 'chu', r: 170 }
      ],
      DC: [
        { k: 'tag', t: 'Tag', kieu: 'chu', r: 92 },
        { k: 'mo', t: 'Mô tả', kieu: 'chu', r: 208 },
        { k: 'gan', t: 'Gắn vào', kieu: 'goi', ds: 'gan', r: 104 },
        { k: 'tin', t: 'Tín hiệu', kieu: 'chon', r: 128, chon: function () {
            return Object.keys(TINHIEU).map(function (k) { return [k, k + ' — ' + TINHIEU[k]]; }); } },
        { k: 'dai', t: 'Dải đo', kieu: 'chu', r: 88 },
        { k: 'dv', t: 'Đơn vị', kieu: 'chu', r: 64 },
        { k: 'nguong', t: 'Ngưỡng / báo động', kieu: 'chu', r: 172 },
        { k: 'ghi', t: 'Ghi chú', kieu: 'chu', r: 120 }
      ]
    };
    var SO_BANG = { TB: function () { return TB; }, TU: function () { return TU; },
                    DC: function () { return DC; } };
    var MAU_DONG = {
      TB: function () { return chuanTB({ loai: 'tank' }, TB.length); },
      TU: function () { return chuanTU({}, TU.length); },
      DC: function () { return chuanDC({ tin: 'AI' }, DC.length); }
    };

    /* Hiển thị giá trị ở chế độ ĐỌC — cùng dữ liệu, khác cách trình bày. */
    function doc(bang2, e, c) {
      var v = e[c.k];
      if (c.k === 'loai') return (LOAI[v] || {}).ten || v;
      if (c.k === 'dau') return DAU[v] || v || DAU[''];
      if (c.k === 'dv' && bang2 === 'TU') return DICHVU[v] || v || '—';
      if (c.k === 'tin') return TINHIEU[v] || v;
      if (c.k === 'dn') return v ? 'DN' + v : '—';
      if (c.kieu === 'so') return v || '—';
      return v === '' || v == null ? '—' : v;
    }

    /* Bề rộng đặt ở colgroup chứ không đặt trên từng ô: đặt trên ô thì mỗi dòng
       tự quyết một kiểu, cột nhảy qua nhảy lại khi gõ. */
    function oSua(bang2, i, c, e) {
      var neo = ' data-b="' + bang2 + '" data-i="' + i + '" data-k="' + c.k + '"';
      var rong = '';
      if (c.kieu === 'chon') {
        var ds = c.chon(), cur = String(e[c.k] == null ? '' : e[c.k]);
        return '<select class="svws-so-o"' + neo + rong + '>' +
          ds.map(function (x) {
            return '<option value="' + esc(x[0]) + '"' +
              (String(x[0]) === cur ? ' selected' : '') + '>' + esc(x[1]) + '</option>';
          }).join('') + '</select>';
      }
      if (c.kieu === 'goi')
        return '<input class="svws-so-o" list="svws-ds-' + c.ds + '"' + neo + rong +
          ' value="' + esc(e[c.k]) + '">';
      if (c.kieu === 'so')
        return '<input class="svws-so-o so" type="number" step="any"' +
          (c.min != null ? ' min="' + c.min + '"' : '') + neo + rong +
          ' value="' + (e[c.k] ? esc(e[c.k]) : '') + '">';
      return '<input class="svws-so-o"' + neo + rong + ' value="' + esc(e[c.k]) + '">';
    }

    /** Danh sách gợi ý cho ô "Từ / Đến" và "Gắn vào" — chống gõ sai tag. */
    function dsGoiY() {
      var tb = TB.map(function (e) { return e.tag; });
      var tu = TU.map(function (t) { return t.ma; });
      function ds(id, arr) {
        return '<datalist id="svws-ds-' + id + '">' + arr.map(function (v) {
          return '<option value="' + esc(v) + '"></option>';
        }).join('') + '</datalist>';
      }
      return ds('tb', tb) + ds('gan', tb.concat(tu));
    }

    function oKiem(bang2, i) {
      var e = loiDong[bang2 + ':' + i] || [];
      return '<td class="svws-so-nhac">' +
        (e.length ? e.map(esc).join('<br>') : '<span class="svws-so-ok">✓</span>') +
        '</td>';
    }

    function bang(ma, tieu, ghi) {
      var cot = COT[ma], ds = SO_BANG[ma]();
      var h = '<h4 class="svws-so-tieu">' + esc(tieu) + '</h4>';
      if (ghi) h += '<div class="svws-so-ghi">' + esc(ghi) + '</div>';
      var wKiem = suaDuoc ? 210 : 260;
      var tong = 38 + wKiem + (suaDuoc ? 34 : 0);
      cot.forEach(function (c) { tong += (c.r || 110); });
      h += '<div class="svws-so-cuon" data-bang="' + ma + '">' +
        '<table class="svws-so" style="min-width:' + tong + 'px">' +
        '<colgroup><col style="width:38px">' +
        cot.map(function (c) {
          return '<col style="width:' + (c.r || 110) + 'px">';
        }).join('') + '<col style="width:' + wKiem + 'px">' +
        (suaDuoc ? '<col style="width:34px">' : '') + '</colgroup>' +
        '<thead><tr><th>#</th>' +
        cot.map(function (c) {
          return '<th' + (c.kieu === 'so' ? ' class="p"' : '') + '>' + esc(c.t) + '</th>';
        }).join('') +
        '<th>Kiểm</th>' + (suaDuoc ? '<th></th>' : '') + '</tr></thead><tbody>';
      ds.forEach(function (e, i) {
        var xau = (loiDong[ma + ':' + i] || []).length;
        h += '<tr class="' + (xau ? 'svws-so-loi' : '') + '" data-b="' + ma +
          '" data-i="' + i + '"><td>' + (i + 1) + '</td>' +
          cot.map(function (c) {
            var lop = (c.k === 'tag' || c.k === 'ma' ? ' class="ma"' :
                       c.kieu === 'so' ? ' class="p"' : '');
            return '<td' + lop + '>' +
              (suaDuoc ? oSua(ma, i, c, e) : esc(doc(ma, e, c))) + '</td>';
          }).join('') + oKiem(ma, i) +
          (suaDuoc ? '<td><button type="button" class="svws-so-xoa" data-b="' + ma +
            '" data-i="' + i + '" title="Xoá dòng này">✕</button></td>' : '') +
          '</tr>';
      });
      h += '</tbody></table></div>';
      if (suaDuoc) h += '<div class="svws-so-nut"><button type="button" ' +
        'class="svws-so-them" data-b="' + ma + '">+ Thêm dòng</button>' +
        '<span>' + ds.length + ' dòng</span></div>';
      return h;
    }

    function bangThietBi() {
      return bang('TB', '1. SỔ THIẾT BỊ — có gì trong hệ',
        'Số lượng và cách đấu nối là thuộc tính của THIẾT BỊ, không phải của ' +
        'đường ống: hai cột lọc song song hay hai bơm 1 chạy 1 dừng đều là MỘT ' +
        'dòng ở đây, vì chúng dùng chung ống góp nên trên sơ đồ là một cụm.');
    }
    function bangTuyen() {
      return bang('TU', '2. SỔ TUYẾN ỐNG — nối với nhau ra sao',
        'Chiều dài, số co và số van KHÔNG khai ở đây — chúng đo từ bản vẽ 3D. ' +
        'Sổ này chỉ nói nối cái gì với cái gì, chở dịch vụ gì, cỡ bao nhiêu.');
    }
    function bangDungCu() {
      return bang('DC', '3. SỔ DỤNG CỤ ĐO — đo cái gì, ở đâu',
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
      return (suaDuoc ? dsGoiY() : '') +
        bangLoi() + bangThietBi() + bangTuyen() + bangDungCu();
    }

    // ------------------------------------------------------- SỬA TẠI CHỖ
    /* Ba sổ chỉ có ích khi sửa được ngay trong tool. Nguyên tắc dựng lại:
       gõ trong ô thì CHỈ vẽ lại cột "Kiểm" và màu dòng — dựng lại cả bảng sau
       mỗi phím là mất con trỏ, không gõ nổi. Thêm/xoá dòng mới dựng lại bảng.
       Bản vẽ thì hẹn một nhịp rồi mới vẽ lại, vì dựng 3D tốn thời gian hơn
       nhiều so với một lần gõ phím. */
    function baoDoi(ngay) {
      if (!khiDoi) return;
      if (hen) { clearTimeout(hen); hen = null; }
      if (ngay) { khiDoi(api); return; }
      hen = setTimeout(function () { hen = null; khiDoi(api); }, 300);
    }

    /** Vẽ lại cột Kiểm và màu dòng, giữ nguyên con trỏ đang gõ. */
    function veLaiKiem() {
      if (!cho) return;
      kiemTra();
      ['TB', 'TU', 'DC'].forEach(function (b) {
        var ds = cho.querySelectorAll('tr[data-b="' + b + '"]');
        for (var i = 0; i < ds.length; i++) {
          var tr = ds[i], j = +tr.getAttribute('data-i');
          var e = loiDong[b + ':' + j] || [];
          tr.className = e.length ? 'svws-so-loi' : '';
          var o2 = tr.querySelector('.svws-so-nhac');
          if (o2) o2.innerHTML = e.length ? e.map(esc).join('<br>')
                                          : '<span class="svws-so-ok">✓</span>';
        }
      });
      var tt = cho.querySelector('.svws-so-tt');
      if (tt) { var m = document.createElement('div'); m.innerHTML = bangLoi();
                tt.parentNode.replaceChild(m.firstChild, tt); }
      capNhatDs();
    }
    /** Cập nhật danh sách gợi ý sau khi tag thiết bị hoặc mã tuyến đổi. */
    function capNhatDs() {
      if (!cho) return;
      var m = document.createElement('div');
      m.innerHTML = dsGoiY();
      ['tb', 'gan'].forEach(function (id) {
        var cu = cho.querySelector('#svws-ds-' + id);
        var moi2 = m.querySelector('#svws-ds-' + id);
        if (cu && moi2) cu.parentNode.replaceChild(moi2, cu);
      });
    }
    /** Dựng lại toàn bộ ba bảng — dùng khi thêm hoặc xoá dòng. */
    function veLai() {
      if (!cho) return;
      cho.innerHTML = tatCa();
      baoDoi(true);
    }

    function datGiaTri(b, i, k, v) {
      var ds = SO_BANG[b](), e = ds[i];
      if (!e) return;
      var cot = COT[b], c = null;
      cot.forEach(function (x) { if (x.k === k) c = x; });
      if (!c) return;
      e[k] = c.kieu === 'so' ? so(v, 0) : String(v);
      if (k === 'sl') e.sl = Math.max(1, so(v, 1));
      if (k === 'kieuDien') e.kieuDien = String(v).toUpperCase();
      if (k === 'tin') e.tin = String(v).toUpperCase();
      if (k === 'dv' && b === 'TU') e.dv = String(v).toLowerCase();
    }

    /**
     * Gắn ba sổ vào một phần tử và bật chế độ sửa.
     * el: phần tử chứa · khiDoi được gọi sau mỗi thay đổi (đã hẹn nhịp).
     */
    function gan(el) {
      // Tự nhúng CSS của chính mình. Để người gọi tự nhớ thì sớm muộn cũng có
      // chỗ quên — và quên thì bảng ra bảng HTML trần: cột giãn theo chữ dài
      // nhất, tràn ngang, nhìn như một rừng ô nhập liệu. Đã dính đúng lỗi đó.
      if (global.document && !document.getElementById('svwsso-css')) {
        var st = document.createElement('style');
        st.id = 'svwsso-css';
        st.textContent = CSS;
        document.head.appendChild(st);
      }
      cho = el;
      el.innerHTML = tatCa();
      if (!suaDuoc) return api;
      el.addEventListener('input', function (ev) {
        var t = ev.target;
        if (!t || !t.getAttribute || !t.getAttribute('data-k')) return;
        datGiaTri(t.getAttribute('data-b'), +t.getAttribute('data-i'),
                  t.getAttribute('data-k'), t.value);
        veLaiKiem();
        baoDoi(false);
      });
      el.addEventListener('change', function (ev) {
        var t = ev.target;
        if (!t || !t.getAttribute || !t.getAttribute('data-k')) return;
        baoDoi(true);
      });
      el.addEventListener('click', function (ev) {
        var t = ev.target;
        if (!t || !t.className) return;
        if (String(t.className).indexOf('svws-so-them') >= 0) {
          var b = t.getAttribute('data-b');
          SO_BANG[b]().push(MAU_DONG[b]());
          veLai();
        } else if (String(t.className).indexOf('svws-so-xoa') >= 0) {
          var b2 = t.getAttribute('data-b'), i2 = +t.getAttribute('data-i');
          SO_BANG[b2]().splice(i2, 1);
          veLai();
        }
      });
      return api;
    }

    /** Ba sổ dạng dữ liệu thuần — để lưu vào file cấu hình JSON. */
    function xuat() {
      function gon(x) {
        var r = {}, k;
        for (k in x) if (x.hasOwnProperty(k) && k.charAt(0) !== '_' &&
                         x[k] !== '' && x[k] !== 0) r[k] = x[k];
        return r;
      }
      return { thietBi: TB.map(gon), tuyen: TU.map(gon), dungCu: DC.map(gon) };
    }
    /** Nạp lại ba sổ từ dữ liệu (mở file JSON) và vẽ lại. */
    function nap(dat) {
      dat = dat || {};
      TB = (dat.thietBi || []).map(function (e, i) { return chuanTB(e, i); });
      TU = (dat.tuyen || []).map(function (e, i) { return chuanTU(e, i); });
      DC = (dat.dungCu || []).map(function (e, i) { return chuanDC(e, i); });
      veLai();
      return api;
    }

    api = {
      kiemTra: kiemTra, tatCa: tatCa, gan: gan, veLai: veLai,
      xuat: xuat, nap: nap,
      bangThietBi: bangThietBi, bangTuyen: bangTuyen, bangDungCu: bangDungCu,
      bangLoi: bangLoi,
      EQUIP: EQUIP, PIPES: PIPES, taiDien: taiDien, kenhIO: kenhIO,
      soThietBi: function () { return TB.slice(); },
      soTuyen: function () { return TU.slice(); },
      soDungCu: function () { return DC.slice(); }
    };
    return api;
  }

  var CSS =
    /* Trình bày như một CUỐN SỔ kỹ thuật: tiêu đề dính khi cuộn, số căn phải
       và cùng bề ngang chữ số, ô nhập chỉ hiện viền khi cần — nhìn vào là đọc
       được ngay, không phải một rừng khung nhập liệu. */
    '.svws-so{border-collapse:collapse;width:100%;font-size:12.5px;font-family:' +
    FONT + ';margin:2px 0 10px;font-variant-numeric:tabular-nums;table-layout:fixed}' +
    '.svws-so th{background:#0b2545;color:#fff;padding:7px 9px;text-align:left;' +
    'font-weight:600;font-size:10.5px;letter-spacing:.05em;text-transform:uppercase;' +
    'white-space:nowrap;position:sticky;top:0;z-index:2}' +
    '.svws-so th.p{text-align:right}' +
    '.svws-so td{padding:4px 5px;border-bottom:1px solid #dbe4ee;vertical-align:middle;' +
    'overflow:hidden}' +
    '.svws-so tbody tr:last-child td{border-bottom:0}' +
    '.svws-so tbody tr:nth-child(even){background:#f7fafd}' +
    '.svws-so tbody tr:hover{background:#eef4fa}' +
    '.svws-so td:first-child{color:#7d8ea0;font-size:11px;text-align:center;' +
    'padding-left:0;padding-right:0}' +
    '.svws-so td.ma .svws-so-o,.svws-so td.ma{font-family:"IBM Plex Mono",Consolas,' +
    'monospace;font-weight:500;letter-spacing:-.01em}' +
    '.svws-so tr.svws-so-loi{background:#fdefec !important}' +
    '.svws-so tr.svws-so-loi:hover{background:#fbe4e0 !important}' +
    '.svws-so-nhac{color:#a8231b;font-size:11px;line-height:1.4;white-space:normal;' +
    'padding:5px 8px !important}' +
    '.svws-so-ok{color:#1f9d55;font-weight:700}' +
    '.svws-so-tieu{margin:18px 0 3px;font:600 15px/1.3 ' + FONT + ';color:#0b2545}' +
    '.svws-so-ghi{font-size:12.5px;color:#5b6b7d;margin:0 0 7px;max-width:80ch;' +
    'line-height:1.5}' +
    '.svws-so-cuon{overflow-x:auto;max-width:100%;border:1px solid #cfdae6;' +
    'border-radius:5px;background:#fff}' +
    '.svws-so-tt{padding:9px 13px;border-radius:5px;font:600 12.5px ' + FONT + ';' +
    'margin:8px 0}' +
    '.svws-so-tt.tot{background:#eaf7f0;color:#12603a;border-left:4px solid #1f9d55}' +
    '.svws-so-tt.xau{background:#fdeeec;color:#8c1d16;border-left:4px solid #b3271e}' +
    '.svws-so-ds{margin:4px 0 12px 18px;font-size:12px;color:#8c1d16;line-height:1.55}' +
    '.svws-so-ds.nhac{color:#7a5a1e}' +
    /* Ô nhập: trong suốt cho tới khi rê chuột hoặc gõ — bảng đọc như sổ in,
       nhưng bấm vào đâu cũng sửa được. */
    '.svws-so-o{width:100%;box-sizing:border-box;font:inherit;font-size:12.5px;' +
    'padding:4px 5px;border:1px solid transparent;border-radius:3px;' +
    'background:transparent;color:#12263a;min-width:0}' +
    '.svws-so-o:hover{border-color:#c3d2e0;background:#fff}' +
    '.svws-so-o:focus{outline:none;border-color:#0b2545;background:#fff;' +
    'box-shadow:0 0 0 2px rgba(11,37,69,.13);position:relative;z-index:1}' +
    '.svws-so td.p .svws-so-o{text-align:right}' +
    'select.svws-so-o{appearance:none;-webkit-appearance:none;cursor:pointer;' +
    'padding-right:16px;background-image:url("data:image/svg+xml;charset=utf-8,' +
    '%3Csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 10 6\'%3E%3Cpath ' +
    'fill=\'%235b6b7d\' d=\'M0 0h10L5 6z\'/%3E%3C/svg%3E");' +
    'background-repeat:no-repeat;background-position:right 5px center;' +
    'background-size:8px}' +
    '.svws-so-xoa{border:0;background:transparent;color:#b3271e;cursor:pointer;' +
    'font-size:13px;line-height:1;padding:4px 6px;border-radius:3px;opacity:.35}' +
    '.svws-so tr:hover .svws-so-xoa{opacity:1}' +
    '.svws-so-xoa:hover{background:#fdeeec}' +
    '.svws-so-nut{display:flex;align-items:center;gap:11px;margin:6px 0 4px}' +
    '.svws-so-them{border:1px dashed #9fb4c8;background:transparent;color:#0b2545;' +
    'cursor:pointer;font:600 12px ' + FONT + ';padding:5px 12px;border-radius:5px}' +
    '.svws-so-them:hover{border-style:solid;background:#f2f7fc}' +
    '.svws-so-nut span{font-size:11.5px;color:#5b6b7d}' +
    '@media print{.svws-so-cuon{overflow:visible;border:0}' +
    '.svws-so{min-width:0 !important;font-size:9.5px}' +
    '.svws-so th{position:static}' +
    '.svws-so-nut,.svws-so-xoa{display:none}' +
    '.svws-so-o{border-color:transparent;background:transparent}}';

  global.SVWSSO = {
    version: '1.0',
    tao: tao, CSS: CSS, CSS_TAG: '<style>' + CSS + '</style>',
    LOAI: LOAI, DAU: DAU, DICHVU: DICHVU, TINHIEU: TINHIEU
  };
})(window);
