"""
theme.py — Tema Dark Navy Blue Premium untuk Dashboard DVRPTW
===============================================================
Desain profesional dengan estetika biru tua akademis untuk skripsi Farida Nuha.
Universitas Negeri Malang — Matematika
"""

BLUE_THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* ═══ OVERRIDE WARNA PRIMER STREAMLIT KE BIRU ═══ */
/* Pastikan semua elemen Streamlit menggunakan biru, bukan oranye */
:root {
    --primary-color: #2563EB !important;
}

/* ── Sidebar: Gradien Biru Gelap ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #090D1A 0%, #0F172A 60%, #1E293B 100%);
    padding-top: 1rem;
    border-right: 1px solid rgba(59,130,246,0.15);
}
section[data-testid="stSidebar"] * { color: #E2E8F0 !important; }
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color: #60A5FA !important; }

/* ── Menu Navigasi Sidebar: Tanpa Ikon, Bersih dan Modern ── */
div[data-testid="stSidebar"] div[role="radiogroup"] {
    gap: 6px !important;
    padding: 10px 0;
}
div[data-testid="stSidebar"] div[role="radiogroup"] label {
    background: rgba(30,41,59,0.7) !important;
    padding: 12px 18px !important;
    border-radius: 8px !important;
    margin-bottom: 2px !important;
    transition: all 0.25s ease !important;
    border: 1px solid rgba(255,255,255,0.05) !important;
    width: 100% !important;
    cursor: pointer !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
}

/* Sembunyikan SEMUA jenis penanda/bulatan/ikon bawaan dari radio button Streamlit */
div[data-testid="stSidebar"] div[role="radiogroup"] label [data-testid="stWidgetCustomComponentGlyph"],
div[data-testid="stSidebar"] div[role="radiogroup"] label input[type="radio"],
div[data-testid="stSidebar"] div[role="radiogroup"] label span[class*="Radio"],
div[data-testid="stSidebar"] div[role="radiogroup"] label [class*="radio"],
div[data-testid="stSidebar"] div[role="radiogroup"] label div[dir="ltr"],
div[data-testid="stSidebar"] div[role="radiogroup"] label span[data-baseweb="radio"],
div[data-testid="stSidebar"] div[role="radiogroup"] label svg {
    display: none !important;
    visibility: hidden !important;
    width: 0 !important;
    height: 0 !important;
    opacity: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}

/* Gaya teks label menu - Diposisikan di Tengah */
div[data-testid="stSidebar"] div[role="radiogroup"] label div[data-testid="stMarkdownContainer"] {
    margin-left: 0 !important;
    padding-left: 0 !important;
    text-align: center !important;
    width: 100% !important;
}
div[data-testid="stSidebar"] div[role="radiogroup"] label p {
    font-size: 14px !important;
    font-weight: 500 !important;
    color: #94A3B8 !important;
    margin: 0 !important;
    text-align: center !important;
    width: 100% !important;
}

/* Efek hover pada menu */
div[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    background: rgba(59,130,246,0.15) !important;
    border-color: rgba(96,165,250,0.3) !important;
    transform: translateX(4px);
}
div[data-testid="stSidebar"] div[role="radiogroup"] label:hover p {
    color: #60A5FA !important;
}

/* Menu yang sedang aktif/terpilih — BIRU SOLID PREMIUM */
div[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked),
div[data-testid="stSidebar"] div[role="radiogroup"] [data-checked="true"] {
    background: linear-gradient(90deg, #1D4ED8 0%, #2563EB 100%) !important;
    border-color: #3B82F6 !important;
    box-shadow: 0 4px 12px rgba(37,99,235,0.3) !important;
}
div[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p,
div[data-testid="stSidebar"] div[role="radiogroup"] [data-checked="true"] p {
    color: #FFFFFF !important;
    font-weight: 600 !important;
}

/* ── Tombol Utama: Gradien Biru ── */
div.stButton > button[kind="primary"], div.stButton > button {
    background: linear-gradient(135deg, #1D4ED8 0%, #2563EB 50%, #3B82F6 100%);
    color: white !important; font-weight: 600; font-size: 14px;
    border-radius: 10px; padding: 10px 24px;
    border: none; transition: all 0.3s ease;
    box-shadow: 0 4px 14px rgba(37,99,235,0.35);
    letter-spacing: 0.2px;
}
div.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(37,99,235,0.45);
}
div.stButton > button:active { transform: translateY(0); }

/* ── Kartu Metrik: Desain Premium ── */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%);
    border: 1px solid #E2E8F0; border-radius: 12px;
    padding: 16px 18px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
}
[data-testid="stMetric"] label { font-weight: 600 !important; color: #475569 !important; }
[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    color: #1E3A5F !important;
    font-weight: 700 !important;
}

/* ── Tab: BIRU KONSISTEN (bukan oranye) ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    border-bottom: 2px solid #E2E8F0;
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    border-radius: 8px 8px 0 0;
    padding: 10px 18px;
    font-weight: 500;
    font-size: 13px;
    border-bottom: 3px solid transparent !important;
    color: #64748B !important;
}
.stTabs [aria-selected="true"] {
    background: #EFF6FF !important;
    color: #1E40AF !important;
    border-bottom: 3px solid #2563EB !important;
    font-weight: 600;
}
/* Override garis bawah tab bawaan Streamlit */
.stTabs [data-baseweb="tab-highlight"] {
    background-color: #2563EB !important;
}

/* ── Checkbox & Slider: Warna Biru ── */
.stCheckbox label span[data-baseweb="checkbox"] {
    border-color: #2563EB !important;
}
.stCheckbox label span[data-baseweb="checkbox"][aria-checked="true"] {
    background-color: #2563EB !important;
    border-color: #2563EB !important;
}
.stSlider [data-baseweb="slider"] div[role="slider"] {
    background-color: #2563EB !important;
}
div[data-baseweb="slider"] > div > div > div {
    background: #2563EB !important;
}

/* ── Tabel Data ── */
.stDataFrame, [data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }

/* ── Expander ── */
details[data-testid="stExpander"] {
    border: 1px solid #DBEAFE; border-radius: 10px;
    background: #FAFBFF;
}

/* ── Garis Pemisah ── */
hr {
    border: none; height: 1px;
    background: linear-gradient(90deg, transparent, #93C5FD, transparent);
    margin: 1.5rem 0;
}

/* ── Spanduk Hero ── */
.hero-banner {
    background: linear-gradient(135deg, #0B1120 0%, #0F2744 35%, #1E3A5F 65%, #1E40AF 100%);
    padding: 32px 28px; border-radius: 16px;
    margin-bottom: 1.5rem;
    box-shadow: 0 8px 32px rgba(11,17,32,0.25);
    border: 1px solid rgba(59,130,246,0.12);
}
.hero-banner .hero-title, .hero-banner h1 {
    font-size: 24px; font-weight: 800; color: #F1F5F9 !important;
    margin: 0 0 4px 0; letter-spacing: -0.3px;
}
.hero-banner .subtitle {
    font-size: 14px; color: #60A5FA;
    letter-spacing: 2px; text-transform: uppercase;
    margin: 0;
}
.hero-banner .author {
    font-size: 13px; color: #94A3B8; margin-top: 12px;
}
.hero-banner .divider {
    width: 48px; height: 2px; margin: 12px 0;
    background: linear-gradient(90deg, #3B82F6, #60A5FA);
}

/* ── Cover Page: Layar Penuh Profesional ── */
.cover-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 80vh;
    text-align: center;
    padding: 60px 20px;
}
.cover-card {
    background: linear-gradient(145deg, #0B1120 0%, #0F2744 30%, #162D50 60%, #1E3A5F 100%);
    border-radius: 24px;
    padding: 60px 50px;
    max-width: 720px;
    width: 100%;
    box-shadow:
        0 25px 50px -12px rgba(0, 0, 0, 0.4),
        0 0 0 1px rgba(59, 130, 246, 0.1),
        inset 0 1px 0 rgba(255, 255, 255, 0.05);
    position: relative;
    overflow: hidden;
}
.cover-card::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -50%;
    width: 100%;
    height: 100%;
    background: radial-gradient(circle, rgba(59,130,246,0.08) 0%, transparent 70%);
    pointer-events: none;
}
.cover-badge {
    display: inline-block;
    background: rgba(59,130,246,0.15);
    color: #60A5FA;
    font-size: 14px;
    font-weight: 600;
    letter-spacing: 3px;
    text-transform: uppercase;
    padding: 6px 16px;
    border-radius: 20px;
    border: 1px solid rgba(59,130,246,0.25);
    margin-bottom: 24px;
}
.cover-title {
    font-size: 32px;
    font-weight: 800;
    color: #FFFFFF !important;
    line-height: 1.2;
    margin: 0 0 16px 0;
    letter-spacing: -0.5px;
}
.cover-subtitle {
    font-size: 15px;
    color: #E2E8F0 !important;
    margin: 0 0 32px 0;
    line-height: 1.6;
}
.cover-line {
    width: 60px;
    height: 3px;
    background: linear-gradient(90deg, #3B82F6, #60A5FA, #93C5FD);
    margin: 0 auto 32px;
    border-radius: 2px;
}
.cover-info {
    display: flex;
    justify-content: center;
    gap: 32px;
    margin-bottom: 36px;
    flex-wrap: wrap;
}
.cover-info-item {
    text-align: center;
}
.cover-info-label {
    font-size: 14px;
    color: #94A3B8 !important;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 4px;
}
.cover-info-value {
    font-size: 17px;
    color: #FFFFFF !important;
    font-weight: 600;
}
.cover-algo {
    display: flex;
    justify-content: center;
    gap: 12px;
    flex-wrap: wrap;
    margin-bottom: 8px;
}
.cover-algo-tag {
    background: rgba(30, 64, 175, 0.2);
    color: #93C5FD !important;
    font-size: 14px;
    font-weight: 500;
    padding: 5px 12px;
    border-radius: 6px;
    border: 1px solid rgba(59, 130, 246, 0.15);
}
.cover-footer {
    font-size: 14px;
    color: #64748B !important;
    margin-top: 28px;
}
</style>
""";

# Spanduk utama yang muncul di setiap halaman dashboard
HERO_BANNER = """
<div class="hero-banner">
    <div class="subtitle" style="color: #60A5FA !important;">Dynamic Vehicle Routing Problem with Time Windows</div>
    <div class="hero-title" style="font-size: 32px; font-weight: 800; color: #FFFFFF !important; margin: 0 0 4px 0; letter-spacing: -0.3px;">DVRPTW Optimizer Dashboard</div>
    <div class="divider"></div>
    <div class="author" style="color: #94A3B8 !important; font-size: 15px;">Farida Nuha · Universitas Negeri Malang — Matematika</div>
</div>
"""

# Halaman cover profesional
COVER_PAGE = """
<div class="cover-container">
    <div class="cover-card">
        <div class="cover-badge" style="color: #60A5FA !important;">Skripsi · Matematika · 2026</div>
        <div class="cover-title" style="color: #FFFFFF !important; font-size: 40px; font-weight: 800; line-height: 1.2; margin: 0 0 16px 0; letter-spacing: -0.5px;">Dynamic Vehicle Routing Problem<br>with Time Windows</div>
        <div class="cover-line"></div>
        <div class="cover-subtitle" style="color: #E2E8F0 !important; font-size: 18px; margin: 0 0 32px 0; line-height: 1.6;">
            Optimasi Rute Distribusi Kendaraan Dinamis dengan Batasan Waktu
            Menggunakan Kombinasi Metode Nearest Neighbor, Cheapest Insertion,
            dan Randomized Variable Neighborhood Descent (RVND)
        </div>
        <div class="cover-info">
            <div class="cover-info-item">
                <div class="cover-info-label" style="color: #94A3B8 !important;">Penulis</div>
                <div class="cover-info-value" style="color: #FFFFFF !important;">Farida Nuha</div>
            </div>
            <div class="cover-info-item">
                <div class="cover-info-label" style="color: #94A3B8 !important;">Program Studi</div>
                <div class="cover-info-value" style="color: #FFFFFF !important;">Matematika</div>
            </div>
            <div class="cover-info-item">
                <div class="cover-info-label" style="color: #94A3B8 !important;">Universitas</div>
                <div class="cover-info-value" style="color: #FFFFFF !important;">Universitas Negeri Malang</div>
            </div>
        </div>
        <div class="cover-algo">
            <span class="cover-algo-tag" style="color: #93C5FD !important;">Nearest Neighbor Heuristic</span>
            <span class="cover-algo-tag" style="color: #93C5FD !important;">Cheapest Insertion</span>
            <span class="cover-algo-tag" style="color: #93C5FD !important;">RVND Local Search</span>
        </div>
        <div class="cover-footer" style="color: #64748B !important;">DVRPTW Optimizer Dashboard · 2026</div>
    </div>
</div>
"""

# Header sidebar: identitas aplikasi
SIDEBAR_HEADER = """
<div style="text-align:center; padding: 16px 8px 8px;">
    <div style="
        font-size: 18px; letter-spacing: 3px; text-transform: uppercase;
        color: #60A5FA !important; margin-bottom: 4px;
    ">DVRPTW</div>
    <div style="font-size: 24px; font-weight: 700; color: #F1F5F9 !important;">
        Optimizer
    </div>
    <div style="
        width: 32px; height: 2px; margin: 8px auto;
        background: linear-gradient(90deg, #3B82F6, #60A5FA);
    "></div>
</div>
"""

# Footer sidebar: keterangan algoritma dan penulis
SIDEBAR_FOOTER = """
<div style="
    margin-top: 1.5rem; padding: 10px;
    background: rgba(30,64,175,0.08); border-radius: 8px;
    border: 1px solid rgba(59,130,246,0.15); text-align: center;
">
    <div style="font-size: 14px; margin: 0; opacity: 0.7; color: #94A3B8 !important;">
        Nearest Neighbor + RVND<br>Farida Nuha · 2026
    </div>
</div>
"""

# Palet warna untuk membedakan rute kendaraan pada grafik
ROUTE_COLORS = [
    "#1E40AF", "#DC2626", "#059669", "#D97706",
    "#7C3AED", "#DB2777", "#0891B2", "#65A30D",
    "#EA580C", "#4338CA", "#0D9488", "#BE185D",
]

