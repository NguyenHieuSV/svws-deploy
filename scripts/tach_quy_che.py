"""Tách TOÀN VĂN từng quy chế từ Sổ tay Word → quy_che_toan_van.json (HTML gọn) cho tab Tổng quan › Quy chế công ty.

Chạy lại MỖI KHI so_tay_quy_che.docx đổi (thêm / sửa văn bản):
    python scripts/tach_quy_che.py
Cần python-docx trên MÁY SOẠN (không cần trên máy chủ — máy chủ chỉ đọc file JSON đã sinh).

Sổ tay được dàn bằng định dạng trực tiếp (không dùng style), nên nhận dạng theo định dạng:
  · canh giữa, cỡ ≥ 15  → tên văn bản          · canh giữa, cỡ 13, đậm → CHƯƠNG / PHẦN
  · đậm, cách trên 7pt  → Điều / Mục           · thụt 0,635 cm → khoản · thụt 1,27 cm → điểm
  · bảng không viền     → khối chữ ký          · bảng có viền  → bảng nội dung
Các văn bản ngăn nhau bằng đoạn ngắt trang; 2 khối đầu là bìa và mục lục."""
import os, sys, json, html as _html
from datetime import datetime
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
GOC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
NGUON = os.path.join(GOC, "so_tay_quy_che.docx")
RA = os.path.join(GOC, "quy_che_toan_van.json")


def _co(rp, tag):
    e = rp.find(W + tag) if rp is not None else None
    return e is not None and e.get(W + "val") not in ("0", "false")


def runs(el):
    """[(chữ, đậm, nghiêng, cỡ pt)] — gồm cả run trong hyperlink; tab → khoảng trắng, xuống dòng mềm → \\n."""
    out = []
    for r in el.iter(W + "r"):
        t = "".join((x.text or "") if x.tag == W + "t" else (" " if x.tag == W + "tab" else ("\n" if x.tag == W + "br" and x.get(W + "type") != "page" else ""))
                    for x in r)
        rp = r.find(W + "rPr")
        sz = rp.find(W + "sz") if rp is not None else None
        if t:
            out.append((t, _co(rp, "b"), _co(rp, "i"), (int(sz.get(W + "val")) / 2.0) if sz is not None else None))
    return out


def inline(rs):
    out = []
    for t, b, i, _ in rs:
        s = _html.escape(t, quote=False).replace("\n", "<br>")
        if i:
            s = f"<i>{s}</i>"
        if b:
            s = f"<b>{s}</b>"
        out.append(s)
    return "".join(out).replace("</b><b>", "").replace("</i><i>", "")


def chu(rs):
    return _html.escape("".join(t for t, _, _, _ in rs).replace("\n", " ").strip(), quote=False)


def bang(tb, d):
    t = Table(tb, d)
    bd = tb.tblPr.find(W + "tblBorders")
    vien = bd is not None and bd.find(W + "top") is not None and bd.find(W + "top").get(W + "val") not in (None, "none", "nil")
    hang = tb.findall(W + "tr")
    if not vien:                                        # khối chữ ký: mỗi ô một cột, các dòng nối bằng <br>
        o = [f'<div class="qcKy{" qcKy1" if len(hang[0].findall(W + "tc")) == 1 else ""}">']
        for tc in hang[0].findall(W + "tc"):
            o.append("<div>" + "<br>".join(inline(runs(p)) or "&nbsp;" for p in tc.findall(W + "p")) + "</div>")
        o.append("</div>")
        return "".join(o)
    rong = []
    for tc in hang[0].findall(W + "tc"):
        w = tc.tcPr.find(W + "tcW") if tc.tcPr is not None else None
        rong.append(float(w.get(W + "w")) if (w is not None and (w.get(W + "w") or "").replace(".", "").isdigit()) else 0.0)
    o = ['<table class="qcTb">']
    if rong and all(rong):
        o.append("<colgroup>" + "".join(f'<col style="width:{x / sum(rong) * 100:.1f}%">' for x in rong) + "</colgroup>")
    dau = [runs(tc) for tc in hang[0].findall(W + "tc")]
    co_dau = len(hang) > 1 and all(all(b for _, b, _, _ in r) for r in dau if r)
    for i, tr in enumerate(hang):
        o.append("<tr>")
        for tc in tr.findall(W + "tc"):
            ps = tc.findall(W + "p")
            giua = any((Paragraph(p, d).alignment == 1) for p in ps)
            nd = "<br>".join(x for x in (inline(runs(p)) for p in ps) if x) or "&nbsp;"
            if i == 0 and co_dau:
                o.append(f"<th>{chu(runs(tc)) or '&nbsp;'}</th>")
            else:
                o.append(f'<td{" class=c" if giua else ""}>{nd}</td>')
        o.append("</tr>")
    o.append("</table>")
    return "".join(o)


def van_ban(els, d, ma_so):
    o, n_ch, n_dieu, tieu_de = [], 0, 0, None
    for el in els:
        if el.tag == W + "tbl":
            o.append(bang(el, d))
            continue
        if el.tag != W + "p":
            continue
        rs = runs(el)
        if not "".join(t for t, _, _, _ in rs).strip():
            continue
        p = Paragraph(el, d)
        pf = p.paragraph_format
        co = max((s for _, _, _, s in rs if s), default=12.0)
        dam = all(b for t, b, _, _ in rs if t.strip())
        li = pf.left_indent.cm if pf.left_indent else 0.0
        sb = pf.space_before.pt if pf.space_before else 0.0
        al = p.alignment
        if al == 1:                                     # canh giữa
            if co >= 15:
                tieu_de = tieu_de or chu(rs)
                o.append(f'<h3 class="qcT">{chu(rs)}</h3>')
            elif co == 13 and dam:
                o.append(f'<h4 class="qcCh" id="qc{ma_so}c{n_ch}">{chu(rs)}</h4>'); n_ch += 1
            else:
                o.append(f'<p class="qcC">{inline(rs)}</p>')
        elif dam and abs(sb - 7.0) < 0.6 and li == 0 and al is None:
            o.append(f'<h5 class="qcDieu" id="qc{ma_so}d{n_dieu}">{chu(rs)}</h5>'); n_dieu += 1
        else:
            lop = "qcK2" if li > 1.0 else ("qcK1" if li > 0.3 else "qcP")
            if al == 2:
                lop += " qcR"
            elif al == 0:
                lop += " qcL"
            o.append(f'<p class="{lop}">{inline(rs)}</p>')
    return {"tieu_de": tieu_de, "so_chuong": n_ch, "so_dieu": n_dieu, "html": "".join(o)}


def main():
    d = Document(NGUON)
    khoi, cur = [], []
    for el in d.element.body:
        if el.tag == W + "sectPr":
            continue
        la_ngat = el.tag == W + "p" and el.find(f".//{W}br[@{W}type='page']") is not None and not Paragraph(el, d).text.strip()
        if la_ngat:
            khoi.append(cur); cur = []
        else:
            cur.append(el)
    khoi.append(cur)
    vb = khoi[2:]                                       # bỏ bìa + mục lục
    muc_luc = [[c.text.strip() for c in r.cells] for r in d.tables[0].rows]
    assert len(vb) == len(muc_luc), f"Số văn bản tách được ({len(vb)}) khác số dòng mục lục ({len(muc_luc)})"
    out = {}
    for (so, ma, ten), els in zip(muc_luc, vb):
        out[so] = dict(van_ban(els, d, so), ma=ma, ten_muc_luc=ten)
    json.dump({"cap_nhat": datetime.now().strftime("%Y-%m-%d %H:%M"), "van_ban": out},
              open(RA, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    sys.stdout.reconfigure(encoding="utf-8")
    for so, v in out.items():
        print(f"{so} {v['ma']:8s} chương/phần {v['so_chuong']:2d} · điều/mục {v['so_dieu']:3d} · {len(v['html']) / 1024:5.1f} KB · {v['tieu_de']}")
    print("→", os.path.normpath(RA), f"{os.path.getsize(RA) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
