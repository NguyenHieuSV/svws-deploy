<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SVWS — Hệ thống quản trị</title>
<style>
  :root{
    --ink:#0F2C44; --teal:#0E7C86; --teal-d:#0a5c64; --mint:#2EC4B6;
    --surface:#EAF1F5; --card:#FFFFFF; --muted:#5B7186; --line:#DCE6EC;
    --amber:#B45309; --amber-bg:#FAEEDA; --red:#B91C1C; --red-bg:#FBEAEA;
    --green:#0F766E; --green-bg:#E1F5EE; --blue-bg:#E6F1FB; --blue:#0C447C;
    --radius:12px; --shadow:0 6px 22px rgba(10,61,98,.10);
    --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
  }
  *{box-sizing:border-box}
  html,body{margin:0;height:100%}
  body{font-family:var(--sans);color:var(--ink);background:var(--surface);
       -webkit-font-smoothing:antialiased;font-size:14px;line-height:1.5}
  button{font-family:inherit;cursor:pointer}
  .hidden{display:none!important}
  ::-webkit-scrollbar{width:10px;height:10px}
  ::-webkit-scrollbar-thumb{background:#c4d3dc;border-radius:8px}

  /* ---------- LOGIN ---------- */
  #login{min-height:100%;display:grid;place-items:center;padding:24px;
    background:radial-gradient(1200px 600px at 70% -10%, #12506b 0%, #0F2C44 55%)}
  .login-card{width:100%;max-width:400px;background:var(--card);border-radius:16px;
    box-shadow:0 24px 60px rgba(0,0,0,.30);padding:30px 28px}
  .brand{display:flex;align-items:center;gap:11px;margin-bottom:6px}
  .logo{width:40px;height:40px;border-radius:10px;background:linear-gradient(135deg,var(--teal),var(--mint));
    display:grid;place-items:center;color:#fff;font-weight:800;font-size:18px;letter-spacing:.5px}
  .brand h1{font-size:18px;margin:0;letter-spacing:.3px}
  .brand .tag{font-size:11px;color:var(--muted);margin-top:1px}
  .login-card h2{font-size:15px;margin:22px 0 4px}
  .login-card p.sub{color:var(--muted);margin:0 0 18px;font-size:12.5px}
  label{display:block;font-size:12px;font-weight:600;color:var(--muted);margin:12px 0 5px}
  input,select{width:100%;padding:10px 12px;border:1px solid var(--line);border-radius:9px;
    font-size:14px;font-family:inherit;background:#fff;color:var(--ink)}
  input:focus,select:focus{outline:2px solid var(--teal);outline-offset:1px;border-color:transparent}
  .btn{display:inline-flex;align-items:center;justify-content:center;gap:7px;width:100%;
    padding:11px 14px;border:0;border-radius:9px;font-weight:700;font-size:14px}
  .btn-primary{background:var(--teal);color:#fff}
  .btn-primary:hover{background:var(--teal-d)}
  .btn-ghost{background:transparent;color:var(--teal);border:1px solid var(--line)}
  .btn-ghost:hover{background:var(--surface)}
  .or{display:flex;align-items:center;gap:10px;color:var(--muted);font-size:11px;margin:16px 0}
  .or::before,.or::after{content:"";height:1px;background:var(--line);flex:1}
  .login-foot{margin-top:16px;font-size:11px;color:var(--muted)}
  details.adv{margin-top:14px}
  details.adv summary{font-size:12px;color:var(--muted);cursor:pointer}
  .msg{margin-top:12px;font-size:12.5px;padding:9px 11px;border-radius:8px;display:none}
  .msg.err{display:block;background:var(--red-bg);color:var(--red)}

  /* ---------- APP SHELL ---------- */
  #app{display:grid;grid-template-columns:248px 1fr;grid-template-rows:auto 1fr;
    grid-template-areas:"side top" "side main";height:100%}
  .topbar{grid-area:top;background:var(--card);border-bottom:1px solid var(--line);
    display:flex;align-items:center;gap:14px;padding:0 20px;height:58px}
  .topbar .pagetitle{font-weight:700;font-size:15px}
  .topbar .spacer{flex:1}
  .demo-pill{display:flex;align-items:center;gap:8px;background:var(--amber-bg);color:var(--amber);
    border-radius:20px;padding:5px 8px 5px 12px;font-size:12px;font-weight:600}
  .demo-pill select{width:auto;padding:4px 8px;border-radius:14px;font-size:12px;font-weight:700;
    border:1px solid #e6cfa0;background:#fff;color:var(--ink)}
  .whoami{text-align:right;line-height:1.25}
  .whoami b{font-size:13px}.whoami span{font-size:11px;color:var(--muted)}
  .icon-btn{border:1px solid var(--line);background:#fff;border-radius:8px;padding:7px 10px;font-size:12px;color:var(--ink)}
  .icon-btn:hover{background:var(--surface)}

  .sidebar{grid-area:side;background:var(--ink);color:#cfe0e8;display:flex;flex-direction:column;min-height:0}
  .sidebar .brand{padding:16px 18px;margin:0;border-bottom:1px solid rgba(255,255,255,.08)}
  .sidebar .brand h1{color:#fff}.sidebar .brand .tag{color:#9fc0cd}
  .nav{padding:10px 10px;overflow:auto;flex:1}
  .nav-group{font-size:10.5px;text-transform:uppercase;letter-spacing:.8px;color:#7fa3b3;
    padding:14px 10px 6px}
  .nav a{display:flex;align-items:center;gap:11px;padding:9px 11px;border-radius:9px;
    color:#cfe0e8;text-decoration:none;font-size:13.5px;font-weight:500;margin-bottom:2px}
  .nav a:hover{background:rgba(255,255,255,.07);color:#fff}
  .nav a.active{background:var(--teal);color:#fff}
  .nav a .ico{width:18px;height:18px;flex:none;opacity:.9}
  .nav a .lbl{flex:1}
  .lvl{font-size:9.5px;font-weight:800;letter-spacing:.4px;padding:2px 6px;border-radius:20px;
    text-transform:uppercase}
  .lvl.XEM{background:rgba(12,68,124,.25);color:#bcd8f5}
  .lvl.THAO_TAC{background:rgba(46,196,182,.22);color:#9af0e4}
  .lvl.DUYET{background:rgba(180,83,9,.30);color:#f4cd96}
  .lvl.QUAN_TRI{background:rgba(155,135,245,.25);color:#d6cffe}
  .sidebar .foot{padding:12px 16px;border-top:1px solid rgba(255,255,255,.08);font-size:11px;color:#85a7b6}

  .main{grid-area:main;overflow:auto;padding:22px 26px}
  .crumb{font-size:12px;color:var(--muted);margin-bottom:3px}
  .h-row{display:flex;align-items:flex-end;gap:12px;margin-bottom:18px}
  .h-row h2{margin:0;font-size:21px;letter-spacing:.2px}
  .h-row p{margin:0;color:var(--muted);font-size:13px}

  .cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px;margin-bottom:22px}
  .stat{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:16px 18px;box-shadow:var(--shadow)}
  .stat .k{font-size:12px;color:var(--muted);font-weight:600}
  .stat .v{font-size:25px;font-weight:800;margin-top:6px;letter-spacing:-.5px}
  .stat .v.small{font-size:19px}
  .stat .d{font-size:11.5px;margin-top:4px}
  .stat.accent{background:linear-gradient(135deg,var(--teal),#0a6470);border:0;color:#fff}
  .stat.accent .k{color:#bdeae4}.stat.accent .d{color:#bdeae4}

  .panel{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);box-shadow:var(--shadow);margin-bottom:18px;overflow:hidden}
  .panel-h{display:flex;align-items:center;gap:10px;padding:14px 18px;border-bottom:1px solid var(--line)}
  .panel-h h3{margin:0;font-size:14.5px}
  .panel-h .spacer{flex:1}
  .panel-b{padding:6px 0}
  table{width:100%;border-collapse:collapse;font-size:13px}
  th{text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.4px;color:var(--muted);
    padding:10px 18px;border-bottom:1px solid var(--line);font-weight:700}
  td{padding:11px 18px;border-bottom:1px solid #eef3f6}
  tr:last-child td{border-bottom:0}
  tr:hover td{background:#f7fafc}
  .num{text-align:right;font-variant-numeric:tabular-nums}
  .badge{font-size:11px;font-weight:700;padding:3px 9px;border-radius:20px;white-space:nowrap}
  .b-cho{background:var(--amber-bg);color:var(--amber)}
  .b-ok{background:var(--green-bg);color:var(--green)}
  .b-tc{background:var(--red-bg);color:var(--red)}
  .b-info{background:var(--blue-bg);color:var(--blue)}
  .btn-sm{padding:6px 12px;border-radius:7px;font-size:12.5px;font-weight:700;border:0;background:var(--teal);color:#fff}
  .btn-sm:hover{background:var(--teal-d)}
  .btn-sm.ghost{background:#fff;border:1px solid var(--line);color:var(--ink)}
  .btn-sm:disabled{background:#e8eef2;color:#9fb0bb;cursor:not-allowed}
  .empty{padding:40px 18px;text-align:center;color:var(--muted)}
  .empty .big{font-size:15px;font-weight:600;color:var(--ink);margin-bottom:4px}
  .formrow{display:flex;gap:10px;flex-wrap:wrap;align-items:end;padding:14px 18px}
  .formrow .f{flex:1;min-width:120px}
  .formrow label{margin-top:0}
  .note{font-size:12px;color:var(--muted);padding:0 18px 14px}
  .perm-denied{font-size:12px;color:var(--amber);background:var(--amber-bg);padding:8px 12px;border-radius:8px;margin:0 18px 14px;display:inline-block}
  .tabs{display:flex;gap:2px;border-bottom:1px solid var(--line);margin-bottom:18px;flex-wrap:wrap}
  .tabs button{background:none;border:0;padding:10px 16px;font-size:13.5px;font-weight:600;color:var(--muted);border-bottom:2px solid transparent;cursor:pointer}
  .tabs button:hover{color:var(--ink)}
  .tabs button.active{color:var(--teal);border-bottom-color:var(--teal)}
  textarea:focus{outline:2px solid var(--teal);outline-offset:1px}
  .ac-box{position:relative}
  .ac-box input{width:100%;padding:10px 12px;border:1px solid var(--line);border-radius:9px;font-family:inherit;font-size:14px;box-sizing:border-box}
  .ac-results{margin-top:6px;background:var(--card);border:1px solid var(--line);border-radius:10px;box-shadow:var(--shadow);max-height:220px;overflow:auto;display:none}
  .ac-results.show{display:block}
  .ac-results>div{padding:9px 12px;cursor:pointer;font-size:14px;border-bottom:1px solid var(--surface)}
  .ac-results>div:last-child{border-bottom:0}
  .ac-results>div:hover{background:var(--blue-bg)}
  .ac-results .muted{color:var(--muted);cursor:default}
  .ac-results .muted:hover{background:transparent}
  .chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
  .chip{display:inline-flex;align-items:center;gap:8px;background:var(--green-bg);color:var(--ink);border:1px solid var(--mint);border-radius:999px;padding:4px 6px 4px 12px;font-size:13px}
  .chip button{border:0;background:var(--card);color:var(--ink);border-radius:999px;width:18px;height:18px;line-height:1;cursor:pointer;font-size:14px}
  tr.qh td{background:var(--red-bg)}

  /* toast */
  #toast{position:fixed;right:20px;bottom:20px;display:flex;flex-direction:column;gap:8px;z-index:50}
  .toast{background:var(--ink);color:#fff;padding:11px 15px;border-radius:10px;font-size:13px;
    box-shadow:0 10px 30px rgba(0,0,0,.25);max-width:340px;animation:slidein .25s ease}
  .toast.ok{background:#0e6b5f}.toast.err{background:#9a2727}
  @keyframes slidein{from{transform:translateY(8px);opacity:0}to{transform:none;opacity:1}}
  @media (prefers-reduced-motion:reduce){.toast{animation:none}}

  @media(max-width:760px){
    #app{grid-template-columns:1fr;grid-template-areas:"top" "main"}
    .sidebar{position:fixed;left:0;top:0;bottom:0;width:248px;z-index:40;transform:translateX(-100%);transition:.2s}
    .sidebar.open{transform:none}
    .menu-toggle{display:inline-flex!important}
    .backdrop{position:fixed;inset:0;background:rgba(0,0,0,.4);z-index:39}
  }
  .menu-toggle{display:none}
</style>
</head>
<body>

<!-- ================= LOGIN ================= -->
<div id="login">
  <div class="login-card">
    <div class="brand">
      <div class="logo">SV</div>
      <div><h1>Song Việt Water Solutions</h1><div class="tag">Hệ thống quản trị hợp nhất</div></div>
    </div>
    <h2>Đăng nhập</h2>
    <p class="sub">Dùng tài khoản nội bộ. Giao diện chỉ hiện các phần thuộc quyền của bạn.</p>
    <label for="email">Email</label>
    <input id="email" type="email" placeholder="ten@svws.vn" value="ceo@svws.vn" autocomplete="username">
    <label for="pw">Mật khẩu</label>
    <input id="pw" type="password" placeholder="••••••••" value="matkhau123" autocomplete="current-password">
    <div class="msg err" id="loginErr"></div>
    <button class="btn btn-primary" style="margin-top:18px" onclick="doLogin()">Đăng nhập</button>
    <div class="or">hoặc</div>
    <button class="btn btn-ghost" onclick="enterDemo()">Xem demo (không cần máy chủ)</button>
    <details class="adv">
      <summary>Cấu hình máy chủ API</summary>
      <label for="api">Địa chỉ API</label>
      <input id="api" type="text" value="http://localhost:8000">
      <script>(function(){try{if(location.protocol==='http:'||location.protocol==='https:'){var a=document.getElementById('api');if(a)a.value=location.origin;}}catch(e){}})();</script>
      <div class="login-foot">Khi chạy backend cục bộ (<code>make run</code>), giữ nguyên giá trị này.</div>
    </details>
  </div>
</div>

<!-- ================= APP ================= -->
<div id="app" class="hidden">
  <aside class="sidebar" id="sidebar">
    <div class="brand"><div class="logo">SV</div>
      <div><h1>SVWS</h1><div class="tag">Quản trị hợp nhất</div></div></div>
    <nav class="nav" id="nav"></nav>
    <div class="foot" id="sideFoot"></div>
  </aside>
  <header class="topbar">
    <button class="icon-btn menu-toggle" onclick="toggleMenu()">☰</button>
    <div class="pagetitle" id="pageTitle">Tổng quan</div>
    <div class="spacer"></div>
    <div class="demo-pill hidden" id="demoPill">
      Demo · vai trò
      <select id="rolePicker" data-nocbx onchange="switchRole(this.value)"></select>
    </div>
    <div class="whoami"><b id="waName">—</b><br><span id="waRole">—</span></div>
    <button class="icon-btn" onclick="logout()">Đăng xuất</button>
  </header>
  <main class="main" id="main"></main>
</div>

<div id="toast"></div>

<script>
/* ============ Cấu hình & dữ liệu ============ */
const MODULES = {
  dashboard:{label:"Tổng quan", group:"Điều hành"},
  dieu_hanh:{label:"Overall Operation", group:"Điều hành"},
  ban_hang:{label:"Bán hàng", group:"Thương mại"},
  crm:{label:"Khách hàng (CRM)", group:"Thương mại"},
  kho:{label:"Kho hàng", group:"Cung ứng"},
  de_xuat:{label:"Đề xuất mua hàng", group:"Cung ứng", permKey:"ncc"},
  ncc:{label:"Nhà cung cấp", group:"Cung ứng"},
  du_an:{label:"Dự án", group:"Dịch vụ"},
  cho_thue:{label:"Cho thuê", group:"Dịch vụ"},
  ke_toan:{label:"Kế toán", group:"Tài chính"},
  tai_chinh:{label:"Tài chính", group:"Tài chính"},
  nhan_su:{label:"Nhân sự & Lương", group:"Nội bộ"},
  tai_lieu:{label:"Tài liệu", group:"Nội bộ"},
  cau_hinh:{label:"Cấu hình", group:"Nội bộ"},
};
const GROUP_ORDER = ["Điều hành","Thương mại","Cung ứng","Dịch vụ","Tài chính","Nội bộ"];
const LVL_LABEL = {XEM:"Xem", THAO_TAC:"Thao tác", DUYET:"Duyệt", QUAN_TRI:"Quản trị"};
const RANK = {KHONG:0, XEM:1, THAO_TAC:2, DUYET:3, QUAN_TRI:4};
/* Overall Operation — luồng nghiệp vụ Bán hàng → Kế toán + mô tả shortcut */
const DH_FLOW = [
  {g:"Thương mại", items:["ban_hang","crm"]},
  {g:"Cung ứng & Kho", items:["de_xuat","ncc","kho"]},
  {g:"Dịch vụ", items:["du_an","cho_thue"]},
  {g:"Tài chính — Kế toán", items:["ke_toan","tai_chinh"]},
  {g:"Nội bộ & Hỗ trợ", items:["nhan_su","tai_lieu","dashboard","cau_hinh"]},
];
const DH_CHAIN = ["ban_hang","crm","de_xuat","ncc","kho","du_an","ke_toan","tai_chinh"];
/* Cột module cho ma trận phân quyền (theo permKey thực trong bảng phan_quyen) */
const DH_MODCOLS = ["dieu_hanh","ban_hang","crm","ncc","kho","du_an","cho_thue","ke_toan","tai_chinh","nhan_su","tai_lieu","dashboard","cau_hinh"];
const DH_COLLABEL = {dieu_hanh:"Overall Op",ban_hang:"Bán hàng",crm:"CRM",ncc:"Cung ứng/NCC",kho:"Kho",du_an:"Dự án",cho_thue:"Cho thuê",ke_toan:"Kế toán",tai_chinh:"Tài chính",nhan_su:"Nhân sự",tai_lieu:"Tài liệu",dashboard:"Tổng quan",cau_hinh:"Cấu hình"};
const MUC_TEN = {KHONG:"Không",XEM:"Xem",THAO_TAC:"Thao tác",DUYET:"Duyệt",QUAN_TRI:"Quản trị"};
const DH_DESC = {
  dashboard:"Bức tranh điều hành theo thời gian thực",
  ban_hang:"Báo giá · đơn hàng · chiến dịch · cơ hội",
  crm:"Khách hàng 360° · liên lạc · phản hồi",
  de_xuat:"Đề xuất mua hàng (sinh từ tồn kho/dự án)",
  ncc:"Nhà cung cấp · RFQ · đơn mua (PO)",
  kho:"Tồn kho · nhập/xuất · cảnh báo tồn min",
  du_an:"Dự án · chỉ tiêu · mốc · an toàn · KPI",
  cho_thue:"Hợp đồng thuê · công nợ thuê",
  ke_toan:"Hóa đơn · hạch toán · HĐĐT · công nợ",
  tai_chinh:"Dòng tiền · vay · quỹ · trích lập",
  nhan_su:"Nhân sự & Lương",
  tai_lieu:"Tài liệu nội bộ",
  cau_hinh:"Cấu hình hệ thống",
};
function ico(){return '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/></svg>';}

const ROLE_NAME = {CEO:"Giám đốc",TP_KD:"Trưởng P. Kinh doanh",NV_KD:"NV Kinh doanh",
  NV_CRM:"NV Chăm sóc KH",TP_CU:"Trưởng P. Cung ứng",NV_MUA:"NV Mua hàng",THUKHO:"Thủ kho",
  KTT:"Kế toán trưởng",NV_KT:"NV Kế toán",TP_DA:"Trưởng dự án",NV_DA:"NV Dự án",
  NV_THUE:"NV Cho thuê",NV_HCNS:"NV Hành chính-NS",ADMIN:"Admin / IT"};

/* Ma trận quyền (đồng bộ với SVWS_seed_rbac) — dùng cho chế độ demo */
const X="XEM",T="THAO_TAC",D="DUYET",A="QUAN_TRI";
const DEMO_PERM = {
  CEO:{dashboard:D,dieu_hanh:A,ban_hang:D,crm:D,kho:D,ncc:D,du_an:D,cho_thue:D,ke_toan:D,tai_chinh:D,nhan_su:D,tai_lieu:D,cau_hinh:X},
  TP_KD:{ban_hang:D,crm:D,kho:X,tai_lieu:T,dashboard:X},
  NV_KD:{ban_hang:T,crm:T,kho:X,tai_lieu:X,dashboard:X},
  NV_CRM:{ban_hang:X,crm:T,tai_lieu:X,dashboard:X},
  TP_CU:{ban_hang:X,kho:D,ncc:D,tai_lieu:T,dashboard:X},
  NV_MUA:{kho:X,ncc:T,tai_lieu:X,dashboard:X},
  THUKHO:{kho:T,ncc:X,tai_lieu:X,dashboard:X},
  KTT:{nhan_su:X,ban_hang:X,ke_toan:D,tai_chinh:D,kho:X,ncc:X,du_an:X,cho_thue:X,tai_lieu:X,dashboard:X},
  NV_KT:{ban_hang:X,ke_toan:T,tai_chinh:T,kho:X,ncc:X,du_an:X,tai_lieu:X,dashboard:X},
  TP_DA:{tai_chinh:X,kho:X,du_an:D,cho_thue:X,tai_lieu:T,dashboard:X},
  NV_DA:{kho:X,du_an:T,tai_lieu:T,dashboard:X},
  NV_THUE:{crm:X,kho:T,cho_thue:T,tai_lieu:T,dashboard:X},
  NV_HCNS:{nhan_su:T,tai_lieu:T,dashboard:X},
  ADMIN:{nhan_su:X,ban_hang:X,crm:X,ke_toan:X,tai_chinh:X,kho:X,ncc:X,du_an:X,cho_thue:X,tai_lieu:X,dashboard:X,cau_hinh:A},
};
/* Hạn mức duyệt (demo) */
const HANMUC = {
  bao_gia:{TP_KD:100e6, CEO:null},
  po:{TP_CU:10e6, CEO:null},
  chi_phi_du_an:{TP_DA:5e6, KTT:50e6, CEO:null},
};
/* Dữ liệu demo */
const DEMO = {
  dongtien:{tong_da_thu:120e6, con_phai_thu:86.4e6, con_phai_tra:34.2e6},
  canhbao:{congno_qua_han:2, hd_sap_het_han:1},
  hang_hoa:[
    {id:1,ma:"BOM-01",ten:"Bơm chìm 3kW",loai:"THIET_BI",don_vi:"cái",so_luong:48,ton_min:5,ton_max:60,gia_ban:12500000},
    {id:2,ma:"HC-PAC",ten:"Hóa chất keo tụ PAC",loai:"HOA_CHAT",don_vi:"kg",so_luong:80,ton_min:100,ton_max:500,gia_ban:18000},
    {id:3,ma:"MBR-01",ten:"Màng MBR",loai:"VAT_TU",don_vi:"tấm",so_luong:12,ton_min:4,ton_max:20,gia_ban:9500000},
    {id:4,ma:"HC-ANTI",ten:"Antiscalant chống cáu cặn RO",loai:"HOA_CHAT",don_vi:"lít",so_luong:25,ton_min:40,ton_max:200,gia_ban:85000},
    {id:5,ma:"HC-CLO",ten:"Chlorine 70%",loai:"HOA_CHAT",don_vi:"kg",so_luong:140,ton_min:50,ton_max:400,gia_ban:32000},
  ],
  phieu_kho:[
    {id:1,so:"NHAP-20260601-1",loai:"NHAP",ngay:"2026-06-01",chi_tiet:[{hang_hoa_id:1,ma:"BOM-01",ten:"Bơm chìm 3kW",don_vi:"cái",so_luong:50}]},
    {id:2,so:"XUAT-20260610-2",loai:"XUAT",ngay:"2026-06-10",chi_tiet:[{hang_hoa_id:2,ma:"PAC-01",ten:"Hóa chất PAC",don_vi:"kg",so_luong:120},{hang_hoa_id:3,ma:"MBR-01",ten:"Màng MBR",don_vi:"tấm",so_luong:2}]},
  ],
  bao_gia:[
    {id:1,so:"BG-0001",khach:"Cty Dệt may X",tong_tien:80e6,trang_thai:"CHO_DUYET"},
    {id:2,so:"BG-0002",khach:"KCN Sóng Thần",tong_tien:150e6,trang_thai:"CHO_DUYET"},
    {id:3,so:"BG-0003",khach:"Nhà máy giấy An Bình",tong_tien:42e6,trang_thai:"DA_DUYET"},
  ],
  ncc:{
    suppliers:[
      {id:1,ma:"NCC-01",ten:"Cty Hóa chất Việt Mỹ",email:"sale@vietmy.vn",han_muc_cong_no:800e6,diem_danh_gia:4.5,blacklist:false},
      {id:2,ma:"NCC-02",ten:"TM Thiết bị Đông Á",email:"info@donga.vn",han_muc_cong_no:300e6,diem_danh_gia:3.8,blacklist:false},
      {id:3,ma:"NCC-03",ten:"Vật tư Hải Long",email:"hailong@vt.vn",han_muc_cong_no:100e6,diem_danh_gia:2.0,blacklist:true},
    ],
    don_mua:[
      {id:1,so:"PO-0001",ncc:"Cty Hóa chất Việt Mỹ",tong_tien:8e6,trang_thai:"CHO_DUYET"},
      {id:2,so:"PO-0002",ncc:"TM Thiết bị Đông Á",tong_tien:15e6,trang_thai:"CHO_DUYET"},
      {id:3,so:"PO-0003",ncc:"Cty Hóa chất Việt Mỹ",tong_tien:3.5e6,trang_thai:"DA_DUYET"},
    ],
    yeu_cau:[
      {id:1,hang:"Hóa chất PAC",so_luong:120,ly_do:"TON_DUOI_MIN"},
    ],
  },
  don_hang:[
    {id:1,so:"DH-0001",khach:"Cty Dệt may X",tong_tien:80e6,trang_thai:"DA_XUAT",
      tep:[{id:1,loai:"PO",ten_file:"PO_DetMayX_2026.pdf",kich_thuoc:248000},
           {id:2,loai:"HOP_DONG",ten_file:"HopDong_DetMayX.pdf",kich_thuoc:512000}]},
    {id:2,so:"DH-0002",khach:"KCN Sóng Thần",tong_tien:150e6,trang_thai:"MOI",tep:[]},
  ],
  don_mua:[
    {id:1,so:"PO-2026-01",nha_cung_cap_id:1,don_hang_id:1,tong_tien:55e6,trang_thai:"DA_DUYET",trang_thai_nhan:"DU",ngay_hen_giao:"2026-06-10",
      chi_tiet:[{id:11,hang_hoa_id:1,ten:"Bơm chìm 3kW",so_luong:5,don_gia:11e6,so_luong_nhan:5}]},
    {id:2,so:"PO-2026-02",nha_cung_cap_id:1,don_hang_id:2,tong_tien:120e6,trang_thai:"DA_DUYET",trang_thai_nhan:"MOT_PHAN",ngay_hen_giao:"2026-06-25",
      chi_tiet:[{id:21,hang_hoa_id:3,ten:"Màng MBR",so_luong:40,don_gia:3e6,so_luong_nhan:20}]},
    {id:3,so:"PO-2026-03",nha_cung_cap_id:2,don_hang_id:null,tong_tien:40e6,trang_thai:"DA_DUYET",trang_thai_nhan:"CHUA",ngay_hen_giao:"2026-06-05",
      chi_tiet:[{id:31,hang_hoa_id:2,ten:"Hóa chất PAC",so_luong:200,don_gia:200000,so_luong_nhan:0}]},
  ],
  cong_no_ncc:[
    {id:1,nha_cung_cap_id:1,so_tien:55e6,da_thanh_toan:55e6,han:"2026-06-30",trang_thai:"DA_TRA"},
    {id:2,nha_cung_cap_id:1,so_tien:60e6,da_thanh_toan:0,han:"2026-05-10",trang_thai:"CHUA_TRA"},
    {id:3,nha_cung_cap_id:2,so_tien:35e6,da_thanh_toan:0,han:"2026-03-01",trang_thai:"CHUA_TRA"},
    {id:4,nha_cung_cap_id:1,so_tien:20e6,da_thanh_toan:0,han:"2026-07-10",trang_thai:"CHUA_TRA"},
  ],
  de_xuat:[
    {id:1,hang_hoa_id:2,ten_hh:"Hóa chất PAC",so_luong:200,don_gia:200000,nha_cung_cap_id:1,don_hang_id:2,ngay_can:"2026-07-01",ly_do:"Phục vụ đơn DH-0002",trang_thai:"MOI",don_mua_id:null},
    {id:2,hang_hoa_id:1,ten_hh:"Bơm chìm 3kW",so_luong:3,don_gia:11000000,nha_cung_cap_id:2,don_hang_id:1,ngay_can:"2026-06-28",ly_do:"Thay bơm hỏng tại công trình",trang_thai:"DA_DUYET",don_mua_id:null},
  ],
  bao_gia:[
    {id:1,nha_cung_cap_id:2,hang_hoa_id:2,don_gia:190000,hieu_luc_den:"2026-08-31",nguon:"THU_CONG"},
  ],
  chien_dich:[
    {id:1,ten:"Chào hàng giải pháp MBR Q3",tieu_de:"Giải pháp xử lý nước cho {ten_kh}",
      noi_dung:"Kính gửi {ten_kh}, SVWS xin giới thiệu giải pháp MBR tiết kiệm 30% chi phí vận hành...",
      bo_loc_abc:"A",trang_thai:"CHO_DUYET",
      tep:[{id:101,ten_file:"Brochure_MBR_SVWS.pdf",kich_thuoc:512000}]},
    {id:2,ten:"Ưu đãi bảo trì cuối năm",tieu_de:"Ưu đãi bảo trì hệ thống cho {ten_kh}",
      noi_dung:"Kính gửi {ten_kh}, nhân dịp cuối năm...",bo_loc_abc:null,trang_thai:"DA_GUI",
      ket_qua:{GUI_OK:2,BO_QUA:1},tep:[]},
  ],
  khach_email:[
    {ten:"Cty Dệt may X",email:"detmayx@kh.vn",abc:"A"},
    {ten:"KCN Sóng Thần",email:"songthan@kh.vn",abc:"A"},
    {ten:"Nhà máy giấy An Bình",email:"",abc:"B"},
  ],
  khach:[
    {id:1,ma:"KH-01",ten:"Cty Dệt may X",email:"detmayx@kh.vn",phan_loai_abc:"A"},
    {id:2,ma:"KH-02",ten:"KCN Sóng Thần",email:"songthan@kh.vn",phan_loai_abc:"A"},
    {id:3,ma:"KH-03",ten:"Nhà máy giấy An Bình",email:"",phan_loai_abc:"B"},
    {id:4,ma:"KH-04",ten:"Cty Thực phẩm Cầu Tre",email:"cautre@kh.vn",phan_loai_abc:"B"},
    {id:5,ma:"KH-05",ten:"Cty Bia Sài Gòn",email:"biasaigon@kh.vn",phan_loai_abc:"A"},
    {id:6,ma:"KH-06",ten:"Bệnh viện Đa khoa Thủ Đức",email:"bvthuduc@kh.vn",phan_loai_abc:"C"},
    {id:7,ma:"KH-07",ten:"Cty Nhuộm Thành Công",email:"nhuomtc@kh.vn",phan_loai_abc:"A"},
  ],
  lien_lac:{
    1:[{kenh:"EMAIL",huong:"DI",tieu_de:"Báo giá hệ thống lọc RO",noi_dung:"Đã gửi báo giá kèm brochure.",gui_tu:"sv-sales@watersolutions.company",trang_thai:"GUI_OK",thoi_diem:"2026-06-10 09:20"},
       {kenh:"GOI",huong:"DI",noi_dung:"Gọi xác nhận nhu cầu, hẹn khảo sát thứ 5.",trang_thai:"GHI_NHAN",thoi_diem:"2026-06-09 15:00"}],
    2:[], 3:[],
  },
  phan_hoi:[],
  cong_viec:[],
  co_hoi:[],
  tai_san_ct:[
    {id:1,ma:"CT-RO-01",ten:"Hệ thống RO di động 10 m³/h",loai:"HE_THONG",nguyen_gia:850000000,gia_thue_thang:35000000,khau_hao_thang:7080000,tinh_trang:"DANG_THUE",khach_hang:"Cty Dệt may X",vi_tri:"KCN Sóng Thần"},
    {id:2,ma:"CT-MBR-02",ten:"Cụm MBR container 200 m³/ngày",loai:"HE_THONG",nguyen_gia:1200000000,gia_thue_thang:48000000,khau_hao_thang:10000000,tinh_trang:"SAN_SANG",khach_hang:null,vi_tri:"Kho SVWS"},
    {id:3,ma:"CT-BOM-03",ten:"Tổ máy bơm & tủ điện dự phòng",loai:"THIET_BI",nguyen_gia:180000000,gia_thue_thang:6000000,khau_hao_thang:1500000,tinh_trang:"BAO_TRI",khach_hang:null,vi_tri:"Xưởng"},
  ],
  chi_phi_vh:[
    {id:1,tai_san:"Hệ thống RO di động 10 m³/h",ma_ban_hang:"CT-RO-01",loai_chi_phi:"VAT_TU",so_tien:6000000,ngay:"2026-06-05",mo_ta:"Thay lõi lọc & màng tiền xử lý",nguon:"DE_XUAT_MUA"},
    {id:2,tai_san:"Tổ máy bơm & tủ điện dự phòng",ma_ban_hang:"CT-BOM-03",loai_chi_phi:"SUA_CHUA",so_tien:3500000,ngay:"2026-06-15",mo_ta:"Sửa cuộn dây bơm",nguon:"BAO_TRI"},
  ],
  bao_tri_ct:[
    {id:1,tai_san:"Hệ thống RO di động 10 m³/h",ma:"CT-RO-01",ten_cong_viec:"Vệ sinh màng RO & thay tiền lọc",chu_ky_ngay:90,ngay_ke_tiep:"2026-07-10",trang_thai:"KE_HOACH",qua_han:false,chi_phi_du_kien:5000000},
    {id:2,tai_san:"Tổ máy bơm & tủ điện dự phòng",ma:"CT-BOM-03",ten_cong_viec:"Bảo dưỡng động cơ & tủ điện",chu_ky_ngay:60,ngay_ke_tiep:"2026-06-10",trang_thai:"KE_HOACH",qua_han:true,chi_phi_du_kien:2000000},
  ],
  dx_thue:[
    {id:1,hang_hoa:"Màng MBR",ma_hh:"MBR-01",loai:"VAT_TU",so_luong:2,don_gia:9500000,thanh_tien:19000000,cho_thue_ma:"CT-MBR-02",trang_thai:"MOI",ngay:"2026-06-18",da_dong_bo:false,ly_do:"Chuẩn bị bàn giao cụm MBR"},
    {id:2,hang_hoa:"Antiscalant chống cáu cặn RO",ma_hh:"HC-ANTI",loai:"HOA_CHAT",so_luong:60,don_gia:85000,thanh_tien:5100000,cho_thue_ma:"CT-RO-01",trang_thai:"MOI",ngay:"2026-06-19",da_dong_bo:false,ly_do:"Bổ sung hóa chất vận hành RO"},
  ],
  hd_thue:[
    {id:1,so:"HDT-20260101-1",khach_hang_id:1,doi_tuong:"THIET_BI",gia_thue:35000000,ngay_ket_thuc:"2026-12-31",trang_thai:"HIEU_LUC"},
  ],
  cham_soc:[
    {id:1,khach_hang_id:1,loai:"GOI",noi_dung:"Chăm sóc sau bán đơn DH-0001 (+7 ngày)",ngay_hen:"2026-06-12",trang_thai:"CHO",csat:null},
    {id:2,khach_hang_id:2,loai:"EMAIL",noi_dung:"Gửi tài liệu kỹ thuật bổ sung theo yêu cầu",ngay_hen:"2026-06-18",trang_thai:"CHO",csat:null},
    {id:3,khach_hang_id:1,loai:"KHIEU_NAI",noi_dung:"Phản ánh bơm phát tiếng ồn sau lắp đặt",ngay_hen:"2026-06-15",trang_thai:"CHO",csat:null,created_at:"2026-06-15"},
    {id:4,khach_hang_id:3,loai:"GOI",noi_dung:"Hỏi thăm vận hành hệ thống MBR",ngay_hen:"2026-05-20",trang_thai:"HOAN_THANH",csat:4.5},
    {id:5,khach_hang_id:4,loai:"SINH_NHAT",noi_dung:"Gửi lời chúc & ưu đãi dịp kỷ niệm hợp tác",ngay_hen:"2026-07-01",trang_thai:"CHO",csat:null},
  ],
  _phanHoiMau:[
    {message_id:"dm-1",tu_email:"detmayx@kh.vn",tieu_de:"Re: Giải pháp xử lý nước cho Cty Dệt may X",noi_dung:"Cảm ơn SVWS. Bên tôi quan tâm, vui lòng gửi báo giá chi tiết cho công suất 500 m3/ngày và thời gian thi công."},
    {message_id:"dm-2",tu_email:"phongmua@congtymoi.vn",tieu_de:"Hỏi về hệ thống RO công nghiệp",noi_dung:"Chúng tôi cần tư vấn hệ RO cho nhà máy mới. Vui lòng liên hệ lại."},
    {message_id:"dm-3",tu_email:"songthan@kh.vn",tieu_de:"Ngừng nhận email",noi_dung:"Vui lòng hủy đăng ký, chúng tôi không nhận email quảng cáo nữa."},
    {message_id:"dm-4",tu_email:"biasaigon@kh.vn",tieu_de:"Auto-reply: Vắng mặt",noi_dung:"Tôi đang đi công tác, hồi âm tự động. Sẽ phản hồi sau."},
    {message_id:"dm-5",tu_email:"bvthuduc@kh.vn",tieu_de:"Sự cố hệ thống lọc",noi_dung:"Hệ thống bị sự cố, nước ra vẫn đục, rất không hài lòng, cần xử lý gấp."},
  ],
};

/* ============ Trạng thái ============ */
let S = {mode:"demo", api:"", token:"", role:"", roleName:"", email:"", perm:{}, page:"dashboard"};

/* ============ Tiện ích ============ */
const $=s=>document.querySelector(s);
const vnd=n=>new Intl.NumberFormat('vi-VN').format(Math.round(n))+" ₫";
function toast(msg,type){const t=document.createElement('div');t.className='toast '+(type||'');t.textContent=msg;
  $("#toast").appendChild(t);setTimeout(()=>t.remove(),3800);}
async function api(path,opts={}){
  const h=Object.assign({'Content-Type':'application/json'},opts.headers||{});
  if(S.token) h['Authorization']='Bearer '+S.token;
  const r=await fetch(S.api+path,Object.assign({},opts,{headers:h}));
  const txt=await r.text(); let data; try{data=JSON.parse(txt)}catch{data=txt}
  if(!r.ok){const e=new Error((data&&data.detail)||('Lỗi '+r.status));e.status=r.status;e.detail=(data&&data.detail);throw e;}
  return data;
}
async function apiUpload(path,formData){
  const h={}; if(S.token) h['Authorization']='Bearer '+S.token;   // KHÔNG set Content-Type để trình duyệt tự thêm boundary
  const r=await fetch(S.api+path,{method:'POST',headers:h,body:formData});
  const txt=await r.text(); let data; try{data=JSON.parse(txt)}catch{data=txt}
  if(!r.ok){const e=new Error((data&&data.detail)||('Lỗi '+r.status));e.status=r.status;e.detail=(data&&data.detail);throw e;}
  return data;
}
function can(mod,lvl){return RANK[S.perm[pmod(mod)]||"KHONG"]>=RANK[lvl];}
function pmod(m){return (MODULES[m]&&MODULES[m].permKey)||m;}

/* ============ Đăng nhập ============ */
async function doLogin(){
  const email=$("#email").value.trim(), pw=$("#pw").value, api_=$("#api").value.trim().replace(/\/$/,'');
  $("#loginErr").classList.remove('err');
  try{
    const form=new URLSearchParams({username:email,password:pw});
    const r=await fetch(api_+"/auth/login",{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:form});
    if(!r.ok) throw new Error('Sai email hoặc mật khẩu');
    const {access_token}=await r.json();
    S={mode:"live",api:api_,token:access_token,page:"dashboard"};
    const q=await api("/auth/quyen-cua-toi");
    S.role=q.vai_tro; S.roleName=q.ten_vai_tro; S.email=q.email; S.perm=q.quyen;
    startApp();
  }catch(e){
    const m=$("#loginErr"); m.classList.add('err');
    m.textContent = (e.message&&e.message.includes('Failed to fetch'))
      ? "Không kết nối được máy chủ API. Hãy chạy backend (make run) hoặc bấm “Xem demo”."
      : (e.message||"Đăng nhập thất bại");
  }
}
function enterDemo(){
  S={mode:"demo",api:"",token:"",page:"dashboard"};
  setRoleDemo("CEO"); startApp();
  $("#demoPill").classList.remove('hidden');
  const rp=$("#rolePicker"); rp.innerHTML=Object.keys(DEMO_PERM).map(r=>`<option value="${r}">${r} — ${ROLE_NAME[r]}</option>`).join('');
  rp.value="CEO";
}
function setRoleDemo(role){S.role=role;S.roleName=ROLE_NAME[role];S.email=role.toLowerCase()+"@svws.vn (demo)";S.perm=DEMO_PERM[role];}
function switchRole(role){setRoleDemo(role);S.page="dashboard";renderNav();go("dashboard");}

/* ============ Khởi động app ============ */
function startApp(){
  $("#login").classList.add('hidden'); $("#app").classList.remove('hidden');
  $("#waName").textContent=S.roleName; $("#waRole").textContent=S.role+(S.mode==="demo"?" · demo":"");
  $("#sideFoot").textContent = S.mode==="demo" ? "Chế độ demo · dữ liệu mẫu" : "Kết nối: "+S.api;
  renderNav(); go(canSee("dashboard")?"dashboard":firstAllowed());
  _initCbxObserver();
}
function canSee(mod){return !!S.perm[pmod(mod)];}
function firstAllowed(){return Object.keys(MODULES).find(m=>S.perm[pmod(m)])||"dashboard";}

function renderNav(){
  const groups={};
  Object.keys(MODULES).forEach(m=>{ if(!S.perm[pmod(m)])return;
    const g=MODULES[m].group;(groups[g]=groups[g]||[]).push(m);});
  let html="";
  GROUP_ORDER.forEach(g=>{ if(!groups[g])return;
    html+=`<div class="nav-group">${g}</div>`;
    groups[g].forEach(m=>{const lv=S.perm[pmod(m)];
      html+=`<a href="#" data-m="${m}" onclick="go('${m}');return false">
        ${ico()}<span class="lbl">${MODULES[m].label}</span>
        <span class="lvl ${lv}">${LVL_LABEL[lv]||lv}</span></a>`;});
  });
  $("#nav").innerHTML=html; highlight();
}
function highlight(){document.querySelectorAll('#nav a').forEach(a=>a.classList.toggle('active',a.dataset.m===S.page));}
function toggleMenu(){$("#sidebar").classList.toggle('open');}

/* ============ Điều hướng ============ */
function go(mod){ S.khSel=null; if(!S.perm[pmod(mod)]){toast("Bạn không có quyền vào "+(MODULES[mod]?.label||mod),"err");return;}
  S.page=mod; $("#pageTitle").textContent=MODULES[mod].label; highlight();
  $("#sidebar").classList.remove('open');
  const m=$("#main"); m.scrollTop=0;
  ({dashboard:viewDashboard,dieu_hanh:viewDieuHanh,crm:viewCRM,cho_thue:viewChoThue,kho:viewKho,ban_hang:viewBanHang,de_xuat:viewDeXuat,ncc:viewNCC,ke_toan:viewKeToan,tai_chinh:viewTaiChinh,nhan_su:viewNhanSu,du_an:viewDuAn}[mod]||viewGeneric)(m,mod);
}

/* ---------- Tổng quan ---------- */
async function viewDashboard(m){
  m.innerHTML=head("Tổng quan","Bức tranh điều hành theo thời gian thực");
  let dt=DEMO.dongtien, cb=DEMO.canhbao;
  if(S.mode==="live"){ try{dt=await api("/tai-chinh/dong-tien");}catch{} 
    try{const q=await api("/cho-thue/sap-het-han");cb={...cb,hd_sap_het_han:q.so_hop_dong_sap_het_han};}catch{} }
  m.innerHTML+=`<div class="cards">
    <div class="stat accent"><div class="k">Đã thu</div><div class="v">${vnd(dt.tong_da_thu||0)}</div><div class="d">Luỹ kế</div></div>
    <div class="stat"><div class="k">Còn phải thu</div><div class="v small">${vnd(dt.con_phai_thu||0)}</div><div class="d" style="color:var(--amber)">Theo dõi công nợ</div></div>
    <div class="stat"><div class="k">Còn phải trả</div><div class="v small">${vnd(dt.con_phai_tra||0)}</div><div class="d">Nhà cung cấp</div></div>
    <div class="stat"><div class="k">Cảnh báo</div><div class="v small">${(cb.congno_qua_han||0)+(cb.hd_sap_het_han||0)} việc</div><div class="d" style="color:var(--red)">Công nợ quá hạn · HĐ sắp hết hạn</div></div>
  </div>`;
  m.innerHTML+=`<div class="panel"><div class="panel-h"><h3>Việc cần chú ý</h3></div><div class="panel-b">
    <table><thead><tr><th>Loại</th><th>Nội dung</th><th>Mức độ</th></tr></thead><tbody>
    <tr><td>Công nợ</td><td>${cb.congno_qua_han||0} công nợ phải thu quá hạn > 30 ngày</td><td><span class="badge b-tc">Cao</span></td></tr>
    <tr><td>Cho thuê</td><td>${cb.hd_sap_het_han||0} hợp đồng sắp hết hạn (≤30 ngày)</td><td><span class="badge b-cho">Vừa</span></td></tr>
    <tr><td>Kho</td><td>Hóa chất PAC dưới mức tồn tối thiểu</td><td><span class="badge b-cho">Vừa</span></td></tr>
    </tbody></table></div></div>`;
}

/* ---------- Overall Operation (điều hành tổng thể) ---------- */
function _dhTile(mod){
  if(!MODULES[mod])return '';
  const ok=canSee(mod), lv=S.perm[pmod(mod)], lb=MODULES[mod].label;
  const act = ok ? `go('${mod}')` : `toast('Vị trí ${S.role} chưa được cấp quyền vào: ${lb}','err')`;
  const hov = ok ? `onmouseover="this.style.borderColor='var(--teal)';this.style.boxShadow='0 2px 12px rgba(0,0,0,.07)'" onmouseout="this.style.borderColor='var(--line)';this.style.boxShadow='none'"` : '';
  return `<div onclick="${act}" ${hov} style="cursor:${ok?'pointer':'not-allowed'};border:1px solid var(--line);border-radius:12px;padding:14px 15px;background:${ok?'#fff':'#f3f6f8'};opacity:${ok?'1':'.65'};display:flex;flex-direction:column;gap:6px;transition:.15s">
    <div style="display:flex;align-items:center;justify-content:space-between;gap:8px">
      <b style="font-size:14px">${lb}</b>
      ${ok?`<span class="badge b-ok">${LVL_LABEL[lv]||lv}</span>`:`<span class="badge b-tc">🔒 Khóa</span>`}
    </div>
    <div style="font-size:12.5px;color:var(--muted);line-height:1.45">${DH_DESC[mod]||''}</div>
    ${ok?'':`<div style="font-size:11.5px;color:var(--red)">Chưa được CEO cấp quyền vị trí</div>`}
  </div>`;
}
function _dhChain(){
  const seg=DH_CHAIN.map(m=>{const ok=canSee(m);
    return `<span style="white-space:nowrap;font-size:12px;font-weight:700;padding:4px 10px;border-radius:20px;background:${ok?'var(--teal)':'#e8eef2'};color:${ok?'#fff':'#9fb0bb'}">${MODULES[m].label}</span>`;});
  return seg.join('<span style="color:var(--muted);margin:0 2px">→</span>');
}
async function viewDieuHanh(m){
  m.innerHTML=head("Overall Operation","Bàn điều hành tổng thể — đi nhanh từ Bán hàng đến Kế toán");
  const isCEO=can("dieu_hanh","QUAN_TRI");
  m.innerHTML+=`<div class="panel"><div class="panel-b">
    <div style="font-size:13px;color:var(--muted);margin-bottom:12px;line-height:1.55">
      Tab này tập hợp lối tắt theo <b>luồng nghiệp vụ</b>. Quyền vào tab do <b>CEO duyệt theo vị trí</b>;
      bên trong, mỗi lối tắt chỉ mở được nếu vị trí của bạn đã được cấp quyền vào module tương ứng (ô khóa = chưa có quyền).
    </div>
    <div style="display:flex;align-items:center;flex-wrap:wrap;gap:4px">${_dhChain()}</div>
  </div></div>`;
  let html="";
  DH_FLOW.forEach(sec=>{
    const tiles=sec.items.map(_dhTile).join('');
    html+=`<div class="panel"><div class="panel-h"><h3>${sec.g}</h3></div>
      <div class="panel-b"><div class="cards" style="margin-bottom:0">${tiles}</div></div></div>`;
  });
  m.innerHTML+=html;
  if(isCEO){
    m.innerHTML+=`<div class="panel" style="border:1px solid var(--teal)">
      <div class="panel-h"><h3>Phân quyền theo vị trí — chỉ CEO duyệt</h3><div class="spacer"></div>
        <span class="badge b-info">CEO</span></div>
      <div class="panel-b" id="dhRoles">Đang tải ma trận phân quyền…</div></div>`;
    _dhLoadMatrix();
  }
}
function _qOpts(cur){return Object.keys(MUC_TEN).map(v=>`<option value="${v}" ${cur===v?'selected':''}>${MUC_TEN[v]}</option>`).join('');}
const _QBG={KHONG:'#f3f6f8',XEM:'#eaf3f8',THAO_TAC:'#e6f5f1',DUYET:'#fdf3e3',QUAN_TRI:'#e9f7ec'};
async function _dhLoadMatrix(){
  if(S.mode==="live"){
    try{ const r=await api("/cau-hinh/ma-tran-quyen"); S.dhVT=r.vai_tro; S.dhMT=r.ma_tran; }
    catch(e){ const el=$("#dhRoles"); if(el)el.innerHTML=`<div class="perm-denied">${e.detail||e.message}</div>`; return; }
  } else {
    S.dhVT=Object.keys(DEMO_PERM).map(r=>({ma:r,ten:ROLE_NAME[r]||r}));
    S.dhMT={}; Object.keys(DEMO_PERM).forEach(r=>{S.dhMT[r]=Object.assign({},DEMO_PERM[r]);});
  }
  _dhDrawMatrix();
}
function _dhDrawMatrix(){
  const el=$("#dhRoles"); if(!el||!S.dhVT)return;
  const ths=DH_MODCOLS.map(mc=>`<th style="font-size:11px;white-space:nowrap;padding:6px 8px">${DH_COLLABEL[mc]||mc}</th>`).join('');
  const rows=S.dhVT.map(v=>{
    const cells=DH_MODCOLS.map(mc=>{
      const cur=(S.dhMT[v.ma]||{})[mc]||"KHONG";
      const lock=(v.ma==="CEO" && mc==="dieu_hanh");
      return `<td style="padding:3px 4px;background:${_QBG[cur]}">
        <select ${lock?'disabled title="CEO luôn Quản trị"':''} onchange="_dhSetQuyen('${v.ma}','${mc}',this.value)"
          style="font-size:11.5px;padding:3px 4px;border:1px solid var(--line);border-radius:6px;background:transparent;max-width:98px">${_qOpts(cur)}</select></td>`;
    }).join('');
    return `<tr><td style="position:sticky;left:0;background:#fff;white-space:nowrap;z-index:1"><b>${v.ma}</b><div style="font-size:11px;color:var(--muted)">${v.ten}</div></td>${cells}</tr>`;
  }).join('');
  el.innerHTML=`
    <div style="display:flex;flex-wrap:wrap;gap:12px;font-size:11.5px;color:var(--muted);margin:0 0 10px;line-height:1.5">
      <span><b>Xem</b>: chỉ đọc</span><span><b>Thao tác</b>: nhập liệu / đề xuất</span>
      <span><b>Duyệt</b>: phê duyệt</span><span><b>Quản trị</b>: toàn quyền</span>
      <span style="color:var(--ink)">Cột <b>Overall Op</b> = quyền vào tab này · <b>Không</b> = không truy cập module.</span></div>
    <div style="overflow:auto;max-height:62vh;border:1px solid var(--line);border-radius:10px">
      <table style="font-size:12px;border-collapse:separate;border-spacing:0">
        <thead><tr><th style="position:sticky;left:0;background:var(--surface);text-align:left;z-index:2">Vị trí</th>${ths}</tr></thead>
        <tbody>${rows}</tbody></table></div>
    <p style="color:var(--muted);font-size:12px;margin:10px 0 0">${S.mode==="live"?"Thay đổi lưu ngay (ghi audit); người bị ảnh hưởng thấy hiệu lực ở lần đăng nhập kế tiếp.":"Chế độ demo: đổi vai trò ở góc trên phải để kiểm thử ngay."}</p>`;
}
async function _dhSetQuyen(vt,mod,muc){
  if(S.mode==="live"){
    try{ await api("/cau-hinh/phan-quyen",{method:'POST',body:JSON.stringify({vai_tro:vt,module:mod,muc})}); }
    catch(e){ toast(e.detail||e.message,"err"); _dhLoadMatrix(); return; }
  }
  S.dhMT[vt]=S.dhMT[vt]||{}; if(muc==="KHONG") delete S.dhMT[vt][mod]; else S.dhMT[vt][mod]=muc;
  if(S.mode!=="live"){
    if(muc==="KHONG"){const p=Object.assign({},DEMO_PERM[vt]);delete p[mod];DEMO_PERM[vt]=p;}
    else DEMO_PERM[vt]=Object.assign({},DEMO_PERM[vt],{[mod]:muc});
    if(vt===S.role){ S.perm=DEMO_PERM[vt]; renderNav(); }
  }
  toast(`Đã đặt ${vt} · ${DH_COLLABEL[mod]||mod} = ${MUC_TEN[muc]}`,"ok");
  _dhDrawMatrix();
}

/* ---------- CRM — Khách hàng: quan hệ & chăm sóc sau bán ---------- */
const CS_LOAI={GOI:"Gọi điện",EMAIL:"Email",KHIEU_NAI:"Khiếu nại",SINH_NHAT:"Dịp đặc biệt"};
const _MU='style="color:var(--muted)"';
async function _crmKhList(){
  if(S.mode==="live"){ try{return await api("/ban-hang/khach-hang");}catch(e){toast(e.detail||e.message,"err");return [];} }
  return DEMO.khach||[];
}
function _crmKhName(id){const k=(DEMO.khach||[]).find(x=>x.id===id);return k?k.ten:("KH #"+id);}
function _demo360(kh){
  const bg=(DEMO.bao_gia||[]).filter(b=>b.khach===kh.ten).length;
  const dh=(DEMO.don_hang||[]).filter(o=>o.khach===kh.ten);
  const ds=dh.reduce((s,o)=>s+(o.tong_tien||0),0);
  return {khach_hang:{id:kh.id,ten:kh.ten,phan_loai_abc:kh.phan_loai_abc},
    so_bao_gia:bg,so_don_hang:dh.length,doanh_so_luy_ke:ds,con_phai_thu:Math.round(ds*0.3),
    cham_soc_gan_day:(DEMO.cham_soc||[]).filter(c=>c.khach_hang_id===kh.id).slice(0,5)};
}

async function viewCRM(m){
  if(!S.crmTab)S.crmTab="tong_quan";
  m.innerHTML=head("Khách hàng (CRM)","Hồ sơ 360° · Phân loại ABC · Chăm sóc sau bán · Khiếu nại (SLA 24h)");
  const tabs=[["tong_quan","Tổng quan"],["khach_hang","Khách hàng 360°"],["cham_soc","Chăm sóc sau bán"],["khieu_nai","Khiếu nại (SLA)"]];
  m.innerHTML+=`<div class="tabs">${tabs.map(([k,l])=>`<button class="${S.crmTab===k?'active':''}" onclick="crmSwitch('${k}')">${l}</button>`).join('')}</div><div id="crmBody">Đang tải…</div>`;
  const host=$("#crmBody");
  if(S.crmTab==="tong_quan") await crmTongQuan(host);
  else if(S.crmTab==="khach_hang") await crmKhachHang(host);
  else if(S.crmTab==="cham_soc") await crmChamSoc(host);
  else if(S.crmTab==="khieu_nai") await crmKhieuNai(host);
}
function crmSwitch(t){S.crmTab=t;S.crmKH=null;viewCRM($("#main"));}

async function crmTongQuan(host){
  let d;
  if(S.mode==="live"){ try{d=await api("/crm/tong-quan");}catch(e){host.innerHTML=`<div class="perm-denied">${e.detail||e.message}</div>`;return;} }
  else {
    const ks=DEMO.khach||[], abc={A:0,B:0,C:0}; let chua=0;
    ks.forEach(k=>{ if(abc[k.phan_loai_abc]!==undefined) abc[k.phan_loai_abc]++; else chua++; });
    const today=new Date().toISOString().slice(0,10);
    const dh=(DEMO.cham_soc||[]).filter(c=>c.trang_thai==="CHO"&&c.ngay_hen&&c.ngay_hen<=today).length;
    const kn=(DEMO.cham_soc||[]).filter(c=>c.loai==="KHIEU_NAI"&&c.trang_thai==="CHO").length;
    const done=(DEMO.cham_soc||[]).filter(c=>c.csat); const cs=done.length?done.reduce((s,c)=>s+c.csat,0)/done.length:null;
    d={so_kh:ks.length,abc,chua_xep:chua,den_han:dh,khieu_nai_qua_han:kn,csat_tb:cs?Math.round(cs*100)/100:null};
  }
  host.innerHTML=`<div class="cards">
    <div class="stat accent"><div class="k">Khách hàng</div><div class="v">${d.so_kh}</div><div class="d">A:${d.abc.A} · B:${d.abc.B} · C:${d.abc.C}${d.chua_xep?` · chưa xếp:${d.chua_xep}`:''}</div></div>
    <div class="stat"><div class="k">Việc chăm sóc đến hạn</div><div class="v small">${d.den_han}</div><div class="d" style="color:var(--amber)">Cần liên hệ hôm nay</div></div>
    <div class="stat"><div class="k">Khiếu nại quá hạn 24h</div><div class="v small">${d.khieu_nai_qua_han}</div><div class="d" style="color:var(--red)">Vi phạm SLA</div></div>
    <div class="stat"><div class="k">CSAT trung bình</div><div class="v small">${d.csat_tb!=null?d.csat_tb+' / 5':'—'}</div><div class="d">Hài lòng sau chăm sóc</div></div>
  </div>
  <div class="panel"><div class="panel-b" style="color:var(--muted);font-size:13px;line-height:1.6">
    CRM tập trung vào <b>quan hệ &amp; sau bán</b>: hồ sơ 360° tổng hợp liên module (báo giá · đơn hàng · công nợ), phân loại ABC theo doanh số,
    lịch chăm sóc +7/+30 ngày sau giao hàng, và khiếu nại theo SLA 24h. Phễu cơ hội &amp; báo giá nằm ở tab <b>Bán hàng</b>.
  </div></div>`;
}

async function crmKhachHang(host){
  if(S.crmKH) return crmKHDetail(host,S.crmKH);
  const list=await _crmKhList(), canDo=can("crm","THAO_TAC");
  const rows=list.map(k=>`<tr>
    <td><b>${k.ma||'—'}</b></td><td>${k.ten}</td>
    <td>${k.email?k.email:'<span style="color:var(--amber)">chưa có email</span>'}</td>
    <td>${k.phan_loai_abc?`<span class="badge b-info">Hạng ${k.phan_loai_abc}</span>`:`<span ${_MU}>chưa xếp</span>`}</td>
    <td><button class="btn-sm ghost" onclick="crmOpen(${k.id})">Hồ sơ 360°</button></td></tr>`).join('');
  host.innerHTML=`<div class="panel">
    <div class="panel-h"><h3>Danh mục khách hàng</h3><div class="spacer"></div>
      ${canDo?`<button class="btn-sm" onclick="crmPhanLoaiABC()">🔄 Phân loại ABC tự động</button>`:''}</div>
    ${canDo?'':`<div class="perm-denied">Vai trò ${S.role} chỉ được xem CRM — không thể phân loại/chăm sóc.</div>`}
    <div class="panel-b"><table><thead><tr><th>Mã</th><th>Tên KH</th><th>Email</th><th>Hạng ABC</th><th></th></tr></thead>
      <tbody>${rows||`<tr><td colspan="5" ${_MU}>Chưa có khách hàng</td></tr>`}</tbody></table></div></div>`;
}
function crmOpen(id){S.crmKH=id;viewCRM($("#main"));}
function crmBack(){S.crmKH=null;viewCRM($("#main"));}

async function crmKHDetail(host,khId){
  let d;
  if(S.mode==="live"){ try{d=await api(`/crm/khach-hang/${khId}`);}catch(e){host.innerHTML=`<div class="perm-denied">${e.detail||e.message}</div>`;return;} }
  else { const k=(DEMO.khach||[]).find(x=>x.id===khId)||{id:khId,ten:_crmKhName(khId)}; d=_demo360(k); }
  const kh=d.khach_hang, canDo=can("crm","THAO_TAC");
  const hist=(d.cham_soc_gan_day||[]).map(c=>`<tr><td>${CS_LOAI[c.loai]||c.loai}</td><td>${c.noi_dung||c.ngay_hen||''}</td>
     <td><span class="badge ${c.trang_thai==='HOAN_THANH'?'b-ok':'b-cho'}">${c.trang_thai==='HOAN_THANH'?'Hoàn thành':'Chờ'}</span></td>
     <td class="num">${c.csat!=null?c.csat+' / 5':'—'}</td></tr>`).join('')||`<tr><td colspan="4" ${_MU}>Chưa có hoạt động chăm sóc</td></tr>`;
  host.innerHTML=`<button class="btn-sm ghost" onclick="crmBack()">← Danh sách</button>
    <div class="cards" style="margin-top:14px">
      <div class="stat accent"><div class="k">${kh.ten}</div><div class="v small">Hạng ${kh.phan_loai_abc||'—'}</div><div class="d">Hồ sơ 360°</div></div>
      <div class="stat"><div class="k">Doanh số luỹ kế</div><div class="v small">${vnd(d.doanh_so_luy_ke||0)}</div><div class="d">Phải thu phát sinh</div></div>
      <div class="stat"><div class="k">Còn phải thu</div><div class="v small">${vnd(d.con_phai_thu||0)}</div><div class="d" style="color:var(--amber)">Công nợ hiện tại</div></div>
      <div class="stat"><div class="k">Báo giá / Đơn hàng</div><div class="v small">${d.so_bao_gia||0} / ${d.so_don_hang||0}</div><div class="d">Lịch sử giao dịch</div></div>
    </div>
    ${canDo?`<div class="panel"><div class="panel-h"><h3>Thao tác nhanh</h3></div><div class="panel-b" style="display:flex;gap:8px;flex-wrap:wrap">
      <button class="btn-sm" onclick="crmQuickCare(${kh.id},'GOI')">+ Việc chăm sóc</button>
      <button class="btn-sm ghost" onclick="crmQuickCare(${kh.id},'KHIEU_NAI')">+ Ghi nhận khiếu nại</button>
    </div></div>`:''}
    <div class="panel"><div class="panel-h"><h3>Hoạt động chăm sóc gần đây</h3></div>
      <div class="panel-b"><table><thead><tr><th>Loại</th><th>Nội dung</th><th>Trạng thái</th><th class="num">CSAT</th></tr></thead>
        <tbody>${hist}</tbody></table></div></div>`;
}
async function crmQuickCare(khId,loai){
  const nd=prompt(loai==="KHIEU_NAI"?"Nội dung khiếu nại:":"Nội dung việc chăm sóc:"); if(nd===null)return;
  _crmCreateCare(khId,loai,nd,null);
}

async function crmChamSoc(host){
  const canDo=can("crm","THAO_TAC");
  let denHan=[];
  if(S.mode==="live"){ try{denHan=await api("/crm/cham-soc/den-han");}catch(e){toast(e.detail||e.message,"err");} }
  else { const today=new Date().toISOString().slice(0,10);
    denHan=(DEMO.cham_soc||[]).filter(c=>c.trang_thai==="CHO"&&c.ngay_hen&&c.ngay_hen<=today); }
  const rows=denHan.map(c=>`<tr><td>${_crmKhName(c.khach_hang_id)}</td><td>${CS_LOAI[c.loai]||c.loai}</td>
    <td>${c.noi_dung||''}</td><td>${c.ngay_hen||''}</td>
    <td>${canDo?`<button class="btn-sm" onclick="crmHoanThanh(${c.id})">Hoàn thành + CSAT</button>`:`<span ${_MU}>—</span>`}</td></tr>`).join('')
    ||`<tr><td colspan="5" ${_MU}>Không có việc đến hạn</td></tr>`;
  const khOpts=(await _crmKhList()).map(k=>`<option value="${k.id}">${k.ten}</option>`).join('');
  let orders=[]; if(S.mode==="live"){ try{orders=await api("/ban-hang/don-hang");}catch{} } else { orders=DEMO.don_hang||[]; }
  const dhOpts=orders.map(o=>`<option value="${o.id}">${o.so||('DH #'+o.id)} — ${o.khach||_crmKhName(o.khach_hang_id)}</option>`).join('');
  host.innerHTML=`
    <div class="panel"><div class="panel-h"><h3>Việc chăm sóc đến hạn</h3></div>
      <div class="panel-b"><table><thead><tr><th>Khách hàng</th><th>Loại</th><th>Nội dung</th><th>Ngày hẹn</th><th></th></tr></thead>
        <tbody>${rows}</tbody></table></div></div>
    ${canDo?`
    <div class="panel"><div class="panel-h"><h3>Tạo việc chăm sóc</h3></div><div class="panel-b">
      <div class="formrow">
        <div class="f"><label>Khách hàng</label><select id="cs_kh">${khOpts}</select></div>
        <div class="f"><label>Loại</label><select id="cs_loai"><option value="GOI">Gọi điện</option><option value="EMAIL">Email</option><option value="SINH_NHAT">Dịp đặc biệt</option></select></div>
        <div class="f"><label>Ngày hẹn</label><input type="date" id="cs_ngay"></div>
        <div class="f" style="flex:2"><label>Nội dung</label><input id="cs_nd" placeholder="VD: Gọi hỏi thăm vận hành, tư vấn bảo trì định kỳ…"></div>
      </div>
      <button class="btn-sm" onclick="crmTaoChamSoc()">+ Tạo việc</button>
    </div></div>
    <div class="panel"><div class="panel-h"><h3>Lên lịch chăm sóc sau bán (+7 / +30 ngày)</h3></div><div class="panel-b">
      <div class="formrow"><div class="f" style="flex:2"><label>Từ đơn hàng đã giao</label><select id="cs_dh">${dhOpts||'<option value="">— chưa có đơn —</option>'}</select></div></div>
      <button class="btn-sm ghost" onclick="crmLenLich()">Tạo 2 lịch tự động</button>
    </div></div>`:`<div class="perm-denied">Vai trò ${S.role} chỉ được xem — không thể tạo việc chăm sóc.</div>`}`;
}

async function crmKhieuNai(host){
  const canDo=can("crm","THAO_TAC");
  let data={so_khieu_nai_qua_han_24h:0,danh_sach:[]};
  if(S.mode==="live"){ try{data=await api("/crm/khieu-nai/qua-han");}catch(e){toast(e.detail||e.message,"err");} }
  else { const ds=(DEMO.cham_soc||[]).filter(c=>c.loai==="KHIEU_NAI"&&c.trang_thai==="CHO");
    data={so_khieu_nai_qua_han_24h:ds.length,danh_sach:ds.map(c=>({id:c.id,khach_hang_id:c.khach_hang_id,noi_dung:c.noi_dung}))}; }
  const rows=data.danh_sach.map(c=>`<tr><td>${_crmKhName(c.khach_hang_id)}</td><td>${c.noi_dung||''}</td>
    <td><span class="badge b-tc">Quá hạn 24h</span></td>
    <td>${canDo?`<button class="btn-sm" onclick="crmHoanThanh(${c.id})">Đã xử lý</button>`:`<span ${_MU}>—</span>`}</td></tr>`).join('')
    ||`<tr><td colspan="4" ${_MU}>Không có khiếu nại quá hạn</td></tr>`;
  const khOpts=(await _crmKhList()).map(k=>`<option value="${k.id}">${k.ten}</option>`).join('');
  host.innerHTML=`
    <div class="cards"><div class="stat"><div class="k">Khiếu nại quá hạn SLA 24h</div>
      <div class="v">${data.so_khieu_nai_qua_han_24h}</div><div class="d" style="color:var(--red)">Cần xử lý ngay</div></div></div>
    <div class="panel"><div class="panel-h"><h3>Danh sách khiếu nại quá hạn</h3></div>
      <div class="panel-b"><table><thead><tr><th>Khách hàng</th><th>Nội dung</th><th>SLA</th><th></th></tr></thead>
        <tbody>${rows}</tbody></table></div></div>
    ${canDo?`<div class="panel"><div class="panel-h"><h3>Ghi nhận khiếu nại mới</h3></div><div class="panel-b">
      <div class="formrow"><div class="f"><label>Khách hàng</label><select id="kn_kh">${khOpts}</select></div>
        <div class="f" style="flex:2"><label>Nội dung khiếu nại</label><input id="kn_nd" placeholder="Mô tả vấn đề khách phản ánh…"></div></div>
      <button class="btn-sm" onclick="crmTaoKhieuNai()">+ Ghi nhận (bắt đầu đếm SLA 24h)</button>
    </div></div>`:''}`;
}

/* --- Hành động CRM --- */
async function crmPhanLoaiABC(){
  if(S.mode!=="live"){toast("Phân loại ABC chạy ở bản kết nối backend","err");return;}
  try{const r=await api("/crm/phan-loai-abc",{method:'POST'});
    toast(`Đã phân loại ${r.da_phan_loai} KH — A:${r.theo_nhom.A} B:${r.theo_nhom.B} C:${r.theo_nhom.C}`,"ok");viewCRM($("#main"));
  }catch(e){toast(e.detail||e.message,"err");}
}
async function _crmCreateCare(khId,loai,nd,ngay){
  if(S.mode!=="live"){
    const id=Math.max(0,...((DEMO.cham_soc||[]).map(c=>c.id)))+1;
    (DEMO.cham_soc=DEMO.cham_soc||[]).push({id,khach_hang_id:Number(khId),loai,noi_dung:nd,
      ngay_hen:ngay||new Date().toISOString().slice(0,10),trang_thai:"CHO",csat:null,created_at:new Date().toISOString().slice(0,10)});
    toast("Đã tạo việc (demo)","ok");viewCRM($("#main"));return;
  }
  try{await api("/crm/cham-soc",{method:'POST',body:JSON.stringify({khach_hang_id:Number(khId),loai,noi_dung:nd,ngay_hen:ngay||null})});
    toast("Đã tạo việc chăm sóc","ok");viewCRM($("#main"));
  }catch(e){toast(e.detail||e.message,"err");}
}
function crmTaoChamSoc(){
  const kh=gv("cs_kh"); if(!kh){toast("Chọn khách hàng","err");return;}
  _crmCreateCare(kh,gv("cs_loai")||"GOI",gv("cs_nd"),gv("cs_ngay")||null);
}
function crmTaoKhieuNai(){
  const kh=gv("kn_kh"), nd=gv("kn_nd");
  if(!kh){toast("Chọn khách hàng","err");return;}
  if(!nd){toast("Nhập nội dung khiếu nại","err");return;}
  _crmCreateCare(kh,"KHIEU_NAI",nd,null);
}
async function crmHoanThanh(csId){
  const v=prompt("Điểm CSAT (1-5), bỏ trống nếu không có:");
  let csat=null;
  if(v!==null&&v.trim()!==""){csat=Number(v.replace(',','.')); if(isNaN(csat)||csat<1||csat>5){toast("CSAT phải từ 1 đến 5","err");return;}}
  if(S.mode!=="live"){
    const c=(DEMO.cham_soc||[]).find(x=>x.id===csId); if(c){c.trang_thai="HOAN_THANH";c.csat=csat;}
    toast("Đã hoàn thành (demo)","ok");viewCRM($("#main"));return;
  }
  try{await api(`/crm/cham-soc/${csId}/hoan-thanh`,{method:'POST',body:JSON.stringify({csat})});
    toast("Đã hoàn thành việc chăm sóc","ok");viewCRM($("#main"));
  }catch(e){toast(e.detail||e.message,"err");}
}
async function crmLenLich(){
  const dh=gv("cs_dh"); if(!dh){toast("Chọn đơn hàng","err");return;}
  if(S.mode!=="live"){toast("Lên lịch sau bán chạy ở bản kết nối backend","err");return;}
  try{const r=await api(`/crm/len-lich-sau-ban/${dh}`,{method:'POST'});
    toast(`Đã tạo ${r.so_lich_tao} lịch chăm sóc (${(r.ngay_hen||[]).join(', ')})`,"ok");viewCRM($("#main"));
  }catch(e){toast(e.detail||e.message,"err");}
}


/* ---------- Cho thuê: tài sản · hợp đồng · chi phí · vật tư · bảo trì · báo cáo ---------- */
const TT_TS={SAN_SANG:["Sẵn sàng","b-ok"],DANG_THUE:["Đang thuê","b-info"],BAO_TRI:["Bảo trì","b-cho"],HONG:["Hỏng","b-tc"],THANH_LY:["Thanh lý","b-tc"]};
const LOAI_TS={THIET_BI:"Thiết bị",HE_THONG:"Hệ thống",XE:"Xe",KHAC:"Khác"};
const LOAI_CP={VAT_TU:"Vật tư",SUA_CHUA:"Sửa chữa",NHAN_CONG:"Nhân công",KHAC:"Khác"};
function _maThang(prefix,thang){return (prefix||'')+(thang||'').slice(5,7)+(thang||'').slice(2,4);}
async function _ctTaiSan(force){
  if(S._ctTS&&!force)return S._ctTS;
  let l; if(S.mode==="live"){try{l=await api("/cho-thue/tai-san");}catch(e){toast(e.detail||e.message,"err");l=[];}} else l=DEMO.tai_san_ct||[];
  S._ctTS=l;return l;
}
async function viewChoThue(m){
  if(!S.ctTab)S.ctTab="bao_cao";
  if(S.ctDuAn===undefined)S.ctDuAn='';
  m.innerHTML=head("Cho thuê","Tài sản · Hợp đồng · Chi phí vận hành · Vật tư-thiết bị · Bảo trì · Báo cáo");
  m.innerHTML+=await _ctDuAnBar();
  const tabs=[["bao_cao","Báo cáo vận hành"],["tai_san","Tài sản"],["hop_dong","Hợp đồng"],["chi_phi","Chi phí vận hành"],["vat_tu","Vật tư & thiết bị"],["dinh_muc","Định mức tiêu hao"],["bao_tri","Bảo trì"],["document","Document"]];
  m.innerHTML+=`<div class="tabs">${tabs.map(([k,l])=>`<button class="${S.ctTab===k?'active':''}" onclick="ctSwitch('${k}')">${l}</button>`).join('')}</div><div id="ctBody">Đang tải…</div>`;
  const h=$("#ctBody");
  if(S.ctTab==="bao_cao")await ctBaoCao(h);
  else if(S.ctTab==="tai_san")await ctTaiSan(h);
  else if(S.ctTab==="hop_dong")await ctHopDong(h);
  else if(S.ctTab==="chi_phi")await ctChiPhi(h);
  else if(S.ctTab==="vat_tu")await ctVatTu(h);
  else if(S.ctTab==="dinh_muc")await ctDinhMuc(h);
  else if(S.ctTab==="bao_tri")await ctBaoTri(h);
  else if(S.ctTab==="document")await ctDocument(h);
}
async function _ctDuAnBar(){
  const list=await _ctTaiSan();
  const opts=`<option value="">— Tất cả dự án —</option>`+list.map(t=>`<option value="${t.id}" ${String(t.id)===String(S.ctDuAn)?'selected':''}>${t.ten_du_an||t.ma} — ${t.ten}</option>`).join('');
  const cur=list.find(t=>String(t.id)===String(S.ctDuAn));
  return `<div class="formrow" style="margin:2px 0 10px;align-items:flex-end">
    <div class="f" style="flex:2;max-width:460px"><label>Dự án — mốc phân bổ dữ liệu</label><select onchange="ctSetDuAn(this.value)">${opts}</select></div>
    ${cur?`<div class="f" style="max-width:none"><span class="badge ${(TT_TS[cur.tinh_trang]||['','b-info'])[1]}">${(TT_TS[cur.tinh_trang]||[cur.tinh_trang])[0]}</span> <span style="color:var(--muted);font-size:12px">Giá thuê ${vnd(cur.gia_thue_thang||0)}/tháng · Khách: ${cur.khach_hang||'—'}</span></div>`:'<div class="f" style="max-width:none"><span style="color:var(--muted);font-size:12px">Đang xem toàn bộ dự án</span></div>'}
  </div>`;
}
function ctSetDuAn(v){S.ctDuAn=v||'';if(v)S.ctDmTS=Number(v);S.ctSel=null;viewChoThue($('#main'));}
function ctSwitch(t){S.ctTab=t;S.ctSel=null;S.ctEdit=null;viewChoThue($("#main"));}

/* --- Báo cáo vận hành --- */
async function ctBaoCao(host){
  // Pivot theo dự án (nguồn dữ liệu chung cho cả 2 chế độ)
  let pivot;
  if(S.mode==="live"){ try{pivot=await api("/cho-thue/bao-cao-theo-du-an");}catch(e){host.innerHTML=`<div class="perm-denied">${e.detail||e.message}</div>`;return;} }
  else { const ts=DEMO.tai_san_ct||[]; const du_an=ts.map(t=>{const pre=t.ten_du_an||t.ma;const cp=(DEMO.chi_phi_vh||[]).filter(c=>c.ma_ban_hang&&String(c.ma_ban_hang).indexOf(pre)===0).reduce((s,c)=>s+c.so_tien,0);const bt=(DEMO.bao_tri_ct||[]).filter(b=>b.ma===t.ma&&b.qua_han).length;return {tai_san_id:t.id,ten_du_an:pre,ten:t.ten,tinh_trang:t.tinh_trang,khach_hang:t.khach_hang,nguyen_gia:t.nguyen_gia,gia_thue_thang:t.gia_thue_thang,doanh_thu_thang:t.tinh_trang==="DANG_THUE"?t.gia_thue_thang:0,chi_phi_luy_ke:cp,bao_tri_den_han:bt};});
    pivot={du_an,tong:{so:du_an.length,doanh_thu_thang:du_an.reduce((s,o)=>s+o.doanh_thu_thang,0),chi_phi_luy_ke:du_an.reduce((s,o)=>s+o.chi_phi_luy_ke,0)}}; }

  if(S.ctDuAn){ return ctBaoCaoDuAn(host,pivot); }

  // ===== Toàn bộ dự án =====
  const rows=pivot.du_an;
  const tt={}; rows.forEach(r=>tt[r.tinh_trang]=(tt[r.tinh_trang]||0)+1);
  const so=rows.length, dangThue=tt.DANG_THUE||0;
  const dtThang=pivot.tong.doanh_thu_thang, cpTong=pivot.tong.chi_phi_luy_ke;
  const nguyenGia=rows.reduce((s,r)=>s+Number(r.nguyen_gia||0),0);
  const btDenHan=rows.reduce((s,r)=>s+Number(r.bao_tri_den_han||0),0);
  const tyLe=so?Math.round(dangThue/so*1000)/10:0;
  const ttStrip=Object.entries(tt).map(([k,v])=>{const m=TT_TS[k]||[k,'b-info'];return `<span class="badge ${m[1]}" style="padding:5px 12px;font-size:12px">${m[0]}: <b>${v}</b></span>`;}).join('')||'<span style="color:var(--muted)">Chưa có tài sản</span>';
  const pivRows=rows.map(r=>{const m=TT_TS[r.tinh_trang]||[r.tinh_trang,'b-info'];return `<tr style="cursor:pointer" onclick="ctSetDuAn('${r.tai_san_id}')"><td><b>${r.ten_du_an}</b></td><td>${r.ten}</td><td><span class="badge ${m[1]}">${m[0]}</span></td><td>${r.khach_hang||'<span style="color:var(--muted)">—</span>'}</td><td class="num">${vnd(r.doanh_thu_thang||0)}</td><td class="num" style="color:#dc2626">${vnd(r.chi_phi_luy_ke||0)}</td><td class="num">${r.bao_tri_den_han||0}</td></tr>`;}).join('')||`<tr><td colspan="7" style="color:var(--muted)">Chưa có dự án</td></tr>`;
  host.innerHTML=`<div class="cards">
    <div class="stat accent"><div class="k">Dự án cho thuê</div><div class="v">${so}</div><div class="d">Đang theo dõi</div></div>
    <div class="stat"><div class="k">Tỷ lệ sử dụng</div><div class="v small">${tyLe}%</div><div class="d">Đang thuê / tổng</div></div>
    <div class="stat"><div class="k">Doanh thu thuê / tháng</div><div class="v small">${vnd(dtThang)}</div><div class="d">Dự án đang thuê</div></div>
    <div class="stat"><div class="k">Chi phí vận hành</div><div class="v small" style="color:#dc2626">${vnd(cpTong)}</div><div class="d">Luỹ kế</div></div>
    <div class="stat"><div class="k">Nguyên giá đội tài sản</div><div class="v small">${vnd(nguyenGia)}</div><div class="d">Tổng</div></div>
    <div class="stat"><div class="k">Bảo trì đến hạn</div><div class="v small">${btDenHan}</div><div class="d" style="color:var(--amber)">≤ 7 ngày / quá hạn</div></div>
  </div>
  <div class="panel"><div class="panel-h"><h3>Phân bố theo tình trạng</h3></div>
    <div class="panel-b"><div style="display:flex;flex-wrap:wrap;gap:10px;align-items:center">${ttStrip}</div></div></div>
  <div class="panel"><div class="panel-h"><h3>Phân bổ dữ liệu theo dự án</h3><div class="spacer"></div><span style="color:var(--muted);font-size:12px">Bấm một dòng để xem chi tiết dự án</span></div>
    <div class="panel-b"><table><thead><tr><th>Tên Dự Án</th><th>Mô tả</th><th>Tình trạng</th><th>Khách thuê</th><th class="num">DT thuê/tháng</th><th class="num">Chi phí luỹ kế</th><th class="num">Bảo trì đến hạn</th></tr></thead>
      <tbody>${pivRows}</tbody></table></div></div>`;
}
async function ctBaoCaoDuAn(host,pivot){
  const r=(pivot.du_an||[]).find(x=>String(x.tai_san_id)===String(S.ctDuAn));
  if(!r){host.innerHTML='<div style="padding:20px;color:var(--muted)">Không tìm thấy dự án.</div>';return;}
  // P&L theo tháng
  let mt;
  if(S.mode==="live"){try{mt=await api(`/cho-thue/du-an/${S.ctDuAn}/cac-thang?so_thang=6`);}catch(e){mt={cac_thang:[]};}}
  else{const dt=Number(r.gia_thue_thang||0);const now=new Date();const cur=now.toISOString().slice(0,7);const ms=[];for(let i=5;i>=0;i--){const dd=new Date(now.getFullYear(),now.getMonth()-i,1);ms.push(dd.getFullYear()+'-'+String(dd.getMonth()+1).padStart(2,'0'));}mt={cac_thang:ms.map(m=>{const cp=m===cur?r.chi_phi_luy_ke:0;return {thang:m,ma_ban_hang:_maThang(r.ten_du_an,m),doanh_thu:dt,chi_phi:cp,loi_nhuan:dt-cp};})};}
  const m=TT_TS[r.tinh_trang]||[r.tinh_trang,'b-info'];
  const mtRows=(mt.cac_thang||[]).map(x=>`<tr><td><b>${x.ma_ban_hang}</b></td><td>${x.thang}</td><td class="num">${vnd(x.doanh_thu)}</td><td class="num" style="color:#dc2626">${vnd(x.chi_phi)}</td><td class="num" style="color:${x.loi_nhuan>=0?'#16a34a':'#dc2626'}">${vnd(x.loi_nhuan)}</td></tr>`).join('')||`<tr><td colspan="5" style="color:var(--muted)">Chưa có dữ liệu</td></tr>`;
  host.innerHTML=`<div class="cards">
      <div class="stat accent"><div class="k">${r.ten_du_an} · ${r.ten}</div><div class="v small"><span class="badge ${m[1]}">${m[0]}</span></div><div class="d">Khách: ${r.khach_hang||'—'}</div></div>
      <div class="stat"><div class="k">Doanh thu thuê / tháng</div><div class="v small">${vnd(r.doanh_thu_thang||0)}</div><div class="d">Khi đang thuê</div></div>
      <div class="stat"><div class="k">Chi phí vận hành</div><div class="v small" style="color:#dc2626">${vnd(r.chi_phi_luy_ke||0)}</div><div class="d">Luỹ kế</div></div>
      <div class="stat"><div class="k">Nguyên giá</div><div class="v small">${vnd(r.nguyen_gia||0)}</div><div class="d">Bảo trì đến hạn: ${r.bao_tri_den_han||0}</div></div>
    </div>
    <div class="panel"><div class="panel-h"><h3>Mã bán hàng theo tháng — ${r.ten_du_an}</h3></div>
      <div class="panel-b"><table><thead><tr><th>Mã bán hàng</th><th>Tháng</th><th class="num">Doanh thu</th><th class="num">Chi phí</th><th class="num">Lợi nhuận</th></tr></thead><tbody>${mtRows}</tbody></table>
      <div style="color:var(--muted);font-size:12px;margin-top:6px">Mỗi tháng một mã = Tên dự án + MMYY. Chi phí = chi phí vận hành phát sinh trong tháng.</div></div></div>`;
}


/* --- Tài sản --- */
async function ctTaiSan(host){
  if(S.ctSel)return ctTaiSanDetail(host,S.ctSel);
  let list=await _ctTaiSan(true); const canOp=can("cho_thue","THAO_TAC"); if(S.ctDuAn)list=list.filter(t=>String(t.id)===String(S.ctDuAn));
  const rows=list.map(t=>{const tt=TT_TS[t.tinh_trang]||[t.tinh_trang,'b-info'];
    return `<tr><td><b>${t.ten_du_an||t.ma}</b></td><td>${t.ten}</td><td>${LOAI_TS[t.loai]||t.loai}</td>
      <td class="num">${vnd(t.gia_thue_thang||0)}</td>
      <td><span class="badge ${tt[1]}">${tt[0]}</span></td>
      <td>${t.khach_hang||'<span style="color:var(--muted)">—</span>'}</td>
      <td><button class="btn-sm ghost" onclick="ctOpenTS(${t.id})">Chi tiết</button>${canOp?` <button class="btn-sm ghost" onclick="ctEditTS(${t.id})">Sửa</button>`:''}</td></tr>`;}).join('');
  host.innerHTML=`<div class="panel">
    <div class="panel-h"><h3>Danh mục tài sản cho thuê</h3><div class="spacer"></div>
      ${canOp?`<button class="btn-sm" onclick="ctFormTS()">+ Thêm tài sản</button>`:''}</div>
    ${canOp?ctFormTSHtml():`<div class="perm-denied">Vai trò ${S.role} chỉ được xem.</div>`}
    <div class="panel-b"><table><thead><tr><th>Tên Dự Án</th><th>Mô tả</th><th>Loại</th><th class="num">Giá thuê/tháng</th><th>Tình trạng</th><th>Khách thuê</th><th></th></tr></thead>
      <tbody>${rows||`<tr><td colspan="7" style="color:var(--muted)">Chưa có tài sản</td></tr>`}</tbody></table></div></div>`;
  if(S.ctEdit)ctFillTS(S.ctEdit);
}
function ctFormTSHtml(){return `<div id="ctFormTS" class="formrow hidden">
  <div class="f"><label>Tên dự án</label><input id="ts_ma" placeholder="VD: RO-STH (mã bán hàng tháng = Tên dự án + MMYY)"></div>
  <div class="f" style="flex:2"><label>Tên tài sản</label><input id="ts_ten"></div>
  <div class="f"><label>Loại</label><select id="ts_loai"><option value="THIET_BI">Thiết bị</option><option value="HE_THONG">Hệ thống</option><option value="XE">Xe</option><option value="KHAC">Khác</option></select></div>
  <div class="f"><label>Nguyên giá</label><input id="ts_ng" type="number" value="0"></div>
  <div class="f"><label>Giá thuê/tháng</label><input id="ts_gt" type="number" value="0"></div>
  <div class="f"><label>Khấu hao/tháng</label><input id="ts_kh" type="number" value="0"></div>
  <div class="f" id="ts_tt_wrap" style="display:none"><label>Tình trạng</label><select id="ts_tt"><option value="SAN_SANG">Sẵn sàng</option><option value="DANG_THUE">Đang thuê</option><option value="BAO_TRI">Bảo trì</option><option value="HONG">Hỏng</option><option value="THANH_LY">Thanh lý</option></select></div>
  <div class="f"><label>Vị trí</label><input id="ts_vt"></div>
  <button class="btn-sm" id="ts_save" onclick="ctSaveTS()">Lưu</button>
  <button class="btn-sm ghost" onclick="ctCancelTS()">Hủy</button></div>`;}
function ctFormTS(){S.ctEdit=null;const f=$("#ctFormTS");f.classList.toggle('hidden');
  if(!f.classList.contains('hidden')){["ts_ten","ts_vt"].forEach(i=>{const e=document.getElementById(i);if(e)e.value='';});
    ["ts_ng","ts_gt","ts_kh"].forEach(i=>{const e=document.getElementById(i);if(e)e.value='0';});
    const ma=document.getElementById('ts_ma');if(ma){ma.value='';ma.disabled=false;}
    document.getElementById('ts_tt_wrap').style.display='none';$("#ts_save").textContent="Lưu";}}
function ctCancelTS(){S.ctEdit=null;$("#ctFormTS").classList.add('hidden');}
function ctEditTS(id){S.ctEdit=id;const f=$("#ctFormTS");if(f)f.classList.remove('hidden');ctFillTS(id);}
function ctFillTS(id){const t=(S._ctTS||[]).find(x=>x.id===id);if(!t)return;const set=(i,v)=>{const e=document.getElementById(i);if(e)e.value=v;};
  set("ts_ma",t.ma);set("ts_ten",t.ten);set("ts_ng",t.nguyen_gia||0);set("ts_gt",t.gia_thue_thang||0);set("ts_kh",t.khau_hao_thang||0);set("ts_vt",t.vi_tri||"");
  const sl=document.getElementById('ts_loai');if(sl)sl.value=t.loai||"THIET_BI";
  document.getElementById('ts_tt_wrap').style.display='';const st=document.getElementById('ts_tt');if(st)st.value=t.tinh_trang||"SAN_SANG";
  const ma=document.getElementById('ts_ma');if(ma)ma.disabled=true;$("#ts_save").textContent="Cập nhật";}
async function ctSaveTS(){
  const ten=gv("ts_ten");if(!ten){toast("Nhập tên tài sản","err");return;}
  const body={ten,loai:gv("ts_loai"),nguyen_gia:Number(gv("ts_ng")||0),gia_thue_thang:Number(gv("ts_gt")||0),khau_hao_thang:Number(gv("ts_kh")||0),vi_tri:gv("ts_vt")||null};
  if(S.ctEdit){
    body.tinh_trang=gv("ts_tt");
    if(S.mode==="live"){try{await api(`/cho-thue/tai-san/${S.ctEdit}`,{method:'PUT',body:JSON.stringify(body)});}catch(e){toast(e.detail||e.message,"err");return;}}
    else{const t=(DEMO.tai_san_ct||[]).find(x=>x.id===S.ctEdit);if(t)Object.assign(t,body);}
    toast("Đã cập nhật tài sản","ok");
  }else{
    body.ma=gv("ts_ma");if(!body.ma){toast("Nhập tên dự án","err");return;}
    body.ten_du_an=body.ma;
    if(S.mode==="live"){try{await api("/cho-thue/tai-san",{method:'POST',body:JSON.stringify(body)});}catch(e){toast(e.detail||e.message,"err");return;}}
    else{(DEMO.tai_san_ct=DEMO.tai_san_ct||[]).push(Object.assign({id:Date.now(),tinh_trang:"SAN_SANG",khach_hang:null},body));}
    toast("Đã thêm tài sản","ok");
  }
  S.ctEdit=null;S._ctTS=null;viewChoThue($("#main"));
}
function ctOpenTS(id){S.ctSel=id;viewChoThue($("#main"));}
function ctBackTS(){S.ctSel=null;viewChoThue($("#main"));}
async function ctTaiSanDetail(host,id){
  let d;
  if(S.mode==="live"){try{d=await api(`/cho-thue/tai-san/${id}`);}catch(e){host.innerHTML=`<div class="perm-denied">${e.detail||e.message}</div>`;return;}}
  else{const t=(DEMO.tai_san_ct||[]).find(x=>x.id===id)||{};
    const cp=(DEMO.chi_phi_vh||[]).filter(c=>c.ma_ban_hang===t.ma);const bt=(DEMO.bao_tri_ct||[]).filter(b=>b.ma===t.ma);
    d={tai_san:t,tong_chi_phi:cp.reduce((s,c)=>s+c.so_tien,0),chi_phi:cp,bao_tri:bt};}
  let mt;
  if(S.mode==="live"){try{mt=await api(`/cho-thue/du-an/${id}/cac-thang?so_thang=6`);}catch(e){mt={cac_thang:[]};}}
  else{const pre=(d.tai_san.ten_du_an||d.tai_san.ma);const dt=Number(d.tai_san.gia_thue_thang||0);const now=new Date();const cur=now.toISOString().slice(0,7);const cpCur=(d.chi_phi||[]).reduce((s,c)=>s+c.so_tien,0);const ms=[];for(let i=5;i>=0;i--){const dd=new Date(now.getFullYear(),now.getMonth()-i,1);ms.push(dd.getFullYear()+'-'+String(dd.getMonth()+1).padStart(2,'0'));}mt={cac_thang:ms.map(m=>{const cp=m===cur?cpCur:0;return {thang:m,ma_ban_hang:_maThang(pre,m),doanh_thu:dt,chi_phi:cp,loi_nhuan:dt-cp};})};}
  const t=d.tai_san,tt=TT_TS[t.tinh_trang]||[t.tinh_trang,'b-info'];
  const cpRows=(d.chi_phi||[]).map(c=>`<tr><td>${c.ngay}</td><td>${LOAI_CP[c.loai_chi_phi]||c.loai_chi_phi}</td><td class="num">${vnd(c.so_tien)}</td><td>${c.mo_ta||''}</td></tr>`).join('')||`<tr><td colspan="4" style="color:var(--muted)">Chưa có chi phí</td></tr>`;
  const btRows=(d.bao_tri||[]).map(b=>`<tr><td>${b.ten_cong_viec}</td><td>${b.chu_ky_ngay} ngày</td><td>${b.ngay_ke_tiep||'—'}</td></tr>`).join('')||`<tr><td colspan="3" style="color:var(--muted)">Chưa có kế hoạch</td></tr>`;
  const mtRows=(mt.cac_thang||[]).map(x=>`<tr><td><b>${x.ma_ban_hang}</b></td><td>${x.thang}</td><td class="num">${vnd(x.doanh_thu)}</td><td class="num" style="color:#dc2626">${vnd(x.chi_phi)}</td><td class="num" style="color:${x.loi_nhuan>=0?'#16a34a':'#dc2626'}">${vnd(x.loi_nhuan)}</td></tr>`).join('')||`<tr><td colspan="5" style="color:var(--muted)">Chưa có dữ liệu</td></tr>`;
  host.innerHTML=`<button class="btn-sm ghost" onclick="ctBackTS()">← Danh sách</button>
    <div class="cards" style="margin-top:14px">
      <div class="stat accent"><div class="k">${t.ten_du_an||t.ma} · ${t.ten}</div><div class="v small"><span class="badge ${tt[1]}">${tt[0]}</span></div><div class="d">${LOAI_TS[t.loai]||t.loai} · ${t.vi_tri||'—'}</div></div>
      <div class="stat"><div class="k">Giá thuê/tháng</div><div class="v small">${vnd(t.gia_thue_thang||0)}</div><div class="d">Khách: ${t.khach_hang||'—'}</div></div>
      <div class="stat"><div class="k">Nguyên giá</div><div class="v small">${vnd(t.nguyen_gia||0)}</div><div class="d">KH/tháng ${vnd(t.khau_hao_thang||0)}</div></div>
      <div class="stat"><div class="k">Chi phí vận hành</div><div class="v small" style="color:#dc2626">${vnd(d.tong_chi_phi||0)}</div><div class="d">Luỹ kế</div></div>
    </div>
    <div class="panel"><div class="panel-h"><h3>Chi phí vận hành</h3></div><div class="panel-b"><table><thead><tr><th>Ngày</th><th>Loại</th><th class="num">Số tiền</th><th>Mô tả</th></tr></thead><tbody>${cpRows}</tbody></table></div></div>
    <div class="panel"><div class="panel-h"><h3>Kế hoạch bảo trì</h3></div><div class="panel-b"><table><thead><tr><th>Công việc</th><th>Chu kỳ</th><th>Kế tiếp</th></tr></thead><tbody>${btRows}</tbody></table></div></div>
    <div class="panel"><div class="panel-h"><h3>Mã bán hàng theo tháng (kiểm soát chi phí–doanh thu)</h3></div>
      <div class="panel-b"><table><thead><tr><th>Mã bán hàng</th><th>Tháng</th><th class="num">Doanh thu</th><th class="num">Chi phí</th><th class="num">Lợi nhuận</th></tr></thead><tbody>${mtRows}</tbody></table>
      <div style="color:var(--muted);font-size:12px;margin-top:6px">Mỗi tháng một mã = <b>Tên dự án + MMYY</b>. Doanh thu = giá thuê/tháng; chi phí = chi phí vận hành phát sinh trong tháng đó.</div></div></div>
    <div id="ctDocHost"></div>`;
  await ctDocument(document.getElementById('ctDocHost'), id);
}

/* --- Hợp đồng --- */
async function ctHopDong(host){
  const canOp=can("cho_thue","THAO_TAC");
  let hds,shh={danh_sach:[]};
  if(S.mode==="live"){ try{hds=await api("/cho-thue/hop-dong");shh=await api("/cho-thue/sap-het-han");}catch(e){host.innerHTML=`<div class="perm-denied">${e.detail||e.message}</div>`;return;} }
  else { hds=DEMO.hd_thue||[]; shh={danh_sach:hds.filter(h=>h.trang_thai==="HIEU_LUC").map(h=>({hop_dong_id:h.id,so:h.so,ngay_ket_thuc:h.ngay_ket_thuc,con_ngay:120}))}; }
  if(S.ctDuAn){const _c=(S._ctTS||[]).find(t=>String(t.id)===String(S.ctDuAn));const kid=_c?_c.khach_hang_id:null;hds=hds.filter(h=>kid&&String(h.khach_hang_id)===String(kid));}
  const rows=hds.map(h=>`<tr><td><b>${h.so||('#'+h.id)}</b></td><td>${_crmKhName(h.khach_hang_id)}</td>
    <td>${h.doi_tuong}</td><td class="num">${vnd(h.gia_thue)}</td><td>${h.ngay_ket_thuc||''}</td>
    <td><span class="badge ${h.trang_thai==='HIEU_LUC'?'b-ok':'b-tc'}">${h.trang_thai==='HIEU_LUC'?'Hiệu lực':'Kết thúc'}</span></td>
    <td>${canOp&&h.trang_thai==='HIEU_LUC'?`<button class="btn-sm" onclick="ctThuPhi(${h.id})">Thu phí kỳ</button> <button class="btn-sm ghost" onclick="ctNhanTra(${h.id})">Nhận trả</button>`:'—'}</td></tr>`).join('')
    ||`<tr><td colspan="7" style="color:var(--muted)">Chưa có hợp đồng</td></tr>`;
  const sh=(shh.danh_sach||[]).map(s=>`<tr><td><b>${s.so}</b></td><td>${s.ngay_ket_thuc}</td><td class="num">${s.con_ngay} ngày</td></tr>`).join('')||`<tr><td colspan="3" style="color:var(--muted)">Không có HĐ sắp hết hạn</td></tr>`;
  host.innerHTML=`
    <div class="panel"><div class="panel-h"><h3>Hợp đồng cho thuê</h3>${S.ctDuAn?' <span style="color:var(--muted);font-size:12px;margin-left:8px">(lọc theo khách của dự án)</span>':''}<div class="spacer"></div>
      ${canOp?`<button class="btn-sm ghost" onclick="ctChayThuPhi()">Chạy thu phí định kỳ</button>`:''}</div>
      <div class="panel-b"><table><thead><tr><th>Số HĐ</th><th>Khách hàng</th><th>Đối tượng</th><th class="num">Giá thuê</th><th>Hết hạn</th><th>Trạng thái</th><th></th></tr></thead>
        <tbody>${rows}</tbody></table></div></div>
    <div class="panel"><div class="panel-h"><h3>Sắp hết hạn (≤ 30 ngày)</h3></div>
      <div class="panel-b"><table><thead><tr><th>Số HĐ</th><th>Ngày hết hạn</th><th class="num">Còn lại</th></tr></thead><tbody>${sh}</tbody></table></div></div>`;
}
async function ctThuPhi(id){
  if(S.mode!=="live"){toast("Thu phí chạy ở bản kết nối backend","err");return;}
  try{const r=await api(`/cho-thue/hop-dong/${id}/thu-phi`,{method:'POST'});toast(`Đã lập hóa đơn thuê ${vnd(r.tong_tien)} (hạn ${r.han_thu})`,"ok");}
  catch(e){toast(e.detail||e.message,"err");}
}
async function ctNhanTra(id){
  if(S.mode!=="live"){toast("Nhận trả chạy ở bản kết nối backend","err");return;}
  try{const r=await api(`/cho-thue/hop-dong/${id}/nhan-tra`,{method:'POST'});toast(`Đã nhận trả ${r.tai_san_nhap_lai} tài sản, HĐ kết thúc`,"ok");viewChoThue($("#main"));}
  catch(e){toast(e.detail||e.message,"err");}
}
async function ctChayThuPhi(){
  if(S.mode!=="live"){toast("Chạy ở bản kết nối backend","err");return;}
  try{const r=await api("/cho-thue/chay-thu-phi-dinh-ky",{method:'POST'});toast(`Đã thu phí ${r.so_hop_dong_thu_phi} hợp đồng`,"ok");}
  catch(e){toast(e.detail||e.message,"err");}
}

/* --- Chi phí vận hành --- */
async function ctChiPhi(host){
  const canOp=can("cho_thue","THAO_TAC");
  let data={tong:0,danh_sach:[]};
  if(S.mode==="live"){ try{data=await api("/cho-thue/chi-phi"+(S.ctDuAn?`?tai_san_id=${S.ctDuAn}`:""));}catch(e){host.innerHTML=`<div class="perm-denied">${e.detail||e.message}</div>`;return;} }
  else { const _c=(S._ctTS||[]).find(t=>String(t.id)===String(S.ctDuAn)); const pre=_c?(_c.ten_du_an||_c.ma):null; let ds=DEMO.chi_phi_vh||[]; if(pre)ds=ds.filter(c=>String(c.ma_ban_hang||"").indexOf(pre)===0); data={tong:ds.reduce((s,c)=>s+c.so_tien,0),danh_sach:ds}; }
  const rows=data.danh_sach.map(c=>`<tr><td>${c.ngay}</td><td>${c.tai_san||c.ma_ban_hang||'—'}</td>
    <td>${LOAI_CP[c.loai_chi_phi]||c.loai_chi_phi}</td><td class="num">${vnd(c.so_tien)}</td>
    <td>${c.mo_ta||''}</td><td><span class="badge ${c.nguon==='DE_XUAT_MUA'?'b-info':c.nguon==='BAO_TRI'?'b-cho':'b-ok'}">${c.nguon==='DE_XUAT_MUA'?'Đề xuất mua':c.nguon==='BAO_TRI'?'Bảo trì':'Thủ công'}</span></td></tr>`).join('')
    ||`<tr><td colspan="6" style="color:var(--muted)">Chưa có chi phí</td></tr>`;
  const tsOpts=(await _ctTaiSan()).map(t=>`<option value="${t.id}" ${String(t.id)===String(S.ctDuAn)?'selected':''}>${t.ten_du_an||t.ma} — ${t.ten}</option>`).join('');
  host.innerHTML=`
    <div class="cards"><div class="stat accent"><div class="k">Tổng chi phí vận hành</div><div class="v small">${vnd(data.tong||0)}</div><div class="d">Thủ công + đề xuất mua + bảo trì</div></div></div>
    <div class="panel"><div class="panel-h"><h3>Chi phí vận hành</h3><div class="spacer"></div>
      ${canOp?`<button class="btn-sm ghost" onclick="ctDongBo()">⟳ Đồng bộ từ đề xuất mua</button>`:''}</div>
      <div class="panel-b"><table><thead><tr><th>Ngày</th><th>Tài sản</th><th>Loại</th><th class="num">Số tiền</th><th>Mô tả</th><th>Nguồn</th></tr></thead>
        <tbody>${rows}</tbody></table></div></div>
    ${canOp?`<div class="panel"><div class="panel-h"><h3>Ghi chi phí thủ công</h3></div><div class="panel-b">
      <div class="formrow">
        <div class="f" style="flex:2"><label>Dự án</label><select id="cp_ts">${tsOpts}</select></div>
        <div class="f"><label>Tháng</label><input id="cp_thang" type="month" value="${new Date().toISOString().slice(0,7)}"></div>
        <div class="f"><label>Loại</label><select id="cp_loai"><option value="VAT_TU">Vật tư</option><option value="SUA_CHUA">Sửa chữa</option><option value="NHAN_CONG">Nhân công</option><option value="KHAC">Khác</option></select></div>
        <div class="f"><label>Số tiền</label><input id="cp_st" type="number"></div>
        <div class="f" style="flex:2"><label>Mô tả</label><input id="cp_mt" placeholder="Nội dung chi phí…"></div>
      </div><button class="btn-sm" onclick="ctThemChiPhi()">+ Ghi chi phí</button></div></div>`:''}`;
}
async function ctDongBo(){
  if(S.mode!=="live"){toast("Đồng bộ chạy ở bản kết nối backend","err");return;}
  try{const r=await api("/cho-thue/dong-bo-chi-phi",{method:'POST'});toast(`Đã thêm ${r.so_chi_phi_them} chi phí từ đề xuất mua (${vnd(r.tong_tien)})`,"ok");viewChoThue($("#main"));}
  catch(e){toast(e.detail||e.message,"err");}
}
async function ctThemChiPhi(){
  const ts=Number(gv("cp_ts")),st=Number(gv("cp_st")||0),thang=gv("cp_thang")||new Date().toISOString().slice(0,7);
  if(!st){toast("Nhập số tiền","err");return;}
  const t=(S._ctTS||[]).find(x=>x.id===ts)||{};const pre=t.ten_du_an||t.ma||'';const ma=_maThang(pre,thang);const ngay=thang+"-01";
  if(S.mode!=="live"){(DEMO.chi_phi_vh=DEMO.chi_phi_vh||[]).unshift({id:Date.now(),tai_san:t.ten,ma_ban_hang:ma,loai_chi_phi:gv("cp_loai"),so_tien:st,ngay,mo_ta:gv("cp_mt"),nguon:"THU_CONG"});toast("Đã ghi chi phí "+ma+" (demo)","ok");viewChoThue($("#main"));return;}
  try{await api("/cho-thue/chi-phi",{method:'POST',body:JSON.stringify({tai_san_id:ts,ma_ban_hang:ma,loai_chi_phi:gv("cp_loai"),so_tien:st,ngay,mo_ta:gv("cp_mt")||null})});toast("Đã ghi chi phí "+ma,"ok");viewChoThue($("#main"));}
  catch(e){toast(e.detail||e.message,"err");}
}

/* --- Vật tư & thiết bị + Hóa chất (đề xuất mua gắn mã cho thuê) --- */
async function ctVatTu(host){
  if(!S.ctVtLoai)S.ctVtLoai="vat_tu";
  const isHC=S.ctVtLoai==="hoa_chat", canOp=can("cho_thue","THAO_TAC");
  let list;
  if(S.mode==="live"){ try{list=await api("/cho-thue/de-xuat-mua");}catch(e){host.innerHTML=`<div class="perm-denied">${e.detail||e.message}</div>`;return;} }
  else list=DEMO.dx_thue||[];
  if(S.ctDuAn){const _c=(S._ctTS||[]).find(t=>String(t.id)===String(S.ctDuAn));const pre=_c?(_c.ten_du_an||_c.ma):null;if(pre)list=list.filter(x=>String(x.cho_thue_ma||"").indexOf(pre)===0);}
  const flt=list.filter(x=> isHC ? x.loai==="HOA_CHAT" : x.loai!=="HOA_CHAT");
  const hangHoa=await _khoHangHoa(true);
  const cat=isHC?["HOA_CHAT"]:["VAT_TU","THIET_BI","SAN_PHAM"];
  const hhCat=hangHoa.filter(h=>cat.includes(h.loai));
  const tsOpts=(await _ctTaiSan()).map(t=>`<option value="${t.id}" ${String(t.id)===String(S.ctDuAn)?'selected':''}>${t.ten_du_an||t.ma} — ${t.ten}</option>`).join('');
  const hhOpts=hhCat.map(h=>`<option value="${h.id}">${h.ma?h.ma+' — ':''}${h.ten}</option>`).join('')
    ||`<option value="">(chưa có ${isHC?'hóa chất':'vật tư/thiết bị'} trong kho)</option>`;
  const toggle=`<div class="tabs" style="margin-bottom:12px">
    <button class="${!isHC?'active':''}" onclick="ctVtSwitch('vat_tu')">Vật tư &amp; Thiết bị</button>
    <button class="${isHC?'active':''}" onclick="ctVtSwitch('hoa_chat')">Hóa chất</button></div>`;

  // Tồn kho hóa chất (chỉ nhóm Hóa chất)
  let tonKhoPanel='';
  if(isHC){
    const cr=hhCat.map(h=>{const ton=Number(h.so_luong||0),min=Number(h.ton_min||0),low=ton<min;
      return `<tr><td><b>${h.ma||''}</b></td><td>${h.ten}</td><td>${h.don_vi||''}</td>
        <td class="num">${ton.toLocaleString('vi-VN')}</td><td class="num">${min.toLocaleString('vi-VN')}</td>
        <td class="num">${vnd(Number(h.gia_ban||0))}</td>
        <td>${low?'<span class="badge b-tc">Dưới mức</span>':'<span class="badge b-ok">Đủ</span>'}${low&&canOp?` <button class="btn-sm ghost" onclick="ctMuaHC(${h.id})">Đề xuất mua</button>`:''}</td></tr>`;}).join('')
      ||`<tr><td colspan="7" style="color:var(--muted)">Chưa có hóa chất trong kho — thêm ở module Kho (loại "Hóa chất").</td></tr>`;
    const soLow=hhCat.filter(h=>Number(h.so_luong||0)<Number(h.ton_min||0)).length;
    const tongGT=hhCat.reduce((s,h)=>s+Number(h.so_luong||0)*Number(h.gia_ban||0),0);
    tonKhoPanel=`<div class="cards">
        <div class="stat accent"><div class="k">Loại hóa chất</div><div class="v">${hhCat.length}</div><div class="d">Đang theo dõi tồn</div></div>
        <div class="stat"><div class="k">Dưới mức tồn</div><div class="v small" style="color:${soLow?'#dc2626':'#16a34a'}">${soLow}</div><div class="d">Cần đề xuất mua</div></div>
        <div class="stat"><div class="k">Giá trị tồn hóa chất</div><div class="v small">${vnd(tongGT)}</div><div class="d">Σ tồn × đơn giá</div></div>
      </div>
      <div class="panel"><div class="panel-h"><h3>Tồn kho hóa chất</h3><div class="spacer"></div>
        <span style="color:var(--muted);font-size:12px">Nguồn: module Kho (loại Hóa chất)</span></div>
        <div class="panel-b"><table><thead><tr><th>Mã</th><th>Tên hóa chất</th><th>ĐVT</th><th class="num">Tồn</th><th class="num">Tồn min</th><th class="num">Đơn giá</th><th>Trạng thái</th></tr></thead>
          <tbody>${cr}</tbody></table></div></div>`;
  }

  const rows=flt.map(x=>`<tr><td><b>${x.ma_hh||'—'}</b> ${x.hang_hoa||''}</td><td class="num">${x.so_luong}</td>
    <td class="num">${vnd(x.don_gia)}</td><td class="num">${vnd(x.thanh_tien)}</td><td>${x.cho_thue_ma}</td>
    <td><span class="badge ${x.trang_thai==='MOI'?'b-cho':'b-ok'}">${x.trang_thai}</span></td>
    <td>${x.da_dong_bo?'<span class="badge b-ok">Đã vào chi phí</span>':'<span style="color:var(--amber)">chưa đồng bộ</span>'}</td></tr>`).join('')
    ||`<tr><td colspan="7" style="color:var(--muted)">Chưa có đề xuất mua ${isHC?'hóa chất':'vật tư/thiết bị'} cho thuê</td></tr>`;

  host.innerHTML=toggle+tonKhoPanel+`
    <div class="panel"><div class="panel-h"><h3>Đề xuất mua ${isHC?'hóa chất':'vật tư / thiết bị'} cho thuê</h3></div>
      <div class="panel-b"><table><thead><tr><th>Hàng hóa</th><th class="num">SL</th><th class="num">Đơn giá</th><th class="num">Thành tiền</th><th>Mã cho thuê</th><th>Trạng thái</th><th>Chi phí</th></tr></thead>
        <tbody>${rows}</tbody></table>
        <div style="color:var(--muted);font-size:12px;margin-top:6px">Đề xuất gắn <b>mã bán hàng cho thuê</b>; bấm <b>Đồng bộ</b> ở tab Chi phí vận hành để cộng vào chi phí tài sản tương ứng.</div></div></div>
    ${canOp?`<div class="panel"><div class="panel-h"><h3>Tạo đề xuất mua ${isHC?'hóa chất':'vật tư/thiết bị'} (gắn mã cho thuê)</h3></div><div class="panel-b">
      <div class="formrow">
        <div class="f" style="flex:2"><label>${isHC?'Hóa chất':'Hàng hóa'} (kho)</label><select id="dx_hh">${hhOpts}</select></div>
        <div class="f"><label>Số lượng</label><input id="dx_sl" type="number" step="any"></div>
        <div class="f"><label>Đơn giá</label><input id="dx_dg" type="number"></div>
        <div class="f" style="flex:2"><label>Dự án</label><select id="dx_ma">${tsOpts}</select></div>
        <div class="f"><label>Tháng</label><input id="dx_thang" type="month" value="${new Date().toISOString().slice(0,7)}"></div>
        <div class="f" style="flex:2"><label>Lý do</label><input id="dx_ld" placeholder="${isHC?'VD: bổ sung hóa chất vận hành':'VD: thay vật tư định kỳ'}"></div>
      </div><button class="btn-sm" onclick="ctTaoDeXuat()">+ Tạo đề xuất</button></div></div>`:''}`;
}
function ctVtSwitch(l){S.ctVtLoai=l;viewChoThue($("#main"));}
function ctMuaHC(id){const e=document.getElementById('dx_hh');if(e)e.value=id;const sl=document.getElementById('dx_sl');if(sl){sl.focus();sl.scrollIntoView({behavior:'smooth',block:'center'});}toast("Đã chọn hóa chất — nhập số lượng để tạo đề xuất","ok");}
async function ctTaoDeXuat(){
  const hh=Number(gv("dx_hh")),sl=Number(gv("dx_sl")||0),tsid=Number(gv("dx_ma")),thang=gv("dx_thang")||new Date().toISOString().slice(0,7);
  if(!hh){toast("Chọn hàng hóa","err");return;}
  if(!sl){toast("Nhập số lượng","err");return;}
  if(!tsid){toast("Chọn dự án","err");return;}
  const t=(S._ctTS||[]).find(x=>x.id===tsid)||{};const pre=t.ten_du_an||t.ma||'';const ma=_maThang(pre,thang);
  const dg=gv("dx_dg")?Number(gv("dx_dg")):null;
  if(S.mode!=="live"){const h=(S._khoHang||[]).find(x=>x.id===hh)||{};const price=dg||Number(h.gia_ban||0);
    (DEMO.dx_thue=DEMO.dx_thue||[]).unshift({id:Date.now(),hang_hoa:h.ten,ma_hh:h.ma,loai:h.loai,so_luong:sl,don_gia:price,thanh_tien:sl*price,cho_thue_ma:ma,trang_thai:"MOI",ngay:thang+"-01",da_dong_bo:false,ly_do:gv("dx_ld")});
    toast("Đã tạo đề xuất "+ma+" (demo)","ok");viewChoThue($("#main"));return;}
  try{await api("/cho-thue/de-xuat-mua",{method:'POST',body:JSON.stringify({hang_hoa_id:hh,so_luong:sl,don_gia:dg,cho_thue_ma:ma,ly_do:gv("dx_ld")||null})});
    toast("Đã tạo đề xuất mua "+ma,"ok");viewChoThue($("#main"));}
  catch(e){toast(e.detail||e.message,"err");}
}

/* --- Bảo trì --- */
async function ctBaoTri(host){
  const canOp=can("cho_thue","THAO_TAC");
  let list;
  if(S.mode==="live"){ try{list=await api("/cho-thue/bao-tri");}catch(e){host.innerHTML=`<div class="perm-denied">${e.detail||e.message}</div>`;return;} }
  else list=DEMO.bao_tri_ct||[];
  if(S.ctDuAn){const _c=(S._ctTS||[]).find(t=>String(t.id)===String(S.ctDuAn));list=list.filter(b=>String(b.tai_san_id)===String(S.ctDuAn)||(_c&&b.ma===_c.ma));}
  const rows=list.map(b=>`<tr><td>${b.ma||''} ${b.tai_san||''}</td><td>${b.ten_cong_viec}</td>
    <td>${b.chu_ky_ngay} ngày</td><td>${b.ngay_ke_tiep||'—'}</td><td>${b.lan_cuoi||'—'}</td>
    <td>${b.qua_han?'<span class="badge b-tc">Quá hạn</span>':'<span class="badge b-ok">Đúng kế hoạch</span>'}</td>
    <td>${canOp?`<button class="btn-sm" onclick="ctHoanThanhBT(${b.id})">Hoàn thành</button>`:'—'}</td></tr>`).join('')
    ||`<tr><td colspan="7" style="color:var(--muted)">Chưa có kế hoạch bảo trì</td></tr>`;
  const tsOpts=(await _ctTaiSan()).map(t=>`<option value="${t.id}" ${String(t.id)===String(S.ctDuAn)?'selected':''}>${t.ten_du_an||t.ma} — ${t.ten}</option>`).join('');
  host.innerHTML=`
    <div class="cards"><div class="stat ${list.some(b=>b.qua_han)?'':'accent'}"><div class="k">Bảo trì quá hạn</div><div class="v">${list.filter(b=>b.qua_han).length}</div><div class="d" style="color:var(--red)">Cần xử lý</div></div></div>
    <div class="panel"><div class="panel-h"><h3>Kế hoạch bảo trì</h3></div>
      <div class="panel-b"><table><thead><tr><th>Tài sản</th><th>Công việc</th><th>Chu kỳ</th><th>Kế tiếp</th><th>Lần cuối</th><th>Trạng thái</th><th></th></tr></thead>
        <tbody>${rows}</tbody></table></div></div>
    ${canOp?`<div class="panel"><div class="panel-h"><h3>Thêm kế hoạch bảo trì</h3></div><div class="panel-b">
      <div class="formrow">
        <div class="f" style="flex:2"><label>Tài sản</label><select id="bt_ts">${tsOpts}</select></div>
        <div class="f" style="flex:2"><label>Công việc</label><input id="bt_cv" placeholder="VD: Vệ sinh màng, thay dầu…"></div>
        <div class="f"><label>Chu kỳ (ngày)</label><input id="bt_ck" type="number" value="90"></div>
        <div class="f"><label>Ngày kế tiếp</label><input id="bt_ngay" type="date"></div>
        <div class="f"><label>Chi phí dự kiến</label><input id="bt_cp" type="number" value="0"></div>
      </div><button class="btn-sm" onclick="ctThemBaoTri()">+ Thêm</button>
      <p style="color:var(--muted);font-size:12px;margin-top:8px">Khi "Hoàn thành", hệ thống dời ngày kế tiếp theo chu kỳ và ghi chi phí bảo trì (nếu có dự kiến).</p></div></div>`:''}`;
}
async function ctThemBaoTri(){
  const ts=Number(gv("bt_ts")),cv=gv("bt_cv");
  if(!cv){toast("Nhập tên công việc","err");return;}
  const body={tai_san_id:ts,ten_cong_viec:cv,chu_ky_ngay:Number(gv("bt_ck")||90),ngay_ke_tiep:gv("bt_ngay")||null,chi_phi_du_kien:Number(gv("bt_cp")||0)};
  if(S.mode!=="live"){const t=(DEMO.tai_san_ct||[]).find(x=>x.id===ts)||{};(DEMO.bao_tri_ct=DEMO.bao_tri_ct||[]).push({id:Date.now(),tai_san:t.ten,ma:t.ma,ten_cong_viec:cv,chu_ky_ngay:body.chu_ky_ngay,ngay_ke_tiep:body.ngay_ke_tiep||new Date(Date.now()+body.chu_ky_ngay*86400000).toISOString().slice(0,10),trang_thai:"KE_HOACH",qua_han:false,chi_phi_du_kien:body.chi_phi_du_kien});toast("Đã thêm (demo)","ok");viewChoThue($("#main"));return;}
  try{await api("/cho-thue/bao-tri",{method:'POST',body:JSON.stringify(body)});toast("Đã thêm kế hoạch bảo trì","ok");viewChoThue($("#main"));}
  catch(e){toast(e.detail||e.message,"err");}
}
async function ctHoanThanhBT(id){
  if(S.mode!=="live"){const b=(DEMO.bao_tri_ct||[]).find(x=>x.id===id);if(b){b.lan_cuoi=new Date().toISOString().slice(0,10);b.ngay_ke_tiep=new Date(Date.now()+(b.chu_ky_ngay||90)*86400000).toISOString().slice(0,10);b.qua_han=false;}toast("Đã hoàn thành (demo)","ok");viewChoThue($("#main"));return;}
  try{const r=await api(`/cho-thue/bao-tri/${id}/hoan-thanh`,{method:'POST'});toast(`Đã hoàn thành — bảo trì kế tiếp ${r.ngay_ke_tiep}`,"ok");viewChoThue($("#main"));}
  catch(e){toast(e.detail||e.message,"err");}
}


/* --- Định mức & tiêu hao theo hệ thống/tháng --- */
function _ctDmInit(){
  if(S.demoDinhMuc)return;
  S.demoDinhMuc={1:[
    {hang_hoa_id:4,ma_hh:"HC-ANTI",ten:"Antiscalant chống cáu cặn RO",don_vi:"lít",gia_ban:85000,dinh_muc_thang:40},
    {hang_hoa_id:5,ma_hh:"HC-CLO",ten:"Chlorine 70%",don_vi:"kg",gia_ban:32000,dinh_muc_thang:60},
    {hang_hoa_id:2,ma_hh:"HC-PAC",ten:"Hóa chất keo tụ PAC",don_vi:"kg",gia_ban:18000,dinh_muc_thang:120},
  ]};
  const _ym=d=>d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0');
  const _n=new Date();
  const m0=_ym(_n),m1=_ym(new Date(_n.getFullYear(),_n.getMonth()-1,1)),m2=_ym(new Date(_n.getFullYear(),_n.getMonth()-2,1));
  S.demoTieuHao={['1|'+m0]:{4:52,5:58,2:100},['1|'+m1]:{4:45,5:62,2:118},['1|'+m2]:{4:38,5:55,2:110}};
}
function _ctDmDemo(tsid,thang){
  _ctDmInit();
  const base=(S.demoDinhMuc[tsid]||[]);
  const dms=base.map(d=>({id:'d'+d.hang_hoa_id,hang_hoa_id:d.hang_hoa_id,ma_hh:d.ma_hh,ten:d.ten,don_vi:d.don_vi,gia_ban:d.gia_ban,dinh_muc_thang:d.dinh_muc_thang,chi_phi_dinh_muc:d.dinh_muc_thang*d.gia_ban}));
  const th=(S.demoTieuHao[tsid+'|'+thang])||{};
  const map={}; base.forEach(d=>map[d.hang_hoa_id]=d);
  Object.keys(th).forEach(hid=>{if(!map[hid]){const h=(DEMO.hang_hoa||[]).find(x=>x.id==hid)||{};map[hid]={hang_hoa_id:+hid,ma_hh:h.ma,ten:h.ten,don_vi:h.don_vi,gia_ban:Number(h.gia_ban||0),dinh_muc_thang:0};}});
  let tdm=0,ttt=0,tcpdm=0,tcptt=0;
  const ct=Object.values(map).map(d=>{const tt=Number(th[d.hang_hoa_id]||0),dm=d.dinh_muc_thang||0;
    const chenh=Math.round((tt-dm)*1000)/1000;const pct=dm>0?Math.round(tt/dm*1000)/10:(tt===0?null:999);
    const cpdm=dm*d.gia_ban,cptt=tt*d.gia_ban;tdm+=dm;ttt+=tt;tcpdm+=cpdm;tcptt+=cptt;
    return {hang_hoa_id:d.hang_hoa_id,ma_hh:d.ma_hh,ten:d.ten,don_vi:d.don_vi,dinh_muc:dm,thuc_te:tt,chenh_lech:chenh,pct,don_gia:d.gia_ban,chi_phi_dinh_muc:cpdm,chi_phi_thuc_te:cptt,vuot_dinh_muc:chenh>0};});
  ct.sort((a,b)=>(a.ten||'')<(b.ten||'')?-1:1);
  const ts=(DEMO.tai_san_ct||[]).find(x=>x.id==tsid)||{};
  return {bc:{tai_san:ts.ten,ma:ts.ma,thang,chi_tiet:ct,tong:{dinh_muc:tdm,thuc_te:ttt,chi_phi_dinh_muc:tcpdm,chi_phi_thuc_te:tcptt,chenh_chi_phi:tcptt-tcpdm}},dms};
}
async function ctDinhMuc(host){
  const canOp=can("cho_thue","THAO_TAC");
  const tsList=await _ctTaiSan();
  if(!S.ctDmTS)S.ctDmTS=tsList[0]?tsList[0].id:null;
  if(!S.ctDmThang)S.ctDmThang=new Date().toISOString().slice(0,7);
  if(!S.ctDmTS){host.innerHTML='<div class="empty" style="padding:20px;color:var(--muted)">Chưa có tài sản cho thuê — thêm ở tab Tài sản.</div>';return;}
  if(!S.ctDmView)S.ctDmView="thang";
  if(S.ctDmView==="sosanh")return ctDmSoSanh(host,tsList);
  let bc,dms;
  if(S.mode==="live"){
    try{ bc=await api(`/cho-thue/bao-cao-tieu-hao?tai_san_id=${S.ctDmTS}&thang=${S.ctDmThang}`);
         dms=await api(`/cho-thue/dinh-muc?tai_san_id=${S.ctDmTS}`);}
    catch(e){host.innerHTML=`<div class="perm-denied">${e.detail||e.message}</div>`;return;}
  } else { ({bc,dms}=_ctDmDemo(S.ctDmTS,S.ctDmThang)); }
  const tsOpts=tsList.map(t=>`<option value="${t.id}" ${t.id===S.ctDmTS?'selected':''}>${t.ma} — ${t.ten}</option>`).join('');
  const hhCons=(await _khoHangHoa()).filter(h=>["VAT_TU","HOA_CHAT"].includes(h.loai));
  const hhOpts=hhCons.map(h=>`<option value="${h.id}">${h.ma?h.ma+' — ':''}${h.ten}</option>`).join('')||`<option value="">(chưa có vật tư/hóa chất trong kho)</option>`;
  const rows=bc.chi_tiet.map(x=>`<tr><td>${x.ma_hh?'<b>'+x.ma_hh+'</b> ':''}${x.ten}</td><td>${x.don_vi||''}</td>
    <td class="num">${x.dinh_muc||0}</td>
    <td class="num">${canOp?`<input type="number" step="any" id="th_${x.hang_hoa_id}" value="${x.thuc_te||0}" style="width:80px;padding:4px 6px;border:1px solid var(--line);border-radius:6px;text-align:right">`:x.thuc_te}</td>
    <td class="num" style="color:${x.chenh_lech>0?'#dc2626':x.chenh_lech<0?'#16a34a':'var(--muted)'}">${x.chenh_lech>0?'+':''}${x.chenh_lech}</td>
    <td class="num">${x.pct==null?'—':x.pct+'%'}${x.vuot_dinh_muc?' <span style="color:#dc2626">⚠</span>':''}</td>
    <td class="num">${vnd(x.chi_phi_dinh_muc)}</td><td class="num" style="${x.vuot_dinh_muc?'color:#dc2626':''}">${vnd(x.chi_phi_thuc_te)}</td></tr>`).join('')
    ||`<tr><td colspan="8" style="color:var(--muted)">Chưa có định mức/tiêu hao cho hệ thống này. Thiết lập định mức bên dưới.</td></tr>`;
  const dmRows=dms.map(d=>`<tr><td>${d.ma_hh?'<b>'+d.ma_hh+'</b> ':''}${d.ten}</td><td>${d.don_vi||''}</td>
    <td class="num">${d.dinh_muc_thang}</td><td class="num">${vnd(d.chi_phi_dinh_muc)}</td>
    <td>${canOp?`<button class="btn-sm ghost" onclick="ctDmXoa('${d.id}')">Xóa</button>`:''}</td></tr>`).join('')
    ||`<tr><td colspan="5" style="color:var(--muted)">Chưa thiết lập định mức cho hệ thống này</td></tr>`;
  const chenh=bc.tong.chenh_chi_phi||0;
  host.innerHTML=_ctDmToggle()+`
    <div class="formrow">
      <div class="f" style="flex:2"><label>Hệ thống (tài sản)</label><select id="dm_ts" onchange="S.ctDmTS=Number(this.value);viewChoThue($('#main'))">${tsOpts}</select></div>
      <div class="f"><label>Tháng</label><input type="month" id="dm_thang" value="${S.ctDmThang}" onchange="S.ctDmThang=this.value;viewChoThue($('#main'))"></div>
    </div>
    <div class="cards">
      <div class="stat accent"><div class="k">Chi phí định mức (kế hoạch)</div><div class="v small">${vnd(bc.tong.chi_phi_dinh_muc)}</div><div class="d">Tháng ${bc.thang}</div></div>
      <div class="stat"><div class="k">Chi phí thực tế</div><div class="v small">${vnd(bc.tong.chi_phi_thuc_te)}</div><div class="d">Theo lượng tiêu hao</div></div>
      <div class="stat"><div class="k">Chênh lệch</div><div class="v small" style="color:${chenh>0?'#dc2626':'#16a34a'}">${chenh>0?'+':''}${vnd(chenh)}</div><div class="d">Thực tế − định mức</div></div>
    </div>
    <div class="panel"><div class="panel-h"><h3>Định mức vs thực tế — ${bc.ma||''} · ${bc.tai_san||''} · ${bc.thang}</h3></div>
      <div class="panel-b"><table><thead><tr><th>Vật tư / hóa chất</th><th>ĐVT</th><th class="num">Định mức/th</th><th class="num">Thực tế</th><th class="num">Chênh</th><th class="num">% ĐM</th><th class="num">CP định mức</th><th class="num">CP thực tế</th></tr></thead>
        <tbody>${rows}</tbody>
        <tfoot><tr><td colspan="6" style="text-align:right"><b>Tổng chi phí</b></td><td class="num"><b>${vnd(bc.tong.chi_phi_dinh_muc)}</b></td><td class="num"><b>${vnd(bc.tong.chi_phi_thuc_te)}</b></td></tr></tfoot></table>
        ${canOp?`<div style="margin-top:10px;display:flex;gap:8px;flex-wrap:wrap">
          <button class="btn-sm" onclick="ctDmLuuTieuHao()">Lưu tiêu hao thực tế</button>
          <button class="btn-sm ghost" onclick="ctDmGhiChiPhi()">→ Ghi chi phí vận hành từ tiêu hao</button></div>
        <p style="color:var(--muted);font-size:12px;margin-top:6px">Nhập lượng dùng thực tế từng dòng → "Lưu tiêu hao". Bấm "Ghi chi phí" để đẩy giá trị tiêu hao vào Chi phí vận hành (mỗi dòng chỉ ghi một lần).</p>`:''}</div></div>
    ${canOp?`<div class="panel"><div class="panel-h"><h3>Thiết lập định mức/tháng cho hệ thống</h3></div><div class="panel-b">
      <table><thead><tr><th>Hóa chất / vật tư</th><th>ĐVT</th><th class="num">Định mức/tháng</th><th class="num">CP định mức</th><th></th></tr></thead><tbody>${dmRows}</tbody></table>
      <div class="formrow" style="margin-top:8px">
        <div class="f" style="flex:2"><label>Vật tư / hóa chất</label><select id="dm_hh">${hhOpts}</select></div>
        <div class="f"><label>Định mức/tháng</label><input id="dm_sl" type="number" step="any"></div>
        <button class="btn-sm" onclick="ctDmThem()">+ Lưu định mức</button>
      </div></div></div>`:''}`;
}
async function ctDmLuuTieuHao(){
  const ct=[];document.querySelectorAll('[id^="th_"]').forEach(el=>{ct.push({hang_hoa_id:Number(el.id.slice(3)),so_luong:Number(el.value||0)});});
  if(!ct.length){toast("Chưa có dòng định mức để ghi tiêu hao","err");return;}
  if(S.mode!=="live"){_ctDmInit();const k=S.ctDmTS+'|'+S.ctDmThang;S.demoTieuHao[k]=S.demoTieuHao[k]||{};ct.forEach(x=>S.demoTieuHao[k][x.hang_hoa_id]=x.so_luong);toast("Đã lưu tiêu hao (demo)","ok");viewChoThue($("#main"));return;}
  try{await api("/cho-thue/tieu-hao",{method:'POST',body:JSON.stringify({tai_san_id:S.ctDmTS,thang:S.ctDmThang,chi_tiet:ct})});toast("Đã lưu tiêu hao thực tế","ok");viewChoThue($("#main"));}
  catch(e){toast(e.detail||e.message,"err");}
}
async function ctDmThem(){
  const hh=Number(gv("dm_hh")),sl=Number(gv("dm_sl")||0);
  if(!hh){toast("Chọn vật tư/hóa chất","err");return;}
  if(S.mode!=="live"){_ctDmInit();const h=(S._khoHang||[]).find(x=>x.id===hh)||{};const arr=S.demoDinhMuc[S.ctDmTS]=S.demoDinhMuc[S.ctDmTS]||[];const ex=arr.find(d=>d.hang_hoa_id===hh);if(ex)ex.dinh_muc_thang=sl;else arr.push({hang_hoa_id:hh,ma_hh:h.ma,ten:h.ten,don_vi:h.don_vi,gia_ban:Number(h.gia_ban||0),dinh_muc_thang:sl});toast("Đã lưu định mức (demo)","ok");viewChoThue($("#main"));return;}
  try{await api("/cho-thue/dinh-muc",{method:'POST',body:JSON.stringify({tai_san_id:S.ctDmTS,hang_hoa_id:hh,dinh_muc_thang:sl})});toast("Đã lưu định mức","ok");viewChoThue($("#main"));}
  catch(e){toast(e.detail||e.message,"err");}
}
async function ctDmXoa(id){
  if(S.mode!=="live"){_ctDmInit();const hid=Number(String(id).replace('d',''));S.demoDinhMuc[S.ctDmTS]=(S.demoDinhMuc[S.ctDmTS]||[]).filter(d=>d.hang_hoa_id!==hid);toast("Đã xóa (demo)","ok");viewChoThue($("#main"));return;}
  try{await api(`/cho-thue/dinh-muc/${id}`,{method:'DELETE'});toast("Đã xóa định mức","ok");viewChoThue($("#main"));}
  catch(e){toast(e.detail||e.message,"err");}
}
async function ctDmGhiChiPhi(){
  if(S.mode!=="live"){toast("Ghi chi phí chạy ở bản kết nối backend","err");return;}
  try{const r=await api(`/cho-thue/tieu-hao/${S.ctDmThang}/ghi-chi-phi?tai_san_id=${S.ctDmTS}`,{method:'POST'});
    toast(r.so_chi_phi_them?`Đã ghi ${r.so_chi_phi_them} chi phí từ tiêu hao (${vnd(r.tong_tien)})`:"Không có tiêu hao mới để ghi","ok");}
  catch(e){toast(e.detail||e.message,"err");}
}


/* --- So sánh tiêu hao nhiều tháng --- */
function _ctDmToggle(){const v=S.ctDmView||"thang";return `<div class="tabs" style="margin-bottom:12px">
  <button class="${v==='thang'?'active':''}" onclick="S.ctDmView='thang';viewChoThue($('#main'))">Theo tháng</button>
  <button class="${v==='sosanh'?'active':''}" onclick="S.ctDmView='sosanh';viewChoThue($('#main'))">So sánh nhiều tháng</button></div>`;}
function _monthsBack(den,n){const p=den.split('-');let y=+p[0],m=+p[1];const out=[];for(let i=n-1;i>=0;i--){let yy=y,mm=m-i;while(mm<=0){mm+=12;yy--;}out.push(yy+'-'+String(mm).padStart(2,'0'));}return out;}
function _svgLines(series,labels,opt){
  opt=opt||{};const w=opt.w||640,h=opt.h||240,padL=46,padB=32,padT=12,padR=12;
  const all=series.flatMap(s=>s.pts);
  if(!all.length)return '<div style="color:var(--muted);padding:18px">Chưa đủ dữ liệu để vẽ biểu đồ.</div>';
  const ymax=opt.ymax||Math.max(1,...all)*1.1;
  const iw=w-padL-padR,ih=h-padB-padT,x0=padL,y0=h-padB,n=labels.length;
  const X=i=>x0+(n<=1?iw/2:iw*i/(n-1));
  const Y=v=>y0-ih*Math.max(0,Math.min(v,ymax))/ymax;
  let g='';
  for(let k=0;k<=4;k++){const yy=y0-ih*k/4;const val=Math.round(ymax*k/4*10)/10;
    g+=`<line x1="${x0}" y1="${yy.toFixed(1)}" x2="${x0+iw}" y2="${yy.toFixed(1)}" stroke="#eef2f4"/><text x="${x0-6}" y="${(yy+3).toFixed(1)}" text-anchor="end" font-size="9.5" fill="#9fb0bb">${val}${opt.unit||''}</text>`;}
  const xl=labels.map((l,i)=>`<text x="${X(i).toFixed(1)}" y="${h-padB+15}" text-anchor="middle" font-size="9" fill="#6b7280">${l.slice(2)}</text>`).join('');
  let paths='';
  series.forEach(s=>{const poly=s.pts.map((v,i)=>`${X(i).toFixed(1)},${Y(v).toFixed(1)}`).join(' ');
    paths+=`<polyline points="${poly}" fill="none" stroke="${s.color}" stroke-width="2" ${s.dash?'stroke-dasharray="5 4"':''}/>`;
    paths+=s.pts.map((v,i)=>`<circle cx="${X(i).toFixed(1)}" cy="${Y(v).toFixed(1)}" r="3" fill="${s.color}"/>`).join('');});
  const leg=series.map(s=>`<span style="display:inline-flex;align-items:center;gap:5px;margin-right:14px;font-size:12px"><span style="width:14px;border-top:3px ${s.dash?'dashed':'solid'} ${s.color}"></span>${s.name}</span>`).join('');
  return `<div style="margin-bottom:6px">${leg}</div><svg viewBox="0 0 ${w} ${h}" style="width:100%;max-width:${w}px;height:auto">${g}${paths}${xl}</svg>`;
}
function _ctDmSoSanhDemo(tsid,den,n){
  _ctDmInit();const months=_monthsBack(den,n);
  const base=S.demoDinhMuc[tsid]||[];const norms={};base.forEach(d=>norms[d.hang_hoa_id]=d);
  const hids=new Set(base.map(d=>d.hang_hoa_id));
  months.forEach(m=>{const th=S.demoTieuHao[tsid+'|'+m]||{};Object.keys(th).forEach(h=>hids.add(Number(h)));});
  const info={};hids.forEach(h=>{const d=norms[h];if(d)info[h]={ma:d.ma_hh,ten:d.ten,don_vi:d.don_vi,gia:d.gia_ban};else{const x=(DEMO.hang_hoa||[]).find(z=>z.id==h)||{};info[h]={ma:x.ma,ten:x.ten,don_vi:x.don_vi,gia:Number(x.gia_ban||0)};}});
  const rows=[...hids].map(h=>{const per={};let tong=0;months.forEach(m=>{const q=Number((S.demoTieuHao[tsid+'|'+m]||{})[h]||0);per[m]=q;tong+=q;});const dm=norms[h]?norms[h].dinh_muc_thang:0;return {hang_hoa_id:h,ma_hh:info[h].ma,ten:info[h].ten,don_vi:info[h].don_vi,dinh_muc:dm,gia:info[h].gia,theo_thang:per,tb_thuc_te:Math.round(tong/months.length*1000)/1000,vuot_thang:months.filter(m=>dm>0&&per[m]>dm)};});
  rows.sort((a,b)=>(a.ten||'')<(b.ten||'')?-1:1);
  const cp_tt=months.map(m=>{let s=0;[...hids].forEach(h=>{s+=Number((S.demoTieuHao[tsid+'|'+m]||{})[h]||0)*info[h].gia;});return Math.round(s);});
  const cdm=base.reduce((s,d)=>s+d.dinh_muc_thang*d.gia_ban,0);
  const ts=(DEMO.tai_san_ct||[]).find(x=>x.id==tsid)||{};
  return {ma:ts.ma,tai_san:ts.ten,thang_list:months,chi_phi_thuc_te:cp_tt,chi_phi_dinh_muc_thang:Math.round(cdm),chi_phi_dinh_muc:months.map(()=>Math.round(cdm)),theo_hang_hoa:rows};
}
async function ctDmSoSanh(host,tsList){
  if(!S.ctDmSoThang)S.ctDmSoThang=6;
  const den=S.ctDmThang||new Date().toISOString().slice(0,7);
  let d;
  if(S.mode==="live"){try{d=await api(`/cho-thue/so-sanh-tieu-hao?tai_san_id=${S.ctDmTS}&den_thang=${den}&so_thang=${S.ctDmSoThang}`);}catch(e){host.innerHTML=_ctDmToggle()+`<div class="perm-denied">${e.detail||e.message}</div>`;return;}}
  else d=_ctDmSoSanhDemo(S.ctDmTS,den,S.ctDmSoThang);
  const tsOpts=tsList.map(t=>`<option value="${t.id}" ${t.id===S.ctDmTS?'selected':''}>${t.ma} — ${t.ten}</option>`).join('');
  const months=d.thang_list;
  const ptsTT=d.chi_phi_thuc_te.map(x=>Math.round(x/1e6*100)/100);
  const ptsDM=d.chi_phi_dinh_muc.map(x=>Math.round(x/1e6*100)/100);
  const ymax=Math.max(1,...ptsTT,...ptsDM)*1.15;
  const chart=_svgLines([{name:"Chi phí thực tế",color:"#0e7490",pts:ptsTT},{name:"Định mức (ngân sách)",color:"#b45309",pts:ptsDM,dash:true}],months,{ymax,unit:"tr"});
  const head=`<th>Vật tư / hóa chất</th><th class="num">ĐM/th</th>${months.map(m=>`<th class="num">${m.slice(2)}</th>`).join('')}<th class="num">TB</th>`;
  const rows=d.theo_hang_hoa.map(r=>{const cells=months.map(m=>{const q=r.theo_thang[m]||0;const vuot=(r.vuot_thang||[]).includes(m);return `<td class="num" style="${vuot?'color:#dc2626;font-weight:600':''}">${q||'—'}${vuot?' ⚠':''}</td>`;}).join('');
    return `<tr><td>${r.ma_hh?'<b>'+r.ma_hh+'</b> ':''}${r.ten} <span style="color:var(--muted)">(${r.don_vi||''})</span></td><td class="num">${r.dinh_muc||'—'}</td>${cells}<td class="num">${r.tb_thuc_te}</td></tr>`;}).join('')
    ||`<tr><td colspan="${months.length+3}" style="color:var(--muted)">Chưa có dữ liệu tiêu hao trong khoảng này</td></tr>`;
  const cpRow=`<tr style="border-top:2px solid var(--line)"><td><b>Chi phí thực tế</b></td><td class="num">${vnd(d.chi_phi_dinh_muc_thang)}</td>${months.map((m,i)=>`<td class="num"><b>${vnd(d.chi_phi_thuc_te[i])}</b></td>`).join('')}<td></td></tr>`;
  host.innerHTML=_ctDmToggle()+`
    <div class="formrow">
      <div class="f" style="flex:2"><label>Hệ thống (tài sản)</label><select onchange="S.ctDmTS=Number(this.value);viewChoThue($('#main'))">${tsOpts}</select></div>
      <div class="f"><label>Đến tháng</label><input type="month" value="${den}" onchange="S.ctDmThang=this.value;viewChoThue($('#main'))"></div>
      <div class="f"><label>Số tháng</label><select onchange="S.ctDmSoThang=Number(this.value);viewChoThue($('#main'))">${[3,6,12].map(n=>`<option ${n===S.ctDmSoThang?'selected':''}>${n}</option>`).join('')}</select></div>
    </div>
    <div class="panel"><div class="panel-h"><h3>Xu hướng chi phí: thực tế vs định mức (triệu đồng)</h3></div>
      <div class="panel-b">${chart}</div></div>
    <div class="panel"><div class="panel-h"><h3>Tiêu hao theo hóa chất qua các tháng — ${d.ma||''} ${d.tai_san||''}</h3></div>
      <div class="panel-b" style="overflow-x:auto"><table><thead><tr>${head}</tr></thead><tbody>${rows}${cpRow}</tbody></table>
      <div style="color:var(--muted);font-size:12px;margin-top:6px">⚠ = tháng vượt định mức. TB = trung bình thực tế trong khoảng. Cột tháng hiển thị YY-MM.</div></div></div>`;
}


/* --- Document dự án: Biểu mẫu (biên bản) + Lưu trữ tài liệu --- */
const NHOM_TL={CO_CQ:["CO/CQ","b-info"],BAN_VE:["Bản vẽ","b-ok"],CODE:["File code điều khiển","b-cho"],BIEU_MAU:["Biểu mẫu đã ký","b-tc"],KHAC:["Khác","b-info"]};
function _fmtKB(n){n=Number(n||0);return n<1024?n+' B':n<1048576?(n/1024).toFixed(0)+' KB':(n/1048576).toFixed(1)+' MB';}

async function ctDocument(host,pid){
  pid=pid||S.ctDuAn; S.ctDocPid=pid;
  if(!pid){host.innerHTML='<div style="padding:22px;color:var(--muted)">Chọn một <b>dự án</b> ở thanh trên cùng (hoặc mở chi tiết một dự án) để quản lý tài liệu.</div>';return;}
  const t=(S._ctTS||[]).find(x=>String(x.id)===String(pid))||{};
  const canOp=can("cho_thue","THAO_TAC");
  let docs;
  if(S.mode==="live"){try{docs=await api(`/cho-thue/du-an/${pid}/tai-lieu`);}catch(e){host.innerHTML=`<div class="perm-denied">${e.detail||e.message}</div>`;return;}}
  else docs=(S.demoTaiLieu&&S.demoTaiLieu[pid])||[];

  const forms=[["giao_nhan","Biên bản giao nhận"],["ban_giao","Biên bản bàn giao"],["nghiem_thu","Biên bản nghiệm thu"],["khao_sat","Biên bản khảo sát hiện trường"]];
  const formBtns=forms.map(([k,l])=>`<button class="btn-sm ghost" style="margin:4px 6px 4px 0" onclick="ctBieuMau('${k}')">🖨 ${l}</button>`).join('');

  const grp={};docs.forEach(d=>{(grp[d.loai]=grp[d.loai]||[]).push(d);});
  const docRows=docs.map(d=>{const m=NHOM_TL[d.loai]||[d.loai,'b-info'];return `<tr><td>${d.ten}</td><td><span class="badge ${m[1]}">${m[0]}</span></td><td>${d.ngay||''}</td><td class="num">${_fmtKB(d.kich_thuoc)}</td>
    <td><button class="btn-sm ghost" onclick="ctTaiLieuTai(${d.id},'${(d.ten||'tai-lieu').replace(/'/g,'')}')">Tải</button>${canOp?` <button class="btn-sm ghost" onclick="ctTaiLieuXoa(${d.id})">Xóa</button>`:''}</td></tr>`;}).join('')
    ||`<tr><td colspan="5" style="color:var(--muted)">Chưa có tài liệu lưu trữ</td></tr>`;

  host.innerHTML=`
    <div class="panel"><div class="panel-h"><h3>1 · Biểu mẫu triển khai dự án</h3><div class="spacer"></div><span style="color:var(--muted);font-size:12px">${t.ten_du_an||t.ma} — ${t.ten||''}</span></div>
      <div class="panel-b">
        <p style="color:var(--muted);font-size:13px;margin:0 0 8px">Mở biểu mẫu in sẵn tiêu đề công ty &amp; thông tin dự án (in / lưu PDF, ký rồi tải lại vào mục lưu trữ bên dưới với nhóm "Biểu mẫu đã ký").</p>
        ${formBtns}
      </div></div>

    <div class="panel"><div class="panel-h"><h3>2 · Lưu trữ dữ liệu dự án</h3><div class="spacer"></div><span style="color:var(--muted);font-size:12px">CO/CQ · Bản vẽ · File code điều khiển · …</span></div>
      <div class="panel-b">
        ${canOp?`<div class="formrow" style="align-items:flex-end">
          <div class="f" style="flex:2"><label>Tên tài liệu (tùy chọn)</label><input id="tl_ten" placeholder="VD: CO/CQ màng RO Dow"></div>
          <div class="f"><label>Nhóm</label><select id="tl_nhom"><option value="CO_CQ">CO/CQ</option><option value="BAN_VE">Bản vẽ</option><option value="CODE">File code điều khiển</option><option value="BIEU_MAU">Biểu mẫu đã ký</option><option value="KHAC">Khác</option></select></div>
          <div class="f" style="flex:2"><label>Tệp</label><input id="tl_file" type="file"></div>
          <button class="btn-sm" onclick="ctTaiLieuUp()">⬆ Tải lên</button>
        </div>`:''}
        <table style="margin-top:6px"><thead><tr><th>Tên</th><th>Nhóm</th><th>Ngày</th><th class="num">Dung lượng</th><th></th></tr></thead>
          <tbody>${docRows}</tbody></table>
      </div></div>`;
}

async function ctTaiLieuUp(){
  const pid=S.ctDocPid||S.ctDuAn;
  const fi=document.getElementById('tl_file');
  if(!fi||!fi.files||!fi.files[0]){toast("Chọn tệp để tải lên","err");return;}
  const file=fi.files[0],nhom=gv("tl_nhom"),ten=gv("tl_ten");
  if(S.mode!=="live"){S.demoTaiLieu=S.demoTaiLieu||{};const arr=S.demoTaiLieu[pid]=S.demoTaiLieu[pid]||[];arr.unshift({id:Date.now(),ten:ten||file.name,loai:nhom,kich_thuoc:file.size,ngay:new Date().toISOString().slice(0,10)});toast("Đã thêm tài liệu (demo)","ok");viewChoThue($("#main"));return;}
  const fd=new FormData();fd.append("file",file);fd.append("loai",nhom);if(ten)fd.append("ten",ten);
  try{await apiUpload(`/cho-thue/du-an/${pid}/tai-lieu`,fd);toast("Đã tải tài liệu lên","ok");viewChoThue($("#main"));}
  catch(e){toast(e.detail||e.message,"err");}
}
async function ctTaiLieuTai(id,ten){
  if(S.mode!=="live"){toast("Tải tệp chạy ở bản kết nối backend","err");return;}
  try{const h={};if(S.token)h['Authorization']='Bearer '+S.token;
    const r=await fetch(S.api+`/cho-thue/tai-lieu/${id}/tai`,{headers:h});
    if(!r.ok)throw new Error('Lỗi '+r.status);
    const blob=await r.blob();const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=ten||('tai-lieu-'+id);a.click();URL.revokeObjectURL(a.href);}
  catch(e){toast(e.message||'Lỗi tải tệp',"err");}
}
async function ctTaiLieuXoa(id){
  const pid=S.ctDocPid||S.ctDuAn;
  if(S.mode!=="live"){S.demoTaiLieu[pid]=(S.demoTaiLieu[pid]||[]).filter(d=>d.id!==id);toast("Đã xóa (demo)","ok");viewChoThue($("#main"));return;}
  try{await api(`/cho-thue/tai-lieu/${id}`,{method:'DELETE'});toast("Đã xóa tài liệu","ok");viewChoThue($("#main"));}
  catch(e){toast(e.detail||e.message,"err");}
}

/* ---- Sinh biểu mẫu biên bản in sẵn (mở cửa sổ in) ---- */
function _inBienBan(type,pinfo){
  const pre=pinfo.pre||'';
  const t={ma:pinfo.ma,ten:pinfo.ten,khach_hang:pinfo.khach_hang,vi_tri:pinfo.vi_tri};
  const TITLES={giao_nhan:"BIÊN BẢN GIAO NHẬN",ban_giao:"BIÊN BẢN BÀN GIAO",nghiem_thu:"BIÊN BẢN NGHIỆM THU",khao_sat:"BIÊN BẢN KHẢO SÁT HIỆN TRƯỜNG"};
  const dl='.....................';
  const letterhead=`<table style="width:100%;border-bottom:2px solid #0e7490;padding-bottom:6px;margin-bottom:6px"><tr>
    <td style="vertical-align:top">
      <div style="font-weight:800;color:#0e7490;font-size:15px">CÔNG TY TNHH GPKT SÓNG VIỆT</div>
      <div style="font-size:11.5px">448 Võ Văn Tần, P. Bàn Cờ, Q.3, TP. Hồ Chí Minh</div>
      <div style="font-size:11.5px">ĐT: +84 28 3736 7889 · songviet.com.vn</div>
    </td><td style="text-align:right;vertical-align:top;font-size:11.5px">
      <div>Số: ......./BB-SVWS</div></td></tr></table>`;
  const national=`<div style="text-align:center;font-weight:700;font-size:13px">CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</div>
    <div style="text-align:center;font-size:12.5px">Độc lập - Tự do - Hạnh phúc</div>
    <div style="text-align:center;margin:2px 0 10px">———————o0o———————</div>`;
  const info=`<table class="info"><tbody>
    <tr><td style="width:130px">Tên dự án:</td><td><b>${pre}</b></td><td style="width:90px">Mã dự án:</td><td>${t.ma||dl}</td></tr>
    <tr><td>Hệ thống/Hạng mục:</td><td colspan="3">${t.ten||dl}</td></tr>
    <tr><td>Khách hàng:</td><td>${t.khach_hang||dl}</td><td>Địa điểm:</td><td>${t.vi_tri||dl}</td></tr>
    <tr><td>Thời gian:</td><td colspan="3">....... giờ ......, ngày ...... tháng ...... năm 20......</td></tr>
  </tbody></table>`;
  const parties=`<p style="margin:10px 0 4px"><b>BÊN A (Khách hàng/Chủ đầu tư):</b> ${t.khach_hang||dl}</p>
    <div style="font-size:12.5px">Đại diện: ........................................................ &nbsp; Chức vụ: ............................</div>
    <p style="margin:10px 0 4px"><b>BÊN B (Đơn vị thực hiện):</b> CÔNG TY TNHH GPKT SÓNG VIỆT</p>
    <div style="font-size:12.5px">Đại diện: ........................................................ &nbsp; Chức vụ: ............................</div>`;
  const sign=`<table style="width:100%;margin-top:26px;text-align:center"><tr>
    <td style="width:50%"><b>ĐẠI DIỆN BÊN A</b><div style="font-size:11.5px">(Ký, ghi rõ họ tên)</div><div style="height:72px"></div></td>
    <td style="width:50%"><b>ĐẠI DIỆN BÊN B</b><div style="font-size:11.5px">(Ký, ghi rõ họ tên)</div><div style="height:72px"></div></td></tr></table>`;
  const closing=`<p style="margin-top:10px">Biên bản được lập thành 02 bản có giá trị pháp lý như nhau, mỗi bên giữ 01 bản.</p>`;
  const rowsBlank=(cols,n)=>{let r='';for(let i=1;i<=n;i++){r+='<tr><td style="text-align:center">'+i+'</td>'+cols.map(()=>'<td>&nbsp;</td>').join('')+'</tr>';}return r;};

  let body='';
  if(type==='giao_nhan'){
    body=`${parties}<p style="margin-top:10px">Hai bên tiến hành giao nhận các hạng mục/thiết bị/vật tư của dự án như sau:</p>
      <table class="data"><thead><tr><th style="width:36px">STT</th><th>Tên thiết bị/vật tư</th><th style="width:60px">ĐVT</th><th style="width:60px">SL</th><th style="width:130px">Tình trạng</th><th style="width:120px">Ghi chú</th></tr></thead>
      <tbody>${rowsBlank(['','','','',''],6)}</tbody></table>
      <p>Tình trạng chung khi giao nhận: ............................................................................................</p>${closing}`;
  }else if(type==='ban_giao'){
    body=`${parties}<p style="margin-top:10px">Bên B bàn giao cho Bên A hệ thống <b>${t.ten||pre}</b> để đưa vào vận hành/sử dụng, kèm theo các tài liệu và nội dung sau:</p>
      <table class="data"><thead><tr><th style="width:36px">STT</th><th>Nội dung bàn giao</th><th style="width:140px">Có / Không</th><th style="width:150px">Ghi chú</th></tr></thead>
      <tbody>
        <tr><td style="text-align:center">1</td><td>Hệ thống/thiết bị đã lắp đặt hoàn chỉnh</td><td>&nbsp;</td><td>&nbsp;</td></tr>
        <tr><td style="text-align:center">2</td><td>Hồ sơ CO/CQ vật tư – thiết bị</td><td>&nbsp;</td><td>&nbsp;</td></tr>
        <tr><td style="text-align:center">3</td><td>Bản vẽ hoàn công / P&amp;ID</td><td>&nbsp;</td><td>&nbsp;</td></tr>
        <tr><td style="text-align:center">4</td><td>Tài liệu hướng dẫn vận hành – bảo trì</td><td>&nbsp;</td><td>&nbsp;</td></tr>
        <tr><td style="text-align:center">5</td><td>File chương trình điều khiển (PLC/HMI)</td><td>&nbsp;</td><td>&nbsp;</td></tr>
        ${rowsBlank(['','',''],2)}
      </tbody></table>${closing}`;
  }else if(type==='nghiem_thu'){
    body=`${parties}<p style="margin-top:10px">Hai bên tiến hành nghiệm thu hệ thống <b>${t.ten||pre}</b>. Kết quả kiểm tra/thử nghiệm:</p>
      <table class="data"><thead><tr><th style="width:36px">STT</th><th>Hạng mục kiểm tra</th><th style="width:150px">Yêu cầu</th><th style="width:120px">Kết quả</th><th style="width:90px">Đạt/Không</th></tr></thead>
      <tbody>${rowsBlank(['','','',''],7)}</tbody></table>
      <p style="margin-top:8px"><b>Kết luận nghiệm thu:</b> &nbsp; ☐ Đạt &nbsp;&nbsp; ☐ Đạt có điều kiện &nbsp;&nbsp; ☐ Không đạt</p>
      <p>Nội dung tồn tại cần khắc phục (nếu có): ............................................................................</p>${closing}`;
  }else{ // khao_sat
    body=`${parties}<p style="margin-top:10px">Bên B tiến hành khảo sát hiện trường phục vụ triển khai dự án. Thông tin ghi nhận:</p>
      <table class="data"><thead><tr><th style="width:36px">STT</th><th>Nội dung khảo sát</th><th>Thông số ghi nhận</th></tr></thead>
      <tbody>
        <tr><td style="text-align:center">1</td><td>Nguồn nước đầu vào (loại, lưu lượng, chất lượng)</td><td>&nbsp;</td></tr>
        <tr><td style="text-align:center">2</td><td>Yêu cầu nước sau xử lý (mục đích, tiêu chuẩn)</td><td>&nbsp;</td></tr>
        <tr><td style="text-align:center">3</td><td>Công suất – nhu cầu sử dụng</td><td>&nbsp;</td></tr>
        <tr><td style="text-align:center">4</td><td>Mặt bằng lắp đặt (diện tích, cao độ)</td><td>&nbsp;</td></tr>
        <tr><td style="text-align:center">5</td><td>Nguồn điện (pha, công suất khả dụng)</td><td>&nbsp;</td></tr>
        ${rowsBlank(['',''],3)}
      </tbody></table>
      <p>Đề xuất/Ghi chú của đơn vị khảo sát: ............................................................................</p>${closing}`;
  }

  const html=`<!doctype html><html lang="vi"><head><meta charset="utf-8"><title>${TITLES[type]} - ${pre}</title>
    <style>@page{size:A4;margin:18mm}
    body{font-family:'Times New Roman',serif;color:#111;font-size:13.5px;line-height:1.5;margin:0}
    h1{text-align:center;font-size:18px;margin:8px 0 2px}
    table{border-collapse:collapse}
    table.info td{padding:3px 6px;font-size:13px;vertical-align:top}
    table.data{width:100%;margin:8px 0}
    table.data th,table.data td{border:1px solid #333;padding:5px 7px;font-size:12.5px}
    .bar{position:fixed;top:0;left:0;right:0;background:#0e7490;color:#fff;padding:8px;text-align:center}
    .bar button{font-size:14px;padding:6px 16px;border:0;border-radius:6px;cursor:pointer;margin:0 4px}
    @media print{.bar{display:none}}</style></head>
    <body>
    <div class="bar"><button onclick="window.print()">🖨 In / Lưu PDF</button><button onclick="window.close()">Đóng</button></div>
    <div style="margin-top:46px">${letterhead}${national}
      <h1>${TITLES[type]}</h1>
      <div style="text-align:center;font-size:12px;margin-bottom:8px">Dự án: <b>${pre}</b></div>
      ${info}${body}${sign}
    </div></body></html>`;
  const w=window.open('','_blank');
  if(!w){toast("Trình duyệt chặn cửa sổ bật lên — hãy cho phép pop-up","err");return;}
  w.document.write(html);w.document.close();
}
function ctBieuMau(type){
  const pid=S.ctDocPid||S.ctDuAn;
  const t=(S._ctTS||[]).find(x=>String(x.id)===String(pid))||{};
  _inBienBan(type,{pre:t.ten_du_an||t.ma||'',ma:t.ma,ten:t.ten,khach_hang:t.khach_hang,vi_tri:t.vi_tri});
}
function daBieuMau(type){
  const ct=S.daCt||{};
  _inBienBan(type,{pre:ct.ma||'',ma:ct.ma,ten:ct.ten,khach_hang:ct.chu_dau_tu,vi_tri:ct.dia_diem||ct.dia_chi});
}

/* ---------- Kho ---------- */
async function viewKho(m){
  if(!S.khoTab)S.khoTab="ton_kho";
  m.innerHTML=head("Kho hàng","Tồn kho · Nhập/Xuất · Phiếu kho · Kiểm kê · Cảnh báo tồn");
  const tabs=[["ton_kho","Tồn kho"],["nhap_xuat","Nhập / Xuất"],["phieu","Phiếu kho"],["kiem_ke","Kiểm kê"],["canh_bao","Cảnh báo tồn"]];
  m.innerHTML+=`<div class="tabs">${tabs.map(([k,l])=>`<button class="${S.khoTab===k?'active':''}" onclick="khoSwitch('${k}')">${l}</button>`).join('')}</div><div id="khoBody">Đang tải…</div>`;
  const host=$("#khoBody");
  if(S.khoTab==="ton_kho") await khoTonKho(host);
  else if(S.khoTab==="nhap_xuat") await khoNhapXuat(host);
  else if(S.khoTab==="phieu") await khoPhieu(host);
  else if(S.khoTab==="kiem_ke") await khoKiemKe(host);
  else if(S.khoTab==="canh_bao") await khoCanhBao(host);
}
function khoSwitch(t){S.khoTab=t;S.khoSel=null;S.khoEdit=null;viewKho($("#main"));}
const LOAI_HH={VAT_TU:"Vật tư",THIET_BI:"Thiết bị",SAN_PHAM:"Sản phẩm",HOA_CHAT:"Hóa chất"};
async function _khoHangHoa(force){
  if(S._khoHang && !force) return S._khoHang;
  let list;
  if(S.mode==="live"){ try{list=await api("/kho/hang-hoa");}catch(e){toast(e.detail||e.message,"err");list=[];} }
  else list=(DEMO.hang_hoa||[]);
  S._khoHang=list; return list;
}

/* --- Tồn kho --- */
async function khoTonKho(host){
  const list=await _khoHangHoa(true), canDo=can("kho","THAO_TAC");
  let kpi;
  if(S.mode==="live"){ try{kpi=await api("/kho/tong-quan");}catch{kpi=null;} }
  if(!kpi){ const gt=list.reduce((s,h)=>s+Number(h.so_luong||0)*Number(h.gia_ban||0),0);
    kpi={so_mat_hang:list.length,duoi_min:list.filter(h=>Number(h.so_luong)<Number(h.ton_min)).length,gia_tri_ton:gt}; }
  const rows=list.map(h=>{const low=Number(h.so_luong)<Number(h.ton_min);const gt=Number(h.so_luong||0)*Number(h.gia_ban||0);
    return `<tr>
      <td><b>${h.ma||'—'}</b></td><td>${h.ten}</td><td><span class="badge b-info">${LOAI_HH[h.loai]||h.loai}</span></td>
      <td class="num">${Number(h.so_luong).toLocaleString('vi-VN')} ${h.don_vi||''}</td>
      <td class="num">${Number(h.ton_min).toLocaleString('vi-VN')}</td>
      <td class="num">${h.ton_max!=null?Number(h.ton_max).toLocaleString('vi-VN'):'—'}</td>
      <td class="num">${h.gia_ban?vnd(h.gia_ban):'—'}</td>
      <td class="num">${gt?vnd(gt):'—'}</td>
      <td>${low?'<span class="badge b-tc">Dưới min</span>':'<span class="badge b-ok">Đủ</span>'}</td>
      <td>${canDo?`<button class="btn-sm ghost" onclick="khoEdit(${h.id})">Sửa</button>`:''}</td></tr>`;}).join('');
  host.innerHTML=`<div class="cards">
    <div class="stat accent"><div class="k">Số mặt hàng</div><div class="v">${kpi.so_mat_hang}</div><div class="d">Đang theo dõi tồn</div></div>
    <div class="stat"><div class="k">Dưới mức tồn tối thiểu</div><div class="v small">${kpi.duoi_min}</div><div class="d" style="color:var(--red)">Cần bổ sung</div></div>
    <div class="stat"><div class="k">Giá trị tồn kho</div><div class="v small">${vnd(kpi.gia_tri_ton||0)}</div><div class="d">Tồn × giá</div></div>
  </div>
  <div class="panel"><div class="panel-h"><h3>Danh mục hàng hóa &amp; tồn</h3><div class="spacer"></div>
    <input id="kho_q" placeholder="Tìm mã/tên…" oninput="khoFilter()" style="padding:6px 10px;border:1px solid var(--line);border-radius:7px;font-size:13px;max-width:200px">
    ${canDo?`<button class="btn-sm" onclick="khoFormToggle()" style="margin-left:8px">+ Thêm hàng hóa</button>`:''}</div>
    ${canDo?khoForm():`<div class="perm-denied">Vai trò ${S.role} chỉ được xem kho — không thể thêm/sửa.</div>`}
    <div class="panel-b"><table><thead><tr><th>Mã</th><th>Tên</th><th>Loại</th>
      <th class="num">Tồn</th><th class="num">Min</th><th class="num">Max</th><th class="num">Giá</th><th class="num">Giá trị</th><th>Trạng thái</th><th></th></tr></thead>
      <tbody id="khoRows">${rows||`<tr><td colspan="10" style="color:var(--muted)">Chưa có hàng hóa</td></tr>`}</tbody></table></div></div>`;
  if(S.khoEdit) khoFillForm(S.khoEdit);
}
function khoFilter(){const q=(gv("kho_q")||'').toLowerCase();
  document.querySelectorAll('#khoRows tr').forEach(tr=>{tr.style.display=tr.textContent.toLowerCase().includes(q)?'':'none';});}
function khoForm(){return `<div id="khoForm" class="formrow hidden">
  <div class="f"><label>Mã</label><input id="k_ma" placeholder="VD: BOM-02"></div>
  <div class="f" style="flex:2"><label>Tên hàng hóa</label><input id="k_ten" placeholder="Tên"></div>
  <div class="f"><label>Loại</label><select id="k_loai"><option value="VAT_TU">Vật tư</option><option value="THIET_BI">Thiết bị</option><option value="HOA_CHAT">Hóa chất</option><option value="SAN_PHAM">Sản phẩm</option></select></div>
  <div class="f"><label>Đơn vị</label><input id="k_dv" placeholder="cái/kg/tấm"></div>
  <div class="f"><label>Giá (₫)</label><input id="k_gia" type="number" value="0"></div>
  <div class="f"><label>Tồn min</label><input id="k_min" type="number" value="0"></div>
  <div class="f"><label>Tồn max</label><input id="k_max" type="number" placeholder="—"></div>
  <button class="btn-sm" id="k_save" onclick="khoSave()">Lưu</button>
  <button class="btn-sm ghost" onclick="khoFormCancel()">Hủy</button></div>`;}
function khoFormToggle(){S.khoEdit=null;const f=$("#khoForm");f.classList.toggle('hidden');
  if(!f.classList.contains('hidden')){["k_ten","k_dv","k_max"].forEach(id=>{const e=document.getElementById(id);if(e)e.value='';});
    ["k_gia","k_min"].forEach(id=>{const e=document.getElementById(id);if(e)e.value='0';});
    const ma=document.getElementById('k_ma');if(ma){ma.value='';ma.disabled=false;} const sv=$("#k_save");if(sv)sv.textContent="Lưu";}}
function khoFormCancel(){S.khoEdit=null;$("#khoForm").classList.add('hidden');}
function khoEdit(id){S.khoEdit=id;const f=$("#khoForm");if(f)f.classList.remove('hidden');khoFillForm(id);}
function khoFillForm(id){const h=(S._khoHang||[]).find(x=>x.id===id);if(!h)return;
  const set=(i,v)=>{const e=document.getElementById(i);if(e)e.value=v;};
  set("k_ma",h.ma||"");set("k_ten",h.ten||"");set("k_dv",h.don_vi||"");set("k_gia",h.gia_ban||0);set("k_min",h.ton_min||0);set("k_max",h.ton_max!=null?h.ton_max:"");
  const sel=document.getElementById('k_loai');if(sel)sel.value=h.loai||"VAT_TU";
  const ma=document.getElementById('k_ma');if(ma)ma.disabled=true; const sv=$("#k_save");if(sv)sv.textContent="Cập nhật";}
async function khoSave(){
  const ten=gv("k_ten"); if(!ten){toast("Nhập tên hàng hóa","err");return;}
  const body={ten,loai:gv("k_loai"),don_vi:gv("k_dv")||null,gia_ban:Number(gv("k_gia")||0),ton_min:Number(gv("k_min")||0),ton_max:gv("k_max")!==''?Number(gv("k_max")):null};
  if(S.khoEdit){
    if(S.mode==="live"){ try{await api(`/kho/hang-hoa/${S.khoEdit}`,{method:'PUT',body:JSON.stringify(body)});}catch(e){toast(e.detail||e.message,"err");return;} }
    else { const h=(DEMO.hang_hoa||[]).find(x=>x.id===S.khoEdit); if(h)Object.assign(h,body); }
    toast("Đã cập nhật hàng hóa","ok");
  } else {
    body.ma=gv("k_ma")||null;
    if(S.mode==="live"){ try{await api("/kho/hang-hoa",{method:'POST',body:JSON.stringify(body)});}catch(e){toast(e.detail||e.message,"err");return;} }
    else { (DEMO.hang_hoa=DEMO.hang_hoa||[]).push(Object.assign({id:Date.now(),so_luong:0},body)); }
    toast("Đã thêm hàng hóa","ok");
  }
  S.khoEdit=null;S._khoHang=null;viewKho($("#main"));
}

/* --- Nhập / Xuất --- */
async function khoNhapXuat(host){
  const canDo=can("kho","THAO_TAC");
  if(!canDo){host.innerHTML=`<div class="perm-denied">Vai trò ${S.role} chỉ được xem — không thể lập phiếu nhập/xuất.</div>`;return;}
  const list=await _khoHangHoa();
  if(!list.length){host.innerHTML=`<div class="panel"><div class="panel-b" style="color:var(--muted)">Chưa có hàng hóa. Hãy thêm ở tab Tồn kho trước.</div></div>`;return;}
  if(!S.khoLines||!S.khoLines.length)S.khoLines=[{hh:String(list[0].id),sl:""}];
  if(!S.khoLoaiPhieu)S.khoLoaiPhieu="NHAP";
  const lineRows=S.khoLines.map((ln,i)=>`<div class="formrow" style="padding-top:0">
    <div class="f" style="flex:3"><label>${i===0?'Hàng hóa':''}</label>
      <select onchange="khoLine(${i},'hh',this.value)">${list.map(h=>`<option value="${h.id}" ${String(h.id)===ln.hh?'selected':''}>${h.ma?h.ma+' — ':''}${h.ten}</option>`).join('')}</select></div>
    <div class="f"><label>${i===0?'Số lượng':''}</label><input type="number" min="0" step="any" value="${ln.sl}" onchange="khoLine(${i},'sl',this.value)" placeholder="0"></div>
    <div class="f" style="flex:0 0 auto;align-self:flex-end"><button class="btn-sm ghost" onclick="khoDelLine(${i})" ${S.khoLines.length<=1?'disabled':''}>✕</button></div>
  </div>`).join('');
  host.innerHTML=`
    <div class="panel"><div class="panel-h"><h3>Lập phiếu nhập / xuất kho</h3></div><div class="panel-b">
      <div class="formrow">
        <div class="f"><label>Loại phiếu</label><select id="nx_loai" onchange="S.khoLoaiPhieu=this.value">
          <option value="NHAP" ${S.khoLoaiPhieu==='NHAP'?'selected':''}>Nhập kho</option>
          <option value="XUAT" ${S.khoLoaiPhieu==='XUAT'?'selected':''}>Xuất kho</option></select></div>
        <div class="f" style="flex:2"><label>Số phiếu (bỏ trống để tự sinh)</label><input id="nx_so" placeholder="tự sinh theo ngày"></div>
      </div>
      ${lineRows}
      <div style="margin:8px 0"><button class="btn-sm ghost" onclick="khoAddLine()">+ Thêm dòng</button></div>
      <button class="btn-sm" onclick="khoLapPhieu()">Lập phiếu</button>
      <p style="color:var(--muted);font-size:12px;margin-top:8px">Xuất kho xuống dưới tồn tối thiểu sẽ <b>tự sinh đề xuất mua</b> tới ngưỡng tồn max (xem tab Đề xuất mua hàng).</p>
    </div></div>`;
}
function khoLine(i,k,v){if(S.khoLines&&S.khoLines[i])S.khoLines[i][k]=v;}
function khoAddLine(){const list=S._khoHang||[];S.khoLines.push({hh:list[0]?String(list[0].id):"",sl:""});khoNhapXuat($("#khoBody"));}
function khoDelLine(i){S.khoLines.splice(i,1);khoNhapXuat($("#khoBody"));}
async function khoLapPhieu(){
  const loai=gv("nx_loai")||S.khoLoaiPhieu||"NHAP", so=gv("nx_so")||null;
  const ct=S.khoLines.filter(l=>l.hh&&Number(l.sl)>0).map(l=>({hang_hoa_id:Number(l.hh),so_luong:Number(l.sl)}));
  if(!ct.length){toast("Thêm ít nhất 1 dòng có số lượng > 0","err");return;}
  if(S.mode!=="live"){
    ct.forEach(d=>{const h=(DEMO.hang_hoa||[]).find(x=>x.id===d.hang_hoa_id);if(h){h.so_luong=Number(h.so_luong)+(loai==="NHAP"?d.so_luong:-d.so_luong);}});
    (DEMO.phieu_kho=DEMO.phieu_kho||[]).unshift({id:Date.now(),so:so||`${loai}-demo-${(DEMO.phieu_kho||[]).length+1}`,loai,ngay:new Date().toISOString().slice(0,10),
      chi_tiet:ct.map(d=>{const h=(DEMO.hang_hoa||[]).find(x=>x.id===d.hang_hoa_id)||{};return {hang_hoa_id:d.hang_hoa_id,ma:h.ma,ten:h.ten,don_vi:h.don_vi,so_luong:d.so_luong};})});
    S.khoLines=null;S._khoHang=null;toast(`Đã lập phiếu ${loai} (demo)`,"ok");S.khoTab="phieu";viewKho($("#main"));return;
  }
  try{const r=await api("/kho/phieu",{method:'POST',body:JSON.stringify({loai,so,chi_tiet:ct})});
    S.khoLines=null;S._khoHang=null;toast(`Đã lập phiếu ${r.so}`,"ok");S.khoTab="phieu";viewKho($("#main"));
  }catch(e){toast(e.detail||e.message,"err");}
}

/* --- Phiếu kho (lịch sử) --- */
async function khoPhieu(host){
  if(S.khoSel) return khoPhieuDetail(host,S.khoSel);
  let list;
  if(S.mode==="live"){ try{list=await api("/kho/phieu");}catch(e){toast(e.detail||e.message,"err");list=[];} }
  else list=(DEMO.phieu_kho||[]);
  const rows=list.map(p=>`<tr><td><b>${p.so||('#'+p.id)}</b></td>
    <td><span class="badge ${p.loai==='NHAP'?'b-ok':'b-cho'}">${p.loai==='NHAP'?'Nhập':'Xuất'}</span></td>
    <td>${p.ngay||''}</td><td><button class="btn-sm ghost" onclick="khoOpenPhieu(${p.id})">Chi tiết</button></td></tr>`).join('')
    ||`<tr><td colspan="4" style="color:var(--muted)">Chưa có phiếu kho</td></tr>`;
  host.innerHTML=`<div class="panel"><div class="panel-h"><h3>Lịch sử phiếu nhập / xuất</h3></div>
    <div class="panel-b"><table><thead><tr><th>Số phiếu</th><th>Loại</th><th>Ngày</th><th></th></tr></thead>
      <tbody>${rows}</tbody></table></div></div>`;
}
function khoOpenPhieu(id){S.khoSel=id;viewKho($("#main"));}
function khoBackPhieu(){S.khoSel=null;viewKho($("#main"));}
async function khoPhieuDetail(host,id){
  let p;
  if(S.mode==="live"){ try{p=await api(`/kho/phieu/${id}`);}catch(e){host.innerHTML=`<div class="perm-denied">${e.detail||e.message}</div>`;return;} }
  else p=(DEMO.phieu_kho||[]).find(x=>x.id===id);
  if(!p){host.innerHTML='<div class="perm-denied">Không tìm thấy phiếu</div>';return;}
  const rows=(p.chi_tiet||[]).map(d=>`<tr><td><b>${d.ma||'—'}</b></td><td>${d.ten||('HH #'+d.hang_hoa_id)}</td>
    <td class="num">${Number(d.so_luong).toLocaleString('vi-VN')} ${d.don_vi||''}</td></tr>`).join('');
  host.innerHTML=`<button class="btn-sm ghost" onclick="khoBackPhieu()">← Danh sách phiếu</button>
    <div class="panel" style="margin-top:14px"><div class="panel-h"><h3>Phiếu ${p.so||('#'+p.id)} · ${p.loai==='NHAP'?'Nhập kho':'Xuất kho'} · ${p.ngay||''}</h3></div>
      <div class="panel-b"><table><thead><tr><th>Mã</th><th>Tên hàng</th><th class="num">Số lượng</th></tr></thead><tbody>${rows||`<tr><td colspan="3" style="color:var(--muted)">Không có dòng</td></tr>`}</tbody></table></div></div>`;
}

/* --- Kiểm kê / điều chỉnh tồn --- */
async function khoKiemKe(host){
  const canDC=can("kho","DUYET");
  const list=await _khoHangHoa();
  const opts=list.map(h=>`<option value="${h.id}" data-sl="${h.so_luong}">${h.ma?h.ma+' — ':''}${h.ten} (tồn ${Number(h.so_luong).toLocaleString('vi-VN')} ${h.don_vi||''})</option>`).join('');
  host.innerHTML=`
    <div class="panel"><div class="panel-h"><h3>Kiểm kê — điều chỉnh tồn thực tế</h3>${canDC?'':'<div class="spacer"></div><span class="badge b-tc">Cần quyền Duyệt</span>'}</div>
    <div class="panel-b">
      ${canDC?`<div class="formrow">
        <div class="f" style="flex:2"><label>Hàng hóa</label><select id="kk_hh" onchange="khoKKSync()">${opts}</select></div>
        <div class="f"><label>Tồn hệ thống</label><input id="kk_cu" disabled></div>
        <div class="f"><label>Tồn thực tế (mới)</label><input id="kk_moi" type="number" min="0" step="any"></div>
        <div class="f" style="flex:2"><label>Lý do</label><input id="kk_ly" placeholder="VD: Kiểm kê quý 2, hao hụt…"></div>
      </div>
      <button class="btn-sm" onclick="khoDieuChinh()">Ghi điều chỉnh</button>
      <p style="color:var(--muted);font-size:12px;margin-top:8px">Điều chỉnh ghi vết audit (giá trị cũ → mới + lý do).</p>`
      :`<div class="perm-denied">Vai trò ${S.role} không có quyền Duyệt — không thể điều chỉnh tồn. Liên hệ Trưởng phòng/CEO.</div>`}
    </div></div>`;
  if(canDC)khoKKSync();
}
function khoKKSync(){const sel=document.getElementById('kk_hh');if(!sel)return;const o=sel.options[sel.selectedIndex];const cu=document.getElementById('kk_cu');if(cu)cu.value=o?o.getAttribute('data-sl'):'';}
async function khoDieuChinh(){
  const hh=gv("kk_hh"),moi=gv("kk_moi"),ly=gv("kk_ly");
  if(!hh){toast("Chọn hàng hóa","err");return;}
  if(moi===''){toast("Nhập tồn thực tế","err");return;}
  if(!ly){toast("Nhập lý do điều chỉnh","err");return;}
  if(S.mode!=="live"){const h=(DEMO.hang_hoa||[]).find(x=>x.id===Number(hh));if(h)h.so_luong=Number(moi);S._khoHang=null;toast("Đã điều chỉnh (demo)","ok");viewKho($("#main"));return;}
  try{const r=await api("/kho/ton-kho/dieu-chinh",{method:'POST',body:JSON.stringify({hang_hoa_id:Number(hh),so_luong_moi:Number(moi),ly_do:ly})});
    S._khoHang=null;toast(`Đã điều chỉnh: ${r.so_luong_cu} → ${r.so_luong_moi}`,"ok");viewKho($("#main"));
  }catch(e){toast(e.detail||e.message,"err");}
}

/* --- Cảnh báo tồn --- */
async function khoCanhBao(host){
  const list=await _khoHangHoa();
  const low=list.filter(h=>Number(h.so_luong)<Number(h.ton_min));
  const rows=low.map(h=>{const thieu=Number(h.ton_min)-Number(h.so_luong);const dx=(h.ton_max!=null?Number(h.ton_max):Number(h.ton_min))-Number(h.so_luong);
    return `<tr><td><b>${h.ma||'—'}</b></td><td>${h.ten}</td>
    <td class="num">${Number(h.so_luong).toLocaleString('vi-VN')} ${h.don_vi||''}</td>
    <td class="num">${Number(h.ton_min).toLocaleString('vi-VN')}</td>
    <td class="num" style="color:var(--red)">${thieu.toLocaleString('vi-VN')}</td>
    <td class="num">${dx>0?dx.toLocaleString('vi-VN'):'—'}</td></tr>`;}).join('')
    ||`<tr><td colspan="6" style="color:var(--muted)">Không có hàng dưới mức tồn tối thiểu 👍</td></tr>`;
  host.innerHTML=`<div class="cards"><div class="stat ${low.length?'':'accent'}"><div class="k">Hàng dưới mức tồn tối thiểu</div>
    <div class="v">${low.length}</div><div class="d" style="color:var(--amber)">Cần lập kế hoạch mua</div></div></div>
    <div class="panel"><div class="panel-h"><h3>Danh sách cảnh báo tồn</h3></div>
      <div class="panel-b"><table><thead><tr><th>Mã</th><th>Tên</th><th class="num">Tồn</th><th class="num">Min</th><th class="num">Thiếu</th><th class="num">Mua đến max</th></tr></thead>
        <tbody>${rows}</tbody></table></div>
      <div class="panel-b" style="color:var(--muted);font-size:12.5px;padding-top:0">Khi xuất kho làm tồn xuống dưới min, hệ thống tự tạo <b>đề xuất mua</b> tới ngưỡng tồn max — xử lý ở tab <b>Đề xuất mua hàng</b>.</div></div>`;
}

/* ---------- Bán hàng (3 tab) ---------- */
const gv=id=>{const e=document.getElementById(id);return e?(e.value||'').trim():'';};
const kb=n=>n?Math.max(1,Math.round(n/1024)).toLocaleString('vi-VN')+" KB":'—';
async function viewBanHang(m){
  if(!S.bhTab)S.bhTab="khach_hang";
  m.innerHTML=head("Bán hàng","Báo giá · Đơn hàng &amp; PO/Hợp đồng · Email chào hàng");
  const tabs=[["khach_hang","Khách hàng"],["bao_gia","Báo giá"],["don_hang","Đơn hàng & PO/Hợp đồng"],["email","Email chào hàng"],["phan_hoi","Hộp thư phản hồi"],["cong_viec","Công việc (SLA)"],["co_hoi","Cơ hội"],["tong_quan","Tổng quan"]];
  m.innerHTML+=`<div class="tabs">${tabs.map(([k,l])=>`<button class="${S.bhTab===k?'active':''}" onclick="bhSwitch('${k}')">${l}</button>`).join('')}</div><div id="bhBody"></div>`;
  const host=$("#bhBody");
  if(S.bhTab==="khach_hang") await bhKhachHang(host);
  else if(S.bhTab==="bao_gia") await bhBaoGia(host);
  else if(S.bhTab==="don_hang") await bhDonHang(host);
  else if(S.bhTab==="phan_hoi") await bhPhanHoi(host);
  else if(S.bhTab==="cong_viec") await bhCongViec(host);
  else if(S.bhTab==="co_hoi") await bhCoHoi(host);
  else if(S.bhTab==="tong_quan") await bhTongQuan(host);
  else await bhEmail(host);
}
function bhSwitch(t){S.bhTab=t;S.khSel=null;cdSelKH=[];viewBanHang($("#main"));}

/* --- Tab Báo giá --- */
async function bhBaoGia(host){
  let rows=DEMO.bao_gia;
  if(S.mode==="live"){ try{const r=await api("/ban-hang/bao-gia");rows=r.map(b=>({id:b.id,so:b.so,khach:"KH #"+b.khach_hang_id,tong_tien:Number(b.tong_tien),trang_thai:b.trang_thai}));}catch(e){toast(e.detail||e.message,"err");} }
  const canApprove = can("ban_hang","XEM") && HANMUC.bao_gia[S.role]!==undefined;
  const body=rows.map(b=>{
    const st=b.trang_thai;
    const badge=st==="DA_DUYET"?'<span class="badge b-ok">Đã duyệt</span>':
                st==="TU_CHOI"?'<span class="badge b-tc">Từ chối</span>':'<span class="badge b-cho">Chờ duyệt</span>';
    const btn=(st==="CHO_DUYET")
      ? (canApprove?`<button class="btn-sm" onclick="duyetBG(${b.id},${b.tong_tien})">Duyệt</button>`
                   :`<button class="btn-sm" disabled title="Không có quyền duyệt">Duyệt</button>`)
      : '—';
    return `<tr><td><b>${b.so}</b></td><td>${b.khach}</td><td class="num">${vnd(b.tong_tien)}</td><td>${badge}</td><td>${btn}</td></tr>`;
  }).join('');
  const gateNote = HANMUC.bao_gia[S.role]!==undefined
    ? `Hạn mức duyệt của bạn: ${HANMUC.bao_gia[S.role]===null?'không giới hạn':vnd(HANMUC.bao_gia[S.role])}.`
    : (can("ban_hang","THAO_TAC")?"Bạn soạn được báo giá nhưng không có quyền duyệt.":"Bạn chỉ được xem.");
  host.innerHTML=`<div class="panel"><div class="panel-h"><h3>Báo giá</h3></div>
    <div class="note">${gateNote}</div>
    <div class="panel-b"><table><thead><tr><th>Số</th><th>Khách hàng</th><th class="num">Giá trị</th><th>Trạng thái</th><th>Hành động</th></tr></thead>
    <tbody>${body}</tbody></table></div></div>`;
}
async function duyetBG(id,amount){
  if(S.mode==="live"){ try{await api(`/ban-hang/bao-gia/${id}/duyet`,{method:'POST'});
    toast("Đã duyệt báo giá","ok");viewBanHang($("#main"));}catch(e){toast(e.status===403?("Bị chặn: "+(e.detail||"vượt hạn mức")):(e.detail||e.message),"err");} return; }
  const cap=HANMUC.bao_gia[S.role];
  if(cap===undefined){toast("Vai trò "+S.role+" không có quyền duyệt báo giá","err");return;}
  if(cap!==null && amount>cap){toast(`Bị chặn: ${vnd(amount)} vượt hạn mức ${vnd(cap)} của ${S.role} — cần trình cấp cao hơn`,"err");return;}
  const b=DEMO.bao_gia.find(x=>x.id===id); if(b)b.trang_thai="DA_DUYET";
  toast("Đã duyệt báo giá (demo)","ok"); viewBanHang($("#main"));
}

/* --- Tab Đơn hàng & tệp PO/Hợp đồng --- */
async function bhDonHang(host){
  let orders=DEMO.don_hang;
  if(S.mode==="live"){ try{ const r=await api("/ban-hang/don-hang");
    orders=await Promise.all(r.map(async o=>{ let tep=[],pnl=null;
      try{tep=await api(`/ban-hang/don-hang/${o.id}/tep`);}catch{}
      try{pnl=await api(`/ban-hang/don-hang/${o.id}/lai-lo`);}catch{}
      return {id:o.id,so:o.so,khach:"KH #"+o.khach_hang_id,tong_tien:Number(o.tong_tien),trang_thai:o.trang_thai,tep,pnl};}));
    }catch(e){toast(e.detail||e.message,"err");} }
  else { orders=(DEMO.don_hang||[]).map(o=>{
      const posAll=(DEMO.don_mua||[]).filter(p=>p.don_hang_id===o.id && p.trang_thai!=="TU_CHOI");
      const camket=posAll.reduce((s,p)=>s+(p.tong_tien||0),0);
      const thuc=posAll.reduce((s,p)=>s+((p.trang_thai_nhan==="DU"?1:p.trang_thai_nhan==="MOT_PHAN"?0.5:0)*(p.tong_tien||0)),0);
      const dt=o.tong_tien||0; const rate=v=>dt?Math.round((dt-v)/dt*1000)/10:0;
      return {...o,pnl:{doanh_thu:dt,gia_von_thuc:thuc,gia_von_cam_ket:camket,lai_lo_thuc:dt-thuc,
        lai_lo_dukien:dt-camket,ty_suat_thuc:rate(thuc),ty_suat_dukien:rate(camket),so_po:posAll.length}};
    }); }
  const canUp=can("ban_hang","THAO_TAC");
  const cards=orders.map(o=>{
    const ma=o.so||('DH-'+o.id);
    const tepRows = (o.tep&&o.tep.length)
      ? o.tep.map(t=>`<tr><td><span class="badge ${t.loai==='PO'?'b-info':t.loai==='HOP_DONG'?'b-ok':'b-cho'}">${t.loai}</span></td>
          <td><b>${ma}</b></td>
          <td>${t.ten_file}</td><td class="num">${kb(t.kich_thuoc)}</td>
          <td><button class="btn-sm ghost" onclick="taiTep(${t.id},'${(t.ten_file||'').replace(/'/g,'')}')">Tải về</button></td></tr>`).join('')
      : `<tr><td colspan="5" style="color:var(--muted);padding:10px 18px">Chưa có tệp đính kèm.</td></tr>`;
    const p=o.pnl;
    const pnlBar = p ? `<div style="display:flex;flex-wrap:wrap;gap:16px;padding:9px 18px;border-bottom:1px solid #eef3f6;font-size:13px">
        <span>Doanh thu: <b>${vnd(p.doanh_thu)}</b></span>
        <span>Giá vốn: thực <b>${vnd(p.gia_von_thuc)}</b> / cam kết <b>${vnd(p.gia_von_cam_ket)}</b>${p.so_po?` <span style="color:var(--muted)">(${p.so_po} PO mua)</span>`:''}</span>
        <span>Lãi/Lỗ thực: <b style="color:${p.lai_lo_thuc>=0?'#16a34a':'#dc2626'}">${vnd(p.lai_lo_thuc)}${p.doanh_thu?` · ${p.ty_suat_thuc}%`:''}</b></span>
        <span style="color:var(--muted)">dự kiến ${vnd(p.lai_lo_dukien)}${p.doanh_thu?` · ${p.ty_suat_dukien}%`:''}</span></div>` : '';
    const upBox = canUp ? `<div class="formrow" style="border-top:1px solid #eef3f6">
        <div class="f"><label>Loại tệp</label><select id="loai_${o.id}"><option value="PO">PO khách hàng</option><option value="HOP_DONG">Hợp đồng</option><option value="KHAC">Khác</option></select></div>
        <div class="f" style="flex:2"><label>Chọn tệp</label><input type="file" id="file_${o.id}"></div>
        <button class="btn-sm" onclick="uploadTep(${o.id})">Tải lên</button></div>`
      : `<div class="perm-denied">Vai trò ${S.role} chỉ được xem — không tải tệp lên.</div>`;
    return `<div class="panel">
      <div class="panel-h"><h3>${ma} · ${o.khach}</h3><div class="spacer"></div>
        <span class="num" style="font-weight:700">${vnd(o.tong_tien)}</span>
        <span class="badge ${o.trang_thai==='DA_XUAT'?'b-ok':'b-info'}" style="margin-left:10px">${o.trang_thai}</span></div>
      ${pnlBar}
      <div class="panel-b"><table><thead><tr><th>Loại</th><th>Mã Bán hàng</th><th>Tên tệp</th><th class="num">Cỡ</th><th>Tải về</th></tr></thead>
        <tbody>${tepRows}</tbody></table></div>${upBox}</div>`;
  }).join('');
  host.innerHTML = `<div class="note" style="padding:0 0 12px">Mỗi đơn hiển thị <b>Mã Bán hàng</b> làm khóa liên kết sang Mua hàng, kèm <b>giá vốn</b> (tổng PO mua liên kết) và <b>lãi/lỗ</b>. Đính kèm PO khách & hợp đồng ngay trên đơn.</div>${cards||'<div class="panel"><div class="empty">Chưa có đơn hàng.</div></div>'}`;
}
async function uploadTep(dhId){
  const inp=document.getElementById('file_'+dhId), f=inp&&inp.files[0];
  if(!f){toast("Hãy chọn tệp","err");return;}
  const loai=gv('loai_'+dhId)||'KHAC';
  if(S.mode==="live"){ const fd=new FormData(); fd.append('file',f); fd.append('loai',loai);
    try{ await apiUpload(`/ban-hang/don-hang/${dhId}/tep`,fd); toast("Đã tải lên: "+f.name,"ok"); viewBanHang($("#main")); }
    catch(e){toast(e.detail||e.message,"err");} return; }
  const o=DEMO.don_hang.find(x=>x.id===dhId);
  if(o)o.tep.push({id:Date.now(),loai,ten_file:f.name,kich_thuoc:f.size});
  toast("Đã đính kèm (demo): "+f.name,"ok"); viewBanHang($("#main"));
}
async function taiTep(id,name){
  if(S.mode!=="live"){toast("Demo: tải tệp “"+name+"”","ok");return;}
  try{ const h={}; if(S.token)h['Authorization']='Bearer '+S.token;
    const r=await fetch(S.api+`/ban-hang/tep/${id}/tai-ve`,{headers:h}); if(!r.ok)throw new Error('Không tải được');
    const blob=await r.blob(), url=URL.createObjectURL(blob), a=document.createElement('a');
    a.href=url; a.download=name; a.click(); URL.revokeObjectURL(url);
  }catch(e){toast(e.message,"err");}
}

/* --- Tab Email chào hàng (soạn → duyệt → gửi) --- */
async function bhEmail(host){
  const FROM="sv-sales@watersolutions.company";
  let cds=DEMO.chien_dich;
  if(S.mode==="live"){ try{ const raw=await api("/ban-hang/chien-dich");
    cds=await Promise.all(raw.map(async c=>{ let tep=[]; try{tep=await api(`/ban-hang/chien-dich/${c.id}/tep`);}catch{} return {...c,tep}; }));
    }catch(e){toast(e.detail||e.message,"err");} }
  const canCompose=can("ban_hang","THAO_TAC"), canApprove=can("ban_hang","DUYET");
  const abcLabel=a=>a?("Hạng "+a):"Tất cả khách hàng";

  const composer = canCompose ? `<div class="panel"><div class="panel-h"><h3>Soạn chiến dịch chào hàng</h3></div>
      <div class="note" style="padding-bottom:0">Gửi từ: <b>${FROM}</b></div>
      <div class="formrow"><div class="f" style="flex:2"><label>Tên chiến dịch</label><input id="cd_ten" placeholder="VD: Chào hàng giải pháp MBR Q3"></div>
        <div class="f"><label>Gửi tới (theo hạng)</label><select id="cd_abc"><option value="">Tất cả khách hàng</option><option value="A">Chỉ hạng A</option><option value="B">Chỉ hạng B</option><option value="C">Chỉ hạng C</option></select></div></div>
      <div class="formrow" style="padding-top:0"><div class="f" style="flex:1"><label>Hoặc gõ tên để tìm & chọn khách cụ thể</label>
        <div class="ac-box"><input id="cd_kh_search" autocomplete="off" placeholder="Bấm để xem danh sách hoặc gõ tên khách..." oninput="searchKH(this.value)" onfocus="searchKH(this.value)" onblur="setTimeout(hideKHResults,160)">
          <div id="cd_kh_results" class="ac-results"></div></div>
        <div id="cd_kh_chips" class="chips"></div>
        <div class="note" style="padding:6px 0 0">Chọn khách cụ thể sẽ chỉ gửi cho những khách này (bỏ qua lọc hạng).</div></div></div>
      <div class="formrow" style="padding-top:0"><div class="f" style="flex:1"><label>Tiêu đề email</label><input id="cd_td" placeholder="Giải pháp xử lý nước cho {ten_kh}"></div></div>
      <div class="formrow" style="padding-top:0"><div class="f" style="flex:1"><label>Nội dung (dùng {ten_kh} để chèn tên KH)</label>
        <textarea id="cd_nd" rows="4" style="width:100%;padding:10px 12px;border:1px solid var(--line);border-radius:9px;font-family:inherit;font-size:14px" placeholder="Kính gửi {ten_kh}, SVWS xin giới thiệu..."></textarea></div></div>
      <div class="formrow" style="padding-top:0"><button class="btn-sm" onclick="taoCD()">Tạo (chờ duyệt)</button>
        <span class="note" style="padding:0">Tạo xong, đính kèm tệp ở thẻ chiến dịch bên dưới rồi trình duyệt.</span></div></div>`
    : `<div class="perm-denied">Vai trò ${S.role} chỉ được xem chiến dịch.</div>`;

  const cards = cds.map(c=>{
    const st=c.trang_thai;
    const badge={CHO_DUYET:'<span class="badge b-cho">Chờ duyệt</span>',DA_DUYET:'<span class="badge b-info">Đã duyệt</span>',
      DA_GUI:'<span class="badge b-ok">Đã gửi</span>',TU_CHOI:'<span class="badge b-tc">Từ chối</span>'}[st]||st;
    let act='';
    if(st==="CHO_DUYET") act = canApprove?`<button class="btn-sm" onclick="duyetCD(${c.id})">Duyệt nội dung</button>`
                                          :`<button class="btn-sm" disabled title="Cần TP_KD/CEO">Duyệt nội dung</button>`;
    else if(st==="DA_DUYET") act = canCompose?`<button class="btn-sm" onclick="guiCD(${c.id})">Gửi</button>`:'';
    else if(st==="DA_GUI") act = `<button class="btn-sm ghost" onclick="xemKetQuaCD(${c.id})">Kết quả</button>`;
    const tep=c.tep||[];
    const tepRows = tep.length
      ? tep.map(t=>`<tr><td>${t.ten_file}</td><td class="num">${kb(t.kich_thuoc)}</td>
          <td><button class="btn-sm ghost" onclick="taiTep(${t.id},'${(t.ten_file||'').replace(/'/g,'')}')">Tải về</button></td></tr>`).join('')
      : `<tr><td colspan="3" style="color:var(--muted);padding:10px 18px">Chưa có tệp đính kèm.</td></tr>`;
    const upBox = (canCompose && st!=="DA_GUI") ? `<div class="formrow" style="border-top:1px solid #eef3f6">
        <div class="f" style="flex:2"><label>Đính kèm tệp gửi kèm email (brochure, catalogue...)</label><input type="file" id="cdfile_${c.id}"></div>
        <button class="btn-sm" onclick="uploadTepCD(${c.id})">Đính kèm</button></div>` : '';
    return `<div class="panel">
      <div class="panel-h"><h3>${c.ten}</h3><div class="spacer"></div>${badge}</div>
      <div class="note" style="padding-bottom:6px">Tiêu đề: ${c.tieu_de}<br>Gửi tới: ${cdTarget(c)} · Gửi từ: <b>${FROM}</b></div>
      <div class="panel-b"><table><thead><tr><th>Tệp đính kèm</th><th class="num">Cỡ</th><th>Tải về</th></tr></thead>
        <tbody>${tepRows}</tbody></table></div>${upBox}
      ${act?`<div class="formrow" style="border-top:1px solid #eef3f6">${act}</div>`:''}</div>`;
  }).join('');

  host.innerHTML = composer + (cards || '<div class="panel"><div class="empty">Chưa có chiến dịch.</div></div>');
  renderChips();
}
async function uploadTepCD(cdId){
  const inp=document.getElementById('cdfile_'+cdId), f=inp&&inp.files[0];
  if(!f){toast("Hãy chọn tệp","err");return;}
  if(S.mode==="live"){ const fd=new FormData(); fd.append('file',f);
    try{ await apiUpload(`/ban-hang/chien-dich/${cdId}/tep`,fd); toast("Đã đính kèm: "+f.name,"ok"); viewBanHang($("#main")); }
    catch(e){toast(e.detail||e.message,"err");} return; }
  const c=DEMO.chien_dich.find(x=>x.id===cdId);
  if(c){ c.tep=c.tep||[]; c.tep.push({id:Date.now(),ten_file:f.name,kich_thuoc:f.size}); }
  toast("Đã đính kèm (demo): "+f.name,"ok"); viewBanHang($("#main"));
}
let cdSelKH=[]; let _khTimer=null;
function cdTarget(c){
  const live=c.khach_hang_ids?(''+c.khach_hang_ids).split(',').filter(Boolean).length:0;
  const demo=(c.khach_ids&&c.khach_ids.length)||0;
  const n=live||demo;
  if(n) return `${n} khách đã chọn`;
  return c.bo_loc_abc?("Hạng "+c.bo_loc_abc):"Tất cả khách hàng";
}
async function searchKH(q){
  const box=document.getElementById('cd_kh_results'); if(!box)return;
  q=(q||'').trim();
  if(S.mode==="live"){ clearTimeout(_khTimer); _khTimer=setTimeout(async()=>{
    try{const list=await api(`/ban-hang/khach-hang${q?`?q=${encodeURIComponent(q)}`:''}`); renderKHResults(list,q);}catch{} },220); return; }
  renderKHResults((DEMO.khach||[]).filter(k=>!q||k.ten.toLowerCase().includes(q.toLowerCase())), q);
}
function hideKHResults(){ const b=document.getElementById('cd_kh_results'); if(b){b.classList.remove('show');} }
function renderKHResults(list,q){
  const box=document.getElementById('cd_kh_results'); if(!box)return;
  const sel=new Set(cdSelKH.map(x=>x.id));
  const items=list.filter(k=>!sel.has(k.id)).slice(0,8);
  box.innerHTML = items.length
    ? items.map(k=>`<div data-id="${k.id}" data-ten="${(k.ten||'').replace(/"/g,'&quot;')}" onclick="addKHEl(this)">${k.ten}${k.email?` <span class="muted">· ${k.email}</span>`:''}</div>`).join('')
    : `<div class="muted">Không có khách khớp “${q}”</div>`;
  box.classList.add('show');
}
function addKHEl(el){ addKH(parseInt(el.dataset.id), el.dataset.ten); }
function addKH(id,ten){ if(!cdSelKH.find(x=>x.id===id)) cdSelKH.push({id,ten});
  const s=document.getElementById('cd_kh_search'); if(s)s.value='';
  const box=document.getElementById('cd_kh_results'); if(box){box.classList.remove('show');box.innerHTML='';}
  renderChips(); }
function removeKH(id){ cdSelKH=cdSelKH.filter(x=>x.id!==id); renderChips(); }
function renderChips(){ const c=document.getElementById('cd_kh_chips'); if(!c)return;
  c.innerHTML=cdSelKH.map(k=>`<span class="chip">${k.ten}<button onclick="removeKH(${k.id})" title="Bỏ chọn">×</button></span>`).join(''); }
async function taoCD(){
  const ten=gv('cd_ten'),tieu_de=gv('cd_td'),noi_dung=gv('cd_nd'),abc=gv('cd_abc')||null;
  if(!ten||!tieu_de||!noi_dung){toast("Nhập đủ tên, tiêu đề và nội dung","err");return;}
  const ids=cdSelKH.map(x=>x.id), tens=cdSelKH.map(x=>x.ten);
  const payload={ten,tieu_de,noi_dung,bo_loc_abc: ids.length?null:abc, khach_hang_ids: ids.length?ids:null};
  if(S.mode==="live"){ try{await api("/ban-hang/chien-dich",{method:'POST',body:JSON.stringify(payload)});
    cdSelKH=[]; toast("Đã tạo chiến dịch (chờ duyệt)","ok");viewBanHang($("#main"));}catch(e){toast(e.detail||e.message,"err");} return; }
  DEMO.chien_dich.unshift({id:Date.now(),ten,tieu_de,noi_dung,bo_loc_abc:payload.bo_loc_abc,khach_ids:ids,khach_ten:tens,trang_thai:"CHO_DUYET",tep:[]});
  cdSelKH=[]; toast("Đã tạo (demo) — chờ duyệt","ok"); viewBanHang($("#main"));
}
async function duyetCD(id){
  if(!can("ban_hang","DUYET")){toast("Bạn không có quyền duyệt nội dung (cần TP_KD/CEO)","err");return;}
  if(S.mode==="live"){ try{await api(`/ban-hang/chien-dich/${id}/duyet`,{method:'POST'});
    toast("Đã duyệt nội dung","ok");viewBanHang($("#main"));}catch(e){toast(e.status===403?"Bị chặn: không có quyền duyệt":(e.detail||e.message),"err");} return; }
  const c=DEMO.chien_dich.find(x=>x.id===id); if(c)c.trang_thai="DA_DUYET";
  toast("Đã duyệt nội dung (demo)","ok"); viewBanHang($("#main"));
}
async function guiCD(id){
  if(S.mode==="live"){ try{const r=await api(`/ban-hang/chien-dich/${id}/gui`,{method:'POST'});
    toast(`Đã gửi — OK ${r.ket_qua.GUI_OK||0}, bỏ qua ${r.ket_qua.BO_QUA||0}`,"ok");viewBanHang($("#main"));}
    catch(e){toast(e.status===400?"Bị chặn: nội dung chưa được duyệt":(e.detail||e.message),"err");} return; }
  const c=DEMO.chien_dich.find(x=>x.id===id);
  if(!c||c.trang_thai!=="DA_DUYET"){toast("Bị chặn: nội dung chưa được duyệt","err");return;}
  const tg=(c.khach_ids&&c.khach_ids.length)
    ? (DEMO.khach||[]).filter(k=>c.khach_ids.includes(k.id))
    : (DEMO.khach||[]).filter(k=>!c.bo_loc_abc||k.phan_loai_abc===c.bo_loc_abc);
  let ok=0,bo=0; tg.forEach(k=>k.email?ok++:bo++);
  c.trang_thai="DA_GUI"; c.ket_qua={GUI_OK:ok,BO_QUA:bo};
  toast(`Đã gửi (demo): ${ok} email · bỏ qua ${bo} KH thiếu email`,"ok"); viewBanHang($("#main"));
}
async function xemKetQuaCD(id){
  if(S.mode==="live"){ try{const r=await api(`/ban-hang/chien-dich/${id}/ket-qua`);
    const ok=r.chi_tiet.filter(x=>x.trang_thai==='GUI_OK').length, bo=r.chi_tiet.filter(x=>x.trang_thai==='BO_QUA').length;
    toast(`Kết quả: ${r.so_email} email — gửi OK ${ok}, bỏ qua ${bo}`,"ok");}catch(e){toast(e.detail||e.message,"err");} return; }
  const c=DEMO.chien_dich.find(x=>x.id===id), k=c&&c.ket_qua||{GUI_OK:0,BO_QUA:0};
  toast(`Kết quả (demo): gửi OK ${k.GUI_OK}, bỏ qua ${k.BO_QUA}`,"ok");
}

/* --- Tab Khách hàng: hồ sơ · gửi email QUA HỆ THỐNG · nhật ký liên lạc --- */
async function bhKhachHang(host){
  if(S.khSel) return bhKhachHangDetail(host, S.khSel);
  let list=DEMO.khach;
  if(S.mode==="live"){ try{const r=await api("/ban-hang/khach-hang");
    list=r.map(k=>({id:k.id,ma:k.ma,ten:k.ten,email:k.email,phan_loai_abc:k.phan_loai_abc}));}catch(e){toast(e.detail||e.message,"err");} }
  const rows=list.map(k=>`<tr>
    <td><b>${k.ma||'—'}</b></td><td>${k.ten}</td>
    <td>${k.email?k.email:'<span style="color:var(--amber)">chưa có email</span>'}</td>
    <td>${k.phan_loai_abc?`<span class="badge b-info">Hạng ${k.phan_loai_abc}</span>`:'—'}</td>
    <td><button class="btn-sm ghost" onclick="openKH(${k.id})">Hồ sơ & liên lạc</button></td></tr>`).join('');
  host.innerHTML=`<div class="note" style="padding:0 0 12px">Mọi khách hàng, trao đổi và tệp đều nằm trong hệ thống. Email gửi từ địa chỉ công ty <b>sv-sales@watersolutions.company</b> và được ghi nhật ký — không dùng mail cá nhân.</div>
    <div class="panel"><div class="panel-h"><h3>Danh sách khách hàng</h3></div>
    <div class="panel-b"><table><thead><tr><th>Mã</th><th>Tên</th><th>Email</th><th>Hạng</th><th></th></tr></thead>
    <tbody>${rows||'<tr><td colspan="5" class="empty">Chưa có khách hàng.</td></tr>'}</tbody></table></div></div>`;
}
function openKH(id){S.bhTab="khach_hang";S.khSel=id;viewBanHang($("#main"));}
function backKH(){S.khSel=null;viewBanHang($("#main"));}

async function bhKhachHangDetail(host, khId){
  const FROM="sv-sales@watersolutions.company";
  let kh=(DEMO.khach||[]).find(x=>x.id===khId)||{id:khId,ten:"KH #"+khId,email:"",ma:""};
  let tl=(DEMO.lien_lac&&DEMO.lien_lac[khId])||[];
  if(S.mode==="live"){
    try{const all=await api("/ban-hang/khach-hang"); const f=all.find(x=>x.id===khId); if(f)kh=f;}catch{}
    try{tl=await api(`/ban-hang/khach-hang/${khId}/lien-lac`);}catch(e){toast(e.detail||e.message,"err");}
  }
  const canOp=can("ban_hang","THAO_TAC");
  const draft=(S.draftReply&&S.draftReply.khId===khId)?S.draftReply:null;
  const unsub=!!kh.khong_nhan_email;
  const tlRows = tl.length ? tl.map(x=>{
    const badge={EMAIL:'b-info',GOI:'b-cho',GAP:'b-cho',GHI_CHU:'b-ok'}[x.kenh]||'b-info';
    const dir=x.huong==="DEN"?"← nhận":"→ gửi";
    return `<tr><td style="white-space:nowrap;color:var(--muted);font-size:12px">${(x.thoi_diem||'').toString().replace('T',' ').slice(0,16)}</td>
      <td><span class="badge ${badge}">${x.kenh}</span> <span style="color:var(--muted);font-size:11px">${dir}</span></td>
      <td>${x.tieu_de?`<b>${x.tieu_de}</b><br>`:''}${(x.noi_dung||'').slice(0,180)}${x.gui_tu?`<div style="color:var(--muted);font-size:11px">từ ${x.gui_tu}${x.trang_thai?' · '+x.trang_thai:''}</div>`:''}</td></tr>`;
  }).join('') : `<tr><td colspan="3" class="empty" style="padding:22px">Chưa có liên lạc nào.</td></tr>`;

  const sendPanel = canOp ? (kh.email ? `<div class="panel"><div class="panel-h"><h3>Gửi email qua hệ thống</h3>${draft?'<div class="spacer"></div><span class="badge b-info">Đã điền gợi ý AI</span>':''}</div>
      <div class="note" style="padding-bottom:0">Gửi từ <b>${FROM}</b> tới <b>${kh.email}</b> — tự ghi vào nhật ký.</div>
      <div class="formrow"><div class="f" style="flex:1"><label>Tiêu đề</label><input id="em_td" value="${draft?(draft.tieu_de||'').replace(/"/g,'&quot;'):''}" placeholder="VD: Báo giá hệ thống xử lý nước"></div></div>
      <div class="formrow" style="padding-top:0"><div class="f" style="flex:1"><label>Nội dung</label>
        <textarea id="em_nd" rows="4" style="width:100%;padding:10px 12px;border:1px solid var(--line);border-radius:9px;font-family:inherit;font-size:14px" placeholder="Kính gửi quý công ty...">${draft?draft.noi_dung:''}</textarea></div></div>
      <div class="formrow" style="padding-top:0"><button class="btn-sm" onclick="guiEmailKH(${khId})">Gửi qua hệ thống</button></div></div>`
    : `<div class="panel"><div class="panel-h"><h3>Gửi email qua hệ thống</h3></div>
        <div class="perm-denied">Khách hàng chưa có email — cập nhật email trong hồ sơ trước khi gửi.</div></div>`) : '';

  const logPanel = canOp ? `<div class="panel"><div class="panel-h"><h3>Ghi nhận liên lạc</h3></div>
      <div class="formrow"><div class="f"><label>Kênh</label><select id="ll_kenh"><option value="GOI">Cuộc gọi</option><option value="GAP">Gặp mặt</option><option value="GHI_CHU">Ghi chú</option></select></div>
        <div class="f" style="flex:2"><label>Nội dung</label><input id="ll_nd" placeholder="Tóm tắt trao đổi..."></div>
        <button class="btn-sm" onclick="ghiLienLac(${khId})">Lưu</button></div></div>` : '';

  host.innerHTML=`<div style="margin-bottom:12px"><button class="btn-sm ghost" onclick="backKH()">← Danh sách khách hàng</button></div>
    <div class="panel"><div class="panel-h"><h3>${kh.ten}</h3><div class="spacer"></div>
      ${unsub?`<span class="badge b-cho">Đã hủy nhận email marketing</span> `:''}${kh.phan_loai_abc?`<span class="badge b-info">Hạng ${kh.phan_loai_abc}</span>`:''}</div>
      <div class="note">Mã: ${kh.ma||'—'} · Email: ${kh.email?`<b>${kh.email}</b>`:'<span style="color:var(--amber)">chưa có</span>'}${unsub?' · <span style="color:var(--muted)">không gửi chiến dịch marketing; vẫn trả lời 1:1 khi khách liên hệ</span>':''}</div></div>
    ${sendPanel}${logPanel}
    <div class="panel"><div class="panel-h"><h3>Nhật ký liên lạc</h3></div>
      <div class="panel-b"><table><thead><tr><th>Thời điểm</th><th>Kênh</th><th>Nội dung</th></tr></thead>
      <tbody>${tlRows}</tbody></table></div></div>`;
  S.draftReply=null;
}
async function guiEmailKH(khId){
  const td=gv('em_td'), nd=gv('em_nd');
  if(!td||!nd){toast("Nhập tiêu đề và nội dung","err");return;}
  if(S.mode==="live"){ try{const r=await api(`/ban-hang/khach-hang/${khId}/gui-email`,{method:'POST',body:JSON.stringify({tieu_de:td,noi_dung:nd})});
    toast(`Đã gửi từ ${r.gui_tu} → ${r.den}`,"ok");viewBanHang($("#main"));}catch(e){toast(e.detail||e.message,"err");} return; }
  (DEMO.lien_lac[khId]=DEMO.lien_lac[khId]||[]).unshift({kenh:"EMAIL",huong:"DI",tieu_de:td,noi_dung:nd,gui_tu:"sv-sales@watersolutions.company",trang_thai:"GUI_OK",thoi_diem:new Date().toISOString().slice(0,16)});
  toast("Đã gửi qua hệ thống (demo) — đã ghi nhật ký","ok"); viewBanHang($("#main"));
}
async function ghiLienLac(khId){
  const kenh=gv('ll_kenh')||'GHI_CHU', nd=gv('ll_nd');
  if(!nd){toast("Nhập nội dung","err");return;}
  if(S.mode==="live"){ try{await api(`/ban-hang/khach-hang/${khId}/lien-lac`,{method:'POST',body:JSON.stringify({kenh,noi_dung:nd})});
    toast("Đã ghi nhận liên lạc","ok");viewBanHang($("#main"));}catch(e){toast(e.detail||e.message,"err");} return; }
  (DEMO.lien_lac[khId]=DEMO.lien_lac[khId]||[]).unshift({kenh,huong:"DI",noi_dung:nd,trang_thai:"GHI_NHAN",thoi_diem:new Date().toISOString().slice(0,16)});
  toast("Đã ghi nhận (demo)","ok"); viewBanHang($("#main"));
}

/* --- AI phân loại (luật, đồng bộ với backend FakeAIProvider) --- */
const YDINH_NHAN={QUAN_TAM:"Quan tâm",HOI_KY_THUAT:"Hỏi kỹ thuật",HEN_GAP:"Hẹn gặp",TU_CHOI:"Từ chối",KHIEU_NAI:"Khiếu nại",HUY_NHAN:"Hủy nhận",VANG_MAT:"Vắng mặt",SPAM:"Spam",KHAC:"Khác"};
const YDINH_MAU={QUAN_TAM:"b-ok",HOI_KY_THUAT:"b-info",HEN_GAP:"b-info",KHIEU_NAI:"b-tc",TU_CHOI:"b-cho",HUY_NHAN:"b-cho",VANG_MAT:"b-cho",SPAM:"b-tc",KHAC:"b-cho"};
const KHAN_MAU={CAO:"b-tc",TRUNG:"b-cho",THAP:"b-info"};
const SLA_GIO={CAO:4,TRUNG:24,THAP:48};
function aiPhanLoai(tieu_de,noi_dung){
  const t=((tieu_de||'')+' '+(noi_dung||'')).toLowerCase();
  const has=(...ks)=>ks.some(k=>t.includes(k));
  let y="KHAC";
  if(has("hủy đăng ký","ngừng nhận","không nhận email","unsubscribe","bỏ nhận tin","ngưng gửi"))y="HUY_NHAN";
  else if(has("vắng mặt","out of office","nghỉ phép","auto-reply","tự động trả lời","đang đi công tác","hồi âm tự động"))y="VANG_MAT";
  else if(has("khiếu nại","không hài lòng","sự cố","hỏng","hư hỏng","lỗi","kém","thất vọng","phàn nàn"))y="KHIEU_NAI";
  else if(has("khảo sát","hẹn","gặp","lịch","cuộc họp","đến xem","ghé"))y="HEN_GAP";
  else if(has("báo giá","quan tâm","tư vấn","công suất","m3","mét khối","cần mua","muốn lắp","đề nghị","giá"))y="QUAN_TAM";
  else if(has("kỹ thuật","thông số","công nghệ","màng","mbr","hỏi về","tài liệu"))y="HOI_KY_THUAT";
  else if(has("không có nhu cầu","từ chối","không quan tâm","đã có nhà cung cấp"))y="TU_CHOI";
  else if(has("trúng thưởng","khuyến mãi","vay vốn"))y="SPAM";
  let khan="THAP";
  if(y==="KHIEU_NAI"||has("gấp","khẩn","ngay","sớm nhất"))khan="CAO";
  else if(["QUAN_TAM","HEN_GAP","HOI_KY_THUAT"].includes(y))khan="TRUNG";
  const tl={QUAN_TAM:"Cảm ơn Quý công ty đã quan tâm. SVWS sẽ gửi báo giá chi tiết kèm phương án kỹ thuật phù hợp. Vui lòng cho biết công suất và yêu cầu cụ thể để chúng tôi tư vấn chính xác.",
    HOI_KY_THUAT:"Cảm ơn câu hỏi của Quý công ty. Bộ phận kỹ thuật SVWS sẽ giải đáp chi tiết và có thể sắp lịch khảo sát nếu cần.",
    HEN_GAP:"SVWS rất sẵn lòng sắp xếp buổi khảo sát/gặp trao đổi. Vui lòng cho biết thời gian và địa điểm thuận tiện.",
    TU_CHOI:"Cảm ơn Quý công ty đã phản hồi. SVWS mong có cơ hội hợp tác trong tương lai.",
    KHIEU_NAI:"SVWS rất tiếc về sự bất tiện này. Chúng tôi sẽ kiểm tra, xử lý ưu tiên và liên hệ ngay để khắc phục.",
    KHAC:"Cảm ơn Quý công ty đã phản hồi. SVWS đã tiếp nhận và sẽ liên hệ lại sớm."};
  return {y_dinh:y,khan,tom_tat:(noi_dung||'').slice(0,140),tra_loi:tl[y]||tl.KHAC};
}
function _aiApplyDemo(x){
  const ai=aiPhanLoai(x.tieu_de,x.noi_dung);
  x.ai_y_dinh=ai.y_dinh;x.ai_khan=ai.khan;x.ai_tom_tat=ai.tom_tat;x.ai_tra_loi=ai.tra_loi;
  if(ai.y_dinh==="HUY_NHAN"){ x.da_xu_ly=true; const kh=x.khach_hang_id&&(DEMO.khach||[]).find(k=>k.id===x.khach_hang_id); if(kh)kh.khong_nhan_email=true; return; }
  if(["VANG_MAT","SPAM"].includes(ai.y_dinh)){ x.da_xu_ly=true; return; }
  if(!(DEMO.cong_viec||[]).some(c=>c.lien_lac_id===x.id)){
    const gio=SLA_GIO[ai.khan]||24;
    DEMO.cong_viec.unshift({id:Date.now()+Math.floor(Math.random()*1e4),lien_lac_id:x.id,loai:ai.y_dinh,
      tieu_de:`[${ai.y_dinh}] ${x.tieu_de||''}`,mo_ta:ai.tom_tat,khach_hang_id:x.khach_hang_id,khach_ten:x.khach_ten,
      uu_tien:ai.khan,han_xu_ly:new Date(Date.now()+gio*3600*1000).toISOString().slice(0,16),trang_thai:"MO"});
  }
  // Cơ hội + nháp báo giá cho ý định bán hàng
  if(["QUAN_TAM","HOI_KY_THUAT","HEN_GAP"].includes(ai.y_dinh) && !(DEMO.co_hoi||[]).some(c=>c.lien_lac_id===x.id)){
    const id=Date.now()+Math.floor(Math.random()*1e4);
    const bg=(ai.y_dinh==="QUAN_TAM"&&x.khach_hang_id)?("BG-N"+id):null;
    DEMO.co_hoi.unshift({id,lien_lac_id:x.id,khach_hang_id:x.khach_hang_id,khach_ten:x.khach_ten,
      tieu_de:x.tieu_de||"Cơ hội từ phản hồi",giai_doan:"QUAN_TAM",gia_tri_dk:0,bao_gia_id:bg,don_hang_id:null,nguon:"EMAIL"});
  }
}

/* --- Tab Hộp thư phản hồi (AI: phân loại, tự xử lý, gợi ý trả lời) --- */
async function bhPhanHoi(host){
  if(!S.phFilter)S.phFilter="chua";
  let list=[], khList=[];
  if(S.mode==="live"){
    try{list=await api(`/ban-hang/phan-hoi${S.phFilter==="chua"?'?chua_xu_ly=true':''}`);}catch(e){toast(e.detail||e.message,"err");}
    try{khList=await api("/ban-hang/khach-hang");}catch{}
  } else {
    list=(DEMO.phan_hoi||[]).filter(x=>S.phFilter==="tat_ca"||!x.da_xu_ly);
    khList=DEMO.khach||[];
  }
  S._phList=list;
  const canOp=can("ban_hang","THAO_TAC");
  const opts=khList.map(k=>`<option value="${k.id}">${k.ten}</option>`).join('');
  const autoY=["HUY_NHAN","VANG_MAT","SPAM"];
  const rows=list.map(x=>{
    const matched=!!x.khach_hang_id;
    const who=matched?(x.khach_ten||("KH #"+x.khach_hang_id)):'<span style="color:var(--amber)">chưa gắn KH</span>';
    const st=x.da_xu_ly?'<span class="badge b-ok">Đã xử lý</span>':'<span class="badge b-cho">Chưa xử lý</span>';
    const aiCell = x.ai_y_dinh
      ? `<span class="badge ${YDINH_MAU[x.ai_y_dinh]||'b-cho'}">${YDINH_NHAN[x.ai_y_dinh]||x.ai_y_dinh}</span> <span class="badge ${KHAN_MAU[x.ai_khan]||'b-cho'}">${x.ai_khan||''}</span>${autoY.includes(x.ai_y_dinh)?'<div style="color:var(--muted);font-size:11px;margin-top:3px">tự xử lý</div>':''}`
      : '<span style="color:var(--muted);font-size:12px">chưa phân tích</span>';
    const goiY = (x.ai_tra_loi && matched && !autoY.includes(x.ai_y_dinh))
      ? `<div style="margin-top:6px;background:var(--surface);border-radius:8px;padding:8px 10px;font-size:12.5px"><b>Gợi ý trả lời:</b> ${x.ai_tra_loi}<br><button class="btn-sm" style="margin-top:6px" onclick="dungGoiY(${x.id})">Dùng gợi ý để trả lời</button></div>` : '';
    let act='';
    if(canOp){
      if(!x.ai_y_dinh) act+=`<button class="btn-sm ghost" onclick="phanTichPH(${x.id})">Phân tích</button> `;
      if(matched) act+=`<button class="btn-sm ghost" onclick="openKH(${x.khach_hang_id})">Mở hồ sơ</button> `;
      else act+=`<select id="ph_kh_${x.id}"><option value="">— chọn khách —</option>${opts}</select> <button class="btn-sm ghost" onclick="ganKhachPH(${x.id})">Gắn</button> `;
      if(!x.da_xu_ly) act+=`<button class="btn-sm" onclick="danhDauPH(${x.id})">Đã xử lý</button>`;
    }
    return `<tr>
      <td style="white-space:nowrap;color:var(--muted);font-size:12px">${(x.thoi_diem||'').toString().replace('T',' ').slice(0,16)}</td>
      <td>${x.tu_email||'—'}<div style="color:var(--muted);font-size:12px">${who}</div></td>
      <td>${x.tieu_de?`<b>${x.tieu_de}</b><br>`:''}<span style="color:var(--muted)">${(x.noi_dung||'').slice(0,140)}</span>${goiY}</td>
      <td>${aiCell}</td><td>${st}</td><td>${act||'—'}</td></tr>`;
  }).join('');
  host.innerHTML=`<div class="note" style="padding:0 0 12px">Thư trả lời được thu vào hệ thống và <b>AI phân loại ý định</b>: hủy-nhận/vắng-mặt được tự xử lý, việc cần làm sinh công việc kèm SLA, và có sẵn <b>gợi ý nội dung trả lời</b> để duyệt rồi gửi từ địa chỉ công ty.</div>
    <div class="panel"><div class="panel-h"><h3>Hộp thư phản hồi</h3><div class="spacer"></div>
      <select id="ph_filter" onchange="S.phFilter=this.value;viewBanHang($('#main'))" style="margin-right:8px">
        <option value="chua"${S.phFilter==="chua"?" selected":""}>Chưa xử lý</option>
        <option value="tat_ca"${S.phFilter==="tat_ca"?" selected":""}>Tất cả</option></select>
      ${canOp?`<button class="btn-sm" onclick="dongBoPhanHoi()">Đồng bộ + phân tích</button>`:''}</div>
    <div class="panel-b"><table><thead><tr><th>Thời điểm</th><th>Từ / Khách</th><th>Nội dung & gợi ý</th><th>Phân loại AI</th><th>Trạng thái</th><th>Hành động</th></tr></thead>
    <tbody>${rows||'<tr><td colspan="6" class="empty" style="padding:24px">Chưa có thư phản hồi. Bấm “Đồng bộ + phân tích” để kéo thư mới.</td></tr>'}</tbody></table></div></div>`;
}
async function dongBoPhanHoi(){
  if(S.mode==="live"){ try{const r=await api("/ban-hang/dong-bo-phan-hoi",{method:'POST'});
    toast(`Đồng bộ: ${r.so_thu_moi} thư · tự xử lý ${r.tu_xu_ly} · việc ${r.cong_viec_moi} · cơ hội ${r.co_hoi_moi} · nháp BG ${r.bao_gia_nhap}`,"ok");viewBanHang($("#main"));}
    catch(e){toast(e.detail||e.message,"err");} return; }
  let moi=0;
  (DEMO._phanHoiMau||[]).forEach(m=>{
    if((DEMO.phan_hoi||[]).some(x=>x.message_id===m.message_id))return;
    const kh=(DEMO.khach||[]).find(k=>(k.email||'').toLowerCase()===m.tu_email.toLowerCase());
    const rec={id:Date.now()+moi,message_id:m.message_id,tu_email:m.tu_email,tieu_de:m.tieu_de,noi_dung:m.noi_dung,
      khach_hang_id:kh?kh.id:null,khach_ten:kh?kh.ten:null,da_xu_ly:false,thoi_diem:new Date().toISOString().slice(0,16)};
    if(kh){(DEMO.lien_lac[kh.id]=DEMO.lien_lac[kh.id]||[]).unshift({kenh:"EMAIL",huong:"DEN",tieu_de:m.tieu_de,noi_dung:m.noi_dung,trang_thai:"NHAN",thoi_diem:rec.thoi_diem});}
    _aiApplyDemo(rec);
    DEMO.phan_hoi.unshift(rec);
    moi++;
  });
  toast(moi?`Đồng bộ + phân tích (demo): ${moi} thư mới`:"Không có thư mới (đã thu trước đó)","ok"); viewBanHang($("#main"));
}
async function phanTichPH(id){
  if(S.mode==="live"){ try{const r=await api(`/ban-hang/phan-hoi/${id}/phan-tich`,{method:'POST'});
    toast("Đã phân tích: "+(YDINH_NHAN[r.y_dinh]||r.y_dinh),"ok");viewBanHang($("#main"));}catch(e){toast(e.detail||e.message,"err");} return; }
  const x=DEMO.phan_hoi.find(p=>p.id===id); if(x)_aiApplyDemo(x);
  toast("Đã phân tích (demo)","ok"); viewBanHang($("#main"));
}
function dungGoiY(id){
  const x=(S._phList||[]).find(p=>p.id===id); if(!x||!x.khach_hang_id){toast("Thư chưa gắn khách","err");return;}
  S.draftReply={khId:x.khach_hang_id, tieu_de:"Re: "+((x.tieu_de||'').replace(/^re:\s*/i,'')), noi_dung:x.ai_tra_loi||''};
  openKH(x.khach_hang_id);
}
async function ganKhachPH(id){
  const sel=document.getElementById('ph_kh_'+id), khId=sel&&parseInt(sel.value);
  if(!khId){toast("Chọn khách để gắn","err");return;}
  if(S.mode==="live"){ try{await api(`/ban-hang/phan-hoi/${id}/gan-khach`,{method:'POST',body:JSON.stringify({khach_hang_id:khId})});
    await api(`/ban-hang/phan-hoi/${id}/phan-tich`,{method:'POST'}).catch(()=>{});
    toast("Đã gắn khách & phân tích","ok");viewBanHang($("#main"));}catch(e){toast(e.detail||e.message,"err");} return; }
  const x=DEMO.phan_hoi.find(p=>p.id===id), kh=(DEMO.khach||[]).find(k=>k.id===khId);
  if(x&&kh){x.khach_hang_id=kh.id;x.khach_ten=kh.ten;(DEMO.lien_lac[kh.id]=DEMO.lien_lac[kh.id]||[]).unshift({kenh:"EMAIL",huong:"DEN",tieu_de:x.tieu_de,noi_dung:x.noi_dung,trang_thai:"NHAN",thoi_diem:x.thoi_diem}); _aiApplyDemo(x);}
  toast("Đã gắn thư vào "+(kh?kh.ten:''),"ok"); viewBanHang($("#main"));
}
async function danhDauPH(id){
  if(S.mode==="live"){ try{await api(`/ban-hang/phan-hoi/${id}/danh-dau`,{method:'POST'});
    toast("Đã đánh dấu xử lý","ok");viewBanHang($("#main"));}catch(e){toast(e.detail||e.message,"err");} return; }
  const x=DEMO.phan_hoi.find(p=>p.id===id); if(x)x.da_xu_ly=true;
  toast("Đã đánh dấu xử lý (demo)","ok"); viewBanHang($("#main"));
}

/* --- Tab Công việc (SLA) từ phản hồi --- */
async function bhCongViec(host){
  if(!S.cvFilter)S.cvFilter="mo";
  let list=[];
  if(S.mode==="live"){ const qp=S.cvFilter==="qua_han"?"?qua_han=true":S.cvFilter==="cua_toi"?"?cua_toi=true":"?mo=true";
    try{list=await api("/ban-hang/cong-viec"+qp);}catch(e){toast(e.detail||e.message,"err");} }
  else {
    const now=Date.now();
    list=(DEMO.cong_viec||[]).map(c=>({...c,qua_han:c.trang_thai!=="XONG"&&c.han_xu_ly&&new Date(c.han_xu_ly).getTime()<now}));
    if(S.cvFilter==="qua_han")list=list.filter(c=>c.qua_han);
    else if(S.cvFilter!=="cua_toi")list=list.filter(c=>c.trang_thai!=="XONG");
  }
  const canOp=can("ban_hang","THAO_TAC");
  const rows=list.map(c=>{
    const pr=KHAN_MAU[c.uu_tien]||'b-cho';
    const stt={MO:'Mở',DANG_XU_LY:'Đang xử lý',XONG:'Xong'}[c.trang_thai]||c.trang_thai;
    const han=(c.han_xu_ly||'').toString().replace('T',' ').slice(0,16);
    let act='';
    if(canOp&&c.trang_thai!=="XONG"){
      if(c.trang_thai==="MO")act+=`<button class="btn-sm ghost" onclick="capNhatCV(${c.id},'DANG_XU_LY')">Bắt đầu</button> `;
      act+=`<button class="btn-sm" onclick="capNhatCV(${c.id},'XONG')">Xong</button> `;
    }
    if(c.khach_hang_id)act+=`<button class="btn-sm ghost" onclick="openKH(${c.khach_hang_id})">Hồ sơ</button>`;
    return `<tr class="${c.qua_han?'qh':''}">
      <td><b>${c.tieu_de}</b>${c.mo_ta?`<div style="color:var(--muted);font-size:12px">${c.mo_ta}</div>`:''}</td>
      <td>${c.khach_ten||(c.khach_hang_id?('KH #'+c.khach_hang_id):'—')}</td>
      <td><span class="badge ${pr}">${c.uu_tien}</span></td>
      <td>${han||'—'} ${c.qua_han?'<span class="badge b-tc">Quá hạn</span>':''}</td>
      <td>${stt}</td><td>${act||'—'}</td></tr>`;
  }).join('');
  host.innerHTML=`<div class="note" style="padding:0 0 12px">Việc tự sinh từ thư phản hồi, gán cho người phụ trách kèm hạn xử lý (SLA theo độ khẩn: Cao 4h · Trung 24h · Thấp 48h). Việc quá hạn được tô đỏ để leo thang.</div>
    <div class="panel"><div class="panel-h"><h3>Công việc từ phản hồi</h3><div class="spacer"></div>
      <select onchange="S.cvFilter=this.value;viewBanHang($('#main'))" style="margin-right:8px">
        <option value="mo"${S.cvFilter==="mo"?" selected":""}>Đang mở</option>
        <option value="cua_toi"${S.cvFilter==="cua_toi"?" selected":""}>Của tôi</option>
        <option value="qua_han"${S.cvFilter==="qua_han"?" selected":""}>Quá hạn</option></select></div>
    <div class="panel-b"><table><thead><tr><th>Việc</th><th>Khách</th><th>Ưu tiên</th><th>Hạn xử lý (SLA)</th><th>Trạng thái</th><th>Hành động</th></tr></thead>
    <tbody>${rows||'<tr><td colspan="6" class="empty" style="padding:24px">Chưa có công việc.</td></tr>'}</tbody></table></div></div>`;
}
async function capNhatCV(id,tt){
  if(S.mode==="live"){ try{await api(`/ban-hang/cong-viec/${id}/trang-thai`,{method:'POST',body:JSON.stringify({trang_thai:tt})});
    toast("Đã cập nhật","ok");viewBanHang($("#main"));}catch(e){toast(e.detail||e.message,"err");} return; }
  const c=(DEMO.cong_viec||[]).find(x=>x.id===id); if(c){c.trang_thai=tt; c.hoan_thanh_luc=(tt==="XONG")?new Date().toISOString().slice(0,16):null;}
  toast("Đã cập nhật (demo)","ok"); viewBanHang($("#main"));
}

/* --- Tab Cơ hội (pipeline CRM) --- */
const GD_NHAN={MOI:"Mới",QUAN_TAM:"Quan tâm",BAO_GIA:"Báo giá",DAM_PHAN:"Đàm phán",THANG:"Thắng",THUA:"Thua"};
const GD_MAU={MOI:"b-info",QUAN_TAM:"b-cho",BAO_GIA:"b-info",DAM_PHAN:"b-cho",THANG:"b-ok",THUA:"b-tc"};
const GD_LIST=["MOI","QUAN_TAM","BAO_GIA","DAM_PHAN","THANG","THUA"];
async function bhCoHoi(host){
  if(!S.chFilter)S.chFilter="";
  let list=[];
  if(S.mode==="live"){ try{list=await api("/ban-hang/co-hoi"+(S.chFilter?`?giai_doan=${S.chFilter}`:""));}catch(e){toast(e.detail||e.message,"err");} }
  else { list=(DEMO.co_hoi||[]).filter(c=>!S.chFilter||c.giai_doan===S.chFilter); }
  const all=S.mode==="live"?null:(DEMO.co_hoi||[]);
  const canOp=can("ban_hang","THAO_TAC");
  // tóm tắt pipeline (đếm + giá trị theo giai đoạn) — từ toàn bộ nếu demo
  const src = all|| list;
  const chips=GD_LIST.map(g=>{const items=src.filter(c=>c.giai_doan===g);const val=items.reduce((s,c)=>s+(c.gia_tri_dk||0),0);
    return `<span class="badge ${GD_MAU[g]}" style="margin:2px 4px 2px 0">${GD_NHAN[g]}: ${items.length}${val?` · ${vnd(val)}`:''}</span>`;}).join('');
  const rows=list.map(c=>{
    const sel=`<select id="ch_gd_${c.id}">${GD_LIST.map(g=>`<option value="${g}"${c.giai_doan===g?' selected':''}>${GD_NHAN[g]}</option>`).join('')}</select>`;
    let act=canOp?`${sel} <input id="ch_val_${c.id}" type="number" placeholder="giá trị" value="${c.gia_tri_dk||''}" style="width:120px"> <button class="btn-sm ghost" onclick="chuyenGD(${c.id})">Lưu</button> `:'';
    if(c.khach_hang_id)act+=`<button class="btn-sm ghost" onclick="openKH(${c.khach_hang_id})">Hồ sơ</button>`;
    const link=[c.bao_gia_id?`BG #${c.bao_gia_id}`:'',c.don_hang_id?`Đơn #${c.don_hang_id}`:''].filter(Boolean).join(' · ')||'—';
    return `<tr><td><b>${c.tieu_de||'—'}</b><div style="color:var(--muted);font-size:12px">${c.nguon==='EMAIL'?'từ phản hồi email':c.nguon||''}</div></td>
      <td>${c.khach_ten||(c.khach_hang_id?('KH #'+c.khach_hang_id):'—')}</td>
      <td><span class="badge ${GD_MAU[c.giai_doan]}">${GD_NHAN[c.giai_doan]||c.giai_doan}</span></td>
      <td style="white-space:nowrap">${c.gia_tri_dk?vnd(c.gia_tri_dk):'—'}</td>
      <td style="color:var(--muted);font-size:12px">${link}</td>
      <td>${act||'—'}</td></tr>`;
  }).join('');
  host.innerHTML=`<div class="note" style="padding:0 0 12px">Cơ hội tự sinh từ thư <b>Quan tâm / Hỏi kỹ thuật / Hẹn gặp</b>; thư Quan tâm còn được tạo sẵn <b>nháp báo giá</b>. Kéo cơ hội qua các giai đoạn để theo dõi chuyển đổi.</div>
    <div class="panel"><div class="panel-h"><h3>Pipeline cơ hội</h3></div><div class="panel-b" style="padding-bottom:6px">${chips}</div></div>
    <div class="panel"><div class="panel-h"><h3>Danh sách cơ hội</h3><div class="spacer"></div>
      <select onchange="S.chFilter=this.value;viewBanHang($('#main'))"><option value="">Tất cả giai đoạn</option>${GD_LIST.map(g=>`<option value="${g}"${S.chFilter===g?' selected':''}>${GD_NHAN[g]}</option>`).join('')}</select></div>
    <div class="panel-b"><table><thead><tr><th>Cơ hội</th><th>Khách</th><th>Giai đoạn</th><th>Giá trị dự kiến</th><th>Liên kết</th><th>Hành động</th></tr></thead>
    <tbody>${rows||'<tr><td colspan="6" class="empty" style="padding:24px">Chưa có cơ hội. Đồng bộ thư phản hồi để tự tạo.</td></tr>'}</tbody></table></div></div>`;
}
async function chuyenGD(id){
  const gd=gv('ch_gd_'+id), valEl=document.getElementById('ch_val_'+id);
  const val=valEl&&valEl.value!==''?Number(valEl.value):null;
  if(S.mode==="live"){ try{await api(`/ban-hang/co-hoi/${id}/giai-doan`,{method:'POST',body:JSON.stringify({giai_doan:gd,gia_tri_dk:val})});
    toast("Đã chuyển giai đoạn","ok");viewBanHang($("#main"));}catch(e){toast(e.detail||e.message,"err");} return; }
  const c=(DEMO.co_hoi||[]).find(x=>x.id===id); if(c){c.giai_doan=gd; if(val!=null)c.gia_tri_dk=val; if(gd==="THANG"&&!c.don_hang_id)c.don_hang_id="DH-"+id;}
  toast("Đã chuyển giai đoạn (demo)","ok"); viewBanHang($("#main"));
}

/* --- Tab Tổng quan (dashboard) --- */
function _dashDemo(){
  const ph=(DEMO.phan_hoi||[]).filter(x=>x.ai_y_dinh==="QUAN_TAM").length;
  const ch=(DEMO.co_hoi||[]); const now=Date.now();
  const n_bg=ch.filter(c=>c.bao_gia_id).length, n_dh=ch.filter(c=>c.giai_doan==="THANG").length;
  const cvs=(DEMO.cong_viec||[]);
  const mo=cvs.filter(c=>c.trang_thai!=="XONG").length;
  const qh=cvs.filter(c=>c.trang_thai!=="XONG"&&c.han_xu_ly&&new Date(c.han_xu_ly).getTime()<now).length;
  const xong=cvs.filter(c=>c.trang_thai==="XONG");
  let dung=0; xong.forEach(c=>{if(c.hoan_thanh_luc&&c.han_xu_ly&&new Date(c.hoan_thanh_luc)<=new Date(c.han_xu_ly))dung++;});
  const pct=(a,b)=>b?Math.round(a/b*1000)/10:0;
  const gd={}; GD_LIST.forEach(g=>gd[g]=ch.filter(c=>c.giai_doan===g).length);
  return {pheu:{phan_hoi_quan_tam:ph,co_hoi:ch.length,bao_gia:n_bg,don_hang:n_dh},
    ty_le:{ph_to_cohoi:pct(ch.length,ph),cohoi_to_baogia:pct(n_bg,ch.length),baogia_to_donhang:pct(n_dh,n_bg)},
    doanh_thu_don:ch.filter(c=>c.giai_doan==="THANG").reduce((s,c)=>s+(c.gia_tri_dk||0),0),
    cong_viec:{mo,qua_han:qh,xong:xong.length,dung_han:dung,ty_le_dung_han:pct(dung,xong.length),gio_xu_ly_tb:0},
    co_hoi_theo_giai_doan:gd};
}
async function bhTongQuan(host){
  let d;
  if(S.mode==="live"){ try{d=await api("/ban-hang/dashboard");}catch(e){toast(e.detail||e.message,"err");return;} }
  else d=_dashDemo();
  const f=d.pheu, t=d.ty_le, cv=d.cong_viec;
  const card=(label,val,sub)=>`<div style="flex:1;min-width:130px;background:var(--surface);border-radius:12px;padding:14px 16px">
    <div style="color:var(--muted);font-size:12px">${label}</div><div style="font-size:24px;font-weight:700;margin-top:2px">${val}</div>${sub?`<div style="color:var(--muted);font-size:11px;margin-top:2px">${sub}</div>`:''}</div>`;
  const arrow=p=>`<div style="display:flex;flex-direction:column;justify-content:center;align-items:center;color:var(--muted);font-size:11px;padding:0 4px">→<br>${p}%</div>`;
  const maxgd=Math.max(1,...GD_LIST.map(g=>d.co_hoi_theo_giai_doan[g]||0));
  const bars=GD_LIST.map(g=>{const n=d.co_hoi_theo_giai_doan[g]||0;return `<div style="display:flex;align-items:center;gap:10px;margin:5px 0">
    <div style="width:80px;font-size:12px;color:var(--muted)">${GD_NHAN[g]}</div>
    <div style="flex:1;background:var(--surface);border-radius:6px;overflow:hidden;height:18px"><div style="width:${Math.round(n/maxgd*100)}%;min-width:${n?'8px':'0'};height:100%;background:var(--brand,#0ea5a4)"></div></div>
    <div style="width:28px;text-align:right;font-size:12px">${n}</div></div>`;}).join('');
  host.innerHTML=`<div class="note" style="padding:0 0 12px">Phễu chuyển đổi từ phản hồi khách đến đơn hàng, và chỉ số xử lý công việc theo SLA.</div>
    <div class="panel"><div class="panel-h"><h3>Phễu chuyển đổi</h3></div>
      <div class="panel-b" style="display:flex;flex-wrap:wrap;gap:8px;align-items:stretch">
        ${card("Phản hồi quan tâm",f.phan_hoi_quan_tam)}${arrow(t.ph_to_cohoi)}
        ${card("Cơ hội",f.co_hoi)}${arrow(t.cohoi_to_baogia)}
        ${card("Báo giá",f.bao_gia)}${arrow(t.baogia_to_donhang)}
        ${card("Đơn hàng",f.don_hang,vnd(d.doanh_thu_don))}</div></div>
    <div class="panel"><div class="panel-h"><h3>Công việc theo SLA</h3></div>
      <div class="panel-b" style="display:flex;flex-wrap:wrap;gap:8px">
        ${card("Đang mở",cv.mo)}${card("Quá hạn",cv.qua_han,"cần leo thang")}${card("Đã xong",cv.xong)}
        ${card("Đúng hạn",cv.ty_le_dung_han+"%",cv.dung_han+"/"+cv.xong)}${card("Giờ xử lý TB",cv.gio_xu_ly_tb)}</div></div>
    <div class="panel"><div class="panel-h"><h3>Cơ hội theo giai đoạn</h3></div><div class="panel-b">${bars}</div></div>`;
}
async function viewNCC(m){
  if(!S.nccTab)S.nccTab="ncc";
  m.innerHTML=head("Nhà cung cấp","Mua hàng: hồ sơ NCC · đơn mua duyệt theo hạn mức · nhận hàng (nhập kho) · công nợ phải trả");
  const tabs=[["ncc","Nhà cung cấp"],["po","Đơn mua (PO)"],["bao_gia","Báo giá"],["cong_no","Công nợ phải trả"],["kiem_soat","Kiểm soát"]];
  m.innerHTML+=`<div class="tabs">${tabs.map(([k,l])=>`<button class="${S.nccTab===k?'active':''}" onclick="nccSwitch('${k}')">${l}</button>`).join('')}</div><div id="nccBody"></div>`;
  const host=$("#nccBody");
  if(S.nccTab==="ncc") await nccSuppliers(host);
  else if(S.nccTab==="po") await nccPO(host);
  else if(S.nccTab==="bao_gia") await nccBaoGia(host);
  else if(S.nccTab==="cong_no") await nccCongNo(host);
  else await nccKiemSoat(host);
}
function nccSwitch(t){S.nccTab=t;S.poRecv=null;viewNCC($("#main"));}
const stars=n=>{const f=Math.round(n);return '★★★★★☆☆☆☆☆'.slice(5-f,10-f);};
async function _nccSups(){ if(S.mode==="live"){ try{return await api("/ncc/nha-cung-cap");}catch{return [];} } return DEMO.ncc.suppliers; }
async function _nccOrders(){ if(S.mode==="live"){ try{return await api("/ban-hang/don-hang");}catch{return [];} } return DEMO.don_hang; }

/* --- Tab Nhà cung cấp --- */
async function nccSuppliers(host){
  const sups=await _nccSups();
  const canAdd=can("ncc","THAO_TAC");
  const rows=sups.map(s=>`<tr>
    <td><b>${s.ma||'—'}</b></td><td>${s.ten}</td><td>${s.email||'—'}</td>
    <td class="num">${vnd(Number(s.han_muc_cong_no||0))}</td>
    <td>${stars(Number(s.diem_danh_gia||0))} <span style="color:var(--muted)">${Number(s.diem_danh_gia||0).toFixed(1)}</span></td>
    <td>${s.blacklist?'<span class="badge b-tc">Hạn chế</span>':'<span class="badge b-ok">Đang dùng</span>'}</td>
    <td>${canAdd?`<button class="btn-sm ghost" onclick="nccDanhGia(${s.id})">Đánh giá</button>`:'—'}</td></tr>`).join('');
  const form=canAdd?`<div id="nccForm" class="formrow hidden">
    <div class="f"><label>Mã</label><input id="n_ma" placeholder="NCC-04"></div>
    <div class="f" style="flex:2"><label>Tên NCC</label><input id="n_ten" placeholder="Tên công ty"></div>
    <div class="f"><label>Email</label><input id="n_email" placeholder="sale@ncc.vn"></div>
    <div class="f"><label>MST</label><input id="n_mst"></div>
    <div class="f"><label>Điện thoại</label><input id="n_dt"></div>
    <div class="f"><label>Hạn mức công nợ</label><input id="n_hm" type="number" value="0"></div>
    <button class="btn-sm" onclick="nccAdd()">Lưu</button></div>`:'';
  host.innerHTML=`<div class="panel"><div class="panel-h"><h3>Hồ sơ nhà cung cấp</h3><div class="spacer"></div>
      ${canAdd?`<button class="btn-sm" onclick="$('#nccForm').classList.toggle('hidden')">+ Thêm NCC</button>`:''}</div>
    ${canAdd?form:`<div class="perm-denied">Vai trò ${S.role} chỉ được xem nhà cung cấp.</div>`}
    <div class="panel-b"><table><thead><tr><th>Mã</th><th>Tên</th><th>Email</th><th class="num">Hạn mức CN</th><th>Đánh giá</th><th>Trạng thái</th><th></th></tr></thead>
    <tbody>${rows}</tbody></table></div></div>`;
}
async function nccAdd(){
  const ten=gv('n_ten'); if(!ten){toast("Nhập tên NCC","err");return;}
  const payload={ma:gv('n_ma')||null,ten,email:gv('n_email')||null,ma_so_thue:gv('n_mst')||null,
    dien_thoai:gv('n_dt')||null,han_muc_cong_no:Number(gv('n_hm')||0)};
  if(S.mode==="live"){ try{await api("/ncc/nha-cung-cap",{method:'POST',body:JSON.stringify(payload)});
    toast("Đã thêm NCC","ok");viewNCC($("#main"));}catch(e){toast(e.detail||e.message,"err");} return; }
  DEMO.ncc.suppliers.push({id:Date.now(),ma:payload.ma||"NEW",ten,email:payload.email,han_muc_cong_no:payload.han_muc_cong_no,diem_danh_gia:0,blacklist:false});
  toast("Đã thêm (demo)","ok"); viewNCC($("#main"));
}
async function nccDanhGia(id){
  const v=prompt("Chấm điểm NCC (0–5):","4"); if(v===null)return; const diem=Number(v);
  if(isNaN(diem)||diem<0||diem>5){toast("Điểm phải 0–5","err");return;}
  if(S.mode==="live"){ try{await api(`/ncc/nha-cung-cap/${id}/danh-gia`,{method:'POST',body:JSON.stringify({diem})});
    toast("Đã đánh giá","ok");viewNCC($("#main"));}catch(e){toast(e.detail||e.message,"err");} return; }
  const s=DEMO.ncc.suppliers.find(x=>x.id===id); if(s){s.diem_danh_gia=Math.round(((s.diem_danh_gia+diem)/2)*10)/10; s.blacklist=s.diem_danh_gia<2.5;}
  toast("Đã đánh giá (demo)","ok"); viewNCC($("#main"));
}

/* --- Tab Đề xuất mua (1 đầu mối xét duyệt) --- */
const DX_NHAN={MOI:"Mới",DA_DUYET:"Đã duyệt",TU_CHOI:"Từ chối",DA_TAO_PO:"Đã tạo PO"};
const DX_MAU={MOI:"b-cho",DA_DUYET:"b-ok",TU_CHOI:"b-tc",DA_TAO_PO:"b-info"};
async function viewDeXuat(m){
  m.innerHTML=head("Đề xuất mua hàng","Một đầu mối tiếp nhận & xét duyệt đề xuất mua — duyệt xong tự chuyển sang Nhà cung cấp để tạo PO");
  const sups=await _nccSups(), orders=await _nccOrders();
  let hhs = S.mode==="live" ? await api("/kho/hang-hoa").catch(()=>[]) : DEMO.hang_hoa;
  let list;
  if(S.mode==="live"){ try{list=await api("/ncc/yeu-cau-mua");}catch(e){toast(e.detail||e.message,"err");list=[];} }
  else list=DEMO.de_xuat||[];
  const hhName=id=>{const h=hhs.find(x=>x.id===id);return h?h.ten:("HH #"+id);};
  const supName=id=>{const s=sups.find(x=>x.id===id);return s?s.ten:(id?("NCC #"+id):'—');};
  const ordNo=id=>{if(!id)return '—';const o=orders.find(x=>x.id===id);return o?(o.so||('DH-'+id)):('Đơn #'+id);};
  const canOp=can("ncc","THAO_TAC"), canApprove=can("ncc","DUYET");
  const rows=list.map(x=>{
    let act='';
    if(x.trang_thai==="MOI"&&canApprove) act+=`<button class="btn-sm" onclick="nccDxDuyet(${x.id})">Duyệt</button> <button class="btn-sm ghost" onclick="nccDxTuChoi(${x.id})">Từ chối</button>`;
    else if(x.trang_thai==="DA_DUYET") act+=`<span style="color:var(--muted)">→ đã chuyển Nhà cung cấp</span>`;
    else if(x.trang_thai==="DA_TAO_PO") act+=`<span style="color:var(--muted)">PO #${x.don_mua_id||''}</span>`;
    const nItem=(x.so_dong||1);
    const badgeN=nItem>1?` <span class="badge b-info">+${nItem-1} mặt hàng</span>`:'';
    let dk='';
    if(x.dinh_kem_url)dk+=`<div><a href="${x.dinh_kem_url}" target="_blank" style="font-size:12px">📊 Dự toán (Sheet)</a></div>`;
    if(x.dinh_kem_file)dk+=`<div><a href="#" onclick="nccDxTaiDinhKem(${x.id});return false" style="font-size:12px">📎 ${(x.dinh_kem_file.split('_').slice(1).join('_'))||'tệp dự toán'}</a></div>`;
    return `<tr><td>${x.ten_hh||hhName(x.hang_hoa_id)}${badgeN}</td><td class="num">${Number(x.so_luong)}</td>
      <td>${ordNo(x.don_hang_id)}</td><td>${supName(x.nha_cung_cap_id)}</td>
      <td class="num">${x.don_gia?vnd(x.don_gia):'—'}</td><td>${x.ly_do||'—'}${dk}</td>
      <td><span class="badge ${DX_MAU[x.trang_thai]||'b-cho'}">${DX_NHAN[x.trang_thai]||x.trang_thai}</span></td>
      <td>${act||'—'}</td></tr>`;
  }).join('');
  window.DXOPTHH = hhs.map(h=>`<option value="${h.id}">${h.ten}</option>`).join('');
  window.DXOPTNCC = '<option value="">— theo đề xuất —</option>'+sups.map(s=>`<option value="${s.id}">${s.ten}</option>`).join('');
  const form = canOp ? `<div class="panel"><div class="panel-h"><h3>Tạo đề xuất mua</h3><div class="spacer"></div>
      <button class="btn-sm" onclick="$('#dxForm').classList.toggle('hidden')">+ Đề xuất</button></div>
    <div id="dxForm" class="hidden" style="padding:0 18px 14px">
     <div style="font-weight:600;margin:6px 0">Sản phẩm đề xuất</div>
     <div id="dxItems">${_dxItemRowHTML()}</div>
     <div style="margin:2px 0 12px"><button class="btn-sm ghost" onclick="dxAddItem()">+ Thêm sản phẩm</button></div>
     <div class="formrow" style="padding-top:0"><div class="f"><label>NCC đề xuất</label><select id="dx_ncc"><option value="">—</option>${sups.map(s=>`<option value="${s.id}">${s.ten}</option>`).join('')}</select></div>
       <div class="f"><label>Mã bán hàng</label><select id="dx_dh"><option value="">— không gắn —</option>${orders.map(o=>`<option value="${o.id}">${o.so||('DH-'+o.id)}</option>`).join('')}</select></div>
       <div class="f"><label>Ngày cần</label><input id="dx_can" type="date"></div></div>
     <div class="formrow" style="padding-top:0"><div class="f" style="flex:3"><label>Lý do</label><input id="dx_ly" placeholder="Lý do đề xuất"></div></div>
     <div style="font-weight:600;margin:6px 0">Đính kèm dự toán (tùy chọn)</div>
     <div class="formrow" style="padding-top:0"><div class="f" style="flex:2"><label>📊 Link Google Sheet</label><input id="dx_url" placeholder="https://docs.google.com/spreadsheets/..."></div>
       <div class="f" style="flex:2"><label>📎 Hoặc tải tệp (xlsx/csv/pdf)</label><input id="dx_file" type="file" accept=".xlsx,.xls,.csv,.pdf"></div></div>
     <button class="btn-sm" onclick="nccDxCreate()">Gửi đề xuất</button></div></div>` : '';
  m.innerHTML+=`<div class="note" style="padding:0 0 12px"><b>Một đầu mối</b> tiếp nhận mọi đề xuất mua (thủ công + tự sinh khi tồn thấp). Gắn <b>Mã bán hàng</b> để dữ liệu liên tục tới giá vốn. Đề xuất được duyệt sẽ xuất hiện ở mục <b>Nhà cung cấp → Đơn mua</b> để tạo PO.</div>
    ${form}
    <div class="panel"><div class="panel-h"><h3>Hàng đợi đề xuất</h3></div>
    <div class="panel-b"><table><thead><tr><th>Hàng hóa</th><th class="num">SL</th><th>Mã bán hàng</th><th>NCC đề xuất</th><th class="num">Đơn giá DK</th><th>Lý do</th><th>Trạng thái</th><th>Hành động</th></tr></thead>
    <tbody>${rows||'<tr><td colspan="8" class="empty" style="padding:20px">Chưa có đề xuất.</td></tr>'}</tbody></table></div></div>`;
}
function _dxItemRowHTML(){
  return `<div class="dxi-row formrow" style="padding-top:0">
    <div class="f" style="flex:2"><label>Hàng hóa</label><select class="dxi-hh">${window.DXOPTHH||''}</select></div>
    <div class="f"><label>Số lượng</label><input class="dxi-sl" type="number" value="1"></div>
    <div class="f"><label>Đơn giá DK</label><input class="dxi-dg" type="number" value="0"></div>
    <div class="f" style="flex:2"><label>Nhà cung cấp</label><select class="dxi-ncc">${window.DXOPTNCC||''}</select></div>
    <div class="f" style="flex:2"><label>Ghi chú / spec</label><input class="dxi-gc" placeholder="quy cách, ghi chú"></div>
    <button class="btn-sm ghost" onclick="dxDelItem(this)" title="Xóa dòng" style="align-self:center">✕</button></div>`;
}
function dxAddItem(){const w=document.getElementById('dxItems');const d=document.createElement('div');d.innerHTML=_dxItemRowHTML();w.appendChild(d.firstElementChild);}
function dxDelItem(btn){const rows=document.querySelectorAll('#dxItems .dxi-row');if(rows.length<=1){toast("Cần ít nhất 1 sản phẩm","err");return;}btn.closest('.dxi-row').remove();}
async function nccDxTaiDinhKem(id){
  if(S.mode!=="live"){toast("Tải tệp đính kèm chạy ở bản kết nối backend","err");return;}
  try{const h={};if(S.token)h['Authorization']='Bearer '+S.token;
    const r=await fetch(S.api+`/ncc/yeu-cau-mua/${id}/dinh-kem`,{headers:h});
    if(!r.ok){toast("Không tải được tệp","err");return;}
    const blob=await r.blob();const cd=r.headers.get('Content-Disposition')||'';const mm=cd.match(/filename="?([^"]+)"?/);
    const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=(mm?mm[1]:('dinhkem_'+id));document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),4000);
  }catch(e){toast(e.message,"err");}
}
async function nccDxCreate(){
  const items=[];
  document.querySelectorAll('#dxItems .dxi-row').forEach(r=>{
    const hh=Number(r.querySelector('.dxi-hh').value); const sl=Number(r.querySelector('.dxi-sl').value||0);
    const dg=r.querySelector('.dxi-dg').value?Number(r.querySelector('.dxi-dg').value):null;
    const nc=r.querySelector('.dxi-ncc').value?Number(r.querySelector('.dxi-ncc').value):null;
    const gc=r.querySelector('.dxi-gc').value||null;
    if(hh&&sl>0)items.push({hang_hoa_id:hh,so_luong:sl,don_gia:dg,nha_cung_cap_id:nc,ghi_chu:gc});
  });
  if(!items.length){toast("Thêm ít nhất 1 sản phẩm (số lượng > 0)","err");return;}
  const ncc=gv('dx_ncc')?Number(gv('dx_ncc')):null, dh=gv('dx_dh')?Number(gv('dx_dh')):null, can_=gv('dx_can')||null, ly=gv('dx_ly')||null, url=gv('dx_url')||null;
  const fileEl=document.getElementById('dx_file'); const file=fileEl&&fileEl.files&&fileEl.files[0];
  if(S.mode==="live"){ try{
      const r=await api("/ncc/yeu-cau-mua",{method:'POST',body:JSON.stringify({items,nha_cung_cap_id:ncc,don_hang_id:dh,ngay_can:can_,ly_do:ly,dinh_kem_url:url})});
      if(file){const fd=new FormData();fd.append('file',file);try{await apiUpload(`/ncc/yeu-cau-mua/${r.id}/dinh-kem`,fd);}catch(e){toast("Đề xuất đã tạo nhưng tải tệp lỗi: "+(e.detail||e.message),"err");}}
      toast(`Đã gửi đề xuất (${items.length} mặt hàng)`,"ok");viewDeXuat($("#main"));
    }catch(e){toast(e.detail||e.message,"err");} return; }
  const p=items[0]; const hhObj=(DEMO.hang_hoa||[]).find(x=>x.id===p.hang_hoa_id);
  const demoItems=items.map(it=>{const o=(DEMO.hang_hoa||[]).find(h=>h.id===it.hang_hoa_id);return {hang_hoa_id:it.hang_hoa_id,ten_hh:o?o.ten:('HH#'+it.hang_hoa_id),so_luong:it.so_luong,don_gia:it.don_gia,nha_cung_cap_id:it.nha_cung_cap_id,ghi_chu:it.ghi_chu};});
  DEMO.de_xuat.unshift({id:Date.now(),hang_hoa_id:p.hang_hoa_id,ten_hh:hhObj?hhObj.ten:('HH#'+p.hang_hoa_id),so_luong:p.so_luong,don_gia:p.don_gia,nha_cung_cap_id:ncc,don_hang_id:dh,ngay_can:can_,ly_do:ly,trang_thai:"MOI",don_mua_id:null,dinh_kem_url:url,dinh_kem_file:file?('x_'+file.name):null,so_dong:items.length,items:demoItems});
  toast(`Đã gửi đề xuất (demo, ${items.length} mặt hàng)`,"ok"); viewDeXuat($("#main"));
}
async function nccDxDuyet(id){
  if(S.mode==="live"){ try{await api(`/ncc/yeu-cau-mua/${id}/duyet`,{method:'POST'});
    toast("Đã duyệt đề xuất","ok");viewDeXuat($("#main"));}catch(e){toast(e.detail||e.message,"err");} return; }
  const x=DEMO.de_xuat.find(p=>p.id===id); if(x)x.trang_thai="DA_DUYET";
  toast("Đã duyệt (demo)","ok"); viewDeXuat($("#main"));
}
async function nccDxTuChoi(id){
  const ly=prompt("Lý do từ chối:",""); if(ly===null)return;
  if(S.mode==="live"){ try{await api(`/ncc/yeu-cau-mua/${id}/tu-choi`,{method:'POST',body:JSON.stringify({ly_do:ly})});
    toast("Đã từ chối","ok");viewDeXuat($("#main"));}catch(e){toast(e.detail||e.message,"err");} return; }
  const x=DEMO.de_xuat.find(p=>p.id===id); if(x)x.trang_thai="TU_CHOI";
  toast("Đã từ chối (demo)","ok"); viewDeXuat($("#main"));
}
async function nccDxTaoPO(id){
  if(S.mode==="live"){ try{const r=await api(`/ncc/yeu-cau-mua/${id}/tao-po`,{method:'POST',body:JSON.stringify({})});
    toast("Đã tạo PO "+(r.so||"")+" (chờ duyệt)","ok");S.nccTab="po";viewNCC($("#main"));}catch(e){toast(e.detail||e.message,"err");} return; }
  const x=DEMO.de_xuat.find(p=>p.id===id); if(!x)return;
  if(!x.nha_cung_cap_id||!x.don_gia){toast("Đề xuất thiếu NCC hoặc đơn giá dự kiến","err");return;}
  const pid=Date.now();
  DEMO.don_mua.push({id:pid,so:"PO-"+pid,nha_cung_cap_id:x.nha_cung_cap_id,don_hang_id:x.don_hang_id,tong_tien:x.so_luong*x.don_gia,trang_thai:"CHO_DUYET",trang_thai_nhan:"CHUA",ngay_hen_giao:x.ngay_can,
    chi_tiet:[{id:pid+1,hang_hoa_id:x.hang_hoa_id,ten:x.ten_hh,so_luong:x.so_luong,don_gia:x.don_gia,so_luong_nhan:0}]});
  x.trang_thai="DA_TAO_PO"; x.don_mua_id=pid;
  toast("Đã tạo PO (demo) — xem tab Đơn mua","ok"); S.nccTab="po"; viewNCC($("#main"));
}
function _goiYDemo(hid, sl){
  const sups=(DEMO.ncc.suppliers||[]).filter(s=>!s.blacklist); const today=new Date();
  const gls={}; (DEMO.don_mua||[]).forEach(p=>(p.chi_tiet||[]).forEach(ct=>{if(ct.hang_hoa_id===hid)gls[p.nha_cung_cap_id]=ct.don_gia;}));
  const gbg={}; (DEMO.bao_gia||[]).forEach(b=>{if(b.hang_hoa_id===hid && (!b.hieu_luc_den||new Date(b.hieu_luc_den)>=today)){const cur=gbg[b.nha_cung_cap_id]; if(!cur||b.id>cur.id)gbg[b.nha_cung_cap_id]={id:b.id,gia:b.don_gia,hl:b.hieu_luc_den};}});
  const dh={}; (DEMO.don_mua||[]).forEach(p=>{if(p.ngay_giao_thuc&&p.ngay_hen_giao){const t=dh[p.nha_cung_cap_id]||{t:0,d:0};t.t++;if(new Date(p.ngay_giao_thuc)<=new Date(p.ngay_hen_giao))t.d++;dh[p.nha_cung_cap_id]=t;}});
  const giaDung=id=>gbg[id]?gbg[id].gia:(gls[id]||null);
  const prices=sups.map(s=>giaDung(s.id)).filter(Boolean); const gmin=prices.length?Math.min(...prices):null;
  let list=sups.map(s=>{
    const bg=gbg[s.id]; const g=giaDung(s.id); const nguon=bg?"BAO_GIA":(gls[s.id]?"LICH_SU":null);
    const td=dh[s.id]; const tyle=td&&td.t?Math.round(td.d/td.t*1000)/1000:null;
    const du=(DEMO.cong_no_ncc||[]).filter(x=>x.nha_cung_cap_id===s.id).reduce((a,x)=>a+(x.so_tien-(x.da_thanh_toan||0)),0);
    const hm=Number(s.han_muc_cong_no||0); const gtri=g?sl*g:null;
    const trong=(hm===0)||(gtri===null)||(du+gtri<=hm);
    const sg=(g&&gmin)?gmin/g:0.6, sdg=(s.diem_danh_gia||0)/5, sdh=tyle!=null?tyle:0.7;
    let diem=Math.round((100*(0.4*sg+0.3*sdg+0.3*sdh))*10)/10; if(!trong)diem=Math.round((diem-30)*10)/10;
    return {nha_cung_cap_id:s.id,ten:s.ten,gia_gan_nhat:g,gia_dung:g,gia_bao_gia:bg?bg.gia:null,gia_lich_su:gls[s.id]||null,
      nguon_gia:nguon,hieu_luc_den:bg?bg.hl:null,diem_danh_gia:s.diem_danh_gia||0,ty_le_dung_han:tyle,trong_han_muc:trong,diem_tong:diem,khuyen_nghi:false};
  }).sort((a,b)=>b.diem_tong-a.diem_tong);
  const best=list.find(x=>x.trong_han_muc); if(best)best.khuyen_nghi=true;
  return {hang_hoa_id:hid,goi_y_ncc_id:best?best.nha_cung_cap_id:null,danh_sach:list};
}
function dxSupChange(id){
  const sug=(window.DXSUG||{})[id]; if(!sug)return;
  const o=(sug.danh_sach||[]).find(z=>z.nha_cung_cap_id===Number(gv('dxncc_'+id)));
  const g=o?(o.gia_dung||o.gia_gan_nhat):null;
  if(g)$("#dxgia_"+id).value=g;
}
async function nccLuuBaoGia(id){
  const ncc=Number(gv('bg_ncc_'+id)), gia=Number(gv('bg_gia_'+id)||0), hl=gv('bg_hl_'+id)||null;
  const hh=(window.DXHH||{})[id];
  if(!ncc||gia<=0){toast("Chọn NCC và nhập đơn giá chào > 0","err");return;}
  delete (window.DXAI||{})[id];
  if(S.mode==="live"){ try{await api("/ncc/bao-gia",{method:'POST',body:JSON.stringify({nha_cung_cap_id:ncc,hang_hoa_id:hh,don_gia:gia,hieu_luc_den:hl,nguon:"THU_CONG"})});
    toast("Đã lưu báo giá — AI & gợi ý sẽ dùng giá chào này","ok");viewNCC($("#main"));}catch(e){toast(e.detail||e.message,"err");} return; }
  DEMO.bao_gia=DEMO.bao_gia||[]; DEMO.bao_gia.push({id:Date.now(),nha_cung_cap_id:ncc,hang_hoa_id:hh,don_gia:gia,hieu_luc_den:hl,nguon:"THU_CONG"});
  toast("Đã lưu báo giá (demo) — gợi ý đã cập nhật","ok"); viewNCC($("#main"));
}
function rfqAll(id,on){const el=document.getElementById('rfq_ncc_'+id);if(!el)return;Array.from(el.options).forEach(o=>o.selected=on);}
function _rfqFields(id){return {quy_cach:gv('rfq_qc_'+id)||null,don_vi:gv('rfq_dv_'+id)||null,noi_giao:gv('rfq_ng_'+id)||null,thoi_gian_giao:gv('rfq_tg_'+id)||null,dieu_kien_thanh_toan:gv('rfq_tt_'+id)||null,yeu_cau_khac:gv('rfq_yc_'+id)||null,han_bao_gia:gv('rfq_han_'+id)||null};}
function _rfqBodyDemo(o){
  const L=["Kính gửi Quý Nhà cung cấp,",""];
  L.push("Công ty Song Việt Water Solutions (SVWS) trân trọng đề nghị Quý công ty báo giá cho nhu cầu mua sắm sau:","");
  L.push("THÔNG TIN HÀNG HÓA",`- Tên hàng: ${o.ten}`);
  if(o.ma)L.push(`- Mã hàng: ${o.ma}`);
  if(o.quy_cach)L.push(`- Quy cách / thông số: ${o.quy_cach}`);
  L.push(`- Đơn vị tính: ${o.don_vi||'-'}`,`- Số lượng: ${o.so_luong}`,"");
  L.push("YÊU CẦU GIAO HÀNG & THANH TOÁN",
    `- Nơi giao: ${o.noi_giao||'Theo thỏa thuận'}`,
    `- Thời gian giao mong muốn: ${o.thoi_gian_giao||'Theo thỏa thuận'}`,
    `- Điều kiện thanh toán: ${o.dieu_kien_thanh_toan||'Theo thỏa thuận'}`);
  if(o.yeu_cau_khac)L.push(`- Yêu cầu khác: ${o.yeu_cau_khac}`);
  L.push("","NỘI DUNG BÁO GIÁ CẦN CUNG CẤP",
    "1. Đơn giá (ghi rõ đã/chưa gồm VAT) và tổng giá trị.",
    "2. Thời hạn hiệu lực của báo giá.",
    "3. Thời gian giao hàng dự kiến.",
    "4. Điều kiện giao hàng và thanh toán.",
    "5. Chứng từ kèm theo (CO, CQ, catalogue...) nếu có.","");
  L.push(`Vui lòng gửi báo giá${o.han_bao_gia?` trước ngày ${o.han_bao_gia}`:''} về địa chỉ email inf@watersolutions.company.`);
  L.push("Mọi trao đổi xin liên hệ Bộ phận Mua hàng theo email trên.","");
  L.push("Trân trọng cảm ơn sự hợp tác của Quý công ty.","");
  L.push("------------------------------","CÔNG TY SONG VIỆT WATER SOLUTIONS (SVWS)",'"We Have Solutions"',
    "Địa chỉ: 448 Võ Văn Tần, Phường Bàn Cờ, TP. Hồ Chí Minh","Email: inf@watersolutions.company","Bộ phận Mua hàng");
  return L.join("\n");
}
async function nccRfqPreview(id){
  const f=_rfqFields(id); let tieu_de,noi_dung;
  if(S.mode==="live"){ try{const r=await api(`/ncc/yeu-cau-mua/${id}/rfq-preview`,{method:'POST',body:JSON.stringify(f)});tieu_de=r.tieu_de;noi_dung=r.noi_dung;}catch(e){toast(e.detail||e.message,"err");return;} }
  else { const x=DEMO.de_xuat.find(p=>p.id===id)||{}; const hh=(DEMO.hang_hoa||[]).find(h=>h.id===x.hang_hoa_id)||{};
    tieu_de=`[SVWS] Yêu cầu báo giá: ${hh.ten||x.ten_hh||''}`;
    noi_dung=_rfqBodyDemo({ten:hh.ten||x.ten_hh||'',ma:hh.ma,don_vi:f.don_vi||hh.don_vi,so_luong:x.so_luong||'',...f}); }
  const ti=$("#rfq_tieude_"+id), bd=$("#rfq_body_"+id); if(ti)ti.value=tieu_de; if(bd)bd.value=noi_dung;
  toast("Đã tạo nội dung email — kiểm tra/chỉnh trước khi gửi","ok");
}
async function nccGuiRFQ(id){
  const el=document.getElementById('rfq_ncc_'+id); if(!el)return;
  const sel=Array.from(el.selectedOptions).map(o=>Number(o.value));
  if(!sel.length){toast("Chọn ít nhất 1 NCC","err");return;}
  const f=_rfqFields(id); const tieu_de=gv('rfq_tieude_'+id)||null;
  const bd=$("#rfq_body_"+id); const noi_dung=(bd&&bd.value.trim())?bd.value.trim():null;
  if(S.mode==="live"){ try{const r=await api(`/ncc/yeu-cau-mua/${id}/gui-rfq`,{method:'POST',body:JSON.stringify({nha_cung_cap_ids:sel,tieu_de,noi_dung,...f})});
    toast(`Đã gửi RFQ ${r.da_gui}/${r.tong} NCC từ ${r.gui_tu}`,"ok");viewNCC($("#main"));}catch(e){toast(e.detail||e.message,"err");} return; }
  const x=DEMO.de_xuat.find(p=>p.id===id)||{}; const hh=(DEMO.hang_hoa||[]).find(h=>h.id===x.hang_hoa_id)||{};
  const body=noi_dung||_rfqBodyDemo({ten:hh.ten||x.ten_hh||'',ma:hh.ma,don_vi:f.don_vi||hh.don_vi,so_luong:x.so_luong||'',...f});
  const log=sel.map(nid=>{const s=DEMO.ncc.suppliers.find(z=>z.id===nid);return {nha_cung_cap_id:nid,email:s?s.email:null,da_gui:!!(s&&s.email),ket_qua:(s&&s.email)?null:"NCC chưa có email"};});
  DEMO.rfq=DEMO.rfq||[]; DEMO.rfq.unshift({id:Date.now(),hang_hoa_id:x.hang_hoa_id,ten_hh:x.ten_hh||hh.ten,so_luong:x.so_luong||0,han_bao_gia:f.han_bao_gia,gui_tu:"inf@watersolutions.company",ngay:new Date().toISOString().slice(0,10),tieu_de:tieu_de||`[SVWS] Yêu cầu báo giá: ${x.ten_hh||hh.ten||''}`,noi_dung:body,log});
  toast(`Đã gửi RFQ (demo) ${log.filter(l=>l.da_gui).length}/${log.length} NCC`,"ok"); viewNCC($("#main"));
}
function _poBodyDemo(po,f){
  const sup=(DEMO.ncc.suppliers||[]).find(s=>s.id===po.nha_cung_cap_id)||{};
  const today=new Date().toISOString().slice(0,10); const v=x=>vnd(x);
  const L=[`Kính gửi ${sup.ten||'Quý NCC'},`,""];
  L.push("Công ty Song Việt Water Solutions (SVWS) xác nhận đặt hàng theo đơn dưới đây:","");
  L.push("ĐƠN ĐẶT HÀNG (PO)",`- Số PO: ${po.so}`,`- Ngày: ${today}`,`- Nhà cung cấp: ${sup.ten||''}`);
  const ln0=(po.chi_tiet||[])[0];
  const bgs=ln0?(DEMO.bao_gia||[]).filter(b=>b.hang_hoa_id===ln0.hang_hoa_id&&b.nha_cung_cap_id===po.nha_cung_cap_id&&(!b.hieu_luc_den||new Date(b.hieu_luc_den)>=new Date())):[];
  const bg=bgs.length?bgs[bgs.length-1]:null;
  if(bg)L.push(`- Tham chiếu báo giá${bg.hieu_luc_den?`, hiệu lực đến ${bg.hieu_luc_den}`:''}`);
  L.push("","CHI TIẾT HÀNG HÓA"); let tong=0;
  (po.chi_tiet||[]).forEach((ct,i)=>{const hh=(DEMO.hang_hoa||[]).find(h=>h.id===ct.hang_hoa_id)||{};const tt=ct.so_luong*ct.don_gia;tong+=tt;
    L.push(`${i+1}. ${ct.ten||hh.ten} | ĐVT: ${hh.don_vi||''} | SL: ${ct.so_luong} | Đơn giá: ${v(ct.don_gia)} | Thành tiền: ${v(tt)}`);});
  L.push(`Tổng cộng (chưa gồm VAT): ${v(tong)}`,"","ĐIỀU KIỆN");
  L.push(`- Nơi giao: ${f.noi_giao||'448 Võ Văn Tần, Phường Bàn Cờ, TP. Hồ Chí Minh'}`);
  L.push(`- Ngày giao yêu cầu: ${f.ngay_hen_giao||po.ngay_hen_giao||'Theo thỏa thuận'}`);
  L.push(`- Điều kiện giao hàng: ${f.dieu_kien_giao_hang||'Theo thỏa thuận'}`);
  L.push(`- Điều kiện thanh toán: ${f.dieu_kien_thanh_toan||'Theo thỏa thuận'}`);
  if(f.ghi_chu)L.push(`- Ghi chú: ${f.ghi_chu}`);
  L.push("","Đề nghị Quý công ty xác nhận đơn hàng và phản hồi về email inf@watersolutions.company.","");
  L.push("Trân trọng,","------------------------------","CÔNG TY SONG VIỆT WATER SOLUTIONS (SVWS)",'"We Have Solutions"',
    "Địa chỉ: 448 Võ Văn Tần, Phường Bàn Cờ, TP. Hồ Chí Minh","Email: inf@watersolutions.company","Bộ phận Mua hàng");
  return L.join("\n");
}
function _poFields(id){return {noi_giao:gv('po_ng_'+id)||null,dieu_kien_giao_hang:gv('po_gh_'+id)||null,dieu_kien_thanh_toan:gv('po_tt_'+id)||null,ghi_chu:gv('po_gc_'+id)||null,ngay_hen_giao:gv('po_hen_'+id)||null};}
function _poPdfFields(id){const k=document.getElementById('po_kyso_'+id);return {
  ma_yeu_cau:gv('po_ma_'+id)||null, hieu_luc_den:gv('po_hl_'+id)||null, vat:Number(gv('po_vat_'+id)||0),
  nguoi_lien_he:gv('po_nlh_'+id)||null, nguoi_dat:gv('po_ndat_'+id)||null, nguoi_duyet:gv('po_nduyet_'+id)||null,
  ky_so:k?k.checked:true,
  specs:(gv('po_spec_'+id)||'').split('|').map(s=>s.trim()).filter(Boolean),
  noi_giao:gv('po_ng_'+id)||null, thoi_gian_giao:gv('po_tgg_'+id)||null,
  dieu_kien_thanh_toan:gv('po_tt_'+id)||null, ngay_hen_giao:gv('po_hen_'+id)||null, ghi_chu:gv('po_gc_'+id)||null };}
async function nccPoPdf(poId){
  if(S.mode!=="live"){toast("Xuất PDF chạy ở bản kết nối backend (reportlab). Mẫu: PO_mau_SVWS.pdf","err");return;}
  const data=_poPdfFields(poId);
  try{
    const h={'Content-Type':'application/json'}; if(S.token)h['Authorization']='Bearer '+S.token;
    const r=await fetch(S.api+`/ncc/don-mua/${poId}/po-pdf`,{method:'POST',headers:h,body:JSON.stringify(data)});
    if(!r.ok){const t=await r.text();toast("Lỗi xuất PDF: "+t.slice(0,120),"err");return;}
    const blob=await r.blob(); const url=URL.createObjectURL(blob);
    const a=document.createElement('a'); a.href=url; a.download=`PO_${poId}.pdf`; document.body.appendChild(a); a.click(); a.remove();
    setTimeout(()=>URL.revokeObjectURL(url),4000); toast("Đã xuất & lưu PDF chứng từ PO","ok");
  }catch(e){toast(e.message,"err");}
}
async function nccPoSend(poId){
  const old=document.getElementById('poModal'); if(old)old.remove();
  const fld=`<div class="formrow">
      <div class="f"><label>Mã yêu cầu (PO)</label><input id="po_ma_${poId}" placeholder="(mặc định lấy số PO)"></div>
      <div class="f"><label>Hiệu lực đến</label><input id="po_hl_${poId}" placeholder="dd/mm/yyyy"></div>
      <div class="f"><label>VAT (%)</label><input id="po_vat_${poId}" type="number" value="8" style="width:90px"></div></div>
    <div class="formrow">
      <div class="f"><label>Nơi giao hàng</label><input id="po_ng_${poId}" value="448 Võ Văn Tần, P. Bàn Cờ, TP.HCM"></div>
      <div class="f"><label>Ngày hẹn giao</label><input id="po_hen_${poId}" type="date"></div>
      <div class="f"><label>Thời gian giao hàng</label><input id="po_tgg_${poId}" value="7-10 ngày làm việc"></div></div>
    <div class="formrow">
      <div class="f"><label>Điều kiện giao hàng</label><input id="po_gh_${poId}" placeholder="VD: giao tại kho công trình, NCC chịu vận chuyển"></div>
      <div class="f"><label>Điều kiện thanh toán</label><input id="po_tt_${poId}" value="Thanh toán trong 30 ngày sau khi nhận hàng"></div></div>
    <div class="f"><label>Mô tả / Spec từng dòng (cách nhau bằng dấu |)</label><input id="po_spec_${poId}" placeholder="VD: Dung dịch lỏng trong, màu Vàng nhạt | spec dòng 2"></div>
    <div class="formrow">
      <div class="f"><label>Người liên hệ NCC</label><input id="po_nlh_${poId}"></div>
      <div class="f"><label>Người đặt hàng</label><input id="po_ndat_${poId}"></div>
      <div class="f"><label>Người duyệt</label><input id="po_nduyet_${poId}"></div></div>
    <div class="f"><label>Ghi chú</label><input id="po_gc_${poId}"></div>
    <div style="margin:6px 0"><label style="font-weight:normal;font-size:13px"><input type="checkbox" id="po_kyso_${poId}" checked> Ký số &amp; đóng dấu công ty (Nguyễn Lê Hiếu) vào PDF</label></div>
    <div style="margin:6px 0"><button class="btn-sm ghost" onclick="nccPoPreview(${poId})">👁 Xem trước email</button>
      <button class="btn-sm ghost" onclick="nccPoPdf(${poId})">📄 Tải PDF (lưu chứng từ)</button></div>
    <div class="f"><label>Tiêu đề email</label><input id="po_tieude_${poId}"></div>
    <div class="f"><label>Nội dung email (có thể chỉnh sửa)</label><textarea id="po_body_${poId}" rows="9" style="width:100%;font-family:inherit"></textarea></div>`;
  const wrap=document.createElement('div'); wrap.id='poModal';
  wrap.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.45);display:flex;align-items:center;justify-content:center;z-index:9999';
  wrap.onclick=e=>{if(e.target===wrap)wrap.remove();};
  const box=document.createElement('div');
  box.style.cssText='background:var(--surface,#fff);max-width:720px;width:94%;max-height:88vh;overflow:auto;border-radius:12px;padding:16px 18px';
  box.innerHTML=`<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
      <div style="font-weight:700;flex:1">📄 Đơn đặt hàng (PO) <span id="po_so_${poId}"></span></div>
      <button class="btn-sm ghost" onclick="document.getElementById('poModal').remove()">Đóng</button></div>
    <div id="po_to_${poId}" style="font-size:12px;color:var(--muted);margin-bottom:8px"></div>
    ${fld}
    <button class="btn-sm" onclick="nccGuiPO(${poId})">✉️ Gửi PO cho NCC (kèm PDF)</button>`;
  wrap.appendChild(box); document.body.appendChild(wrap);
  await nccPoPreview(poId);
}
async function nccPoPreview(poId){
  const f=_poFields(poId); let tieu_de,noi_dung,email,so,hen;
  if(S.mode==="live"){ try{const r=await api(`/ncc/don-mua/${poId}/po-preview`,{method:'POST',body:JSON.stringify(f)});tieu_de=r.tieu_de;noi_dung=r.noi_dung;email=r.email;so=r.so;hen=r.ngay_hen_giao;}catch(e){toast(e.detail||e.message,"err");return;} }
  else { const po=(DEMO.don_mua||[]).find(p=>p.id===poId); if(!po)return; const sup=(DEMO.ncc.suppliers||[]).find(s=>s.id===po.nha_cung_cap_id)||{};
    tieu_de=`[SVWS] Đơn đặt hàng ${po.so}`; noi_dung=_poBodyDemo(po,f); email=sup.email; so=po.so; hen=po.ngay_hen_giao; }
  const $so=$("#po_so_"+poId); if($so)$so.textContent=so?('· '+so):'';
  const $to=$("#po_to_"+poId); if($to)$to.innerHTML= email?`Gửi tới: <b>${email}</b> · từ inf@watersolutions.company`:`<span style="color:#dc2626">NCC chưa có email — không gửi được. Hãy bổ sung email NCC trước.</span>`;
  const ti=$("#po_tieude_"+poId), bd=$("#po_body_"+poId), hd=$("#po_hen_"+poId);
  if(ti)ti.value=tieu_de; if(bd)bd.value=noi_dung; if(hd&&hen&&!hd.value)hd.value=hen;
}
async function nccGuiPO(poId){
  const f=_poFields(poId); const pf=_poPdfFields(poId); const tieu_de=gv('po_tieude_'+poId)||null; const bd=$("#po_body_"+poId); const noi_dung=(bd&&bd.value.trim())?bd.value.trim():null;
  if(S.mode==="live"){ try{const r=await api(`/ncc/don-mua/${poId}/gui-po`,{method:'POST',body:JSON.stringify({...pf,dieu_kien_giao_hang:f.dieu_kien_giao_hang,tieu_de,noi_dung,dinh_kem_pdf:true})});
    if(r.da_gui){toast(`Đã gửi PO tới ${r.email} từ ${r.gui_tu}${r.co_pdf?' (kèm PDF)':''}`,"ok");const m=document.getElementById('poModal');if(m)m.remove();viewNCC($("#main"));}
    else toast(r.ly_do||"Không gửi được (NCC thiếu email)","err");}catch(e){toast(e.detail||e.message,"err");} return; }
  const po=(DEMO.don_mua||[]).find(p=>p.id===poId); const sup=(DEMO.ncc.suppliers||[]).find(s=>s.id===(po&&po.nha_cung_cap_id))||{};
  if(f.ngay_hen_giao&&po)po.ngay_hen_giao=f.ngay_hen_giao;
  if(!sup.email){toast("NCC chưa có email — không gửi được","err");return;}
  toast(`Đã gửi PO (demo) tới ${sup.email} từ inf@watersolutions.company (kèm PDF ở bản backend)`,"ok");
  const m=document.getElementById('poModal');if(m)m.remove(); viewNCC($("#main"));
}
async function nccBaoGia(host){
  const sups=await _nccSups();
  let hhs = S.mode==="live" ? await api("/kho/hang-hoa").catch(()=>[]) : DEMO.hang_hoa;
  let quotes, rfqs;
  if(S.mode==="live"){ try{quotes=await api("/ncc/bao-gia");}catch(e){toast(e.detail||e.message,"err");quotes=[];} try{rfqs=await api("/ncc/rfq");}catch{rfqs=[];} }
  else { quotes=(DEMO.bao_gia||[]); rfqs=(DEMO.rfq||[]); }
  const hhName=id=>{const h=hhs.find(x=>x.id===id);return h?h.ten:("HH #"+id);};
  const supName=id=>{const s=sups.find(x=>x.id===id);return s?s.ten:("NCC #"+id);};
  const today=new Date();
  const tt=q=>{ if(!q.hieu_luc_den)return {lbl:"Không hạn",cls:"b-info",d:99999}; const d=Math.floor((new Date(q.hieu_luc_den)-today)/864e5); return d<0?{lbl:"Hết hạn",cls:"b-tc",d}:d<=7?{lbl:`Sắp hết hạn (${d} ngày)`,cls:"b-cho",d}:{lbl:"Còn hiệu lực",cls:"b-ok",d}; };
  const en=quotes.map(q=>({...q,_tt:tt(q)})); const sapHet=en.filter(q=>q._tt.d>=0&&q._tt.d<=7).length; const hetHan=en.filter(q=>q._tt.d<0).length;
  const canAdd=can("ncc","THAO_TAC");
  const rows=en.sort((a,b)=>a._tt.d-b._tt.d).map(q=>`<tr class="${q._tt.d<0?'qh':''}"><td>${hhName(q.hang_hoa_id)}</td><td>${supName(q.nha_cung_cap_id)}</td>
    <td class="num">${vnd(q.don_gia)}</td><td class="num">${Number(q.so_luong_toi_thieu||0)}</td>
    <td>${q.hieu_luc_den||'—'}</td><td><span class="badge b-info">${q.nguon||'THU_CONG'}</span></td>
    <td><span class="badge ${q._tt.cls}">${q._tt.lbl}</span></td></tr>`).join('');
  const form=canAdd?`<div id="bgForm2" class="formrow hidden">
    <div class="f" style="flex:2"><label>Hàng hóa</label><select id="bg2_hh">${hhs.map(h=>`<option value="${h.id}">${h.ten}</option>`).join('')}</select></div>
    <div class="f" style="flex:2"><label>NCC</label><select id="bg2_ncc">${sups.map(s=>`<option value="${s.id}">${s.ten}</option>`).join('')}</select></div>
    <div class="f"><label>Đơn giá</label><input id="bg2_gia" type="number" value="0"></div>
    <div class="f"><label>SL tối thiểu</label><input id="bg2_min" type="number" value="0"></div>
    <div class="f"><label>Hiệu lực đến</label><input id="bg2_hl" type="date"></div>
    <button class="btn-sm" onclick="nccBgCreate()">Lưu</button></div>`:'';
  const rfqRows=(rfqs||[]).map(r=>{const log=r.log||null;
    return `<tr><td>${r.ten_hh||hhName(r.hang_hoa_id)}</td><td class="num">${Number(r.so_luong||0)}</td>
      <td>${r.ngay||'—'}</td><td>${r.han_bao_gia||'—'}</td><td>${r.gui_tu||''}</td>
      <td>${log?`${log.filter(l=>l.da_gui).length}/${log.length} NCC`:'<span style="color:var(--muted)">đã gửi</span>'}</td>
      <td><button class="btn-sm ghost" onclick="nccRfqXem(${r.id})">Xem email</button></td></tr>`;}).join('');
  host.innerHTML=`<div style="display:flex;flex-wrap:wrap;gap:8px;padding:0 0 12px">
      <div style="flex:1;min-width:150px;background:var(--surface);border-radius:10px;padding:10px 12px"><div style="color:var(--muted);font-size:12px">Tổng báo giá</div><div style="font-weight:700">${en.length}</div></div>
      <div style="flex:1;min-width:150px;background:#fff7ed;border-radius:10px;padding:10px 12px"><div style="color:#b45309;font-size:12px">Sắp hết hạn (≤7 ngày)</div><div style="font-weight:700">${sapHet}</div></div>
      <div style="flex:1;min-width:150px;background:var(--red-bg);border-radius:10px;padding:10px 12px"><div style="color:#b91c1c;font-size:12px">Đã hết hạn</div><div style="font-weight:700">${hetHan}</div></div></div>
    <div class="panel"><div class="panel-h"><h3>Báo giá theo mặt hàng / NCC</h3><div class="spacer"></div>
      ${canAdd?`<button class="btn-sm" onclick="$('#bgForm2').classList.toggle('hidden')">+ Báo giá</button>`:''}</div>
      ${form}
      <div class="panel-b"><table><thead><tr><th>Hàng hóa</th><th>NCC</th><th class="num">Đơn giá</th><th class="num">SL tối thiểu</th><th>Hiệu lực đến</th><th>Nguồn</th><th>Trạng thái</th></tr></thead>
      <tbody>${rows||'<tr><td colspan="7" class="empty" style="padding:20px">Chưa có báo giá.</td></tr>'}</tbody></table></div></div>
    <div class="panel"><div class="panel-h"><h3>Nhật ký RFQ — gửi từ inf@watersolutions.company</h3></div>
      <div class="panel-b"><table><thead><tr><th>Hàng hóa</th><th class="num">SL</th><th>Ngày gửi</th><th>Hạn báo giá</th><th>Đầu mối</th><th>Đã gửi</th><th>Email</th></tr></thead>
      <tbody>${rfqRows||'<tr><td colspan="7" class="empty" style="padding:18px">Chưa gửi RFQ nào. Gửi từ panel “chờ tạo PO” (nút ✉️ RFQ).</td></tr>'}</tbody></table></div></div>`;
}
function _emailModal(tieu_de,noi_dung){
  const old=document.getElementById('emailModal'); if(old)old.remove();
  const wrap=document.createElement('div'); wrap.id='emailModal';
  wrap.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.45);display:flex;align-items:center;justify-content:center;z-index:9999';
  wrap.onclick=e=>{if(e.target===wrap)wrap.remove();};
  const box=document.createElement('div');
  box.style.cssText='background:var(--surface,#fff);max-width:680px;width:92%;max-height:84vh;overflow:auto;border-radius:12px;padding:16px 18px;box-shadow:0 10px 40px rgba(0,0,0,.25)';
  box.innerHTML=`<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
      <div style="font-weight:700;flex:1">${tieu_de||'Email hỏi giá'}</div>
      <button class="btn-sm ghost" onclick="document.getElementById('emailModal').remove()">Đóng</button></div>
    <div style="font-size:12px;color:var(--muted);margin-bottom:8px">Gửi từ inf@watersolutions.company</div>
    <pre style="white-space:pre-wrap;font-family:inherit;font-size:13px;line-height:1.5;margin:0;background:var(--bg,#f8fafc);padding:12px;border-radius:8px">${(noi_dung||'(không có nội dung)').replace(/</g,'&lt;')}</pre>`;
  wrap.appendChild(box); document.body.appendChild(wrap);
}
async function nccRfqXem(id){
  if(S.mode==="live"){ try{const r=await api(`/ncc/rfq/${id}`);_emailModal(r.tieu_de||"Email hỏi giá",r.noi_dung);}catch(e){toast(e.detail||e.message,"err");} return; }
  const r=(DEMO.rfq||[]).find(x=>x.id===id); if(!r){toast("Không tìm thấy RFQ","err");return;}
  _emailModal(r.tieu_de||"Email hỏi giá",r.noi_dung);
}
async function nccBgCreate(){
  const hh=Number(gv('bg2_hh')),ncc=Number(gv('bg2_ncc')),gia=Number(gv('bg2_gia')||0),mn=Number(gv('bg2_min')||0),hl=gv('bg2_hl')||null;
  if(!hh||!ncc||gia<=0){toast("Chọn hàng hóa, NCC và đơn giá > 0","err");return;}
  if(S.mode==="live"){ try{await api("/ncc/bao-gia",{method:'POST',body:JSON.stringify({hang_hoa_id:hh,nha_cung_cap_id:ncc,don_gia:gia,so_luong_toi_thieu:mn,hieu_luc_den:hl,nguon:"THU_CONG"})});
    toast("Đã lưu báo giá","ok");viewNCC($("#main"));}catch(e){toast(e.detail||e.message,"err");} return; }
  DEMO.bao_gia=DEMO.bao_gia||[]; DEMO.bao_gia.push({id:Date.now(),hang_hoa_id:hh,nha_cung_cap_id:ncc,don_gia:gia,so_luong_toi_thieu:mn,hieu_luc_den:hl,nguon:"THU_CONG"});
  toast("Đã lưu báo giá (demo)","ok"); viewNCC($("#main"));
}
async function nccDxTaoPOChon(id){
  const ncc=Number(gv('dxncc_'+id)), gia=Number(gv('dxgia_'+id)||0), hen=gv('dxhen_'+id)||null;
  if(!ncc){toast("Chọn nhà cung cấp","err");return;}
  if(gia<=0){toast("Nhập đơn giá","err");return;}
  if(S.mode==="live"){ try{const r=await api(`/ncc/yeu-cau-mua/${id}/tao-po`,{method:'POST',body:JSON.stringify({nha_cung_cap_id:ncc,don_gia:gia,ngay_hen_giao:hen})});
    const n=r.so_po||1; toast(n>1?`Đã tạo ${n} PO (tách theo NCC)`:("Đã tạo PO "+((r.po&&r.po[0]&&r.po[0].so)||"")),"ok");
    S.nccTab="po";viewNCC($("#main")); if(n===1 && r.po && r.po[0]) nccPoSend(r.po[0].id);
  }catch(e){toast(e.detail||e.message,"err");} return; }
  const x=DEMO.de_xuat.find(p=>p.id===id); if(!x)return;
  const items=(x.items&&x.items.length)?x.items:[{hang_hoa_id:x.hang_hoa_id,ten_hh:x.ten_hh,so_luong:x.so_luong,don_gia:gia,nha_cung_cap_id:ncc}];
  const groups={};
  items.forEach((it,i)=>{const nid=it.nha_cung_cap_id||ncc; const g=(i===0?gia:(it.don_gia||gia)); (groups[nid]=groups[nid]||[]).push({hang_hoa_id:it.hang_hoa_id,ten:it.ten_hh,so_luong:it.so_luong,don_gia:it.don_gia||g});});
  const newPo=[]; let base=Date.now();
  Object.keys(groups).forEach((nidStr,gi)=>{const nid=Number(nidStr); const pid=base+gi*100;
    const chi=groups[nidStr].map((ct,k)=>({id:pid+1+k,hang_hoa_id:ct.hang_hoa_id,ten:ct.ten,so_luong:ct.so_luong,don_gia:ct.don_gia,so_luong_nhan:0}));
    const tong=chi.reduce((a,ct)=>a+ct.so_luong*ct.don_gia,0);
    DEMO.don_mua.push({id:pid,so:"PO-"+pid,nha_cung_cap_id:nid,don_hang_id:x.don_hang_id,tong_tien:tong,trang_thai:"CHO_DUYET",trang_thai_nhan:"CHUA",ngay_hen_giao:hen||x.ngay_can,chi_tiet:chi});
    newPo.push(pid);});
  x.trang_thai="DA_TAO_PO"; x.don_mua_id=newPo[0];
  toast(newPo.length>1?`Đã tạo ${newPo.length} PO (demo, tách theo NCC)`:"Đã tạo PO (demo)","ok");
  S.nccTab="po"; viewNCC($("#main")); if(newPo.length===1)nccPoSend(newPo[0]);
}
function _ungVienNganhDemo(ten){
  const t=(ten||"").toLowerCase(); const g=[];
  if(/hóa chất|hoa chat|pac|pam|clo|polymer|khử|phèn|naoh/.test(t)) g.push(["Nhà phân phối hóa chất xử lý nước","Kiểm chứng GPKD hóa chất, MSDS/COA, nguồn gốc lô."]);
  if(/bơm|bom|pump/.test(t)) g.push(["Đại lý bơm công nghiệp (Ebara/Grundfos/Pentax/Wilo)","Kiểm chứng chính hãng, bảo hành, sẵn hàng."]);
  if(/màng|mang|mbr| ro |^ro|uf|nf|swro/.test(t)) g.push(["NCC màng lọc (Toray/DOW/Hydranautics/LG)","Kiểm chứng chính hãng, model, lead time."]);
  if(/van|valve|ống|ong|phụ kiện|phu kien/.test(t)) g.push(["NCC van & vật tư đường ống","Kiểm chứng tiêu chuẩn vật liệu, áp lực, chứng chỉ."]);
  if(!g.length) g.push(["NCC vật tư xử lý nước tổng hợp","Kiểm chứng năng lực, hồ sơ pháp lý & báo giá."]);
  return g.map(x=>({ten:x[0],ghi_chu:x[1]}));
}
function _aiSourceDemo(x){
  const sug=_goiYDemo(x.hang_hoa_id, Number(x.so_luong)); const list=sug.danh_sach;
  const trong=list.filter(u=>u.trong_han_muc); const best=trong[0]||list[0];
  const rui=[];
  if(best&&!best.trong_han_muc) rui.push("NCC điểm cao nhất đang vượt/sát hạn mức công nợ — cân nhắc thanh toán bớt trước.");
  if(list.length<=1) rui.push("Chỉ có 1 nguồn cung nội bộ — nên mời thêm báo giá để có phương án thay thế.");
  const over=list.filter(u=>!u.trong_han_muc).map(u=>u.ten);
  if(over.length) rui.push("NCC rẻ nhưng vượt hạn mức công nợ: "+over.join(", ")+".");
  let ly="";
  if(best){const p=[]; if(best.gia_gan_nhat)p.push("giá gần nhất "+vnd(best.gia_gan_nhat)); if(best.diem_danh_gia)p.push("đánh giá "+best.diem_danh_gia.toFixed(1)+"/5"); if(best.ty_le_dung_han!=null)p.push("đúng hạn "+Math.round(best.ty_le_dung_han*100)+"%"); ly="Đề xuất chọn "+best.ten+" (điểm "+best.diem_tong+"): "+p.join(", ")+".";}
  const top=list.slice(0,3).map(u=>u.ten);
  return {khuyen_nghi_ncc_id:best?best.nha_cung_cap_id:null,ten_khuyen_nghi:best?best.ten:null,ly_do:ly,rui_ro:rui,
    hanh_dong:top.length?("Gửi yêu cầu báo giá (RFQ) tới: "+top.join(", ")+"."):"Bổ sung hồ sơ NCC cho mặt hàng này.",
    ung_vien_moi:_ungVienNganhDemo(x.ten_hh||""),nguon:"DEMO"};
}
async function nccDxAI(id){
  let res;
  if(S.mode==="live"){ try{const r=await api(`/ncc/yeu-cau-mua/${id}/tim-ncc-ai`,{method:'POST',body:JSON.stringify({})}); res=r.ai||r;}catch(e){toast(e.detail||e.message,"err");return;} }
  else { const x=DEMO.de_xuat.find(p=>p.id===id); if(!x)return; res=_aiSourceDemo(x); }
  window.DXAI=window.DXAI||{}; window.DXAI[id]=res;
  toast("AI đã phân tích nguồn cung — đã chọn NCC khuyến nghị","ok"); viewNCC($("#main"));
}
function _webDemo(x){
  return {kha_dung:false,nguon:"DEMO",
    thong_bao:"Đang ở chế độ demo. Bật AI_PROVIDER=ANTHROPIC + web search để dò NCC mới trên web. Dưới đây là nhóm nguồn nên tìm:",
    ung_vien:_ungVienNganhDemo(x.ten_hh||"").map(u=>({ten:u.ten,website:"",ghi_chu:u.ghi_chu,nguon_url:"",kiem_chung:false}))};
}
async function nccDxWeb(id){
  let res;
  if(S.mode==="live"){ try{res=await api(`/ncc/yeu-cau-mua/${id}/tim-ncc-web`,{method:'POST',body:JSON.stringify({})});}catch(e){toast(e.detail||e.message,"err");return;} }
  else { const x=DEMO.de_xuat.find(p=>p.id===id); if(!x)return; res=_webDemo(x); }
  window.DXWEB=window.DXWEB||{}; window.DXWEB[id]=res;
  toast(res.kha_dung?"Đã dò NCC trên web":"Web search chưa bật — hiện nhóm nguồn gợi ý","ok"); viewNCC($("#main"));
}
async function nccThemNccTuWeb(ten,website){
  if(!ten){toast("Thiếu tên NCC","err");return;}
  const payload={ma:null,ten,email:website||null,ghi_chu:"Nguồn web — cần kiểm chứng"};
  if(S.mode==="live"){ try{await api("/ncc/nha-cung-cap",{method:'POST',body:JSON.stringify(payload)});
    toast("Đã thêm vào hồ sơ NCC (cần kiểm chứng)","ok");viewNCC($("#main"));}catch(e){toast(e.detail||e.message,"err");} return; }
  DEMO.ncc.suppliers.push({id:Date.now(),ma:"WEB",ten,email:website||null,han_muc_cong_no:0,diem_danh_gia:0,blacklist:false});
  toast("Đã thêm vào hồ sơ NCC (demo) — cần kiểm chứng","ok"); viewNCC($("#main"));
}

/* --- Tab Đơn mua (PO): tạo · duyệt · nhận hàng --- */
async function nccPO(host){
  const sups=await _nccSups(), orders=await _nccOrders();
  let hhs = S.mode==="live" ? await api("/kho/hang-hoa").catch(()=>[]) : DEMO.hang_hoa;
  let pos;
  if(S.mode==="live"){ try{pos=await api("/ncc/don-mua");}catch(e){toast(e.detail||e.message,"err");pos=[];} }
  else pos=DEMO.don_mua;
  let dxDuyet;
  if(S.mode==="live"){ try{dxDuyet=await api("/ncc/yeu-cau-mua?trang_thai=DA_DUYET");}catch{dxDuyet=[];} }
  else dxDuyet=(DEMO.de_xuat||[]).filter(x=>x.trang_thai==="DA_DUYET");
  const hhName=id=>{const h=hhs.find(x=>x.id===id);return h?h.ten:("HH #"+id);};
  const supName=id=>{const s=sups.find(x=>x.id===id);return s?s.ten:("NCC #"+id);};
  const ordNo=id=>{if(!id)return '—';const o=orders.find(x=>x.id===id);return o?(o.so||('DH-'+id)):('Đơn #'+id);};
  const canApprove=can("ncc","XEM")&&HANMUC.po[S.role]!==undefined;
  const stt=s=>s==="DA_DUYET"?'<span class="badge b-ok">Đã duyệt</span>':s==="TU_CHOI"?'<span class="badge b-tc">Từ chối</span>':'<span class="badge b-cho">Chờ duyệt</span>';
  const nhanBadge=n=>n==="DU"?'<span class="badge b-ok">Đủ</span>':n==="MOT_PHAN"?'<span class="badge b-cho">Một phần</span>':'<span class="badge b-info">Chưa</span>';
  const rows=pos.map(p=>{
    let act='';
    if(p.trang_thai==="CHO_DUYET") act+=canApprove?`<button class="btn-sm" onclick="duyetPO(${p.id},${Number(p.tong_tien)})">Duyệt</button> `:`<button class="btn-sm" disabled title="Không có quyền duyệt">Duyệt</button> `;
    if(p.trang_thai==="DA_DUYET" && p.trang_thai_nhan!=="DU" && can("kho","THAO_TAC")) act+=`<button class="btn-sm ghost" onclick="nccRecvOpen(${p.id})">Nhận hàng</button>`;
    if(can("ncc","THAO_TAC")) act+=` <button class="btn-sm ghost" onclick="nccPoSend(${p.id})">Gửi PO</button>`;
    return `<tr><td><b>${p.so||('PO-'+p.id)}</b></td><td>${supName(p.nha_cung_cap_id)}</td>
      <td>${ordNo(p.don_hang_id)}</td><td class="num">${vnd(Number(p.tong_tien))}</td>
      <td>${stt(p.trang_thai)}</td><td>${nhanBadge(p.trang_thai_nhan)}</td><td>${act||'—'}</td></tr>`;
  }).join('');
  const createForm = can("ncc","THAO_TAC") ? `<div class="panel"><div class="panel-h"><h3>Tạo đơn mua (PO)</h3><div class="spacer"></div>
      <button class="btn-sm" onclick="$('#poForm').classList.toggle('hidden')">+ Tạo PO</button></div>
    <div id="poForm" class="hidden" style="padding:0 18px 14px">
     <div class="formrow"><div class="f"><label>Nhà cung cấp</label><select id="po_ncc">${sups.map(s=>`<option value="${s.id}">${s.ten}</option>`).join('')}</select></div>
       <div class="f"><label>Mã đơn bán (tùy chọn)</label><select id="po_dh"><option value="">— không gắn —</option>${orders.map(o=>`<option value="${o.id}">${o.so||('DH-'+o.id)}</option>`).join('')}</select></div>
       <div class="f"><label>Ngày hẹn giao</label><input id="po_hen" type="date"></div></div>
     <div class="formrow" style="padding-top:0"><div class="f" style="flex:2"><label>Hàng hóa</label><select id="po_hh">${hhs.map(h=>`<option value="${h.id}">${h.ten}</option>`).join('')}</select></div>
       <div class="f"><label>Số lượng</label><input id="po_sl" type="number" value="1"></div>
       <div class="f"><label>Đơn giá</label><input id="po_dg" type="number" value="0"></div>
       <button class="btn-sm" onclick="poCreate()">Lưu PO</button></div></div></div>` : '';
  const recvPanel = S.poRecv ? await nccRecvPanel(S.poRecv) : '';
  const canOp=can("ncc","THAO_TAC");
  // Gợi ý NCC tối ưu cho từng đề xuất
  const DXSUG={};
  for(const x of dxDuyet){
    let sug=null;
    if(S.mode==="live"){ try{sug=await api(`/ncc/goi-y-ncc?hang_hoa_id=${x.hang_hoa_id}&so_luong=${x.so_luong}`);}catch{sug=null;} }
    else sug=_goiYDemo(x.hang_hoa_id, Number(x.so_luong));
    DXSUG[x.id]=sug;
  }
  window.DXSUG=DXSUG;
  const dxRows=dxDuyet.map(x=>{
    const sug=DXSUG[x.id];
    window.DXHH=window.DXHH||{}; window.DXHH[x.id]=x.hang_hoa_id;
    let ai=(window.DXAI||{})[x.id];
    if(!ai){ if(x.ai_goi_y){try{ai=JSON.parse(x.ai_goi_y).ai;}catch{}} else if(S.mode!=="live"){ai=_aiSourceDemo(x);} }
    const web=(window.DXWEB||{})[x.id];
    const recId = (ai&&ai.khuyen_nghi_ncc_id) || x.ai_ncc_id || (sug ? sug.goi_y_ncc_id : null);
    const defNcc = recId || x.nha_cung_cap_id || (sups[0]&&sups[0].id);
    const cand = (sug&&sug.danh_sach&&sug.danh_sach.length) ? sug.danh_sach
      : sups.map(s=>({nha_cung_cap_id:s.id,ten:s.ten,khuyen_nghi:false,gia_gan_nhat:null,diem_danh_gia:Number(s.diem_danh_gia||0),ty_le_dung_han:null,trong_han_muc:true}));
    const opts = cand.map(o=>{
      const tag=o.khuyen_nghi?' ⭐':'';
      const gtxt=o.gia_dung?((o.nguon_gia==="BAO_GIA"?"BG ":"")+vnd(o.gia_dung)+(o.hieu_luc_den?` (HL ${o.hieu_luc_den})`:"")):null;
      const metric=[gtxt, o.diem_danh_gia?o.diem_danh_gia.toFixed(1)+'★':null,
        o.ty_le_dung_han!=null?Math.round(o.ty_le_dung_han*100)+'% đúng hạn':null, !o.trong_han_muc?'vượt HM':null].filter(Boolean).join(' · ');
      return `<option value="${o.nha_cung_cap_id}" ${o.nha_cung_cap_id===defNcc?'selected':''}>${o.ten}${tag}${metric?(' — '+metric):''}</option>`;
    }).join('');
    const recObj = (sug&&recId)?(sug.danh_sach.find(o=>o.nha_cung_cap_id===recId)||{}):{};
    const defGia = (recObj.gia_dung)||(recObj.gia_gan_nhat)||x.don_gia||0;
    const mainRow=`<tr><td>${x.ten_hh||hhName(x.hang_hoa_id)}</td><td class="num">${Number(x.so_luong)}</td>
      <td>${ordNo(x.don_hang_id)}</td>
      <td><select id="dxncc_${x.id}" onchange="dxSupChange(${x.id})" style="max-width:280px">${opts}</select>
        ${recObj.ten?`<div style="font-size:11px;color:#16a34a;margin-top:2px">Gợi ý tối ưu: ${recObj.ten}${recObj.diem_tong!=null?` (điểm ${recObj.diem_tong})`:''}${recObj.nguon_gia==="BAO_GIA"?' · theo báo giá':''}</div>`:''}</td>
      <td><input id="dxgia_${x.id}" type="number" value="${defGia}" style="width:120px"></td>
      <td><input id="dxhen_${x.id}" type="date" value="${x.ngay_can||''}" style="width:150px"></td>
      <td style="white-space:nowrap"><button class="btn-sm ghost" onclick="nccDxAI(${x.id})">🤖 AI</button>
        <button class="btn-sm ghost" onclick="nccDxWeb(${x.id})">🌐 Web</button>
        ${canOp?`<button class="btn-sm ghost" onclick="$('#dxbg_${x.id}').classList.toggle('hidden')">💲 Báo giá</button>`:''}
        ${canOp?`<button class="btn-sm ghost" onclick="$('#dxrfq_${x.id}').classList.toggle('hidden')">✉️ RFQ</button>`:''}
        ${canOp?`<button class="btn-sm" onclick="nccDxTaoPOChon(${x.id})">Tạo PO</button>`:''}</td></tr>`;
    let bgForm='';
    if(canOp){
      bgForm=`<tr id="dxbg_${x.id}" class="hidden"><td colspan="7" style="background:#fffbea">
        <div style="padding:8px 10px;display:flex;flex-wrap:wrap;gap:10px;align-items:end">
          <div class="f"><label>Nhà cung cấp</label><select id="bg_ncc_${x.id}">${sups.map(s=>`<option value="${s.id}" ${s.id===defNcc?'selected':''}>${s.ten}</option>`).join('')}</select></div>
          <div class="f"><label>Đơn giá chào</label><input id="bg_gia_${x.id}" type="number" value="${x.don_gia||0}" style="width:130px"></div>
          <div class="f"><label>Hiệu lực đến</label><input id="bg_hl_${x.id}" type="date" style="width:150px"></div>
          <button class="btn-sm" onclick="nccLuuBaoGia(${x.id})">Lưu báo giá</button>
          <span style="color:var(--muted);font-size:12px">Lưu xong, AI & gợi ý sẽ tự dùng giá chào còn hiệu lực này.</span>
        </div></td></tr>`;
    }
    let rfqForm='';
    if(canOp){
      const topIds = (sug&&sug.danh_sach)?sug.danh_sach.slice(0,3).map(o=>o.nha_cung_cap_id):[];
      const optNcc = sups.map(s=>`<option value="${s.id}" ${topIds.includes(s.id)?'selected':''}>${s.ten} — ${s.email||'(chưa có email)'}</option>`).join('');
      rfqForm=`<tr id="dxrfq_${x.id}" class="hidden"><td colspan="7" style="background:#eef6ff">
        <div style="padding:10px 12px">
          <div style="font-weight:600;margin-bottom:6px">✉️ Soạn email hỏi giá (RFQ)</div>
          <div class="formrow">
            <div class="f" style="flex:2"><label>Gửi tới NCC (Ctrl/Cmd chọn nhiều)</label>
              <select id="rfq_ncc_${x.id}" multiple size="3" style="min-width:260px">${optNcc}</select>
              <div style="margin-top:3px"><a href="#" onclick="rfqAll(${x.id},true);return false" style="font-size:12px">Chọn tất cả</a> · <a href="#" onclick="rfqAll(${x.id},false);return false" style="font-size:12px">Bỏ chọn</a></div></div>
            <div class="f"><label>Hạn báo giá</label><input id="rfq_han_${x.id}" type="date"></div>
          </div>
          <div class="formrow">
            <div class="f" style="flex:2"><label>Quy cách / thông số kỹ thuật</label><input id="rfq_qc_${x.id}" placeholder="VD: PAC bột ≥30% Al2O3, bao 25kg"></div>
            <div class="f"><label>Đơn vị tính</label><input id="rfq_dv_${x.id}" placeholder="kg / cái / m³"></div>
          </div>
          <div class="formrow">
            <div class="f"><label>Nơi giao hàng</label><input id="rfq_ng_${x.id}" value="448 Võ Văn Tần, P. Bàn Cờ, TP.HCM"></div>
            <div class="f"><label>Thời gian giao mong muốn</label><input id="rfq_tg_${x.id}" placeholder="VD: trong 7 ngày"></div>
          </div>
          <div class="formrow">
            <div class="f"><label>Điều kiện thanh toán</label><input id="rfq_tt_${x.id}" value="Thanh toán trong 30 ngày sau khi giao hàng"></div>
            <div class="f"><label>Yêu cầu khác / chứng từ</label><input id="rfq_yc_${x.id}" value="CO/CQ, hóa đơn VAT"></div>
          </div>
          <div style="margin:6px 0"><button class="btn-sm ghost" onclick="nccRfqPreview(${x.id})">👁 Xem trước email</button>
            <span style="color:var(--muted);font-size:12px;margin-left:8px">Gửi từ inf@watersolutions.company · có nhật ký ở tab Báo giá</span></div>
          <div class="f"><label>Tiêu đề email</label><input id="rfq_tieude_${x.id}" placeholder="(tự tạo sau khi Xem trước)"></div>
          <div class="f"><label>Nội dung email (có thể chỉnh sửa)</label>
            <textarea id="rfq_body_${x.id}" rows="10" style="width:100%;font-family:inherit" placeholder="Bấm “Xem trước email” để tạo nội dung chuyên nghiệp, rồi chỉnh nếu cần."></textarea></div>
          <button class="btn-sm" onclick="nccGuiRFQ(${x.id})">✉️ Gửi RFQ</button>
        </div></td></tr>`;
    }
    let aiRow='';
    if(ai){
      const rui=(ai.rui_ro||[]).map(r=>`<li>${r}</li>`).join('');
      const moi=(ai.ung_vien_moi||[]).map(u=>`<li><b>${u.ten}</b>${u.ghi_chu?` — <span style="color:var(--muted)">${u.ghi_chu}</span>`:''}</li>`).join('');
      aiRow=`<tr><td colspan="7" style="background:#f5fbff;border-left:3px solid #2563eb">
        <div style="padding:8px 10px;font-size:13px">
          <div><b>🤖 AI Sourcing</b>${ai.nguon?` <span class="badge b-info">${ai.nguon}</span>`:''} — ${ai.ly_do||'—'}</div>
          ${ai.hanh_dong?`<div style="margin-top:4px"><b>Hành động:</b> ${ai.hanh_dong}</div>`:''}
          ${rui?`<div style="margin-top:4px"><b>Rủi ro:</b><ul style="margin:4px 0 0 18px">${rui}</ul></div>`:''}
          ${moi?`<div style="margin-top:4px"><b>Nguồn mới nên mời báo giá (cần kiểm chứng):</b><ul style="margin:4px 0 0 18px">${moi}</ul></div>`:''}
        </div></td></tr>`;
    }
    let webRow='';
    if(web){
      const uv=(web.ung_vien||[]).map(u=>`<li style="margin-bottom:3px"><b>${u.ten}</b>
        ${u.website?` · <a href="${/^https?:/.test(u.website)?u.website:'https://'+u.website}" target="_blank">${u.website}</a>`:''}
        ${u.ghi_chu?` — <span style="color:var(--muted)">${u.ghi_chu}</span>`:''}
        ${u.nguon_url?` · <a href="${u.nguon_url}" target="_blank">nguồn</a>`:''}
        <span class="badge b-cho">chưa kiểm chứng</span>
        <button class="btn-sm ghost" onclick="nccThemNccTuWeb('${(u.ten||'').replace(/'/g,'')}','${(u.website||'').replace(/'/g,'')}')">Thêm vào hồ sơ</button></li>`).join('');
      webRow=`<tr><td colspan="7" style="background:#f7fff7;border-left:3px solid #16a34a">
        <div style="padding:8px 10px;font-size:13px">
          <div><b>🌐 Dò NCC trên web</b>${web.nguon?` <span class="badge b-info">${web.nguon}</span>`:''}</div>
          ${web.thong_bao?`<div style="margin-top:3px;color:var(--muted)">${web.thong_bao}</div>`:''}
          <ul style="margin:6px 0 0 18px">${uv||'<li>Không có kết quả.</li>'}</ul>
          <div style="margin-top:4px;color:var(--muted);font-size:12px">NCC từ web cần bộ phận mua <b>kiểm chứng</b> (pháp lý, năng lực, báo giá) trước khi đưa vào giao dịch.</div>
        </div></td></tr>`;
    }
    return mainRow+bgForm+rfqForm+aiRow+webRow;
  }).join('');
  const dxPanel = dxDuyet.length ? `<div class="panel" style="border:1px solid #16a34a55"><div class="panel-h"><h3>Đề xuất đã duyệt — chờ tạo PO</h3><div class="spacer"></div><span class="badge b-ok">${dxDuyet.length}</span></div>
    <div class="note">Đề xuất đã duyệt chuyển sang đây. <b>AI Sourcing tự chạy khi duyệt</b> (nếu bật <code>AUTO_TIM_NCC</code>) — gợi ý NCC tối ưu kèm rủi ro; có thể bấm <b>🤖 AI</b> để chạy lại, <b>🌐 Web</b> để dò NCC mới (cần kiểm chứng). Đổi NCC/đơn giá/hẹn giao trước khi <b>Tạo PO</b>. PO giữ nguyên Mã bán hàng.</div>
    <div class="panel-b"><table><thead><tr><th>Hàng hóa</th><th class="num">SL</th><th>Mã bán hàng</th><th>Nhà cung cấp (gợi ý/đổi)</th><th class="num">Đơn giá</th><th>Hẹn giao</th><th>Hành động</th></tr></thead><tbody>${dxRows}</tbody></table></div></div>` : '';
  host.innerHTML=`<div class="note" style="padding:0 0 12px">Tạo PO, gắn <b>mã đơn Bán hàng</b> để tính giá vốn; duyệt theo hạn mức; <b>nhận hàng</b> sẽ nhập kho và sinh công nợ phải trả.</div>
    ${dxPanel}${createForm}${recvPanel}
    <div class="panel"><div class="panel-h"><h3>Đơn mua hàng</h3></div>
    <div class="panel-b"><table><thead><tr><th>Số</th><th>Nhà cung cấp</th><th>Mã đơn bán</th><th class="num">Giá trị</th><th>Duyệt</th><th>Nhận</th><th>Hành động</th></tr></thead>
    <tbody>${rows||'<tr><td colspan="7" class="empty" style="padding:20px">Chưa có đơn mua.</td></tr>'}</tbody></table></div></div>`;
}
async function poCreate(){
  const ncc=Number(gv('po_ncc')), hh=Number(gv('po_hh')), sl=Number(gv('po_sl')||0), dg=Number(gv('po_dg')||0);
  const dh=gv('po_dh')?Number(gv('po_dh')):null, hen=gv('po_hen')||null;
  if(!ncc||!hh||sl<=0){toast("Chọn NCC, hàng hóa và số lượng > 0","err");return;}
  if(S.mode==="live"){ try{await api("/ncc/don-mua",{method:'POST',body:JSON.stringify({nha_cung_cap_id:ncc,don_hang_id:dh,ngay_hen_giao:hen,chi_tiet:[{hang_hoa_id:hh,so_luong:sl,don_gia:dg}]})});
    toast("Đã tạo PO (chờ duyệt)","ok");viewNCC($("#main"));}catch(e){toast(e.detail||e.message,"err");} return; }
  const id=Date.now(); const hhObj=(DEMO.hang_hoa||[]).find(x=>x.id===hh);
  DEMO.don_mua.push({id,so:"PO-"+id,nha_cung_cap_id:ncc,don_hang_id:dh,tong_tien:sl*dg,trang_thai:"CHO_DUYET",trang_thai_nhan:"CHUA",ngay_hen_giao:hen,
    chi_tiet:[{id:id+1,hang_hoa_id:hh,ten:hhObj?hhObj.ten:("HH#"+hh),so_luong:sl,don_gia:dg,so_luong_nhan:0}]});
  toast("Đã tạo PO (demo)","ok"); viewNCC($("#main"));
}
async function duyetPO(id,amount){
  if(S.mode==="live"){ try{await api(`/ncc/don-mua/${id}/duyet`,{method:'POST'});
    toast("Đã duyệt đơn mua","ok");viewNCC($("#main"));}catch(e){toast(e.status===403?("Bị chặn: "+(e.detail||"vượt hạn mức")):(e.detail||e.message),"err");} return; }
  const cap=HANMUC.po[S.role];
  if(cap===undefined){toast("Vai trò "+S.role+" không có quyền duyệt đơn mua","err");return;}
  if(cap!==null && amount>cap){toast(`Bị chặn: ${vnd(amount)} vượt hạn mức ${vnd(cap)} của ${S.role} — cần trình cấp cao hơn`,"err");return;}
  const p=DEMO.don_mua.find(x=>x.id===id); if(p)p.trang_thai="DA_DUYET";
  toast("Đã duyệt đơn mua (demo)","ok"); viewNCC($("#main"));
}
function nccRecvOpen(id){S.poRecv=id;viewNCC($("#main"));}
function nccRecvClose(){S.poRecv=null;viewNCC($("#main"));}
async function nccRecvPanel(poId){
  let po;
  if(S.mode==="live"){ try{po=await api("/ncc/don-mua/"+poId);}catch(e){toast(e.detail||e.message,"err");return '';} }
  else po=(DEMO.don_mua||[]).find(p=>p.id===poId);
  if(!po)return '';
  const lines=(po.chi_tiet||[]).map(ct=>{
    const con=Number(ct.so_luong)-Number(ct.so_luong_nhan||0);
    return `<tr><td>${ct.ten||('HH #'+ct.hang_hoa_id)}</td><td class="num">${Number(ct.so_luong)}</td>
      <td class="num">${Number(ct.so_luong_nhan||0)}</td><td class="num">${con}</td>
      <td><input id="rc_${ct.id}" type="number" min="0" max="${con}" value="${con}" style="width:90px"></td></tr>`;
  }).join('');
  return `<div class="panel" style="border:1px solid var(--brand,#0ea5a4)"><div class="panel-h"><h3>Nhận hàng · ${po.so||('PO-'+po.id)}</h3><div class="spacer"></div>
      <button class="btn-sm ghost" onclick="nccRecvClose()">Đóng</button></div>
    <div class="panel-b"><table><thead><tr><th>Hàng hóa</th><th class="num">Đặt</th><th class="num">Đã nhận</th><th class="num">Còn lại</th><th>Nhận lần này</th></tr></thead>
    <tbody>${lines}</tbody></table>
    <div class="formrow"><div class="f"><label>Hạn thanh toán</label><input id="rc_han" type="date"></div>
      <div class="f"><label>Sinh công nợ phải trả</label><select id="rc_cn"><option value="1">Có</option><option value="0">Không</option></select></div>
      <div class="f"><label>Đạt kiểm tra chất lượng (QC)</label><select id="rc_qc"><option value="1">Đạt</option><option value="0">Không đạt</option></select></div>
      <button class="btn-sm" onclick="nccRecvSubmit(${po.id})">Xác nhận nhận hàng</button></div></div>`;
}
async function nccRecvSubmit(poId){
  let po=(DEMO.don_mua||[]).find(p=>p.id===poId), cts;
  if(S.mode==="live"){ try{po=await api("/ncc/don-mua/"+poId);}catch(e){toast(e.detail||e.message,"err");return;} cts=po.chi_tiet; }
  else cts=po?po.chi_tiet:[];
  const chi_tiet=[];
  (cts||[]).forEach(ct=>{const v=Number(gv('rc_'+ct.id)||0); if(v>0)chi_tiet.push({don_mua_ct_id:ct.id,so_luong:v});});
  if(!chi_tiet.length){toast("Nhập số lượng nhận","err");return;}
  const han=gv('rc_han')||null, tao_cong_no=gv('rc_cn')!=="0", dat_qc=gv('rc_qc')!=="0";
  if(S.mode==="live"){ try{const r=await api(`/ncc/don-mua/${poId}/nhan-hang`,{method:'POST',body:JSON.stringify({chi_tiet,han_thanh_toan:han,tao_cong_no,dat_qc})});
    let msg=`Đã nhận · ${vnd(r.gia_tri_nhan)} · ${r.trang_thai_nhan}`;
    if(r.danh_gia_ncc)msg+=` · điểm giao hàng ${r.danh_gia_ncc.diem_giao_hang} → TB ${r.danh_gia_ncc.diem_danh_gia_moi}★`;
    toast(msg,"ok");S.poRecv=null;viewNCC($("#main"));}catch(e){toast(e.detail||e.message,"err");} return; }
  let gtri=0;
  po.chi_tiet.forEach(ct=>{const v=Number(gv('rc_'+ct.id)||0); if(v>0){ct.so_luong_nhan=Number(ct.so_luong_nhan||0)+v; gtri+=v*ct.don_gia;
    const hh=(DEMO.hang_hoa||[]).find(x=>x.id===ct.hang_hoa_id); if(hh)hh.so_luong=Number(hh.so_luong)+v;}});
  const du=po.chi_tiet.every(ct=>Number(ct.so_luong_nhan)>=Number(ct.so_luong));
  const co=po.chi_tiet.some(ct=>Number(ct.so_luong_nhan)>0);
  po.trang_thai_nhan=du?"DU":(co?"MOT_PHAN":"CHUA"); po.ngay_giao_thuc=new Date().toISOString().slice(0,10);
  if(tao_cong_no&&gtri>0)DEMO.cong_no_ncc.push({id:Date.now(),nha_cung_cap_id:po.nha_cung_cap_id,so_tien:gtri,da_thanh_toan:0,han,trang_thai:"CHUA_TRA"});
  let dgMsg="";
  if(du){ const dg=_chamDiemDemo(po,dat_qc); if(dg)dgMsg=` · điểm giao hàng ${dg.diem_giao_hang} → TB ${dg.diem_danh_gia_moi}★${dg.blacklist?' · ⚠ blacklist':''}`; }
  toast(`Đã nhận (demo) · ${vnd(gtri)} · ${po.trang_thai_nhan}${dgMsg}`,"ok"); S.poRecv=null; viewNCC($("#main"));
}
function _chamDiemDemo(po,dat_qc){
  const s=(DEMO.ncc.suppliers||[]).find(z=>z.id===po.nha_cung_cap_id); if(!s)return null;
  let s_ot=2; if(po.ngay_hen_giao&&po.ngay_giao_thuc){const tre=Math.floor((new Date(po.ngay_giao_thuc)-new Date(po.ngay_hen_giao))/864e5); s_ot=tre<=0?2:Math.max(0,2-0.2*tre);}
  const diem=Math.round(Math.min(5,Math.max(0,s_ot+(dat_qc?2:0)+1))*10)/10;
  DEMO.dg_log=DEMO.dg_log||[]; DEMO.dg_log.push({nha_cung_cap_id:s.id,don_mua_id:po.id,diem});
  const ds=DEMO.dg_log.filter(x=>x.nha_cung_cap_id===s.id).map(x=>x.diem);
  s.diem_danh_gia=Math.round(ds.reduce((a,b)=>a+b,0)/ds.length*10)/10;
  const kem=ds.filter(d=>d<2).length; if(s.diem_danh_gia<2&&kem>=2)s.blacklist=true;
  return {diem_giao_hang:diem,diem_danh_gia_moi:s.diem_danh_gia,blacklist:!!s.blacklist};
}

/* --- Tab Công nợ phải trả (tuổi nợ + thanh toán) --- */
function _agingDemo(cns){
  const today=new Date(); const b={chua_den_han:0,b_0_30:0,b_31_60:0,b_61_90:0,b_90p:0};
  cns.forEach(x=>{const con=x.so_tien-(x.da_thanh_toan||0); if(con<=0)return;
    const qua=x.han?Math.floor((today-new Date(x.han))/864e5):-1;
    const k=qua<=0?'chua_den_han':qua<=30?'b_0_30':qua<=60?'b_31_60':qua<=90?'b_61_90':'b_90p'; b[k]+=con;});
  return b;
}
async function nccCongNo(host){
  const sups=await _nccSups(); let cns, aging;
  if(S.mode==="live"){
    try{cns=await api("/ncc/cong-no");}catch(e){toast(e.detail||e.message,"err");cns=[];}
    try{aging=(await api("/ncc/cong-no/tuoi-no")).buckets;}catch{aging=_agingDemo(cns);}
  } else {
    cns=(DEMO.cong_no_ncc||[]).map(x=>{const con=x.so_tien-(x.da_thanh_toan||0);
      return {...x,con_lai:con,qua_han:x.trang_thai!=="DA_TRA"&&x.han&&new Date(x.han)<new Date()&&con>0};});
    aging=_agingDemo(DEMO.cong_no_ncc||[]);
  }
  const supName=id=>{const s=sups.find(x=>x.id===id);return s?s.ten:("NCC #"+id);};
  const canPay=can("ke_toan","THAO_TAC");
  const tong=cns.reduce((s,x)=>s+(x.con_lai||0),0);
  const cards=[['Chưa đến hạn','chua_den_han'],['1–30 ngày','b_0_30'],['31–60','b_31_60'],['61–90','b_61_90'],['>90 ngày','b_90p']]
    .map(([l,k])=>`<div style="flex:1;min-width:118px;background:var(--surface);border-radius:10px;padding:10px 12px">
      <div style="color:var(--muted);font-size:12px">${l}</div><div style="font-weight:700;margin-top:2px">${vnd(aging[k]||0)}</div></div>`).join('');
  const rows=cns.map(x=>{
    const pay=(canPay&&x.con_lai>0)?`<button class="btn-sm" onclick="nccThanhToan(${x.id},${x.con_lai})">Thanh toán</button>`:'—';
    return `<tr class="${x.qua_han?'qh':''}"><td>${supName(x.nha_cung_cap_id)}</td>
    <td class="num">${vnd(x.so_tien)}</td><td class="num">${vnd(x.da_thanh_toan||0)}</td><td class="num"><b>${vnd(x.con_lai)}</b></td>
    <td>${x.han||'—'} ${x.qua_han?'<span class="badge b-tc">Quá hạn</span>':''}</td>
    <td>${x.con_lai<=0?'<span class="badge b-ok">Đã trả</span>':'<span class="badge b-cho">Còn nợ</span>'}</td><td>${pay}</td></tr>`;}).join('');
  host.innerHTML=`<div class="note" style="padding:0 0 12px">Công nợ phải trả sinh khi nhận hàng. <b>Tuổi nợ</b> phân theo số ngày quá hạn; khoản quá hạn tô đỏ. Kế toán ghi nhận thanh toán để giảm nợ.</div>
    <div style="display:flex;flex-wrap:wrap;gap:8px;padding:0 0 12px">${cards}</div>
    <div class="panel"><div class="panel-h"><h3>Công nợ phải trả</h3><div class="spacer"></div><span class="num" style="font-weight:700">Còn phải trả: ${vnd(tong)}</span></div>
    <div class="panel-b"><table><thead><tr><th>Nhà cung cấp</th><th class="num">Số tiền</th><th class="num">Đã trả</th><th class="num">Còn lại</th><th>Hạn</th><th>Trạng thái</th><th>Thanh toán</th></tr></thead>
    <tbody>${rows||'<tr><td colspan="7" class="empty" style="padding:20px">Chưa có công nợ.</td></tr>'}</tbody></table></div></div>`;
}
async function nccThanhToan(id,conlai){
  const v=prompt(`Số tiền thanh toán (còn lại ${vnd(conlai)}):`,String(conlai)); if(v===null)return;
  const st=Number(v); if(isNaN(st)||st<=0||st>conlai){toast("Số tiền không hợp lệ (≤ còn lại)","err");return;}
  if(S.mode==="live"){ try{await api(`/ncc/cong-no/${id}/thanh-toan`,{method:'POST',body:JSON.stringify({so_tien:st,hinh_thuc:"CK"})});
    toast("Đã ghi nhận thanh toán","ok");viewNCC($("#main"));}catch(e){toast(e.detail||e.message,"err");} return; }
  const x=(DEMO.cong_no_ncc||[]).find(p=>p.id===id); if(x){x.da_thanh_toan=(x.da_thanh_toan||0)+st; x.trang_thai=x.da_thanh_toan>=x.so_tien?"DA_TRA":"TRA_MOT_PHAN";}
  toast("Đã thanh toán (demo)","ok"); viewNCC($("#main"));
}

/* --- Tab Kiểm soát: trễ hạn giao + hạn mức công nợ --- */
function _treHanDemo(){
  const today=new Date(); const sup=id=>{const s=DEMO.ncc.suppliers.find(x=>x.id===id);return s?s.ten:("NCC #"+id);};
  return (DEMO.don_mua||[]).filter(p=>p.trang_thai==="DA_DUYET"&&p.ngay_hen_giao).map(p=>{
      const moc=p.ngay_giao_thuc?new Date(p.ngay_giao_thuc):today; const tre=Math.floor((moc-new Date(p.ngay_hen_giao))/864e5);
      const chuaDu=p.trang_thai_nhan!=="DU"; return {p,tre,chuaDu};})
    .filter(o=>o.tre>0&&(o.chuaDu||o.p.ngay_giao_thuc))
    .map(o=>({so:o.p.so,ten_ncc:sup(o.p.nha_cung_cap_id),ngay_hen_giao:o.p.ngay_hen_giao,ngay_giao_thuc:o.p.ngay_giao_thuc||null,
      trang_thai_nhan:o.p.trang_thai_nhan,so_ngay_tre:o.tre,da_nhan_xong:!!o.p.ngay_giao_thuc&&!o.chuaDu}))
    .sort((a,b)=>b.so_ngay_tre-a.so_ngay_tre);
}
function _kiemSoatDemo(){
  return (DEMO.ncc.suppliers||[]).map(s=>{
      const du=(DEMO.cong_no_ncc||[]).filter(x=>x.nha_cung_cap_id===s.id).reduce((a,x)=>a+(x.so_tien-(x.da_thanh_toan||0)),0);
      const hm=Number(s.han_muc_cong_no||0); const ty=hm>0?Math.round(du/hm*1000)/10:null;
      return {ten:s.ten,han_muc:hm,du_no:du,ty_le:ty,vuot:hm>0&&du>hm,sap_vuot:hm>0&&ty>=80&&ty<=100};})
    .filter(x=>x.du_no>0||x.han_muc>0).sort((a,b)=>(b.ty_le||0)-(a.ty_le||0));
}
async function nccKiemSoat(host){
  let tre, ks;
  if(S.mode==="live"){
    try{tre=await api("/ncc/giao-hang/tre-han");}catch(e){toast(e.detail||e.message,"err");tre=[];}
    try{ks=await api("/ncc/kiem-soat-cong-no");}catch{ks=[];}
  } else { tre=_treHanDemo(); ks=_kiemSoatDemo(); }
  const treRows=tre.map(x=>`<tr class="${x.so_ngay_tre>7?'qh':''}"><td><b>${x.so}</b></td><td>${x.ten_ncc||'—'}</td>
    <td>${x.ngay_hen_giao||'—'}</td><td>${x.ngay_giao_thuc||'<span style="color:var(--muted)">chưa giao</span>'}</td>
    <td class="num"><b style="color:#dc2626">${x.so_ngay_tre}</b></td>
    <td>${x.da_nhan_xong?'<span class="badge b-cho">Đã nhận (trễ)</span>':'<span class="badge b-tc">Chưa nhận</span>'}</td></tr>`).join('');
  const ksRows=ks.map(x=>{
    const ty=x.ty_le; const cls=x.vuot?'b-tc':x.sap_vuot?'b-cho':'b-ok';
    const lbl=x.vuot?'Vượt hạn mức':x.sap_vuot?'Sắp vượt':'Trong hạn mức';
    const bar=x.han_muc>0?`<div style="background:var(--surface);border-radius:6px;overflow:hidden;height:8px;margin-top:4px"><div style="width:${Math.min(100,ty||0)}%;height:100%;background:${x.vuot?'#dc2626':x.sap_vuot?'#f59e0b':'#16a34a'}"></div></div>`:'';
    return `<tr><td>${x.ten}</td><td class="num">${x.han_muc>0?vnd(x.han_muc):'<span style="color:var(--muted)">chưa đặt</span>'}</td>
      <td class="num"><b>${vnd(x.du_no)}</b></td><td>${ty!=null?ty+'%':'—'}${bar}</td>
      <td><span class="badge ${cls}">${lbl}</span></td></tr>`;}).join('');
  host.innerHTML=`<div class="panel"><div class="panel-h"><h3>Giao hàng trễ hạn</h3></div>
      <div class="note">PO đã duyệt bị trễ so với ngày hẹn giao (chưa nhận đủ, hoặc đã nhận nhưng trễ). Trễ trên 7 ngày tô đỏ.</div>
      <div class="panel-b"><table><thead><tr><th>PO</th><th>Nhà cung cấp</th><th>Hẹn giao</th><th>Giao thực</th><th class="num">Trễ (ngày)</th><th>Trạng thái</th></tr></thead>
      <tbody>${treRows||'<tr><td colspan="6" class="empty" style="padding:18px">Không có PO trễ hạn.</td></tr>'}</tbody></table></div></div>
    <div class="panel"><div class="panel-h"><h3>Kiểm soát hạn mức công nợ</h3></div>
      <div class="note">Dư nợ phải trả từng NCC so với hạn mức. Khi duyệt PO làm vượt trần, hệ thống sẽ chặn.</div>
      <div class="panel-b"><table><thead><tr><th>Nhà cung cấp</th><th class="num">Hạn mức</th><th class="num">Dư nợ</th><th>Mức sử dụng</th><th>Cảnh báo</th></tr></thead>
      <tbody>${ksRows||'<tr><td colspan="5" class="empty" style="padding:18px">Chưa có dữ liệu.</td></tr>'}</tbody></table></div></div>`;
}

/* ---------- KẾ TOÁN: quỹ tiền · phiếu thu–chi (duyệt nhiều cấp) · lãi/lỗ mã bán · cân đối ---------- */
const KT_TT={NHAP:['Nháp','b-cho'],CHO_DUYET:['Chờ duyệt','b-cho'],DA_DUYET:['Đã duyệt','b-ok'],TU_CHOI:['Từ chối','b-tc'],HUY:['Đã hủy','b-tc']};
function _ktInitDemo(){ if(!DEMO.ke_toan)DEMO.ke_toan={quy:[
  {id:1,ma:"QTM",ten:"Quỹ tiền mặt",loai:"TIEN_MAT",tk_ke_toan:"111",so_du_dau:50e6,so_du:50e6},
  {id:2,ma:"NH-VCB",ten:"Tài khoản Vietcombank",loai:"NGAN_HANG",tk_ke_toan:"112",so_du_dau:300e6,so_du:300e6}],phieu:[]}; }
async function viewKeToan(m){
  if(!S.ktTab)S.ktTab="tq"; _ktInitDemo();
  m.innerHTML=head("Kế toán","Quỹ tiền · phiếu thu–chi duyệt nhiều cấp · công nợ · sổ cái · truy vết theo mã hàng bán");
  const tabs=[["tq","Tổng quan"],["quy","Quỹ & sổ quỹ"],["thongke","Thống kê thu–chi"],["hoadon","Hóa đơn"],["phieu","Phiếu thu–chi"],["lailo","Lãi/lỗ mã bán"],["tratruoc","Trả trước"],["quytl","Trích lập quỹ"],["cdps","Cân đối phát sinh"]];
  m.innerHTML+=`<div class="tabs">${tabs.map(([k,l])=>`<button class="${S.ktTab===k?'active':''}" onclick="ktSwitch('${k}')">${l}</button>`).join('')}</div><div id="ktBody"></div>`;
  ktRender();
}
function ktSwitch(t){S.ktTab=t;ktRender();}
async function ktRender(){const h=$("#ktBody"); if(!h)return; h.innerHTML='<div class="empty" style="padding:24px">Đang tải…</div>';
  try{ if(S.ktTab==="tq")await ktTongQuan(h); else if(S.ktTab==="quy")await ktQuy(h); else if(S.ktTab==="thongke")await ktThongKe(h); else if(S.ktTab==="hoadon")await ktHoaDon(h); else if(S.ktTab==="phieu")await ktPhieu(h); else if(S.ktTab==="lailo")await ktLaiLo(h); else if(S.ktTab==="tratruoc")await ktTraTruoc(h); else if(S.ktTab==="quytl")await qtTrichLap(h); else await ktCanDoi(h);}catch(e){h.innerHTML=`<div class="empty" style="padding:24px;color:#dc2626">${e.detail||e.message}</div>`;}
}
function _ktCard(l,v,c){return `<div style="flex:1;min-width:150px;background:var(--surface);border-radius:10px;padding:12px 14px">
  <div style="color:var(--muted);font-size:12px">${l}</div><div style="font-weight:700;margin-top:3px;font-size:18px;${c?('color:'+c):''}">${v}</div></div>`;}

async function ktTongQuan(host){
  let d;
  if(S.mode==="live"){ d=await api("/ke-toan/tong-quan"); }
  else { const q=DEMO.ke_toan.quy; const pt=(DEMO.don_hang||[]).reduce((s,o)=>s+(o.tong_tien||0),0)-_ktDemoThu();
    const ptr=(DEMO.cong_no_ncc||[]).reduce((s,x)=>s+((x.so_tien||0)-(x.da_thanh_toan||0)),0);
    d={tong_quy:q.reduce((s,x)=>s+x.so_du,0),phai_thu:pt,phai_tra:ptr,phieu_cho_duyet:(DEMO.ke_toan.phieu||[]).filter(p=>p.trang_thai==="CHO_DUYET").length,quy:q}; }
  const cards=_ktCard("Tổng tiền quỹ",vnd(d.tong_quy),d.tong_quy<0?'#dc2626':'')+
    _ktCard("Phải thu khách hàng",vnd(d.phai_thu))+_ktCard("Phải trả người bán",vnd(d.phai_tra))+
    _ktCard("Phiếu chờ duyệt",d.phieu_cho_duyet,d.phieu_cho_duyet>0?'#f59e0b':'');
  const qr=(d.quy||[]).map(q=>`<tr><td>${q.ma}</td><td>${q.ten}</td><td>${q.loai==="TIEN_MAT"?"Tiền mặt":"Ngân hàng"} (${q.tk_ke_toan})</td><td class="num"><b>${vnd(q.so_du)}</b></td></tr>`).join('');
  host.innerHTML=`<div class="note" style="padding:0 0 12px">Dữ liệu kế toán liên tục: chứng từ mua/bán → công nợ → phiếu thu/chi (duyệt nhiều cấp) → bút toán sổ cái. Mọi phát sinh truy vết được theo <b>mã hàng bán</b> ở tab Lãi/lỗ.</div>
    <div style="display:flex;flex-wrap:wrap;gap:8px;padding:0 0 14px">${cards}</div>
    <div class="panel"><div class="panel-h"><h3>Số dư các quỹ</h3></div><div class="panel-b"><table><thead><tr><th>Mã</th><th>Tên quỹ</th><th>Loại (TK)</th><th class="num">Số dư</th></tr></thead><tbody>${qr||'<tr><td colspan="4" class="empty">Chưa có quỹ.</td></tr>'}</tbody></table></div></div>`;
}

async function ktQuy(host){
  const canOp=can("ke_toan","THAO_TAC");
  const quy=S.mode==="live"?await api("/ke-toan/quy"):DEMO.ke_toan.quy;
  const rows=quy.map(q=>`<tr><td>${q.ma}</td><td>${q.ten}</td><td>${q.loai==="TIEN_MAT"?"Tiền mặt":"Ngân hàng"}${q.so_tk?(' · '+q.so_tk):''}</td>
    <td class="num">${q.tk_ke_toan}</td><td class="num"><b>${vnd(q.so_du)}</b></td>
    <td><button class="btn-sm ghost" onclick="ktSoQuy(${q.id})">Sổ quỹ</button></td></tr>`).join('');
  const form=canOp?`<div class="panel"><div class="panel-h"><h3>Tạo quỹ / tài khoản</h3><div class="spacer"></div><button class="btn-sm" onclick="$('#qForm').classList.toggle('hidden')">+ Quỹ</button></div>
    <div id="qForm" class="hidden" style="padding:0 18px 14px"><div class="formrow">
      <div class="f"><label>Tên quỹ</label><input id="q_ten" placeholder="VD: Quỹ tiền mặt CN2"></div>
      <div class="f"><label>Loại</label><select id="q_loai"><option value="TIEN_MAT">Tiền mặt (111)</option><option value="NGAN_HANG">Ngân hàng (112)</option></select></div>
      <div class="f"><label>Số TK ngân hàng</label><input id="q_stk" placeholder="(nếu là NH)"></div>
      <div class="f"><label>Số dư đầu</label><input id="q_sdd" type="number" value="0"></div>
      <button class="btn-sm" onclick="ktTaoQuy()">Lưu</button></div></div></div>`:'';
  host.innerHTML=form+`<div class="panel"><div class="panel-h"><h3>Quỹ tiền & tài khoản ngân hàng</h3></div>
    <div class="panel-b"><table><thead><tr><th>Mã</th><th>Tên</th><th>Loại</th><th class="num">TK</th><th class="num">Số dư</th><th>Sổ quỹ</th></tr></thead>
    <tbody>${rows||'<tr><td colspan="6" class="empty">Chưa có quỹ.</td></tr>'}</tbody></table></div></div>`;
}
async function ktTaoQuy(){
  const ten=gv('q_ten'); if(!ten){toast("Nhập tên quỹ","err");return;}
  const body={ten,loai:gv('q_loai'),so_tk:gv('q_stk')||null,tk_ke_toan:gv('q_loai')==="NGAN_HANG"?"112":"111",so_du_dau:Number(gv('q_sdd')||0)};
  if(S.mode==="live"){ try{await api("/ke-toan/quy",{method:'POST',body:JSON.stringify(body)});toast("Đã tạo quỹ","ok");ktRender();}catch(e){toast(e.detail||e.message,"err");} return; }
  const id=Date.now(); DEMO.ke_toan.quy.push({id,ma:"Q"+id,...body,so_du:body.so_du_dau}); toast("Đã tạo quỹ (demo)","ok"); ktRender();
}
async function ktSoQuy(id){
  let d;
  if(S.mode==="live"){ d=await api(`/ke-toan/quy/${id}/so-quy`); }
  else { const q=DEMO.ke_toan.quy.find(x=>x.id===id); let sd=q.so_du_dau; const dong=(DEMO.ke_toan.phieu||[]).filter(p=>p.quy_id===id&&p.trang_thai==="DA_DUYET").map(p=>{sd+=p.loai==="THU"?p.so_tien:-p.so_tien;return {so:p.so,ngay:p.ngay,dien_giai:p.dien_giai||'',ma_ban:p.ma_ban,thu:p.loai==="THU"?p.so_tien:0,chi:p.loai==="CHI"?p.so_tien:0,so_du:sd};}); d={quy:q,so_du_dau:q.so_du_dau,so_du_cuoi:sd,dong}; }
  const rows=d.dong.map(x=>`<tr><td>${x.so||''}</td><td>${x.ngay}</td><td>${x.dien_giai}${x.ma_ban?` · <span class="badge b-info">${x.ma_ban}</span>`:''}</td>
    <td class="num" style="color:#16a34a">${x.thu?vnd(x.thu):''}</td><td class="num" style="color:#dc2626">${x.chi?vnd(x.chi):''}</td><td class="num"><b>${vnd(x.so_du)}</b></td></tr>`).join('');
  _ktModal(`Sổ quỹ — ${d.quy.ten}`,`<div style="margin-bottom:8px">Số dư đầu: <b>${vnd(d.so_du_dau)}</b> · Số dư cuối: <b>${vnd(d.so_du_cuoi)}</b></div>
    <table><thead><tr><th>Số CT</th><th>Ngày</th><th>Diễn giải</th><th class="num">Thu</th><th class="num">Chi</th><th class="num">Tồn quỹ</th></tr></thead>
    <tbody>${rows||'<tr><td colspan="6" class="empty">Chưa có phát sinh.</td></tr>'}</tbody></table>`);
}

/* --- Tab Hóa đơn (mua & bán) --- */
/* Combobox gõ-để-tìm (autocomplete) dùng lại được: input hiển thị + hidden lưu id */
function _cbxStrip(s){return (s||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/đ/g,'d');}
/* Biến MỌI <select> thành ô GÕ-ĐỂ-TÌM. Giữ nguyên id/value/onchange của select gốc
   (select bị ẩn nhưng vẫn là nguồn dữ liệu), nên code cũ đọc .value / set innerHTML vẫn chạy. */
function _enhanceSelects(root){
  (root||document).querySelectorAll('select:not([data-cbx]):not([data-nocbx])').forEach(sel=>{
    if(sel.multiple)return;
    sel.setAttribute('data-cbx','1'); sel.style.display='none';
    const wrap=document.createElement('div'); wrap.className='cbx'; wrap.style.cssText='position:relative;width:100%';
    const txt=document.createElement('input'); txt.type='text'; txt.autocomplete='off'; txt.className='cbx-inp'; txt.style.width='100%';
    const first=sel.options[0];
    txt.placeholder=sel.getAttribute('data-ph')||((first&&first.value==='')?first.textContent.trim():'Gõ để tìm…');
    const dd=document.createElement('div');
    dd.style.cssText='display:none;position:absolute;left:0;right:0;top:100%;z-index:60;background:var(--surface,#fff);border:1px solid var(--border,#e2e8f0);border-radius:8px;max-height:230px;overflow:auto;box-shadow:0 8px 24px rgba(0,0,0,.18)';
    sel.parentNode.insertBefore(wrap,sel); wrap.appendChild(txt); wrap.appendChild(dd); wrap.appendChild(sel);
    const opts=()=>Array.from(sel.options).map(o=>({v:o.value,l:o.textContent.trim()}));
    const syncText=()=>{const o=sel.options[sel.selectedIndex]; txt.value=(o&&o.value!=='')?o.textContent.trim():'';};
    const render=q=>{
      const s=_cbxStrip((q||'').trim());
      const list=opts().filter(o=>_cbxStrip(o.l).includes(s)).slice(0,60);
      if(!list.length){dd.innerHTML='<div style="padding:8px 10px;color:var(--muted)">Không có kết quả</div>';dd.style.display='block';return;}
      dd.innerHTML=list.map(o=>`<div data-v="${String(o.v).replace(/"/g,'&quot;')}" style="padding:8px 10px;cursor:pointer" onmouseenter="this.style.background='var(--surface)'" onmouseleave="this.style.background=''">${o.l||'—'}</div>`).join('');
      dd.style.display='block';
      Array.from(dd.children).forEach(ch=>{ch.onmousedown=e=>{e.preventDefault(); sel.value=ch.getAttribute('data-v'); syncText(); dd.style.display='none'; sel.dispatchEvent(new Event('change',{bubbles:true}));};});
    };
    txt.addEventListener('input',()=>render(txt.value));
    txt.addEventListener('focus',()=>render(''));
    txt.addEventListener('blur',()=>setTimeout(()=>{dd.style.display='none'; syncText();},160));
    new MutationObserver(()=>syncText()).observe(sel,{childList:true});
    syncText();
  });
}
function _initCbxObserver(){
  if(window._cbxInit)return; window._cbxInit=1;
  _enhanceSelects(document);
  new MutationObserver(()=>{ if(window._cbxT)return; window._cbxT=setTimeout(()=>{window._cbxT=null; _enhanceSelects(document);},30); })
    .observe(document.body,{childList:true,subtree:true});
}

const HD_TK=[["632","632 — Giá vốn hàng bán"],["642","642 — Chi phí QLDN"],["641","641 — Chi phí bán hàng"],["627","627 — Chi phí SX chung"]];
/* (mọi select tự thành ô gõ-để-tìm qua _enhanceSelects) */
function ktOnHdLoai(){
  const l=gv('h_loai'); const sel=document.getElementById('h_dt');
  if(sel){const list=l==="BAN"?(window.KTKH||[]):(window.KTNCC||[]);
    sel.innerHTML='<option value="">— chọn '+(l==="BAN"?"khách hàng":"nhà cung cấp")+' —</option>'+list.map(x=>`<option value="${x.id}">${x.ten}</option>`).join('');
    sel.value='';}
  const w=document.getElementById('h_tkw'); if(w)w.style.display=l==="MUA"?'':'none';
  const lb=document.getElementById('h_dtlb'); if(lb)lb.textContent=l==="BAN"?"Khách hàng":"Nhà cung cấp";
}
async function ktHoaDon(host){
  const canOp=can("ke_toan","THAO_TAC");
  let hds, khs, nccs, orders;
  if(S.mode==="live"){
    [hds,khs,nccs,orders]=await Promise.all([api("/ke-toan/hoa-don"),
      api("/ban-hang/khach-hang").catch(()=>[]), _nccSups(), _nccOrders()]);
  } else {
    if(!DEMO.ke_toan.hoa_don)DEMO.ke_toan.hoa_don=[];
    hds=DEMO.ke_toan.hoa_don; nccs=DEMO.ncc.suppliers||[];
    khs=[...new Map((DEMO.don_hang||[]).map(o=>[o.khach,{id:o.id,ten:o.khach}])).values()];
    orders=DEMO.don_hang;
  }
  window.KTKH=khs; window.KTNCC=nccs; window.KTORD=orders||[];
  const dtOpt='<option value="">— chọn khách hàng —</option>'+(khs||[]).map(x=>`<option value="${x.id}">${x.ten}</option>`).join('');
  const ordOpt='<option value="">— không gắn —</option>'+(window.KTORD).map(o=>`<option value="${o.id}">${o.so||('DH-'+o.id)}</option>`).join('');
  const tkOpt=HD_TK.map(([v,l])=>`<option value="${v}">${l}</option>`).join('');
  const form=canOp?`<div class="panel"><div class="panel-h"><h3>Ghi nhận hóa đơn</h3><div class="spacer"></div><button class="btn-sm" onclick="$('#hForm').classList.toggle('hidden')">+ Hóa đơn</button></div>
    <div id="hForm" class="hidden" style="padding:0 18px 14px">
     <div class="formrow"><div class="f"><label>Loại hóa đơn</label><select id="h_loai" onchange="ktOnHdLoai()"><option value="BAN">Bán ra (doanh thu)</option><option value="MUA">Mua vào (chi phí / giá vốn)</option></select></div>
       <div class="f"><label id="h_dtlb">Khách hàng</label><select id="h_dt" data-ph="Gõ tên để tìm…">${dtOpt}</select></div>
       <div class="f"><label>Mã hàng bán</label><select id="h_dh" data-ph="Gõ mã đơn để tìm…">${ordOpt}</select></div></div>
     <div class="formrow" style="padding-top:0"><div class="f"><label>Tiền trước thuế</label><input id="h_truoc" type="number" value="0"></div>
       <div class="f"><label>Thuế suất %</label><input id="h_vat" type="number" value="8"></div>
       <div class="f" id="h_tkw" style="display:none"><label>TK chi phí / giá vốn</label><select id="h_tk">${tkOpt}</select></div></div>
     <div class="formrow" style="padding-top:0"><div class="f" style="flex:3"><label>Diễn giải</label><input id="h_dg" placeholder="VD: Xử lý nước thải đợt 1 / Mua hóa chất PAC"></div>
       <div class="f"><label style="font-weight:normal;font-size:13px"><input type="checkbox" id="h_cn" checked> Tạo công nợ</label><br>
         <label style="font-weight:normal;font-size:13px"><input type="checkbox" id="h_ht" checked> Hạch toán ngay</label></div>
       <button class="btn-sm" onclick="ktTaoHoaDon()">Lưu hóa đơn</button></div></div></div>`:'';
  const rows=(hds||[]).map(h=>{
    const ban=h.loai==="BAN";
    const cn=h.cong_no; const conlai=cn?cn.con_lai:0;
    const stHt=h.da_hach_toan?'<span class="badge b-ok">Đã hạch toán</span>':'<span class="badge b-cho">Chưa hạch toán</span>';
    const stHddt=ban?(h.hddt_trang_thai==="DA_PHAT_HANH"?` <span class="badge b-ok">HĐĐT ✓</span>`:''):'';
    let act='';
    if(canOp&&!h.da_hach_toan)act+=`<button class="btn-sm" onclick="ktHachToanHD(${h.id})">Hạch toán</button> `;
    if(canOp&&ban&&h.hddt_trang_thai!=="DA_PHAT_HANH")act+=`<button class="btn-sm ghost" onclick="ktPhatHanhHddt(${h.id})">Phát hành HĐĐT</button>`;
    return `<tr><td><b>${h.so}</b></td><td><span class="badge ${ban?'b-ok':'b-tc'}">${ban?'BÁN':'MUA'}</span></td>
      <td>${h.ten_doi_tac||'—'}</td><td>${h.ma_ban?`<span class="badge b-info">${h.ma_ban}</span>`:'—'}</td>
      <td class="num">${vnd(h.tien_truoc_thue)}</td><td class="num">${vnd(h.tien_thue)}</td><td class="num"><b>${vnd(h.tong_tien)}</b></td>
      <td class="num">${cn?vnd(conlai):'—'}</td><td>${stHt}${stHddt}</td><td>${act||'—'}</td></tr>`;}).join('');
  host.innerHTML=form+`<div class="note" style="padding:0 0 10px">Ghi nhận hóa đơn <b>bán</b> → sinh <b>phải thu</b> + hạch toán <b>doanh thu</b> (Nợ 131/Có 511, 3331). Hóa đơn <b>mua</b> → sinh <b>phải trả</b> + <b>chi phí/giá vốn</b> + thuế GTGT vào (Nợ 632/642·1331/Có 331). Công nợ sinh ra dùng để lập phiếu thu/chi ở tab bên cạnh.</div>
    <div class="panel"><div class="panel-h"><h3>Hóa đơn mua &amp; bán</h3></div>
    <div class="panel-b"><table><thead><tr><th>Số HĐ</th><th>Loại</th><th>Đối tác</th><th>Mã bán</th><th class="num">Trước thuế</th><th class="num">Thuế</th><th class="num">Tổng</th><th class="num">Còn nợ</th><th>Trạng thái</th><th>Hành động</th></tr></thead>
    <tbody>${rows||'<tr><td colspan="10" class="empty" style="padding:18px">Chưa có hóa đơn.</td></tr>'}</tbody></table></div></div>`;
}
async function ktTaoHoaDon(){
  const loai=gv('h_loai'), truoc=Number(gv('h_truoc')||0), vat=Number(gv('h_vat')||0);
  if(truoc<=0){toast("Nhập tiền trước thuế > 0","err");return;}
  const dt=gv('h_dt'); if(!dt){toast("Chọn đối tác","err");return;}
  const body={loai,tien_truoc_thue:truoc,thue_suat:vat,don_hang_id:gv('h_dh')?Number(gv('h_dh')):null,
    dien_giai:gv('h_dg')||null,tao_cong_no:document.getElementById('h_cn')?.checked!==false,hach_toan_luon:document.getElementById('h_ht')?.checked!==false};
  if(loai==="BAN")body.khach_hang_id=Number(dt); else {body.nha_cung_cap_id=Number(dt); body.tk_chi_phi=gv('h_tk');}
  if(S.mode==="live"){ try{await api("/ke-toan/hoa-don",{method:'POST',body:JSON.stringify(body)});toast("Đã ghi nhận hóa đơn","ok");ktRender();}catch(e){toast(e.detail||e.message,"err");} return; }
  const id=Date.now(); const thue=Math.round(truoc*vat/100); const tong=truoc+thue;
  const ten=loai==="BAN"?(window.KTKH.find(x=>x.id===Number(dt))||{}).ten:(window.KTNCC.find(x=>x.id===Number(dt))||{}).ten;
  const dh=(DEMO.don_hang||[]).find(o=>o.id===body.don_hang_id);
  DEMO.ke_toan.hoa_don.unshift({id,so:(loai==="BAN"?"HDB":"HDM")+"-"+id,loai,ten_doi_tac:ten,ma_ban:dh?dh.so:null,tien_truoc_thue:truoc,tien_thue:thue,tong_tien:tong,da_hach_toan:body.hach_toan_luon,hddt_trang_thai:loai==="BAN"?"CHUA_PHAT_HANH":null,cong_no:body.tao_cong_no?{loai:loai==="BAN"?"PHAI_THU":"PHAI_TRA",con_lai:tong}:null});
  toast("Đã ghi nhận hóa đơn (demo)","ok"); ktRender();
}
async function ktHachToanHD(id){
  if(S.mode==="live"){ try{await api(`/ke-toan/hoa-don/${id}/hach-toan`,{method:'POST'});toast("Đã hạch toán","ok");ktRender();}catch(e){toast(e.detail||e.message,"err");} return; }
  const h=(DEMO.ke_toan.hoa_don||[]).find(x=>x.id===id); if(h)h.da_hach_toan=true; toast("Đã hạch toán (demo)","ok"); ktRender();
}
async function ktPhatHanhHddt(id){
  if(S.mode==="live"){ try{await api(`/ke-toan/hoa-don/${id}/phat-hanh-hddt`,{method:'POST',body:JSON.stringify({})});toast("Đã phát hành HĐĐT","ok");ktRender();}catch(e){toast(e.detail||e.message,"err");} return; }
  const h=(DEMO.ke_toan.hoa_don||[]).find(x=>x.id===id); if(h){h.hddt_trang_thai="DA_PHAT_HANH";h.da_hach_toan=true;} toast("Đã phát hành HĐĐT (demo)","ok"); ktRender();
}

function _ktDemoThu(){return (DEMO.ke_toan.phieu||[]).filter(p=>p.loai==="THU"&&p.trang_thai==="DA_DUYET").reduce((s,p)=>s+p.so_tien,0);}
async function ktPhieu(host){
  const canOp=can("ke_toan","THAO_TAC"), canDuyet=can("ke_toan","DUYET");
  let phieu, quy, orders, congno, nccs;
  if(S.mode==="live"){
    [phieu,quy,orders,nccs]=await Promise.all([api("/ke-toan/phieu"),api("/ke-toan/quy"),_nccOrders(),_nccSups()]);
    try{congno=await api("/ke-toan/cong-no-mo");}catch{congno=[];}
  } else { phieu=DEMO.ke_toan.phieu; quy=DEMO.ke_toan.quy; orders=DEMO.don_hang; nccs=DEMO.ncc.suppliers||[];
    const sup=id=>((DEMO.ncc.suppliers||[]).find(s=>s.id===id)||{}).ten||('NCC #'+id);
    congno=(DEMO.cong_no_ncc||[]).map(x=>({id:x.id,loai:"PHAI_TRA",ten_doi_tac:sup(x.nha_cung_cap_id),con_lai:(x.so_tien||0)-(x.da_thanh_toan||0),han:x.han,qua_han:x.trang_thai!=="DA_TRA"&&x.han&&new Date(x.han)<new Date()})).filter(c=>c.con_lai>0); }
  window.KTCN=congno;
  const nccOpt='<option value="">— chọn nhà cung cấp —</option>'+(nccs||[]).map(n=>`<option value="${n.id}">${n.ten}</option>`).join('');
  const ordOpt='<option value="">— không gắn —</option>'+(orders||[]).map(o=>`<option value="${o.id}">${o.so||('DH-'+o.id)}</option>`).join('');
  const quyOpt=(quy||[]).map(q=>`<option value="${q.id}">${q.ten} (${vnd(q.so_du)})</option>`).join('');
  const form=canOp?`<div class="panel"><div class="panel-h"><h3>Lập phiếu thu / chi</h3><div class="spacer"></div><button class="btn-sm" onclick="$('#pForm').classList.toggle('hidden')">+ Phiếu</button></div>
    <div id="pForm" class="hidden" style="padding:0 18px 14px">
     <div class="formrow"><div class="f"><label>Loại phiếu</label><select id="p_loai" onchange="ktOnLoaiChange()"><option value="THU">Phiếu THU (tiền vào)</option><option value="CHI">Phiếu CHI (tiền ra)</option></select></div>
       <div class="f"><label>Quỹ / tài khoản</label><select id="p_quy">${quyOpt}</select></div>
       <div class="f"><label>Số tiền</label><input id="p_st" type="number" value="0"></div></div>
     <div class="formrow" style="padding-top:0"><div class="f"><label>Mã hàng bán (đơn hàng)</label><select id="p_dh" data-ph="Gõ mã đơn…">${ordOpt}</select></div>
       <div class="f"><label>Cấn trừ công nợ <span style="color:var(--muted);font-weight:normal" id="p_cn_hint">(nợ khách hàng)</span></label><select id="p_cn" onchange="ktOnCnChange()">${_ktCnOptions('THU')}</select></div>
       <div class="f"><label>TK đối ứng</label><input id="p_tk" placeholder="tự suy luận: 131/331/511/642…"></div></div>
     <div class="formrow" style="padding-top:0"><div class="f"><label style="font-weight:normal;font-size:13px"><input type="checkbox" id="p_tu" onchange="ktOnTuChange()"> Tạm ứng / Trả trước <span style="color:var(--muted)">(chưa có hóa đơn — sẽ tự cấn trừ sau)</span></label></div>
       <div class="f" id="p_nccw" style="display:none"><label>Nhà cung cấp (trả trước)</label><select id="p_ncc" data-ph="Gõ tên NCC…">${nccOpt}</select></div></div>
     <div class="formrow" style="padding-top:0"><div class="f" style="flex:3"><label>Diễn giải</label><input id="p_dg" placeholder="VD: Thu tạm ứng đợt 1 / Chi phí lắp đặt"></div>
       <div class="f"><label style="font-weight:normal;font-size:13px"><input type="checkbox" id="p_trinh" checked> Trình duyệt luôn</label></div>
       <button class="btn-sm" onclick="ktTaoPhieu()">Lưu phiếu</button></div></div></div>`:'';
  const rows=(phieu||[]).map(p=>{
    const tt=KT_TT[p.trang_thai]||[p.trang_thai,'b-cho'];
    let act='';
    if(p.trang_thai==="NHAP"&&canOp)act+=`<button class="btn-sm" onclick="ktTrinh(${p.id})">Trình</button> <button class="btn-sm ghost" onclick="ktHuy(${p.id})">Hủy</button>`;
    else if(p.trang_thai==="CHO_DUYET"&&canDuyet)act+=`<button class="btn-sm" onclick="ktDuyet(${p.id})">Duyệt</button> <button class="btn-sm ghost" onclick="ktTuChoi(${p.id})">Từ chối</button>`;
    else if(p.trang_thai==="CHO_DUYET"&&canOp)act+=`<button class="btn-sm ghost" onclick="ktHuy(${p.id})">Hủy</button>`;
    return `<tr><td><b>${p.so||('#'+p.id)}</b></td><td><span class="badge ${p.loai==="THU"?'b-ok':'b-tc'}">${p.loai}</span></td>
      <td>${p.ten_quy||''}</td><td>${p.ten_doi_tac||p.dien_giai||'—'}${p.la_tam_ung?` <span class="badge b-cho">Tạm ứng${p.con_lai_tam_ung>0?' · còn '+vnd(p.con_lai_tam_ung):' · đã cấn trừ'}</span>`:''}</td>
      <td>${p.ma_ban?`<span class="badge b-info">${p.ma_ban}</span>`:'—'}</td>
      <td class="num"><b>${vnd(p.so_tien)}</b></td>
      <td><span class="badge ${tt[1]}">${tt[0]}</span></td><td>${act||'—'}</td></tr>`;}).join('');
  host.innerHTML=form+`<div class="note" style="padding:0 0 10px">Phiếu được lập (Nháp) → <b>trình</b> → <b>duyệt theo hạn mức</b> (KTT ≤ 50tr, vượt mức tự chuyển CEO). Khi duyệt: cộng/trừ quỹ, cấn trừ công nợ, sinh bút toán sổ cái, gắn mã hàng bán.</div>
    <div class="panel"><div class="panel-h"><h3>Danh sách phiếu thu–chi</h3></div>
    <div class="panel-b"><table><thead><tr><th>Số CT</th><th>Loại</th><th>Quỹ</th><th>Đối tác / diễn giải</th><th>Mã bán</th><th class="num">Số tiền</th><th>Trạng thái</th><th>Hành động</th></tr></thead>
    <tbody>${rows||'<tr><td colspan="8" class="empty" style="padding:18px">Chưa có phiếu.</td></tr>'}</tbody></table></div></div>`;
}
function _ktCnOptions(loai){
  const want=loai==="THU"?"PHAI_THU":"PHAI_TRA";
  const list=(window.KTCN||[]).filter(c=>c.loai===want);
  return '<option value="">— không cấn trừ —</option>'+list.map(c=>`<option value="${c.id}" data-con="${c.con_lai}">${c.ten_doi_tac} · còn ${vnd(c.con_lai)}${c.han?(' · hạn '+c.han):''}${c.qua_han?' ⚠ quá hạn':''}</option>`).join('');
}
function ktOnLoaiChange(){
  const l=gv('p_loai'); const sel=document.getElementById('p_cn'); if(sel)sel.innerHTML=_ktCnOptions(l);
  const hint=document.getElementById('p_cn_hint'); if(hint)hint.textContent=l==="THU"?"(nợ khách hàng)":"(nợ nhà cung cấp)";
  ktOnTuChange();
}
function ktOnTuChange(){
  const tu=document.getElementById('p_tu')?.checked, l=gv('p_loai');
  const cn=document.getElementById('p_cn'); if(cn){cn.disabled=!!tu; if(tu)cn.value='';}
  const cnf=cn?cn.closest('.f'):null; if(cnf)cnf.style.opacity=tu?'.45':'';
  const nw=document.getElementById('p_nccw'); if(nw)nw.style.display=(tu&&l==="CHI")?'':'none';
}
function ktOnCnChange(){
  const sel=document.getElementById('p_cn'); if(!sel)return;
  const opt=sel.options[sel.selectedIndex]; const con=opt?Number(opt.getAttribute('data-con')||0):0;
  const st=document.getElementById('p_st'); if(con>0 && st && (!st.value||Number(st.value)===0)) st.value=con;
}
async function ktTaoPhieu(){
  const loai=gv('p_loai'),quy_id=Number(gv('p_quy')),so_tien=Number(gv('p_st')||0);
  if(!quy_id||so_tien<=0){toast("Chọn quỹ và số tiền > 0","err");return;}
  const tu=document.getElementById('p_tu')?.checked===true;
  if(tu && !gv('p_dh')){toast("Tạm ứng/Trả trước phải gắn mã hàng bán","err");return;}
  if(tu && loai==="CHI" && !gv('p_ncc')){toast("Chọn nhà cung cấp cho khoản trả trước","err");return;}
  const body={loai,quy_id,so_tien,don_hang_id:gv('p_dh')?Number(gv('p_dh')):null,
    cong_no_id:(!tu&&gv('p_cn'))?Number(gv('p_cn')):null,tk_doi_ung:gv('p_tk')||null,
    dien_giai:gv('p_dg')||null,la_tam_ung:tu,trinh_luon:document.getElementById('p_trinh')?.checked!==false};
  if(tu && loai==="CHI")body.nha_cung_cap_id=Number(gv('p_ncc'));
  if(S.mode==="live"){ try{await api("/ke-toan/phieu",{method:'POST',body:JSON.stringify(body)});toast(tu?"Đã lập khoản tạm ứng/trả trước":"Đã lập phiếu","ok");ktRender();}catch(e){toast(e.detail||e.message,"err");} return; }
  const id=Date.now(); const q=DEMO.ke_toan.quy.find(x=>x.id===quy_id); const dh=(DEMO.don_hang||[]).find(o=>o.id===body.don_hang_id);
  DEMO.ke_toan.phieu.unshift({id,so:(loai==="THU"?"PT":"PC")+"-"+id,loai,quy_id,ten_quy:q?q.ten:'',so_tien,dien_giai:body.dien_giai,don_hang_id:body.don_hang_id,ma_ban:dh?dh.so:null,cong_no_id:body.cong_no_id,tk_doi_ung:body.tk_doi_ung,la_tam_ung:tu,con_lai_tam_ung:tu?so_tien:0,trang_thai:body.trinh_luon?"CHO_DUYET":"NHAP"});
  toast(tu?"Đã lập tạm ứng (demo)":"Đã lập phiếu (demo)","ok"); ktRender();
}
async function _ktAction(id,path,okmsg){
  if(S.mode==="live"){ try{await api(`/ke-toan/phieu/${id}/${path}`,{method:'POST'});toast(okmsg,"ok");ktRender();}catch(e){toast(e.detail||e.message,"err");} return; }
  const p=(DEMO.ke_toan.phieu||[]).find(x=>x.id===id); if(!p)return;
  if(path==="trinh")p.trang_thai="CHO_DUYET";
  else if(path==="duyet"){ p.trang_thai="DA_DUYET"; const q=DEMO.ke_toan.quy.find(x=>x.id===p.quy_id); if(q)q.so_du+=(p.loai==="THU"?p.so_tien:-p.so_tien); }
  else if(path==="tu-choi")p.trang_thai="TU_CHOI";
  else if(path==="huy")p.trang_thai="HUY";
  toast(okmsg+" (demo)","ok"); ktRender();
}
function ktTrinh(id){_ktAction(id,"trinh","Đã trình duyệt");}
function ktDuyet(id){_ktAction(id,"duyet","Đã duyệt phiếu (đã hạch toán)");}
function ktTuChoi(id){_ktAction(id,"tu-choi","Đã từ chối");}
function ktHuy(id){if(confirm("Hủy phiếu này?"))_ktAction(id,"huy","Đã hủy phiếu");}

async function ktLaiLo(host){
  let rows;
  if(S.mode==="live"){ rows=await api("/ke-toan/lai-lo-ma-ban"); }
  else { rows=(DEMO.don_hang||[]).map(o=>{const gv_=(DEMO.don_mua||[]).filter(d=>d.don_hang_id===o.id).reduce((s,d)=>s+(d.tong_tien||0),0);
    const cp=(DEMO.ke_toan.phieu||[]).filter(p=>p.don_hang_id===o.id&&p.loai==="CHI"&&p.trang_thai==="DA_DUYET"&&p.tk_doi_ung!=="331").reduce((s,p)=>s+p.so_tien,0);
    const thu=(DEMO.ke_toan.phieu||[]).filter(p=>p.don_hang_id===o.id&&p.loai==="THU"&&p.trang_thai==="DA_DUYET").reduce((s,p)=>s+p.so_tien,0);
    const ln=(o.tong_tien||0)-gv_-cp; return {don_hang_id:o.id,ma_ban:o.so,doanh_thu:o.tong_tien||0,gia_von:gv_,chi_phi_khac:cp,loi_nhuan:ln,ty_suat:o.tong_tien?Math.round(ln/o.tong_tien*1000)/10:null,da_thu:thu,con_phai_thu:Math.max((o.tong_tien||0)-thu,0)};}); }
  const tr=rows.map(x=>`<tr><td><b>${x.ma_ban}</b></td><td class="num">${vnd(x.doanh_thu)}</td><td class="num">${vnd(x.gia_von)}</td>
    <td class="num">${vnd(x.chi_phi_khac)}</td><td class="num"><b style="color:${x.loi_nhuan>=0?'#16a34a':'#dc2626'}">${vnd(x.loi_nhuan)}</b></td>
    <td class="num">${x.ty_suat!=null?x.ty_suat+'%':'—'}</td>
    <td class="num">${vnd(x.tam_ung_thu||0)}${x.tam_ung_thu_con_lai>0?`<br><span style="font-size:11px;color:var(--muted)">còn ${vnd(x.tam_ung_thu_con_lai)}</span>`:''}</td>
    <td class="num">${vnd(x.tam_ung_chi||0)}${x.tam_ung_chi_con_lai>0?`<br><span style="font-size:11px;color:var(--muted)">còn ${vnd(x.tam_ung_chi_con_lai)}</span>`:''}</td>
    <td class="num">${vnd(x.con_phai_thu)}</td>
    <td><button class="btn-sm ghost" onclick="ktThe(${x.don_hang_id})">Thẻ chi tiết</button></td></tr>`).join('');
  host.innerHTML=`<div class="note" style="padding:0 0 10px">Lãi/lỗ theo từng <b>mã hàng bán</b>: Doanh thu (đơn hàng) − Giá vốn (các PO mua phục vụ đơn) − Chi phí trực tiếp. Cột <b>Tạm ứng thu</b> = khách trả trước, <b>Trả trước</b> = ứng cho NCC; "còn" là phần chưa cấn trừ vào hóa đơn. Bấm <b>Thẻ chi tiết</b> để xem toàn bộ chứng từ.</div>
    <div class="panel"><div class="panel-h"><h3>Lãi/lỗ &amp; trả trước theo mã hàng bán</h3></div>
    <div class="panel-b"><table><thead><tr><th>Mã bán</th><th class="num">Doanh thu</th><th class="num">Giá vốn</th><th class="num">Chi phí khác</th><th class="num">Lợi nhuận</th><th class="num">Tỷ suất</th><th class="num">Tạm ứng thu</th><th class="num">Trả trước NCC</th><th class="num">Còn phải thu</th><th></th></tr></thead>
    <tbody>${tr||'<tr><td colspan="10" class="empty">Chưa có mã hàng bán.</td></tr>'}</tbody></table></div></div>`;
}
async function ktThe(id){
  if(S.mode!=="live"){toast("Thẻ chi tiết hiển thị đầy đủ ở bản kết nối backend","err");return;}
  const d=await api(`/ke-toan/the-ma-ban/${id}`); const t=d.tom_tat;
  const po=d.don_mua.map(p=>`<tr><td>${p.so}</td><td class="num">${vnd(p.tong_tien)}</td><td>${p.trang_thai}</td></tr>`).join('')||'<tr><td colspan="3" class="empty">—</td></tr>';
  const ph2=d.phieu.map(p=>`<tr><td>${p.so}</td><td>${p.loai}${p.la_tam_ung?' <span class="badge b-cho">tạm ứng</span>':''}</td><td class="num">${vnd(p.so_tien)}</td><td>${(KT_TT[p.trang_thai]||[p.trang_thai])[0]}</td></tr>`).join('')||'<tr><td colspan="4" class="empty">—</td></tr>';
  const bt=d.but_toan.map(b=>`<tr><td>${b.ngay}</td><td>Nợ ${b.tk_no} / Có ${b.tk_co}</td><td class="num">${vnd(b.so_tien)}</td><td>${b.dien_giai||''}</td></tr>`).join('')||'<tr><td colspan="4" class="empty">—</td></tr>';
  _ktModal(`Thẻ mã hàng bán — ${d.don_hang.so}`,
    `<div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:10px">
      ${_ktCard("Doanh thu",vnd(t.doanh_thu))}${_ktCard("Giá vốn",vnd(t.gia_von))}${_ktCard("Chi phí khác",vnd(t.chi_phi_khac))}${_ktCard("Lợi nhuận",vnd(t.loi_nhuan),t.loi_nhuan>=0?'#16a34a':'#dc2626')}
      ${_ktCard("Đã thu",vnd(t.da_thu))}${_ktCard("Còn phải thu",vnd(t.con_phai_thu))}
      ${_ktCard("KH tạm ứng",vnd(t.tam_ung_thu||0)+(t.tam_ung_thu_con_lai>0?' (còn '+vnd(t.tam_ung_thu_con_lai)+')':''))}
      ${_ktCard("Trả trước NCC",vnd(t.tam_ung_chi||0)+(t.tam_ung_chi_con_lai>0?' (còn '+vnd(t.tam_ung_chi_con_lai)+')':''))}</div>
    <div style="font-weight:600;margin:6px 0">Đơn mua (giá vốn)</div><table><thead><tr><th>PO</th><th class="num">Giá trị</th><th>Trạng thái</th></tr></thead><tbody>${po}</tbody></table>
    <div style="font-weight:600;margin:10px 0 6px">Phiếu thu / chi</div><table><thead><tr><th>Số CT</th><th>Loại</th><th class="num">Số tiền</th><th>Trạng thái</th></tr></thead><tbody>${ph2}</tbody></table>
    <div style="font-weight:600;margin:10px 0 6px">Bút toán sổ cái</div><table><thead><tr><th>Ngày</th><th>Định khoản</th><th class="num">Số tiền</th><th>Diễn giải</th></tr></thead><tbody>${bt}</tbody></table>`);
}

async function ktThongKe(host){
  if(!S.tkF)S.tkF={tu:'',den:'',quy_id:''};
  let d, quy;
  if(S.mode==="live"){
    quy=await api("/ke-toan/quy");
    const qs=new URLSearchParams();
    if(S.tkF.tu)qs.set('tu_ngay',S.tkF.tu); if(S.tkF.den)qs.set('den_ngay',S.tkF.den); if(S.tkF.quy_id)qs.set('quy_id',S.tkF.quy_id);
    d=await api("/ke-toan/thong-ke-thu-chi"+(qs.toString()?('?'+qs):''));
  } else { quy=DEMO.ke_toan.quy; d=_tkDemo(); }
  const quyOpt='<option value="">Tất cả quỹ</option>'+(quy||[]).map(q=>`<option value="${q.id}" ${String(S.tkF.quy_id)===String(q.id)?'selected':''}>${q.ten}</option>`).join('');
  // biểu đồ cột theo tháng
  const mx=Math.max(1,...d.theo_thang.map(m=>Math.max(m.thu,m.chi)));
  const bars=d.theo_thang.map(m=>`<div style="flex:1;min-width:54px;text-align:center">
    <div style="display:flex;gap:3px;align-items:flex-end;justify-content:center;height:130px">
      <div title="Thu ${vnd(m.thu)}" style="width:15px;height:${Math.max(2,Math.round(m.thu/mx*130))}px;background:#16a34a;border-radius:3px 3px 0 0"></div>
      <div title="Chi ${vnd(m.chi)}" style="width:15px;height:${Math.max(2,Math.round(m.chi/mx*130))}px;background:#dc2626;border-radius:3px 3px 0 0"></div>
    </div><div style="font-size:11px;color:var(--muted);margin-top:4px">${m.ky}</div></div>`).join('')||'<div class="empty" style="padding:20px">Chưa có dữ liệu trong kỳ.</div>';
  const loaiRows=d.theo_loai.map(r=>`<tr><td><b>${r.tk}</b></td><td>${r.ten_tk||''}</td><td class="num" style="color:#16a34a">${r.thu?vnd(r.thu):''}</td><td class="num" style="color:#dc2626">${r.chi?vnd(r.chi):''}</td></tr>`).join('');
  const mbRows=d.theo_ma_ban.map(r=>`<tr><td>${r.ma_ban}</td><td class="num" style="color:#16a34a">${r.thu?vnd(r.thu):''}</td><td class="num" style="color:#dc2626">${r.chi?vnd(r.chi):''}</td><td class="num"><b style="color:${r.rong<0?'#dc2626':'#16a34a'}">${vnd(r.rong)}</b></td></tr>`).join('');
  const quyRows=(d.theo_quy||[]).map(r=>`<tr><td>${r.quy}</td><td class="num" style="color:#16a34a">${vnd(r.thu)}</td><td class="num" style="color:#dc2626">${vnd(r.chi)}</td><td class="num"><b>${vnd(r.thu-r.chi)}</b></td></tr>`).join('');
  host.innerHTML=`<div class="panel"><div class="panel-b" style="display:flex;flex-wrap:wrap;gap:10px;align-items:end;padding:14px 18px">
      <div class="f" style="min-width:150px"><label>Từ ngày</label><input type="date" id="tk_tu" value="${S.tkF.tu||''}"></div>
      <div class="f" style="min-width:150px"><label>Đến ngày</label><input type="date" id="tk_den" value="${S.tkF.den||''}"></div>
      <div class="f" style="min-width:180px"><label>Quỹ</label><select id="tk_quy">${quyOpt}</select></div>
      <button class="btn-sm" onclick="ktTkApply()">Lọc</button>
      <button class="btn-sm ghost" onclick="S.tkF={tu:'',den:'',quy_id:''};ktRender()">Xóa lọc</button></div></div>
    <div style="display:flex;flex-wrap:wrap;gap:8px;padding:0 0 14px">
      ${_ktCard("Tổng thu",vnd(d.tong_thu),'#16a34a')}${_ktCard("Tổng chi",vnd(d.tong_chi),'#dc2626')}
      ${_ktCard("Dòng tiền ròng",vnd(d.rong),d.rong<0?'#dc2626':'#16a34a')}${_ktCard("Số phiếu",d.so_phieu||0)}</div>
    <div class="panel"><div class="panel-h"><h3>Thu–chi theo tháng</h3><div class="spacer"></div>
      <span style="font-size:12px;color:var(--muted)"><span style="color:#16a34a">■</span> Thu &nbsp; <span style="color:#dc2626">■</span> Chi</span></div>
      <div class="panel-b"><div style="display:flex;gap:8px;align-items:flex-end;overflow-x:auto;padding:6px 2px">${bars}</div></div></div>
    <div class="panel"><div class="panel-h"><h3>Thu–chi theo mã hàng bán (kiểm soát tiền dự án)</h3></div>
      <div class="panel-b"><table><thead><tr><th>Mã bán / dự án</th><th class="num">Thu</th><th class="num">Chi</th><th class="num">Ròng</th></tr></thead>
      <tbody>${mbRows||'<tr><td colspan="4" class="empty">—</td></tr>'}</tbody></table></div></div>
    <div class="panel"><div class="panel-h"><h3>Thu–chi theo loại tài khoản</h3></div>
      <div class="panel-b"><table><thead><tr><th>TK</th><th>Tên tài khoản</th><th class="num">Thu</th><th class="num">Chi</th></tr></thead>
      <tbody>${loaiRows||'<tr><td colspan="4" class="empty">—</td></tr>'}</tbody></table></div></div>
    <div class="panel"><div class="panel-h"><h3>Thu–chi theo quỹ</h3></div>
      <div class="panel-b"><table><thead><tr><th>Quỹ</th><th class="num">Thu</th><th class="num">Chi</th><th class="num">Ròng</th></tr></thead>
      <tbody>${quyRows||'<tr><td colspan="4" class="empty">—</td></tr>'}</tbody></table></div></div>`;
}
function ktTkApply(){ S.tkF={tu:gv('tk_tu'),den:gv('tk_den'),quy_id:gv('tk_quy')}; ktRender(); }
function _tkDemo(){
  const ps=(DEMO.ke_toan.phieu||[]).filter(p=>p.trang_thai==="DA_DUYET"
    &&(!S.tkF.tu||(p.ngay||'')>=S.tkF.tu)&&(!S.tkF.den||(p.ngay||'')<=S.tkF.den)&&(!S.tkF.quy_id||String(p.quy_id)===String(S.tkF.quy_id)));
  const thang={},loai={},quy={},mb={}; let tThu=0,tChi=0;
  const qn=id=>((DEMO.ke_toan.quy||[]).find(q=>q.id===id)||{}).ten||('Quỹ '+id);
  ps.forEach(p=>{const a=p.so_tien; const off=p.tk_doi_ung||(p.loai==="THU"?"131":"642"); const ky=(p.ngay||'').slice(0,7)||'—'; const m=p.ma_ban||'(không gắn)';
    [[thang,ky],[loai,off],[quy,qn(p.quy_id)],[mb,m]].forEach(([d,k])=>{const g=d[k]||(d[k]={thu:0,chi:0});g[p.loai==="THU"?"thu":"chi"]+=a;});
    if(p.loai==="THU")tThu+=a;else tChi+=a;});
  return {tong_thu:tThu,tong_chi:tChi,rong:tThu-tChi,so_phieu:ps.length,
    theo_thang:Object.entries(thang).sort().map(([ky,v])=>({ky,...v,rong:v.thu-v.chi})),
    theo_loai:Object.entries(loai).map(([tk,v])=>({tk,ten_tk:'',...v})).sort((a,b)=>(b.thu+b.chi)-(a.thu+a.chi)),
    theo_quy:Object.entries(quy).map(([quy,v])=>({quy,...v})),
    theo_ma_ban:Object.entries(mb).map(([ma_ban,v])=>({ma_ban,...v,rong:v.thu-v.chi})).sort((a,b)=>(b.thu+b.chi)-(a.thu+a.chi))};
}

async function ktTraTruoc(host){
  const canOp=can("ke_toan","THAO_TAC");
  const COC={DU:['Đủ cọc','b-ok'],THIEU:['Thiếu cọc','b-tc'],VUOT:['Vượt cọc','b-cho'],KHONG:['—','']};
  let bc, lailo;
  if(S.mode==="live"){ [bc,lailo]=await Promise.all([api("/ke-toan/bao-cao-tra-truoc"),api("/ke-toan/lai-lo-ma-ban")]); }
  else {
    const adv=(DEMO.ke_toan.phieu||[]).filter(p=>p.la_tam_ung&&p.trang_thai==="DA_DUYET");
    lailo=(DEMO.don_hang||[]).map(o=>{const ty=o._coc||0; const dk=Math.round((o.tong_tien||0)*ty/100);
      const ung=adv.filter(p=>p.don_hang_id===o.id&&p.loai==="THU").reduce((s,p)=>s+p.so_tien,0);
      const st=ty<=0?"KHONG":ung<dk*0.999?"THIEU":ung>dk*1.001?"VUOT":"DU";
      return {don_hang_id:o.id,ma_ban:o.so,doanh_thu:o.tong_tien||0,ty_le_dat_coc:ty,dat_coc_du_kien:dk,dat_coc_da_ung:ung,coc_chenh_lech:ung-dk,coc_trang_thai:st};});
    const nhom={};
    adv.forEach(p=>{const con=p.con_lai_tam_ung||0; if(con<=0)return; const k=(p.loai==="THU"?"KH":"NCC")+(p.ten_doi_tac||p.nha_cung_cap_id||'');
      const g=nhom[k]||(nhom[k]={doi_tac_loai:p.loai==="THU"?"KH":"NCC",ten:p.ten_doi_tac||'(đối tác)',so_khoan:0,con_treo:0});g.so_khoan++;g.con_treo+=con;});
    const td=Object.values(nhom);
    bc={theo_doi_tac:td,tong_treo_thu:td.filter(g=>g.doi_tac_loai==="KH").reduce((s,g)=>s+g.con_treo,0),tong_treo_chi:td.filter(g=>g.doi_tac_loai==="NCC").reduce((s,g)=>s+g.con_treo,0)};
  }
  const soThieu=lailo.filter(x=>x.coc_trang_thai==="THIEU").length;
  const cards=_ktCard("Khách còn treo (chưa cấn trừ)",vnd(bc.tong_treo_thu))+
    _ktCard("Đã trả trước NCC còn treo",vnd(bc.tong_treo_chi))+
    _ktCard("Đơn thiếu cọc",soThieu,soThieu>0?'#dc2626':'#16a34a');
  const aRows=lailo.map(x=>{const [lbl,cls]=COC[x.coc_trang_thai]||['—',''];
    return `<tr class="${x.coc_trang_thai==="THIEU"?'qh':''}"><td><b>${x.ma_ban}</b></td><td class="num">${vnd(x.doanh_thu)}</td>
    <td class="num">${canOp?`<input type="number" id="coc_${x.don_hang_id}" value="${x.ty_le_dat_coc||0}" style="width:62px;text-align:right;padding:4px 6px"> %`:(x.ty_le_dat_coc||0)+'%'}</td>
    <td class="num">${vnd(x.dat_coc_du_kien)}</td><td class="num">${vnd(x.dat_coc_da_ung)}</td>
    <td class="num" style="color:${x.coc_chenh_lech<0?'#dc2626':'#16a34a'}">${x.coc_chenh_lech>0?'+':''}${vnd(x.coc_chenh_lech)}</td>
    <td>${x.ty_le_dat_coc>0?`<span class="badge ${cls}">${lbl}</span>`:'<span style="color:var(--muted)">chưa đặt</span>'}</td>
    ${canOp?`<td><button class="btn-sm ghost" onclick="ktSetCoc(${x.don_hang_id})">Lưu</button></td>`:'<td>—</td>'}</tr>`;}).join('');
  const bRows=(bc.theo_doi_tac||[]).map(g=>`<tr><td><span class="badge ${g.doi_tac_loai==="KH"?'b-ok':'b-tc'}">${g.doi_tac_loai==="KH"?'Khách':'NCC'}</span></td>
    <td>${g.ten}</td><td class="num">${g.so_khoan}</td><td class="num"><b>${vnd(g.con_treo)}</b></td></tr>`).join('');
  host.innerHTML=`<div class="note" style="padding:0 0 10px">Đặt <b>% cọc dự kiến</b> cho từng mã hàng bán; hệ thống đối chiếu với số khách <b>đã ứng</b> và cảnh báo <b>Thiếu/Đủ/Vượt</b>. Bảng dưới tổng hợp khoản trả trước <b>còn treo</b> (chưa cấn trừ vào hóa đơn) theo từng khách/NCC.</div>
    <div style="display:flex;flex-wrap:wrap;gap:8px;padding:0 0 14px">${cards}</div>
    <div class="panel"><div class="panel-h"><h3>Cam kết đặt cọc theo mã hàng bán</h3></div>
    <div class="panel-b"><table><thead><tr><th>Mã bán</th><th class="num">Giá trị</th><th class="num">% cọc</th><th class="num">Cọc dự kiến</th><th class="num">Đã ứng</th><th class="num">Chênh lệch</th><th>Trạng thái</th><th></th></tr></thead>
    <tbody>${aRows||'<tr><td colspan="8" class="empty">Chưa có mã hàng bán.</td></tr>'}</tbody></table></div></div>
    <div class="panel"><div class="panel-h"><h3>Khoản trả trước còn treo theo đối tác</h3></div>
    <div class="panel-b"><table><thead><tr><th>Đối tác</th><th>Tên</th><th class="num">Số khoản</th><th class="num">Còn treo</th></tr></thead>
    <tbody>${bRows||'<tr><td colspan="4" class="empty">Không còn khoản trả trước nào treo.</td></tr>'}</tbody></table></div></div>`;
}
async function ktSetCoc(id){
  const ty=Number(gv('coc_'+id)||0);
  if(ty<0||ty>100){toast("% cọc trong khoảng 0–100","err");return;}
  if(S.mode==="live"){ try{await api(`/ke-toan/ma-ban/${id}/dat-coc`,{method:'PUT',body:JSON.stringify({ty_le:ty})});toast("Đã lưu % cọc","ok");ktRender();}catch(e){toast(e.detail||e.message,"err");} return; }
  const o=(DEMO.don_hang||[]).find(x=>x.id===id); if(o)o._coc=ty; toast("Đã lưu % cọc (demo)","ok"); ktRender();
}

async function ktCanDoi(host){
  // placeholder anchor for insertion (real body below)
  return _ktCanDoiReal(host);
}
/* ---- Tab Trích lập quỹ (được trừ / sau thuế) ---- */
async function qtTrichLap(host){
  const canOp=can("ke_toan","THAO_TAC");
  if(!S.qtNam)S.qtNam=String(new Date().getFullYear());
  let tq,cb;
  if(S.mode==="live"){
    const tnttQ=S.qtTntt?`&thu_nhap_tinh_thue=${S.qtTntt}`:'';
    [tq,cb]=await Promise.all([api(`/quy-trich-lap?nam=${S.qtNam}`),api(`/quy-trich-lap/canh-bao?nam=${S.qtNam}${tnttQ}`)]);
  } else { tq=_qtDemo(); cb=_qtDemoCB(); }
  const quy=tq.quy||[];
  const truoc=quy.filter(q=>q.duoc_tru), sau=quy.filter(q=>!q.duoc_tru);
  // bộ lọc năm + thu nhập tính thuế
  let html=`<div class="panel"><div class="panel-b" style="display:flex;flex-wrap:wrap;gap:10px;align-items:end;padding:14px 18px">
    <div class="f" style="min-width:110px"><label>Năm</label><input type="number" id="qt_nam" value="${S.qtNam}"></div>
    <div class="f" style="min-width:200px"><label>Thu nhập tính thuế (để kiểm trần KH&CN)</label><input type="number" id="qt_tntt" value="${S.qtTntt||''}" placeholder="ước tính từ sổ cái nếu để trống"></div>
    <button class="btn-sm ghost" onclick="qtApply()">Áp dụng</button></div></div>`;
  html+=`<div style="display:flex;flex-wrap:wrap;gap:8px;padding:0 0 12px">
    ${_tcCard("Quỹ trích TRƯỚC thuế (được trừ)",vnd(tq.tong_truoc_thue),"giảm thu nhập chịu thuế",'#16a34a')}
    ${_tcCard("Quỹ trích SAU thuế (không được trừ)",vnd(tq.tong_sau_thue),"từ lợi nhuận sau thuế",'#dc2626')}
    ${_tcCard("Cảnh báo vượt trần",(cb.canh_bao||[]).length,(cb.canh_bao||[]).length?'cần xử lý':'không có',(cb.canh_bao||[]).length?'#dc2626':'#16a34a')}</div>`;
  // cảnh báo trần
  html+=`<div class="panel"><div class="panel-h"><h3>Kiểm soát trần theo Luật Thuế TNDN 2025</h3></div><div class="panel-b">
    <div style="display:flex;flex-wrap:wrap;gap:14px;font-size:13px;margin-bottom:8px">
      <span>Quỹ KH&CN: đã trích <b>${vnd(cb.trich_khcn)}</b> / trần 20% TNTT <b>${vnd(cb.tran_khcn)}</b></span>
      <span>Chi phúc lợi: đã chi <b>${vnd(cb.chi_phuc_loi)}</b> / trần 1 tháng lương BQ <b>${vnd(cb.luong_thang_bq)}</b></span></div>
    ${(cb.canh_bao||[]).map(c=>`<div style="display:flex;gap:10px;padding:9px 0;border-top:1px solid var(--line)"><span class="badge ${c.muc_do==='CAO'?'b-tc':'b-cho'}" style="height:fit-content">${c.muc_do==='CAO'?'Cao':'Lưu ý'}</span><div><div style="font-weight:600">${c.tieu_de}</div><div style="color:var(--muted);font-size:13px">${c.chi_tiet}</div><div style="font-size:13px;margin-top:2px">💡 ${c.goi_y}</div></div></div>`).join('')||'<div class="empty" style="padding:8px">Các quỹ trong giới hạn cho phép.</div>'}</div></div>`;
  // form trích lập / sử dụng
  if(canOp){
    const opt=g=>g.map(q=>`<option value="${q.ma}">${q.ten} (Nợ ${q.tk_no}/Có ${q.tk_co})</option>`).join('');
    html+=`<div class="panel"><div class="panel-h"><h3>Trích lập / sử dụng quỹ</h3></div><div class="panel-b">
      <div class="formrow"><div class="f" style="flex:2"><label>Quỹ</label><select id="qt_quy">
        <optgroup label="── Trích TRƯỚC thuế (được trừ) ──">${opt(truoc)}</optgroup>
        <optgroup label="── Trích SAU thuế (không được trừ) ──">${opt(sau)}</optgroup></select></div>
        <div class="f"><label>Kỳ (năm hoặc YYYY-MM)</label><input id="qt_ky" value="${S.qtNam}"></div>
        <div class="f"><label>Số tiền</label><input id="qt_st" type="number" placeholder="0"></div>
        <div class="f" style="flex:2"><label>Diễn giải</label><input id="qt_dg" placeholder="VD: Trích quỹ KH&CN năm ${S.qtNam}"></div></div>
      <div style="display:flex;gap:8px"><button class="btn-sm" onclick="qtTrich()">Trích lập</button><button class="btn-sm ghost" onclick="qtSuDung()">Sử dụng quỹ</button></div></div></div>`;
  }
  // bảng quỹ
  const row=q=>`<tr><td><b>${q.ten}</b></td>
    <td>${q.duoc_tru?'<span class="badge b-ok">Được trừ</span>':'<span class="badge b-tc">Sau thuế</span>'}</td>
    <td style="font-size:12px;color:var(--muted)">Nợ ${q.tk_no} / Có ${q.tk_co}</td>
    <td class="num"><b>${vnd(q.so_du)}</b></td><td class="num">${vnd(q.trich_nam)}</td><td class="num">${vnd(q.su_dung_nam)}</td>
    <td><button class="btn-sm ghost" onclick="qtLichSu('${q.ma}','${q.ten.replace(/'/g,"")}')">Lịch sử</button></td></tr>`;
  html+=`<div class="panel"><div class="panel-h"><h3>Danh sách quỹ (năm ${S.qtNam})</h3></div><div class="panel-b"><table>
    <thead><tr><th>Quỹ</th><th>Tính chất</th><th>Hạch toán</th><th class="num">Số dư</th><th class="num">Trích năm</th><th class="num">Sử dụng năm</th><th></th></tr></thead>
    <tbody>${truoc.map(row).join('')}${sau.map(row).join('')}</tbody></table>
    <div class="note" style="margin-top:8px;color:var(--muted)"><b>Được trừ</b> = trích trước thuế, giảm thu nhập chịu thuế TNDN (dự phòng đúng quy định, Quỹ KH&CN ≤20%). <b>Sau thuế</b> = trích từ lợi nhuận sau thuế (khen thưởng, phúc lợi, đầu tư phát triển…), KHÔNG tính vào chi phí được trừ.</div></div></div>`;
  host.innerHTML=html;
}
function qtApply(){S.qtNam=gv('qt_nam')||S.qtNam;const t=gv('qt_tntt');S.qtTntt=t?Number(t):null;ktRender();}
async function qtTrich(){
  const body={ma_quy:gv('qt_quy'),ky:gv('qt_ky')||S.qtNam,so_tien:Number(gv('qt_st')||0),dien_giai:gv('qt_dg')||null};
  if(!body.ma_quy||body.so_tien<=0){toast("Chọn quỹ và số tiền > 0","err");return;}
  if(S.mode!=="live"){toast("Đã trích lập (demo)","ok");return;}
  try{const r=await api("/quy-trich-lap/trich",{method:'POST',body:JSON.stringify(body)});
    let m=`Đã trích lập · Nợ ${r.but_toan.no}/Có ${r.but_toan.co}`; if(r.canh_bao.length)m+=` ⚠️ ${r.canh_bao[0].tieu_de}`;
    toast(m,r.canh_bao.length?"err":"ok");ktRender();}catch(e){toast(e.detail||e.message,"err");}
}
async function qtSuDung(){
  const body={ma_quy:gv('qt_quy'),ky:gv('qt_ky')||S.qtNam,so_tien:Number(gv('qt_st')||0),dien_giai:gv('qt_dg')||null};
  if(!body.ma_quy||body.so_tien<=0){toast("Chọn quỹ và số tiền > 0","err");return;}
  if(S.mode!=="live"){toast("Đã sử dụng quỹ (demo)","ok");return;}
  try{const r=await api("/quy-trich-lap/su-dung",{method:'POST',body:JSON.stringify(body)});
    let m="Đã ghi sử dụng quỹ"; if(r.canh_bao.length)m+=` ⚠️ ${r.canh_bao[0].tieu_de}`; toast(m,r.canh_bao.length?"err":"ok");ktRender();}catch(e){toast(e.detail||e.message,"err");}
}
async function qtLichSu(ma,ten){
  let ls; try{ ls = S.mode==="live" ? await api(`/quy-trich-lap/${ma}/lich-su`) : []; }catch(e){toast(e.detail||e.message,"err");return;}
  const rows=ls.map(x=>`<tr><td>${x.ngay}</td><td>${x.loai==='TRICH_LAP'?'<span class="badge b-info">Trích lập</span>':'<span class="badge b-cho">Sử dụng</span>'}</td><td>${x.ky}</td><td class="num">${vnd(x.so_tien)}</td><td>${x.dien_giai||''}</td></tr>`).join('');
  _ktModal("Lịch sử quỹ — "+ten,`<table><thead><tr><th>Ngày</th><th>Loại</th><th>Kỳ</th><th class="num">Số tiền</th><th>Diễn giải</th></tr></thead><tbody>${rows||'<tr><td colspan="5" class="empty">Chưa có giao dịch.</td></tr>'}</tbody></table>`);
}
function _qtDemo(){return {nam:String(new Date().getFullYear()),tong_truoc_thue:70000000,tong_sau_thue:35000000,quy:[
  {ma:"KHCN",ten:"Quỹ phát triển khoa học & công nghệ",ban_chat:"TRUOC_THUE",duoc_tru:true,tk_no:"642",tk_co:"356",so_du:50000000,trich_nam:50000000,su_dung_nam:0},
  {ma:"DP_PTKD",ten:"Dự phòng nợ phải thu khó đòi",ban_chat:"TRUOC_THUE",duoc_tru:true,tk_no:"642",tk_co:"2293",so_du:20000000,trich_nam:20000000,su_dung_nam:0},
  {ma:"PHUC_LOI",ten:"Quỹ phúc lợi",ban_chat:"SAU_THUE",duoc_tru:false,tk_no:"421",tk_co:"3532",so_du:35000000,trich_nam:70000000,su_dung_nam:35000000},
  {ma:"KHEN_THUONG",ten:"Quỹ khen thưởng",ban_chat:"SAU_THUE",duoc_tru:false,tk_no:"421",tk_co:"3531",so_du:0,trich_nam:0,su_dung_nam:0}]};}
function _qtDemoCB(){return {tran_khcn:40000000,trich_khcn:50000000,luong_thang_bq:230000000/12,chi_phuc_loi:35000000,
  canh_bao:[{ma:"KHCN_20",muc_do:"CAO",tieu_de:"Quỹ KH&CN vượt trần 20%",chi_tiet:"Đã trích 50.000.000đ > trần 20% thu nhập tính thuế (40.000.000đ).",goi_y:"Giảm mức trích về ≤20% hoặc loại phần vượt khi quyết toán."}]};}

async function _ktCanDoiReal(host){
  let d;
  if(S.mode==="live"){ d=await api("/ke-toan/can-doi-phat-sinh"); }
  else { d={rows:[],tong_no:0,tong_co:0}; }
  const tr=(d.rows||[]).map(x=>`<tr><td><b>${x.tk}</b></td><td>${x.ten_tk||''}</td><td class="num">${vnd(x.ps_no)}</td><td class="num">${vnd(x.ps_co)}</td></tr>`).join('');
  const can=Math.abs((d.tong_no||0)-(d.tong_co||0))<1;
  host.innerHTML=`<div class="note" style="padding:0 0 10px">Bảng cân đối phát sinh tổng hợp từ <b>bút toán kép</b>. Tổng phát sinh Nợ phải bằng tổng phát sinh Có (nguyên tắc cân đối).</div>
    <div class="panel"><div class="panel-h"><h3>Cân đối phát sinh</h3><div class="spacer"></div>
      <span class="badge ${can?'b-ok':'b-tc'}">${can?'Cân đối ✓':'Lệch ✗'}</span></div>
    <div class="panel-b"><table><thead><tr><th>TK</th><th>Tên tài khoản</th><th class="num">PS Nợ</th><th class="num">PS Có</th></tr></thead>
    <tbody>${tr||'<tr><td colspan="4" class="empty">Chưa có bút toán. Hãy duyệt phiếu thu/chi hoặc phát hành hóa đơn.</td></tr>'}
    ${d.rows&&d.rows.length?`<tr style="font-weight:700;background:var(--surface)"><td colspan="2">TỔNG CỘNG</td><td class="num">${vnd(d.tong_no)}</td><td class="num">${vnd(d.tong_co)}</td></tr>`:''}</tbody></table></div></div>`;
}

function _ktModal(tieu_de,html){
  const old=document.getElementById('ktModal'); if(old)old.remove();
  const wrap=document.createElement('div'); wrap.id='ktModal';
  wrap.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.45);display:flex;align-items:center;justify-content:center;z-index:9999';
  wrap.onclick=e=>{if(e.target===wrap)wrap.remove();};
  const box=document.createElement('div');
  box.style.cssText='background:var(--surface,#fff);max-width:880px;width:94%;max-height:86vh;overflow:auto;border-radius:12px;padding:16px 18px;box-shadow:0 10px 40px rgba(0,0,0,.25)';
  box.innerHTML=`<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px"><div style="font-weight:700;flex:1">${tieu_de}</div><button class="btn-sm ghost" onclick="document.getElementById('ktModal').remove()">Đóng</button></div>${html}`;
  wrap.appendChild(box); document.body.appendChild(wrap);
}

/* ---------- TÀI CHÍNH: chỉ số doanh nghiệp · cảnh báo · cố vấn AI ---------- */
const TC_MUC={CAO:['Cao','b-tc'],TRUNG:['Trung bình','b-cho'],THAP:['Thấp','b-ok']};
function _num(x,d=2){return x==null?'—':Number(x).toLocaleString('vi-VN',{maximumFractionDigits:d});}
function _pct(x){return x==null?'—':(Number(x)*100).toLocaleString('vi-VN',{maximumFractionDigits:1})+'%';}
function _tcCard(label,value,sub,color){return `<div style="flex:1;min-width:160px;background:var(--surface);border-radius:10px;padding:12px 14px">
  <div style="color:var(--muted);font-size:12px">${label}</div>
  <div style="font-weight:700;margin-top:3px;font-size:18px;${color?('color:'+color):''}">${value}</div>
  ${sub?`<div style="color:var(--muted);font-size:11px;margin-top:2px">${sub}</div>`:''}</div>`;}
function _tcCol(v,good,ok){return v==null?'':(v>=good?'#16a34a':v>=ok?'#f59e0b':'#dc2626');}
function _tcGroup(title,cards){return `<div class="panel"><div class="panel-h"><h3>${title}</h3></div>
  <div class="panel-b" style="display:flex;flex-wrap:wrap;gap:8px">${cards}</div></div>`;}

async function viewTaiChinh(m){
  if(!S.tcDays)S.tcDays=90; if(!S.tcTab)S.tcTab="tongquan";
  const tabs=[["tongquan","Tổng quan & cảnh báo"],["cocau","Cân đối & ROA/ROE"],["vay","Tiền vay"],["dubao","Dự báo dòng tiền 13 tuần"]];
  m.innerHTML=head("Tài chính","Chỉ số tài chính doanh nghiệp · cảnh báo theo ngưỡng · cố vấn AI (CFO ảo)")
    +`<div class="tabs">${tabs.map(([k,l])=>`<button class="${S.tcTab===k?'active':''}" onclick="tcTab('${k}')">${l}</button>`).join('')}</div><div id="tcBody"></div>`;
  tcRender();
}
function tcTab(k){S.tcTab=k;tcRender();}
async function tcRender(){
  const h=document.getElementById('tcBody'); if(!h)return;
  h.innerHTML='<div class="empty" style="padding:20px">Đang tải…</div>';
  try{ if(S.tcTab==="cocau")await tcCoCau(h); else if(S.tcTab==="vay")await tcVay(h); else if(S.tcTab==="dubao")await tcDuBao(h); else await tcTongQuan(h); }
  catch(e){ h.innerHTML=`<div class="empty" style="padding:24px;color:#dc2626">${e.detail||e.message}</div>`; }
}
async function tcTongQuan(host){
  let d;
  d = S.mode==="live" ? await api(`/tai-chinh/chi-so?so_ngay=${S.tcDays}`) : _tcDemo();
  const cs=d.chi_so, cb=d.canh_bao||[];
  const diem=d.diem_suc_khoe;
  const diemCol=diem>=75?'#16a34a':diem>=50?'#f59e0b':'#dc2626';
  const periods=[[30,'30 ngày'],[90,'90 ngày'],[180,'6 tháng'],[365,'1 năm']];
  // Bộ lọc kỳ + nút AI
  let html=`<div style="display:flex;flex-wrap:wrap;gap:10px;align-items:center;padding:0 0 12px">
    <span style="color:var(--muted);font-size:13px">Kỳ phân tích:</span>
    ${periods.map(([v,l])=>`<button class="btn-sm ${S.tcDays===v?'':'ghost'}" onclick="tcSetDays(${v})">${l}</button>`).join('')}
    <div class="spacer" style="flex:1"></div>
    <button class="btn-sm" onclick="tcRunAI()">🤖 Phân tích bằng AI</button></div>`;
  // Sức khỏe tổng thể
  html+=`<div style="display:flex;flex-wrap:wrap;gap:8px;padding:0 0 12px">
    ${_tcCard("Điểm sức khỏe tài chính",diem+"/100",cb.length+" cảnh báo",diemCol)}
    ${_tcCard("Lợi nhuận thuần (kỳ)",vnd(cs.loi_nhuan_thuan),"DT − GV − chi phí",cs.loi_nhuan_thuan<0?'#dc2626':'#16a34a')}
    ${_tcCard("Dòng tiền ròng (kỳ)",vnd(cs.dong_tien_rong_ky),"tiền vào − tiền ra",cs.dong_tien_rong_ky<0?'#dc2626':'#16a34a')}
    ${_tcCard("Tiền mặt còn lại",cs.so_thang_tien_mat_con_lai!=null?_num(cs.so_thang_tien_mat_con_lai,1)+" tháng":"—","theo nhịp chi",_tcCol(cs.so_thang_tien_mat_con_lai,3,2))}</div>`;
  // Nhóm chỉ số
  html+=_tcGroup("Khả năng thanh toán (thanh khoản)",
    _tcCard("Thanh toán hiện hành",_num(cs.ty_so_thanh_toan_hien_hanh),"TSNH / Nợ ngắn hạn (≥1,5 tốt)",_tcCol(cs.ty_so_thanh_toan_hien_hanh,1.5,1))+
    _tcCard("Thanh toán nhanh",_num(cs.ty_so_thanh_toan_nhanh),"(Tiền+Phải thu)/Nợ NH",_tcCol(cs.ty_so_thanh_toan_nhanh,1,0.8))+
    _tcCard("Thanh toán tiền mặt",_num(cs.ty_so_thanh_toan_tien_mat),"Tiền / Nợ ngắn hạn",_tcCol(cs.ty_so_thanh_toan_tien_mat,0.5,0.2)));
  html+=_tcGroup(`Khả năng sinh lời (kỳ ${cs.ky_so_ngay} ngày)`,
    _tcCard("Doanh thu",vnd(cs.doanh_thu))+_tcCard("Giá vốn",vnd(cs.gia_von))+_tcCard("Chi phí",vnd(cs.chi_phi))+
    _tcCard("Biên LN gộp",_pct(cs.bien_loi_nhuan_gop),"(DT−GV)/DT",_tcCol(cs.bien_loi_nhuan_gop,0.25,0.1))+
    _tcCard("Biên LN thuần",_pct(cs.bien_loi_nhuan_thuan),null,_tcCol(cs.bien_loi_nhuan_thuan,0.1,0)));
  html+=_tcGroup("Hiệu quả & công nợ",
    _tcCard("Kỳ thu tiền BQ",cs.ky_thu_tien_bq!=null?_num(cs.ky_thu_tien_bq,0)+" ngày":"—","DSO (≤30 tốt)",cs.ky_thu_tien_bq==null?'':(cs.ky_thu_tien_bq<=30?'#16a34a':cs.ky_thu_tien_bq<=60?'#f59e0b':'#dc2626'))+
    _tcCard("Kỳ trả tiền BQ",cs.ky_tra_tien_bq!=null?_num(cs.ky_tra_tien_bq,0)+" ngày":"—","DPO")+
    _tcCard("Số ngày tồn kho",cs.so_ngay_ton_kho!=null?_num(cs.so_ngay_ton_kho,0)+" ngày":"—")+
    _tcCard("Phải thu",vnd(cs.phai_thu),cs.phai_thu_qua_han>0?('quá hạn '+vnd(cs.phai_thu_qua_han)):null,cs.phai_thu_qua_han>0?'#dc2626':'')+
    _tcCard("Phải trả",vnd(cs.phai_tra),cs.phai_tra_qua_han>0?('quá hạn '+vnd(cs.phai_tra_qua_han)):null,cs.phai_tra_qua_han>0?'#dc2626':''));
  html+=_tcGroup("Dòng tiền & tài sản",
    _tcCard("Tiền mặt & ngân hàng",vnd(cs.tien_mat_va_nh))+_tcCard("Tồn kho (ước tính)",vnd(cs.ton_kho))+
    _tcCard("Tiền vào (kỳ)",vnd(cs.tien_vao_ky),null,'#16a34a')+_tcCard("Tiền ra (kỳ)",vnd(cs.tien_ra_ky),null,'#dc2626')+
    _tcCard("Chi bình quân/tháng",vnd(cs.chi_binh_quan_thang)));
  // Cảnh báo
  const cbRows=cb.map(c=>{const t=TC_MUC[c.muc_do]||[c.muc_do,'b-cho'];
    return `<div style="display:flex;gap:10px;padding:10px 0;border-top:1px solid var(--line)">
      <span class="badge ${t[1]}" style="height:fit-content">${t[0]}</span>
      <div><div style="font-weight:600">${c.tieu_de}</div>
      <div style="color:var(--muted);font-size:13px;margin-top:2px">${c.chi_tiet}</div>
      <div style="font-size:13px;margin-top:3px">💡 ${c.goi_y}</div></div></div>`;}).join('');
  html+=`<div class="panel"><div class="panel-h"><h3>Cảnh báo tài chính</h3><div class="spacer"></div>
      <span class="badge ${cb.length?'b-tc':'b-ok'}">${cb.length?cb.length+' cảnh báo':'Không có cảnh báo'}</span></div>
    <div class="panel-b">${cbRows||'<div class="empty" style="padding:14px">Các chỉ số trong ngưỡng an toàn.</div>'}</div></div>`;
  // Khu vực cố vấn AI
  html+=`<div class="panel"><div class="panel-h"><h3>Cố vấn tài chính AI (CFO ảo)</h3></div>
    <div class="panel-b" id="tcAI"><div class="empty" style="padding:14px">Bấm <b>🤖 Phân tích bằng AI</b> để nhận đánh giá tổng thể và khuyến nghị hành động ưu tiên.</div></div></div>`;
  host.innerHTML=html;
}
function tcSetDays(d){S.tcDays=d;tcRender();}
async function tcRunAI(){
  const host=document.getElementById('tcAI'); if(host)host.innerHTML='<div class="empty" style="padding:14px">🤖 Đang phân tích…</div>';
  let tv;
  try{ tv = S.mode==="live" ? (await api(`/tai-chinh/tu-van-ai?so_ngay=${S.tcDays}`,{method:'POST'})).tu_van : _tcDemoAI(); }
  catch(e){ if(host)host.innerHTML=`<div class="empty" style="padding:14px;color:#dc2626">${e.detail||e.message}</div>`; return; }
  const SK={TOT:['Tốt','#16a34a'],KHA:['Khá','#16a34a'],TRUNG_BINH:['Trung bình','#f59e0b'],YEU:['Yếu','#dc2626']};
  const sk=SK[tv.suc_khoe]||[tv.suc_khoe,'#6b7280'];
  const nd=(tv.nhan_dinh||[]).map(x=>`<li style="margin:3px 0">${x}</li>`).join('');
  const ut=(tv.uu_tien||[]).map(u=>{const t=TC_MUC[u.muc_do]||[u.muc_do,'b-cho'];
    return `<div style="display:flex;gap:10px;padding:9px 0;border-top:1px solid var(--line)">
      <span class="badge ${t[1]}" style="height:fit-content">${t[0]}</span>
      <div><div style="font-weight:600">${u.tieu_de}</div><div style="font-size:13px;margin-top:2px">→ ${u.hanh_dong}</div></div></div>`;}).join('');
  host.innerHTML=`<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
      <span style="font-weight:700">Sức khỏe tài chính:</span><span class="badge" style="background:${sk[1]}22;color:${sk[1]}">${sk[0]}</span>
      <span style="color:var(--muted);font-size:12px;margin-left:auto">Nguồn: ${tv.nguon==="ANTHROPIC"?'AI (Claude)':'Quy tắc nội bộ'}</span></div>
    <div style="line-height:1.55">${tv.danh_gia||''}</div>
    ${nd?`<div style="font-weight:600;margin:10px 0 4px">Nhận định</div><ul style="margin:0;padding-left:18px">${nd}</ul>`:''}
    <div style="font-weight:600;margin:12px 0 2px">Khuyến nghị ưu tiên</div>${ut||'<div class="empty">—</div>'}`;
}
function _tcDemo(){
  return {ngay:new Date().toISOString().slice(0,10),diem_suc_khoe:62,
    chi_so:{ky_so_ngay:90,tien_mat_va_nh:350e6,phai_thu:280e6,phai_tra:210e6,ton_kho:120e6,thue_phai_nop:18e6,
      tai_san_ngan_han:750e6,no_ngan_han:228e6,ty_so_thanh_toan_hien_hanh:3.29,ty_so_thanh_toan_nhanh:2.76,ty_so_thanh_toan_tien_mat:1.54,
      doanh_thu:900e6,gia_von:560e6,chi_phi:240e6,loi_nhuan_gop:340e6,loi_nhuan_thuan:100e6,
      bien_loi_nhuan_gop:0.378,bien_loi_nhuan_thuan:0.111,ty_le_chi_phi:0.267,
      ky_thu_tien_bq:28,ky_tra_tien_bq:34,so_ngay_ton_kho:19,
      tien_vao_ky:820e6,tien_ra_ky:760e6,dong_tien_rong_ky:60e6,chi_binh_quan_thang:253e6,so_thang_tien_mat_con_lai:1.4,
      phai_thu_qua_han:45e6,phai_tra_qua_han:0},
    canh_bao:[
      {ma:"RUNWAY",muc_do:"CAO",tieu_de:"Tiền mặt mỏng so với nhịp chi",chi_tiet:"Tiền mặt chỉ đủ ~1,4 tháng theo nhịp chi hiện tại.",goi_y:"Lập kế hoạch dòng tiền 13 tuần, tăng thu đặt cọc, hoãn chi chưa cấp thiết."},
      {ma:"AR_QH",muc_do:"TRUNG",tieu_de:"Có công nợ phải thu quá hạn",chi_tiet:"Phải thu quá hạn 45.000.000đ.",goi_y:"Nhắc nợ theo tuổi nợ, ưu tiên khoản lớn/lâu nhất."}]};
}
function _tcDemoAI(){
  return {nguon:"DEMO",suc_khoe:"KHA",
    danh_gia:"Sức khỏe tài chính tổng thể: khá. Thanh khoản tốt (hiện hành 3,29), biên lợi nhuận gộp 37,8% và có lãi. Điểm cần lưu ý là đệm tiền mặt mỏng so với nhịp chi và có khoản phải thu quá hạn.",
    nhan_dinh:["Hệ số thanh toán hiện hành 3,29 — an toàn (>1,5).","Biên lợi nhuận gộp 37,8% — tốt.","Kỳ thu tiền 28 ngày — tốt.","Tiền mặt đủ ~1,4 tháng theo nhịp chi hiện tại."],
    uu_tien:[{tieu_de:"Tiền mặt mỏng so với nhịp chi",muc_do:"CAO",hanh_dong:"Lập kế hoạch dòng tiền 13 tuần, tăng thu đặt cọc, hoãn chi chưa cấp thiết."},
      {tieu_de:"Có công nợ phải thu quá hạn",muc_do:"TRUNG",hanh_dong:"Nhắc nợ theo tuổi nợ, ưu tiên khoản lớn/lâu nhất."}]};
}

/* ---- Tab Cân đối kế toán + ROA/ROE/đòn bẩy ---- */
async function tcCoCau(host){
  let ts,d;
  if(S.mode==="live"){ [ts,d]=await Promise.all([api("/tai-chinh/tham-so"),api(`/tai-chinh/can-doi-ke-toan?so_ngay=${S.tcDays}`)]); }
  else { ts={von_chu_so_huu:1000000000,tai_san_co_dinh:600000000,no_dai_han:200000000,chi_co_dinh_thang:80000000}; d=_tcDemoCoCau(ts); }
  const A=d.tai_san,N=d.nguon_von,X=d.chi_so;
  const canOp=can("tai_chinh","THAO_TAC")||S.mode!=="live";
  const fld=(id,lb,v)=>`<div class="f"><label>${lb}</label><input type="number" id="${id}" value="${v||0}"></div>`;
  let html=`<div class="panel"><div class="panel-h"><h3>Khai báo số liệu vốn & tài sản dài hạn</h3></div>
    <div class="panel-b"><div class="note" style="margin-bottom:8px">ERP tự tính tài sản ngắn hạn (tiền, phải thu, tồn kho) và nợ ngắn hạn. Anh chỉ cần khai báo các khoản dưới đây để hệ thống lập bảng cân đối và tính ROA/ROE/đòn bẩy.</div>
    <div class="formrow">${fld('ts_vcsh','Vốn chủ sở hữu',ts.von_chu_so_huu)}${fld('ts_tscd','Tài sản cố định (thuần)',ts.tai_san_co_dinh)}${fld('ts_nodh','Nợ dài hạn',ts.no_dai_han)}${fld('ts_chicd','Chi phí cố định / tháng',ts.chi_co_dinh_thang)}
      ${canOp?'<button class="btn-sm" style="align-self:end" onclick="tcLuuThamSo()">Lưu</button>':''}</div></div></div>`;
  if(d.khai_bao_thieu) html+=`<div class="note" style="color:#b45309;padding:8px 0">⚠️ Chưa khai báo VCSH/TSCĐ — ROA/ROE và đòn bẩy chưa phản ánh đúng. Vui lòng nhập số liệu phía trên.</div>`;
  // Bảng cân đối 2 cột
  const row=(l,v,b)=>`<tr><td style="${b?'font-weight:700':''}">${l}</td><td class="num" style="${b?'font-weight:700':''}">${vnd(v)}</td></tr>`;
  html+=`<div style="display:flex;flex-wrap:wrap;gap:12px">
    <div class="panel" style="flex:1;min-width:280px"><div class="panel-h"><h3>TÀI SẢN</h3></div><div class="panel-b"><table>
      ${row('Tiền & ngân hàng',A.tien)}${row('Phải thu',A.phai_thu)}${row('Tồn kho',A.ton_kho)}
      ${row('• Tài sản ngắn hạn',A.tai_san_ngan_han,1)}${row('Tài sản cố định',A.tai_san_co_dinh)}
      ${row('TỔNG TÀI SẢN',A.tong_tai_san,1)}</table></div></div>
    <div class="panel" style="flex:1;min-width:280px"><div class="panel-h"><h3>NGUỒN VỐN</h3></div><div class="panel-b"><table>
      ${row('Nợ ngắn hạn',N.no_ngan_han)}${row('Nợ dài hạn',N.no_dai_han)}${row('• Tổng nợ phải trả',N.tong_no,1)}
      ${row('Vốn chủ sở hữu',N.von_chu_so_huu)}${row('TỔNG NGUỒN VỐN',N.tong_nguon_von,1)}</table>
      ${Math.abs(N.chenh_lech)>=1?`<div class="note" style="margin-top:6px;color:var(--muted)">Chênh lệch ${vnd(N.chenh_lech)} = lợi nhuận giữ lại/khoản chưa khai báo (tài sản trừ nguồn vốn đã khai).</div>`:'<div class="note" style="margin-top:6px;color:#16a34a">✓ Cân đối khớp.</div>'}</div></div></div>`;
  // ROA/ROE/đòn bẩy
  html+=_tcGroup("Hiệu quả vốn & đòn bẩy",
    _tcCard("ROA",_pct(X.roa),"LN năm ước tính / tổng tài sản",_tcCol(X.roa,0.08,0))+
    _tcCard("ROE",_pct(X.roe),"LN năm ước tính / VCSH",_tcCol(X.roe,0.15,0))+
    _tcCard("Hệ số nợ",_pct(X.he_so_no),"tổng nợ / tổng tài sản (≤0,5 tốt)",X.he_so_no==null?'':(X.he_so_no<=0.5?'#16a34a':X.he_so_no<=0.7?'#f59e0b':'#dc2626'))+
    _tcCard("Nợ / VCSH",_num(X.no_tren_vcsh),"D/E (≤1 an toàn)",X.no_tren_vcsh==null?'':(X.no_tren_vcsh<=1?'#16a34a':X.no_tren_vcsh<=2?'#f59e0b':'#dc2626'))+
    _tcCard("Hệ số tự tài trợ",_pct(X.he_so_tu_tai_tro),"VCSH / tổng tài sản",_tcCol(X.he_so_tu_tai_tro,0.5,0.3))+
    _tcCard("LN năm (ước tính)",vnd(X.loi_nhuan_nam_uoc_tinh),"quy đổi từ kỳ "+d.so_ngay+" ngày",X.loi_nhuan_nam_uoc_tinh<0?'#dc2626':'#16a34a'));
  const cbRows=(d.canh_bao||[]).map(c=>{const t=TC_MUC[c.muc_do]||[c.muc_do,'b-cho'];
    return `<div style="display:flex;gap:10px;padding:9px 0;border-top:1px solid var(--line)"><span class="badge ${t[1]}" style="height:fit-content">${t[0]}</span><div><div style="font-weight:600">${c.tieu_de}</div><div style="color:var(--muted);font-size:13px">${c.chi_tiet}</div><div style="font-size:13px;margin-top:2px">💡 ${c.goi_y}</div></div></div>`;}).join('');
  if(cbRows) html+=`<div class="panel"><div class="panel-h"><h3>Cảnh báo cơ cấu vốn</h3></div><div class="panel-b">${cbRows}</div></div>`;
  host.innerHTML=html;
}
async function tcLuuThamSo(){
  const body={von_chu_so_huu:Number(gv('ts_vcsh')||0),tai_san_co_dinh:Number(gv('ts_tscd')||0),no_dai_han:Number(gv('ts_nodh')||0),chi_co_dinh_thang:Number(gv('ts_chicd')||0)};
  if(S.mode==="live"){ try{await api("/tai-chinh/tham-so",{method:'PUT',body:JSON.stringify(body)});toast("Đã lưu số liệu","ok");tcRender();}catch(e){toast(e.detail||e.message,"err");} return; }
  toast("Đã lưu (demo)","ok"); tcRender();
}

/* ---- Tab Dự báo dòng tiền 13 tuần ---- */
async function tcDuBao(host){
  const d = S.mode==="live" ? await api("/tai-chinh/du-bao-dong-tien?so_tuan=13") : _tcDemoDuBao();
  const w=d.weeks;
  // biểu đồ tồn cuối theo tuần (cột; âm tô đỏ)
  const vals=w.map(x=>x.ton_cuoi); const mx=Math.max(1,...vals.map(Math.abs));
  const H=130;
  const bars=w.map(x=>{const h=Math.max(2,Math.round(Math.abs(x.ton_cuoi)/mx*H/2)); const neg=x.ton_cuoi<0;
    return `<div style="flex:1;min-width:34px;text-align:center">
      <div style="height:${H}px;display:flex;flex-direction:column;justify-content:center;position:relative">
        <div style="position:absolute;left:0;right:0;top:50%;border-top:1px dashed var(--line)"></div>
        ${neg?'':`<div style="height:${h}px;background:#16a34a;border-radius:3px 3px 0 0;margin-top:auto" title="${vnd(x.ton_cuoi)}"></div>`}
        ${neg?`<div style="height:${h}px;background:#dc2626;border-radius:0 0 3px 3px;margin-bottom:auto" title="${vnd(x.ton_cuoi)}"></div>`:''}
      </div><div style="font-size:10px;color:var(--muted);margin-top:2px">T${x.tuan}</div></div>`;}).join('');
  let html=`<div style="display:flex;flex-wrap:wrap;gap:8px;padding:0 0 12px">
    ${_tcCard("Tồn quỹ đầu kỳ",vnd(d.opening))}
    ${_tcCard("Tồn thấp nhất (dự báo)",vnd(d.min_ton),null,d.min_ton<0?'#dc2626':'#16a34a')}
    ${_tcCard("Tuần thiếu hụt đầu tiên",d.tuan_thieu_dau?('Tuần '+d.tuan_thieu_dau):'Không',d.so_tuan_am?(d.so_tuan_am+' tuần âm'):'',d.tuan_thieu_dau?'#dc2626':'#16a34a')}
    ${_tcCard("Chi cố định / tuần",vnd(d.chi_co_dinh_tuan),"lương, thuê… trải đều")}</div>`;
  (d.canh_bao||[]).forEach(c=>{html+=`<div class="note" style="color:#b91c1c;padding:6px 0">⚠️ <b>${c.tieu_de}.</b> ${c.chi_tiet} 💡 ${c.goi_y}</div>`;});
  html+=`<div class="panel"><div class="panel-h"><h3>Số dư tiền dự báo theo tuần</h3><div class="spacer"></div>
      <span style="font-size:12px;color:var(--muted)"><span style="color:#16a34a">■</span> dương &nbsp; <span style="color:#dc2626">■</span> âm (thiếu hụt)</span></div>
    <div class="panel-b"><div style="display:flex;gap:6px;align-items:stretch;overflow-x:auto;padding:4px 2px">${bars}</div></div></div>`;
  const rows=w.map(x=>`<tr class="${x.thieu_hut?'qh':''}"><td><b>T${x.tuan}</b></td><td>${x.tu_ngay} → ${x.den_ngay}</td>
    <td class="num" style="color:#16a34a">${x.thu?vnd(x.thu):''}</td><td class="num" style="color:#dc2626">${x.chi?vnd(x.chi):''}</td>
    <td class="num">${vnd(x.rong)}</td><td class="num"><b style="color:${x.ton_cuoi<0?'#dc2626':'#16a34a'}">${vnd(x.ton_cuoi)}</b></td>
    <td>${x.thieu_hut?'<span class="badge b-tc">Thiếu hụt</span>':''}</td></tr>`).join('');
  html+=`<div class="panel"><div class="panel-h"><h3>Chi tiết 13 tuần</h3></div><div class="panel-b"><table>
    <thead><tr><th>Tuần</th><th>Khoảng</th><th class="num">Thu (PThu đến hạn)</th><th class="num">Chi (PTra + cố định)</th><th class="num">Ròng</th><th class="num">Tồn cuối</th><th></th></tr></thead>
    <tbody>${rows}</tbody></table>
    <div class="note" style="margin-top:8px;color:var(--muted)">Thu/chi xếp theo <b>hạn công nợ</b>; khoản quá hạn dồn vào tuần 1. Phải thu chưa có hạn: ${vnd(d.ar_khong_han)} · phải trả chưa có hạn: ${vnd(d.ap_khong_han)} (chưa đưa vào dự báo). Chi cố định lấy từ khai báo ở tab "Cân đối".</div></div></div>`;
  host.innerHTML=html;
}
function _tcDemoCoCau(ts){
  const tien=350e6,pthu=280e6,ton=120e6,tsnh=tien+pthu+ton,nonh=228e6;
  const tong_ts=tsnh+ts.tai_san_co_dinh, tong_no=nonh+ts.no_dai_han, tong_nv=tong_no+ts.von_chu_so_huu;
  const ln_nam=100e6*365/90;
  return {so_ngay:90,tai_san:{tien,phai_thu:pthu,ton_kho:ton,tai_san_ngan_han:tsnh,tai_san_co_dinh:ts.tai_san_co_dinh,tong_tai_san:tong_ts},
    nguon_von:{no_ngan_han:nonh,no_dai_han:ts.no_dai_han,tong_no,von_chu_so_huu:ts.von_chu_so_huu,tong_nguon_von:tong_nv,chenh_lech:tong_ts-tong_nv},
    chi_so:{roa:ln_nam/tong_ts,roe:ln_nam/ts.von_chu_so_huu,he_so_no:tong_no/tong_ts,no_tren_vcsh:tong_no/ts.von_chu_so_huu,he_so_tu_tai_tro:ts.von_chu_so_huu/tong_ts,loi_nhuan_nam_uoc_tinh:Math.round(ln_nam)},
    canh_bao:[],khai_bao_thieu:false};
}
function _tcDemoDuBao(){
  const today=new Date(); const wk=[]; let ton=350e6;
  const thu=[120e6,0,80e6,0,150e6,0,60e6,0,90e6,0,40e6,0,70e6], chi=[180e6,18e6,60e6,18e6,40e6,18e6,200e6,18e6,55e6,18e6,33e6,18e6,48e6];
  for(let i=0;i<13;i++){const tu=new Date(today.getTime()+i*7*864e5),den=new Date(tu.getTime()+6*864e5);
    const rong=thu[i]-chi[i]; ton+=rong;
    wk.push({tuan:i+1,tu_ngay:tu.toISOString().slice(0,10),den_ngay:den.toISOString().slice(0,10),thu:thu[i],chi:chi[i],rong,ton_cuoi:ton,thieu_hut:ton<0});}
  const min_ton=Math.min(...wk.map(x=>x.ton_cuoi)); const first=wk.find(x=>x.thieu_hut);
  return {opening:350e6,so_tuan:13,weeks:wk,min_ton,tuan_thieu_dau:first?first.tuan:null,so_tuan_am:wk.filter(x=>x.thieu_hut).length,chi_co_dinh_tuan:18666667,ar_khong_han:60e6,ap_khong_han:0,canh_bao:first?[{muc_do:"CAO",tieu_de:`Thiếu hụt tiền mặt từ tuần ${first.tuan}`,chi_tiet:`Tồn thấp nhất ${min_ton.toLocaleString('vi-VN')}đ.`,goi_y:"Đẩy thu công nợ, giãn lịch trả NCC."}]:[]};
}

/* ---------- NHÂN SỰ & LƯƠNG ---------- */
const NS_TT={NHAP:['Đang nhập','b-cho'],DA_CHOT:['Đã chốt','b-ok'],CHUA_TAO:['Chưa tạo','b-tc']};
function _nsThangMacDinh(){const d=new Date();return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0');}
async function viewNhanSu(m){
  if(!S.nsTab)S.nsTab="bangluong"; if(!S.nsThang)S.nsThang=_nsThangMacDinh();
  const tabs=[["bangluong","Bảng lương theo kỳ"],["hoso","Hồ sơ lương"],["motacv","Mô tả CV & KPI"]];
  m.innerHTML=head("Nhân sự & Lương","Quy trình lương tự động: chấm công · tăng ca · bảo hiểm · thuế TNCN · chi phí lương · email phiếu lương")
    +`<div class="tabs">${tabs.map(([k,l])=>`<button class="${S.nsTab===k?'active':''}" onclick="nsTab('${k}')">${l}</button>`).join('')}</div><div id="nsBody"></div>`;
  nsRender();
}
function nsTab(k){S.nsTab=k;nsRender();}
async function nsRender(){
  const h=document.getElementById('nsBody'); if(!h)return; h.innerHTML='<div class="empty" style="padding:20px">Đang tải…</div>';
  try{ if(S.nsTab==="hoso")await nsHoSo(h); else if(S.nsTab==="motacv")await nsMotaCV(h); else await nsBangLuong(h); }
  catch(e){ h.innerHTML=`<div class="empty" style="padding:24px;color:#dc2626">${e.detail||e.message}</div>`; }
}


/* ===== Mô tả CV & KPI ===== */
const CAP_BADGE={"Điều hành":"b-tc","Quản lý":"b-info","Chuyên viên":"b-cho","Nhân viên":"b-ok"};
const LOAIKY_TEN={TUAN:"Tuần",THANG:"Tháng",QUY:"Quý",NAM:"Năm"};
function _xepBadge(x){return {A:"b-ok",B:"b-info",C:"b-cho",D:"b-tc"}[x]||"b-info";}
function _isoWeek(d){const t=new Date(Date.UTC(d.getFullYear(),d.getMonth(),d.getDate()));const day=t.getUTCDay()||7;t.setUTCDate(t.getUTCDate()+4-day);const ys=new Date(Date.UTC(t.getUTCFullYear(),0,1));return Math.ceil((((t-ys)/86400000)+1)/7);}
function _kyHienTai(loai){const d=new Date(),y=d.getFullYear();
  if(loai==="NAM")return String(y);
  if(loai==="QUY")return `${y}-Q${Math.floor(d.getMonth()/3)+1}`;
  if(loai==="TUAN")return `${y}-W${String(_isoWeek(d)).padStart(2,'0')}`;
  return `${y}-${String(d.getMonth()+1).padStart(2,'0')}`;}
function _kpiTinh(chieu,mt,thuc,ts){
  if(thuc===null||thuc===''||isNaN(Number(thuc)))return {pct:null,diem:0};
  thuc=Number(thuc);let pct;
  if(mt===null||mt===undefined)pct=100;
  else{mt=Number(mt);
    if(chieu==="THAP")pct=mt===0?(thuc<=0?100:Math.max(0,100-thuc*25)):(thuc<=mt?100:mt/thuc*100);
    else pct=mt===0?100:thuc/mt*100;}
  return {pct:Math.round(Math.min(pct,200)*100)/100,diem:Math.round(Number(ts||0)*Math.min(pct,100)/100*100)/100};
}

const DEMO_JD={
 NV_DA:{vai_tro:"NV_DA",ten_vai_tro:"NV Dự án (giám sát thực địa)",chuc_danh:"Nhân viên Dự án (giám sát thực địa)",cap_bac:"Nhân viên",bao_cao_cho:"TP_DA",
  muc_dich:"Triển khai, giám sát thi công và vận hành thử hệ thống tại hiện trường theo thiết kế và tiêu chuẩn.",
  trach_nhiem:["Giám sát thi công, lắp đặt thiết bị theo bản vẽ và tiến độ.","Theo dõi chỉ tiêu vận hành, lấy mẫu và ghi nhật ký công trường.","Cập nhật khối lượng, mốc và rủi ro lên hệ thống dự án.","Thực hiện quy định an toàn lao động tại hiện trường."],
  quyen_han:["Ghi nhận nhật ký, khối lượng (chờ duyệt).","Đề xuất xử lý phát sinh kỹ thuật."],
  yeu_cau:{hoc_van:"Cao đẳng/Đại học Kỹ thuật.",kinh_nghiem:"≥ 1 năm thi công/vận hành hệ thống nước.",ky_nang:["Đọc bản vẽ P&ID","Giám sát thi công","Lấy mẫu & đo đạc","An toàn lao động"]},
  kpis:[{id:1,ten:"Tiến độ hạng mục được giao",don_vi:"%",trong_so:35,muc_tieu:95,chieu:"CAO",chu_ky:"TUAN"},{id:2,ten:"Chỉ tiêu vận hành đạt yêu cầu",don_vi:"%",trong_so:30,muc_tieu:100,chieu:"CAO",chu_ky:"THANG"},{id:3,ten:"Đầy đủ nhật ký & hồ sơ hiện trường",don_vi:"%",trong_so:20,muc_tieu:100,chieu:"CAO",chu_ky:"TUAN"},{id:4,ten:"Vi phạm an toàn lao động",don_vi:"lần",trong_so:15,muc_tieu:0,chieu:"THAP",chu_ky:"THANG"}]},
 NV_KD:{vai_tro:"NV_KD",ten_vai_tro:"Nhân viên Kinh doanh",chuc_danh:"Nhân viên Kinh doanh",cap_bac:"Nhân viên",bao_cao_cho:"TP_KD",
  muc_dich:"Tìm kiếm, tư vấn và chốt hợp đồng giải pháp xử lý nước; chăm sóc danh mục khách hàng được giao.",
  trach_nhiem:["Khai thác khách hàng tiềm năng, khảo sát nhu cầu và lập báo giá.","Tư vấn giải pháp kỹ thuật phối hợp bộ phận Dự án.","Theo dõi cơ hội trên phễu, đẩy nhanh chốt đơn.","Theo dõi thanh toán và công nợ khách phụ trách."],
  quyen_han:["Lập báo giá, đơn hàng (chờ duyệt).","Đề xuất chiết khấu trong khung."],
  yeu_cau:{hoc_van:"Cao đẳng/Đại học.",kinh_nghiem:"≥ 1 năm bán hàng kỹ thuật.",ky_nang:["Tư vấn giải pháp","Giao tiếp","Lập báo giá","Chăm sóc khách hàng"]},
  kpis:[{id:11,ten:"Doanh số cá nhân / chỉ tiêu",don_vi:"%",trong_so:45,muc_tieu:100,chieu:"CAO",chu_ky:"THANG"},{id:12,ten:"Số báo giá gửi đi",don_vi:"báo giá",trong_so:20,muc_tieu:12,chieu:"CAO",chu_ky:"THANG"},{id:13,ten:"Số cơ hội mới vào phễu",don_vi:"cơ hội",trong_so:20,muc_tieu:10,chieu:"CAO",chu_ky:"THANG"},{id:14,ten:"Công nợ quá hạn KH phụ trách",don_vi:"triệu",trong_so:15,muc_tieu:0,chieu:"THAP",chu_ky:"THANG"}]},
 KTT:{vai_tro:"KTT",ten_vai_tro:"Kế toán trưởng",chuc_danh:"Kế toán trưởng",cap_bac:"Quản lý",bao_cao_cho:"CEO",
  muc_dich:"Tổ chức công tác kế toán – tài chính, bảo đảm tuân thủ pháp luật, kiểm soát chi phí và cung cấp thông tin quản trị.",
  trach_nhiem:["Tổ chức hạch toán, lập BCTC và quyết toán thuế đúng hạn.","Kiểm soát dòng tiền, công nợ và ngân sách.","Duyệt & hạch toán bảng lương.","Tham mưu Giám đốc về tài chính, thuế, rủi ro."],
  quyen_han:["Duyệt bút toán, phiếu thu/chi trong hạn mức.","Duyệt bảng lương (bước KTT)."],
  yeu_cau:{hoc_van:"Đại học Kế toán – Tài chính; chứng chỉ KTT.",kinh_nghiem:"≥ 5 năm, ≥ 2 năm KTT.",ky_nang:["Kế toán tổng hợp","Thuế","Phân tích tài chính","Kiểm soát nội bộ"]},
  kpis:[{id:21,ten:"Báo cáo tài chính/thuế đúng hạn",don_vi:"%",trong_so:35,muc_tieu:100,chieu:"CAO",chu_ky:"QUY"},{id:22,ten:"Sai sót bị cơ quan thuế điều chỉnh",don_vi:"lần",trong_so:25,muc_tieu:0,chieu:"THAP",chu_ky:"NAM"},{id:23,ten:"Số ngày phải thu bình quân (DSO)",don_vi:"ngày",trong_so:20,muc_tieu:45,chieu:"THAP",chu_ky:"QUY"},{id:24,ten:"Chênh lệch ngân sách chi phí",don_vi:"%",trong_so:20,muc_tieu:5,chieu:"THAP",chu_ky:"QUY"}]},
};
function _demoJDList(){return Object.values(DEMO_JD).map(j=>({vai_tro:j.vai_tro,chuc_danh:j.chuc_danh,cap_bac:j.cap_bac,bao_cao_cho:j.bao_cao_cho,ten_vai_tro:j.ten_vai_tro,so_kpi:j.kpis.length}));}

async function nsMotaCV(host){
  if(!S.nsKpiTab)S.nsKpiTab="jd";
  const subs=[["jd","Mô tả công việc (JD)"],["danhgia","Đánh giá KPI"],["tongket","Tổng kết kết quả"]];
  host.innerHTML=`<div class="tabs" style="margin-bottom:14px">${subs.map(([k,l])=>`<button class="${S.nsKpiTab===k?'active':''}" onclick="nsKpiSub('${k}')">${l}</button>`).join('')}</div>
    ${S.mode!=="live"?`<div class="panel" style="margin-bottom:12px"><div class="panel-b" style="color:var(--muted);font-size:12.5px">Chế độ demo hiển thị 3 vị trí mẫu. Kết nối hệ thống (live) để xem & chỉnh đầy đủ 14 vị trí và lưu đánh giá.</div></div>`:''}
    <div id="kpiBody">Đang tải…</div>`;
  const h=$("#kpiBody");
  if(S.nsKpiTab==="jd")await nsJD(h);
  else if(S.nsKpiTab==="danhgia")await nsDanhGia(h);
  else await nsTongKet(h);
}
function nsKpiSub(k){S.nsKpiTab=k;S.nsJDSel=null;nsRender();}

/* --- JD --- */
async function nsJD(host){
  if(S.nsJDSel)return nsJDDetail(host,S.nsJDSel);
  let list;
  if(S.mode==="live"){ try{list=await api("/nhan-su/mo-ta-cv");}catch(e){host.innerHTML=`<div class="perm-denied">${e.detail||e.message}</div>`;return;} }
  else list=_demoJDList();
  const rows=list.map(j=>`<tr><td><b>${j.vai_tro}</b></td><td>${j.chuc_danh}</td>
    <td><span class="badge ${CAP_BADGE[j.cap_bac]||'b-info'}">${j.cap_bac||'—'}</span></td>
    <td>${ROLE_NAME[j.bao_cao_cho]||j.bao_cao_cho||'—'}</td>
    <td class="num">${j.so_kpi}</td>
    <td><button class="btn-sm ghost" onclick="nsOpenJD('${j.vai_tro}')">Xem mô tả</button></td></tr>`).join('');
  host.innerHTML=`<div class="panel"><div class="panel-h"><h3>Bảng mô tả công việc theo vị trí</h3></div>
    <div class="panel-b"><table><thead><tr><th>Mã VT</th><th>Chức danh</th><th>Cấp bậc</th><th>Báo cáo cho</th><th class="num">Số KPI</th><th></th></tr></thead>
      <tbody>${rows}</tbody></table></div></div>`;
}
function nsOpenJD(vt){S.nsJDSel=vt;nsRender();}
function nsBackJD(){S.nsJDSel=null;nsRender();}
async function nsJDDetail(host,vt){
  let j;
  if(S.mode==="live"){ try{j=await api(`/nhan-su/mo-ta-cv/${vt}`);}catch(e){host.innerHTML=`<div class="perm-denied">${e.detail||e.message}</div>`;return;} }
  else j=DEMO_JD[vt];
  if(!j){host.innerHTML='<div class="perm-denied">Không có mô tả</div>';return;}
  const canEdit=can("nhan_su","DUYET");
  const yc=j.yeu_cau||{};
  const li=arr=>(arr||[]).map(x=>`<li style="margin-bottom:5px;line-height:1.5">${x}</li>`).join('')||'<li style="color:var(--muted)">—</li>';
  const kpiRows=(j.kpis||[]).map(k=>`<tr><td>${k.ten}</td><td>${k.don_vi||'—'}</td>
    <td class="num">${k.trong_so}%</td><td class="num">${k.muc_tieu!=null?k.muc_tieu:'—'}</td>
    <td>${k.chieu==='CAO'?'Càng cao càng tốt':'Càng thấp càng tốt'}</td><td>${LOAIKY_TEN[k.chu_ky]||k.chu_ky}</td></tr>`).join('');
  const tongTS=(j.kpis||[]).reduce((s,k)=>s+Number(k.trong_so||0),0);
  host.innerHTML=`<button class="btn-sm ghost" onclick="nsBackJD()">← Danh sách vị trí</button>
    <div class="panel" style="margin-top:14px"><div class="panel-h">
      <h3>${j.chuc_danh}</h3><div class="spacer"></div>
      <span class="badge ${CAP_BADGE[j.cap_bac]||'b-info'}">${j.cap_bac||''}</span>
      ${canEdit?`<button class="btn-sm ghost" style="margin-left:8px" onclick="nsEditJD('${vt}')">✎ Chỉnh sửa</button>`:''}</div>
      <div class="panel-b">
        <div style="display:flex;gap:24px;flex-wrap:wrap;font-size:13px;color:var(--muted);margin-bottom:14px">
          <div>Mã vị trí: <b style="color:var(--ink)">${j.vai_tro}</b></div>
          <div>Báo cáo cho: <b style="color:var(--ink)">${ROLE_NAME[j.bao_cao_cho]||j.bao_cao_cho||'—'}</b></div>
        </div>
        <h4 style="margin:0 0 6px">Mục đích công việc</h4>
        <p style="margin:0 0 16px;line-height:1.6">${j.muc_dich||'—'}</p>
        <h4 style="margin:0 0 6px">Trách nhiệm chính</h4>
        <ul style="margin:0 0 16px;padding-left:20px">${li(j.trach_nhiem)}</ul>
        <h4 style="margin:0 0 6px">Quyền hạn</h4>
        <ul style="margin:0 0 16px;padding-left:20px">${li(j.quyen_han)}</ul>
        <h4 style="margin:0 0 6px">Yêu cầu năng lực</h4>
        <div style="line-height:1.7;margin-bottom:4px"><b>Học vấn:</b> ${yc.hoc_van||'—'}<br><b>Kinh nghiệm:</b> ${yc.kinh_nghiem||'—'}<br>
          <b>Kỹ năng:</b> ${(yc.ky_nang||[]).map(s=>`<span class="badge b-info" style="margin:2px">${s}</span>`).join('')||'—'}</div>
      </div></div>
    <div class="panel"><div class="panel-h"><h3>Bộ chỉ tiêu KPI</h3><div class="spacer"></div>
      <span class="badge ${tongTS===100?'b-ok':'b-tc'}">Tổng trọng số ${tongTS}%</span></div>
      <div class="panel-b"><table><thead><tr><th>Chỉ tiêu</th><th>Đơn vị</th><th class="num">Trọng số</th><th class="num">Mục tiêu</th><th>Chiều hướng</th><th>Chu kỳ</th></tr></thead>
        <tbody>${kpiRows||'<tr><td colspan="6" style="color:var(--muted)">Chưa có KPI</td></tr>'}</tbody></table></div></div>`;
}
async function nsEditJD(vt){
  let j;
  if(S.mode==="live"){ try{j=await api(`/nhan-su/mo-ta-cv/${vt}`);}catch(e){toast(e.detail||e.message,"err");return;} } else j=DEMO_JD[vt];
  const host=$("#kpiBody");
  host.innerHTML=`<button class="btn-sm ghost" onclick="nsBackJD()">← Hủy</button>
    <div class="panel" style="margin-top:14px"><div class="panel-h"><h3>Chỉnh sửa mô tả — ${j.chuc_danh}</h3></div>
    <div class="panel-b">
      <div class="formrow"><div class="f" style="flex:1"><label>Mục đích công việc</label><textarea id="jd_md" rows="2" style="width:100%">${j.muc_dich||''}</textarea></div></div>
      <div class="formrow" style="padding-top:0"><div class="f" style="flex:1"><label>Trách nhiệm chính (mỗi dòng một mục)</label><textarea id="jd_tn" rows="6" style="width:100%">${(j.trach_nhiem||[]).join('\n')}</textarea></div></div>
      <div class="formrow" style="padding-top:0"><div class="f" style="flex:1"><label>Quyền hạn (mỗi dòng một mục)</label><textarea id="jd_qh" rows="3" style="width:100%">${(j.quyen_han||[]).join('\n')}</textarea></div></div>
      <button class="btn-sm" onclick="nsSaveJD('${vt}')">Lưu mô tả</button>
    </div></div>`;
}
async function nsSaveJD(vt){
  const body={muc_dich:gv("jd_md"),
    trach_nhiem:($("#jd_tn").value||'').split('\n').map(s=>s.trim()).filter(Boolean),
    quyen_han:($("#jd_qh").value||'').split('\n').map(s=>s.trim()).filter(Boolean)};
  if(S.mode!=="live"){Object.assign(DEMO_JD[vt],body);toast("Đã lưu (demo)","ok");S.nsJDSel=vt;nsRender();return;}
  try{await api(`/nhan-su/mo-ta-cv/${vt}`,{method:'PUT',body:JSON.stringify(body)});
    toast("Đã lưu mô tả công việc","ok");S.nsJDSel=vt;nsRender();
  }catch(e){toast(e.detail||e.message,"err");}
}

/* --- Đánh giá KPI --- */
async function nsDanhGia(host){
  const canDo=can("nhan_su","THAO_TAC");
  let jdList,nvList;
  if(S.mode==="live"){ try{jdList=await api("/nhan-su/mo-ta-cv");nvList=await api("/nhan-su/ho-so");}catch(e){host.innerHTML=`<div class="perm-denied">${e.detail||e.message}</div>`;return;} }
  else { jdList=_demoJDList(); nvList=(typeof _nsDemoHoSo==="function"?_nsDemoHoSo():[{id:1,ho_ten:"Nhân viên demo",chuc_danh:""}]); }
  if(!S.nsDgVT)S.nsDgVT=jdList[0]?jdList[0].vai_tro:"";
  if(!S.nsDgLoai)S.nsDgLoai="THANG";
  // KPI của vị trí đang chọn
  let kpis=[];
  if(S.nsDgVT){ if(S.mode==="live"){ try{kpis=(await api(`/nhan-su/mo-ta-cv/${S.nsDgVT}`)).kpis;}catch{} } else kpis=(DEMO_JD[S.nsDgVT]||{}).kpis||[]; }
  const vtOpts=jdList.map(j=>`<option value="${j.vai_tro}" ${j.vai_tro===S.nsDgVT?'selected':''}>${j.chuc_danh}</option>`).join('');
  const nvOpts=nvList.map(n=>`<option value="${n.id}">${n.ho_ten}${n.chuc_danh?' — '+n.chuc_danh:''}</option>`).join('');
  const lkOpts=Object.entries(LOAIKY_TEN).map(([k,v])=>`<option value="${k}" ${k===S.nsDgLoai?'selected':''}>${v}</option>`).join('');
  const kpiRows=kpis.map(k=>`<tr><td>${k.ten} <span style="color:var(--muted)">(${k.don_vi||'-'})</span></td>
    <td class="num">${k.trong_so}%</td><td class="num">${k.muc_tieu!=null?k.muc_tieu:'—'} ${k.chieu==='THAP'?'↓':'↑'}</td>
    <td><input type="number" step="any" id="dg_${k.id}" data-ts="${k.trong_so}" data-mt="${k.muc_tieu!=null?k.muc_tieu:''}" data-ch="${k.chieu}" style="width:90px;padding:5px 7px;border:1px solid var(--line);border-radius:6px" oninput="nsDgPreview()"></td>
    <td class="num" id="pre_${k.id}" style="color:var(--muted)">—</td></tr>`).join('');
  host.innerHTML=`
    ${canDo?'':`<div class="perm-denied">Vai trò ${S.role} chỉ được xem — không thể chấm KPI.</div>`}
    <div class="panel"><div class="panel-h"><h3>Chấm điểm KPI theo kỳ</h3></div><div class="panel-b">
      <div class="formrow">
        <div class="f" style="flex:2"><label>Vị trí (bộ KPI)</label><select id="dg_vt" onchange="S.nsDgVT=this.value;nsRender()">${vtOpts}</select></div>
        <div class="f" style="flex:2"><label>Nhân viên</label><select id="dg_nv">${nvOpts}</select></div>
        <div class="f"><label>Loại kỳ</label><select id="dg_loai" onchange="nsDgKy()">${lkOpts}</select></div>
        <div class="f"><label>Kỳ</label><input id="dg_ky" value="${_kyHienTai(S.nsDgLoai)}"></div>
      </div>
      <table><thead><tr><th>Chỉ tiêu</th><th class="num">Trọng số</th><th class="num">Mục tiêu</th><th>Giá trị thực</th><th class="num">Điểm</th></tr></thead>
        <tbody>${kpiRows||'<tr><td colspan="5" style="color:var(--muted)">Vị trí chưa có KPI</td></tr>'}</tbody>
        <tfoot><tr><td colspan="4" style="text-align:right"><b>Tổng điểm dự kiến</b></td><td class="num"><b id="dg_tong">0</b> <span id="dg_xl"></span></td></tr></tfoot></table>
      <div class="formrow" style="padding-top:6px"><div class="f" style="flex:1"><label>Nhận xét</label><input id="dg_nx" placeholder="Nhận xét tổng quan…"></div></div>
      ${canDo&&kpis.length?`<button class="btn-sm" onclick="nsLuuDanhGia()">Chấm điểm &amp; lưu</button>`:''}
    </div></div>
    <div class="panel"><div class="panel-h"><h3>Đánh giá gần đây (${LOAIKY_TEN[S.nsDgLoai]})</h3></div>
      <div class="panel-b" id="dgRecent">Đang tải…</div></div>`;
  nsDgRecent(); nsDgPreview();
}
function nsDgKy(){S.nsDgLoai=gv("dg_loai");const e=$("#dg_ky");if(e)e.value=_kyHienTai(S.nsDgLoai);nsDgRecent();}
function nsDgPreview(){
  let tong=0;
  document.querySelectorAll('[id^="dg_"]').forEach(el=>{ if(!/^dg_\d+$/.test(el.id))return;
    const mt=el.dataset.mt===''?null:Number(el.dataset.mt);
    const r=_kpiTinh(el.dataset.ch,mt,el.value,el.dataset.ts);
    const pre=document.getElementById('pre_'+el.id.slice(3));
    if(pre)pre.textContent=el.value===''?'—':(r.diem+' đ'+(r.pct!=null?` (${r.pct}%)`:''));
    tong+=r.diem;});
  tong=Math.round(tong*100)/100;
  const t=document.getElementById('dg_tong');if(t)t.textContent=tong;
  const xl=tong>=85?'A':tong>=70?'B':tong>=50?'C':'D';
  const x=document.getElementById('dg_xl');if(x)x.innerHTML=`<span class="badge ${_xepBadge(xl)}">Loại ${xl}</span>`;
}
async function nsDgRecent(){
  const host=$("#dgRecent");if(!host)return;
  let list=[];
  if(S.mode==="live"){ try{list=await api(`/nhan-su/danh-gia?loai_ky=${S.nsDgLoai}`);}catch(e){host.innerHTML=`<span style="color:var(--red)">${e.detail||e.message}</span>`;return;} }
  else list=(S.demoDanhGia||[]).filter(d=>d.loai_ky===S.nsDgLoai);
  const rows=list.map(d=>`<tr><td>${d.ho_ten}</td><td>${ROLE_NAME[d.vai_tro]||d.ten_vai_tro||d.vai_tro||'—'}</td>
    <td>${d.ky}</td><td class="num">${d.tong_diem}</td><td><span class="badge ${_xepBadge(d.xep_loai)}">Loại ${d.xep_loai}</span></td></tr>`).join('')
    ||`<tr><td colspan="5" style="color:var(--muted)">Chưa có đánh giá</td></tr>`;
  host.innerHTML=`<table><thead><tr><th>Nhân viên</th><th>Vị trí</th><th>Kỳ</th><th class="num">Điểm</th><th>Xếp loại</th></tr></thead><tbody>${rows}</tbody></table>`;
}
async function nsLuuDanhGia(){
  const nvid=Number(gv("dg_nv")),loai=gv("dg_loai"),ky=gv("dg_ky");
  if(!nvid){toast("Chọn nhân viên","err");return;}
  if(!ky){toast("Nhập kỳ (VD 2026-06)","err");return;}
  const ct=[];
  document.querySelectorAll('[id^="dg_"]').forEach(el=>{ if(!/^dg_\d+$/.test(el.id))return;
    ct.push({kpi_id:Number(el.id.slice(3)),gia_tri_thuc:el.value===''?null:Number(el.value)});});
  if(!ct.length){toast("Vị trí chưa có KPI","err");return;}
  if(S.mode!=="live"){
    let tong=0;document.querySelectorAll('[id^="dg_"]').forEach(el=>{if(!/^dg_\d+$/.test(el.id))return;const mt=el.dataset.mt===''?null:Number(el.dataset.mt);tong+=_kpiTinh(el.dataset.ch,mt,el.value,el.dataset.ts).diem;});
    tong=Math.round(tong*100)/100;const xl=tong>=85?'A':tong>=70?'B':tong>=50?'C':'D';
    const nv=(_nsDemoHoSo?_nsDemoHoSo():[]).find(n=>n.id===nvid)||{ho_ten:"NV "+nvid};
    (S.demoDanhGia=S.demoDanhGia||[]).unshift({ho_ten:nv.ho_ten,vai_tro:S.nsDgVT,loai_ky:loai,ky,tong_diem:tong,xep_loai:xl});
    toast(`Đã chấm: ${tong} điểm — loại ${xl} (demo)`,"ok");nsRender();return;
  }
  try{const r=await api("/nhan-su/danh-gia",{method:'POST',body:JSON.stringify({nhan_vien_id:nvid,loai_ky:loai,ky,nhan_xet:gv("dg_nx")||null,chi_tiet:ct})});
    toast(`Đã chấm: ${r.tong_diem} điểm — loại ${r.xep_loai}`,"ok");nsRender();
  }catch(e){toast(e.detail||e.message,"err");}
}

/* --- Tổng kết --- */
async function nsTongKet(host){
  if(!S.nsTKLoai)S.nsTKLoai="THANG";
  const canCfg=can("nhan_su","DUYET");
  let tk,list,xh,cfg=null;
  if(S.mode==="live"){
    try{
      tk=await api(`/nhan-su/danh-gia-tong-ket?loai_ky=${S.nsTKLoai}`);
      list=await api(`/nhan-su/danh-gia?loai_ky=${S.nsTKLoai}`);
      xh=await api(`/nhan-su/danh-gia-xu-huong?loai_ky=${S.nsTKLoai}${S.nsXhNV?`&nhan_vien_id=${S.nsXhNV}`:''}`);
      if(canCfg)cfg=await api("/nhan-su/cau-hinh-thuong-kpi");
    }catch(e){host.innerHTML=`<div class="perm-denied">${e.detail||e.message}</div>`;return;}
  } else {
    list=(S.demoDanhGia||[]).filter(d=>d.loai_ky===S.nsTKLoai);
    const pb={A:0,B:0,C:0,D:0};let t=0;list.forEach(d=>{pb[d.xep_loai]=(pb[d.xep_loai]||0)+1;t+=d.tong_diem;});
    tk={so_danh_gia:list.length,diem_trung_binh:list.length?Math.round(t/list.length*100)/100:null,phan_bo:pb};
    const byk={};list.forEach(d=>{(byk[d.ky]=byk[d.ky]||[]).push(d.tong_diem);});
    const tq=Object.keys(byk).sort().map(k=>({ky:k,diem_tb:Math.round(byk[k].reduce((a,b)=>a+b,0)/byk[k].length*100)/100,so:byk[k].length}));
    let tn=null; if(S.nsXhNV){tn=list.filter(d=>String(d.nhan_vien_id)===String(S.nsXhNV)).sort((a,b)=>a.ky<b.ky?-1:1).map(d=>({ky:d.ky,diem:d.tong_diem,xep_loai:d.xep_loai}));}
    xh={tong_quan:tq,theo_nhan_vien:tn};
    cfg=S.cfgThuong||{muc_co_so:2000000,hs:{A:1.5,B:1.0,C:0.5,D:0}};
  }
  const lkOpts=Object.entries(LOAIKY_TEN).map(([k,v])=>`<option value="${k}" ${k===S.nsTKLoai?'selected':''}>${v}</option>`).join('');
  const pb=tk.phan_bo||{A:0,B:0,C:0,D:0};
  const nvMap={}; list.forEach(d=>{nvMap[d.nhan_vien_id]=d.ho_ten;});
  const nvOpts=`<option value="">— Trung bình toàn bộ —</option>`+Object.entries(nvMap).map(([id,ten])=>`<option value="${id}" ${String(id)===String(S.nsXhNV)?'selected':''}>${ten}</option>`).join('');
  const useNV=S.nsXhNV&&xh.theo_nhan_vien&&xh.theo_nhan_vien.length;
  const pts=(useNV?xh.theo_nhan_vien.map(p=>p.diem):(xh.tong_quan||[]).map(p=>p.diem_tb));
  const labs=(useNV?xh.theo_nhan_vien.map(p=>p.ky):(xh.tong_quan||[]).map(p=>p.ky));
  const rows=list.map(d=>`<tr><td>${d.ho_ten}</td><td>${ROLE_NAME[d.vai_tro]||d.ten_vai_tro||d.vai_tro||'—'}</td>
    <td>${d.ky}</td><td class="num">${d.tong_diem}</td><td><span class="badge ${_xepBadge(d.xep_loai)}">Loại ${d.xep_loai}</span></td></tr>`).join('')
    ||`<tr><td colspan="5" style="color:var(--muted)">Chưa có đánh giá cho kỳ này</td></tr>`;
  host.innerHTML=`
    <div class="formrow">
      <div class="f" style="max-width:200px"><label>Tổng kết theo</label><select onchange="S.nsTKLoai=this.value;S.nsXhNV='';nsRender()">${lkOpts}</select></div>
      <div style="flex:1"></div>
      <div class="f" style="align-self:flex-end"><button class="btn-sm ghost" onclick="nsXuatExcel()">⬇ Xuất Excel (.xlsx)</button></div>
    </div>
    <div class="cards">
      <div class="stat accent"><div class="k">Số lượt đánh giá</div><div class="v">${tk.so_danh_gia}</div><div class="d">Kỳ ${LOAIKY_TEN[S.nsTKLoai]}</div></div>
      <div class="stat"><div class="k">Điểm trung bình</div><div class="v small">${tk.diem_trung_binh!=null?tk.diem_trung_binh:'—'}</div><div class="d">/ 100</div></div>
      <div class="stat"><div class="k">Phân loại</div><div class="v small" style="font-size:18px">
        <span class="badge b-ok">A:${pb.A||0}</span> <span class="badge b-info">B:${pb.B||0}</span>
        <span class="badge b-cho">C:${pb.C||0}</span> <span class="badge b-tc">D:${pb.D||0}</span></div><div class="d">Theo xếp loại</div></div>
    </div>
    <div class="panel"><div class="panel-h"><h3>Xu hướng điểm theo kỳ</h3><div class="spacer"></div>
      <select onchange="S.nsXhNV=this.value;nsRender()" style="padding:5px 8px;border:1px solid var(--line);border-radius:6px;font-size:12.5px;max-width:220px">${nvOpts}</select></div>
      <div class="panel-b">${_svgLine(pts,labs,{color:useNV?'#b45309':'#0e7490'})}
        <div style="color:var(--muted);font-size:12px;margin-top:4px">${useNV?('Xu hướng cá nhân: '+nvMap[S.nsXhNV]):'Điểm trung bình toàn công ty theo từng kỳ.'}</div></div></div>
    <div class="panel"><div class="panel-h"><h3>Kết quả công việc theo kỳ — ${LOAIKY_TEN[S.nsTKLoai]}</h3></div>
      <div class="panel-b"><table><thead><tr><th>Nhân viên</th><th>Vị trí</th><th>Kỳ</th><th class="num">Điểm</th><th>Xếp loại</th></tr></thead>
        <tbody>${rows}</tbody></table></div>
      <div class="panel-b" style="color:var(--muted);font-size:12px;padding-top:0">Xếp loại: A ≥ 85 · B ≥ 70 · C ≥ 50 · D &lt; 50. Điểm = Σ (trọng số × % đạt, tối đa 100%/chỉ tiêu).</div></div>
    ${canCfg?`<div class="panel"><div class="panel-h"><h3>Cấu hình thưởng KPI</h3><div class="spacer"></div><span class="badge b-info">Quyền Duyệt</span></div>
      <div class="panel-b">
        <div class="formrow">
          <div class="f" style="flex:2"><label>Mức thưởng cơ sở (₫)</label><input type="number" id="ct_co_so" value="${cfg.muc_co_so}"></div>
          <div class="f"><label>Hệ số A</label><input type="number" step="0.1" id="ct_a" value="${cfg.hs.A}"></div>
          <div class="f"><label>Hệ số B</label><input type="number" step="0.1" id="ct_b" value="${cfg.hs.B}"></div>
          <div class="f"><label>Hệ số C</label><input type="number" step="0.1" id="ct_c" value="${cfg.hs.C}"></div>
          <div class="f"><label>Hệ số D</label><input type="number" step="0.1" id="ct_d" value="${cfg.hs.D}"></div>
        </div>
        <button class="btn-sm" onclick="nsLuuCfgThuong()">Lưu cấu hình</button>
        <p style="color:var(--muted);font-size:12px;margin-top:8px">Thưởng KPI = <b>mức cơ sở × hệ số</b> (theo xếp loại đánh giá <b>tháng</b>). Vào tab <b>Bảng lương theo kỳ</b> bấm <b>Áp thưởng KPI</b> để cộng vào lương tháng (đã tính thuế/BH).</p>
      </div></div>`:''}`;
}
function _svgLine(pts,labels,opt){
  opt=opt||{};const w=opt.w||580,h=opt.h||210,pad=36,ymax=opt.ymax||100,col=opt.color||'#0e7490';
  if(!pts||!pts.length)return '<div style="color:var(--muted);padding:18px 4px">Chưa đủ dữ liệu để vẽ biểu đồ (cần ≥ 1 kỳ).</div>';
  const iw=w-pad-14,ih=h-pad-18,x0=pad,y0=h-pad;
  const X=i=>x0+(pts.length<=1?iw/2:iw*i/(pts.length-1));
  const Y=v=>y0-ih*Math.max(0,Math.min(v,ymax))/ymax;
  let g='';
  for(let k=0;k<=4;k++){const yy=y0-ih*k/4;g+=`<line x1="${x0}" y1="${yy.toFixed(1)}" x2="${x0+iw}" y2="${yy.toFixed(1)}" stroke="#eef2f4"/><text x="${x0-6}" y="${(yy+3).toFixed(1)}" text-anchor="end" font-size="10" fill="#9fb0bb">${ymax*k/4}</text>`;}
  const poly=pts.map((v,i)=>`${X(i).toFixed(1)},${Y(v).toFixed(1)}`).join(' ');
  const dots=pts.map((v,i)=>`<circle cx="${X(i).toFixed(1)}" cy="${Y(v).toFixed(1)}" r="3.6" fill="${col}"/><text x="${X(i).toFixed(1)}" y="${(Y(v)-8).toFixed(1)}" text-anchor="middle" font-size="10" fill="#374151">${v}</text>`).join('');
  const xl=labels.map((l,i)=>`<text x="${X(i).toFixed(1)}" y="${h-pad+15}" text-anchor="middle" font-size="9.5" fill="#6b7280">${l}</text>`).join('');
  return `<svg viewBox="0 0 ${w} ${h}" style="width:100%;max-width:${w}px;height:auto">${g}${pts.length>1?`<polyline points="${poly}" fill="none" stroke="${col}" stroke-width="2"/>`:''}${dots}${xl}</svg>`;
}
async function nsXuatExcel(){
  const qs=`?loai_ky=${S.nsTKLoai}`;
  if(S.mode!=="live"){
    const list=(S.demoDanhGia||[]).filter(d=>d.loai_ky===S.nsTKLoai);
    const rows=[["Họ tên","Vị trí","Kỳ","Tổng điểm","Xếp loại"],...list.map(d=>[d.ho_ten,ROLE_NAME[d.vai_tro]||d.vai_tro||'',d.ky,d.tong_diem,d.xep_loai])];
    const csv='\ufeff'+rows.map(r=>r.map(x=>`"${String(x).replace(/"/g,'""')}"`).join(',')).join('\n');
    const b=new Blob([csv],{type:'text/csv;charset=utf-8'}),u=URL.createObjectURL(b),a=document.createElement('a');
    a.href=u;a.download=`danh-gia-kpi_${S.nsTKLoai}.csv`;a.click();URL.revokeObjectURL(u);toast("Đã xuất CSV (demo)","ok");return;
  }
  try{
    const hd={}; if(S.token)hd['Authorization']='Bearer '+S.token;
    const r=await fetch(S.api+`/nhan-su/danh-gia-xuat${qs}`,{headers:hd});
    if(!r.ok){toast("Không xuất được Excel","err");return;}
    const blob=await r.blob(),u=URL.createObjectURL(blob),a=document.createElement('a');
    a.href=u;a.download=`danh-gia-kpi_${S.nsTKLoai}.xlsx`;document.body.appendChild(a);a.click();a.remove();
    setTimeout(()=>URL.revokeObjectURL(u),4000);toast("Đã xuất Excel","ok");
  }catch(e){toast(e.message,"err");}
}
async function nsLuuCfgThuong(){
  const body={muc_co_so:Number(gv("ct_co_so")||0),hs_a:Number(gv("ct_a")||0),hs_b:Number(gv("ct_b")||0),hs_c:Number(gv("ct_c")||0),hs_d:Number(gv("ct_d")||0)};
  if(S.mode!=="live"){S.cfgThuong={muc_co_so:body.muc_co_so,hs:{A:body.hs_a,B:body.hs_b,C:body.hs_c,D:body.hs_d}};toast("Đã lưu cấu hình (demo)","ok");return;}
  try{await api("/nhan-su/cau-hinh-thuong-kpi",{method:'PUT',body:JSON.stringify(body)});toast("Đã lưu cấu hình thưởng KPI","ok");}
  catch(e){toast(e.detail||e.message,"err");}
}
async function nsApThuongKPI(){
  if(S.mode!=="live"){toast("Áp thưởng KPI chạy ở bản kết nối backend","err");return;}
  try{const r=await api(`/nhan-su/ky-luong/${S.nsThang}/ap-thuong-kpi`,{method:'POST'});
    toast(`Đã áp thưởng KPI cho ${r.so_ap} nhân viên (tháng ${S.nsThang})`,"ok");nsRender();
  }catch(e){toast(e.detail||e.message,"err");}
}

/* --- Tab Hồ sơ lương --- */
async function nsHoSo(host){
  const canOp=can("nhan_su","THAO_TAC");
  const ds = S.mode==="live" ? await api("/nhan-su/ho-so") : _nsDemoHoSo();
  const rows=ds.map(x=>`<tr><td><b>${x.ma||x.id}</b></td><td>${x.ho_ten}</td><td>${x.chuc_danh||''}</td>
    <td class="num">${vnd(x.luong_co_ban)}</td><td class="num">${vnd(x.luong_dong_bh||x.luong_co_ban)}</td>
    <td class="num">${vnd((x.phu_cap_an||0)+(x.phu_cap_di_lai||0)+(x.phu_cap_dien_thoai||0)+(x.phu_cap_trach_nhiem||0))}</td>
    <td class="num">${x.so_phu_thuoc||0}</td><td>${x.email||'<span style="color:#dc2626">— thiếu —</span>'}</td>
    ${canOp?`<td><button class="btn-sm ghost" onclick='nsSuaHoSo(${JSON.stringify(x).replace(/'/g,"&#39;")})'>Sửa</button></td>`:'<td></td>'}</tr>`).join('');
  host.innerHTML=`<div class="note" style="padding:0 0 10px;display:flex;align-items:center;gap:10px;flex-wrap:wrap">
    <span style="flex:1">Khai báo lương cơ bản, lương đóng BH, phụ cấp, số người phụ thuộc (giảm trừ thuế), tài khoản & <b>email</b> nhận phiếu lương cho từng nhân viên.</span>
    ${can("nhan_su","DUYET")?'<button class="btn-sm ghost" onclick="nsThamSo()">⚖️ Tham số lương theo luật</button>':''}</div>
    <div class="panel"><div class="panel-h"><h3>Hồ sơ lương nhân viên</h3></div><div class="panel-b"><table>
    <thead><tr><th>Mã</th><th>Họ tên</th><th>Chức danh</th><th class="num">Lương CB</th><th class="num">Lương đóng BH</th><th class="num">Phụ cấp</th><th class="num">Phụ thuộc</th><th>Email</th><th></th></tr></thead>
    <tbody>${rows||'<tr><td colspan="9" class="empty">Chưa có nhân viên.</td></tr>'}</tbody></table></div></div>`;
}
function nsSuaHoSo(x){
  const f=(id,lb,v,t='number')=>`<div class="f"><label>${lb}</label><input id="${id}" type="${t}" value="${v??''}"></div>`;
  _ktModal("Hồ sơ lương — "+x.ho_ten,`
    <div class="formrow">${f('h_lcb','Lương cơ bản',x.luong_co_ban)}${f('h_ldbh','Lương đóng BH (0=theo lương CB)',x.luong_dong_bh)}${f('h_pt','Số người phụ thuộc',x.so_phu_thuoc||0)}</div>
    <div class="formrow">${f('h_pan','Phụ cấp ăn',x.phu_cap_an||0)}${f('h_pdl','Phụ cấp đi lại',x.phu_cap_di_lai||0)}${f('h_pdt','Phụ cấp điện thoại',x.phu_cap_dien_thoai||0)}${f('h_ptn','Phụ cấp trách nhiệm',x.phu_cap_trach_nhiem||0)}</div>
    <div class="formrow">${f('h_email','Email nhận phiếu lương',x.email||'','email')}${f('h_stk','Số tài khoản',x.so_tai_khoan||'','text')}${f('h_nh','Ngân hàng',x.ngan_hang||'','text')}<div class="f"><label>TK chi phí</label><select id="h_tk"><option ${x.tk_chi_phi==='642'?'selected':''}>642</option><option ${x.tk_chi_phi==='622'?'selected':''}>622</option><option ${x.tk_chi_phi==='627'?'selected':''}>627</option></select></div></div>
    <div style="text-align:right;margin-top:8px"><button class="btn-sm" onclick="nsLuuHoSo(${x.id})">Lưu hồ sơ</button></div>`);
}
async function nsLuuHoSo(id){
  const body={luong_co_ban:Number(gv('h_lcb')||0),luong_dong_bh:Number(gv('h_ldbh')||0),so_phu_thuoc:Number(gv('h_pt')||0),
    phu_cap_an:Number(gv('h_pan')||0),phu_cap_di_lai:Number(gv('h_pdl')||0),phu_cap_dien_thoai:Number(gv('h_pdt')||0),phu_cap_trach_nhiem:Number(gv('h_ptn')||0),
    email:gv('h_email')||null,so_tai_khoan:gv('h_stk')||null,ngan_hang:gv('h_nh')||null,tk_chi_phi:gv('h_tk')||'642'};
  if(S.mode==="live"){ try{await api(`/nhan-su/nhan-vien/${id}/ho-so`,{method:'PUT',body:JSON.stringify(body)});toast("Đã lưu hồ sơ","ok");}catch(e){toast(e.detail||e.message,"err");return;} }
  else toast("Đã lưu (demo)","ok");
  const md=document.getElementById('ktModal'); if(md)md.remove(); nsRender();
}

async function nsThamSo(){
  let ts; try{ ts = S.mode==="live" ? await api("/nhan-su/tham-so-luong") : {tl_bhxh_nv:0.08,tl_bhyt_nv:0.015,tl_bhtn_nv:0.01,tl_bhxh_dn:0.175,tl_bhyt_dn:0.03,tl_bhtn_dn:0.01,tran_bhxh_bhyt:46800000,tran_bhtn:99200000,giam_tru_ban_than:11000000,giam_tru_phu_thuoc:4400000,mien_thue_an:730000,hs_ot_thuong:1.5,hs_ot_cuoi_tuan:2,hs_ot_le:3,luong_co_so:2340000,luong_toi_thieu_vung:4960000,bac_thue:[[5000000,0.05],[10000000,0.10],[18000000,0.15],[32000000,0.20],[52000000,0.25],[80000000,0.30],[null,0.35]]}; }catch(e){toast(e.detail||e.message,"err");return;}
  const pct=(id,lb,v)=>`<div class="f"><label>${lb}</label><input id="${id}" type="number" step="0.01" value="${(v*100).toFixed(2)}"> %</div>`;
  const num=(id,lb,v,step)=>`<div class="f"><label>${lb}</label><input id="${id}" type="number" ${step?`step="${step}"`:''} value="${v}"></div>`;
  const bac=(ts.bac_thue||[]).map(b=>`${b[0]===null?'> '+(0).toLocaleString():'≤ '+Number(b[0]).toLocaleString('vi-VN')}: ${(b[1]*100).toFixed(0)}%`).join('  ·  ');
  _ktModal("Tham số lương theo luật",`
    <div class="note" style="margin-bottom:8px">Các tham số này dùng để tính BHXH/BHYT/BHTN và thuế TNCN. Khi Nhà nước thay đổi (lương cơ sở, mức giảm trừ, trần đóng, biểu thuế…), cập nhật tại đây — lương các kỳ <b>chưa chốt</b> sẽ tính lại theo tham số mới.</div>
    <div style="font-weight:600;margin:4px 0;font-size:13px">Tỷ lệ bảo hiểm — Người lao động</div>
    <div class="formrow">${pct('t_bhxhnv','BHXH',ts.tl_bhxh_nv)}${pct('t_bhytnv','BHYT',ts.tl_bhyt_nv)}${pct('t_bhtnnv','BHTN',ts.tl_bhtn_nv)}</div>
    <div style="font-weight:600;margin:6px 0;font-size:13px">Tỷ lệ bảo hiểm — Doanh nghiệp</div>
    <div class="formrow">${pct('t_bhxhdn','BHXH',ts.tl_bhxh_dn)}${pct('t_bhytdn','BHYT',ts.tl_bhyt_dn)}${pct('t_bhtndn','BHTN',ts.tl_bhtn_dn)}</div>
    <div style="font-weight:600;margin:6px 0;font-size:13px">Trần đóng & giảm trừ</div>
    <div class="formrow">${num('t_tranxhyt','Trần BHXH/BHYT',ts.tran_bhxh_bhyt)}${num('t_trantn','Trần BHTN',ts.tran_bhtn)}${num('t_gtbt','Giảm trừ bản thân',ts.giam_tru_ban_than)}${num('t_gtpt','Giảm trừ/người phụ thuộc',ts.giam_tru_phu_thuoc)}</div>
    <div class="formrow">${num('t_an','Miễn thuế cơm trưa',ts.mien_thue_an)}${num('t_lcs','Lương cơ sở',ts.luong_co_so)}${num('t_lttv','LTT vùng',ts.luong_toi_thieu_vung)}</div>
    <div style="font-weight:600;margin:6px 0;font-size:13px">Hệ số tăng ca</div>
    <div class="formrow">${num('t_otth','Ngày thường',ts.hs_ot_thuong,'0.1')}${num('t_otct','Cuối tuần',ts.hs_ot_cuoi_tuan,'0.1')}${num('t_otle','Lễ/Tết',ts.hs_ot_le,'0.1')}</div>
    <div style="font-weight:600;margin:6px 0;font-size:13px">Biểu thuế TNCN lũy tiến (hiện hành)</div>
    <div style="font-size:12px;color:var(--muted);margin-bottom:4px">${bac}</div>
    <div class="f"><label>Biểu thuế (JSON nâng cao — để trống nếu không đổi)</label><input id="t_bac" placeholder='[[5000000,0.05],...,[null,0.35]]'></div>
    <div style="text-align:right;margin-top:8px"><button class="btn-sm" onclick="nsLuuThamSo()">Lưu tham số</button></div>`);
}
async function nsLuuThamSo(){
  const body={tl_bhxh_nv:Number(gv('t_bhxhnv'))/100,tl_bhyt_nv:Number(gv('t_bhytnv'))/100,tl_bhtn_nv:Number(gv('t_bhtnnv'))/100,
    tl_bhxh_dn:Number(gv('t_bhxhdn'))/100,tl_bhyt_dn:Number(gv('t_bhytdn'))/100,tl_bhtn_dn:Number(gv('t_bhtndn'))/100,
    tran_bhxh_bhyt:Number(gv('t_tranxhyt')||0),tran_bhtn:Number(gv('t_trantn')||0),giam_tru_ban_than:Number(gv('t_gtbt')||0),giam_tru_phu_thuoc:Number(gv('t_gtpt')||0),
    mien_thue_an:Number(gv('t_an')||0),luong_co_so:Number(gv('t_lcs')||0),luong_toi_thieu_vung:Number(gv('t_lttv')||0),
    hs_ot_thuong:Number(gv('t_otth')||1.5),hs_ot_cuoi_tuan:Number(gv('t_otct')||2),hs_ot_le:Number(gv('t_otle')||3)};
  const bacRaw=gv('t_bac'); if(bacRaw){ try{body.bac_thue=JSON.parse(bacRaw);}catch{toast("Biểu thuế JSON không hợp lệ","err");return;} }
  if(S.mode!=="live"){toast("Đã lưu (demo)","ok");const md=document.getElementById('ktModal');if(md)md.remove();return;}
  try{await api("/nhan-su/tham-so-luong",{method:'PUT',body:JSON.stringify(body)});toast("Đã lưu tham số luật. Các kỳ chưa chốt sẽ tính lại khi cập nhật chấm công.","ok");const md=document.getElementById('ktModal');if(md)md.remove();}catch(e){toast(e.detail||e.message,"err");}
}

/* --- Tab Bảng lương theo kỳ --- */
async function nsBangLuong(host){
  const canOp=can("nhan_su","THAO_TAC");
  let det;
  det = S.mode==="live" ? await api(`/nhan-su/ky-luong/${S.nsThang}`) : _nsDemoKy();
  const ky=det.ky, pl=det.phieu||[], tg=det.tong||{}, daChot=ky.trang_thai==="DA_CHOT";
  const st=NS_TT[ky.trang_thai]||[ky.trang_thai,'b-cho'];
  // thanh điều khiển kỳ
  let html=`<div class="panel"><div class="panel-b" style="display:flex;flex-wrap:wrap;gap:10px;align-items:end;padding:14px 18px">
    <div class="f" style="min-width:140px"><label>Tháng lương</label><input type="month" id="ns_thang" value="${S.nsThang}"></div>
    <button class="btn-sm ghost" onclick="nsXemThang()">Xem</button>
    <div style="flex:1"></div>
    ${!daChot&&canOp?`<div class="f" style="min-width:110px"><label>Công chuẩn</label><input type="number" id="ns_cc" value="${ky.cong_chuan||26}"></div>
      <div class="f" style="min-width:150px"><label>Hạn chốt (≤ ngày 7)</label><input type="date" id="ns_hanchot" value="${ky.ngay_chot||''}"></div>
      <button class="btn-sm" onclick="nsSinhBang()">Sinh / cập nhật bảng lương</button>
      <button class="btn-sm ghost" onclick="nsApThuongKPI()">★ Áp thưởng KPI</button>`:''}</div></div>`;
  // trạng thái + cảnh báo trễ hạn
  html+=`<div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;padding:0 0 10px">
    <span class="badge ${st[1]}">${st[0]}</span>
    ${ky.ngay_chot?`<span style="color:var(--muted);font-size:13px">Hạn chốt: <b>${ky.ngay_chot}</b></span>`:''}
    ${det.tre_han?'<span class="badge b-tc">⚠️ Trễ hạn chốt (đã quá ngày 7)</span>':''}
    ${ky.da_gui_email?'<span class="badge b-ok">Đã gửi email</span>':''}</div>`;
  // thẻ tổng
  html+=`<div style="display:flex;flex-wrap:wrap;gap:8px;padding:0 0 12px">
    ${_tcCard("Tổng thu nhập",vnd(tg.thu_nhap||0))}${_tcCard("BH người LĐ",vnd(tg.bh_nv||0),null,'#dc2626')}
    ${_tcCard("BH doanh nghiệp",vnd(tg.bh_dn||0),"chi phí DN",'#dc2626')}${_tcCard("Thuế TNCN",vnd(tg.thue_tncn||0))}
    ${_tcCard("Thực lĩnh",vnd(tg.thuc_linh||0),null,'#16a34a')}${_tcCard("TỔNG CHI PHÍ LƯƠNG (DN)",vnd(tg.chi_phi_dn||0),"lương + BH DN",'#0e7490')}</div>`;
  // bảng phiếu lương
  const rows=pl.map(p=>{const edit=!daChot&&canOp; const khauTru=(p.khau_tru_nghi||0)+(p.khau_tru_tre||0)+(p.khau_tru_khac||0);
    const otTong=(p.gio_ot_thuong||0)+(p.gio_ot_cuoi_tuan||0)+(p.gio_ot_le||0);
    return `<tr><td><b>${p.ho_ten}</b><div style="font-size:11px;color:var(--muted)">${p.chuc_danh||''}</div></td>
      <td class="num">${p.cong_thuc_te}${p.ngay_nghi_kpep>0?`<div style="font-size:11px;color:#dc2626">nghỉ KP ${p.ngay_nghi_kpep}</div>`:''}</td>
      <td class="num">${otTong>0?vnd(p.ot):'—'}${otTong>0?`<div style="font-size:11px;color:var(--muted)">${otTong}h</div>`:''}</td>
      <td class="num">${vnd(p.phu_cap)}${p.phu_cap_khac>0?`<div style="font-size:11px;color:#16a34a">+PS ${vnd(p.phu_cap_khac)}</div>`:''}${p.thuong_kpi>0?`<div style="font-size:11px;color:#0e7490">+KPI ${vnd(p.thuong_kpi)}</div>`:''}</td>
      <td class="num">${vnd(p.tong_thu_nhap)}</td>
      <td class="num" style="color:#dc2626">${vnd(p.bhxh+p.bhyt+p.bhtn)}</td><td class="num" style="color:#dc2626">${vnd(p.thue_tncn)}</td>
      <td class="num" style="color:#dc2626">${khauTru>0?vnd(khauTru):'—'}${(p.tam_ung||0)>0?`<div style="font-size:11px;color:#dc2626">ứng ${vnd(p.tam_ung)}</div>`:''}</td>
      <td class="num"><b style="color:#16a34a">${vnd(p.thuc_linh)}</b></td>
      <td>${p.email_sent?'<span class="badge b-ok">đã gửi</span> ':''}
        ${edit?`<button class="btn-sm ghost" onclick='nsChamCong(${JSON.stringify(p).replace(/'/g,"&#39;")})'>Chấm công</button>`:''}
        <button class="btn-sm ghost" onclick="nsXemPhieu(${p.id})">Phiếu</button></td></tr>`;}).join('');
  html+=`<div class="panel"><div class="panel-h"><h3>Bảng lương ${ky.thang} (${pl.length} người)</h3><div class="spacer"></div>
    ${!daChot&&canOp&&pl.length?`<button class="btn-sm" onclick="nsChot()">🔒 Chốt lương & hạch toán</button>`:''}
    ${daChot&&canOp?`<button class="btn-sm" onclick="nsGuiEmail()">📧 Gửi email phiếu lương</button>`:''}</div>
    <div class="panel-b"><table><thead><tr><th>Nhân viên</th><th class="num">Công</th><th class="num">Tăng ca</th><th class="num">Phụ cấp</th><th class="num">Tổng TN</th><th class="num">BH (NLĐ)</th><th class="num">TNCN</th><th class="num">Khấu trừ</th><th class="num">Thực lĩnh</th><th></th></tr></thead>
    <tbody>${rows||'<tr><td colspan="10" class="empty">Chưa có bảng lương — bấm "Sinh bảng lương" để tạo.</td></tr>'}</tbody></table>
    <div class="note" style="margin-top:8px;color:var(--muted)">OT: ngày thường ×1,5 · cuối tuần ×2 · lễ/Tết ×3. BH: NLĐ 10,5% · DN 21,5% (áp trần). TNCN lũy tiến (miễn thuế cơm trưa ≤730k & phần vượt OT). Cột "Khấu trừ" gồm nghỉ không phép + đi trễ + khấu trừ khác (+ tạm ứng). Bấm <b>Chấm công</b> để nhập tay; khi có <b>app chấm công</b>, dữ liệu công/OT/nghỉ KP/đi trễ sẽ tự đồng bộ vào kỳ (API <code>/nhan-su/ky-luong/{thang}/cham-cong-import</code>). Tỷ lệ BH & biểu thuế lấy từ <b>Tham số lương theo luật</b> (tab Hồ sơ lương).</div></div></div>`;
  host.innerHTML=html;
}
function nsChamCong(p){
  const f=(id,lb,v,step)=>`<div class="f"><label>${lb}</label><input id="${id}" type="number" ${step?`step="${step}"`:''} value="${v??0}"></div>`;
  _ktModal("Chấm công — "+p.ho_ten+" · "+p.thang,`
    <div style="font-weight:600;margin:2px 0 4px;font-size:13px">Công & tăng ca</div>
    <div class="formrow">${f('cc_cong','Công thực tế (được trả)',p.cong_thuc_te)}${f('cc_ott','OT ngày thường (giờ)',p.gio_ot_thuong)}${f('cc_otc','OT cuối tuần (giờ)',p.gio_ot_cuoi_tuan)}${f('cc_otl','OT lễ/Tết (giờ)',p.gio_ot_le)}</div>
    <div style="font-weight:600;margin:8px 0 4px;font-size:13px">Phụ cấp phát sinh trong kỳ</div>
    <div class="formrow">${f('cc_pck','Phụ cấp / thưởng phát sinh',p.phu_cap_khac)}</div>
    <div style="font-weight:600;margin:8px 0 4px;font-size:13px">Khấu trừ</div>
    <div class="formrow">${f('cc_nghi','Nghỉ không phép (số ngày)',p.ngay_nghi_kpep,'0.5')}${f('cc_tre','Đi làm trễ (tổng phút)',p.so_phut_di_tre)}${f('cc_ktk','Khấu trừ khác (sau thuế)',p.khau_tru_khac)}${f('cc_tu','Tạm ứng',p.tam_ung)}</div>
    <div class="note" style="color:var(--muted)">Nghỉ không phép trừ theo đơn giá ngày (lương/công chuẩn); đi trễ trừ theo đơn giá phút. "Công thực tế" là số công được trả lương (không gồm ngày nghỉ KP).</div>
    <div style="text-align:right;margin-top:8px"><button class="btn-sm" onclick="nsLuuChamCong(${p.id})">Lưu & tính lại</button></div>`);
}
function nsXemThang(){const v=gv('ns_thang');if(v){S.nsThang=v;nsRender();}}
async function nsSinhBang(){
  const body={thang:S.nsThang,cong_chuan:Number(gv('ns_cc')||26),ngay_chot:gv('ns_hanchot')||null};
  if(S.mode!=="live"){toast("Sinh bảng lương (demo)","ok");return;}
  try{const r=await api("/nhan-su/ky-luong",{method:'POST',body:JSON.stringify(body)});toast(`Đã sinh ${r.so_nhan_vien} bảng lương`,"ok");nsRender();}catch(e){toast(e.detail||e.message,"err");}
}
async function nsLuuChamCong(id){
  const body={cong_thuc_te:Number(gv('cc_cong')||0),gio_ot_thuong:Number(gv('cc_ott')||0),gio_ot_cuoi_tuan:Number(gv('cc_otc')||0),gio_ot_le:Number(gv('cc_otl')||0),
    phu_cap_khac:Number(gv('cc_pck')||0),ngay_nghi_kpep:Number(gv('cc_nghi')||0),so_phut_di_tre:Number(gv('cc_tre')||0),khau_tru_khac:Number(gv('cc_ktk')||0),tam_ung:Number(gv('cc_tu')||0)};
  if(S.mode!=="live"){toast("Đã lưu (demo)","ok");const md=document.getElementById('ktModal');if(md)md.remove();return;}
  try{await api(`/nhan-su/phieu-luong/${id}`,{method:'PUT',body:JSON.stringify(body)});toast("Đã cập nhật & tính lại","ok");const md=document.getElementById('ktModal');if(md)md.remove();nsRender();}catch(e){toast(e.detail||e.message,"err");}
}
async function nsChot(){
  if(!confirm("Chốt lương sẽ hạch toán chi phí lương và khóa kỳ. Tiếp tục?"))return;
  if(S.mode!=="live"){toast("Đã chốt (demo)","ok");return;}
  try{const r=await api(`/nhan-su/ky-luong/${S.nsThang}/chot`,{method:'POST'});toast(`Đã chốt · ${r.so_but_toan_luong} bút toán · chi phí DN ${vnd(r.tong_chi_phi_dn)}`,"ok");nsRender();}catch(e){toast(e.detail||e.message,"err");}
}
async function nsGuiEmail(){
  if(S.mode!=="live"){toast("Đã gửi email (demo)","ok");return;}
  try{const r=await api(`/nhan-su/ky-luong/${S.nsThang}/gui-email`,{method:'POST'});
    let msg=`Đã gửi ${r.da_gui} phiếu lương`; if(r.tre_han)msg+=" (lưu ý: trễ hạn ngày 7)"; if(r.bo_qua_thieu_email&&r.bo_qua_thieu_email.length)msg+=` · ${r.bo_qua_thieu_email.length} người thiếu email`;
    toast(msg,r.tre_han?"err":"ok");nsRender();}catch(e){toast(e.detail||e.message,"err");}
}
async function nsXemPhieu(id){
  let p; try{ p = S.mode==="live" ? await api(`/nhan-su/phieu-luong/${id}`) : (_nsDemoKy().phieu.find(x=>x.id===id)); }catch(e){toast(e.detail||e.message,"err");return;}
  const r=(l,v,c)=>`<tr><td style="padding:4px 0">${l}</td><td class="num" style="${c?('color:'+c):''}">${vnd(v)}</td></tr>`;
  _ktModal(`Phiếu lương ${p.thang} — ${p.ho_ten}`,`
    <div style="color:var(--muted);font-size:13px;margin-bottom:8px">${p.chuc_danh||''} · Công ${p.cong_thuc_te}/${p.cong_chuan} · OT: ${p.gio_ot_thuong}h/${p.gio_ot_cuoi_tuan}h/${p.gio_ot_le}h</div>
    <table style="width:100%"><tbody>
    ${r('Lương theo công',(p.luong_thuc_te||0)+(p.khau_tru_nghi||0)+(p.khau_tru_tre||0))}${r('Tăng ca',p.ot)}${r('Phụ cấp'+(p.phu_cap_khac>0?' (gồm PS '+vnd(p.phu_cap_khac)+')':''),p.phu_cap)}
    ${p.khau_tru_nghi>0?r(`Trừ nghỉ không phép (${p.ngay_nghi_kpep} ngày)`,-p.khau_tru_nghi,'#dc2626'):''}
    ${p.khau_tru_tre>0?r(`Trừ đi trễ (${p.so_phut_di_tre} phút)`,-p.khau_tru_tre,'#dc2626'):''}
    <tr style="font-weight:700;border-top:1px solid var(--line)">${`<td style="padding-top:6px">TỔNG THU NHẬP</td><td class="num" style="padding-top:6px">${vnd(p.tong_thu_nhap)}</td>`}</tr>
    ${r('BHXH (8%)',-p.bhxh,'#dc2626')}${r('BHYT (1,5%)',-p.bhyt,'#dc2626')}${r('BHTN (1%)',-p.bhtn,'#dc2626')}${r('Thuế TNCN',-p.thue_tncn,'#dc2626')}${p.khau_tru_khac>0?r('Khấu trừ khác',-p.khau_tru_khac,'#dc2626'):''}${p.tam_ung?r('Tạm ứng',-p.tam_ung,'#dc2626'):''}
    <tr style="font-weight:700;font-size:16px;border-top:2px solid #0e7490"><td style="padding-top:8px;color:#0e7490">THỰC LĨNH</td><td class="num" style="padding-top:8px;color:#0e7490">${vnd(p.thuc_linh)}</td></tr>
    </tbody></table>
    <div style="margin-top:10px;padding-top:8px;border-top:1px solid var(--line);font-size:13px;color:var(--muted)">Chi phí DN (gồm BH DN): <b>${vnd(p.chi_phi_dn)}</b>${p.so_tai_khoan?` · CK: ${p.so_tai_khoan} ${p.ngan_hang||''}`:''}</div>`);
}
function _nsDemoHoSo(){return [
  {id:1,ma:"NV001",ho_ten:"Trần Văn Kỹ",chuc_danh:"Kỹ sư",luong_co_ban:20000000,luong_dong_bh:20000000,so_phu_thuoc:1,phu_cap_an:730000,phu_cap_di_lai:500000,phu_cap_dien_thoai:300000,phu_cap_trach_nhiem:0,email:"ky@svws.vn",so_tai_khoan:"0123456789",ngan_hang:"VCB",tk_chi_phi:"642"},
  {id:2,ma:"NV002",ho_ten:"Lê Thị Hành",chuc_danh:"Hành chính",luong_co_ban:12000000,luong_dong_bh:12000000,so_phu_thuoc:0,phu_cap_an:730000,phu_cap_di_lai:300000,phu_cap_dien_thoai:200000,phu_cap_trach_nhiem:0,email:"hanh@svws.vn",tk_chi_phi:"642"}];}
function _nsDemoKy(){
  const pl=[
    {id:1,nhan_vien_id:1,ho_ten:"Trần Văn Kỹ",chuc_danh:"Kỹ sư",thang:_nsThangMacDinh(),cong_chuan:26,cong_thuc_te:26,gio_ot_thuong:10,gio_ot_cuoi_tuan:0,gio_ot_le:0,luong_thuc_te:20000000,ot:1442308,phu_cap:1530000,tong_thu_nhap:22972308,bhxh:1600000,bhyt:300000,bhtn:200000,bhxh_dn:3500000,bhyt_dn:600000,bhtn_dn:200000,thue_tncn:228077,tam_ung:0,thuc_linh:20644231,chi_phi_dn:27272308,email_sent:false,so_tai_khoan:"0123456789",ngan_hang:"VCB"},
    {id:2,nhan_vien_id:2,ho_ten:"Lê Thị Hành",chuc_danh:"Hành chính",thang:_nsThangMacDinh(),cong_chuan:26,cong_thuc_te:26,gio_ot_thuong:0,gio_ot_cuoi_tuan:0,gio_ot_le:0,luong_thuc_te:12000000,ot:0,phu_cap:1230000,tong_thu_nhap:13230000,bhxh:960000,bhyt:180000,bhtn:120000,bhxh_dn:2100000,bhyt_dn:360000,bhtn_dn:120000,thue_tncn:0,tam_ung:0,thuc_linh:11970000,chi_phi_dn:15810000,email_sent:false}];
  const sum=k=>pl.reduce((s,p)=>s+(p[k]||0),0);
  return {ky:{thang:_nsThangMacDinh(),cong_chuan:26,ngay_chot:_nsThangMacDinh()+"-07",trang_thai:"NHAP",da_gui_email:false},tre_han:false,phieu:pl,
    tong:{thu_nhap:sum('tong_thu_nhap'),thuc_linh:sum('thuc_linh'),bh_nv:sum('bhxh')+sum('bhyt')+sum('bhtn'),bh_dn:sum('bhxh_dn')+sum('bhyt_dn')+sum('bhtn_dn'),thue_tncn:sum('thue_tncn'),chi_phi_dn:sum('chi_phi_dn')}};
}

/* ---- Tab Tiền vay ---- */
const VAY_PT={GOC_DEU:"Gốc đều (lãi giảm dần)",TRA_DEU:"Trả đều (niên kim)",GOC_CUOI:"Lãi hàng kỳ, gốc cuối"};
async function tcVay(host){
  const canOp=can("tai_chinh","THAO_TAC");
  let ds,tq;
  if(S.mode==="live"){ [ds,tq]=await Promise.all([api("/vay"),api("/vay/tong-quan")]); }
  else { ds=_tcDemoVay(); tq={du_no_goc:450000000,du_no_ngan_han:450000000,du_no_dai_han:0,lai_con_phai_tra:18750000,so_ky_qua_han:0,goc_qua_han:0,lai_qua_han:0}; }
  let html=`<div style="display:flex;flex-wrap:wrap;gap:8px;padding:0 0 12px">
    ${_tcCard("Dư nợ gốc",vnd(tq.du_no_goc))}${_tcCard("Vay ngắn hạn",vnd(tq.du_no_ngan_han))}
    ${_tcCard("Vay dài hạn",vnd(tq.du_no_dai_han))}${_tcCard("Lãi còn phải trả",vnd(tq.lai_con_phai_tra))}
    ${_tcCard("Kỳ quá hạn",tq.so_ky_qua_han||0,tq.so_ky_qua_han?'⚠️ '+vnd(tq.goc_qua_han+tq.lai_qua_han):'',tq.so_ky_qua_han?'#dc2626':'#16a34a')}</div>`;
  if(canOp){
    html+=`<div class="panel"><div class="panel-h"><h3>Khế ước vay mới</h3></div><div class="panel-b">
      <div class="formrow"><div class="f" style="flex:2"><label>Bên cho vay</label><input id="v_ben" placeholder="VD: Ngân hàng ACB"></div>
        <div class="f"><label>Loại</label><select id="v_loai"><option value="NGAN_HAN">Ngắn hạn</option><option value="DAI_HAN">Dài hạn</option></select></div>
        <div class="f"><label>Số tiền gốc</label><input id="v_goc" type="number" placeholder="500000000"></div>
        <div class="f"><label>Lãi suất %/năm</label><input id="v_ls" type="number" step="0.1" placeholder="10"></div></div>
      <div class="formrow"><div class="f"><label>Phương thức</label><select id="v_pt"><option value="GOC_DEU">Gốc đều (lãi giảm dần)</option><option value="TRA_DEU">Trả đều (niên kim)</option><option value="GOC_CUOI">Lãi hàng kỳ, gốc cuối</option></select></div>
        <div class="f"><label>Ngày nhận</label><input id="v_ngay" type="date"></div>
        <div class="f"><label>Số kỳ</label><input id="v_soky" type="number" value="12"></div>
        <div class="f"><label>Chu kỳ (tháng/kỳ)</label><input id="v_ck" type="number" value="1"></div>
        <div class="f"><label>TK tiền</label><select id="v_tk"><option value="112">112 - Ngân hàng</option><option value="111">111 - Tiền mặt</option></select></div>
        <button class="btn-sm" style="align-self:end" onclick="tcTaoVay()">Tạo khế ước</button></div></div></div>`;
  }
  const rows=ds.map(v=>{const sap=v.ky_sap_toi;
    return `<tr><td><b>${v.so||('#'+v.id)}</b><div style="font-size:11px;color:var(--muted)">${VAY_PT[v.phuong_thuc]||v.phuong_thuc}</div></td>
      <td>${v.ben_cho_vay}</td><td><span class="badge ${v.loai==='NGAN_HAN'?'b-cho':'b-info'}">${v.loai==='NGAN_HAN'?'Ngắn hạn':'Dài hạn'}</span></td>
      <td class="num">${vnd(v.so_tien_goc)}</td><td class="num">${_num(v.lai_suat_nam,2)}%</td>
      <td class="num"><b>${vnd(v.con_lai_goc)}</b></td>
      <td>${sap?`${sap.ngay_den_han}<div style="font-size:11px;color:${sap.qua_han?'#dc2626':'var(--muted)'}">${sap.qua_han?'QUÁ HẠN · ':''}${vnd(sap.tong)}</div>`:'—'}</td>
      <td>${v.trang_thai==='DA_TAT_TOAN'?'<span class="badge b-ok">Tất toán</span>':(v.so_ky_qua_han?`<span class="badge b-tc">${v.so_ky_qua_han} kỳ quá hạn</span>`:'<span class="badge b-info">Đang vay</span>')}</td>
      <td><button class="btn-sm ghost" onclick="tcVayChiTiet(${v.id})">Lịch & trả nợ</button></td></tr>`;}).join('');
  html+=`<div class="panel"><div class="panel-h"><h3>Khế ước vay</h3></div><div class="panel-b"><table>
    <thead><tr><th>Số/Phương thức</th><th>Bên cho vay</th><th>Loại</th><th class="num">Gốc vay</th><th class="num">Lãi/năm</th><th class="num">Dư nợ</th><th>Kỳ tới</th><th>Trạng thái</th><th></th></tr></thead>
    <tbody>${rows||'<tr><td colspan="9" class="empty">Chưa có khoản vay nào.</td></tr>'}</tbody></table></div></div>`;
  host.innerHTML=html;
}
async function tcTaoVay(){
  const body={ben_cho_vay:gv('v_ben'),loai:gv('v_loai'),so_tien_goc:Number(gv('v_goc')||0),lai_suat_nam:Number(gv('v_ls')||0),
    phuong_thuc:gv('v_pt'),ngay_nhan:gv('v_ngay'),so_ky:Number(gv('v_soky')||12),chu_ky_thang:Number(gv('v_ck')||1),tk_tien:gv('v_tk')};
  if(!body.ben_cho_vay||body.so_tien_goc<=0||!body.ngay_nhan){toast("Nhập bên cho vay, số tiền và ngày nhận","err");return;}
  if(S.mode!=="live"){toast("Đã tạo khế ước (demo)","ok");return;}
  try{await api("/vay",{method:'POST',body:JSON.stringify(body)});toast("Đã tạo khế ước vay + hạch toán nhận tiền","ok");tcRender();}catch(e){toast(e.detail||e.message,"err");}
}
async function tcVayChiTiet(id){
  let v; try{ v = S.mode==="live" ? await api(`/vay/${id}`) : _tcDemoVay().find(x=>x.id===id); }catch(e){toast(e.detail||e.message,"err");return;}
  if(S.mode!=="live"&&!v.lich)v.lich=_tcDemoLich();
  const canOp=can("tai_chinh","THAO_TAC");
  const rows=(v.lich||[]).map(l=>`<tr class="${l.qua_han?'qh':''}"><td>${l.ky}</td><td>${l.ngay_den_han}${l.qua_han?' <span class="badge b-tc">quá hạn</span>':''}</td>
    <td class="num">${vnd(l.du_no_dau)}</td><td class="num">${vnd(l.goc_phai_tra)}</td><td class="num">${vnd(l.lai_phai_tra)}</td>
    <td class="num"><b>${vnd(l.tong_phai_tra)}</b></td><td class="num">${vnd(l.du_no_cuoi)}</td>
    <td>${l.da_tra?`<span class="badge b-ok">đã trả</span><div style="font-size:11px;color:var(--muted)">${l.ngay_tra||''}</div>`:(canOp&&v.trang_thai!=='DA_TAT_TOAN'?`<button class="btn-sm ghost" onclick="tcTraKy(${v.id},${l.ky})">Trả kỳ</button>`:'<span style="color:var(--muted)">chưa trả</span>')}</td></tr>`).join('');
  _ktModal(`Khế ước ${v.so||('#'+v.id)} — ${v.ben_cho_vay}`,`
    <div style="display:flex;flex-wrap:wrap;gap:14px;color:var(--muted);font-size:13px;margin-bottom:8px">
      <span>Gốc vay: <b style="color:var(--text)">${vnd(v.so_tien_goc)}</b></span><span>Lãi suất: <b style="color:var(--text)">${_num(v.lai_suat_nam,2)}%/năm</b></span>
      <span>Phương thức: <b style="color:var(--text)">${VAY_PT[v.phuong_thuc]||v.phuong_thuc}</b></span>
      <span>Dư nợ: <b style="color:var(--text)">${vnd(v.con_lai_goc)}</b></span><span>Đáo hạn: <b style="color:var(--text)">${v.ngay_dao_han||'—'}</b></span></div>
    <table><thead><tr><th>Kỳ</th><th>Đến hạn</th><th class="num">Dư nợ đầu</th><th class="num">Gốc</th><th class="num">Lãi</th><th class="num">Tổng trả</th><th class="num">Dư nợ cuối</th><th></th></tr></thead>
    <tbody>${rows||'<tr><td colspan="8" class="empty">—</td></tr>'}</tbody></table>`);
}
async function tcTraKy(id,ky){
  if(!confirm(`Xác nhận trả nợ kỳ ${ky}? Hệ thống sẽ hạch toán gốc (341) và lãi (635).`))return;
  if(S.mode!=="live"){toast("Đã trả (demo)","ok");return;}
  try{await api(`/vay/${id}/tra-ky/${ky}`,{method:'POST'});toast("Đã trả nợ & hạch toán","ok");
    const md=document.getElementById('ktModal'); if(md)md.remove(); tcVayChiTiet(id); tcRender();}catch(e){toast(e.detail||e.message,"err");}
}
function _tcDemoVay(){return [{id:1,so:"KU-2026-01",ben_cho_vay:"Ngân hàng ACB",loai:"NGAN_HAN",so_tien_goc:500000000,lai_suat_nam:10,phuong_thuc:"GOC_DEU",ngay_nhan:"2026-06-01",so_ky:10,chu_ky_thang:1,ngay_dao_han:"2027-04-01",con_lai_goc:450000000,trang_thai:"DANG_VAY",so_ky_qua_han:0,ky_sap_toi:{ky:2,ngay_den_han:"2026-08-01",goc:50000000,lai:3750000,tong:53750000,qua_han:false}}];}
function _tcDemoLich(){const L=[];let du=500000000;for(let k=1;k<=10;k++){const g=50000000,la=Math.round(du*0.10/12);L.push({ky:k,ngay_den_han:`2026-${String(6+k>12?6+k-12:6+k).padStart(2,'0')}-01`,du_no_dau:du,goc_phai_tra:g,lai_phai_tra:la,tong_phai_tra:g+la,du_no_cuoi:du-g,da_tra:k===1,ngay_tra:k===1?"2026-07-01":null,qua_han:false});du-=g;}return L;}

/* ===================== PHÂN HỆ DỰ ÁN ===================== */
const DA_LOAI={CAP_NUOC:"Cấp nước",NUOC_THAI:"Nước thải",KHI_THAI:"Khí thải",KHAC:"Khác"};
const DA_TT={MOI:"Mới",DANG_CHAY:"Đang chạy",NGHIEM_THU:"Nghiệm thu",HOAN_THANH:"Hoàn thành",TAM_DUNG:"Tạm dừng"};
const DA_GD={KHAO_SAT:"Khảo sát",THIET_KE:"Thiết kế",MUA_SAM:"Mua sắm",THI_CONG:"Thi công",LAP_DAT:"Lắp đặt",CHAY_THU:"Chạy thử",NGHIEM_THU:"Nghiệm thu",BAN_GIAO:"Bàn giao"};
const DA_TLOAI={THIET_BI:"Thiết bị",VAT_TU:"Vật tư",BAN_VE:"Bản vẽ",BB_GIAO_NHAN:"Biên bản giao nhận",BAN_GIAO:"Bàn giao",NGHIEM_THU:"Nghiệm thu",KHAC:"Khác"};
const DA_RR={CAO:"Cao",TRUNG:"Trung bình",THAP:"Thấp"};
const DA_TTMOC={CHUA_BAT_DAU:"Chưa bắt đầu",DANG_LAM:"Đang làm",HOAN_THANH:"Hoàn thành",CHAM_TRE:"Chậm trễ"};
/* Danh sách tiêu chuẩn VN làm NHÃN tham chiếu (không kèm giá trị giới hạn — giá trị do người dùng nhập). Gồm bản mới nhất + bản cũ cho dự án đang chuyển tiếp. */
const QC_NUOC=["QCVN 40:2025/BTNMT — Nước thải công nghiệp","QCVN 14:2025/BTNMT — Nước thải sinh hoạt/đô thị","QCVN 62:2025/BTNMT — Nước thải chăn nuôi","QCVN 01-1:2018/BYT — Nước sạch sinh hoạt","QCVN 08:2023/BTNMT — Chất lượng nước mặt","QCVN 09:2023/BTNMT — Chất lượng nước dưới đất","QCVN 40:2011/BTNMT — Nước thải công nghiệp (cũ)","QCVN 13-MT:2015/BTNMT — Nước thải dệt nhuộm (cũ)","QCVN 14:2008/BTNMT — Nước thải sinh hoạt (cũ)","QCVN 11-MT:2015/BTNMT — Nước thải thủy sản (cũ)","QCVN 12-MT:2015/BTNMT — Nước thải giấy & bột giấy (cũ)"];
const QC_KHI=["QCVN 19:2024/BTNMT — Khí thải công nghiệp","QCVN 05:2023/BTNMT — Chất lượng không khí xung quanh","QCVN 19:2009/BTNMT — Khí thải CN bụi & vô cơ (cũ)","QCVN 20:2009/BTNMT — Khí thải CN chất hữu cơ (cũ)","QCVN 23:2009/BTNMT — Khí thải sản xuất xi măng (cũ)","QCVN 51:2017/BTNMT — Khí thải sản xuất thép"];
function _qcList(loai){if(loai==='KHI_THAI')return QC_KHI;if(loai==='CAP_NUOC'||loai==='NUOC_THAI')return QC_NUOC;return QC_NUOC.concat(QC_KHI);}
/* Danh mục TÊN chỉ tiêu + đơn vị theo phạm vi tiêu chuẩn (KHÔNG kèm giá trị giới hạn — giá trị do người dùng nhập theo cột áp dụng). Mẫu tham chiếu, sửa/xóa được sau khi nạp. */
const _CT_NUOC_CN=[{ten:"pH",don_vi:"-"},{ten:"Nhiệt độ",don_vi:"°C"},{ten:"Màu",don_vi:"Pt-Co"},{ten:"BOD5",don_vi:"mg/L"},{ten:"COD",don_vi:"mg/L"},{ten:"TSS",don_vi:"mg/L"},{ten:"Amoni (theo N)",don_vi:"mg/L"},{ten:"Tổng Nitơ",don_vi:"mg/L"},{ten:"Tổng Phốt pho (theo P)",don_vi:"mg/L"},{ten:"Sunfua (theo H2S)",don_vi:"mg/L"},{ten:"Florua",don_vi:"mg/L"},{ten:"Xianua",don_vi:"mg/L"},{ten:"Phenol",don_vi:"mg/L"},{ten:"Dầu mỡ khoáng",don_vi:"mg/L"},{ten:"Asen (As)",don_vi:"mg/L"},{ten:"Thủy ngân (Hg)",don_vi:"mg/L"},{ten:"Chì (Pb)",don_vi:"mg/L"},{ten:"Cadimi (Cd)",don_vi:"mg/L"},{ten:"Crom VI",don_vi:"mg/L"},{ten:"Crom III",don_vi:"mg/L"},{ten:"Đồng (Cu)",don_vi:"mg/L"},{ten:"Kẽm (Zn)",don_vi:"mg/L"},{ten:"Niken (Ni)",don_vi:"mg/L"},{ten:"Sắt (Fe)",don_vi:"mg/L"},{ten:"Mangan (Mn)",don_vi:"mg/L"},{ten:"Clo dư",don_vi:"mg/L"},{ten:"Tổng Coliform",don_vi:"MPN/100mL"}];
const _CT_DET_NHUOM=[{ten:"pH",don_vi:"-"},{ten:"Nhiệt độ",don_vi:"°C"},{ten:"Độ màu (pH=7)",don_vi:"Pt-Co"},{ten:"BOD5",don_vi:"mg/L"},{ten:"COD",don_vi:"mg/L"},{ten:"TSS",don_vi:"mg/L"},{ten:"Tổng dầu mỡ khoáng",don_vi:"mg/L"},{ten:"Sunfua (theo H2S)",don_vi:"mg/L"},{ten:"Crom VI",don_vi:"mg/L"},{ten:"Crom III",don_vi:"mg/L"},{ten:"Sắt (Fe)",don_vi:"mg/L"},{ten:"Đồng (Cu)",don_vi:"mg/L"},{ten:"Clo dư",don_vi:"mg/L"},{ten:"Amoni (theo N)",don_vi:"mg/L"},{ten:"Tổng Nitơ",don_vi:"mg/L"}];
const _CT_SINH_HOAT=[{ten:"pH",don_vi:"-"},{ten:"BOD5",don_vi:"mg/L"},{ten:"TSS",don_vi:"mg/L"},{ten:"Tổng chất rắn hòa tan (TDS)",don_vi:"mg/L"},{ten:"Sunfua (theo H2S)",don_vi:"mg/L"},{ten:"Amoni (theo N)",don_vi:"mg/L"},{ten:"Nitrat (theo N)",don_vi:"mg/L"},{ten:"Dầu mỡ động thực vật",don_vi:"mg/L"},{ten:"Phosphat (PO4 theo P)",don_vi:"mg/L"},{ten:"Chất hoạt động bề mặt",don_vi:"mg/L"},{ten:"Tổng Coliform",don_vi:"MPN/100mL"}];
const _CT_KHI_CN=[{ten:"Lưu lượng khí thải",don_vi:"Nm³/h"},{ten:"Bụi tổng",don_vi:"mg/Nm³"},{ten:"SO2",don_vi:"mg/Nm³"},{ten:"NOx (theo NO2)",don_vi:"mg/Nm³"},{ten:"CO",don_vi:"mg/Nm³"},{ten:"HCl",don_vi:"mg/Nm³"},{ten:"HF",don_vi:"mg/Nm³"},{ten:"Cl2",don_vi:"mg/Nm³"},{ten:"H2S",don_vi:"mg/Nm³"},{ten:"NH3",don_vi:"mg/Nm³"},{ten:"Chì (Pb)",don_vi:"mg/Nm³"},{ten:"Thủy ngân (Hg)",don_vi:"mg/Nm³"},{ten:"Cadimi (Cd)",don_vi:"mg/Nm³"},{ten:"Asen (As)",don_vi:"mg/Nm³"}];
const _CT_KK_XQ=[{ten:"SO2",don_vi:"µg/m³"},{ten:"CO",don_vi:"µg/m³"},{ten:"NO2",don_vi:"µg/m³"},{ten:"O3",don_vi:"µg/m³"},{ten:"Bụi tổng (TSP)",don_vi:"µg/m³"},{ten:"Bụi PM10",don_vi:"µg/m³"},{ten:"Bụi PM2.5",don_vi:"µg/m³"},{ten:"Chì (Pb)",don_vi:"µg/m³"}];
const _CT_NUOC_MAT=[{ten:"pH",don_vi:"-"},{ten:"DO (oxy hòa tan)",don_vi:"mg/L"},{ten:"BOD5",don_vi:"mg/L"},{ten:"COD",don_vi:"mg/L"},{ten:"TSS",don_vi:"mg/L"},{ten:"Amoni (theo N)",don_vi:"mg/L"},{ten:"Nitrat (theo N)",don_vi:"mg/L"},{ten:"Phosphat (theo P)",don_vi:"mg/L"},{ten:"Sắt (Fe)",don_vi:"mg/L"},{ten:"Tổng Coliform",don_vi:"MPN/100mL"}];
const _CT_NUOC_CAP=[{ten:"pH",don_vi:"-"},{ten:"Độ đục",don_vi:"NTU"},{ten:"Màu sắc",don_vi:"TCU"},{ten:"Clo dư tự do",don_vi:"mg/L"},{ten:"Asen (As)",don_vi:"mg/L"},{ten:"Amoni (theo N)",don_vi:"mg/L"},{ten:"Sắt (Fe)",don_vi:"mg/L"},{ten:"Mangan (Mn)",don_vi:"mg/L"},{ten:"Độ cứng (theo CaCO3)",don_vi:"mg/L"},{ten:"Tổng chất rắn hòa tan (TDS)",don_vi:"mg/L"},{ten:"Coliform",don_vi:"CFU/100mL"},{ten:"E. coli",don_vi:"CFU/100mL"}];
function _chiTieuMau(s,loai){s=(s||'').toUpperCase();
  if(s.includes('13-MT'))return _CT_DET_NHUOM;
  if(s.includes('QCVN 14'))return _CT_SINH_HOAT;
  if(s.includes('QCVN 40')||s.includes('11-MT')||s.includes('12-MT')||s.includes('QCVN 52')||s.includes('QCVN 60')||s.includes('QCVN 63'))return _CT_NUOC_CN;
  if(s.includes('QCVN 19')||s.includes('QCVN 20')||s.includes('QCVN 21')||s.includes('QCVN 22')||s.includes('QCVN 23')||s.includes('QCVN 51'))return _CT_KHI_CN;
  if(s.includes('QCVN 05')||s.includes('QCVN 06'))return _CT_KK_XQ;
  if(s.includes('QCVN 08'))return _CT_NUOC_MAT;
  if(s.includes('QCVN 09'))return _CT_NUOC_MAT;
  if(s.includes('QCVN 01')||s.includes('01-1'))return _CT_NUOC_CAP;
  if(loai==='KHI_THAI')return _CT_KHI_CN;
  if(loai==='NUOC_THAI'||loai==='CAP_NUOC')return _CT_NUOC_CN;
  return null;}
/* BẢNG GIÁ TRỊ GIỚI HẠN (giá trị C) — đã đối chiếu nguồn chính thức. gioi_han_ra=null khi là dải (pH). Cmax=C×Kq×Kf (trừ pH, nhiệt độ, màu, coliform). QCVN 13-MT lấy giá trị "cơ sở mới" (áp dụng cho mọi cơ sở từ 01/01/2020). */
const VAL_13MT={A:[{ten:"Nhiệt độ",don_vi:"°C",gioi_han_ra:40,ghi_chu:"cột A · Cmax=C"},{ten:"pH",don_vi:"-",gioi_han_ra:null,ghi_chu:"cột A · 6-9 · Cmax=C"},{ten:"Độ màu (pH=7)",don_vi:"Pt-Co",gioi_han_ra:50,ghi_chu:"cột A · cơ sở mới"},{ten:"BOD5",don_vi:"mg/L",gioi_han_ra:30,ghi_chu:"cột A · ×Kq×Kf"},{ten:"COD",don_vi:"mg/L",gioi_han_ra:75,ghi_chu:"cột A · cơ sở mới · ×Kq×Kf"},{ten:"TSS",don_vi:"mg/L",gioi_han_ra:50,ghi_chu:"cột A · ×Kq×Kf"},{ten:"Xyanua",don_vi:"mg/L",gioi_han_ra:0.07,ghi_chu:"cột A · ×Kq×Kf"},{ten:"Clo dư",don_vi:"mg/L",gioi_han_ra:1,ghi_chu:"cột A · ×Kq×Kf"},{ten:"Crôm VI (Cr6+)",don_vi:"mg/L",gioi_han_ra:0.05,ghi_chu:"cột A · ×Kq×Kf"},{ten:"Tổng các chất hoạt động bề mặt",don_vi:"mg/L",gioi_han_ra:5,ghi_chu:"cột A · ×Kq×Kf"}],
  B:[{ten:"Nhiệt độ",don_vi:"°C",gioi_han_ra:40,ghi_chu:"cột B · Cmax=C"},{ten:"pH",don_vi:"-",gioi_han_ra:null,ghi_chu:"cột B · 5,5-9 · Cmax=C"},{ten:"Độ màu (pH=7)",don_vi:"Pt-Co",gioi_han_ra:150,ghi_chu:"cột B · cơ sở mới"},{ten:"BOD5",don_vi:"mg/L",gioi_han_ra:50,ghi_chu:"cột B · ×Kq×Kf"},{ten:"COD",don_vi:"mg/L",gioi_han_ra:150,ghi_chu:"cột B · cơ sở mới · ×Kq×Kf"},{ten:"TSS",don_vi:"mg/L",gioi_han_ra:100,ghi_chu:"cột B · ×Kq×Kf"},{ten:"Xyanua",don_vi:"mg/L",gioi_han_ra:0.1,ghi_chu:"cột B · ×Kq×Kf"},{ten:"Clo dư",don_vi:"mg/L",gioi_han_ra:2,ghi_chu:"cột B · ×Kq×Kf"},{ten:"Crôm VI (Cr6+)",don_vi:"mg/L",gioi_han_ra:0.10,ghi_chu:"cột B · ×Kq×Kf"},{ten:"Tổng các chất hoạt động bề mặt",don_vi:"mg/L",gioi_han_ra:10,ghi_chu:"cột B · ×Kq×Kf"}]};
const VAL_40_2011={A:[{ten:"Nhiệt độ",don_vi:"°C",gioi_han_ra:40,ghi_chu:"cột A · Cmax=C"},{ten:"pH",don_vi:"-",gioi_han_ra:null,ghi_chu:"cột A · 6-9 · Cmax=C"},{ten:"BOD5",don_vi:"mg/L",gioi_han_ra:30,ghi_chu:"cột A · ×Kq×Kf"},{ten:"COD",don_vi:"mg/L",gioi_han_ra:75,ghi_chu:"cột A · ×Kq×Kf"},{ten:"TSS",don_vi:"mg/L",gioi_han_ra:50,ghi_chu:"cột A · ×Kq×Kf"},{ten:"Tổng dầu mỡ khoáng",don_vi:"mg/L",gioi_han_ra:5,ghi_chu:"cột A · ×Kq×Kf"},{ten:"Tổng Nitơ",don_vi:"mg/L",gioi_han_ra:20,ghi_chu:"cột A · ×Kq×Kf"},{ten:"Tổng Phốt pho (theo P)",don_vi:"mg/L",gioi_han_ra:4,ghi_chu:"cột A · ×Kq×Kf"}],
  B:[{ten:"Nhiệt độ",don_vi:"°C",gioi_han_ra:40,ghi_chu:"cột B · Cmax=C"},{ten:"pH",don_vi:"-",gioi_han_ra:null,ghi_chu:"cột B · 5,5-9 · Cmax=C"},{ten:"BOD5",don_vi:"mg/L",gioi_han_ra:50,ghi_chu:"cột B · ×Kq×Kf"},{ten:"COD",don_vi:"mg/L",gioi_han_ra:150,ghi_chu:"cột B · ×Kq×Kf"},{ten:"TSS",don_vi:"mg/L",gioi_han_ra:100,ghi_chu:"cột B · ×Kq×Kf"},{ten:"Tổng dầu mỡ khoáng",don_vi:"mg/L",gioi_han_ra:10,ghi_chu:"cột B · ×Kq×Kf"},{ten:"Tổng Nitơ",don_vi:"mg/L",gioi_han_ra:40,ghi_chu:"cột B · ×Kq×Kf"},{ten:"Tổng Phốt pho (theo P)",don_vi:"mg/L",gioi_han_ra:6,ghi_chu:"cột B · ×Kq×Kf"}]};
/* Trả mảng giá trị theo (tiêu chuẩn, cột) nếu đã có bảng đối chiếu; nếu chưa → null để rơi về nạp tên chỉ tiêu. */
function _mk(matrix){const out={A:[],B:[],C:[]};matrix.forEach(r=>{const[ten,dv,a,b,cc,gc]=r;const g=gc?gc+' · ':'';
  out.A.push({ten,don_vi:dv,gioi_han_ra:a,ghi_chu:g+'cột A'});out.B.push({ten,don_vi:dv,gioi_han_ra:b,ghi_chu:g+'cột B'});out.C.push({ten,don_vi:dv,gioi_han_ra:cc,ghi_chu:g+'cột C'});});return out;}
/* QCVN 40:2025/BTNMT — Bảng 1 (BOD/COD/TSS, lấy F≤2000 m³/ngày) + Bảng 2 (58 thông số). Đã bỏ Kq/Kf — giá trị là giới hạn trực tiếp. Nguồn: PDF công báo (Thông tư 06/2025/TT-BTNMT). */
const VAL_40_2025=_mk([
 ["BOD5","mg/L",40,60,80,"Bảng1 F≤2000"],["COD","mg/L",65,90,130,"Bảng1 F≤2000"],["TSS","mg/L",40,80,120,"Bảng1 F≤2000"],
 ["pH","-",null,null,null,"6-9"],["Nhiệt độ","°C",40,40,40,""],["Tổng Nitơ (T-N)","mg/L",20,40,60,""],
 ["Tổng Phốt pho (T-P)","mg/L",4.0,6.0,10,"sông/biển; hồ-ao 2/2,5/3"],["Tổng Coliform","MPN/100mL",3000,5000,5000,""],
 ["Độ màu","Pt/Co",50,100,150,""],["Asen (As)","mg/L",0.05,0.25,0.25,""],["Thủy ngân (Hg)","mg/L",0.001,0.005,0.005,""],
 ["Chì (Pb)","mg/L",0.1,0.5,0.5,""],["Cadmi (Cd)","mg/L",0.02,0.1,0.1,""],["Crom VI (Cr6+)","mg/L",0.1,0.5,0.5,""],
 ["Tổng Crom (Cr)","mg/L",0.5,2.0,2.0,""],["Đồng (Cu)","mg/L",1.0,3.0,3.0,""],["Kẽm (Zn)","mg/L",1.0,5.0,5.0,""],
 ["Niken (Ni)","mg/L",0.1,3.0,3.0,""],["Mangan (Mn)","mg/L",2.0,10,10,""],["Sắt (Fe)","mg/L",2.0,10,10,""],
 ["Bari (Ba)","mg/L",1.0,10,10,""],["Antimon (Sb)","mg/L",0.02,0.2,0.2,""],["Thiếc (Sn)","mg/L",0.5,5.0,5.0,""],
 ["Selen (Se)","mg/L",0.1,1.0,1.0,""],["Xianua (CN-)","mg/L",0.2,1.0,1.0,""],["Amoni (theo N)","mg/L",5.0,10,12,""],
 ["Phenol","mg/L",0.1,0.5,0.5,""],["Tổng Phenol","mg/L",1.0,3.0,3.0,""],["Dầu mỡ khoáng","mg/L",1.0,5.0,5.0,""],
 ["Dầu mỡ động thực vật","mg/L",5.0,30,30,""],["Sunfua (S2-)","mg/L",0.2,0.5,1.0,""],["Florua (F-)","mg/L",3.0,15,15,""],
 ["Clorua (Cl-)","mg/L",500,1000,1000,""],["Clo dư","mg/L",1.0,2.0,2.0,""],
 ["Tổng HCBVTV Clo hữu cơ","mg/L",0.05,0.1,0.1,""],["Tổng HCBVTV Photpho hữu cơ","mg/L",0.3,1.0,1.0,""],
 ["PCB","mg/L",0.003,0.003,0.003,""],["Dioxin/Furan","pgTEQ/L",10,10,10,""],["AOX","mg/L",7.5,15,15,""],
 ["Chất HĐBM anion","mg/L",3.0,5.0,5.0,""],["Pentachlorophenol","mg/L",0.001,0.01,0.01,""],
 ["Trichloroethylene","mg/L",0.06,0.3,0.3,""],["Tetrachloroethylene","mg/L",0.04,0.1,0.1,""],
 ["Benzene","mg/L",0.01,0.1,0.1,""],["Methylene chloride","mg/L",0.02,0.2,0.2,""],
 ["Carbon tetrachloride","mg/L",0.004,0.04,0.04,""],["1,1-dichloroethylene","mg/L",0.05,0.3,0.3,""],
 ["1,2-dichloroethane","mg/L",0.03,0.3,0.3,""],["Chloroform","mg/L",0.3,0.8,0.8,""],["1,4-Dioxane","mg/L",0.05,4.0,4.0,""],
 ["DEHP","mg/L",0.02,0.2,0.2,""],["Vinyl chloride","mg/L",0.01,0.5,0.5,""],["Acrylonitrile","mg/L",0.01,0.2,0.2,""],
 ["Bromoform","mg/L",0.1,0.3,0.3,""],["Naphthalene","mg/L",0.05,0.5,0.5,""],["Formaldehyde","mg/L",1.0,5.0,5.0,""],
 ["Epichlorohydrin","mg/L",0.03,0.3,0.3,""],["Toluene","mg/L",0.7,7.0,7.0,""],["Xylene","mg/L",0.5,5.0,5.0,""],
 ["Perchlorate","mg/L",0.03,0.3,0.3,""],["Acrylamide","mg/L",0.015,0.04,0.04,""],["Styrene","mg/L",0.02,0.2,0.2,""],
 ["Bis(2-ethylhexyl) adipate","mg/L",0.2,2.0,2.0,""],["Sunfit (SO3 2-)","mg/L",5.0,10,15,""]]);
/* QCVN 19:2024/BTNMT — khí thải. Giá trị theo TỪNG LOẠI THIẾT BỊ; đây là hàng "Các thiết bị xả thải khác" (mặc định chung), kèm hiệu chỉnh ôxy tham chiếu riêng. Bụi & kim loại (Bảng 2 thể hạt) chưa đối chiếu được — để trống. Nguồn: PDF công báo Bộ TN&MT. */
const VAL_19_2024=_mk([
 ["Amoniac (NH3)","mg/Nm³",15,20,25,"thiết bị khác"],["Cacbon monoxit (CO)","mg/Nm³",300,400,450,"thiết bị khác"],
 ["Axit clohydric (HCl)","mg/Nm³",10,15,20,"thiết bị khác"],["Lưu huỳnh đioxit (SO2)","mg/Nm³",200,300,350,"thiết bị khác"],
 ["Nitơ oxit (NOx theo NO2)","mg/Nm³",250,400,500,"thiết bị khác"],["Hydro sunphua (H2S)","mg/Nm³",6,7,8,"thiết bị khác"],
 ["Bụi tổng (PM)","mg/Nm³",null,null,null,"Bảng 2 thể hạt — cần đối chiếu giá trị"]]);
/* QCVN 19:2024 — giá trị theo TỪNG LOẠI THIẾT BỊ (Bảng 1 thể khí). Số trong () của QCVN là % ôxy tham chiếu — giá trị đo phải hiệu chỉnh về mức O₂ref này. Nguồn: PDF công báo Bộ TN&MT. */
const DA_TB19={KHAC:"Thiết bị xả thải khác (chung)",LH_RAN_NHO:"Lò hơi — nhiên liệu rắn (<20 t/h)",LH_RAN_LON:"Lò hơi — nhiên liệu rắn (≥20 t/h)",LH_SK:"Lò hơi — nhiên liệu sinh khối",LH_LONG_NHO:"Lò hơi — nhiên liệu lỏng (<20 t/h)",LH_LONG_LON:"Lò hơi — nhiên liệu lỏng (≥20 t/h)",LH_KHI:"Lò hơi — nhiên liệu khí",LDOT_LON:"Lò đốt chất thải (≥2 t/h)",LDOT_NHO:"Lò đốt chất thải (<2 t/h)"};
const _bui=["Bụi tổng (PM)","mg/Nm³",null,null,null,"Bảng 2 thể hạt — cần đối chiếu"];
const VAL_19_2024_TB={
 KHAC:VAL_19_2024,
 LH_RAN_NHO:_mk([["Cacbon monoxit (CO)","mg/Nm³",300,400,450,"lò hơi rắn <20t/h · O₂ref 6%"],["Lưu huỳnh đioxit (SO2)","mg/Nm³",250,350,400,"lò hơi rắn <20t/h · O₂ref 6%"],["Nitơ oxit (NOx theo NO2)","mg/Nm³",250,400,450,"lò hơi rắn <20t/h · O₂ref 6%"],_bui]),
 LH_RAN_LON:_mk([["Cacbon monoxit (CO)","mg/Nm³",250,350,400,"lò hơi rắn ≥20t/h · O₂ref 6%"],["Lưu huỳnh đioxit (SO2)","mg/Nm³",200,300,350,"lò hơi rắn ≥20t/h · O₂ref 6%"],["Nitơ oxit (NOx theo NO2)","mg/Nm³",200,300,350,"lò hơi rắn ≥20t/h · O₂ref 6%"],_bui]),
 LH_SK:_mk([["Cacbon monoxit (CO)","mg/Nm³",200,300,350,"lò hơi sinh khối · O₂ref 6%"],["Lưu huỳnh đioxit (SO2)","mg/Nm³",130,200,250,"lò hơi sinh khối · O₂ref 6%"],["Nitơ oxit (NOx theo NO2)","mg/Nm³",150,250,300,"lò hơi sinh khối · O₂ref 6%"],_bui]),
 LH_LONG_NHO:_mk([["Cacbon monoxit (CO)","mg/Nm³",250,350,400,"lò hơi lỏng <20t/h · O₂ref 4%"],["Lưu huỳnh đioxit (SO2)","mg/Nm³",250,350,400,"lò hơi lỏng <20t/h · O₂ref 4%"],["Nitơ oxit (NOx theo NO2)","mg/Nm³",250,400,450,"lò hơi lỏng <20t/h · O₂ref 4%"],_bui]),
 LH_LONG_LON:_mk([["Cacbon monoxit (CO)","mg/Nm³",200,300,350,"lò hơi lỏng ≥20t/h · O₂ref 4%"],["Lưu huỳnh đioxit (SO2)","mg/Nm³",200,300,350,"lò hơi lỏng ≥20t/h · O₂ref 4%"],["Nitơ oxit (NOx theo NO2)","mg/Nm³",200,300,350,"lò hơi lỏng ≥20t/h · O₂ref 4%"],_bui]),
 LH_KHI:_mk([["Cacbon monoxit (CO)","mg/Nm³",80,100,120,"lò hơi khí · O₂ref 4%"],["Lưu huỳnh đioxit (SO2)","mg/Nm³",90,120,150,"lò hơi khí · O₂ref 4%"],["Nitơ oxit (NOx theo NO2)","mg/Nm³",70,120,150,"lò hơi khí · O₂ref 4%"],_bui]),
 LDOT_LON:_mk([["Cacbon monoxit (CO)","mg/Nm³",120,180,200,"lò đốt CT ≥2t/h · O₂ref 12%"],["Lưu huỳnh đioxit (SO2)","mg/Nm³",80,100,150,"lò đốt CT ≥2t/h · O₂ref 12%"],["Nitơ oxit (NOx theo NO2)","mg/Nm³",180,250,300,"lò đốt CT ≥2t/h · O₂ref 12%"],["Axit clohydric (HCl)","mg/Nm³",20,25,30,"lò đốt CT ≥2t/h · O₂ref 12%"],["Amoniac (NH3)","mg/Nm³",15,20,25,"lò đốt CT ≥2t/h · O₂ref 12%"],["Hydro sunphua (H2S)","mg/Nm³",3,3,4,"lò đốt CT ≥2t/h · O₂ref 12%"],_bui,["Dioxin/Furan","ngTEQ/Nm³",null,null,null,"Bảng 2 — cần đối chiếu"]]),
 LDOT_NHO:_mk([["Cacbon monoxit (CO)","mg/Nm³",150,200,250,"lò đốt CT <2t/h · O₂ref 12%"],["Lưu huỳnh đioxit (SO2)","mg/Nm³",100,120,180,"lò đốt CT <2t/h · O₂ref 12%"],["Nitơ oxit (NOx theo NO2)","mg/Nm³",200,300,350,"lò đốt CT <2t/h · O₂ref 12%"],["Axit clohydric (HCl)","mg/Nm³",25,30,35,"lò đốt CT <2t/h · O₂ref 12%"],["Amoniac (NH3)","mg/Nm³",15,20,25,"lò đốt CT <2t/h · O₂ref 12%"],["Hydro sunphua (H2S)","mg/Nm³",3,4,5,"lò đốt CT <2t/h · O₂ref 12%"],_bui,["Dioxin/Furan","ngTEQ/Nm³",null,null,null,"Bảng 2 — cần đối chiếu"]])
};
function _giaTri19(equip,cot){const t=VAL_19_2024_TB[equip]||VAL_19_2024_TB.KHAC;return (t[cot]||t.B).map(x=>Object.assign({},x));}
/* QCVN 01-1:2018/BYT — NƯỚC CẤP (nước sạch sinh hoạt, đạt mức ăn uống). Thay thế QCVN 01:2009 (ăn uống) + QCVN 02:2009 (sinh hoạt). Giới hạn TỐI ĐA đơn trị (không cột A/B/C). Nạp Nhóm A (bắt buộc) + vô cơ Nhóm B. Nguồn: PDF công báo (TT 41/2018/TT-BYT). */
const VAL_0112018=[
 {ten:"Coliform",don_vi:"CFU/100mL",gioi_han_ra:3,ghi_chu:"Nhóm A · <3"},
 {ten:"E.coli / Coliform chịu nhiệt",don_vi:"CFU/100mL",gioi_han_ra:1,ghi_chu:"Nhóm A · <1"},
 {ten:"Asen (As)",don_vi:"mg/L",gioi_han_ra:0.01,ghi_chu:"Nhóm A · (*) nước ngầm"},
 {ten:"Clo dư tự do",don_vi:"mg/L",gioi_han_ra:null,ghi_chu:"Nhóm A · khoảng 0,2-1,0 (nếu khử trùng Clo)"},
 {ten:"Độ đục",don_vi:"NTU",gioi_han_ra:2,ghi_chu:"Nhóm A"},
 {ten:"Màu sắc",don_vi:"TCU",gioi_han_ra:15,ghi_chu:"Nhóm A"},
 {ten:"Mùi, vị",don_vi:"-",gioi_han_ra:null,ghi_chu:"Nhóm A · không có mùi, vị lạ"},
 {ten:"pH",don_vi:"-",gioi_han_ra:null,ghi_chu:"Nhóm A · khoảng 6,0-8,5"},
 {ten:"Tụ cầu vàng (Staphylococcus aureus)",don_vi:"CFU/100mL",gioi_han_ra:1,ghi_chu:"Nhóm B · <1"},
 {ten:"Trực khuẩn mủ xanh (Ps. aeruginosa)",don_vi:"CFU/100mL",gioi_han_ra:1,ghi_chu:"Nhóm B · <1"},
 {ten:"Amoni (NH3 & NH4+ theo N)",don_vi:"mg/L",gioi_han_ra:0.3,ghi_chu:"Nhóm B"},
 {ten:"Antimon (Sb)",don_vi:"mg/L",gioi_han_ra:0.02,ghi_chu:"Nhóm B"},
 {ten:"Bari (Ba)",don_vi:"mg/L",gioi_han_ra:0.7,ghi_chu:"Nhóm B"},
 {ten:"Bor (Borat & axit Boric, B)",don_vi:"mg/L",gioi_han_ra:0.3,ghi_chu:"Nhóm B"},
 {ten:"Cadmi (Cd)",don_vi:"mg/L",gioi_han_ra:0.003,ghi_chu:"Nhóm B"},
 {ten:"Chì (Pb)",don_vi:"mg/L",gioi_han_ra:0.01,ghi_chu:"Nhóm B"},
 {ten:"Chỉ số pecmanganat",don_vi:"mg/L",gioi_han_ra:2,ghi_chu:"Nhóm B"},
 {ten:"Clorua (Cl-)",don_vi:"mg/L",gioi_han_ra:250,ghi_chu:"Nhóm B · 300 vùng ven biển/hải đảo"},
 {ten:"Crom (Cr)",don_vi:"mg/L",gioi_han_ra:0.05,ghi_chu:"Nhóm B"},
 {ten:"Đồng (Cu)",don_vi:"mg/L",gioi_han_ra:1,ghi_chu:"Nhóm B"},
 {ten:"Độ cứng (theo CaCO3)",don_vi:"mg/L",gioi_han_ra:300,ghi_chu:"Nhóm B"},
 {ten:"Florua (F)",don_vi:"mg/L",gioi_han_ra:1.5,ghi_chu:"Nhóm B"},
 {ten:"Kẽm (Zn)",don_vi:"mg/L",gioi_han_ra:2,ghi_chu:"Nhóm B"},
 {ten:"Mangan (Mn)",don_vi:"mg/L",gioi_han_ra:0.1,ghi_chu:"Nhóm B"},
 {ten:"Natri (Na)",don_vi:"mg/L",gioi_han_ra:200,ghi_chu:"Nhóm B"},
 {ten:"Nhôm (Al)",don_vi:"mg/L",gioi_han_ra:0.2,ghi_chu:"Nhóm B"},
 {ten:"Nickel (Ni)",don_vi:"mg/L",gioi_han_ra:0.07,ghi_chu:"Nhóm B"},
 {ten:"Nitrat (NO3- theo N)",don_vi:"mg/L",gioi_han_ra:2,ghi_chu:"Nhóm B"},
 {ten:"Nitrit (NO2- theo N)",don_vi:"mg/L",gioi_han_ra:0.05,ghi_chu:"Nhóm B"},
 {ten:"Sắt (Fe)",don_vi:"mg/L",gioi_han_ra:0.3,ghi_chu:"Nhóm B"},
 {ten:"Selen (Se)",don_vi:"mg/L",gioi_han_ra:0.01,ghi_chu:"Nhóm B"},
 {ten:"Sunphat (SO4)",don_vi:"mg/L",gioi_han_ra:250,ghi_chu:"Nhóm B"},
 {ten:"Sunfua",don_vi:"mg/L",gioi_han_ra:0.05,ghi_chu:"Nhóm B"},
 {ten:"Thủy ngân (Hg)",don_vi:"mg/L",gioi_han_ra:0.001,ghi_chu:"Nhóm B"},
 {ten:"Tổng chất rắn hòa tan (TDS)",don_vi:"mg/L",gioi_han_ra:1000,ghi_chu:"Nhóm B"},
 {ten:"Xyanua (CN-)",don_vi:"mg/L",gioi_han_ra:0.05,ghi_chu:"Nhóm B"}
];
/* ====== CHUẨN THEO NGÀNH (ngoài QCVN nhà nước) — giá trị lấy từ nguồn gốc ====== */
const DA_NGANH={ZDHC:"Dệt nhuộm — ZDHC (nước thải)",THUCPHAM:"Thực phẩm/đồ uống — nước sạch (QCVN 01-1:2018)",NDCHAI:"Nước đóng chai (QCVN 6-1:2010/BYT)",DUOC_PW:"Dược — Nước tinh khiết PW",DUOC_WFI:"Dược — Nước pha tiêm WFI",LAB_ISO3696:"Phòng thí nghiệm — ISO 3696",BANDAN_UPW:"Bán dẫn — UPW (ASTM D5127/SEMI)",NOIHOI_LP:"Nồi hơi — nước cấp áp thấp (ABMA/ASME)",NLAMAT:"Nước làm mát tuần hoàn (LSI/ASHRAE)",THUYSAN_TOM:"Thủy sản — nước nuôi tôm (QCVN 02-19)",THUYSAN_CA:"Thủy sản — nước nuôi cá tra (QCVN 02-20)"};
const _ngLoai={NUOC_THAI:["ZDHC"],CAP_NUOC:["THUCPHAM","NDCHAI","DUOC_PW","DUOC_WFI","LAB_ISO3696","BANDAN_UPW","NOIHOI_LP","NLAMAT","THUYSAN_TOM","THUYSAN_CA"]};
const VAL_NGANH={
 /* ZDHC Wastewater Guidelines V2.1 (dệt) — ĐẦY ĐỦ 3 mức: cột A=Aspirational, B=Progressive, C=Foundational. Nguồn: PDF V2.1 Bảng 2 (kim loại) + Bảng 3 (thông số quy ước & anion). */
 ZDHC:_mk([
  ["pH","-",null,null,null,"6-9 (mọi mức)"],
  ["Nhiệt độ (ΔT)","°C",5,10,15,"Δ+ so với nguồn nhận"],
  ["COD","mg/L",40,80,150,""],["BOD5","mg/L",8,15,30,""],["TSS","mg/L",5,15,50,""],
  ["Tổng Nitơ","mg/L",5,10,20,""],["Amoni (theo N)","mg/L",0.5,1,10,""],["Tổng Phốt pho","mg/L",0.1,0.5,3,""],
  ["AOX","mg/L",0.1,0.5,3,""],["Dầu mỡ khoáng","mg/L",0.5,2,10,""],["Tổng Phenol","mg/L",0.001,0.01,0.5,""],
  ["Sunfua (S2-)","mg/L",0.01,0.05,0.5,""],["Sunfit (SO3)","mg/L",0.2,0.5,2,""],["Xianua tổng (CN-)","mg/L",0.05,0.1,0.2,""],
  ["E.coli","MPN/100mL",126,126,126,"đơn trị mọi mức"],
  ["Độ màu 436nm","m⁻¹",2,5,7,"VIS-436"],["Độ màu 525nm","m⁻¹",1,3,5,"VIS-525"],["Độ màu 620nm","m⁻¹",1,2,3,"VIS-620"],
  ["Asen (As)","mg/L",0.005,0.01,0.05,"kim loại"],["Cadimi (Cd)","mg/L",0.01,0.05,0.1,"kim loại"],
  ["Crom VI (Cr6+)","mg/L",0.001,0.005,0.05,"kim loại"],["Tổng Crom (Cr)","mg/L",0.05,0.1,0.2,"kim loại"],
  ["Đồng (Cu)","mg/L",0.25,0.5,1,"kim loại"],["Chì (Pb)","mg/L",0.01,0.05,0.1,"kim loại"],
  ["Niken (Ni)","mg/L",0.05,0.1,0.2,"kim loại"],["Kẽm (Zn)","mg/L",0.5,1,5,"kim loại"],
  ["Thủy ngân (Hg)","mg/L",0.001,0.005,0.01,"kim loại"],["Antimon (Sb)","mg/L",0.01,0.05,0.1,"kim loại; polyester chỉ b/c"],
  ["Coban (Co)","mg/L",0.01,0.02,0.05,"kim loại"],["Bạc (Ag)","mg/L",0.005,0.05,0.1,"kim loại"],
  ["TDS","mg/L",null,null,null,"Sample & Report"],["Sunfat (SO4)","mg/L",null,null,null,"Sample & Report"],
  ["Clorua (Cl-)","mg/L",null,null,null,"Sample & Report"],["Oxy hòa tan (DO)","mg/L",null,null,null,"Sample & Report"]]),
 /* Thực phẩm/đồ uống: nước chế biến phải đạt nước sạch ăn uống — dùng QCVN 01-1:2018/BYT. */
 THUCPHAM:VAL_0112018,
 /* Nước đóng chai (QCVN 6-1:2010/BYT, TT 34/2010) — Phụ lục A hóa học + vi sinh. */
 NDCHAI:[
  {ten:"pH",don_vi:"-",gioi_han_ra:null,ghi_chu:"6,5-8,5"},
  {ten:"Độ đục",don_vi:"NTU",gioi_han_ra:5,ghi_chu:"≤5"},
  {ten:"Antimon (Sb)",don_vi:"mg/L",gioi_han_ra:0.02,ghi_chu:"Phụ lục A"},
  {ten:"Asen (As)",don_vi:"mg/L",gioi_han_ra:0.01,ghi_chu:""},
  {ten:"Bari (Ba)",don_vi:"mg/L",gioi_han_ra:0.7,ghi_chu:""},
  {ten:"Bor (B)",don_vi:"mg/L",gioi_han_ra:0.5,ghi_chu:""},
  {ten:"Bromat (BrO3)",don_vi:"mg/L",gioi_han_ra:0.01,ghi_chu:""},
  {ten:"Cadimi (Cd)",don_vi:"mg/L",gioi_han_ra:0.003,ghi_chu:""},
  {ten:"Clo dư",don_vi:"mg/L",gioi_han_ra:5,ghi_chu:""},
  {ten:"Clorat (ClO3)",don_vi:"mg/L",gioi_han_ra:0.7,ghi_chu:""},
  {ten:"Clorit (ClO2)",don_vi:"mg/L",gioi_han_ra:0.7,ghi_chu:""},
  {ten:"Crom (Cr)",don_vi:"mg/L",gioi_han_ra:0.05,ghi_chu:""},
  {ten:"Đồng (Cu)",don_vi:"mg/L",gioi_han_ra:2,ghi_chu:""},
  {ten:"Xianua (CN)",don_vi:"mg/L",gioi_han_ra:0.07,ghi_chu:""},
  {ten:"Florua (F)",don_vi:"mg/L",gioi_han_ra:1.5,ghi_chu:""},
  {ten:"Chì (Pb)",don_vi:"mg/L",gioi_han_ra:0.01,ghi_chu:""},
  {ten:"Mangan (Mn)",don_vi:"mg/L",gioi_han_ra:0.4,ghi_chu:""},
  {ten:"Thủy ngân (Hg)",don_vi:"mg/L",gioi_han_ra:0.006,ghi_chu:""},
  {ten:"Molybden (Mo)",don_vi:"mg/L",gioi_han_ra:0.07,ghi_chu:""},
  {ten:"Nickel (Ni)",don_vi:"mg/L",gioi_han_ra:0.07,ghi_chu:""},
  {ten:"Nitrat (NO3)",don_vi:"mg/L",gioi_han_ra:50,ghi_chu:"NO3/50 + NO2/3 < 1"},
  {ten:"Nitrit (NO2)",don_vi:"mg/L",gioi_han_ra:3,ghi_chu:"NO3/50 + NO2/3 < 1"},
  {ten:"Selen (Se)",don_vi:"mg/L",gioi_han_ra:0.01,ghi_chu:""},
  {ten:"Hoạt độ phóng xạ α",don_vi:"Bq/L",gioi_han_ra:0.5,ghi_chu:"loại B"},
  {ten:"Hoạt độ phóng xạ β",don_vi:"Bq/L",gioi_han_ra:1,ghi_chu:"loại B"},
  {ten:"E.coli / coliform chịu nhiệt",don_vi:"/250mL",gioi_han_ra:0,ghi_chu:"không phát hiện"},
  {ten:"Coliform tổng số",don_vi:"/250mL",gioi_han_ra:0,ghi_chu:"không phát hiện (KT lần 2 nếu 1-2)"},
  {ten:"Streptococci faecal",don_vi:"/250mL",gioi_han_ra:0,ghi_chu:"không phát hiện"},
  {ten:"Pseudomonas aeruginosa",don_vi:"/250mL",gioi_han_ra:0,ghi_chu:"không phát hiện"},
  {ten:"Bào tử kị khí khử sulfit",don_vi:"/50mL",gioi_han_ra:0,ghi_chu:"không phát hiện"}],
 /* Nước làm mát tuần hoàn (hệ hở) — hướng dẫn ASHRAE 189.1 / tháp giải nhiệt. LSI là CHỈ SỐ, không phải giới hạn trên. */
 NLAMAT:[
  {ten:"Chỉ số Langelier (LSI)",don_vi:"-",gioi_han_ra:null,ghi_chu:"khuyến nghị 0 đến +1,0; CHỈ SỐ tính từ pH/Ca/kiềm/TDS/t°"},
  {ten:"pH",don_vi:"-",gioi_han_ra:null,ghi_chu:"6,5-9,0"},
  {ten:"Clorua (Cl-)",don_vi:"mg/L",gioi_han_ra:300,ghi_chu:"≤300 thép thường/mạ kẽm; đến 900 nếu KL chịu được"},
  {ten:"Độ dẫn điện",don_vi:"µS/cm",gioi_han_ra:3000,ghi_chu:"≤2500-3000 (tùy số chu kỳ cô đặc COC)"},
  {ten:"TDS",don_vi:"mg/L",gioi_han_ra:2050,ghi_chu:"ASHRAE tối đa; ≈60-70% độ dẫn"},
  {ten:"Độ cứng tổng (CaCO3)",don_vi:"mg/L",gioi_han_ra:500,ghi_chu:"≤500 (Ca-hardness ≤600 ASHRAE)"},
  {ten:"Độ kiềm tổng (CaCO3)",don_vi:"mg/L",gioi_han_ra:null,ghi_chu:"100-500 (≤600 ASHRAE)"},
  {ten:"Silica (SiO2)",don_vi:"mg/L",gioi_han_ra:150,ghi_chu:"≤150 (chống cáu silicat)"},
  {ten:"Sunfat (SO4)",don_vi:"mg/L",gioi_han_ra:250,ghi_chu:"250 ASHRAE; đến 800 tùy Ca"},
  {ten:"Đồng (Cu)",don_vi:"mg/L",gioi_han_ra:0.1,ghi_chu:"≤0,1"},
  {ten:"Nitrat (NO3)",don_vi:"mg/L",gioi_han_ra:300,ghi_chu:"≤300 (dưỡng chất vi khuẩn)"},
  {ten:"Clo dư tự do",don_vi:"mg/L",gioi_han_ra:0.4,ghi_chu:"≤0,4 liên tục; ≤1 sốc"},
  {ten:"Tổng vi khuẩn",don_vi:"CFU/mL",gioi_han_ra:100000,ghi_chu:"<100.000"},
  {ten:"Legionella",don_vi:"CFU/mL",gioi_han_ra:100,ghi_chu:"<100 (kiểm soát nghiêm)"},
  {ten:"Nhiệt độ",don_vi:"°C",gioi_han_ra:null,ghi_chu:"≤51,7 tháp tiêu chuẩn"}],
 /* Nồi hơi — nước cấp áp thấp (0-300 psig) theo ABMA/ASME. */
 NOIHOI_LP:[
  {ten:"Độ cứng tổng (CaCO3)",don_vi:"mg/L",gioi_han_ra:0.3,ghi_chu:"≈0 (khử mềm/khử khoáng) ≤0,3"},
  {ten:"Oxy hòa tan (DO)",don_vi:"mg/L",gioi_han_ra:0.007,ghi_chu:"sau khử khí+scavenger; ≤0,04 trước"},
  {ten:"pH",don_vi:"-",gioi_han_ra:null,ghi_chu:"8,3-10,5 (ABMA/ASME)"},
  {ten:"Sắt (Fe)",don_vi:"mg/L",gioi_han_ra:0.1,ghi_chu:"nước cấp"},
  {ten:"Đồng (Cu)",don_vi:"mg/L",gioi_han_ra:0.05,ghi_chu:"nước cấp"},
  {ten:"TOC không bay hơi",don_vi:"mg/L",gioi_han_ra:1,ghi_chu:"nước cấp"},
  {ten:"Dầu mỡ",don_vi:"mg/L",gioi_han_ra:1,ghi_chu:"nước cấp"},
  {ten:"Silica (SiO2) nước lò",don_vi:"mg/L",gioi_han_ra:150,ghi_chu:"nước trong lò 0-300 psig; siết mạnh khi áp tăng"},
  {ten:"TDS nước lò",don_vi:"mg/L",gioi_han_ra:3500,ghi_chu:"nước trong lò 0-300 psig (700-3500)"}],
 /* Thủy sản — nước nuôi tôm nước lợ (QCVN 02-19:2014/BNNPTNT). */
 THUYSAN_TOM:[
  {ten:"Oxy hòa tan (DO)",don_vi:"mg/L",gioi_han_ra:3.5,ghi_chu:"tối thiểu ≥3,5"},
  {ten:"pH",don_vi:"-",gioi_han_ra:null,ghi_chu:"7-9"},
  {ten:"Độ mặn",don_vi:"‰",gioi_han_ra:null,ghi_chu:"5-35‰"},
  {ten:"Độ trong",don_vi:"cm",gioi_han_ra:null,ghi_chu:"20-50 cm"},
  {ten:"Nhiệt độ",don_vi:"°C",gioi_han_ra:null,ghi_chu:"18-33°C"},
  {ten:"NH3",don_vi:"mg/L",gioi_han_ra:0.3,ghi_chu:"<0,3 (tối ưu 0,1)"},
  {ten:"H2S",don_vi:"mg/L",gioi_han_ra:0.05,ghi_chu:"<0,05"}],
 /* Thủy sản — nước nuôi cá tra trong ao (QCVN 02-20:2014/BNNPTNT). */
 THUYSAN_CA:[
  {ten:"Oxy hòa tan (DO)",don_vi:"mg/L",gioi_han_ra:2.0,ghi_chu:"tối thiểu ≥2,0"},
  {ten:"pH",don_vi:"-",gioi_han_ra:null,ghi_chu:"7-9"},
  {ten:"Độ kiềm (CaCO3)",don_vi:"mg/L",gioi_han_ra:null,ghi_chu:"60-180"},
  {ten:"Nhiệt độ",don_vi:"°C",gioi_han_ra:null,ghi_chu:"25-32°C"},
  {ten:"NH3",don_vi:"mg/L",gioi_han_ra:0.3,ghi_chu:"<0,3"},
  {ten:"H2S",don_vi:"mg/L",gioi_han_ra:0.05,ghi_chu:"<0,05"}],
 /* Dược điển — Nước tinh khiết (Ph.Eur. 0008 / USP <645>; DĐVN theo Ph.Eur.). */
 DUOC_PW:[
  {ten:"Độ dẫn điện",don_vi:"µS/cm",gioi_han_ra:1.3,ghi_chu:"≤1,3 ở 25°C (≤1,1 ở 20°C)"},
  {ten:"TOC (cacbon hữu cơ tổng)",don_vi:"mg/L",gioi_han_ra:0.5,ghi_chu:"≤0,5 (=500 ppb)"},
  {ten:"Nitrat (NO3)",don_vi:"mg/L",gioi_han_ra:0.2,ghi_chu:"Ph.Eur. ≤0,2 ppm"},
  {ten:"Vi sinh vật hiếu khí",don_vi:"CFU/mL",gioi_han_ra:100,ghi_chu:"giới hạn hành động ≤100"}],
 /* Dược điển — Nước pha tiêm WFI (Ph.Eur. 0169 / USP). */
 DUOC_WFI:[
  {ten:"Độ dẫn điện",don_vi:"µS/cm",gioi_han_ra:1.3,ghi_chu:"≤1,3 ở 25°C (khoảng 0,6-1,5)"},
  {ten:"TOC",don_vi:"mg/L",gioi_han_ra:0.5,ghi_chu:"≤0,5 (=500 ppb)"},
  {ten:"Nội độc tố vi khuẩn",don_vi:"EU/mL",gioi_han_ra:0.25,ghi_chu:"≤0,25 EU(IU)/mL"},
  {ten:"Vi sinh vật hiếu khí",don_vi:"CFU/100mL",gioi_han_ra:10,ghi_chu:"≤10 CFU/100mL"},
  {ten:"Nitrat (NO3)",don_vi:"mg/L",gioi_han_ra:0.2,ghi_chu:"≤0,2 ppm (bỏ nếu đạt độ dẫn WFI)"}],
 /* ISO 3696:1987 — nước phòng thí nghiệm. Grade 1/2/3 → cột A/B/C. */
 LAB_ISO3696:_mk([
  ["Độ dẫn điện","µS/cm",0.1,1.0,5.0,"ISO3696 G1/G2/G3 ở 25°C"],
  ["pH","-",null,null,null,"chỉ Grade 3: 5,0-7,5"],
  ["Chất oxy hóa (theo O2)","mg/L",null,0.08,0.4,"G1 không quy định"],
  ["Độ hấp thụ 254nm (1cm)","-",0.001,0.01,null,"G3 không quy định"],
  ["Cặn bay hơi 110°C","mg/kg",null,1,2,"G1 không quy định"],
  ["Silica (SiO2)","mg/L",0.01,0.02,null,"G3 không quy định"]]),
 /* Bán dẫn — UPW (ASTM D5127 Type E-1 / SEMI F63). Điện trở suất là giá trị TỐI THIỂU. */
 BANDAN_UPW:[
  {ten:"Điện trở suất",don_vi:"MΩ·cm",gioi_han_ra:18.2,ghi_chu:"≥18,2 ở 25°C (giá trị tối thiểu)"},
  {ten:"Độ dẫn điện",don_vi:"µS/cm",gioi_han_ra:0.055,ghi_chu:"≈0,055 (nghịch đảo 18,2 MΩ·cm)"},
  {ten:"TOC",don_vi:"ppb",gioi_han_ra:1,ghi_chu:"≤1-2 ppb (E-1.2:≤1; E-1.1:≤2)"},
  {ten:"Silica tổng",don_vi:"ppb",gioi_han_ra:3,ghi_chu:"E-1; tiên tiến SEMI F63 <0,3 ppb"},
  {ten:"Vi khuẩn",don_vi:"CFU/100mL",gioi_han_ra:1,ghi_chu:"E-1.2:≤1; E-1.1:≤3"},
  {ten:"Hạt >0,05µm",don_vi:"hạt/mL",gioi_han_ra:1,ghi_chu:"<1/mL"}]
};
function _ngOptions(loai){const ks=_ngLoai[loai]||[];return '<option value="">(Không chọn ngành)</option>'+ks.map(k=>`<option value="${k}">${DA_NGANH[k]}</option>`).join('');}
function _canhBaoNganh(k){
  if(k==="ZDHC")return "\nLưu ý ZDHC (dệt nhuộm): cột A=Aspirational (nghiêm nhất) · B=Progressive · C=Foundational (bắt buộc tối thiểu). Chuẩn ngành tự nguyện, KHÔNG thay QCVN. E.coli 126 MPN/100mL & độ màu 3 bước sóng là đơn trị mọi mức. MRSL hóa chất hạn chế (hàng trăm chất) chưa nạp. TDS/sunfat/clorua/DO: Sample & Report.";
  if(k==="THUCPHAM")return "\nLưu ý: nước chế biến thực phẩm/đồ uống phải đạt nước sạch ăn uống — nạp theo QCVN 01-1:2018/BYT (đơn trị). Nước đóng chai/đóng bình theo QCVN 6-1:2010/BYT (chọn riêng).";
  if(k==="NDCHAI")return "\nLưu ý nước đóng chai: theo QCVN 6-1:2010/BYT (TT 34/2010, Phụ lục A). Vi sinh yêu cầu KHÔNG phát hiện trong 250mL. Nitrat+nitrit ràng buộc: NO3/50 + NO2/3 < 1. Dư lượng thuốc BVTV (Phụ lục B) chưa nạp.";
  if(k==="NLAMAT")return "\nLưu ý nước làm mát tuần hoàn: theo hướng dẫn ASHRAE 189.1/tháp giải nhiệt (KHÔNG phải QCVN). LSI là CHỈ SỐ tính toán (khuyến nghị 0 đến +1,0), không phải giới hạn trên. Nhiều giá trị phụ thuộc kim loại hệ thống & số chu kỳ cô đặc (COC) — điều chỉnh theo phân tích nước thực tế.";
  if(k==="DUOC_PW"||k==="DUOC_WFI")return "\nLưu ý Dược: giá trị theo Ph.Eur./USP (DĐVN tương đương). Độ dẫn điện là phép thử nhiều mức theo nhiệt độ; đây là ngưỡng ở 25°C. Cần thẩm định GMP đầy đủ.";
  if(k==="LAB_ISO3696")return "\nLưu ý ISO 3696: Grade 1/2/3 ứng với cột A/B/C. Một số thông số không quy định ở Grade tương ứng (để trống). Chỉ áp dụng cho phân tích vô cơ.";
  if(k==="BANDAN_UPW")return "\nLưu ý UPW bán dẫn: điện trở suất là giá trị TỐI THIỂU (≥18,2), không phải giới hạn trên. Các giá trị ppb/ppt cần thiết bị đo chuyên dụng (TOC online, đếm hạt).";
  if(k==="NOIHOI_LP")return "\nLưu ý nồi hơi: giá trị cho nồi hơi ÁP THẤP (0-300 psig) theo ABMA/ASME. Áp suất càng cao giới hạn càng siết (silica/TDS giảm mạnh). Độ cứng yêu cầu ≈0; oxy phải khử bằng khử khí + scavenger.";
  if(k==="THUYSAN_TOM"||k==="THUYSAN_CA")return "\nLưu ý thủy sản: theo QCVN 02-19/02-20:2014/BNNPTNT (nước cấp/ao nuôi). Nhiều thông số là KHOẢNG (pH, độ mặn, độ kiềm, nhiệt độ, độ trong) hoặc TỐI THIỂU (DO) — ghi ở cột Ghi chú, không phải giới hạn trên.";
  return "";}
function _donTri(s){return (s||'').toUpperCase().includes('01-1:2018');}
function _giaTriMau(s,cot){s=(s||'').toUpperCase();cot=(cot||'B').toUpperCase();
  if(s.includes('01-1:2018'))return VAL_0112018.map(x=>Object.assign({},x));
  let t=null;
  if(s.includes('13-MT'))t=VAL_13MT;
  else if(s.includes('QCVN 40:2025'))t=VAL_40_2025;
  else if(s.includes('QCVN 40:2011'))t=VAL_40_2011;
  else if(s.includes('QCVN 19:2024'))t=VAL_19_2024;
  if(!t||!t[cot])return null;
  return t[cot].map(x=>Object.assign({},x));}
function _coBangGiaTri(s){s=(s||'').toUpperCase();return s.includes('13-MT')||s.includes('QCVN 40:2011')||s.includes('QCVN 40:2025')||s.includes('QCVN 19:2024')||s.includes('01-1:2018');}
function _canhBaoNap(s){s=(s||'').toUpperCase();
  if(s.includes('01-1:2018'))return "\nLưu ý QCVN 01-1:2018/BYT (NƯỚC CẤP — nước sạch sinh hoạt, đạt mức ăn uống; thay QCVN 01:2009 & 02:2009): giá trị là GIỚI HẠN TỐI ĐA đơn trị, không có cột A/B/C. pH (6,0-8,5), Clo dư (0,2-1,0), Mùi-vị là khoảng/định tính nên để trống số. Đây là chất lượng MỤC TIÊU của nước sau xử lý. Đã nạp Nhóm A + vô cơ Nhóm B; nhóm hữu cơ/HCBVTV/phóng xạ (TT 37-99) chưa nạp.";
  if(s.includes('QCVN 19:2024'))return "\nLưu ý QCVN 19:2024: giá trị theo loại thiết bị đã chọn, CÓ hiệu chỉnh ôxy tham chiếu (O₂ref ghi ở cột Ghi chú) — giá trị đo phải quy về mức O₂ref đó. Bụi & Dioxin (Bảng 2 thể hạt) chưa có giá trị, cần đối chiếu công báo.";
  if(s.includes('QCVN 40:2025'))return "\nLưu ý QCVN 40:2025: đã bỏ Kq/Kf — giá trị là giới hạn trực tiếp. BOD/COD/TSS lấy theo F≤2.000 m³/ngày; nếu dự án >2.000 m³/ngày, sửa lại 3 dòng này (BOD≤30/50/60, COD≤60/70/90, TSS≤30/60/80).";
  return "\nGiá trị nạp là C (cơ sở). Giới hạn thực Cmax = C×Kq×Kf tùy nguồn tiếp nhận & lưu lượng (trừ pH, nhiệt độ, màu). Hãy đối chiếu công báo.";}
function _bar(pct,color){pct=Math.max(0,Math.min(100,pct||0));return `<div style="background:var(--line);border-radius:6px;height:8px;overflow:hidden"><div style="width:${pct}%;height:100%;background:${color||'#0e7490'}"></div></div>`;}

async function viewDuAn(m){
  if(S.daId){ return daDetail(m); }
  m.innerHTML=head("Dự án","Quản lý dự án: thông tin · thiết kế · tiến độ · an toàn · triển khai · document · KPI · báo cáo");
  let ds; try{ ds = S.mode==="live" ? await api("/du-an") : _daDemoList(); }catch(e){m.innerHTML+=`<div class="empty" style="color:#dc2626;padding:24px">${e.detail||e.message}</div>`;return;}
  const canOp=can("du_an","THAO_TAC");
  let html="";
  if(canOp){
    html+=`<div class="panel"><div class="panel-h"><h3>Dự án mới</h3></div><div class="panel-b">
      <div class="formrow"><div class="f"><label>Mã dự án</label><input id="da_ma" placeholder="DA-2026-01"></div>
        <div class="f" style="flex:2"><label>Tên dự án</label><input id="da_ten" placeholder="Trạm XLNT 1.200 m³/ngày"></div>
        <button class="btn-sm" style="align-self:end" onclick="daTao()">Tạo dự án</button></div></div></div>`;
  }
  const rows=(ds||[]).map(d=>`<tr style="cursor:pointer" onclick="daOpen(${d.id})">
    <td><b>${d.ma||('#'+d.id)}</b></td><td>${d.ten}${d.chu_dau_tu?`<div style="font-size:11px;color:var(--muted)">${d.chu_dau_tu}</div>`:''}</td>
    <td>${d.loai_du_an?`<span class="badge b-info">${DA_LOAI[d.loai_du_an]||d.loai_du_an}</span>`:'—'}</td>
    <td>${d.cong_suat||'—'}</td>
    <td style="min-width:120px">${_bar(d.tien_do)}<div style="font-size:11px;color:var(--muted);margin-top:2px">${_num(d.tien_do||0,1)}%</div></td>
    <td><span class="badge ${d.trang_thai==='HOAN_THANH'?'b-ok':(d.trang_thai==='TAM_DUNG'?'b-tc':'b-cho')}">${DA_TT[d.trang_thai]||d.trang_thai}</span></td>
    <td class="num">${d.gia_tri_hop_dong?vnd(d.gia_tri_hop_dong):'—'}</td></tr>`).join('');
  html+=`<div class="panel"><div class="panel-h"><h3>Danh sách dự án</h3></div><div class="panel-b"><table>
    <thead><tr><th>Mã</th><th>Tên / Chủ đầu tư</th><th>Loại</th><th>Công suất</th><th>Tiến độ</th><th>Trạng thái</th><th class="num">Giá trị HĐ</th></tr></thead>
    <tbody>${rows||'<tr><td colspan="7" class="empty">Chưa có dự án. Tạo dự án mới để bắt đầu.</td></tr>'}</tbody></table></div></div>`;
  m.innerHTML+=html;
}
async function daTao(){
  const body={ma:gv('da_ma')||null,ten:gv('da_ten')};
  if(!body.ten){toast("Nhập tên dự án","err");return;}
  if(S.mode!=="live"){toast("Đã tạo (demo)","ok");return;}
  try{const d=await api("/du-an",{method:'POST',body:JSON.stringify(body)});toast("Đã tạo dự án","ok");daOpen(d.id);}catch(e){toast(e.detail||e.message,"err");}
}
function daOpen(id){S.daId=id;S.daTab="thongtin";viewDuAn($("#main"));}
function daBack(){S.daId=null;S.daTab=null;viewDuAn($("#main"));}

async function daDetail(m){
  let ct; try{ ct = S.mode==="live" ? await api(`/du-an/${S.daId}/chi-tiet`) : _daDemoCt(); }catch(e){m.innerHTML=head("Dự án","")+`<div class="empty" style="color:#dc2626;padding:24px">${e.detail||e.message}</div><button class="btn-sm ghost" onclick="daBack()">← Danh sách</button>`;return;}
  S.daCt=ct;
  const tabs=[["thongtin","Thông tin"],["thietke","Thiết kế"],["tiendo","Tiến độ"],["antoan","An toàn"],["trienkhai","Triển khai"],["tailieu","Document"],["kpi","KPI"],["baocao","Báo cáo"]];
  m.innerHTML=head("Dự án",ct.ten);
  m.innerHTML+=`<button class="btn-sm ghost" style="margin-bottom:10px" onclick="daBack()">← Danh sách dự án</button>
    <div class="panel"><div class="panel-b" style="padding:16px 18px">
      <div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:8px">
        <h3 style="margin:0">${ct.ma?ct.ma+' · ':''}${ct.ten}</h3>
        ${ct.loai_du_an?`<span class="badge b-info">${DA_LOAI[ct.loai_du_an]||ct.loai_du_an}</span>`:''}
        <span class="badge ${ct.trang_thai==='HOAN_THANH'?'b-ok':(ct.trang_thai==='TAM_DUNG'?'b-tc':'b-cho')}">${DA_TT[ct.trang_thai]||ct.trang_thai}</span></div>
      <div style="display:flex;flex-wrap:wrap;gap:18px;font-size:13px;color:var(--muted);margin-bottom:10px">
        ${ct.chu_dau_tu?`<span>Chủ đầu tư: <b style="color:var(--text)">${ct.chu_dau_tu}</b></span>`:''}
        ${ct.cong_suat?`<span>Công suất: <b style="color:var(--text)">${ct.cong_suat}</b></span>`:''}
        ${ct.gia_tri_hop_dong?`<span>Giá trị HĐ: <b style="color:var(--text)">${vnd(ct.gia_tri_hop_dong)}</b></span>`:''}
        ${ct.ngay_kt_ke_hoach?`<span>Hoàn thành KH: <b style="color:var(--text)">${ct.ngay_kt_ke_hoach}</b></span>`:''}</div>
      <div style="max-width:420px">${_bar(ct.tien_do)}<div style="font-size:12px;color:var(--muted);margin-top:3px">Tiến độ tổng: <b style="color:var(--text)">${_num(ct.tien_do,1)}%</b> · ${ct.so_moc} mốc · ${ct.so_an_toan_mo} an toàn mở · ${ct.so_tai_lieu} tài liệu</div></div>
    </div></div>`;
  m.innerHTML+=`<div class="tabs">${tabs.map(([k,l])=>`<button class="${S.daTab===k?'active':''}" onclick="daSwitch('${k}')">${l}</button>`).join('')}</div><div id="daBody"></div>`;
  daRenderTab();
}
function daSwitch(t){S.daTab=t;daRenderTab();}
async function daRenderTab(){const h=$("#daBody");if(!h)return;h.innerHTML='<div class="empty" style="padding:24px">Đang tải…</div>';
  try{const f={thongtin:daThongTin,thietke:daThietKe,tiendo:daTienDo,antoan:daAnToan,trienkhai:daTrienKhai,tailieu:daTaiLieu,kpi:daKpi,baocao:daBaoCao}[S.daTab]||daThongTin;await f(h);}
  catch(e){h.innerHTML=`<div class="empty" style="color:#dc2626;padding:24px">${e.detail||e.message}</div>`;}
}

/* --- Tab Thông tin --- */
async function daThongTin(h){
  const ct=S.daCt; const canOp=can("du_an","THAO_TAC"); const ro=canOp?'':'disabled';
  const fopt=(id,lb,v,opts)=>`<div class="f"><label>${lb}</label><select id="${id}" ${ro}>${opts.map(([k,l])=>`<option value="${k}" ${v===k?'selected':''}>${l}</option>`).join('')}</select></div>`;
  const fin=(id,lb,v,ty)=>`<div class="f"><label>${lb}</label><input id="${id}" ${ty?`type="${ty}"`:''} value="${v??''}" ${ro}></div>`;
  let cti; try{ cti = S.mode==="live" ? await api(`/du-an/${S.daId}/chi-tieu`) : _daDemoChiTieu(); }catch(e){ cti={tieu_chuan_dau_ra:ct.tieu_chuan_dau_ra,danh_sach:[]}; }
  const qcOpts=_qcList(ct.loai_du_an).map(x=>`<option value="${x}">`).join('');
  // Panel 1: thông tin chung
  let html=`<div class="panel"><div class="panel-h"><h3>Thông tin dự án</h3></div><div class="panel-b">
    <div class="formrow">${fin('i_ma','Mã',ct.ma)}${fin('i_ten','Tên dự án',ct.ten)}${fopt('i_loai','Loại',ct.loai_du_an||'KHAC',Object.entries(DA_LOAI))}${fopt('i_tt','Trạng thái',ct.trang_thai,Object.entries(DA_TT))}</div>
    <div class="formrow">${fin('i_cdt','Chủ đầu tư',ct.chu_dau_tu)}${fin('i_dd','Địa điểm',ct.dia_diem)}${fin('i_cs','Công suất',ct.cong_suat)}${fin('i_gt','Giá trị hợp đồng',ct.gia_tri_hop_dong,'number')}</div>
    <div class="formrow">${fin('i_qcvn','Tiêu chuẩn áp dụng (chung)',ct.qcvn)}${fin('i_bd','Ngày bắt đầu',ct.ngay_bat_dau,'date')}${fin('i_ktkh','Hoàn thành (kế hoạch)',ct.ngay_kt_ke_hoach,'date')}${fin('i_kttt','Hoàn thành (thực tế)',ct.ngay_kt_thuc_te,'date')}</div>
    <div class="f" style="flex:1 1 100%;width:100%"><label>Mô tả (nguồn thải, ngành, mục tiêu xả/tái sử dụng…)</label><textarea id="i_mota" rows="6" style="width:100%;resize:vertical" ${ro}>${ct.mo_ta||''}</textarea></div>
    <div style="text-align:right;margin-top:8px"><button class="btn-sm ghost" onclick="daPhanTichAI()">🤖 Phân tích AI – nguyên lý thiết kế</button>${canOp?` <button class="btn-sm" onclick="daLuuThongTin()">Lưu thông tin</button>`:''}</div>
    <div id="da_ai_kq"></div></div></div>`;
  // Panel 2: chất lượng đầu vào & chỉ tiêu giới hạn đầu ra
  html+=`<div class="panel"><div class="panel-h"><h3>Chất lượng đầu vào & chỉ tiêu giới hạn đầu ra</h3></div><div class="panel-b">
    <div class="formrow"><div class="f" style="flex:3"><label>Tiêu chuẩn nước/khí đầu ra (chọn QCVN hoặc tự nhập)</label>
      <input id="i_chuan" list="i_qc_list" value="${cti.tieu_chuan_dau_ra||''}" placeholder="vd: QCVN 40:2025/BTNMT, cột B — hoặc nhập tiêu chuẩn khác" ${ro}>
      <datalist id="i_qc_list">${qcOpts}</datalist></div>
      <div class="f" style="max-width:100px"><label>Cột</label><select id="i_cot" ${ro}><option value="A">Cột A</option><option value="B" selected>Cột B</option><option value="C">Cột C</option></select></div>
      <div class="f" style="max-width:240px"><label>Loại thiết bị (khí thải)</label><select id="i_tb" ${ro}>${Object.entries(DA_TB19).map(([k,l])=>`<option value="${k}">${l}</option>`).join('')}</select></div>
      <div class="f" style="max-width:260px"><label>Chuẩn theo ngành</label><select id="i_nganh" ${ro}>${_ngOptions(ct.loai_du_an)}</select></div>
      ${canOp?`<button class="btn-sm ghost" style="align-self:end" onclick="daLuuChuan()">Lưu tiêu chuẩn</button><button class="btn-sm" style="align-self:end" onclick="daNapChiTieu()">⬇ Nạp chỉ tiêu</button>`:''}</div>`;
  if(canOp){
    html+=`<div class="formrow" style="margin-top:6px;align-items:end">
      <div class="f"><label>Chỉ tiêu</label><input id="ct_ten" placeholder="COD"></div>
      <div class="f"><label>Đơn vị</label><input id="ct_dv" placeholder="mg/L"></div>
      <div class="f"><label>Giá trị đầu vào</label><input id="ct_vao" type="number" step="any"></div>
      <div class="f"><label>Giới hạn đầu ra</label><input id="ct_ra" type="number" step="any"></div>
      <div class="f"><label>Ghi chú</label><input id="ct_gc" placeholder="cột B"></div>
      <button class="btn-sm" onclick="daThemChiTieu()">Thêm</button></div>`;
  }
  const rows=(cti.danh_sach||[]).map(c=>`<tr><td>${c.thu_tu||''}</td><td><b>${c.ten}</b></td><td>${c.don_vi||'—'}</td>
    <td class="num">${canOp?`<input type="number" step="any" id="cv_${c.id}" value="${c.gia_tri_vao??''}" style="width:84px;padding:3px 5px">`:(c.gia_tri_vao!=null?_num(c.gia_tri_vao,2):'—')}</td>
    <td class="num">${canOp?`<input type="number" step="any" id="cr_${c.id}" value="${c.gioi_han_ra??''}" style="width:84px;padding:3px 5px">`:(c.gioi_han_ra!=null?_num(c.gioi_han_ra,2):'—')}</td>
    <td class="num">${c.can_xu_ly!=null?`<b style="color:#0e7490">${_num(c.can_xu_ly,1)}%</b>`:'—'}</td>
    <td>${c.ghi_chu||''}</td>
    <td>${canOp?`<button class="btn-sm ghost" onclick="daSuaChiTieu(${c.id})">Lưu</button> <button class="btn-sm ghost" onclick="daXoaChiTieu(${c.id})">✕</button>`:''}</td></tr>`).join('');
  html+=`<table style="margin-top:10px"><thead><tr><th>#</th><th>Chỉ tiêu</th><th>Đơn vị</th><th class="num">Đầu vào</th><th class="num">Giới hạn đầu ra</th><th class="num">Cần xử lý</th><th>Ghi chú</th><th></th></tr></thead>
    <tbody>${rows||'<tr><td colspan="8" class="empty">Chưa có chỉ tiêu. Nhập chất lượng đầu vào và giới hạn đầu ra theo tiêu chuẩn áp dụng.</td></tr>'}</tbody></table>
    <div class="note" style="margin-top:8px;color:var(--muted)">Giá trị đầu vào & giới hạn đầu ra do anh nhập (theo số đo thực tế và cột tiêu chuẩn áp dụng). Danh sách QCVN chỉ là nhãn tham chiếu — hệ thống không tự điền giá trị giới hạn. "% cần xử lý" = (đầu vào − giới hạn)/đầu vào, chỉ hiện khi có đủ hai số.</div></div></div>`;
  h.innerHTML=html;
}
async function daLuuThongTin(){
  const body={ma:gv('i_ma')||null,ten:gv('i_ten'),loai_du_an:gv('i_loai'),trang_thai:gv('i_tt'),chu_dau_tu:gv('i_cdt')||null,dia_diem:gv('i_dd')||null,cong_suat:gv('i_cs')||null,gia_tri_hop_dong:Number(gv('i_gt')||0),qcvn:gv('i_qcvn')||null,ngay_bat_dau:gv('i_bd')||null,ngay_kt_ke_hoach:gv('i_ktkh')||null,ngay_kt_thuc_te:gv('i_kttt')||null,mo_ta:gv('i_mota')||null};
  if(S.mode!=="live"){toast("Đã lưu (demo)","ok");return;}
  try{await api(`/du-an/${S.daId}/thong-tin`,{method:'PUT',body:JSON.stringify(body)});toast("Đã lưu thông tin","ok");viewDuAn($("#main"));}catch(e){toast(e.detail||e.message,"err");}
}
async function daPhanTichAI(){
  const kq=$("#da_ai_kq"); if(kq)kq.innerHTML='<div class="note" style="padding:8px 0;color:var(--muted)">🤖 Đang phân tích mô tả & dữ liệu chất lượng…</div>';
  if(S.mode!=="live"){ if(kq)kq.innerHTML=_daRenderAI(_daDemoAI()); return; }
  try{ const r=await api(`/du-an/${S.daId}/phan-tich-ai`,{method:'POST',body:JSON.stringify({mo_ta:gv('i_mota')||null})}); if(kq)kq.innerHTML=_daRenderAI(r); }
  catch(e){ if(kq)kq.innerHTML=`<div class="note" style="color:#dc2626;padding:8px 0">${e.detail||e.message}</div>`; }
}
function _daRenderAI(r){
  const li=arr=>(arr&&arr.length)?'<ul style="margin:4px 0 10px;padding-left:18px">'+arr.map(x=>`<li style="margin:3px 0">${x}</li>`).join('')+'</ul>':'<div style="color:var(--muted);margin-bottom:8px">—</div>';
  const badge=r.nguon==='ANTHROPIC'?'<span class="badge b-info">AI</span>':'<span class="badge b-cho">Sơ bộ (quy tắc)</span>';
  return `<div class="panel" style="margin-top:12px;border:1px solid var(--teal)"><div class="panel-h"><h3>🤖 Phân tích nguyên lý thiết kế</h3><div class="spacer"></div>${badge}</div><div class="panel-b">
    ${r.tom_tat?`<div style="margin-bottom:10px">${r.tom_tat}</div>`:''}
    <div style="font-weight:600">Nguyên lý thiết kế</div>${li(r.nguyen_ly)}
    <div style="font-weight:600">Sơ đồ công nghệ đề xuất</div><div style="margin:4px 0 10px;font-size:14px">${(r.so_do_cong_nghe||[]).join(' → ')||'—'}</div>
    <div style="font-weight:600">Cần kiểm chứng</div>${li(r.can_kiem_chung)}
    ${(r.du_lieu_thieu&&r.du_lieu_thieu.length)?`<div style="font-weight:600;color:#d97706">Dữ liệu còn thiếu</div>${li(r.du_lieu_thieu)}`:''}
    <div class="note" style="color:var(--muted);padding:6px 0 0">${r.luu_y||''}</div></div></div>`;
}
function _daDemoAI(){return {nguon:"HEURISTIC",tom_tat:"Phân tích sơ bộ (demo) dựa trên dữ liệu chất lượng đã nhập.",nguyen_ly:["Tách rắn đầu vào: keo tụ/tạo bông → lắng/DAF","Hữu cơ COD/BOD: xử lý sinh học kỵ khí + hiếu khí","Độ màu: oxy hóa nâng cao (Fenton/O₃) và/hoặc than hoạt tính","Tái sử dụng: bổ sung màng UF → RO, xử lý reject bằng AOP"],so_do_cong_nghe:["Tiền xử lý","Xử lý sinh học","Oxy hóa/khử màu","Lọc hoàn thiện","Khử trùng/tái sử dụng"],can_kiem_chung:["Cân bằng tải lượng theo lưu lượng thực","Jar test xác định hóa chất & liều","Khả thi mặt bằng & chi phí vận hành"],du_lieu_thieu:[],luu_y:"Gợi ý sơ bộ theo quy tắc kỹ thuật chung, cần kỹ sư thẩm định và thí nghiệm thực tế."};}
async function daLuuChuan(){
  if(S.mode!=="live"){toast("Đã lưu (demo)","ok");return;}
  try{await api(`/du-an/${S.daId}/thong-tin`,{method:'PUT',body:JSON.stringify({tieu_chuan_dau_ra:gv('i_chuan')||null})});toast("Đã lưu tiêu chuẩn đầu ra","ok");}catch(e){toast(e.detail||e.message,"err");}
}
async function daNapChiTieu(){
  const s=gv('i_chuan'); const cot=(gv('i_cot')||'B'); const loai=(S.daCt||{}).loai_du_an;
  const nganh=gv('i_nganh')||'';
  const la19=(s||'').toUpperCase().includes('QCVN 19:2024');
  let danh_sach, kemGT, extra='', dt=_donTri(s), chuanLuu=gv('i_chuan');
  if(nganh && VAL_NGANH[nganh]){ const v=VAL_NGANH[nganh];
    if(Array.isArray(v)){ danh_sach=v.map(x=>Object.assign({},x)); dt=true; }
    else { danh_sach=(v[cot]||v.B).map(x=>Object.assign({},x)); dt=false; }
    kemGT=true; extra=' · '+DA_NGANH[nganh]; chuanLuu=DA_NGANH[nganh]; }
  else if(la19){ const tb=gv('i_tb')||'KHAC'; danh_sach=_giaTri19(tb,cot); kemGT=true; extra=' · '+(DA_TB19[tb]||tb); }
  else { const vals=_giaTriMau(s,cot);
    if(vals){ danh_sach=vals; kemGT=true; }
    else { const mau=_chiTieuMau(s,loai); if(!mau){toast("Chưa có danh mục mẫu cho tiêu chuẩn này — anh nhập thủ công","err");return;} danh_sach=mau; kemGT=false; } }
  const ghichu = kemGT ? (dt?`kèm giới hạn (đơn trị)${extra}`:`kèm giá trị giới hạn cột ${cot}${extra}`) : (_coBangGiaTri(s)?`cột ${cot} chưa có bảng giá trị — chỉ nạp tên`:`chỉ nạp tên chỉ tiêu (chưa có bảng giá trị cho tiêu chuẩn này)`);
  const canhBao = nganh ? _canhBaoNganh(nganh) : (kemGT ? _canhBaoNap(s) : "\nGiá trị giới hạn để trống để anh nhập theo cột áp dụng.");
  if(!confirm(`Nạp ${danh_sach.length} chỉ tiêu — ${ghichu}?${canhBao}`))return;
  if(S.mode!=="live"){toast(`Đã nạp ${danh_sach.length} chỉ tiêu (demo)`,"ok");return;}
  try{
    if(chuanLuu)await api(`/du-an/${S.daId}/thong-tin`,{method:'PUT',body:JSON.stringify({tieu_chuan_dau_ra:chuanLuu})});
    const r=await api(`/du-an/${S.daId}/chi-tieu/nap-mau`,{method:'POST',body:JSON.stringify({danh_sach})});
    toast(`Đã nạp ${r.them} chỉ tiêu${r.bo_qua?` (bỏ qua ${r.bo_qua} đã có)`:''}${kemGT?(dt?' kèm giới hạn':` kèm giới hạn cột ${cot}`):''}`,"ok");daRenderTab();
  }catch(e){toast(e.detail||e.message,"err");}
}
async function daThemChiTieu(){
  const v=gv('ct_vao'),r=gv('ct_ra');
  const body={ten:gv('ct_ten'),don_vi:gv('ct_dv')||null,gia_tri_vao:v!==''?Number(v):null,gioi_han_ra:r!==''?Number(r):null,ghi_chu:gv('ct_gc')||null};
  if(!body.ten){toast("Nhập tên chỉ tiêu","err");return;}
  if(S.mode!=="live"){toast("Đã thêm (demo)","ok");return;}
  try{await api(`/du-an/${S.daId}/chi-tieu`,{method:'POST',body:JSON.stringify(body)});toast("Đã thêm chỉ tiêu","ok");daRenderTab();}catch(e){toast(e.detail||e.message,"err");}
}
async function daSuaChiTieu(id){
  const v=gv('cv_'+id),r=gv('cr_'+id);
  if(S.mode!=="live"){toast("Đã lưu (demo)","ok");return;}
  try{await api(`/du-an/chi-tieu/${id}`,{method:'PUT',body:JSON.stringify({gia_tri_vao:v!==''?Number(v):null,gioi_han_ra:r!==''?Number(r):null})});toast("Đã cập nhật","ok");daRenderTab();}catch(e){toast(e.detail||e.message,"err");}
}
async function daXoaChiTieu(id){
  if(!confirm("Xóa chỉ tiêu này?"))return;
  if(S.mode!=="live"){toast("Đã xóa (demo)","ok");return;}
  try{await api(`/du-an/chi-tieu/${id}`,{method:'DELETE'});toast("Đã xóa","ok");daRenderTab();}catch(e){toast(e.detail||e.message,"err");}
}
function _daDemoChiTieu(){return {tieu_chuan_dau_ra:"QCVN 40:2025/BTNMT — Nước thải công nghiệp (cột B)",danh_sach:[{id:1,thu_tu:1,ten:"COD",don_vi:"mg/L",gia_tri_vao:1017,gioi_han_ra:150,ghi_chu:"cột B",can_xu_ly:85.3},{id:2,thu_tu:2,ten:"Độ màu",don_vi:"Pt-Co",gia_tri_vao:1200,gioi_han_ra:150,ghi_chu:"cột B",can_xu_ly:87.5},{id:3,thu_tu:3,ten:"pH",don_vi:"-",gia_tri_vao:null,gioi_han_ra:null,ghi_chu:"6-9",can_xu_ly:null}]};}

/* --- Tab Thiết kế --- */
async function daThietKe(h){
  const tk=(S.daCt&&S.daCt.thiet_ke)||{}; const canOp=can("du_an","THAO_TAC"); const ro=canOp?'':'disabled';
  const ts=Array.isArray(tk.thong_so)?tk.thong_so:[];
  const tsText=ts.map(x=>`${x.ten||''} | ${x.gia_tri||''} | ${x.don_vi||''}`).join('\n');
  const tsTable=ts.length?`<table><thead><tr><th>Thông số</th><th>Giá trị</th><th>Đơn vị</th></tr></thead><tbody>${ts.map(x=>`<tr><td>${x.ten||''}</td><td class="num">${x.gia_tri||''}</td><td>${x.don_vi||''}</td></tr>`).join('')}</tbody></table>`:'<div class="empty" style="padding:8px">Chưa có thông số.</div>';
  h.innerHTML=`<div class="panel"><div class="panel-h"><h3>Thiết kế</h3>${tk.trang_thai?`<div class="spacer"></div><span class="badge ${tk.trang_thai==='DA_DUYET'?'b-ok':'b-cho'}">${tk.trang_thai==='DA_DUYET'?'Đã duyệt':'Dự thảo'}</span>`:''}</div><div class="panel-b">
    <div class="f"><label>Công nghệ áp dụng</label><textarea id="tk_cn" rows="2" ${ro}>${tk.cong_nghe||''}</textarea></div>
    <div class="formrow"><div class="f"><label>Công suất thiết kế</label><input id="tk_cs" value="${tk.cong_suat_tk||''}" ${ro}></div>
      <div class="f"><label>Tiêu chuẩn</label><input id="tk_tc" value="${tk.tieu_chuan||''}" ${ro}></div>
      <div class="f"><label>Người thiết kế</label><input id="tk_ntk" value="${tk.nguoi_thiet_ke||''}" ${ro}></div>
      <div class="f"><label>Phiên bản</label><input id="tk_pb" value="${tk.phien_ban||'v1.0'}" ${ro}></div>
      <div class="f"><label>Trạng thái</label><select id="tk_tt" ${ro}><option value="DU_THAO" ${tk.trang_thai!=='DA_DUYET'?'selected':''}>Dự thảo</option><option value="DA_DUYET" ${tk.trang_thai==='DA_DUYET'?'selected':''}>Đã duyệt</option></select></div></div>
    <div style="font-weight:600;font-size:13px;margin:8px 0 4px">Thông số thiết kế</div>
    ${canOp?`<div class="f"><label>Nhập mỗi dòng: tên | giá trị | đơn vị</label><textarea id="tk_ts" rows="4" placeholder="COD đầu vào | 1017 | mg/L">${tsText}</textarea></div>`:tsTable}
    ${canOp?`<div style="text-align:right;margin-top:8px"><button class="btn-sm" onclick="daLuuThietKe()">Lưu thiết kế</button></div>`:''}</div></div>
    ${canOp&&ts.length?`<div class="panel"><div class="panel-h"><h3>Bảng thông số hiện tại</h3></div><div class="panel-b">${tsTable}</div></div>`:''}`;
}
async function daLuuThietKe(){
  const raw=gv('tk_ts')||''; const thong_so=raw.split('\n').map(l=>l.trim()).filter(Boolean).map(l=>{const p=l.split('|').map(x=>x.trim());return {ten:p[0]||'',gia_tri:p[1]||'',don_vi:p[2]||''};});
  const body={cong_nghe:gv('tk_cn')||null,cong_suat_tk:gv('tk_cs')||null,tieu_chuan:gv('tk_tc')||null,nguoi_thiet_ke:gv('tk_ntk')||null,phien_ban:gv('tk_pb')||null,trang_thai:gv('tk_tt'),thong_so};
  if(S.mode!=="live"){toast("Đã lưu (demo)","ok");return;}
  try{await api(`/du-an/${S.daId}/thiet-ke`,{method:'PUT',body:JSON.stringify(body)});toast("Đã lưu thiết kế","ok");S.daCt=await api(`/du-an/${S.daId}/chi-tiet`);daRenderTab();}catch(e){toast(e.detail||e.message,"err");}
}

/* --- Tab Tiến độ --- */
async function daTienDo(h){
  const canOp=can("du_an","THAO_TAC");
  let d; try{ d = S.mode==="live" ? await api(`/du-an/${S.daId}/moc`) : _daDemoMoc(); }catch(e){h.innerHTML=`<div class="empty" style="color:#dc2626;padding:16px">${e.detail||e.message}</div>`;return;}
  let html=`<div class="panel"><div class="panel-b" style="padding:14px 18px"><div style="max-width:480px">${_bar(d.tien_do)}<div style="font-size:13px;margin-top:4px">Tiến độ tổng (theo trọng số mốc): <b>${_num(d.tien_do,1)}%</b></div></div></div></div>`;
  if(canOp){
    html+=`<div class="panel"><div class="panel-h"><h3>Thêm mốc / hạng mục</h3></div><div class="panel-b">
      <div class="formrow"><div class="f"><label>Thứ tự</label><input id="mc_tt" type="number" style="max-width:80px"></div>
        <div class="f" style="flex:2"><label>Tên mốc</label><input id="mc_ten" placeholder="Thi công lắp đặt"></div>
        <div class="f"><label>Giai đoạn</label><select id="mc_gd">${Object.entries(DA_GD).map(([k,l])=>`<option value="${k}">${l}</option>`).join('')}</select></div>
        <div class="f"><label>Trọng số</label><input id="mc_ts" type="number" value="1" style="max-width:90px"></div>
        <div class="f"><label>BĐ kế hoạch</label><input id="mc_bd" type="date"></div>
        <div class="f"><label>KT kế hoạch</label><input id="mc_kt" type="date"></div>
        <button class="btn-sm" style="align-self:end" onclick="daThemMoc()">Thêm</button></div></div></div>`;
  }
  const rows=(d.moc||[]).map(m=>{const tre=m.ngay_kt_kh&&!['HOAN_THANH'].includes(m.trang_thai)&&m.ngay_kt_kh<new Date().toISOString().slice(0,10);
    return `<tr><td>${m.thu_tu||''}</td><td><b>${m.ten}</b>${m.phu_trach?`<div style="font-size:11px;color:var(--muted)">${m.phu_trach}</div>`:''}</td>
    <td>${DA_GD[m.giai_doan]||m.giai_doan||'—'}</td><td class="num">${_num(m.trong_so,1)}</td>
    <td style="min-width:140px">${_bar(m.phan_tram)}<div style="font-size:11px;color:var(--muted);margin-top:2px">${_num(m.phan_tram,0)}%</div></td>
    <td>${m.ngay_kt_kh||'—'}${tre?'<div style="font-size:11px;color:#dc2626">trễ hạn</div>':''}</td>
    <td><span class="badge ${m.trang_thai==='HOAN_THANH'?'b-ok':(m.trang_thai==='CHAM_TRE'||tre?'b-tc':'b-cho')}">${DA_TTMOC[m.trang_thai]||m.trang_thai}</span></td>
    <td>${canOp?`<input type="number" id="mp_${m.id}" value="${m.phan_tram}" style="width:60px;padding:3px 5px" title="% hoàn thành"> <button class="btn-sm ghost" onclick="daSuaMoc(${m.id})">Lưu</button> <button class="btn-sm ghost" onclick="daXoaMoc(${m.id})">✕</button>`:''}</td></tr>`;}).join('');
  html+=`<div class="panel"><div class="panel-h"><h3>Mốc tiến độ</h3></div><div class="panel-b"><table>
    <thead><tr><th>#</th><th>Mốc</th><th>Giai đoạn</th><th class="num">Trọng số</th><th>% hoàn thành</th><th>KT kế hoạch</th><th>Trạng thái</th><th></th></tr></thead>
    <tbody>${rows||'<tr><td colspan="8" class="empty">Chưa có mốc tiến độ.</td></tr>'}</tbody></table>
    <div class="note" style="margin-top:8px;color:var(--muted)">Tiến độ tổng = Σ(trọng số × %)/Σ trọng số — tính trực tiếp từ % của các mốc anh nhập, không suy đoán.</div></div></div>`;
  h.innerHTML=html;
}
async function daThemMoc(){
  const body={thu_tu:Number(gv('mc_tt')||0),ten:gv('mc_ten'),giai_doan:gv('mc_gd'),trong_so:Number(gv('mc_ts')||1),ngay_bd_kh:gv('mc_bd')||null,ngay_kt_kh:gv('mc_kt')||null};
  if(!body.ten){toast("Nhập tên mốc","err");return;}
  if(S.mode!=="live"){toast("Đã thêm (demo)","ok");return;}
  try{await api(`/du-an/${S.daId}/moc`,{method:'POST',body:JSON.stringify(body)});toast("Đã thêm mốc","ok");daRenderTab();}catch(e){toast(e.detail||e.message,"err");}
}
async function daSuaMoc(id){
  const pt=Number(gv('mp_'+id)||0);
  if(S.mode!=="live"){toast("Đã lưu (demo)","ok");return;}
  try{const r=await api(`/du-an/moc/${id}`,{method:'PUT',body:JSON.stringify({phan_tram:pt})});toast(`Đã cập nhật · tiến độ tổng ${_num(r.tien_do,1)}%`,"ok");daRenderTab();}catch(e){toast(e.detail||e.message,"err");}
}
async function daXoaMoc(id){
  if(!confirm("Xóa mốc này?"))return;
  if(S.mode!=="live"){toast("Đã xóa (demo)","ok");return;}
  try{await api(`/du-an/moc/${id}`,{method:'DELETE'});toast("Đã xóa","ok");daRenderTab();}catch(e){toast(e.detail||e.message,"err");}
}

/* --- Tab An toàn --- */
async function daAnToan(h){
  const canOp=can("du_an","THAO_TAC");
  let d; try{ d = S.mode==="live" ? await api(`/du-an/${S.daId}/an-toan`) : _daDemoAT(); }catch(e){h.innerHTML=`<div class="empty" style="color:#dc2626;padding:16px">${e.detail||e.message}</div>`;return;}
  let html=`<div style="display:flex;flex-wrap:wrap;gap:8px;padding:0 0 12px">
    ${_tcCard("Tổng mối nguy",d.tong)}${_tcCard("Đang mở",d.mo,'',d.mo?'#dc2626':'#16a34a')}
    ${_tcCard("Rủi ro CAO",d.theo_muc_rui_ro.CAO||0,'',(d.theo_muc_rui_ro.CAO||0)?'#dc2626':'#16a34a')}</div>`;
  if(canOp){
    html+=`<div class="panel"><div class="panel-h"><h3>Thêm đánh giá an toàn (nhận diện mối nguy)</h3></div><div class="panel-b">
      <div class="formrow"><div class="f" style="flex:2"><label>Hạng mục / khu vực</label><input id="at_hm" placeholder="Làm việc trong bể kín"></div>
        <div class="f"><label>Mức rủi ro</label><select id="at_rr"><option value="CAO">Cao</option><option value="TRUNG" selected>Trung bình</option><option value="THAP">Thấp</option></select></div>
        <div class="f"><label>Phụ trách</label><input id="at_pt"></div>
        <div class="f"><label>Hạn xử lý</label><input id="at_han" type="date"></div></div>
      <div class="formrow"><div class="f" style="flex:1"><label>Mối nguy</label><input id="at_mn" placeholder="Thiếu oxy, khí độc H2S"></div>
        <div class="f" style="flex:1"><label>Biện pháp kiểm soát</label><input id="at_bp" placeholder="Thông gió, đo khí, giấy phép vào KGHC"></div>
        <button class="btn-sm" style="align-self:end" onclick="daThemAnToan()">Thêm</button></div></div></div>`;
  }
  const rows=(d.danh_sach||[]).map(a=>`<tr><td><b>${a.hang_muc}</b>${a.phu_trach?`<div style="font-size:11px;color:var(--muted)">PT: ${a.phu_trach}</div>`:''}</td>
    <td>${a.moi_nguy||'—'}</td><td><span class="badge ${a.muc_rui_ro==='CAO'?'b-tc':(a.muc_rui_ro==='THAP'?'b-ok':'b-cho')}">${DA_RR[a.muc_rui_ro]||a.muc_rui_ro}</span></td>
    <td>${a.bien_phap||'—'}</td><td>${a.han||'—'}</td>
    <td><span class="badge ${a.trang_thai==='DA_KIEM_SOAT'?'b-ok':'b-cho'}">${a.trang_thai==='DA_KIEM_SOAT'?'Đã kiểm soát':(a.trang_thai==='DANG_XU_LY'?'Đang xử lý':'Mở')}</span></td>
    <td>${canOp?`<select onchange="daSuaAnToan(${a.id},this.value)" style="padding:3px 5px"><option ${a.trang_thai==='MO'?'selected':''} value="MO">Mở</option><option ${a.trang_thai==='DANG_XU_LY'?'selected':''} value="DANG_XU_LY">Đang xử lý</option><option ${a.trang_thai==='DA_KIEM_SOAT'?'selected':''} value="DA_KIEM_SOAT">Đã kiểm soát</option></select>`:''}</td></tr>`).join('');
  html+=`<div class="panel"><div class="panel-h"><h3>Bảng đánh giá rủi ro an toàn (HIRA)</h3></div><div class="panel-b"><table>
    <thead><tr><th>Hạng mục</th><th>Mối nguy</th><th>Mức RR</th><th>Biện pháp</th><th>Hạn</th><th>Trạng thái</th><th></th></tr></thead>
    <tbody>${rows||'<tr><td colspan="7" class="empty">Chưa có đánh giá an toàn.</td></tr>'}</tbody></table>
    <div class="note" style="margin-top:8px;color:var(--muted)">Mức rủi ro do người đánh giá xác định (không tự gán). Mục "Đang mở" gồm các mối nguy chưa kiểm soát.</div></div></div>`;
  h.innerHTML=html;
}
async function daThemAnToan(){
  const body={hang_muc:gv('at_hm'),moi_nguy:gv('at_mn')||null,muc_rui_ro:gv('at_rr'),bien_phap:gv('at_bp')||null,phu_trach:gv('at_pt')||null,han:gv('at_han')||null};
  if(!body.hang_muc){toast("Nhập hạng mục","err");return;}
  if(S.mode!=="live"){toast("Đã thêm (demo)","ok");return;}
  try{await api(`/du-an/${S.daId}/an-toan`,{method:'POST',body:JSON.stringify(body)});toast("Đã thêm","ok");daRenderTab();}catch(e){toast(e.detail||e.message,"err");}
}
async function daSuaAnToan(id,tt){
  if(S.mode!=="live"){return;}
  try{await api(`/du-an/an-toan/${id}`,{method:'PUT',body:JSON.stringify({hang_muc:S.daCt.ten,trang_thai:tt})});toast("Đã cập nhật trạng thái","ok");daRenderTab();}catch(e){toast(e.detail||e.message,"err");}
}

/* --- Tab Triển khai (nhật ký) --- */
async function daTrienKhai(h){
  const canOp=can("du_an","THAO_TAC");
  let ds; try{ ds = S.mode==="live" ? await api(`/du-an/${S.daId}/nhat-ky`) : []; }catch(e){h.innerHTML=`<div class="empty" style="color:#dc2626;padding:16px">${e.detail||e.message}</div>`;return;}
  let html="";
  if(canOp){
    html+=`<div class="panel"><div class="panel-h"><h3>Ghi nhật ký triển khai</h3></div><div class="panel-b">
      <div class="formrow"><div class="f"><label>Ngày</label><input id="nk_ngay" type="date" value="${new Date().toISOString().slice(0,10)}"></div>
        <div class="f"><label>Nhân lực</label><input id="nk_nl" placeholder="6 CN + 1 giám sát"></div>
        <div class="f"><label>Thiết bị</label><input id="nk_tb" placeholder="Cẩu 5 tấn"></div>
        <div class="f"><label>Thời tiết</label><input id="nk_tt" placeholder="Nắng"></div></div>
      <div class="f"><label>Nội dung công việc</label><textarea id="nk_nd" rows="2"></textarea></div>
      <div class="formrow"><div class="f" style="flex:1"><label>Vấn đề / vướng mắc</label><input id="nk_vd"></div>
        <button class="btn-sm" style="align-self:end" onclick="daThemNhatKy()">Lưu nhật ký</button></div></div></div>`;
  }
  const rows=(ds||[]).map(r=>`<tr><td>${r.ngay}</td><td>${r.noi_dung||'—'}${r.van_de?`<div style="font-size:11px;color:#dc2626">⚠️ ${r.van_de}</div>`:''}</td>
    <td>${r.nhan_luc||'—'}</td><td>${r.thiet_bi||'—'}</td><td>${r.thoi_tiet||'—'}</td><td style="font-size:12px;color:var(--muted)">${r.nguoi_ghi||''}</td></tr>`).join('');
  html+=`<div class="panel"><div class="panel-h"><h3>Nhật ký thi công</h3></div><div class="panel-b"><table>
    <thead><tr><th>Ngày</th><th>Nội dung</th><th>Nhân lực</th><th>Thiết bị</th><th>Thời tiết</th><th>Người ghi</th></tr></thead>
    <tbody>${rows||'<tr><td colspan="6" class="empty">Chưa có nhật ký.</td></tr>'}</tbody></table></div></div>`;
  h.innerHTML=html;
}
async function daThemNhatKy(){
  const body={ngay:gv('nk_ngay')||null,noi_dung:gv('nk_nd')||null,nhan_luc:gv('nk_nl')||null,thiet_bi:gv('nk_tb')||null,thoi_tiet:gv('nk_tt')||null,van_de:gv('nk_vd')||null};
  if(S.mode!=="live"){toast("Đã lưu (demo)","ok");return;}
  try{await api(`/du-an/${S.daId}/nhat-ky`,{method:'POST',body:JSON.stringify(body)});toast("Đã lưu nhật ký","ok");daRenderTab();}catch(e){toast(e.detail||e.message,"err");}
}

/* --- Tab Tài liệu --- */
async function daTaiLieu(h){
  const canOp=can("du_an","THAO_TAC");
  let d; try{ d = S.mode==="live" ? await api(`/du-an/${S.daId}/tai-lieu`) : _daDemoTL(); }catch(e){h.innerHTML=`<div class="empty" style="color:#dc2626;padding:16px">${e.detail||e.message}</div>`;return;}
  let html=`<div class="panel"><div class="panel-h"><h3>1 · Biểu mẫu triển khai dự án</h3></div><div class="panel-b">
    <p style="color:var(--muted);font-size:13px;margin:0 0 8px">Mở biểu mẫu in sẵn tiêu đề công ty &amp; thông tin dự án (in / lưu PDF). Ký xong tải lại vào mục lưu trữ bên dưới (loại "Khác" hoặc loại phù hợp).</p>
    ${[["giao_nhan","Biên bản giao nhận"],["ban_giao","Biên bản bàn giao"],["nghiem_thu","Biên bản nghiệm thu"],["khao_sat","Biên bản khảo sát hiện trường"]].map(([k,l])=>`<button class="btn-sm ghost" style="margin:4px 6px 4px 0" onclick="daBieuMau('${k}')">🖨 ${l}</button>`).join('')}
  </div></div>
  <div class="panel-h" style="border:0;padding:6px 2px 2px"><h3>2 · Lưu trữ dữ liệu</h3></div>
  <div style="display:flex;flex-wrap:wrap;gap:8px;padding:0 0 12px">
    ${Object.entries(DA_TLOAI).map(([k,l])=>_tcCard(l,d.theo_loai[k]||0)).join('')}</div>`;
  if(canOp){
    html+=`<div class="panel"><div class="panel-h"><h3>Thêm tài liệu</h3></div><div class="panel-b">
      <div class="formrow"><div class="f"><label>Loại</label><select id="tl_loai">${Object.entries(DA_TLOAI).map(([k,l])=>`<option value="${k}">${l}</option>`).join('')}</select></div>
        <div class="f" style="flex:2"><label>Tên tài liệu</label><input id="tl_ten" placeholder="Bản vẽ P&ID hệ thống"></div>
        <div class="f"><label>Mã số</label><input id="tl_ms" placeholder="DWG-001"></div>
        <div class="f"><label>Phiên bản</label><input id="tl_pb" placeholder="A"></div></div>
      <div class="formrow"><div class="f" style="flex:1"><label>Tệp đính kèm (tùy chọn)</label><input id="tl_file" type="file"></div>
        <button class="btn-sm" style="align-self:end" onclick="daThemTaiLieu()">Thêm tài liệu</button></div></div></div>`;
  }
  const rows=(d.danh_sach||[]).map(t=>`<tr><td><span class="badge b-info">${DA_TLOAI[t.loai]||t.loai}</span></td>
    <td><b>${t.ten}</b>${t.ghi_chu?`<div style="font-size:11px;color:var(--muted)">${t.ghi_chu}</div>`:''}</td><td>${t.ma_so||'—'}</td><td>${t.phien_ban||'—'}</td><td>${t.ngay||'—'}</td>
    <td>${t.co_file?`<button class="btn-sm ghost" onclick="daTaiVe(${t.id})">Tải về</button>`:'<span style="color:var(--muted);font-size:12px">không có tệp</span>'}</td>
    <td>${canOp?`<button class="btn-sm ghost" onclick="daXoaTaiLieu(${t.id})">✕</button>`:''}</td></tr>`).join('');
  html+=`<div class="panel"><div class="panel-h"><h3>Hồ sơ tài liệu dự án</h3></div><div class="panel-b"><table>
    <thead><tr><th>Loại</th><th>Tên</th><th>Mã số</th><th>P.bản</th><th>Ngày</th><th>Tệp</th><th></th></tr></thead>
    <tbody>${rows||'<tr><td colspan="7" class="empty">Chưa có tài liệu.</td></tr>'}</tbody></table>
    <div class="note" style="margin-top:8px;color:var(--muted)">Phân loại: thiết bị · vật tư · bản vẽ · biên bản giao nhận · bàn giao · nghiệm thu. Có thể đính kèm tệp (PDF, ảnh, bản vẽ…).</div></div></div>`;
  h.innerHTML=html;
}
async function daThemTaiLieu(){
  const ten=gv('tl_ten'); if(!ten){toast("Nhập tên tài liệu","err");return;}
  if(S.mode!=="live"){toast("Đã thêm (demo)","ok");return;}
  const fd=new FormData();fd.append('ten',ten);fd.append('loai',gv('tl_loai'));
  if(gv('tl_ms'))fd.append('ma_so',gv('tl_ms'));if(gv('tl_pb'))fd.append('phien_ban',gv('tl_pb'));
  const fi=$('#tl_file');if(fi&&fi.files&&fi.files[0])fd.append('file',fi.files[0]);
  try{await apiUpload(`/du-an/${S.daId}/tai-lieu`,fd);toast("Đã thêm tài liệu","ok");daRenderTab();}catch(e){toast(e.detail||e.message,"err");}
}
async function daXoaTaiLieu(id){
  if(!confirm("Xóa tài liệu này?"))return;
  if(S.mode!=="live"){toast("Đã xóa (demo)","ok");return;}
  try{await api(`/du-an/tai-lieu/${id}`,{method:'DELETE'});toast("Đã xóa","ok");daRenderTab();}catch(e){toast(e.detail||e.message,"err");}
}
async function daTaiVe(id){
  if(S.mode!=="live"){toast("Tải về (demo)","ok");return;}
  try{const h={};if(S.token)h['Authorization']='Bearer '+S.token;const r=await fetch(S.api+`/du-an/tai-lieu/${id}/tai-ve`,{headers:h});
    if(!r.ok)throw new Error("Không tải được");const blob=await r.blob();const u=URL.createObjectURL(blob);const a=document.createElement('a');a.href=u;a.download='tailieu';a.click();URL.revokeObjectURL(u);}catch(e){toast(e.message,"err");}
}

/* --- Tab KPI --- */
async function daKpi(h){
  const canOp=can("du_an","THAO_TAC");
  let d; try{ d = S.mode==="live" ? await api(`/du-an/${S.daId}/kpi`) : _daDemoKPI(); }catch(e){h.innerHTML=`<div class="empty" style="color:#dc2626;padding:16px">${e.detail||e.message}</div>`;return;}
  let html=`<div style="display:flex;gap:8px;padding:0 0 12px">${_tcCard("KPI bình quân đạt (theo trọng số)",d.binh_quan_dat!=null?_num(d.binh_quan_dat,1)+'%':'—','','#0e7490')}</div>`;
  if(canOp){
    html+=`<div class="panel"><div class="panel-h"><h3>Thêm KPI</h3></div><div class="panel-b">
      <div class="formrow"><div class="f" style="flex:2"><label>Tên KPI</label><input id="kp_ten" placeholder="Tiến độ đúng hạn"></div>
        <div class="f"><label>Đơn vị</label><input id="kp_dv" placeholder="%"></div>
        <div class="f"><label>Chiều tốt</label><select id="kp_chieu"><option value="CAO">Càng cao càng tốt</option><option value="THAP">Càng thấp càng tốt</option></select></div>
        <div class="f"><label>Mục tiêu</label><input id="kp_mt" type="number"></div>
        <div class="f"><label>Thực tế</label><input id="kp_tt" type="number"></div>
        <div class="f"><label>Trọng số</label><input id="kp_ts" type="number" value="1" style="max-width:90px"></div>
        <button class="btn-sm" style="align-self:end" onclick="daThemKpi()">Thêm</button></div></div></div>`;
  }
  const rows=(d.danh_sach||[]).map(k=>{const dat=k.dat_phan_tram;const mau=dat==null?'var(--muted)':(dat>=100?'#16a34a':(dat>=80?'#d97706':'#dc2626'));
    return `<tr><td><b>${k.ten}</b></td><td>${k.chieu==='THAP'?'↓ thấp tốt':'↑ cao tốt'}</td>
    <td class="num">${_num(k.muc_tieu,2)} ${k.don_vi||''}</td>
    <td>${canOp?`<input type="number" id="kt_${k.id}" value="${k.thuc_te}" style="width:80px;padding:3px 5px">`:_num(k.thuc_te,2)+' '+(k.don_vi||'')}</td>
    <td class="num">${_num(k.trong_so,1)}</td>
    <td class="num"><b style="color:${mau}">${dat==null?'—':_num(dat,1)+'%'}</b></td>
    <td>${canOp?`<button class="btn-sm ghost" onclick="daSuaKpi(${k.id})">Lưu</button> <button class="btn-sm ghost" onclick="daXoaKpi(${k.id})">✕</button>`:''}</td></tr>`;}).join('');
  html+=`<div class="panel"><div class="panel-h"><h3>KPI dự án</h3></div><div class="panel-b"><table>
    <thead><tr><th>KPI</th><th>Chiều</th><th class="num">Mục tiêu</th><th>Thực tế</th><th class="num">Trọng số</th><th class="num">Đạt</th><th></th></tr></thead>
    <tbody>${rows||'<tr><td colspan="7" class="empty">Chưa có KPI. Tự định nghĩa mục tiêu/thực tế theo dự án.</td></tr>'}</tbody></table>
    <div class="note" style="margin-top:8px;color:var(--muted)">Mục tiêu & thực tế do anh nhập theo thực tế dự án. % đạt = thực tế/mục tiêu (chiều "cao tốt") hoặc mục tiêu/thực tế (chiều "thấp tốt"). Bình quân theo trọng số.</div></div></div>`;
  h.innerHTML=html;
}
async function daThemKpi(){
  const body={ten:gv('kp_ten'),don_vi:gv('kp_dv')||null,chieu:gv('kp_chieu'),muc_tieu:gv('kp_mt')!==''?Number(gv('kp_mt')):null,thuc_te:gv('kp_tt')!==''?Number(gv('kp_tt')):null,trong_so:Number(gv('kp_ts')||1)};
  if(!body.ten){toast("Nhập tên KPI","err");return;}
  if(S.mode!=="live"){toast("Đã thêm (demo)","ok");return;}
  try{await api(`/du-an/${S.daId}/kpi`,{method:'POST',body:JSON.stringify(body)});toast("Đã thêm KPI","ok");daRenderTab();}catch(e){toast(e.detail||e.message,"err");}
}
async function daSuaKpi(id){
  const tt=gv('kt_'+id);
  if(S.mode!=="live"){toast("Đã lưu (demo)","ok");return;}
  try{await api(`/du-an/kpi/${id}`,{method:'PUT',body:JSON.stringify({thuc_te:tt!==''?Number(tt):null})});toast("Đã cập nhật","ok");daRenderTab();}catch(e){toast(e.detail||e.message,"err");}
}
async function daXoaKpi(id){
  if(!confirm("Xóa KPI này?"))return;
  if(S.mode!=="live"){toast("Đã xóa (demo)","ok");return;}
  try{await api(`/du-an/kpi/${id}`,{method:'DELETE'});toast("Đã xóa","ok");daRenderTab();}catch(e){toast(e.detail||e.message,"err");}
}

/* --- Tab Báo cáo --- */
async function daBaoCao(h){
  const canOp=can("du_an","THAO_TAC");
  let bc,ds; try{ if(S.mode==="live"){[bc,ds]=await Promise.all([api(`/du-an/${S.daId}/bao-cao-tong-hop`),api(`/du-an/${S.daId}/bao-cao`)]);} else {bc=_daDemoBC();ds=[];} }catch(e){h.innerHTML=`<div class="empty" style="color:#dc2626;padding:16px">${e.detail||e.message}</div>`;return;}
  const mocTT=bc.moc.theo_trang_thai||{};
  let html=`<div class="panel"><div class="panel-h"><h3>Báo cáo tổng hợp (số liệu thực tại thời điểm xem)</h3></div><div class="panel-b">
    <div style="display:flex;flex-wrap:wrap;gap:8px">
      ${_tcCard("Tiến độ tổng",_num(bc.tien_do,1)+'%')}
      ${_tcCard("Mốc hoàn thành",`${mocTT.HOAN_THANH||0}/${bc.moc.tong}`)}
      ${_tcCard("An toàn đang mở",bc.an_toan.mo,'',bc.an_toan.mo?'#dc2626':'#16a34a')}
      ${_tcCard("Tài liệu",bc.tai_lieu.tong)}
      ${_tcCard("KPI bình quân",bc.kpi.binh_quan_dat!=null?_num(bc.kpi.binh_quan_dat,1)+'%':'—')}
      ${_tcCard("Ngân sách còn lại",vnd(bc.ngan_sach.con_lai),bc.ngan_sach.vuot?'⚠️ vượt dự toán':'',bc.ngan_sach.vuot?'#dc2626':'#16a34a')}</div>
    <div class="note" style="margin-top:10px;color:var(--muted)">An toàn theo mức rủi ro: CAO ${bc.an_toan.theo_muc_rui_ro.CAO||0} · TRUNG ${bc.an_toan.theo_muc_rui_ro.TRUNG||0} · THẤP ${bc.an_toan.theo_muc_rui_ro.THAP||0}. Tài liệu theo loại: ${Object.entries(bc.tai_lieu.theo_loai||{}).map(([k,v])=>`${DA_TLOAI[k]||k} ${v}`).join(' · ')||'—'}.</div></div></div>`;
  if(canOp){
    html+=`<div class="panel"><div class="panel-h"><h3>Lập báo cáo kỳ (chốt số liệu)</h3></div><div class="panel-b">
      <div class="formrow"><div class="f"><label>Kỳ</label><input id="bc_ky" placeholder="2026-08"></div>
        <div class="f" style="flex:2"><label>Tiêu đề</label><input id="bc_td" placeholder="Báo cáo tiến độ tháng 8"></div></div>
      <div class="f"><label>Nội dung</label><textarea id="bc_nd" rows="2"></textarea></div>
      <div class="formrow"><div class="f" style="flex:1"><label>Vấn đề / kiến nghị</label><input id="bc_vd"></div>
        <button class="btn-sm" style="align-self:end" onclick="daLapBaoCao()">Lập báo cáo</button></div>
      <div class="note" style="color:var(--muted)">Báo cáo sẽ chốt lại % tiến độ thực tại thời điểm lập để lưu lịch sử.</div></div></div>`;
  }
  const rows=(ds||[]).map(r=>`<tr><td>${r.ky||'—'}</td><td><b>${r.tieu_de||''}</b>${r.noi_dung?`<div style="font-size:12px;color:var(--muted)">${r.noi_dung}</div>`:''}${r.van_de?`<div style="font-size:11px;color:#dc2626">⚠️ ${r.van_de}</div>`:''}</td>
    <td class="num">${_num(r.tien_do,1)}%</td><td>${r.ngay}</td><td style="font-size:12px;color:var(--muted)">${r.nguoi_tao||''}</td></tr>`).join('');
  html+=`<div class="panel"><div class="panel-h"><h3>Lịch sử báo cáo</h3></div><div class="panel-b"><table>
    <thead><tr><th>Kỳ</th><th>Tiêu đề</th><th class="num">Tiến độ</th><th>Ngày</th><th>Người lập</th></tr></thead>
    <tbody>${rows||'<tr><td colspan="5" class="empty">Chưa có báo cáo nào.</td></tr>'}</tbody></table></div></div>`;
  h.innerHTML=html;
}
async function daLapBaoCao(){
  const body={ky:gv('bc_ky')||null,tieu_de:gv('bc_td')||null,noi_dung:gv('bc_nd')||null,van_de:gv('bc_vd')||null};
  if(S.mode!=="live"){toast("Đã lập (demo)","ok");return;}
  try{const r=await api(`/du-an/${S.daId}/bao-cao`,{method:'POST',body:JSON.stringify(body)});toast(`Đã lập báo cáo · chốt tiến độ ${_num(r.tien_do,1)}%`,"ok");daRenderTab();}catch(e){toast(e.detail||e.message,"err");}
}

/* --- Demo dữ liệu dự án --- */
function _daDemoList(){return [{id:1,ma:"DA-2026-01",ten:"Trạm XLNT dệt nhuộm 1.200 m³/ngày",chu_dau_tu:"Công ty Dệt ABC",loai_du_an:"NUOC_THAI",cong_suat:"1.200 m³/ngày",tien_do:42.9,trang_thai:"DANG_CHAY",gia_tri_hop_dong:6190000000}];}
function _daDemoCt(){return {id:1,ma:"DA-2026-01",ten:"Trạm XLNT dệt nhuộm 1.200 m³/ngày",chu_dau_tu:"Công ty Dệt ABC",dia_diem:"KCN Tân Bình",loai_du_an:"NUOC_THAI",cong_suat:"1.200 m³/ngày",gia_tri_hop_dong:6190000000,qcvn:"QCVN 13",ngay_kt_ke_hoach:"2026-12-31",trang_thai:"DANG_CHAY",tien_do:42.9,mo_ta:"RO + AOP Fenton",so_moc:4,so_an_toan_mo:2,so_tai_lieu:5,so_kpi:3,so_nhat_ky:1,thiet_ke:{cong_nghe:"Tiền xử lý → DAF → MBR → RO → AOP Fenton",cong_suat_tk:"1.700 m³/ngày",tieu_chuan:"QCVN 13-MT:2015 cột A",thong_so:[{ten:"COD đầu vào",gia_tri:"1017",don_vi:"mg/L"}],nguoi_thiet_ke:"P. Kỹ thuật",phien_ban:"v1.0",trang_thai:"DA_DUYET"}};}
function _daDemoMoc(){return {tien_do:42.9,moc:[{id:1,thu_tu:1,ten:"Khảo sát & thiết kế",giai_doan:"THIET_KE",trong_so:1,phan_tram:100,trang_thai:"HOAN_THANH"},{id:2,thu_tu:2,ten:"Mua sắm thiết bị",giai_doan:"MUA_SAM",trong_so:2,phan_tram:100,trang_thai:"HOAN_THANH"},{id:3,thu_tu:3,ten:"Thi công lắp đặt",giai_doan:"THI_CONG",trong_so:3,phan_tram:0,trang_thai:"DANG_LAM"}]};}
function _daDemoAT(){return {tong:2,mo:2,theo_muc_rui_ro:{CAO:1,TRUNG:1,THAP:0},danh_sach:[{id:1,hang_muc:"Làm việc trong bể kín",moi_nguy:"Thiếu oxy, H2S",muc_rui_ro:"CAO",bien_phap:"Thông gió, đo khí",trang_thai:"MO"}]};}
function _daDemoTL(){return {theo_loai:{BAN_VE:1,THIET_BI:1,VAT_TU:1,BB_GIAO_NHAN:1,NGHIEM_THU:1},danh_sach:[{id:1,loai:"BAN_VE",ten:"Bản vẽ P&ID",ma_so:"DWG-001",phien_ban:"A",ngay:"2026-08-01",co_file:true}]};}
function _daDemoKPI(){return {binh_quan_dat:97.3,danh_sach:[{id:1,ten:"Tiến độ đúng hạn",don_vi:"%",chieu:"CAO",muc_tieu:100,thuc_te:95,trong_so:2,dat_phan_tram:95}]};}
function _daDemoBC(){return {tien_do:42.9,moc:{tong:4,theo_trang_thai:{HOAN_THANH:2}},an_toan:{tong:2,mo:2,theo_muc_rui_ro:{CAO:1,TRUNG:1}},tai_lieu:{tong:5,theo_loai:{BAN_VE:1}},kpi:{binh_quan_dat:97.3,so_kpi:3},ngan_sach:{du_toan:6000000000,chi_phi_thuc_te:3000000000,con_lai:3000000000,vuot:false}};}

/* ---------- Module khác (khung) ---------- */
function viewGeneric(m,mod){
  m.innerHTML=head(MODULES[mod].label, "Mức quyền của bạn: "+(LVL_LABEL[S.perm[pmod(mod)]]||S.perm[pmod(mod)]));
  m.innerHTML+=`<div class="panel"><div class="empty">
    <div class="big">Màn hình “${MODULES[mod].label}” đã có API đầy đủ ở backend</div>
    Lát cắt giao diện mẫu hiện minh họa Tổng quan, Kho và Bán hàng.<br>
    Các module còn lại dùng chung đúng khuôn này — mở <code>/docs</code> để xem ${countEndpoints(mod)} endpoint của module.
    <div style="margin-top:16px">${S.mode==="live"?`<a class="btn-sm" style="text-decoration:none" href="${S.api}/docs" target="_blank">Mở API docs</a>`:''}</div>
  </div></div>`;
}
function countEndpoints(){return "các";}
function head(title,sub){return `<div class="crumb">SVWS · ${S.roleName}</div>
  <div class="h-row"><h2>${title}</h2><p>${sub}</p></div>`;}
function logout(){S={mode:"demo",api:"",token:"",role:"",perm:{},page:"dashboard"};
  $("#app").classList.add('hidden');$("#login").classList.remove('hidden');$("#demoPill").classList.add('hidden');}

/* Enter để đăng nhập */
document.addEventListener('keydown',e=>{if(e.key==='Enter'&&!$("#login").classList.contains('hidden'))doLogin();});
</script>
</body>
</html>
