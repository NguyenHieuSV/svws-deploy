/*!
 * SVWSCM — bộ sinh HỒ SƠ CHẠY THỬ & NGHIỆM THU (commissioning) cho tool SVWS
 * ==========================================================================
 * Vì sao có thư viện này: hồ sơ chạy thử là thứ AI viết ra dễ đọc nhất mà sai
 * nhiều nhất — nó gõ "thử áp 10 bar" cho mọi tuyến, "kiểm tra bơm" cho mọi bơm,
 * và số hạng mục thì tuỳ hứng. Chạy thử là lúc người ta mở van thật, đóng điện
 * thật, cấp dòng một chiều vào stack EDI thật; biểu mẫu sai ở đây tốn tiền và
 * có khi tốn người.
 *
 * Nguyên tắc: KHÔNG có hằng số mô tả hệ thống trong file này. Mọi dòng biểu mẫu
 * đều suy từ chính SỔ THIẾT BỊ (EQUIP), SỔ TUYẾN ỐNG (PIPES / công đoạn của
 * SVWSVT) và BẢNG ĐIỆN (danh sách tải, bảng I/O, bảng logic của SVWSDIEN) mà
 * tool đã khai. Thêm một bơm vào 3D thì mục 8.1 có thêm hạng mục kiểm bơm đó,
 * 8.3 có thêm một lộ đo cách điện, 8.5 có thêm kịch bản đổi bơm dự phòng —
 * không ai phải nhớ sửa ba chỗ.
 *
 * Dùng tối thiểu:
 *   const CM = SVWSCM.tao({
 *     ma: 'SVWS-DIW-168', ten: 'Hệ nước DI 168 m³/ngày',
 *     EQUIP: EQUIP, PIPES: PIPES,
 *     cd:  V.congDoan(),        // ưu tiên — cùng nguồn với BOQ nên không lệch
 *     ong: S.thongKeOng(),      // hoặc chỉ có cái này
 *     tai: DL.danhSach(),       // bảng chọn thiết bị điện
 *     io:  IO.danhSach(),       // bảng I/O
 *     lg:  LG.danhSach(),       // logic + báo động + trình tự
 *     params: P
 *   });
 *   elTab8.innerHTML = SVWSCM.CSS_TAG + CM.tatCa();
 *   CM.kiemTra();               // phải sạch trước khi phát hành
 */
(function (global) {
  'use strict';

  var FONT = '"IBM Plex Sans","Segoe UI",Arial,sans-serif';

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
  function so(v, m) { var n = parseFloat(v); return isFinite(n) ? n : (m || 0); }
  function lam(v, n) { var k = Math.pow(10, n || 0); return Math.round(v * k) / k; }
  function loai(e) { return String((e && e.type) || '').toLowerCase(); }
  function ten(e) {
    if (!e) return '';
    var t = e.tag || e.id || '';
    return e.name ? (t ? t + ' — ' + e.name : e.name) : t;
  }

  // ------------------------------------------------------------------ bảng
  function bang(tieu, cot, dong, ghi) {
    if (!dong || !dong.length) return '';
    var h = '';
    if (tieu) h += '<h4 class="svws-bang-tieu">' + esc(tieu) + '</h4>';
    if (ghi) h += '<div class="svws-ghi">' + esc(ghi) + '</div>';
    /* Biểu mẫu chạy thử có bảng tới 14 cột. Trên màn hình hẹp mà để bảng tự co
       thì mỗi ô xuống dòng thành một cột chữ dựng đứng, đọc không nổi — cho
       bảng giữ bề rộng tối thiểu và cuộn ngang trong khung của chính nó. */
    h += '<div class="svws-cuon"><table class="svws-bang" ' +
      'style="min-width:' + Math.max(720, cot.length * 108) + 'px"><thead><tr>' +
      cot.map(function (t) { return '<th>' + esc(t) + '</th>'; }).join('') +
      '</tr></thead><tbody>';
    dong.forEach(function (r) {
      h += '<tr>' + r.map(function (c) {
        return c === null ? '<td class="svws-ky"></td>' : '<td>' + esc(c) + '</td>';
      }).join('') + '</tr>';
    });
    return h + '</tbody></table></div>';
  }
  function muc(so2, tieu, than) {
    return '<section class="svws-cm-trang" data-muc="' + esc(so2) + '">' +
      '<h3 class="svws-cm-h">' + esc(so2) + '  ' + esc(tieu) + '</h3>' + than +
      '</section>';
  }

  // ------------------------------------------------------- 7 cổng chạy thử
  /* Chạy thử theo CỔNG chứ không theo danh sách phẳng: không qua cổng trước thì
     không được mở cổng sau. Đây là chỗ hay bị bỏ nhất — người ta đóng điện chạy
     bơm khi ống chưa thử áp, hoặc cấp dòng EDI khi nước cấp chưa đạt. */
  var GATE = [
    ['G1', 'Hoàn thành cơ khí (MC)',
     'Lắp đặt xong toàn bộ thiết bị, đường ống, giá đỡ; vệ sinh mặt bằng',
     'Hết 100 % hạng mục mục 8.1; không còn tồn đọng loại A',
     'Biên bản MC + danh mục tồn đọng (punch list)'],
    ['G2', 'Thử áp & xúc rửa đường ống',
     'Thử kín theo từng tuyến, xúc rửa tới tiêu chí, xả sạch',
     'Đủ 100 % tuyến ở mục 8.2 đạt; không tuyến nào sụt áp quá ngưỡng',
     'Biên bản thử áp từng tuyến + biên bản xúc rửa'],
    ['G3', 'Điện — chạy nguội',
     'Kiểm tra tủ, đo cách điện, thứ tự pha, quay không tải từng động cơ',
     'Cách điện đạt; chiều quay đúng; dòng không tải trong dải; rơ-le nhiệt đã đặt',
     'Biên bản megger + biên bản chạy không tải'],
    ['G4', 'Thiết bị đo & loop check',
     'Hiệu chuẩn và kiểm vòng tín hiệu từ hiện trường tới HMI',
     '100 % kênh AI đạt tại 3 điểm 4/12/20 mA; DI/DO đúng trạng thái',
     'Phiếu loop check từng kênh'],
    ['G5', 'Interlock & trình tự',
     'Thử từng khoá liên động và từng trình tự tự động',
     'Mọi kịch bản mục 8.5 cho tác động đúng, đúng thời gian đáp ứng',
     'Biên bản thử interlock có chữ ký hai bên'],
    ['G6', 'Chạy công nghệ từng cụm',
     'Nạp vật liệu, khởi động và cân chỉnh từng cụm theo chiều dòng',
     'Từng cụm đạt thông số thiết kế và đã ghi baseline',
     'Phiếu vận hành từng cụm + bảng baseline'],
    ['G7', 'Chạy thử liên tục 72 h & nghiệm thu hiệu năng',
     'Chạy liên tục theo lịch tiêu thụ mô phỏng, lấy mẫu theo tần suất',
     'Đủ 8 chỉ tiêu cam kết mục 8.8; không có can thiệp tay',
     'Nhật ký 72 h + kết quả phân tích + biên bản nghiệm thu']
  ];

  var NHANSU = [
    ['Chỉ huy chạy thử', 'Điều phối toàn bộ, ký thông qua từng cổng', '1',
     'Kỹ sư ≥ 5 năm, đã chạy thử ≥ 3 hệ tương đương'],
    ['Kỹ sư công nghệ', 'Cân chỉnh cụm, đọc số liệu, chuẩn hoá baseline', '1',
     'Kỹ sư hoá / môi trường, hiểu màng và trao đổi ion'],
    ['Kỹ sư điện – PLC', 'Loop check, interlock, chỉnh biến tần, sửa chương trình', '1',
     'Có kinh nghiệm PLC/HMI của hãng đang dùng'],
    ['Thợ cơ khí', 'Siết, thay gioăng, xử lý rò, hỗ trợ nạp vật liệu', '2', 'Bậc 3/7 trở lên'],
    ['Thợ điện', 'Đấu nối, đo, hỗ trợ megger và thử interlock', '1', 'Chứng chỉ an toàn điện'],
    ['Vận hành viên chủ đầu tư', 'Tiếp nhận, vận hành có giám sát ở giai đoạn 72 h', '2',
     'Là người sẽ vận hành thật — không cử người khác học thay'],
    ['Cán bộ an toàn (HSE)', 'Cấp PTW, giám sát LOTO, hoá chất, không gian hạn chế', '1',
     'Chứng chỉ an toàn còn hiệu lực'],
    ['QA/QC', 'Lấy mẫu, niêm phong, gửi phân tích, lưu hồ sơ', '1', 'Nắm quy trình lấy mẫu']
  ];

  var DUNGCU = [
    ['Bơm thử áp bằng tay/điện + đồng hồ chuẩn cấp 0,5', 'Thử áp đường ống', 'Có tem hiệu chuẩn'],
    ['Megger 500/1000 V DC', 'Đo cách điện cáp và cuộn dây', 'Tem hiệu chuẩn ≤ 12 tháng'],
    ['Ampe kìm true-RMS', 'Đo dòng không tải và có tải từng lộ', 'Đo được cả sóng biến tần'],
    ['Đồng hồ vạn năng', 'Đo thông mạch, điện áp điều khiển', ''],
    ['Bộ phát dòng 4–20 mA / bộ mô phỏng tín hiệu', 'Loop check kênh AI, AO', 'Bắt buộc'],
    ['Máy đo độ dẫn / điện trở suất cầm tay', 'Đối chứng QIT/CIT trên tuyến', 'Có bù nhiệt 25 °C'],
    ['Bút pH + dung dịch đệm 4,01 · 7,00 · 10,01', 'Hiệu chuẩn kênh pH', 'Đệm còn hạn'],
    ['Bộ đo SDI (phin 0,45 µm)', 'Kiểm nước cấp màng RO', 'Bắt buộc trước khi nạp màng'],
    ['Đồng hồ lưu lượng siêu âm kẹp ngoài', 'Đối chứng FIT mà không phải cắt ống', ''],
    ['Camera nhiệt', 'Soi điểm nóng đầu cốt sau khi mang tải', 'Soi lại sau 2 h chạy tải'],
    ['Tốc kế / thiết bị đo rung', 'Kiểm chiều quay và độ rung bơm', 'Rung ≤ 4,5 mm/s RMS'],
    ['Máy đo độ ồn', 'Nghiệm thu chỉ tiêu ồn', 'Đo tại 1 m, cao 1,5 m'],
    ['Cân và can chuẩn có vạch', 'Hiệu chuẩn bơm định lượng theo thể tích', '']
  ];

  var EHS = [
    ['Giấy phép làm việc (PTW)',
     'Mở PTW riêng cho: làm việc điện hạ áp · làm việc trên cao · vào không gian hạn chế (bể) · làm việc với hoá chất. Hết ca đóng phiếu.'],
    ['Khoá – thẻ (LOTO)',
     'Trước mọi việc trên phần cơ: cắt lộ tương ứng, khoá tay gạt bằng khoá cá nhân, treo thẻ ghi tên và giờ. Chỉ người treo được gỡ.'],
    ['Thử áp',
     'Ưu tiên thử bằng NƯỚC, không thử bằng khí. Rào vùng thử, không ai đứng đối diện mặt bích trong lúc tăng áp; tăng áp theo nấc và giữ trước khi lên nấc kế.'],
    ['Không gian hạn chế',
     'Vào bể phải đo khí, có người canh ngoài, dây cứu hộ, đèn 24 V; cấm vào một mình.'],
    ['Hoá chất',
     'MSDS treo tại nơi pha; kính chắn mặt, găng chống hoá chất, tạp dề; vòi rửa mắt và tắm khẩn cấp trong bán kính 10 m và ĐÃ THỬ CHẢY.'],
    ['Điện',
     'Chỉ thợ điện có chứng chỉ được mở tủ khi có điện; dùng dụng cụ cách điện; thảm cách điện trước tủ; cấm tháo nắp che thanh cái khi đang mang điện.'],
    ['Ứng cứu',
     'Số điện thoại khẩn, vị trí tủ thuốc và bình chữa cháy dán tại cửa; phổ biến trước khi khởi công mỗi ngày (toolbox meeting).']
  ];

  // --------------------------------------------- tiêu chí cơ khí theo LOẠI
  /* Tiêu chí phải CÓ SỐ. "Kiểm tra bơm đạt yêu cầu" không kiểm được và không ai
     dám ký; "độ rung ≤ 4,5 mm/s RMS đo tại gối đỡ" thì đo xong biết đạt hay không. */
  var CK = {
    tank: [
      ['Vị trí và cao độ đặt so với bản vẽ', 'Sai lệch ≤ ±10 mm', 'Thước + máy thuỷ bình'],
      ['Độ thăng bằng miệng bể', '≤ 2 mm/m, tổng ≤ 5 mm', 'Ni-vô ống nước'],
      ['Thử kín bằng nước đầy 24 h', 'Sụt mức ≤ 3 mm, không vết thấm', 'Vạch mốc + quan sát'],
      ['Cổ ống: cao độ, góc quay so với bảng nozzle', '±5 mm và ±2°', 'Thước + thước đo góc'],
      ['Thông hơi có lưới chắn côn trùng, ống tràn dẫn về hố ga', 'Có, thông thoáng', 'Quan sát'],
      ['Thang, sàn thao tác, lan can', 'Lan can ≥ 1.100 mm, mặt sàn chống trượt', 'Thước'],
      ['Vệ sinh lòng bể, không dị vật', 'Sạch, chụp ảnh trước khi đóng nắp', 'Quan sát + ảnh']
    ],
    vessel: [
      ['Model, đường kính, chiều cao đúng bảng thông số', 'Đúng 100 %', 'Đối chiếu nhãn'],
      ['Áp làm việc cho phép của bình', '≥ 1,5 × áp vận hành thiết kế', 'Nhãn / CO-CQ'],
      ['Đầu thu dưới đáy (lateral) đủ, không nứt gãy', 'Đủ số nhánh, không gãy', 'Mở kiểm trước khi nạp'],
      ['Cụm van / van đa cổng đúng sơ đồ, quay đúng chiều', 'Đúng sơ đồ P&ID', 'Quay thử từng vị trí'],
      ['Đồng hồ áp vào – ra và van lấy mẫu vào – ra', 'Có đủ 2 đồng hồ + 2 van lấy mẫu', 'Quan sát'],
      ['Độ nghiêng thân bình', '≤ 2 mm/m', 'Ni-vô'],
      ['Siết nắp trên đúng mô-men nhà sản xuất', 'Theo bảng mô-men, siết chéo', 'Cờ-lê lực']
    ],
    cartridge: [
      ['Số lõi và chiều dài lõi đúng thiết kế', 'Đúng 100 %', 'Đếm + đo'],
      ['Gioăng nắp còn nguyên, bulông siết chéo', 'Theo mô-men nhà sản xuất', 'Cờ-lê lực'],
      ['Đồng hồ chênh áp vào – ra, van xả khí', 'Có đủ', 'Quan sát'],
      ['Thử kín vỏ lọc', '1,5 × áp làm việc, giữ 30 phút, không rò', 'Bơm thử áp']
    ],
    pump: [
      ['Đồng tâm trục bơm – động cơ (nếu khớp nối rời)', 'Lệch tâm ≤ 0,05 mm', 'Đồng hồ so'],
      ['Đế bơm chèn vữa, bulông neo siết đủ', 'Không hở chân đế', 'Quan sát + cờ-lê lực'],
      ['Van chặn hút – đẩy và van một chiều đúng chiều', 'Mũi tên đúng chiều dòng', 'Quan sát'],
      ['Đồng hồ áp hút và áp đẩy', 'Có đủ 2 cái', 'Quan sát'],
      ['Ống hút không có điểm đọng khí, dốc về bơm', 'Không có đoạn nhô cao', 'Quan sát tuyến 3D'],
      ['Mồi nước đầy, quay trục bằng tay nhẹ, không kẹt', 'Quay được bằng tay', 'Thử tay'],
      ['Độ rung sau khi chạy (ghi ở mục 8.3)', '≤ 4,5 mm/s RMS tại gối đỡ', 'Máy đo rung']
    ],
    roskid: [
      ['Khung skid cân bằng, đệm chống rung', '≤ 2 mm/m', 'Ni-vô'],
      ['Số vessel màng, đầu bịt và o-ring đủ theo thiết kế', 'Đúng 100 %', 'Đếm'],
      ['Ống cao áp SS316 siết đúng, không lệch tâm mặt bích', 'Khe hở đều ≤ 0,5 mm', 'Thước lá'],
      ['Đồng hồ áp trước màng – sau màng – concentrate', 'Có đủ 3 vị trí', 'Quan sát'],
      ['Lưu lượng kế permeate và concentrate', 'Có đủ, đọc được từ lối đi', 'Quan sát'],
      ['Van tiết lưu concentrate và van hồi lưu', 'Có, đóng mở nhẹ', 'Thử tay'],
      ['CHƯA NẠP MÀNG trong lúc thử áp và xúc rửa', 'Vessel rỗng, có biên bản', 'Quan sát + ký']
    ],
    edi: [
      ['Số stack đúng thiết kế (5 m³/h mỗi stack)', 'Đúng 100 %', 'Đếm'],
      ['Ti giằng siết đúng mô-men và đúng trình tự nhà sản xuất', 'Theo bảng hãng', 'Cờ-lê lực'],
      ['Đấu nối một chiều đúng cực, siết chắc', 'Đúng cực, không phát nhiệt', 'Đối chiếu sơ đồ'],
      ['Ba dòng nước (sản phẩm · cô đặc · điện cực) đúng sơ đồ, không đảo',
       'Đúng 100 %', 'Dò từng đường'],
      ['Van chỉnh và đồng hồ đủ trên cả ba dòng', 'Có đủ', 'Quan sát'],
      ['CHƯA CẤP DÒNG DC khi chưa đủ lưu lượng và chất lượng nước cấp',
       'Có khoá liên động, đã thử', 'Thử tại mục 8.5']
    ],
    mixedbed: [
      ['Tỷ lệ nhựa cation : anion đúng thiết kế', 'Theo bảng thông số', 'Cân / đong khi nạp'],
      ['Đầu thu dưới đáy và bộ phân phối trên đủ', 'Không gãy, không lệch', 'Mở kiểm trước khi nạp'],
      ['Van lấy mẫu ra và đầu đo điện trở suất', 'Có đủ', 'Quan sát']
    ],
    uv: [
      ['Ống thạch anh sạch, không nứt; đèn đúng công suất', 'Đúng model', 'Quan sát + nhãn'],
      ['Cảm biến cường độ lắp đúng vị trí, có cửa kiểm', 'Có', 'Quan sát'],
      ['Khoá liên động mất nước / quá nhiệt', 'Có, thử tại mục 8.5', 'Đối chiếu I/O'],
      ['Kín nước tại hai đầu bịt', 'Không rò khi thử áp', 'Thử áp']
    ],
    dosing: [
      ['Bồn pha có vạch mức và máy khuấy', 'Đọc được mức từ lối đi', 'Quan sát'],
      ['Chậu chứa tràn (bund)', '≥ 110 % thể tích bồn lớn nhất', 'Đo và tính'],
      ['Bơm định lượng: dải lưu lượng phủ được liều thiết kế', 'Liều đặt nằm trong 20–80 % dải',
       'Đối chiếu catalogue'],
      ['Van một chiều + van an toàn + bình giảm xung ở đầu đẩy', 'Có đủ 3', 'Quan sát'],
      ['Điểm châm đặt sau thiết bị trộn / sau cút để trộn đều', 'Đúng vị trí P&ID', 'Quan sát'],
      ['Nhãn hoá chất và MSDS treo tại chỗ', 'Có', 'Quan sát'],
      ['Vòi rửa mắt / tắm khẩn cấp trong 10 m và đã thử chảy', 'Có nước, thử đạt', 'Thử tại chỗ']
    ]
  };

  /* Hạng mục dùng chung: giá đỡ, nhà xưởng, tiếp địa. Không gắn với một thiết bị
     nào nên không sinh theo EQUIP được, nhưng thiếu thì không ai nghiệm thu nổi. */
  function CK_CHUNG(caoRack) {
    return [
      ['Giá đỡ ống', 'Cao trình tầng giá đỡ so với bản vẽ',
       (caoRack ? 'Cao nhất ' + caoRack + ' mm, sai lệch ≤ ±10 mm' : 'Sai lệch ≤ ±10 mm'),
       'Máy thuỷ bình'],
      ['Giá đỡ ống', 'Bước gối đỡ theo vật liệu',
       'uPVC DN ≤ 50: ≤ 1,0 m · uPVC DN > 50: ≤ 1,5 m · thép/SS: ≤ 2,5 m', 'Thước'],
      ['Giá đỡ ống', 'Gối cố định tại điểm đổi hướng, gối trượt trên đoạn thẳng dài',
       'Có đủ theo bản vẽ', 'Quan sát'],
      ['Đường ống', 'Độ dốc về điểm xả', '≥ 0,5 %', 'Ni-vô'],
      ['Đường ống', 'Nhãn tuyến và mũi tên chiều dòng',
       '100 % tuyến có nhãn ở hai đầu và tại mỗi lần xuyên tường', 'Đếm'],
      ['Mặt bằng', 'Lối đi thao tác quanh thiết bị', '≥ 800 mm', 'Thước'],
      ['Mặt bằng', 'Rãnh thoát sàn và độ dốc về hố ga', '≥ 1 %, không đọng nước', 'Đổ nước thử'],
      ['Mặt bằng', 'Chiếu sáng vùng thao tác', '≥ 200 lux', 'Máy đo lux'],
      ['Tiếp địa', 'Điện trở tiếp địa vỏ thiết bị và tủ', '≤ 4 Ω', 'Máy đo tiếp địa']
    ];
  }

  // ------------------------------------------------- vật liệu & áp thử ống
  var TEN_DV = {
    raw: 'Nước thô / nước cấp', filtered: 'Nước sau lọc', ro: 'Nước RO',
    di: 'Nước DI / siêu tinh khiết', chem: 'Hoá chất', air: 'Khí nén',
    waste: 'Nước thải / cô đặc', steam: 'Hơi / nước nóng', drain: 'Xả đáy'
  };

  /**
   * Vật liệu suy từ dịch vụ, trừ khi tuyến tự khai `vl`. Nước RO và DI ăn mòn
   * thép thường và nhả ion từ nhựa rẻ tiền — chọn sai vật liệu ở đây thì cả hệ
   * không bao giờ lên nổi 18 MΩ·cm dù màng và EDI đều tốt.
   */
  function vatLieu(sv, khai, cao) {
    if (khai) return khai;
    if (cao) return 'SS316L chịu áp cao (ống và phụ kiện cùng cấp áp)';
    switch (sv) {
      case 'ro': return 'uPVC PN10 hoặc PVDF (đoạn áp thấp)';
      case 'di': return 'PVDF hoặc SS316L đánh bóng (Ra ≤ 0,8 µm)';
      case 'chem': return 'PE / PVDF chịu hoá chất';
      case 'air': return 'SS304 hoặc đồng';
      case 'steam': return 'SS304 có bảo ôn';
      default: return 'uPVC PN10';
    }
  }

  /**
   * Áp thử theo DỊCH VỤ, không phải một con số cho cả hệ:
   *   · uPVC (nước thô, sau lọc, thải, xả)  → 9 bar
   *   · SS316 cao áp trước/sau bơm cao áp   → 1,5 × áp vận hành của pass đó
   *   · Mạch vòng phân phối DI              → 1,5 × (áp cuối vòng + 3 bar)
   *   · Đường châm hoá chất                 → 10 bar (bơm định lượng dựng áp cao)
   * Thử cả hệ bằng một áp duy nhất thì hoặc phá uPVC, hoặc không kiểm được
   * đoạn cao áp.
   */
  function apThu(t, p) {
    if (t.ap) return { ap: so(t.ap), ly: 'Do tuyến tự khai' };
    var sv = t.service, ln = String(t.line || '') + ' ' + String(t.ghi || '');
    var vong = t.vong || /vòng|vong|loop|pou/i.test(ln);
    if (sv === 'chem')
      return { ap: 10, ly: 'Đường châm hoá chất — bơm định lượng dựng áp cao' };
    if (sv === 'di' && vong) {
      var pl = so(p.Ploop, 3);
      return { ap: lam(1.5 * (pl + 3), 1),
               ly: '1,5 × (áp cuối vòng ' + pl + ' bar + 3 bar dự phòng bơm)' };
    }
    /* CAO ÁP chỉ là đoạn từ ĐẦU ĐẨY BƠM CAO ÁP tới cụm màng. Nước thấm ra khỏi
       màng pass 1 cũng mang dịch vụ "ro" nhưng chạy ở áp thấp — thử nó ở 22,5
       bar là phá đường ống mà chẳng kiểm được gì. */
    if (t.cao) {
      var pr = so(t.pass === 2 ? p.pRO2 : p.pRO1, so(p.pRO1, 15));
      return { ap: lam(1.5 * pr, 1), ly: '1,5 × áp vận hành RO' + (t.pass || 1) +
               ' (' + pr + ' bar) — đoạn SS316 cao áp sau bơm cao áp' };
    }
    if (sv === 'ro') return { ap: 9, ly: 'Đoạn nước RO áp thấp (nước thấm) — cấp PN10' };
    if (sv === 'di') return { ap: 9, ly: 'Đoạn DI áp thấp — thử theo cấp uPVC/PVDF PN10' };
    if (sv === 'air') return { ap: 12, ly: '1,5 × áp khí nén 8 bar' };
    if (sv === 'drain')
      return { ap: 0, ly: 'Đường xả tự chảy — thử kín bằng nước đầy 2 h, không thử áp' };
    return { ap: 9, ly: 'uPVC PN10 — thử 9 bar theo chuẩn công ty' };
  }

  function xucRua(sv, vong) {
    if (sv === 'chem')
      return 'Xúc bằng nước sạch → thổi khô → tráng bằng chính hoá chất sẽ dùng, xả bỏ mẻ đầu';
    if (sv === 'di' && vong)
      return 'Xúc bằng nước RO → sanitize → passivation → xúc lại tới khi đạt điện trở suất nền';
    if (sv === 'di' || sv === 'ro')
      return 'Xúc bằng nước RO tới khi độ dẫn nước ra ≤ 5 µS/cm và không còn hạt';
    if (sv === 'drain') return 'Đổ đầy nước, quan sát 2 h, kiểm tra thông tắc';
    return 'Xúc bằng nước sạch ở vận tốc ≥ 1,5 m/s tới khi nước ra trong, không cặn';
  }
  function tieuChi(sv, ap) {
    if (!ap) return 'Không rò rỉ, thoát hết nước, không đọng';
    return 'Giữ ' + (ap >= 10 ? 60 : 30) + ' phút, sụt áp ≤ 0,2 bar và không có giọt rò ' +
           'tại mọi mối nối';
  }

  // =========================================================================
  function tao(o) {
    o = o || {};
    var EQ = o.EQUIP || [], PI = o.PIPES || [];
    var p = o.params || {};
    var cd = o.cd || null;                 // công đoạn của SVWSVT (ưu tiên)
    var ong = o.ong || [];                 // thongKeOng() của SVWS3D
    var tai = o.tai || [];                 // DL.danhSach()
    var io = o.io || [];                   // IO.danhSach()
    var lg = o.lg || {};                   // LG.danhSach()
    var ma = o.ma || 'SVWS';
    var loi = [], canhBao = [];

    function timTB(id) {
      for (var i = 0; i < EQ.length; i++)
        if (EQ[i].id === id || EQ[i].tag === id) return EQ[i];
      return null;
    }
    function tenTB(id) { var e = timTB(id); return e ? ten(e) : id; }
    function co(re) { return EQ.some(function (e) { return re.test(loai(e)); }); }
    function loc(re) { return EQ.filter(function (e) { return re.test(loai(e)); }); }
    var Qtb = so(p.Qavg, 0), Qmax = so(p.Qmax, Qtb);

    /* Danh sách tuyến dùng chung cho 8.2: ưu tiên công đoạn của SVWSVT vì BOQ
       cũng đọc từ đó — hai bảng cùng một nguồn thì không thể lệch số van. */
    function dsTuyen() {
      if (cd && cd.length) return cd.map(function (c, i) {
        var k = PI[i] || {};
        return { i: i, from: c.from, to: c.to, dn: c.dn, service: c.service,
                 vl: c.vl, daiM: c.daiM, soCo: c.soCo, caoNhat: c.caoNhat,
                 van: (c.van || 0) + (c.cumBom > 1 ? c.cumBom * 2 : 0),
                 mc: c.cumBom > 1 ? c.cumBom : (c.coMotChieu ? 1 : 0),
                 line: k.line, ap: k.ap, pass: k.pass, vong: k.vong, ghi: k.ghi };
      });
      if (ong.length) return ong.map(function (t, i) {
        var k = PI[i] || {};
        return { i: i, from: t.from, to: t.to, dn: t.dn, service: t.service,
                 vl: k.vl, daiM: lam(t.dai / 1000, 2), soCo: t.soCo,
                 caoNhat: t.caoNhat, van: so(k.van, 1), mc: 0,
                 line: k.line, ap: k.ap, pass: k.pass, vong: k.vong, ghi: k.ghi };
      });
      return PI.map(function (k, i) {
        return { i: i, from: k.from, to: k.to, dn: k.dn, service: k.service,
                 vl: k.vl, daiM: null, soCo: null, van: so(k.van, 1), mc: 0,
                 line: k.line, ap: k.ap, pass: k.pass, vong: k.vong, ghi: k.ghi };
      });
    }
    function maTuyen(t) { return t.line || ('L-' + ('0' + (t.i + 1)).slice(-2)); }

    /* Đoạn cao áp = từ ĐẦU ĐẨY một bơm SANG cụm màng. Suy từ loại thiết bị hai
       đầu chứ không suy từ dịch vụ: nước thấm ra khỏi màng cũng là "ro" nhưng
       chạy ở áp khí quyển. Tuyến tự khai `cao` thì tôn trọng khai báo. */
    function laCaoAp(t) {
      if (t.cao != null) return !!t.cao;
      var a = timTB(t.from), b = timTB(t.to);
      return !!a && !!b && /pump|bom/.test(loai(a)) && /roskid|^ro$/.test(loai(b));
    }
    /* Pass của đoạn cao áp lấy theo chính cụm màng nó dẫn vào. */
    function passCua(t) {
      if (t.pass) return t.pass;
      var b = timTB(t.to);
      return b ? so(b.pass, 1) : 1;
    }

    // ================================================== 8.0 Tổng quan
    function tongQuan() {
      var h = '<div class="svws-tq">Chạy thử đi theo BẢY CỔNG. Không thông qua ' +
        'cổng trước thì không được mở cổng sau — đây là chỗ hay bị bỏ nhất: đóng ' +
        'điện chạy bơm khi ống chưa thử áp, hay cấp dòng một chiều vào stack EDI ' +
        'khi nước cấp chưa đạt.</div>';
      h += bang('Bảy cổng chạy thử', ['Cổng', 'Tên', 'Nội dung', 'Tiêu chí thông qua',
        'Hồ sơ để lại', 'Ngày', 'Người ký'],
        GATE.map(function (g) { return g.concat([null, null]); }));

      h += bang('Nhân sự chạy thử',
        ['Vai trò', 'Trách nhiệm', 'Số người', 'Yêu cầu năng lực'], NHANSU);

      var dk = [];
      dk.push(['Nguồn điện', 'Cấp từ ' + (p.mcb || 'MCB-D9') + ' — 3P+N 380/220 V 50 Hz',
        'Đã đóng điện tới đầu vào tủ, đo đủ 3 pha, thứ tự pha đúng',
        'Không có nguồn ổn định thì mọi phép đo dòng đều vô nghĩa']);
      dk.push(['Nước cấp', 'Đủ lưu lượng ≥ ' + (Qmax || '—') + ' m³/h, liên tục',
        'Áp tại điểm đấu nối ≥ 1,5 bar; có kết quả phân tích nước nguồn còn hiệu lực',
        'Thiếu nước cấp thì không chạy nổi 72 h, phải dừng giữa chừng']);
      var hc = loc(/dosing/);
      dk.push(['Hoá chất', hc.length
        ? hc.map(function (e) { return ten(e); }).join(' · ')
        : 'Theo bảng hoá chất của thiết kế',
        'Đủ lượng cho 72 h + 20 % dự phòng; còn hạn; có MSDS',
        'Pha sẵn trước ngày G6, không pha lúc đang chạy']);
      if (co(/edi|mixedbed/))
        dk.push(['Nước DI mồi', 'Nước RO/DI để nạp và xúc EDI, cột trao đổi ion',
          'Ước tính ' + (uocNuocMoi() || '—') + ' m³ — chuẩn bị trước hoặc chạy RO ' +
          'trước một ngày để tự tích',
          'Nạp EDI và nhựa bằng nước máy là hỏng vật liệu ngay lần đầu']);
      dk.push(['Thoát nước', 'Rãnh và hố ga nhận nước xả trong lúc xúc rửa và chạy thử',
        'Chịu được ' + lam(Qmax * 1.5, 1) + ' m³/h; có điểm trung hoà trước khi thải',
        'Xúc rửa xả rất nhiều nước trong thời gian ngắn']);
      dk.push(['Khí nén (nếu có van khí)', 'Áp 5–7 bar, khô, đã lọc dầu',
        'Có bình tích và van xả nước ngưng', '']);
      dk.push(['SCADA / mạng', 'Đường truyền tới HMI và tới SIM nhắn tin cảnh báo',
        'Đã thử gửi được một tin nhắn thật', 'Thử ở G4, không để tới lúc bàn giao']);
      dk.push(['Hồ sơ', 'Bản vẽ mới nhất, P&ID, bảng I/O, chương trình PLC đã nạp',
        'Đúng Rev đang thi công', 'Chạy thử theo bản vẽ cũ là nguồn sai lớn nhất']);
      h += bang('Điều kiện tiên quyết — kiểm trước khi mở G1',
        ['Hạng mục', 'Yêu cầu', 'Tiêu chí xác nhận', 'Vì sao'], dk);

      h += bang('Dụng cụ và thiết bị đo phải có tại công trường',
        ['Dụng cụ', 'Dùng cho', 'Yêu cầu'], DUNGCU);
      h += bang('An toàn — EHS, PTW, LOTO',
        ['Nội dung', 'Quy định áp dụng trong suốt đợt chạy thử'], EHS);
      return h;
    }

    /** Nước mồi ước tính: thể tích cột nhựa/stack × 5 lần xúc. */
    function uocNuocMoi() {
      var v = 0;
      loc(/edi|mixedbed/).forEach(function (e) {
        if (/edi/.test(loai(e))) {
          var n = so(e.soStack, Math.max(1, Math.ceil(Qtb / 5)));
          v += n * 0.3;                                   // ~0,3 m³ mỗi stack kể cả ống
        } else {
          var d = so(e.D, so(e.dia, 600)) / 1000, hh = so(e.H, so(e.h, 1800)) / 1000;
          v += Math.PI * d * d / 4 * hh * 0.6;
        }
      });
      return v ? lam(v * 5, 1) : 0;
    }

    // ================================================== 8.1 Cơ khí
    function coKhi() {
      var d = [], n = 0;
      EQ.forEach(function (e) {
        var t = loai(e);
        if (/panel|tu|mcc|plc/.test(t)) return;          // tủ điện kiểm ở 8.3
        var b = CK[t] || (t === 'filter' ? CK.vessel : t === 'ro' ? CK.roskid : null);
        if (!b) {
          canhBao.push('Thiết bị ' + ten(e) + ' loại "' + t +
            '" chưa có bộ tiêu chí cơ khí — mục 8.1 sẽ thiếu hạng mục cho thiết bị này.');
          return;
        }
        b.forEach(function (r) {
          d.push([++n, ten(e), r[0], r[1], r[2], null, null]);
        });
      });
      CK_CHUNG(o.caoRack || 0).forEach(function (r) {
        d.push([++n, r[0], r[1], r[2], r[3], null, null]);
      });
      var h = '<div class="svws-tq">Checklist sinh thẳng từ sổ thiết bị: ' +
        EQ.length + ' thiết bị khai báo → <b>' + n + ' hạng mục</b>. Thêm một bơm ' +
        'vào bản vẽ 3D là bảng này tự có thêm bảy dòng kiểm cho bơm đó.</div>';
      h += bang('8.1 Checklist hoàn thành cơ khí (MC) — cổng G1',
        ['TT', 'Thiết bị / hạng mục', 'Nội dung kiểm', 'Tiêu chí (có số)',
         'Phương pháp', 'Kết quả', 'Ký'], d);
      h += '<div class="svws-ghi">Tồn đọng phân loại A (chặn cổng — phải xong mới ' +
        'qua G1) · B (xong trước G7) · C (xong trước bàn giao). Ghi vào phiếu ' +
        'punch list kèm ảnh và hạn khắc phục.</div>';
      return h;
    }

    // ================================================== 8.2 Đường ống
    function duongOng() {
      var ts = dsTuyen();
      if (!ts.length) { loi.push('Chưa có tuyến ống nào — mục 8.2 rỗng.'); return ''; }
      var d = ts.map(function (t) {
        t.cao = laCaoAp(t); t.pass = passCua(t);
        var a = apThu(t, p);
        return [maTuyen(t), tenTB(t.from) + ' → ' + tenTB(t.to),
          TEN_DV[t.service] || t.service || '',
          'DN' + (t.dn || '—'), vatLieu(t.service, t.vl, t.cao),
          t.daiM == null ? '—' : t.daiM,
          t.soCo == null ? '—' : t.soCo,
          (t.van || 0) + (t.mc ? ' + ' + t.mc + ' MC' : ''),
          a.ap ? a.ap + ' bar' : 'Không thử áp',
          a.ly, xucRua(t.service, t.vong), tieuChi(t.service, a.ap), null, null];
      });
      var h = '<div class="svws-tq">' + ts.length + ' tuyến, chiều dài · số co · số ' +
        'van lấy thẳng từ bản vẽ 3D và bảng vật tư — cùng một nguồn với BOQ nên ' +
        'không thể lệch. Áp thử tính theo DỊCH VỤ của từng tuyến, không dùng một ' +
        'con số cho cả hệ.</div>';
      h += bang('8.2 Thử áp và xúc rửa từng tuyến — cổng G2',
        ['Tuyến', 'Từ → đến', 'Dịch vụ', 'DN', 'Vật liệu', 'Dài (m)', 'Co 90°',
         'Van', 'Áp thử', 'Cơ sở tính áp thử', 'Cách xúc rửa', 'Tiêu chí đạt',
         'Kết quả', 'Ký'], d);
      h += bang('Quy tắc chung khi thử áp', ['Nội dung', 'Quy định'], [
        ['Môi chất thử', 'Thử bằng NƯỚC. Chỉ thử bằng khí khi không thể dùng nước và ' +
         'phải rào vùng, giảm áp thử theo quy định an toàn.'],
        ['Cách tăng áp', 'Tăng theo nấc 50 % → 75 % → 100 % áp thử, mỗi nấc giữ 5 phút ' +
         'và đi kiểm mối nối trước khi lên nấc kế.'],
        ['Đồng hồ', 'Dùng đồng hồ cấp chính xác ≥ 0,5, thang đo 1,5–2 lần áp thử, ' +
         'còn tem hiệu chuẩn.'],
        ['Cô lập', 'Cô lập thiết bị không chịu được áp thử (màng RO, stack EDI, đèn UV, ' +
         'lưu lượng kế) bằng bích đặc — KHÔNG bằng van.'],
        ['Sau khi thử', 'Xả áp từ từ, xả kiệt nước, chỉ mở bích cô lập sau khi áp về 0.']
      ]);
      return h;
    }

    // ================================================== 8.3 Điện
    function dien() {
      var h = bang('8.3.1 Kiểm tra tủ điện trước khi đóng điện',
        ['Nội dung kiểm', 'Tiêu chí', 'Phương pháp', 'Kết quả', 'Ký'], [
        ['Siết lại toàn bộ đầu cốt động lực và điều khiển',
         'Theo mô-men nhà sản xuất, đánh dấu sơn sau khi siết', 'Cờ-lê lực', null, null],
        ['Cách điện thanh cái và mạch động lực (đã ngắt tải)',
         '≥ 5 MΩ ở 500 V DC', 'Megger', null, null],
        ['Tiếp địa vỏ tủ và cửa tủ', '≤ 4 Ω, dây nối cửa còn nguyên', 'Máy đo tiếp địa',
         null, null],
        ['Cấp bảo vệ vỏ tủ và gioăng cửa', 'Đúng IP thiết kế, gioăng không rách',
         'Quan sát', null, null],
        ['Quạt hút, lưới lọc, thermostat', 'Quạt chạy đúng chiều, đặt nhiệt 35–40 °C',
         'Thử tay', null, null],
        ['Nhãn từng lộ đúng bảng chọn thiết bị điện', '100 % lộ có nhãn khớp bản vẽ',
         'Đối chiếu', null, null],
        ['Sơ đồ nguyên lý đặt trong túi hồ sơ trong tủ', 'Đúng Rev đang thi công',
         'Quan sát', null, null],
        ['Thứ tự pha tại đầu vào MCCB tổng', 'L1–L2–L3 thuận, lệch điện áp pha ≤ 2 %',
         'Đồng hồ thứ tự pha', null, null],
        ['Khoá cửa tủ và biển cảnh báo điện', 'Có đủ', 'Quan sát', null, null]
      ]);

      if (!tai.length) {
        canhBao.push('Chưa nạp danh sách tải điện (DL.danhSach()) — mục 8.3 thiếu ' +
          'bảng kiểm từng lộ động cơ.');
      } else {
        var d = tai.map(function (t, i) {
          var In = so(t.I, 0);
          var kt = t.kieu === 'VFD';
          return ['Q' + (i + 1), t.tag, t.ten, t.kW + ' kW',
            lam(In, 1) + ' A', t.cbTen,
            '≥ 5 MΩ (500 V DC)',
            'Đúng chiều mũi tên trên vỏ bơm',
            lam(In * 0.3, 1) + '–' + lam(In * 0.45, 1) + ' A',
            '≤ ' + lam(In * 1.05, 1) + ' A',
            kt ? '— (biến tần bảo vệ)' : 'Đặt ' + lam(In * 1.05, 1) + ' A',
            kt ? ('U 380 V · In ' + lam(In, 1) + ' A · P ' + t.kW + ' kW · f 0–50 Hz · ' +
                  'ramp 10 s/10 s · giới hạn dòng 1,1×In · điều khiển V/f · ' +
                  'lệnh chạy và đặt tốc độ từ PLC · tự khởi động lại sau mất điện: TẮT')
               : '—',
            null, null];
        });
        h += bang('8.3.2 Kiểm tra và chạy nguội từng lộ động cơ — cổng G3',
          ['Lộ', 'Tag', 'Thiết bị', 'Công suất', 'In tính toán', 'Aptomat',
           'Cách điện cáp', 'Chiều quay', 'Dòng không tải (dự kiến)',
           'Dòng có tải cho phép', 'Đặt rơ-le nhiệt', 'Tham số biến tần cần đặt',
           'Kết quả', 'Ký'], d,
          'Dòng không tải dự kiến lấy 30–45 % In — đo ra ngoài dải này là dấu hiệu ' +
          'quay ngược pha, kẹt cơ khí hoặc chọn sai động cơ. Đo cách điện PHẢI tháo ' +
          'cáp khỏi biến tần, nếu không sẽ hỏng tầng công suất.');
      }

      var d3 = [];
      if (co(/edi/)) d3.push(['Bộ chỉnh lưu EDI',
        'Đo cách điện stack trước khi đấu; kiểm đúng cực; đặt giới hạn dòng và điện áp ' +
        'theo bảng của hãng; thử cảnh báo mất dòng',
        'Cách điện ≥ 5 MΩ · đúng cực · dòng đặt ≤ định mức stack · cảnh báo mất dòng tác động',
        'CHƯA cấp dòng khi chưa đủ lưu lượng — khoá liên động thử tại 8.5', null, null]);
      if (co(/uv/)) d3.push(['Đèn UV',
        'Cấp nguồn ballast, kiểm cường độ khi ống đầy nước, thử khoá liên động mất nước',
        'Cường độ ≥ ngưỡng cài đặt sau 60 s khởi động; mất nước là ngắt đèn',
        'Không bật đèn khi ống cạn — cháy ống thạch anh', null, null]);
      loc(/dosing/).forEach(function (e) {
        d3.push([ten(e),
          'Chỉnh hành trình (stroke) và tần số, hiệu chuẩn thể tích bằng ống chuẩn ' +
          'trong 10 phút',
          'Liều thực đo lệch ≤ ±5 % so với liều đặt; điểm làm việc nằm trong 20–80 % dải',
          'Hiệu chuẩn bằng chính hoá chất sẽ dùng, không hiệu chuẩn bằng nước', null, null]);
      });
      if (d3.length) h += bang('8.3.3 Thiết bị điện chuyên dụng',
        ['Thiết bị', 'Nội dung', 'Tiêu chí', 'Lưu ý', 'Kết quả', 'Ký'], d3);
      return h;
    }

    // ================================================== 8.4 Thiết bị đo
    /* Dải đo suy từ tiền tố tag theo ISA, trừ khi kênh tự khai `dai`. Ghi dải đo
       sai thì loop check vẫn "đạt" mà số trên HMI vẫn sai — lỗi khó tìm nhất. */
    function daiDo(k) {
      if (k.dai) return { dai: k.dai, dv: k.dv || '', pp: k.pp || '' };
      var t = String(k.tag || '').toUpperCase(), m = String(k.mo || '');
      if (/^F/.test(t)) return { dai: '0 – ' + lam(Math.max(Qmax * 1.5, 1), 1),
        dv: 'm³/h', pp: 'Đối chứng bằng đồng hồ siêu âm kẹp ngoài hoặc đo thể tích theo thời gian' };
      if (/^P/.test(t)) {
        var hp = /cao áp|ro|màng|mang/i.test(m);
        return { dai: '0 – ' + (hp ? lam(Math.max(so(p.pRO1, 15), so(p.pRO2, 15)) * 2, 0) : 16),
          dv: 'bar', pp: 'Bơm tay + đồng hồ chuẩn cấp 0,5, so tại 0 – 50 – 100 %' };
      }
      if (/^L/.test(t)) return { dai: '0 – ' + (k.cao || 3000), dv: 'mm',
        pp: 'Đổ nước theo vạch mốc, so tại đáy – giữa – mức tràn' };
      if (/^Q|^C/.test(t)) {
        var di = /di|18|siêu tinh|edi|mb|pou/i.test(m);
        return di ? { dai: '0 – 18,2', dv: 'MΩ·cm',
                      pp: 'So với máy cầm tay đã hiệu chuẩn, cùng nhiệt độ, bù về 25 °C' }
                  : { dai: '0 – 2.000', dv: 'µS/cm',
                      pp: 'Dung dịch chuẩn 84 µS/cm và 1.413 µS/cm' };
      }
      if (/^T/.test(t)) return { dai: '0 – 50', dv: '°C',
        pp: 'So với nhiệt kế chuẩn trong cùng cốc nước' };
      if (/^A|PH/.test(t)) return { dai: '0 – 14', dv: 'pH',
        pp: 'Dung dịch đệm 4,01 · 7,00 · 10,01' };
      return { dai: k.dai || '—', dv: k.dv || '', pp: 'Theo hướng dẫn nhà sản xuất' };
    }

    function thietBiDo() {
      if (!io.length) {
        loi.push('Chưa nạp bảng I/O (IO.danhSach()) — mục 8.4 không sinh được.');
        return '';
      }
      var ai = io.filter(function (k) { return k.kieu === 'AI'; });
      var h = '<div class="svws-tq">' + ai.length + ' kênh analog đọc thẳng từ bảng ' +
        'I/O của tab điện. Kênh nào có trong tủ là có phiếu hiệu chuẩn ở đây — ' +
        'P&ID, bảng I/O và biểu mẫu chạy thử không thể lệch nhau.</div>';
      h += bang('8.4.1 Hiệu chuẩn và loop check kênh analog (AI) — cổng G4',
        ['TT', 'Tag', 'Mô tả', 'Địa chỉ PLC', 'Dải đo', 'Đơn vị',
         '4 mA (0 %)', '12 mA (50 %)', '20 mA (100 %)', 'Sai số cho phép',
         'Phương pháp hiệu chuẩn', 'Đạt', 'Ký'],
        ai.map(function (k, i) {
          var dd = daiDo(k);
          return [i + 1, k.tag, k.mo, k.dc, dd.dai, dd.dv, '', '', '',
            '≤ ±1 % toàn thang', dd.pp, null, null];
        }),
        'Phát dòng chuẩn tại HIỆN TRƯỜNG, đọc trên HMI — đó mới là "loop check". ' +
        'Mô phỏng ngay tại đầu vào PLC thì bỏ lọt đứt dây, đấu ngược cực và sai ' +
        'điện trở đường dây.');

      var di = io.filter(function (k) { return k.kieu === 'DI'; });
      if (di.length) h += bang('8.4.2 Kiểm tra tín hiệu số vào (DI)',
        ['TT', 'Tag', 'Mô tả', 'Địa chỉ', 'Cách tạo trạng thái',
         'Trạng thái mong đợi trên HMI', 'Đạt', 'Ký'],
        di.map(function (k, i) {
          return [i + 1, k.tag, k.mo, k.dc,
            /estop|e-?stop/i.test(k.tag) ? 'Nhấn nút dừng khẩn cấp'
              : /door|cửa/i.test(k.tag) ? 'Mở cửa tủ'
              : /ls|mức|muc/i.test(k.tag) ? 'Nâng/hạ phao hoặc đổ nước tới ngưỡng'
              : /flt|lỗi|loi/i.test(k.tag) ? 'Nhấn thử tiếp điểm báo lỗi tại thiết bị'
              : 'Đóng/mở tiếp điểm tại hiện trường',
            'Đổi trạng thái tức thì, đúng chiều logic', null, null];
        }));

      var don = io.filter(function (k) { return k.kieu === 'DO' || k.kieu === 'AO'; });
      if (don.length) h += bang('8.4.3 Kiểm tra đầu ra (DO / AO) và van điều khiển',
        ['TT', 'Loại', 'Tag', 'Mô tả', 'Địa chỉ', 'Cách thử',
         'Kết quả mong đợi', 'Đạt', 'Ký'],
        don.map(function (k, i) {
          return [i + 1, k.kieu, k.tag, k.mo, k.dc,
            k.kieu === 'AO' ? 'Ép giá trị 0 – 50 – 100 % từ HMI'
                            : 'Cưỡng bức đầu ra ở chế độ tay',
            k.kieu === 'AO' ? 'Cơ cấu chấp hành đi đúng vị trí, phản hồi khớp ≤ ±2 %'
              : /sms/i.test(k.tag) ? 'Nhận được tin nhắn thật trên số điện thoại đã khai'
              : 'Contactor/van tác động đúng, có phản hồi trạng thái', null, null];
        }));
      return h;
    }

    // ================================================== 8.5 Interlock
    function interlock() {
      var d = [], n = 0;
      function them(ma2, kb, tao2, td, tg, kp) {
        d.push(['IT-' + ('0' + (++n)).slice(-2), ma2, kb, tao2, td, tg, kp, null, null]);
      }
      them('E-STOP', 'Nhấn dừng khẩn cấp khi hệ đang chạy có tải',
        'Nhấn nút S0 trên cửa tủ',
        'Toàn bộ động cơ và dòng DC EDI ngắt ngay bằng PHẦN CỨNG (không qua PLC); ' +
        'HMI báo E-STOP', '≤ 0,5 s', 'Xoay nhả nút → nhấn RESET → hệ ở trạng thái dừng an toàn');
      if (io.some(function (k) { return /door|cửa/i.test(k.tag); }))
        them('Cửa tủ', 'Mở cửa tủ khi đang chạy', 'Mở cửa tủ động lực',
          'Cảnh báo trên HMI, ghi nhật ký; không tự dừng hệ', '≤ 2 s', 'Đóng cửa, xoá cảnh báo');
      if (io.some(function (k) { return /lsl/i.test(k.tag); }))
        them('LSL bể cấp', 'Bể cấp cạn dưới mức thấp',
          'Hạ phao hoặc bơm cạn tới ngưỡng LSL',
          'Dừng bơm cấp ngay, cấm khởi động lại tới khi mức phục hồi + trễ 60 s',
          '≤ 2 s', 'Bơm nước lên trên mức, chờ trễ, tự chạy lại');
      if (io.some(function (k) { return /lsh/i.test(k.tag); }))
        them('LSH bể thành phẩm', 'Bể thành phẩm đầy',
          'Nâng phao tới ngưỡng LSH', 'Dừng cấp nước vào bể, hệ chuyển chờ',
          '≤ 2 s', 'Hạ mức, hệ tự chạy lại');
      if (co(/roskid|ro/)) {
        them('PSL hút bơm cao áp', 'Áp hút bơm cao áp thấp',
          'Đóng dần van hút hoặc bịt tạm đầu lấy mẫu để tụt áp',
          'TRIP bơm cao áp trước khi bơm chạy khô', '≤ 1 s',
          'Mở van, reset, khởi động lại theo trình tự');
        them('PSH đẩy màng', 'Áp sau bơm cao áp vượt ngưỡng',
          'Đóng dần van tiết lưu concentrate', 'TRIP bơm cao áp, báo động HH',
          '≤ 1 s', 'Mở van về vị trí cân chỉnh, reset');
        them('Chất lượng sau RO', 'Độ dẫn sau RO vượt ngưỡng HH',
          'Ép giá trị kênh CIT/QIT vượt ngưỡng bằng bộ phát dòng',
          'Báo động HH + nhắn tin; chuyển van xả bỏ, không cấp vào bể thành phẩm',
          '≤ 5 s', 'Trả giá trị về, xác nhận cảnh báo');
      }
      them('Chất lượng tại POU', 'Điện trở suất tại điểm dùng dưới ngưỡng',
        'Ép kênh QIT POU xuống dưới ' + (p.res || 18) + ' MΩ·cm',
        'Van ba ngả chuyển về xả/hồi bể, không cấp cho sản xuất; báo động',
        '≤ 5 s', 'Trả giá trị về, van tự trả vị trí cấp');
      var bomKep = EQ.filter(function (e) {
        return /pump|bom/.test(loai(e)) && (so(e.soBom, 1) > 1 || e.dup);
      });
      if (bomKep.length)
        them('Đổi bơm dự phòng', 'Bơm đang chạy (duty) mất phản hồi',
          'Cắt aptomat lộ bơm duty khi đang chạy',
          'Tự chuyển sang bơm standby, báo động H, không mất áp quá 3 s',
          '≤ 5 s', 'Đóng lại aptomat, reset, luân phiên trở lại');
      if (io.some(function (k) { return k.kieu === 'AO'; }))
        them('PID giữ áp mạch vòng', 'Đổi điểm đặt áp và thay đổi lượng tiêu thụ đột ngột',
          'Đổi setpoint ±0,5 bar; đóng/mở nhanh một nhánh sử dụng',
          'Áp về điểm đặt, quá điều chỉnh ≤ 10 %, ổn định trong 30 s, không dao động',
          '≤ 30 s', 'Trả setpoint về giá trị thiết kế');
      if (io.some(function (k) { return /ph/i.test(k.tag); }))
        them('pH nước xả', 'pH nước xả ra ngoài dải cho phép',
          'Ép kênh pH ra ngoài dải 6–9',
          'Dừng bơm xả ngoài, chạy trung hoà, báo động', '≤ 5 s',
          'Trả giá trị về dải, xác nhận cảnh báo');
      if (co(/vessel|filter/))
        them('Rửa ngược tự động', 'Kích rửa ngược theo chênh áp và theo thời gian',
          'Hạ ngưỡng chênh áp tạm thời hoặc chỉnh đồng hồ tới giờ đặt',
          'Chạy đúng trình tự rửa ngược: dừng cấp → rửa ngược → xả nhanh → về chạy',
          'Theo thời gian đặt từng bước', 'Trả ngưỡng và giờ về giá trị thiết kế');
      (lg.buoc || []).reduce(function (acc, b) {
        if (acc.indexOf(b.seq) < 0) acc.push(b.seq); return acc;
      }, []).forEach(function (s) {
        them('Trình tự', 'Chạy trọn ' + s, 'Kích từ HMI ở chế độ AUTO',
          'Đi hết các bước theo đúng điều kiện chuyển bước và thời gian trễ đã lập trình',
          'Theo bảng trình tự', 'Về trạng thái chờ');
      });
      them('Mất SCADA / HMI', 'Rút mạng hoặc tắt HMI khi hệ đang chạy',
        'Rút dây mạng giữa PLC và HMI',
        'PLC tiếp tục chạy độc lập theo chương trình, ghi cảnh báo mất truyền thông; ' +
        'không thiết bị nào tự dừng hay tự chạy', '≤ 10 s',
        'Cắm lại, HMI đồng bộ trạng thái, không mất dữ liệu nhật ký');

      /* Mọi báo động mức TRIP/HH đã khai ở tab điện đều phải có kịch bản thử.
         Đây là chỗ hai bảng dễ lệch nhau nhất — thêm báo động mà quên thử. */
      var daCo = d.map(function (r) { return String(r[2]).toLowerCase(); }).join(' | ');
      (lg.bao || []).forEach(function (b) {
        if (b.muc === 'H') return;
        var k = String(b.mo || '').toLowerCase();
        if (k && daCo.indexOf(k.slice(0, 14)) >= 0) return;
        them(b.ma || b.muc, b.mo + ' (mức ' + b.muc + ')',
          'Tạo điều kiện: ' + (b.nguong || 'theo ngưỡng đã cài'),
          b.tacDong || (b.muc === 'TRIP' ? 'Dừng thiết bị liên quan' : 'Cảnh báo và nhắn tin'),
          b.muc === 'TRIP' ? '≤ 1 s' : '≤ 5 s', b.xuLy || 'Trả về điều kiện bình thường');
      });

      var h = '<div class="svws-tq">' + n + ' kịch bản. Mọi báo động mức HH và TRIP ' +
        'khai trong bảng logic của tab điện đều tự sinh một kịch bản thử ở đây — ' +
        'thêm báo động mà quên thử là chuyện không xảy ra được nữa.</div>';
      h += bang('8.5 Thử khoá liên động và trình tự tự động — cổng G5',
        ['Mã', 'Nhóm', 'Kịch bản', 'Cách tạo điều kiện thử', 'Tác động mong đợi',
         'Thời gian đáp ứng', 'Cách khôi phục', 'Kết quả', 'Ký'], d);
      h += '<div class="svws-ghi">Logic an toàn, dừng khẩn cấp và điều kiện TRIP do ' +
        'công cụ soạn thảo là BẢN NHÁP. Kỹ sư có chứng chỉ phải rà và ký trước khi ' +
        'nạp vào nhà máy đang vận hành.</div>';
      return h;
    }

    // ================================================== 8.6 Công nghệ
    function congNghe() {
      /* Đánh số mục con bằng BỘ ĐẾM CHẠY, không bằng công thức theo số cụm RO:
         hệ không có lọc tinh hay không có MB thì công thức để lại khoảng trống
         trong mục lục, và người đọc tưởng mình đang cầm thiếu tờ. */
      var stt = 0;
      function s6() { return '8.6.' + (++stt) + ' '; }
      var h = '<div class="svws-tq">Chạy theo CHIỀU DÒNG, từng cụm một. Cụm sau chỉ ' +
        'được khởi động khi nước từ cụm trước đã đạt — đưa nước chưa đạt vào màng ' +
        'hay vào stack EDI là hỏng vật liệu, không sửa được bằng chỉnh thông số.</div>';

      var vs = loc(/vessel|filter/);
      if (vs.length) {
        var d = [];
        vs.forEach(function (e) {
          var D = so(e.D, so(e.dia, 900)) / 1000;
          var A = Math.PI * D * D / 4;
          var la = /gac|than|carbon/i.test(ten(e) + ' ' + (e.vl || '')) ? 'GAC' : 'MMF';
          var vbw = la === 'GAC' ? 12 : 12;          // m/h — nở lớp 20–50 %
          var Hl = so(e.Hlop, so(e.H, 1800) * 0.55) / 1000;
          d.push([ten(e), la,
            'Ø' + lam(D * 1000, 0) + ' mm · tiết diện ' + lam(A, 3) + ' m²',
            'Chiều cao lớp ' + lam(Hl, 2) + ' m → thể tích vật liệu ' +
              lam(A * Hl, 2) + ' m³',
            'Nạp theo lớp: sỏi đỡ → lớp thô → lớp mịn, đổ nước ngập trước khi nạp ' +
              'để vật liệu không rơi tự do làm vỡ hạt',
            'Rửa ngược ' + lam(vbw * A, 1) + ' m³/h (' + vbw + ' m/h) trong 15 phút, ' +
              'nở lớp ' + (la === 'GAC' ? '30–50' : '20–30') + ' %',
            'Xả nhanh xuôi dòng 5 phút · nước ra trong, độ đục ≤ 1 NTU' +
              (la === 'GAC' ? ' và không còn bụi than' : ''), null, null]);
        });
        h += bang(s6() + 'Nạp vật liệu lọc và rửa ngược lần đầu',
          ['Cột', 'Loại', 'Hình học', 'Khối lượng vật liệu', 'Cách nạp',
           'Lưu lượng rửa ngược thật', 'Tiêu chí đạt', 'Kết quả', 'Ký'], d,
          'Lưu lượng rửa ngược tính từ TIẾT DIỆN THẬT của cột trong bản vẽ, không ' +
          'lấy con số chung. Rửa thiếu thì bụi than đi thẳng vào màng RO.');
      }

      if (co(/cartridge/)) h += bang(s6() + 'Lọc tinh và kiểm SDI trước khi nạp màng',
        ['Bước', 'Việc', 'Thông số đặt', 'Tiêu chí đạt', 'Ghi nhận', 'Ký'], [
        ['1', 'Lắp lõi lọc mới đúng độ mịn thiết kế', '5 µm (hoặc theo thiết kế)',
         'Chênh áp ban đầu ≤ 0,3 bar', null, null],
        ['2', 'Chạy xả bỏ nước đầu qua lọc tinh', '15 phút', 'Nước ra trong, không sợi lõi',
         null, null],
        ['3', 'Đo SDI15 tại đầu vào màng', 'Phin 0,45 µm, áp 2,07 bar',
         'SDI15 ≤ 3 (bắt buộc ≤ 5). Không đạt thì KHÔNG nạp màng', null, null],
        ['4', 'Đo clo dư tự do tại đầu vào màng', '', '< 0,02 ppm — clo phá màng polyamide',
         null, null]
      ]);

      var ros = loc(/roskid|^ro$/);
      ros.forEach(function (e, i) {
        var pass = so(e.pass, i + 1);
        var pw = so(pass === 2 ? p.pRO2 : p.pRO1, 15);
        var rec = so(pass === 2 ? p.rec2 : p.rec1, 75);
        h += bang(s6() + 'Khởi động ' + ten(e) + ' (pass ' + pass + ')',
          ['Bước', 'Việc', 'Thông số đặt', 'Tiêu chí đạt', 'Ghi nhận', 'Ký'], [
          ['1', 'Nạp màng đúng chiều, bôi trơn o-ring bằng glycerin, lắp đầu bịt',
           'Đúng số phần tử mỗi vessel', 'Đủ số màng, ghi số sê-ri từng màng', null, null],
          ['2', 'Flush đuổi chất bảo quản — KHÔNG hồi lưu, xả bỏ toàn bộ',
           'Áp ≤ 4 bar, 30–60 phút', 'Nước thấm hết mùi, TOC/độ dẫn về nền', null, null],
          ['3', 'Tăng áp dần bằng van tiết lưu concentrate',
           'Tăng ≤ 0,7 bar mỗi 10 s tới ' + pw + ' bar',
           'Không sốc áp — sốc áp làm bung màng', null, null],
          ['4', 'Cân chỉnh thu hồi', 'Thu hồi đặt ' + rec + ' %',
           'Lưu lượng thấm và cô đặc đúng thiết kế ±5 %', null, null],
          ['5', 'Ghi BASELINE để chuẩn hoá', 'Ghi Qp · Qc · P cấp · P thấm · ΔP · ' +
           'T · độ dẫn cấp và thấm',
           'Quy về 25 °C theo công thức chuẩn hoá của hãng màng; đây là mốc so sánh ' +
           'cho toàn bộ vòng đời hệ', null, null],
          ['6', 'Kiểm loại muối', 'Tính từ độ dẫn cấp và thấm',
           'Loại muối ≥ 97 % (pass 1) — thấp hơn là dấu hiệu o-ring hở hoặc màng lỗi',
           null, null]
        ]);
      });

      if (ros.length > 1 || co(/edi/)) {
        h += bang(s6() + 'Nâng pH trước pass 2 / trước EDI',
          ['Bước', 'Việc', 'Thông số đặt', 'Tiêu chí đạt', 'Ghi nhận', 'Ký'], [
          ['1', 'Châm NaOH vào nước cấp pass 2', 'pH 8,5 – 9,0',
           'Nâng pH để CO2 chuyển thành bicarbonate và bị màng giữ lại — ' +
           'không nâng pH thì CO2 xuyên qua màng và đè tải lên EDI', null, null],
          ['2', 'Kiểm điểm châm và độ trộn', 'Đo pH cách điểm châm ≥ 10×DN',
           'pH ổn định, dao động ≤ ±0,2', null, null],
          ['3', 'Kiểm khả năng kết tủa', 'Tính LSI ở điều kiện cô đặc',
           'Không vượt ngưỡng kết tủa của antiscalant đang dùng', null, null]
        ]);
      }

      if (co(/edi/)) {
        var eds = loc(/edi/);
        var nStack = eds.reduce(function (a, e) {
          return a + so(e.soStack, Math.max(1, Math.ceil(Qtb / 5)));
        }, 0);
        h += bang(s6() + 'Khởi động EDI (' + nStack +
          ' stack — 5 m³/h mỗi stack)',
          ['Bước', 'Việc', 'Thông số đặt', 'Tiêu chí đạt', 'Ghi nhận', 'Ký'], [
          ['1', 'Kiểm ĐỦ 5 ĐIỀU KIỆN nước cấp trước khi mở seal — không đạt thì DỪNG',
           'Xem bảng bên dưới', 'Đủ cả 5, có số đo kèm chữ ký', null, null],
          ['2', 'Flush toàn bộ ba dòng bằng nước cấp, chưa cấp dòng DC',
           'Chạy 30 phút, xả bỏ', 'Không bọt khí, không rò, ba dòng thông', null, null],
          ['3', 'Cân chỉnh lưu lượng ba dòng',
           'Sản phẩm · cô đặc · điện cực theo bảng của hãng',
           'Đúng tỷ lệ ±5 %; áp sản phẩm luôn CAO HƠN áp cô đặc', null, null],
          ['4', 'Ramp dòng một chiều dần lên',
           'Từ 0 tới dòng làm việc trong 15–30 phút',
           'Không đóng dòng đột ngột; điện áp trong dải hãng cho phép', null, null],
          ['5', 'Chạy ổn định và ghi baseline',
           '2 – 4 giờ', 'Điện trở suất ra ≥ ' + (p.resEDI || 16) +
           ' MΩ·cm và còn tăng dần', null, null]
        ]);
        h += bang('Năm điều kiện nước cấp EDI — kiểm trước khi mở seal',
          ['#', 'Chỉ tiêu', 'Giới hạn', 'Nếu vượt', 'Số đo', 'Ký'], [
          ['1', 'Độ dẫn tương đương nước cấp', '≤ 40 µS/cm (sau 2 pass thường ≤ 5)',
           'Kiểm lại RO, không cấp vào EDI', null, null],
          ['2', 'Tổng anion yếu (CO2 + silica) quy về CaCO3', '≤ 25 ppm',
           'Nâng pH trước pass 2 hoặc bổ sung khử khí', null, null],
          ['3', 'Độ cứng tổng', '≤ 0,1 ppm CaCO3',
           'DỪNG — độ cứng đóng cặn trong ngăn cô đặc, hỏng stack vĩnh viễn', null, null],
          ['4', 'Clo dư tự do · oxy hoá', '< 0,02 ppm',
           'DỪNG — phá nhựa và màng trao đổi ion', null, null],
          ['5', 'Sắt · mangan · H2S', '≤ 0,01 ppm mỗi loại',
           'Xử lý ở tiền xử lý trước, không cấp vào EDI', null, null]
        ], 'Giới hạn tham khảo theo thông lệ; PHẢI đối chiếu với bảng của chính hãng ' +
           'stack đang dùng trước khi ký.');
      }

      if (co(/mixedbed/)) h += bang(s6() + 'Cột trao đổi ion tinh (MB)',
        ['Bước', 'Việc', 'Thông số đặt', 'Tiêu chí đạt', 'Ghi nhận', 'Ký'], [
        ['1', 'Nạp nhựa đúng tỷ lệ cation : anion, ngâm bằng nước DI',
         'Theo bảng thông số', 'Không nạp bằng nước máy', null, null],
        ['2', 'Xúc xuôi dòng bằng nước DI', 'Tới khi ra ổn định',
         'Điện trở suất ra ≥ ' + (p.res || 18) + ' MΩ·cm và TOC về nền', null, null],
        ['3', 'Ghi mốc ban đầu', '', 'Ghi thể tích nước đã qua để tính chu kỳ tái sinh',
         null, null]
      ]);

      if (co(/uv/)) h += bang(s6() + 'UV và điểm dùng (POU)',
        ['Bước', 'Việc', 'Thông số đặt', 'Tiêu chí đạt', 'Ghi nhận', 'Ký'], [
        ['1', 'Chạy đầy nước rồi mới bật đèn', 'Chờ 60 s ổn định',
         'Cường độ ≥ ngưỡng; liều ≥ ' + (p.uvd || 40) + ' mJ/cm²', null, null],
        ['2', 'Kiểm lọc cuối tại điểm dùng', 'Lọc 0,2 µm nếu thiết kế có',
         'Đã xả bỏ nước đầu theo hướng dẫn phin lọc', null, null],
        ['3', 'Đo chất lượng ngay tại vòi lấy nước', '',
         'Điện trở suất ≥ ' + (p.res || 18) + ' MΩ·cm tại POU', null, null]
      ]);

      h += bang(s6() + 'Sát trùng, thụ động hoá và cân áp mạch vòng',
        ['Bước', 'Việc', 'Thông số đặt', 'Tiêu chí đạt', 'Ghi nhận', 'Ký'], [
        ['1', 'Thụ động hoá (passivation) đoạn SS316 của mạch vòng',
         'Axit citric 2 % ở 50–60 °C, tuần hoàn 2–4 h (hoặc theo quy trình đã duyệt)',
         'Bề mặt thụ động, sắt hoà tan trong nước xúc về nền', null, null],
        ['2', 'Sát trùng toàn vòng',
         'Nước nóng 80 °C ≥ 30 phút tại điểm xa nhất, hoặc H2O2 / ozone theo quy trình',
         'Đạt nhiệt độ/nồng độ tại ĐIỂM XA NHẤT, không chỉ tại đầu ra', null, null],
        ['3', 'Xúc lại tới nền',
         'Xúc bằng nước DI', 'Điện trở suất về ≥ ' + (p.res || 18) +
         ' MΩ·cm, không dư hoá chất', null, null],
        ['4', 'Cân áp và vận tốc vòng',
         'Chỉnh van hồi để áp cuối vòng ≥ ' + (p.Ploop || 2) + ' bar',
         'Vận tốc trong ống vòng ≥ 1,0 m/s ở mọi nhánh — dưới ngưỡng này vi sinh ' +
         'bám thành ống', null, null],
        ['5', 'Kiểm từng điểm dùng', 'Mở lần lượt từng POU',
         'Áp và chất lượng tại điểm bất lợi nhất vẫn đạt', null, null]
      ]);

      h += bang(s6() + 'Trung hoà và kiểm soát nước xả',
        ['Bước', 'Việc', 'Thông số đặt', 'Tiêu chí đạt', 'Ghi nhận', 'Ký'], [
        ['1', 'Gom nước xả từ rửa ngược, flush, CIP về bể trung hoà', '',
         'Không xả thẳng ra cống trong suốt đợt chạy thử', null, null],
        ['2', 'Trung hoà trước khi thải', 'pH 6 – 9',
         'Đo và ghi trước mỗi lần xả; khoá liên động pH đã thử ở 8.5', null, null],
        ['3', 'Ghi khối lượng nước xả', '',
         'Dùng cho chỉ tiêu nghiệm thu lượng nước xả ở mục 8.8', null, null]
      ]);
      return h;
    }

    // ================================================== 8.7 Chạy thử 72 h
    function chayThu72() {
      var gio = so(p.gioChay, 72);
      var mau = [
        ['0 – 6', '0,5 × Qtb', lam(Qtb * 0.5, 1), 'Tải thấp ban đêm — kiểm bơm biến tần ' +
         'chạy ở tần số thấp mà không quá nhiệt'],
        ['6 – 12', 'Qmax', lam(Qmax, 1), 'Cao điểm — kiểm hệ giữ được lưu lượng và ' +
         'chất lượng ở công suất lớn nhất'],
        ['12 – 18', 'Qtb', lam(Qtb, 1), 'Tải thiết kế — lấy số liệu chuẩn hoá'],
        ['18 – 24', 'Dừng 1 h rồi Qtb', lam(Qtb, 1), 'Kiểm hệ tự dừng khi bể đầy và ' +
         'TỰ KHỞI ĐỘNG LẠI đúng trình tự, không cần người']
      ];
      var d = [], t = 0, i = 0;
      while (t < gio) {
        var m = mau[i % 4];
        var het = Math.min(t + 6, gio);
        d.push(['K-' + ('0' + (i + 1)).slice(-2), t + ' – ' + het + ' h',
          m[1], m[2] + ' m³/h', m[3], null, null]);
        t = het; i++;
      }
      var h = '<div class="svws-tq">Chạy ' + gio + ' giờ theo LỊCH TIÊU THỤ MÔ PHỎNG, ' +
        'không chạy một mức đều tay. Hệ chỉ chạy một mức thì vòng điều khiển không ' +
        'bao giờ bị thử, và lỗi sẽ nổ ra ở tuần đầu bàn giao.</div>';
      h += bang('8.7.1 Lịch tiêu thụ mô phỏng — cổng G7',
        ['Khối', 'Giờ tích luỹ', 'Chế độ', 'Lưu lượng lấy ra', 'Mục đích kiểm',
         'Đã chạy', 'Ký'], d);

      var sp = [];
      var n = 0;
      function themSP(vt, ct, ts, gh) {
        sp.push(['SP-' + (++n), vt, ct, ts, gh, null, null]);
      }
      themSP('Nước cấp đầu vào', 'pH · độ dẫn · độ cứng · Fe · clo dư · SDI · độ đục',
        '1 lần/ca (3 lần/ngày)', 'Trong dải nước nguồn thiết kế; clo dư < 0,02 ppm ' +
        'tại đầu vào màng');
      if (co(/vessel|filter/))
        themSP('Sau cụm lọc MMF/GAC', 'Độ đục · clo dư · chênh áp qua cột',
          '1 lần/ca', 'Độ đục ≤ 1 NTU · clo dư < 0,02 ppm · ΔP ≤ 0,7 bar');
      if (ros_len() >= 1)
        themSP('Nước thấm RO pass 1', 'Độ dẫn · lưu lượng thấm · lưu lượng cô đặc · ΔP',
          '2 giờ/lần', 'Loại muối ≥ 97 % · lưu lượng ±5 % baseline chuẩn hoá');
      if (ros_len() >= 2)
        themSP('Nước thấm RO pass 2', 'Độ dẫn · pH · lưu lượng',
          '2 giờ/lần', 'Độ dẫn ≤ 5 µS/cm · pH 8,5–9,0');
      if (co(/edi|mixedbed/))
        themSP('Sau EDI / MB', 'Điện trở suất · dòng và điện áp DC · lưu lượng ba dòng',
          '1 giờ/lần', 'Điện trở suất ≥ ' + (p.resEDI || 16) + ' MΩ·cm, ổn định');
      themSP('Điểm dùng cuối vòng (POU bất lợi nhất)',
        'Điện trở suất · TOC · nhiệt độ · áp · vi sinh (TVC) · endotoxin nếu có yêu cầu',
        'Điện trở suất liên tục; TOC 1 lần/ngày; vi sinh 1 lần vào ngày cuối',
        'Điện trở suất ≥ ' + (p.res || 18) + ' MΩ·cm · các chỉ tiêu còn lại theo ' +
        'tiêu chuẩn nước áp dụng cho dự án');
      h += bang('8.7.2 Sáu điểm lấy mẫu trong 72 giờ',
        ['Điểm', 'Vị trí', 'Chỉ tiêu', 'Tần suất', 'Giới hạn', 'Kết quả', 'Ký'], sp,
        'Mẫu vi sinh và TOC gửi phòng thí nghiệm được công nhận; niêm phong và ghi ' +
        'giờ lấy mẫu ngay tại chỗ.');

      h += bang('8.7.3 Nhật ký ghi trong suốt 72 giờ',
        ['Nhóm số liệu', 'Nội dung ghi', 'Tần suất'], [
        ['Lưu lượng', 'Cấp · thấm · cô đặc · xả · cấp vào vòng', '1 giờ'],
        ['Áp suất', 'Trước và sau từng cụm, áp cuối vòng', '1 giờ'],
        ['Chất lượng', 'Độ dẫn từng bậc, điện trở suất POU, pH, nhiệt độ', '1 giờ'],
        ['Điện', 'Dòng từng lộ, tần số biến tần, điện năng tiêu thụ luỹ kế', '2 giờ'],
        ['Sự kiện', 'Mọi báo động, mọi lần can thiệp tay, lý do và người xử lý',
         'Ngay khi xảy ra'],
        ['Hoá chất', 'Mức bồn, lượng tiêu thụ', '1 ca']
      ]);
      return h;
    }
    function ros_len() { return loc(/roskid|^ro$/).length; }

    // ================================================== 8.8 Nghiệm thu
    function nghiemThu() {
      /* Điện năng riêng phải tính theo công suất CHẠY ĐỒNG THỜI, không phải công
         suất lắp đặt: cụm 1 chạy 1 dừng có hai lộ nhưng chỉ một bơm quay. Cộng
         cả bơm dự phòng thì suất điện cam kết vống lên gần gấp rưỡi, và đó là con
         số công ty phải bồi thường nếu không đạt. */
      var goc = {}, tongKW = 0;
      tai.forEach(function (t) {
        if (t.duPhong) return;
        var g = String(t.tag || '').replace(/[A-Z]$/, '');   // P-101A và P-101B → P-101
        goc[g] = Math.max(goc[g] || 0, so(t.kW, 0));
      });
      Object.keys(goc).forEach(function (k) { tongKW += goc[k]; });
      var kwh = Qtb > 0 ? lam(tongKW * 0.75 / Qtb, 2) : 0;   // hệ số mang tải 0,75
      var rec = so(p.recHT, 0);
      if (!rec && p.rec1) rec = lam(so(p.rec1) * so(p.rec2, 100) / 100, 1);
      var d = [
        ['1', 'Công suất nước thành phẩm',
         '≥ ' + Qtb + ' m³/h liên tục, đạt ' + lam(Qtb * 24, 1) + ' m³/ngày',
         'Đọc FIT thành phẩm, đối chứng bằng đồng hồ siêu âm', null, null, null],
        ['2', 'Điện trở suất tại điểm dùng (POU)',
         '≥ ' + (p.res || 18) + ' MΩ·cm ở 25 °C, duy trì suốt 72 h',
         'Đo liên tục trên tuyến + đối chứng máy cầm tay đã hiệu chuẩn', null, null, null],
        ['3', 'Điện trở suất sau EDI',
         '≥ ' + (p.resEDI || 16) + ' MΩ·cm', 'Đo tại van lấy mẫu đầu ra EDI',
         null, null, null],
        ['4', 'Thu hồi toàn hệ',
         (rec ? '≥ ' + rec + ' %' : 'Theo cam kết hợp đồng'),
         'Tính từ lưu lượng thành phẩm chia lưu lượng nước cấp trong cùng khoảng thời gian',
         null, null, null],
        ['5', 'Điện năng riêng',
         (kwh ? '≤ ' + (p.kWh || kwh) + ' kWh/m³ nước thành phẩm' : 'Theo cam kết'),
         'Công tơ đầu vào tủ chia sản lượng trong 72 h' +
         (p.kWh ? '' : ' (ước tính từ ' + lam(tongKW, 1) + ' kW chạy đồng thời — đã ' +
          'trừ bơm dự phòng — với hệ số mang tải 0,75)'),
         null, null, null],
        ['6', 'Lượng nước xả',
         (p.xa ? '≤ ' + p.xa + ' m³/h' : 'Theo cân bằng nước thiết kế'),
         'Đo tại điểm xả chung trong 72 h', null, null, null],
        ['7', 'Vận hành tự động',
         'Không có can thiệp tay trong 72 h; mọi lần dừng/chạy do hệ tự quyết định',
         'Đếm số lần can thiệp trong nhật ký sự kiện — chỉ tiêu đạt khi bằng 0',
         null, null, null],
        ['8', 'Độ ồn và độ kín',
         'Ồn ≤ ' + (p.on || 85) + ' dBA đo tại 1 m, cao 1,5 m · không có điểm rò rỉ nào',
         'Máy đo ồn + đi kiểm toàn tuyến cuối đợt', null, null, null]
      ];
      var h = '<div class="svws-tq">Tám chỉ tiêu cam kết. Giá trị cam kết lấy từ ' +
        'bảng thông số thiết kế và bảng điện của chính tool — đổi thông số thiết kế ' +
        'là bảng nghiệm thu đổi theo, không phải sửa tay.</div>';
      h += bang('8.8 Nghiệm thu hiệu năng',
        ['TT', 'Chỉ tiêu cam kết', 'Giá trị cam kết', 'Phương pháp đo',
         'Số đo thực tế', 'Đạt / Không', 'Ký'], d);
      h += '<div class="svws-ghi">Không đạt một chỉ tiêu thì ghi rõ nguyên nhân, biện ' +
        'pháp khắc phục và thời hạn chạy lại phần liên quan — không ký nghiệm thu ' +
        '"có điều kiện" cho chỉ tiêu chất lượng nước.</div>';
      return h;
    }

    // ================================================== 8.9 Đào tạo & hồ sơ
    function daoTao() {
      var h = bang('8.9.1 Chương trình đào tạo 2 ngày',
        ['Buổi', 'Nội dung', 'Thời lượng', 'Đối tượng', 'Tài liệu', 'Đánh giá'], [
        ['Ngày 1 — sáng', 'Tổng quan công nghệ: vì sao có từng cụm, nước đi đâu, ' +
         'thông số nào quan trọng; đọc P&ID', '3 h', 'Vận hành + bảo trì',
         'P&ID, sơ đồ khối, bảng thông số', 'Hỏi đáp'],
        ['Ngày 1 — chiều', 'An toàn: hoá chất và MSDS, LOTO, điện, không gian hạn chế; ' +
         'sử dụng vòi rửa mắt', '3 h', 'Toàn bộ nhân sự vận hành',
         'MSDS, quy trình an toàn', 'Bài kiểm tra ngắn'],
        ['Ngày 2 — sáng', 'Thực hành trên HMI: khởi động · dừng · chuyển AUTO/MAN · ' +
         'đọc và xác nhận báo động · đổi điểm đặt', '3 h', 'Vận hành viên',
         'Sổ O&M, bảng trình tự', 'Thao tác thực tế có chấm'],
        ['Ngày 2 — chiều', 'Thực hành bảo trì: rửa ngược, thay lõi lọc, CIP, ghi nhật ký, ' +
         'xử lý 5 sự cố thường gặp', '3 h', 'Bảo trì + vận hành',
         'Sổ O&M, lịch bảo trì', 'Tình huống giả định']
      ], 'Người dự đào tạo phải là NGƯỜI SẼ VẬN HÀNH THẬT. Cử người khác học thay ' +
         'rồi truyền miệng là nguyên nhân của phần lớn sự cố trong ba tháng đầu.');

      h += bang('8.9.2 Danh mục hồ sơ bàn giao',
        ['Nhóm', 'Tài liệu', 'Dạng', 'Đủ / Thiếu', 'Ký nhận'], [
        ['Chất lượng', 'CO / CQ toàn bộ thiết bị và vật tư chính (bơm, màng, stack EDI, ' +
         'van, ống, vật liệu lọc)', 'Bản gốc hoặc bản sao có dấu', null, null],
        ['Bản vẽ', 'Hoàn công: P&ID · mặt bằng GA · bản vẽ chế tạo · sơ đồ điện · ' +
         'sơ đồ đấu nối PLC — đúng hiện trạng đã lắp', 'Giấy A3 + file gốc', null, null],
        ['Biên bản', 'MC · thử áp từng tuyến · xúc rửa · megger · chạy không tải · ' +
         'loop check · interlock · nạp vật liệu · baseline RO/EDI · nhật ký 72 h · ' +
         'nghiệm thu hiệu năng', 'Bản ký hai bên', null, null],
        ['Phần mềm', 'Backup chương trình PLC và HMI, sơ đồ mạng, tài khoản và mật khẩu ' +
         'quản trị, bản quyền phần mềm còn hiệu lực', 'File + văn bản bàn giao mật',
         null, null],
        ['Vận hành', 'Sổ O&M · lịch bảo trì · bảng xử lý sự cố · biểu mẫu nhật ký',
         'Giấy + file', null, null],
        ['Vật tư', 'Danh mục phụ tùng khuyến nghị dự trữ và nhà cung cấp',
         'Bảng', null, null],
        ['Bảo hành', 'Chứng chỉ bảo hành từng thiết bị, điều kiện và đầu mối liên hệ',
         'Văn bản', null, null],
        ['Pháp lý', 'Hồ sơ nghiệm thu PCCC, hồ sơ môi trường liên quan điểm xả, ' +
         'MSDS hoá chất', 'Bản sao có dấu', null, null],
        ['Đào tạo', 'Biên bản đào tạo có danh sách và chữ ký người dự', 'Bản ký', null, null]
      ]);
      return h;
    }

    // ================================================== kiểm tra & xuất
    function kiemTra() {
      loi = []; canhBao = [];
      if (!EQ.length) loi.push('Chưa khai thiết bị nào — không sinh được hồ sơ chạy thử.');
      if (!Qtb) loi.push('Thiếu params.Qavg — mọi lưu lượng trong mục 8.7 và 8.8 sẽ trống.');
      if (!p.res) canhBao.push('Thiếu params.res (điện trở suất cam kết tại POU) — ' +
        'mục 8.8 đang lấy mặc định 18 MΩ·cm.');
      var ts = dsTuyen();
      if (!ts.length) loi.push('Chưa có tuyến ống — mục 8.2 rỗng.');
      ts.forEach(function (t) {
        if (!t.service) canhBao.push('Tuyến ' + maTuyen(t) +
          ' chưa khai dịch vụ — áp thử đang lấy mặc định uPVC 9 bar.');
        t.cao = laCaoAp(t); t.pass = passCua(t);
        var a = apThu(t, p);
        if (a.ap && t.apLV && a.ap <= so(t.apLV))
          loi.push('Tuyến ' + maTuyen(t) + ': áp thử ' + a.ap +
            ' bar không lớn hơn áp làm việc — thử như vậy không phát hiện được rò.');
      });
      var noi = {};
      ts.forEach(function (t) { noi[t.from] = 1; noi[t.to] = 1; });
      EQ.forEach(function (e) {
        var id = e.id || e.tag;
        if (/panel|tu|mcc|plc/.test(loai(e))) return;
        if (!noi[id]) canhBao.push('Thiết bị ' + ten(e) +
          ' không nối vào tuyến ống nào — kiểm lại sổ tuyến ống.');
      });
      if (!io.length) loi.push('Chưa nạp bảng I/O — mục 8.4 không sinh được.');
      else if (!io.some(function (k) { return k.kieu === 'AI'; }))
        loi.push('Bảng I/O không có kênh AI nào — không có gì để hiệu chuẩn ở mục 8.4.');
      if (!tai.length) canhBao.push('Chưa nạp danh sách tải điện — mục 8.3 thiếu bảng ' +
        'kiểm từng lộ động cơ.');
      if (!(lg.bao || []).some(function (b) { return b.muc === 'TRIP'; }))
        canhBao.push('Bảng báo động chưa có mức TRIP nào — hệ không có gì được phép ' +
          'dừng máy, kiểm lại logic an toàn.');
      // chạy qua các mục để gom cảnh báo của chúng
      coKhi();
      return { loi: loi.slice(), canhBao: canhBao.slice(),
               soThietBi: EQ.length, soTuyen: ts.length,
               soKenhAI: io.filter(function (k) { return k.kieu === 'AI'; }).length };
    }

    /** Số bản vẽ riêng cho hồ sơ chạy thử: <mã dự án>-CM-00n. */
    function soBanVe(i) { return ma + '-CM-' + ('00' + (i || 1)).slice(-3); }

    var MUC = [
      ['8.0', 'Tổng quan chạy thử — bảy cổng, nhân sự, điều kiện tiên quyết, an toàn', tongQuan],
      ['8.1', 'Checklist hoàn thành cơ khí (MC)', coKhi],
      ['8.2', 'Thử áp và xúc rửa đường ống', duongOng],
      ['8.3', 'Kiểm tra và chạy nguội phần điện', dien],
      ['8.4', 'Hiệu chuẩn thiết bị đo và loop check', thietBiDo],
      ['8.5', 'Thử khoá liên động và trình tự tự động', interlock],
      ['8.6', 'Chạy công nghệ từng cụm theo chiều dòng', congNghe],
      ['8.7', 'Chạy thử liên tục ' + so(p.gioChay, 72) + ' giờ', chayThu72],
      ['8.8', 'Nghiệm thu hiệu năng', nghiemThu],
      ['8.9', 'Đào tạo và hồ sơ bàn giao', daoTao]
    ];

    function tatCa() {
      // Dải đầu trang mang logo công ty: tab xem trên màn hình cũng phải nhận
      // ra là hồ sơ của Sóng Việt, không chỉ lúc in.
      var dau = global.SVWSKT
        ? global.SVWSKT.dauTrang('Chạy thử & nghiệm thu — ' + ma) : '';
      return dau + MUC.map(function (m, i) {
        return muc(m[0], m[1] + '   [' + soBanVe(i + 1) + ']', m[2]() || '');
      }).join('');
    }

    /**
     * In khổ A3 NGANG, mỗi mục một tờ có số bản vẽ riêng -CM-00n.
     * Khung tên do tool truyền vào (hàm nhận số bản vẽ và tên bản vẽ) để dùng
     * chung một khung tên với các tab khác — không vẽ khung riêng ở đây.
     */
    function inA3(k) {
      /* Khung tên lấy từ SVWSKT nên có LOGO công ty và trùng đúng khung tên
         của các bản vẽ khác; chỉ khi mở file rời thiếu thư viện mới dùng bản
         rút gọn bên dưới, để tờ in không bao giờ trắng đầu trang. */
      var K = global.SVWSKT;
      var khung = typeof k === 'function' ? k
        : K ? function (sbv, tbv) { return K.html({ tenBV: tbv, soBV: sbv }); }
        : function (sbv, tbv) {
        return '<div class="svws-cm-khung"><b>' + esc(o.ten || ma) + '</b>' +
          '<span>' + esc(tbv) + '</span><span>Số bản vẽ: ' + esc(sbv) + '</span>' +
          '<span>Rev: ' + esc(o.rev || '0') + '</span>' +
          '<span>Lập: ' + esc(o.nguoiLap || '') + '</span>' +
          '<span>Ngày: ' + esc(o.ngay || '') + '</span></div>';
      };
      var than = MUC.map(function (m, i) {
        var noiDung = m[2]() || '';
        if (!noiDung) return '';
        return '<section class="svws-cm-trang">' +
          khung(soBanVe(i + 1), m[0] + ' ' + m[1]) +
          '<h3 class="svws-cm-h">' + esc(m[0] + '  ' + m[1]) + '</h3>' +
          noiDung + '</section>';
      }).join('');
      var w = global.open('', '_blank');
      if (!w) return null;
      w.document.write('<!doctype html><html lang="vi"><head><meta charset="utf-8">' +
        '<title>' + esc(ma) + ' — Chạy thử &amp; nghiệm thu</title><style>' +
        CSS + CSS_IN + (global.SVWSKT ? global.SVWSKT.CSS : '') +
        '</style></head><body>' + than + '</body></html>');
      w.document.close();
      w.focus();
      setTimeout(function () { w.print(); }, 400);
      return w;
    }

    return {
      tongQuan: tongQuan, coKhi: coKhi, duongOng: duongOng, dien: dien,
      thietBiDo: thietBiDo, interlock: interlock, congNghe: congNghe,
      chayThu: chayThu72, nghiemThu: nghiemThu, daoTao: daoTao,
      tatCa: tatCa, inA3: inA3, soBanVe: soBanVe, kiemTra: kiemTra,
      MUC: MUC.map(function (m, i) {
        return { so: m[0], ten: m[1], bv: soBanVe(i + 1) };
      })
    };
  }

  // ------------------------------------------------------------------- CSS
  var CSS = '.svws-bang{width:100%;border-collapse:collapse;font-size:11.5px;' +
    'font-family:' + FONT + ';margin:6px 0 16px}' +
    '.svws-bang th{background:#0b2545;color:#fff;padding:6px 8px;text-align:left;' +
    'font-weight:600;border:1px solid #0b2545}' +
    '.svws-bang td{padding:5px 8px;border:1px solid #cfd8e3;vertical-align:top}' +
    '.svws-bang tbody tr:nth-child(even){background:#f4f8fb}' +
    '.svws-bang td.svws-ky{background:#fffdf5;min-width:74px}' +
    '.svws-cuon{overflow-x:auto;max-width:100%}' +
    '.svws-bang-tieu{margin:14px 0 4px;font:600 13px ' + FONT + ';color:#0b2545}' +
    '.svws-ghi{font-size:11.5px;color:#33475b;margin:2px 0 6px;font-style:italic}' +
    '.svws-tq{background:#eef4fb;border-left:4px solid #0b2545;padding:8px 12px;' +
    'font:600 12.5px ' + FONT + ';color:#0b2545;margin:8px 0 14px}' +
    '.svws-cm-h{font:700 15px ' + FONT + ';color:#0b2545;margin:20px 0 8px;' +
    'padding-bottom:5px;border-bottom:2px solid #b3271e}' +
    '.svws-cm-khung{display:flex;gap:14px;flex-wrap:wrap;font:11px ' + FONT + ';' +
    'border:1px solid #0b2545;padding:5px 9px;margin-bottom:8px;color:#0b2545}';

  var CSS_IN = '@page{size:A3 landscape;margin:10mm}' +
    'body{margin:0;font-family:' + FONT + '}' +
    '.svws-cm-trang{page-break-after:always}' +
    '.svws-cm-trang:last-child{page-break-after:auto}' +
    '.svws-bang{page-break-inside:auto}' +
    '.svws-bang tr{page-break-inside:avoid}' +
    '.svws-bang thead{display:table-header-group}' +
    '.svws-cuon{overflow:visible}'+
    '.svws-bang{min-width:0 !important;width:100%}';

  global.SVWSCM = {
    version: '1.0',
    tao: tao,
    CSS: CSS, CSS_IN: CSS_IN,
    CSS_TAG: '<style>' + CSS + '@media print{' + CSS_IN + '}</style>' +
      (global.SVWSKT ? global.SVWSKT.CSS_TAG : ''),
    GATE: GATE, CK: CK, TEN_DV: TEN_DV,
    apThu: apThu, vatLieu: vatLieu
  };
})(window);
