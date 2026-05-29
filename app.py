"""
app.py — Dashboard DVRPTW (Nuha Bahiyya Al Faridha)
=========================================
Aplikasi Streamlit untuk optimasi rute kendaraan dinamis
(Dynamic Vehicle Routing Problem with Time Windows).

Algoritma: Sequential Insertion + Cheapest Insertion + ILS (Local Search + RVND + Perturbasi).
Penulis  : Nuha Bahiyya Al Faridha (NIM: 220312609348)
Universitas Negeri Malang — Matematika
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import time as _time
import json as _json
import copy
import math
import os
from solver import (
    Customer, Depot, Route,
    route_distance, route_time,
    total_distance, total_time,
    get_route_arrival_times,
    run_dvrptw_simulation,
    update_route_metrics,
)
from theme import (
    BLUE_THEME_CSS, HERO_BANNER, COVER_PAGE,
    SIDEBAR_HEADER, SIDEBAR_FOOTER,
    ROUTE_COLORS,
)


# ─── Konfigurasi Caching Lokal (Persistensi Data) ───
# Dinamisasi path agar portabel (otomatis mendeteksi folder lokasi file app.py saat ini)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(CURRENT_DIR, "_data", "active_session_cache.json")

def save_session_cache():
    cache_data = {}
    for k in ["n_cust", "depot_open", "depot_close", "capacity", "speed", "max_vehicles"]:
        if k in st.session_state:
            cache_data[k] = st.session_state[k]
            
    # Serialize dataframes
    if st.session_state.cust_df is not None:
        cache_data["cust_df"] = st.session_state.cust_df.to_dict(orient="records")
    else:
        cache_data["cust_df"] = None
        
    if st.session_state.dyn_df is not None:
        cache_data["dyn_df"] = st.session_state.dyn_df.to_dict(orient="records")
    else:
        cache_data["dyn_df"] = None
        
    if st.session_state.dist_mx is not None:
        cache_data["dist_mx"] = st.session_state.dist_mx.to_dict(orient="split")
    else:
        cache_data["dist_mx"] = None
        
    if st.session_state.time_mx is not None:
        cache_data["time_mx"] = st.session_state.time_mx.to_dict(orient="split")
    else:
        cache_data["time_mx"] = None

    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w") as f:
            _json.dump(cache_data, f, indent=4)
    except Exception as e:
        print(f"Error saving cache: {e}")

def load_session_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                cache_data = _json.load(f)
            for k in ["n_cust", "depot_open", "depot_close", "capacity", "speed", "max_vehicles"]:
                if k in cache_data:
                    st.session_state[k] = cache_data[k]
            
            if cache_data.get("cust_df") is not None:
                st.session_state.cust_df = pd.DataFrame(cache_data["cust_df"])
            if cache_data.get("dyn_df") is not None:
                st.session_state.dyn_df = pd.DataFrame(cache_data["dyn_df"])
                
            if cache_data.get("dist_mx") is not None:
                split_dist = cache_data["dist_mx"]
                st.session_state.dist_mx = pd.DataFrame(
                    split_dist["data"],
                    columns=split_dist["columns"],
                    index=split_dist["index"]
                )
            if cache_data.get("time_mx") is not None:
                split_time = cache_data["time_mx"]
                st.session_state.time_mx = pd.DataFrame(
                    split_time["data"],
                    columns=split_time["columns"],
                    index=split_time["index"]
                )
        except Exception as e:
            print(f"Error loading cache: {e}")


def solve_2d_positions(dist_matrix):
    """
    Classic Multi-Dimensional Scaling (MDS)
    Memetakan matriks jarak N x N menjadi koordinat 2D (N x 2)
    agar rasio jarak spasial di peta akurat mencerminkan matriks jarak sesungguhnya.
    """
    n = len(dist_matrix)
    # Centering matrix
    H = np.eye(n) - np.ones((n, n)) / n
    # Double centering
    B = -0.5 * H.dot(dist_matrix ** 2).dot(H)
    # Eigenvalue decomposition
    evals, evecs = np.linalg.eigh(B)
    # Urutkan eigen dari terbesar ke terkecil
    idx = np.argsort(evals)[::-1]
    evals = evals[idx]
    evecs = evecs[:, idx]
    # Ambil dua komponen utama pertama
    X = evecs[:, :2] * np.sqrt(np.maximum(evals[:2], 1e-5))
    return X


def format_hours_to_hms(decimal_hours: float) -> str:
    """
    Konversi jam desimal (e.g. 0.9005 jam) ke format human-readable 
    'X jam Y menit Z detik' atau 'Y menit Z detik'.
    """
    if decimal_hours <= 0:
        return "0 detik"
    
    total_seconds = int(round(decimal_hours * 3600))
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    parts = []
    if hours > 0:
        parts.append(f"{hours} jam")
    if minutes > 0:
        parts.append(f"{minutes} menit")
    if seconds > 0 or not parts:
        parts.append(f"{seconds} detik")
        
    return " ".join(parts)


# ─── Konfigurasi Halaman ───
st.set_page_config(
    page_title="DVRPTW | Nuha Bahiyya Al Faridha",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(BLUE_THEME_CSS, unsafe_allow_html=True)


# ─── Inisialisasi Session State ───
_defaults = {
    "n_cust": 7,
    "depot_open": 4.0,
    "depot_close": 7.0,
    "capacity": 2500,
    "speed": 60.0,
    "max_vehicles": 2,
    "cust_df": None,
    "dyn_df": None,
    "dist_mx": None,
    "time_mx": None,
    "sim_result": None,
    "sim_unopt_result": None,
    "sim_opt_result": None,
    "entered_dashboard": False,  # kontrol apakah sudah melewati cover page
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

load_session_cache()


# ═══════════════════════════════════════════════════
# COVER PAGE — Halaman Pembuka Profesional
# ═══════════════════════════════════════════════════
if not st.session_state.entered_dashboard:
    # Sembunyikan sidebar saat di cover page
    st.markdown("""
    <style>
    section[data-testid="stSidebar"] { display: none; }
    [data-testid="stSidebarCollapsedControl"] { display: none; }
    .stMainBlockContainer { max-width: 100% !important; padding: 0 !important; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(COVER_PAGE, unsafe_allow_html=True)

    # Tombol masuk dashboard — posisi tengah
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("Masuk ke Dashboard", use_container_width=True):
            st.session_state.entered_dashboard = True
            st.rerun()

    st.stop()  # Hentikan eksekusi di sini jika belum masuk dashboard


# ═══════════════════════════════════════════════════
# DASHBOARD UTAMA (setelah melewati cover page)
# ═══════════════════════════════════════════════════

# ─── Sidebar Navigasi ───
st.sidebar.markdown(SIDEBAR_HEADER, unsafe_allow_html=True)
st.sidebar.markdown("---")
menu = st.sidebar.radio("Menu", [
    "🏠 Beranda",
    "👥 Data Pelanggan",
    "🚚 Konfigurasi Armada",
    "⚙️ Simulasi DVRPTW",
    "📊 Analisis Hasil",
], label_visibility="collapsed")
st.sidebar.markdown("---")
if st.sidebar.button("⬅️ Kembali ke Cover Page", use_container_width=True):
    st.session_state.entered_dashboard = False
    st.rerun()

if st.sidebar.button("⚠️ Reset Semua Data", use_container_width=True):
    entered = st.session_state.entered_dashboard
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.session_state.entered_dashboard = entered
    if os.path.exists(CACHE_FILE):
        try:
            os.remove(CACHE_FILE)
        except Exception:
            pass
    st.rerun()
st.sidebar.markdown(SIDEBAR_FOOTER, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════
# HALAMAN: BERANDA
# ═══════════════════════════════════════════════════
if menu == "🏠 Beranda":
    st.markdown(HERO_BANNER, unsafe_allow_html=True)
    st.markdown("### Tentang Aplikasi")
    st.markdown("""
    Aplikasi ini menyelesaikan **Dynamic Vehicle Routing Problem with Time Windows (DVRPTW)** —
    sebuah permasalahan optimasi rute kendaraan di mana **pesanan pelanggan dapat muncul secara
    dinamis** selama proses distribusi berlangsung.

    Permasalahan diselesaikan dengan kombinasi metode optimasi metaheuristik:
    - **Sequential Insertion Heuristic** untuk konstruksi solusi awal dari pelanggan statis.
    - **Cheapest Insertion** untuk penyisipan pelanggan dinamis ke rute yang sudah berjalan secara real-time.
    - **Iterated Local Search (ILS)** yang mengombinasikan **Local Search deterministik**, **RVND (Randomized Variable Neighborhood Descent)**, dan **Perturbasi** untuk meminimalkan total jarak tempuh secara optimal.
    """)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("#### Sequential Insertion")
        st.caption(
            "Membangun rute awal dengan menyisipkan pelanggan belum dikunjungi secara sekuensial "
            "ke posisi terbaik di rute berjalan dengan biaya tambahan paling minimal."
        )
    with c2:
        st.markdown("#### Cheapest Insertion")
        st.caption(
            "Penyisipan otomatis pesanan dinamis ke posisi termurah dalam "
            "rute yang sudah berjalan, tanpa mengganggu node committed."
        )
    with c3:
        st.markdown("#### Metaheuristik ILS & RVND")
        st.caption(
            "Optimasi berlapis menggunakan Local Search (2-Opt, Or-Opt, Exchange), RVND (5 struktur lingkungan), "
            "dan Perturbasi acak untuk membebaskan solusi dari optimum lokal."
        )

    st.markdown("---")
    st.markdown("#### Batasan Model DVRPTW")
    st.markdown("""
    - Setiap rute kendaraan dimulai dan diakhiri di **depot pusat** (node 0).
    - Setiap pelanggan hanya dilayani **tepat satu kali** oleh satu kendaraan.
    - Armada kendaraan bersifat **homogen** — 2 kendaraan dengan kapasitas masing-masing 2500 kg.
    - Menggunakan **kecepatan rata-rata** kendaraan; efek kemacetan diabaikan.
    - Setiap pelanggan memiliki **service time** (durasi pelayanan) tertentu.
    - **Non-preemption**: kendaraan tidak boleh putar balik di tengah jalan.
    - Pelanggan dinamis disisipkan ke posisi layak setelah node yang sudah dikunjungi.
    - **Tujuan**: Meminimalkan total jarak tempuh seluruh armada kendaraan.
    """)


# ═══════════════════════════════════════════════════
# HALAMAN: DATA PELANGGAN
# ═══════════════════════════════════════════════════
elif menu == "👥 Data Pelanggan":
    st.markdown(HERO_BANNER, unsafe_allow_html=True)
    st.markdown("### 📥 Upload Berkas Data DVRPTW")
    st.caption(
        "Upload file JSON yang berisi data pelanggan (statis & dinamis), matriks jarak, dan matriks waktu. "
        "Seluruh data akan langsung dimuat secara otomatis di bawah ini."
    )
    
    up = st.file_uploader("Pilih Berkas JSON", type=["json"], label_visibility="collapsed")
    if up:
        try:
            raw = _json.loads(up.read())
            if isinstance(raw, dict) and "customers" in raw:
                cust_list = raw["customers"]
                df = pd.DataFrame(cust_list)
                if "Service Time (detik)" in df.columns:
                    df["Service Time (jam)"] = (df["Service Time (detik)"] / 3600.0).round(6)
                st.session_state.cust_df = df
                st.session_state.n_cust = len(df)

                if "depot" in raw:
                    dep = raw["depot"]
                    st.session_state.depot_open = float(dep.get("tw_open", 4.0))
                    st.session_state.depot_close = float(dep.get("tw_close", 7.0))
                    st.session_state.capacity = int(dep.get("capacity", 2500))
                    st.session_state.speed = float(dep.get("speed", 60.0))
                    st.session_state.max_vehicles = int(dep.get("max_vehicles", 2))

                if "distance_matrix" in raw:
                    dmx_arr = np.array(raw["distance_matrix"])
                    nn = len(dmx_arr)
                    st.session_state.dist_mx = pd.DataFrame(
                        dmx_arr,
                        columns=[str(i) for i in range(nn)],
                        index=[str(i) for i in range(nn)],
                    )

                if "time_matrix" in raw:
                    tmx_arr = np.array(raw["time_matrix"])
                    nn = len(tmx_arr)
                    st.session_state.time_mx = pd.DataFrame(
                        tmx_arr,
                        columns=[str(i) for i in range(nn)],
                        index=[str(i) for i in range(nn)],
                    )

                if "dynamic_customers" in raw and raw["dynamic_customers"]:
                    dyn_df = pd.DataFrame(raw["dynamic_customers"])
                    if "Service Time (detik)" in dyn_df.columns:
                        dyn_df["Service Time (jam)"] = (dyn_df["Service Time (detik)"] / 3600.0).round(6)
                    st.session_state.dyn_df = dyn_df
                else:
                    st.session_state.dyn_df = None

                # Reset hasil simulasi sebelumnya agar tidak stale
                st.session_state.sim_result = None
                st.session_state.sim_el = None
                st.session_state.sim_c = None
                st.session_state.sim_d = None
                st.session_state.sim_t = None
                st.session_state.sim_dep = None

                save_session_cache()
                st.success(f"✅ Data berhasil dimuat dari **{up.name}**!")
            else:
                st.error("Format JSON tidak valid. Pastikan ada kunci 'customers'.")
        except Exception as e:
            st.error(f"Gagal memproses file: {e}")

    # Cek apakah ada data aktif di session state
    if st.session_state.cust_df is not None:
        st.markdown("---")
        
        # 📊 Ringkasan Data Aktif
        n_st = len(st.session_state.cust_df)
        n_dyn = len(st.session_state.dyn_df) if st.session_state.dyn_df is not None else 0
        
        st.markdown("#### 📊 Ringkasan Dataset Aktif")
        c1, c2, c3 = st.columns(3)
        c1.metric("Pelanggan Statis", f"{n_st} Pelanggan")
        c2.metric("Pelanggan Dinamis", f"{n_dyn} Pelanggan")
        c3.metric("Total Pelanggan Terdaftar", f"{n_st + n_dyn} Pelanggan")
        
        st.markdown("---")
        
        # 🔵 Data Pelanggan Statis
        st.markdown("### 🔵 Data Pelanggan Statis")
        st.caption(
            "Pelanggan statis adalah pelanggan yang pesanannya sudah diketahui sejak awal operasional."
        )
        
        with st.expander("⚙️ Pengaturan Manual Jumlah Pelanggan Statis"):
            n = st.number_input(
                "Atur Jumlah Pelanggan Statis", 1, 200,
                st.session_state.n_cust, key="n_static"
            )
            if len(st.session_state.cust_df) != n:
                st.session_state.cust_df = pd.DataFrame({
                    "Customer": range(1, n + 1),
                    "Demand": [0] * n,
                    "Service Time (detik)": [0] * n,
                    "Service Time (jam)": [0.0] * n,
                    "Reveal Time (jam)": [st.session_state.depot_open] * n,
                })
                st.session_state.n_cust = n
                save_session_cache()
                st.rerun()

        cols_to_keep = [
            "Customer", "Demand", "Service Time (detik)",
            "Service Time (jam)", "Reveal Time (jam)",
        ]
        for col in cols_to_keep:
            if col not in st.session_state.cust_df.columns:
                if col == "Reveal Time (jam)":
                    st.session_state.cust_df[col] = st.session_state.depot_open
                elif col == "Service Time (jam)":
                    if "Service Time (detik)" in st.session_state.cust_df.columns:
                        st.session_state.cust_df[col] = (st.session_state.cust_df["Service Time (detik)"] / 3600.0).round(6)
                    else:
                        st.session_state.cust_df[col] = 0.0
                else:
                    st.session_state.cust_df[col] = 0

        st.session_state.cust_df = st.session_state.cust_df[cols_to_keep]

        edited_cust = st.data_editor(
            st.session_state.cust_df,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Customer": st.column_config.NumberColumn("ID Pelanggan", disabled=True),
                "Demand": st.column_config.NumberColumn("Demand (kg)", min_value=0),
                "Service Time (detik)": st.column_config.NumberColumn(
                    "Service Time (detik)", min_value=0
                ),
                "Service Time (jam)": st.column_config.NumberColumn(
                    "Service Time (jam)", format="%.4f", disabled=True
                ),
                "Reveal Time (jam)": st.column_config.NumberColumn(
                    "Reveal Time (jam)", format="%.2f", disabled=True,
                    help="Reveal time = jam buka depot."
                ),
            },
            key="cust_editor"
        )
        
        # Cek dan simpan jika ada perubahan
        if not edited_cust.equals(st.session_state.cust_df):
            st.session_state.cust_df = edited_cust
            if "Service Time (detik)" in st.session_state.cust_df.columns:
                st.session_state.cust_df["Service Time (jam)"] = (st.session_state.cust_df["Service Time (detik)"] / 3600).round(6)
            save_session_cache()
            st.rerun()

        df = st.session_state.cust_df
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Demand Statis", f"{int(df['Demand'].sum())} kg")
        c2.metric("Rata-rata Demand Statis", f"{df['Demand'].mean():.1f} kg")
        c3.metric("Kapasitas Armada Tersedia", f"{st.session_state.capacity} kg/mobil")

        st.markdown("---")

        # 🔴 Data Pelanggan Dinamis
        st.markdown("### 🔴 Data Pelanggan Dinamis")
        st.caption(
            "Pelanggan dinamis adalah pelanggan yang pesanannya muncul setelah kendaraan sudah berangkat. "
            "Pesanan disisipkan menggunakan Cheapest Insertion."
        )
        
        with st.expander("⚙️ Pengaturan Manual Jumlah Pelanggan Dinamis"):
            n_dyn_input = st.number_input(
                "Atur Jumlah Pelanggan Dinamis", 0, 50,
                n_dyn, key="n_dynamic"
            )
            if (st.session_state.dyn_df is None and n_dyn_input > 0) or (st.session_state.dyn_df is not None and len(st.session_state.dyn_df) != n_dyn_input):
                if n_dyn_input > 0:
                    start_id = st.session_state.n_cust + 1
                    st.session_state.dyn_df = pd.DataFrame({
                        "Customer": range(start_id, start_id + n_dyn_input),
                        "Demand": [0] * n_dyn_input,
                        "Service Time (detik)": [0] * n_dyn_input,
                        "Service Time (jam)": [0.0] * n_dyn_input,
                        "Reveal Time (jam)": [st.session_state.depot_open + 0.5] * n_dyn_input,
                    })
                else:
                    st.session_state.dyn_df = None
                save_session_cache()
                st.rerun()

        if st.session_state.dyn_df is not None and len(st.session_state.dyn_df) > 0:
            dyn_cols = [
                "Customer", "Demand", "Service Time (detik)",
                "Service Time (jam)", "Reveal Time (jam)",
            ]
            for col in dyn_cols:
                if col not in st.session_state.dyn_df.columns:
                    if col == "Reveal Time (jam)":
                        st.session_state.dyn_df[col] = st.session_state.depot_open + 0.5
                    elif col == "Service Time (jam)":
                        if "Service Time (detik)" in st.session_state.dyn_df.columns:
                            st.session_state.dyn_df[col] = (st.session_state.dyn_df["Service Time (detik)"] / 3600.0).round(6)
                        else:
                            st.session_state.dyn_df[col] = 0.0
                    else:
                        st.session_state.dyn_df[col] = 0

            st.session_state.dyn_df = st.session_state.dyn_df[dyn_cols]

            edited_dyn = st.data_editor(
                st.session_state.dyn_df,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Customer": st.column_config.NumberColumn("ID Pelanggan", disabled=True),
                    "Demand": st.column_config.NumberColumn("Demand (kg)", min_value=0),
                    "Service Time (detik)": st.column_config.NumberColumn(
                        "Service Time (detik)", min_value=0
                    ),
                    "Service Time (jam)": st.column_config.NumberColumn(
                        "Service Time (jam)", format="%.4f", disabled=True
                    ),
                    "Reveal Time (jam)": st.column_config.NumberColumn(
                        "Reveal Time (jam)", format="%.2f",
                        help="Jam pesanan masuk ke sistem. Harus > jam buka depot."
                    ),
                },
                key="dyn_editor"
            )
            
            if not edited_dyn.equals(st.session_state.dyn_df):
                st.session_state.dyn_df = edited_dyn
                if "Service Time (detik)" in st.session_state.dyn_df.columns:
                    st.session_state.dyn_df["Service Time (jam)"] = (st.session_state.dyn_df["Service Time (detik)"] / 3600).round(6)
                save_session_cache()
                st.rerun()

            dfd = st.session_state.dyn_df
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Demand Dinamis", f"{int(dfd['Demand'].sum())} kg")
            c2.metric("Rata-rata Demand Dinamis", f"{dfd['Demand'].mean():.1f} kg")
            c3.metric("Maksimum Reveal Time", f"{dfd['Reveal Time (jam)'].max():.2f} jam")
        else:
            st.info("ℹ️ Tidak ada pelanggan dinamis aktif dalam data.")

        st.markdown("---")

        # 🗺️ Matriks Jarak & Matriks Waktu
        st.markdown("### 🗺️ Matriks Jarak & Matriks Waktu Tempuh")
        st.caption(
            "Matriks jarak (km) dan matriks waktu tempuh (jam) antar seluruh node (Node 0 = Depot Pusat)."
        )

        nn = st.session_state.n_cust + 1
        if st.session_state.dyn_df is not None and len(st.session_state.dyn_df) > 0:
            nn = st.session_state.n_cust + len(st.session_state.dyn_df) + 1

        if st.session_state.dist_mx is None or st.session_state.dist_mx.shape != (nn, nn):
            st.session_state.dist_mx = pd.DataFrame(
                np.zeros((nn, nn)),
                columns=[str(i) for i in range(nn)],
                index=[str(i) for i in range(nn)],
            )
        if st.session_state.time_mx is None or st.session_state.time_mx.shape != (nn, nn):
            st.session_state.time_mx = pd.DataFrame(
                np.zeros((nn, nn)),
                columns=[str(i) for i in range(nn)],
                index=[str(i) for i in range(nn)],
            )

        col_dist, col_time = st.columns(2)
        with col_dist:
            st.markdown("#### Matriks Jarak (km)")
            edited_dist = st.data_editor(
                st.session_state.dist_mx,
                use_container_width=True,
                key="dist_editor",
                height=min(320, 36 * nn + 40),
            )
            if not edited_dist.equals(st.session_state.dist_mx):
                st.session_state.dist_mx = edited_dist
                save_session_cache()
                st.rerun()

        with col_time:
            st.markdown("#### Matriks Waktu (jam)")
            edited_time = st.data_editor(
                st.session_state.time_mx,
                use_container_width=True,
                key="time_editor",
                height=min(320, 36 * nn + 40),
            )
            if not edited_time.equals(st.session_state.time_mx):
                st.session_state.time_mx = edited_time
                save_session_cache()
                st.rerun()
    else:
        st.info("ℹ️ Silakan upload file JSON data DVRPTW di atas untuk menampilkan isi tabel secara langsung.")


# ═══════════════════════════════════════════════════
# HALAMAN: KONFIGURASI ARMADA
# ═══════════════════════════════════════════════════
elif menu == "🚚 Konfigurasi Armada":
    st.markdown(HERO_BANNER, unsafe_allow_html=True)
    st.markdown("### Parameter Depot dan Kendaraan")
    ca, cb = st.columns(2, gap="large")
    with ca:
        st.markdown("#### Depot Pusat")
        st.session_state.depot_open = st.number_input(
            "Jam Buka Depot (e₀)", 0.0, 24.0, st.session_state.depot_open,
            help="Format desimal. Contoh: 4.0 = pukul 04:00"
        )
        st.session_state.depot_close = st.number_input(
            "Jam Tutup Depot (l₀)", 0.0, 24.0, st.session_state.depot_close,
        )
    with cb:
        st.markdown("#### Armada Kendaraan (Homogen)")
        st.session_state.capacity = st.number_input(
            "Kapasitas per Kendaraan (Q) dalam kg", 1, 99999, st.session_state.capacity,
            help="Kapasitas muatan TIAP kendaraan, bukan total gabungan."
        )
        st.session_state.speed = st.number_input(
            "Kecepatan Rata-rata (km/jam)", 1.0, 200.0, st.session_state.speed,
        )
        st.session_state.max_vehicles = st.number_input(
            "Jumlah Kendaraan Tersedia", 1, 50, st.session_state.max_vehicles,
        )

    tw = st.session_state.depot_close - st.session_state.depot_open
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Durasi Operasional", f"{tw:.1f} jam")
    c2.metric("Kapasitas/Kendaraan", f"{st.session_state.capacity} kg")
    c3.metric("Kecepatan Rata-rata", f"{st.session_state.speed} km/jam")
    c4.metric("Jumlah Kendaraan", st.session_state.max_vehicles)

    total_cap = st.session_state.capacity * st.session_state.max_vehicles
    st.info(
        f"Total kapasitas seluruh armada: **{total_cap:,} kg** "
        f"({st.session_state.max_vehicles} kendaraan × "
        f"{st.session_state.capacity:,} kg/kendaraan)"
    )


# ═══════════════════════════════════════════════════
# HALAMAN: SIMULASI DVRPTW
# ═══════════════════════════════════════════════════
elif menu == "⚙️ Simulasi DVRPTW":
    st.markdown(HERO_BANNER, unsafe_allow_html=True)
    cdf = st.session_state.cust_df
    dmx = st.session_state.dist_mx
    tmx = st.session_state.time_mx
    dyn_df = st.session_state.dyn_df

    errs = []
    if cdf is None or len(cdf) == 0:
        errs.append("Tabel data pelanggan statis belum diisi.")
    elif cdf["Demand"].sum() == 0:
        errs.append("Demand pelanggan statis masih bernilai 0.")
    if dmx is None or dmx.to_numpy().max() == 0:
        errs.append("Matriks jarak belum terisi.")
    if tmx is None or tmx.to_numpy().max() == 0:
        errs.append("Matriks waktu tempuh belum terisi.")

    if errs:
        for e in errs:
            st.warning(f"⚠️ {e}")
        st.info("Mohon lengkapi data terlebih dahulu di halaman **Data Pelanggan**.")
    else:
        depot = Depot(
            tw_open=st.session_state.depot_open,
            tw_close=st.session_state.depot_close,
            capacity=st.session_state.capacity,
            speed=st.session_state.speed,
            max_vehicles=st.session_state.max_vehicles,
        )

        custs = {}
        for _, r in cdf.iterrows():
            cid = int(r["Customer"])
            custs[cid] = Customer(
                id=cid,
                demand=float(r["Demand"]),
                service_time=float(r.get("Service Time (jam)", 0)),
                is_dynamic=False,
                reveal_time=depot.tw_open,
            )

        n_dynamic = 0
        if dyn_df is not None and len(dyn_df) > 0:
            for _, r in dyn_df.iterrows():
                cid = int(r["Customer"])
                rev_time = float(r.get("Reveal Time (jam)", depot.tw_open + 0.5))
                custs[cid] = Customer(
                    id=cid,
                    demand=float(r["Demand"]),
                    service_time=float(r.get("Service Time (jam)", 0)),
                    is_dynamic=True,
                    reveal_time=rev_time,
                )
                n_dynamic += 1

        dist = dmx.to_numpy().astype(float)
        tmtx = tmx.to_numpy().astype(float)

        ns = sum(1 for c in custs.values() if not c.is_dynamic)
        nd = sum(1 for c in custs.values() if c.is_dynamic)

        st.markdown("### Ringkasan Pelanggan Terdaftar")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Pelanggan Statis", ns)
        c2.metric("Pelanggan Dinamis", nd)
        c3.metric("Total Pelanggan", ns + nd)
        c4.metric("Total Demand", f"{sum(c.demand for c in custs.values()):.0f} kg")

        # 📌 RINGKASAN RENCANA OPERASIONAL SEBELUM SIMULASI
        with st.expander("📋 Ringkasan Rencana Operasional Distribusi", expanded=True):
            st.markdown(f"""
            Berikut adalah detail rencana operasional pengiriman yang siap dijalankan oleh sistem:
            *   **Kapasitas Armada**: Operasional kali ini dikonfigurasi maksimal **{st.session_state.max_vehicles} kendaraan** dengan kapasitas muatan homogen masing-masing **{st.session_state.capacity:,} kg**.
            *   **Distribusi Muatan**: Total muatan pelanggan statis (yang diketahui sejak awal hari) adalah sebesar **{sum(c.demand for c in custs.values() if not c.is_dynamic):.0f} kg**. Muatan ini akan langsung dijadwalkan pada rute awal.
            *   **Penanganan Pesanan Mendadak**: Total muatan dari pesanan dinamis baru yang masuk di tengah hari adalah sebesar **{sum(c.demand for c in custs.values() if c.is_dynamic):.0f} kg**. Pesanan-pesanan mendadak ini akan disisipkan secara bertahap sepanjang simulasi jam kerja depot, mulai pukul **{st.session_state.depot_open:.2f}** hingga batas depot tutup pukul **{st.session_state.depot_close:.2f}**.
            """)

        if nd == 0:
            st.warning(
                "Belum ada pelanggan dinamis. Simulasi berjalan sebagai VRP statis."
            )

        st.markdown("---")
        st.markdown("### ⚙️ Konfigurasi Mesin Optimasi & Acakan")
        
        col_opt1, col_opt2 = st.columns(2, gap="large")
        with col_opt1:
            st.markdown("#### Metode Perbaikan Rute")
            do_rvnd = st.toggle(
                "Terapkan Optimasi RVND",
                value=True,
                help="Mengaktifkan optimasi lokal berlapis dengan 5 operator neighborhood untuk memperpendek total jarak tempuh."
            )
            st.caption("RVND bertugas melakukan pencarian lokal (local search) intra-route dan inter-route secara intensif.")
            
        with col_opt2:
            st.markdown("#### Konsistensi Hasil (Reproduksibilitas)")
            use_fixed_seed = st.toggle(
                "Kunci Acakan (Fixed Seed)",
                value=True,
                help="Mengunci acakan algoritma agar hasil rute selalu konsisten ketika dijalankan berulang kali."
            )
            if use_fixed_seed:
                seed_val = st.number_input(
                    "Nilai Seed (Acuan Acakan)",
                    min_value=0, max_value=999999,
                    value=42,
                    help="Gunakan angka bulat acak mana saja. Jika angkanya sama, hasil rute akan selalu sama."
                )
            else:
                seed_val = 42
        
        selected_seed = int(seed_val) if use_fixed_seed else None

        if st.button("Jalankan Simulasi DVRPTW", use_container_width=True):
            with st.spinner("Memproses simulasi distribusi dinamis..."):
                t0 = _time.time()
                # Selalu jalankan versi tanpa optimasi (Unoptimized)
                res_unopt = run_dvrptw_simulation(
                    custs, dist, tmtx, depot,
                    time_step=0.05, apply_rvnd=False, random_seed=selected_seed
                )
                # Selalu jalankan versi dengan optimasi (Optimized - RVND)
                res_opt = run_dvrptw_simulation(
                    custs, dist, tmtx, depot,
                    time_step=0.05, apply_rvnd=True, random_seed=selected_seed
                )
                el = _time.time() - t0
                
            st.session_state.sim_unopt_result = res_unopt
            st.session_state.sim_opt_result = res_opt
            st.session_state.sim_result = res_opt if do_rvnd else res_unopt
            st.session_state.sim_el = el
            st.session_state.sim_c = custs
            st.session_state.sim_d = dist
            st.session_state.sim_t = tmtx
            st.session_state.sim_dep = depot
            st.toast(f"Simulasi selesai dalam {el:.2f} detik!", icon="✅")

        if st.session_state.sim_result:
            r = st.session_state.sim_result
            m = r["metrics"]
            st.markdown("---")
            st.success(f"Simulasi DVRPTW Selesai — Waktu Komputasi: {st.session_state.sim_el:.3f} detik")

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Jarak Akhir", f"{m['final_distance']:.2f} km")
            c2.metric(
                "Total Waktu Operasional", 
                f"{m['final_time']:.4f} jam",
                delta=format_hours_to_hms(m['final_time']),
                delta_color="off"
            )
            c3.metric("Kendaraan Terpakai", m["total_routes"])
            c4.metric(
                "Dynamic Overhead Gap",
                f"{m['dynamic_gap_pct']:.2f}%",
                help="Persentase tambahan jarak rute dinamis vs statis ideal."
            )
            
            # 💡 ANALISIS HASIL SIMULASI DINAMIS (ZERO HARDCODING)
            with st.expander("💡 Ringkasan Analisis Performa Rute Dinamis", expanded=True):
                st.markdown(f"""
                Simulasi pengiriman dinamis telah diselesaikan dengan hasil evaluasi performa sebagai berikut:
                *   **Penggunaan Armada**: Sebanyak **{m['total_routes']} kendaraan** aktif digunakan untuk melayani total **{m['total_customers']} lokasi** (terdiri dari **{m['static_customers']} pesanan statis** awal dan **{m['dynamic_customers']} pesanan dinamis** baru yang masuk saat armada sedang dalam perjalanan). Batas kapasitas armada yang dikonfigurasi adalah maksimal **{st.session_state.max_vehicles} kendaraan**.
                *   **Efisiensi & Celah Dinamis (Dynamic Gap)**: Total jarak tempuh rute riil adalah **{m['final_distance']:.2f} km**. Jarak ini menghasilkan **tambahan jarak operasional (Dynamic Overhead Gap) sebesar {m['dynamic_gap_pct']:.2f}%** jika dibandingkan dengan Solusi Statis Ideal ({m['ideal_static_distance']:.2f} km) yang mengasumsikan seluruh pesanan sudah diketahui sejak awal tanpa ada pesanan mendadak. Nilai gap yang rendah menunjukkan bahwa algoritma **Cheapest Insertion** berhasil menyisipkan pesanan baru secara efisien.
                *   **Kelayakan Batasan Operasional**: Aturan *non-preemption* terpenuhi sepenuhnya, di mana pengalihan rute hanya dilakukan pada segmen yang belum dilewati kendaraan (tidak ada kendaraan yang berputar balik di tengah jalan). Seluruh armada juga dipastikan berhasil kembali ke depot pusat sebelum batas tutup operasional pada pukul **{st.session_state.depot_close:.2f}**.
                """)
            
            st.info("Buka halaman **Analisis Hasil** untuk visualisasi lengkap.")


# ═══════════════════════════════════════════════════
# HALAMAN: ANALISIS HASIL
# ═══════════════════════════════════════════════════
elif menu == "📊 Analisis Hasil":
    st.markdown(HERO_BANNER, unsafe_allow_html=True)
    if not st.session_state.sim_result:
        st.info("Belum ada hasil simulasi. Jalankan simulasi di halaman **Simulasi DVRPTW**.")
    else:
        res = st.session_state.sim_result
        custs = st.session_state.sim_c
        dist = st.session_state.sim_d
        tmtx = st.session_state.sim_t
        depot_obj = st.session_state.sim_dep
        m = res["metrics"]

        t_rute, t_peta, t_rvnd, t_analisis, t_log = st.tabs([
            "Rute Optimal",
            "Visualisasi Jaringan",
            "Sebelum vs Setelah Optimasi (RVND)",
            "Analisis Komparasi",
            "Log Kejadian Dinamis",
        ])

        # ═══ TAB 1: RUTE OPTIMAL ═══
        with t_rute:
            st.markdown("### Daftar Rute Optimal Kendaraan")
            tbl = []
            for i, rt in enumerate(res["final_routes"]):
                rd = route_distance(rt.path, dist)
                rtt = route_time(rt.path, tmtx, custs)
                ld = sum(custs[n].demand for n in rt.customers_only if n in custs)
                cap_pct = (ld / depot_obj.capacity * 100) if depot_obj.capacity > 0 else 0
                tbl.append({
                    "Kendaraan": f"Kendaraan {i + 1}",
                    "Rute": " → ".join(map(str, rt.path)),
                    "Pelanggan Dilayani": len(rt.customers_only),
                    "Muatan (kg)": f"{ld:.0f}",
                    "Utilitas Kapasitas": f"{cap_pct:.1f}%",
                    "Jarak (km)": f"{rd:.2f}",
                    "Durasi": f"{rtt:.4f} jam ({format_hours_to_hms(rtt)})",
                })
            st.dataframe(pd.DataFrame(tbl), hide_index=True, use_container_width=True)

            st.markdown("---")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Jarak Tempuh", f"{m['final_distance']:.2f} km")
            c2.metric(
                "Total Waktu Kerja", 
                f"{m['final_time']:.4f} jam",
                delta=format_hours_to_hms(m['final_time']),
                delta_color="off"
            )
            c3.metric("Kendaraan Terpakai", m["total_routes"])
            avg_util = sum(
                sum(custs[n].demand for n in rt.customers_only if n in custs)
                for rt in res["final_routes"]
            ) / (len(res["final_routes"]) * depot_obj.capacity) * 100 if res["final_routes"] else 0
            c4.metric("Rata-rata Utilisasi", f"{avg_util:.1f}%")
            
            # Penjelasan metrik
            with st.expander("ℹ️ Penjelasan Metrik Rute Final", expanded=False):
                st.markdown(f"""
                **Total Jarak Tempuh**: Jumlah total jarak yang ditempuh oleh seluruh kendaraan dalam kilometer (km). Semakin kecil nilai ini, semakin efisien rute yang dihasilkan.
                
                **Total Waktu Kerja**: Durasi total operasional seluruh armada dalam jam desimal. Nilai ini mencakup waktu perjalanan antar node dan waktu pelayanan di setiap pelanggan. Format HMS (Jam:Menit:Detik) ditampilkan untuk kemudahan pembacaan.
                
                **Kendaraan Terpakai**: Jumlah kendaraan yang digunakan untuk melayani seluruh pelanggan. Dalam kasus ini, maksimal **{depot_obj.max_vehicles} kendaraan** tersedia dengan kapasitas masing-masing **{depot_obj.capacity:,} kg**.
                
                **Rata-rata Utilisasi**: Persentase rata-rata penggunaan kapasitas kendaraan. Nilai tinggi (mendekati 100%) menunjukkan kendaraan dimanfaatkan secara optimal tanpa banyak ruang kosong.
                """)

            # 📊 GRAFIK DISTRIBUSI MUATAN PER KENDARAAN (Dipindahkan dari Tab 2 agar layout rapi)
            st.markdown("---")
            st.markdown("#### Distribusi Muatan per Kendaraan")
            
            with st.expander("ℹ️ Cara Membaca Grafik Distribusi Muatan", expanded=False):
                st.markdown(f"""
                **Muatan Terisi (Biru Tua)**: Jumlah muatan barang yang diangkut oleh kendaraan dalam kilogram (kg).
                
                **Sisa Kapasitas (Biru Muda)**: Kapasitas kosong yang masih tersedia pada kendaraan dalam kilogram (kg).
                
                **Garis Merah Putus-putus**: Batas maksimum kapasitas muatan kendaraan (**{depot_obj.capacity:,} kg**).
                
                **Interpretasi**: Semakin tinggi bagian biru tua (Muatan Terisi), semakin optimal pemanfaatan kapasitas kendaraan homogen.
                """)
            
            load_data = []
            for i, rt in enumerate(res["final_routes"]):
                ld = sum(custs[n].demand for n in rt.customers_only if n in custs)
                load_data.append({
                    "Kendaraan": f"Kendaraan {i + 1}",
                    "Muatan (kg)": ld,
                    "Sisa Kapasitas (kg)": depot_obj.capacity - ld,
                })
            load_df = pd.DataFrame(load_data)

            fig_load = go.Figure()
            fig_load.add_trace(go.Bar(
                x=load_df["Kendaraan"], y=load_df["Muatan (kg)"],
                name="Muatan Terisi",
                marker_color="#1E40AF",
                text=load_df["Muatan (kg)"].apply(lambda x: f"{x:.0f} kg"),
                textposition="auto",
                textfont=dict(size=14),
            ))
            fig_load.add_trace(go.Bar(
                x=load_df["Kendaraan"], y=load_df["Sisa Kapasitas (kg)"],
                name="Sisa Kapasitas",
                marker_color="#BFDBFE",
                text=load_df["Sisa Kapasitas (kg)"].apply(lambda x: f"{x:.0f} kg"),
                textposition="auto",
                textfont=dict(size=14),
            ))
            fig_load.update_layout(
                barmode="stack",
                yaxis_title="Kapasitas (kg)",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                height=350,
                font=dict(family="Inter"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(size=13)),
                hoverlabel=dict(font_size=12, font_family="Inter"),
            )
            fig_load.add_hline(
                y=depot_obj.capacity,
                line_dash="dash", line_color="#DC2626",
                annotation_text=f"Kapasitas Maks: {depot_obj.capacity} kg",
                annotation_position="top right",
            )
            st.plotly_chart(fig_load, use_container_width=True)

            # Detail waktu kedatangan per rute
            st.markdown("---")
            st.markdown("#### Detail Waktu Kedatangan per Rute")
            
            with st.expander("ℹ️ Cara Membaca Detail Waktu Kedatangan"):
                st.markdown("""
                **Urutan**: Nomor urut kunjungan dalam rute (dimulai dari depot = 1).
                
                **Node**: Nama lokasi yang dikunjungi (Depot atau Pelanggan).
                
                **Tipe**: Kategori pelanggan — **Statis** (diketahui sejak awal) atau **Dinamis** (muncul saat simulasi berjalan).
                
                **Demand**: Jumlah muatan yang harus diangkut dari pelanggan tersebut dalam kilogram (kg).
                
                **Jarak dari Sebelumnya**: Jarak tempuh dari node sebelumnya ke node saat ini dalam kilometer (km).
                
                **Waktu Tiba**: Waktu kedatangan kendaraan di node tersebut dalam jam desimal dan format HMS. Waktu ini dihitung kumulatif dari depot dengan memperhitungkan waktu perjalanan dan waktu pelayanan di setiap node sebelumnya.
                """)
            
            for i, rt in enumerate(res["final_routes"]):
                arr_times = get_route_arrival_times(
                    rt.path, tmtx, custs, depot_obj.tw_open
                )
                detail_rows = []
                for j, node in enumerate(rt.path):
                    if node == 0:
                        label = "Depot"
                        tipe = "-"
                        dem = "-"
                    else:
                        c_obj = custs.get(node)
                        tipe = "Dinamis" if c_obj and c_obj.is_dynamic else "Statis"
                        label = f"Pelanggan {node}"
                        dem = f"{c_obj.demand:.0f} kg" if c_obj else "-"

                    # Hitung jarak dari node sebelumnya
                    jarak_seg = f"{dist[rt.path[j-1]][node]:.2f} km" if j > 0 else "-"

                    detail_rows.append({
                        "Urutan": j + 1,
                        "Node": label,
                        "Tipe": tipe,
                        "Demand": dem,
                        "Jarak dari Sebelumnya": jarak_seg,
                        "Waktu Tiba": f"{arr_times[j]:.4f} jam ({format_hours_to_hms(arr_times[j])})",
                    })
                with st.expander(f"Kendaraan {i + 1}: {' → '.join(map(str, rt.path))}"):
                    st.dataframe(
                        pd.DataFrame(detail_rows),
                        hide_index=True, use_container_width=True,
                    )

        # ═══ TAB 2: VISUALISASI JARINGAN RUTE ═══
        with t_peta:
            st.markdown("### Visualisasi Jaringan Rute Kendaraan")
            st.caption(
                "Grafik ini menampilkan jaringan distribusi berupa node pelanggan "
                "dan jalur rute masing-masing kendaraan. Posisi node dihitung secara "
                "otomatis dari matriks jarak menggunakan pendekatan geometrik."
            )
            
            with st.expander("ℹ️ Cara Membaca Peta Jaringan Rute"):
                st.markdown("""
                **Node Depot (Persegi Hitam)**: Titik pusat distribusi (node 0) tempat semua kendaraan berangkat dan kembali.
                
                **Node Pelanggan (Lingkaran)**: Setiap pelanggan ditampilkan sebagai lingkaran dengan warna berbeda:
                - **Biru**: Pelanggan statis (diketahui sejak awal)
                - **Merah**: Pelanggan dinamis (muncul saat simulasi berjalan)
                
                **Garis Rute**: Jalur yang dilalui setiap kendaraan ditampilkan dengan warna berbeda. Panah menunjukkan arah perjalanan.
                
                **Label Jarak**: Angka di tengah setiap segmen menunjukkan jarak antar node dalam kilometer (km).
                
                **Legenda**: Menunjukkan warna rute untuk setiap kendaraan.
                """)

            # Hitung posisi node menggunakan MDS Klasik agar mencerminkan jarak sesungguhnya
            all_nodes = set()
            for rt in res["final_routes"]:
                all_nodes.update(rt.path)
            node_list = sorted(all_nodes)
            n_nodes = len(node_list)
            
            # Pelanggan yang ada di dalam rute (selain depot 0)
            cust_nodes = [n for n in node_list if n != 0]

            try:
                # Proyeksi jarak menjadi koordinat 2D
                coords = solve_2d_positions(dist)
                # Skala posisi agar nyaman dilihat di plot
                positions = {i: (coords[i, 0] * 10, coords[i, 1] * 10) for i in range(len(coords))}
            except Exception:
                # Fallback ke layout melingkar jika gagal
                positions = {}
                positions[0] = (0.0, 0.0)  # depot di pusat
                for idx, node in enumerate(cust_nodes):
                    angle = 2 * math.pi * idx / max(len(cust_nodes), 1)
                    r = dist[0][node] / max(dist[0].max(), 1) * 5 + 1.5
                    positions[node] = (r * math.cos(angle), r * math.sin(angle))

            fig_net = go.Figure()

            # Gambar rute tiap kendaraan sebagai garis berwarna
            for r_idx, rt in enumerate(res["final_routes"]):
                color = ROUTE_COLORS[r_idx % len(ROUTE_COLORS)]
                path_x = [positions[n][0] for n in rt.path]
                path_y = [positions[n][1] for n in rt.path]

                # Garis rute
                fig_net.add_trace(go.Scatter(
                    x=path_x, y=path_y,
                    mode="lines",
                    line=dict(color=color, width=3),
                    name=f"Rute Kendaraan {r_idx + 1}",
                    legendgroup=f"Kendaraan {r_idx + 1}",
                    showlegend=True,
                    hoverinfo="skip",
                ))

                # Panah arah di setiap segmen
                for seg_i in range(len(rt.path) - 1):
                    x0, y0 = positions[rt.path[seg_i]]
                    x1, y1 = positions[rt.path[seg_i + 1]]
                    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
                    dx, dy = x1 - x0, y1 - y0
                    seg_dist = dist[rt.path[seg_i]][rt.path[seg_i + 1]]

                    fig_net.add_annotation(
                        x=mx + dx * 0.15, y=my + dy * 0.15,
                        ax=mx - dx * 0.15, ay=my - dy * 0.15,
                        xref="x", yref="y", axref="x", ayref="y",
                        showarrow=True,
                        arrowhead=3, arrowsize=1.2, arrowwidth=2,
                        arrowcolor=color,
                    )

                    # Label jarak di setiap segmen sebagai annotation di atas segmen dengan background putih bulat agar tidak tertutup panah
                    fig_net.add_annotation(
                        x=mx, y=my,
                        text=f"<b>{seg_dist:.1f} km</b>",
                        showarrow=False,
                        font=dict(size=9.5, color="#1E3A8A", family="JetBrains Mono"),
                        bgcolor="#FFFFFF",
                        bordercolor="#93C5FD",
                        borderwidth=1.5,
                        borderpad=3,
                        yshift=0,
                    )

            # Node depot (persegi besar)
            fig_net.add_trace(go.Scatter(
                x=[positions[0][0]], y=[positions[0][1]],
                mode="markers+text",
                marker=dict(size=28, color="#0F172A", symbol="square",
                            line=dict(width=3, color="#3B82F6")),
                text=["<b>Depot</b>"],
                textposition="bottom center",
                textfont=dict(size=15, color="#0F172A", family="Inter"),
                name="Depot Pusat (Node 0)",
                legendgroup="Depot",
                showlegend=True,
                hovertemplate="Depot (Node 0)<extra></extra>",
            ))

            # Node pelanggan (Dengan pengelompokan legenda yang rapi)
            show_static_legend = True
            show_dynamic_legend = True

            for node in cust_nodes:
                c_obj = custs.get(node)
                is_dyn = c_obj.is_dynamic if c_obj else False
                color_node = "#EF4444" if is_dyn else "#2563EB"
                symbol = "diamond" if is_dyn else "circle"
                tipe_str = "Dinamis" if is_dyn else "Statis"
                demand_str = f"{c_obj.demand:.0f} kg" if c_obj else "?"

                if is_dyn:
                    show_leg = show_dynamic_legend
                    show_dynamic_legend = False
                    leg_name = "Pelanggan Dinamis"
                    leg_group = "Pelanggan Dinamis"
                else:
                    show_leg = show_static_legend
                    show_static_legend = False
                    leg_name = "Pelanggan Statis"
                    leg_group = "Pelanggan Statis"

                fig_net.add_trace(go.Scatter(
                    x=[positions[node][0]], y=[positions[node][1]],
                    mode="markers+text",
                    marker=dict(size=24, color=color_node, symbol=symbol,
                                line=dict(width=2, color="white")),
                    text=[f"<b>{node}</b>"],
                    textposition="middle center",
                    textfont=dict(size=15, color="white", family="Inter"),
                    name=leg_name,
                    legendgroup=leg_group,
                    showlegend=show_leg,
                    hovertemplate=(
                        f"Pelanggan {node} ({tipe_str})<br>"
                        f"Demand: {demand_str}<br>"
                        f"Jarak ke Depot: {dist[0][node]:.1f} km"
                        "<extra></extra>"
                    ),
                ))

            fig_net.update_layout(
                height=550,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter"),
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02,
                    xanchor="center", x=0.5,
                    font=dict(size=13),
                ),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                           scaleanchor="x", scaleratio=1),
                margin=dict(l=20, r=20, t=60, b=20),
                hoverlabel=dict(font_size=12, font_family="Inter"),
            )
            st.plotly_chart(fig_net, use_container_width=True)

            # Legenda penjelasan
            st.markdown("""
            **Legenda:**
            🔵 Pelanggan Statis — 🔴 Pelanggan Dinamis — ⬛ Depot Pusat —
            *Angka miring abu-abu pada garis (e.g., 4.0 km) = jarak antar segmen rute*
            """)

        # ═══ TAB 3: SEBELUM VS SETELAH OPTIMASI (RVND) ═══
        with t_rvnd:
            if st.session_state.sim_unopt_result is None or st.session_state.sim_opt_result is None:
                with st.spinner("Menghitung data perbandingan..."):
                    st.session_state.sim_unopt_result = run_dvrptw_simulation(
                        custs, dist, tmtx, depot_obj, time_step=0.05, apply_rvnd=False
                    )
                    st.session_state.sim_opt_result = run_dvrptw_simulation(
                        custs, dist, tmtx, depot_obj, time_step=0.05, apply_rvnd=True
                    )
            
            res_un = st.session_state.sim_unopt_result
            res_op = st.session_state.sim_opt_result
            m_un = res_un["metrics"]
            m_op = res_op["metrics"]

            st.markdown("### Analisis Perbaikan Rute: Sebelum vs Setelah Optimasi ILS & RVND")
            st.caption(
                "Halaman ini membandingkan kinerja rute heuristik dasar (Sequential Insertion + Cheapest Insertion) "
                "dengan rute yang telah disempurnakan secara dinamis menggunakan Iterated Local Search (ILS) yang mengintegrasikan RVND."
            )
            
            with st.expander("ℹ️ Apa itu Optimasi ILS & RVND?"):
                st.markdown("""
                **Iterated Local Search (ILS)** dikombinasikan dengan **RVND (Randomized Variable Neighborhood Descent)** bekerja dengan alur bertahap:
                
                1. **Local Search (Intra-Route)**: Menjalankan optimasi deterministik 2-Opt, Or-Opt, dan Exchange pada setiap rute.
                2. **RVND (Inter & Intra-Route)**: Mengacak penggunaan 5 operator neighborhood secara acak:
                   - **2-Opt**: Membalik urutan segmen rute untuk menghilangkan persilangan jalur.
                   - **Or-Opt**: Memindahkan 1-2 pelanggan berurutan ke posisi lain dalam satu rute.
                   - **Exchange**: Menukar posisi dua pelanggan dalam satu rute.
                   - **Relocate**: Memindahkan satu pelanggan dari satu rute ke rute lain.
                   - **Swap(1,1)**: Menukar satu pelanggan antar dua rute berbeda.
                3. **Perturbasi (Perturbation)**: Melakukan pengacakan layak terkontrol pada rute untuk menghindari jebakan optimum lokal (*local optima*), kemudian melakukan siklus pencarian lokal kembali.
                
                Proses ini menjamin rute yang dihasilkan jauh lebih efisien dengan tetap menjaga batas non-preemption.
                """)

            # Perbedaan metrik
            dist_un = m_un["final_distance"]
            dist_op = m_op["final_distance"]
            dist_diff = dist_un - dist_op
            dist_pct = (dist_diff / dist_un * 100) if dist_un > 0 else 0
            
            time_un = m_un["final_time"]
            time_op = m_op["final_time"]
            time_diff = time_un - time_op
            time_pct = (time_diff / time_un * 100) if time_un > 0 else 0

            veh_un = m_un["total_routes"]
            veh_op = m_op["total_routes"]
            veh_diff = veh_un - veh_op

            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric(
                    "Total Jarak Tempuh",
                    f"{dist_op:.2f} km",
                    delta=f"-{dist_diff:.2f} km (-{dist_pct:.2f}%)" if dist_diff > 0 else "0.00 km (0.00%)",
                    delta_color="inverse"
                )
                st.markdown(f"<div style='font-size: 13.5px; font-weight: 600; color: #1E293B; margin-top: -12px; margin-bottom: 8px;'>Sebelum: <span style='color: #64748B; font-weight: bold;'>{dist_un:.2f} km</span> &nbsp;➔&nbsp; Setelah: <span style='color: #10B981; font-weight: 800;'>{dist_op:.2f} km</span></div>", unsafe_allow_html=True)
            with c2:
                st.metric(
                    "Total Waktu Operasional",
                    f"{time_op:.4f} jam",
                    delta=f"-{time_diff:.4f} jam (-{time_pct:.2f}%)" if time_diff > 0 else "0.00 jam (0.00%)",
                    delta_color="inverse"
                )
                st.markdown(f"<div style='font-size: 13.5px; font-weight: 600; color: #1E293B; margin-top: -12px; margin-bottom: 8px;'>Sebelum: <span style='color: #64748B; font-weight: bold;'>{time_un:.4f} jam</span> <span style='font-size: 13.5px; color: #64748B;'>({format_hours_to_hms(time_un)})</span> &nbsp;➔&nbsp; Setelah: <span style='color: #10B981; font-weight: 800;'>{time_op:.4f} jam</span> <span style='font-size: 13.5px; color: #10B981; font-weight: bold;'>({format_hours_to_hms(time_op)})</span></div>", unsafe_allow_html=True)
            with c3:
                st.metric(
                    "Kendaraan Terpakai",
                    f"{veh_op} Kendaraan",
                    delta=f"-{veh_diff} Kendaraan" if veh_diff > 0 else "0",
                    delta_color="inverse" if veh_diff > 0 else "off"
                )
                st.markdown(f"<div style='font-size: 13.5px; font-weight: 600; color: #1E293B; margin-top: -12px; margin-bottom: 8px;'>Sebelum: <span style='color: #64748B; font-weight: bold;'>{veh_un} mobil</span> &nbsp;➔&nbsp; Setelah: <span style='color: #10B981; font-weight: 800;'>{veh_op} mobil</span></div>", unsafe_allow_html=True)
            
            with st.expander("ℹ️ Penjelasan Metrik Perbandingan"):
                st.markdown("""
                **Total Jarak Tempuh**: Pengurangan jarak menunjukkan efisiensi rute. Nilai negatif (hijau) berarti ILS & RVND berhasil memangkas jarak tempuh.
                
                **Total Waktu Operasional**: Pengurangan waktu berarti armada dapat menyelesaikan pengiriman lebih cepat, menghemat biaya operasional.
                
                **Kendaraan Terpakai**: Jika jumlah kendaraan berkurang, berarti ILS & RVND berhasil mengkonsolidasikan rute sehingga lebih sedikit armada yang dibutuhkan.
                
                **Delta (Perubahan)**: Angka negatif dengan warna hijau menunjukkan perbaikan (pengurangan biaya). Semakin besar persentase pengurangan, semakin efektif optimasi ILS & RVND.
                """)

            st.markdown("---")
            st.markdown("#### Tabel Perbandingan Parameter Sebelum vs Setelah Optimasi")
            
            # Hitung muatan rata-rata per rute
            avg_ld_un = np.mean([sum(custs[n].demand for n in rt.customers_only if n in custs) for rt in res_un['final_routes']]) if res_un['final_routes'] else 0
            avg_ld_op = np.mean([sum(custs[n].demand for n in rt.customers_only if n in custs) for rt in res_op['final_routes']]) if res_op['final_routes'] else 0

            comp_rvnd_df = pd.DataFrame({
                "Parameter Evaluasi": [
                    "Total Jarak Tempuh Armada",
                    "Total Waktu Operasional Armada",
                    "Representasi Waktu (HMS)",
                    "Jumlah Kendaraan Aktif",
                    "Rata-rata Muatan per Kendaraan",
                    "Rata-rata Jarak per Kendaraan",
                ],
                "Sebelum Optimasi (Sequential Insertion + Cheapest Insertion)": [
                    f"{dist_un:.2f} km",
                    f"{time_un:.4f} jam",
                    format_hours_to_hms(time_un),
                    f"{veh_un} kendaraan",
                    f"{avg_ld_un:.0f} kg",
                    f"{dist_un / max(veh_un, 1):.2f} km",
                ],
                "Setelah Optimasi (ILS & RVND Metaheuristic)": [
                    f"{dist_op:.2f} km",
                    f"{time_op:.4f} jam",
                    format_hours_to_hms(time_op),
                    f"{veh_op} kendaraan",
                    f"{avg_ld_op:.0f} kg",
                    f"{dist_op / max(veh_op, 1):.2f} km",
                ],
                "Dampak Efisiensi": [
                    f"Berkurang {dist_diff:.2f} km ({dist_pct:.2f}%) ✅ Lebih Pendek" if dist_diff > 0 else "Sama (0.00%)",
                    f"Berkurang {time_diff:.4f} jam ({time_pct:.2f}%) ✅ Lebih Cepat" if time_diff > 0 else "Sama (0.00%)",
                    "Menghemat Waktu Kerja" if time_diff > 0 else "Sama",
                    f"Mereduksi {veh_diff} kendaraan" if veh_diff > 0 else "Sama (Penggunaan Optimal)",
                    "Distribusi Muatan Lebih Padat" if veh_diff > 0 else "Sama",
                    f"Lebih Pendek {dist_diff / max(veh_op, 1):.2f} km/mobil" if dist_diff > 0 else "Sama",
                ]
            })
            st.dataframe(comp_rvnd_df, hide_index=True, use_container_width=True)

            st.markdown("---")
            st.markdown("#### Visualisasi Efisiensi Optimasi ILS & RVND")
            
            with st.expander("ℹ️ Cara Membaca Grafik Perbandingan"):
                st.markdown("""
                **Grafik Batang Jarak (Kiri)**: Membandingkan total jarak tempuh sebelum dan setelah optimasi ILS & RVND. Batang merah menunjukkan kondisi awal (lebih panjang), batang hijau menunjukkan hasil optimasi (lebih pendek).
                
                **Grafik Batang Waktu (Kanan)**: Membandingkan total waktu operasional dalam jam desimal. Batang oranye menunjukkan kondisi awal, batang hijau menunjukkan hasil optimasi.
                
                **Interpretasi**: Semakin besar selisih tinggi antara batang merah/oranye dengan batang hijau, semakin besar penghematan yang dihasilkan oleh algoritma ILS & RVND.
                """)
            
            col_g1, col_g2 = st.columns(2)
            
            with col_g1:
                fig_g1 = go.Figure()
                fig_g1.add_trace(go.Bar(
                    x=["Sebelum Optimasi"],
                    y=[dist_un],
                    name="Sebelum Optimasi",
                    marker_color="#EF4444",
                    text=[f"{dist_un:.2f} km"],
                    textposition="auto",
                    width=0.4
                ))
                fig_g1.add_trace(go.Bar(
                    x=["Setelah Optimasi"],
                    y=[dist_op],
                    name="Setelah Optimasi",
                    marker_color="#10B981",
                    text=[f"{dist_op:.2f} km"],
                    textposition="auto",
                    width=0.4
                ))
                fig_g1.update_layout(
                    title="Perbandingan Total Jarak Tempuh (km)",
                    yaxis_title="Jarak (km)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    height=300,
                    font=dict(family="Inter"),
                    showlegend=True,
                    legend=dict(
                        orientation="h", yanchor="bottom", y=1.02,
                        xanchor="center", x=0.5,
                        font=dict(size=12),
                    ),
                    hoverlabel=dict(font_size=12, font_family="Inter"),
                )
                st.plotly_chart(fig_g1, use_container_width=True)
                
            with col_g2:
                fig_g2 = go.Figure()
                fig_g2.add_trace(go.Bar(
                    x=["Sebelum Optimasi"],
                    y=[time_un],
                    name="Sebelum Optimasi",
                    marker_color="#F59E0B",
                    text=[f"{time_un:.4f} jam"],
                    textposition="auto",
                    width=0.4
                ))
                fig_g2.add_trace(go.Bar(
                    x=["Setelah Optimasi"],
                    y=[time_op],
                    name="Setelah Optimasi",
                    marker_color="#10B981",
                    text=[f"{time_op:.4f} jam"],
                    textposition="auto",
                    width=0.4
                ))
                fig_g2.update_layout(
                    title="Perbandingan Total Waktu Operasional (jam desimal)",
                    yaxis_title="Waktu (jam desimal)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    height=300,
                    font=dict(family="Inter"),
                    showlegend=True,
                    legend=dict(
                        orientation="h", yanchor="bottom", y=1.02,
                        xanchor="center", x=0.5,
                        font=dict(size=12),
                    ),
                    hoverlabel=dict(font_size=12, font_family="Inter"),
                )
                st.plotly_chart(fig_g2, use_container_width=True)

            # 📝 KESIMPULAN AKADEMIS
            st.markdown("---")
            
            # Hitung rata-rata utilisasi untuk kesimpulan
            avg_util = sum(
                sum(custs[n].demand for n in rt.customers_only if n in custs)
                for rt in res_op["final_routes"]
            ) / (len(res_op["final_routes"]) * depot_obj.capacity) * 100 if res_op["final_routes"] else 0

            with st.expander("📝 **Kesimpulan Analisis Permasalahan DVRPTW**", expanded=True):
                st.markdown(f"""
                #### **1. Rasionalisasi Penggunaan Jam Desimal (Decimal Hours)**
                *   Seluruh durasi dan matriks waktu dalam sistem ini direpresentasikan dalam **Jam Desimal** (misalnya `0.9005 jam`). Representasi ini digunakan agar komputasi matematis (seperti pembagian jarak terhadap kecepatan rata-rata armada $v = {depot_obj.speed:.1f} \\text{{ km/jam}}$) tetap presisi tanpa ada pembulatan berulang.
                *   **Konversi Riil Hasil Pengiriman Saat Ini**:
                    *   Total waktu operasional rute optimal saat ini adalah **{time_op:.4f} jam** yang secara otomatis dikonversi oleh sistem menjadi **{format_hours_to_hms(time_op)}** untuk kemudahan pemahaman operasional di lapangan.
                
                #### **2. Efektivitas Algoritma ILS & RVND (Optimasi Metaheuristik)**
                *   Kombinasi metode **Sequential Insertion** sebagai rute awal dan **ILS & RVND (Iterated Local Search & Randomized Variable Neighborhood Descent)** terbukti **sangat efektif** dalam meningkatkan efisiensi distribusi.
                *   Algoritma berhasil meminimalkan total jarak tempuh dari **{dist_un:.2f} km** menjadi **{dist_op:.2f} km** (menghemat **{dist_diff:.2f} km** atau **{dist_pct:.2f}%** jarak tempuh).
                *   Durasi waktu operasional armada juga terpangkas dari **{time_un:.4f} jam** ({format_hours_to_hms(time_un)}) menjadi **{time_op:.4f} jam** ({format_hours_to_hms(time_op)}) (hemat **{time_pct:.2f}%** waktu kerja).
                *   Hasil ini membuktikan keunggulan konstruksi *Sequential Insertion* serta kekuatan metaheuristik ILS yang menggunakan *perturbasi* untuk mendobrak optimum lokal sehingga didapatkan rute global yang jauh lebih optimal bagi armada logistik.
                
                #### **3. Analisis Kelayakan Solusi (Feasibility & Fleet Utility)**
                *   Seluruh rute hasil simulasi dinyatakan **LAYAK (FEASIBLE)** secara matematis dan operasional:
                    *   **Kapasitas Kendaraan**: Muatan maksimum setiap rute tidak melebihi kapasitas homogen **{depot_obj.capacity:,} kg**.
                    *   **Jendela Waktu (Time Windows)**: Kendaraan berhasil menyelesaikan seluruh pengantaran dan kembali ke depot sebelum batas jam tutup depot pukul **{format_hours_to_hms(depot_obj.tw_close)}** (durasi maksimal **{depot_obj.tw_close - depot_obj.tw_open:.1f} jam** kerja dari pukul **{format_hours_to_hms(depot_obj.tw_open)}**).
                    *   **Utilisasi Armada**: Dengan mengoptimalkan rute, utilisasi rata-rata kapasitas kendaraan mencapai **{avg_util:.1f}%**.
                
                #### **4. Efek Ketidakpastian Informasi (Dynamic Overhead Gap)**
                *   Nilai *Dynamic Overhead Gap* sebesar **{m_op['dynamic_gap_pct']:.2f}%** menunjukkan biaya tambahan (*overhead*) berupa selisih jarak yang harus dibayar akibat sifat kedatangan pesanan yang dinamis (muncul mendadak saat rute sudah berjalan) dibandingkan dengan solusi *offline* ideal di mana semua pesanan sudah diketahui sejak awal.
                *   Nilai gap yang sangat kecil ini membuktikan bahwa strategi **Cheapest Insertion** untuk penyisipan pelanggan dinamis, dikombinasikan dengan re-optimasi **ILS & RVND**, mampu meminimalkan efek negatif dari ketidakpastian informasi secara real-time.
                """)

        # ═══ TAB 4: LOG KEJADIAN DINAMIS ═══
        with t_log:
            st.markdown("### Log Kejadian Simulasi (Event Log)")
            st.caption(
                "Menunjukkan kronologi perubahan rute secara real-time "
                "saat pesanan dinamis muncul selama simulasi."
            )
            
            with st.expander("ℹ️ Cara Membaca Log Kejadian"):
                st.markdown("""
                **Waktu**: Waktu simulasi dalam jam desimal saat kejadian terjadi (misalnya Pukul 4.05 = 04:03).
                
                **Kejadian**: Jenis kejadian yang terjadi:
                - **INITIAL_SOLUTION**: Pembentukan rute awal dari pelanggan statis
                - **DYNAMIC_INSERTION**: Penyisipan pelanggan dinamis baru ke rute yang sedang berjalan
                - **RE_OPTIMIZATION**: Proses optimasi ulang rute menggunakan RVND setelah insertion
                
                **Deskripsi**: Penjelasan detail tentang apa yang terjadi pada kejadian tersebut.
                
                **Total Jarak (km)**: Total jarak tempuh sementara seluruh armada pada waktu tersebut. Nilai ini dapat naik (saat insertion) atau turun (saat re-optimization).
                """)
            
            evts = res["events"]
            if evts:
                et = [{
                    "Waktu": f"Pukul {e['time']:.2f}",
                    "Kejadian": e["event"],
                    "Deskripsi": e["detail"],
                    "Total Jarak (km)": f"{e.get('total_distance', 0):.2f}",
                } for e in evts]
                st.dataframe(pd.DataFrame(et), hide_index=True, use_container_width=True)

                dists = [
                    {"t": e["time"], "d": e.get("total_distance", 0)}
                    for e in evts if "total_distance" in e
                ]
                if len(dists) > 1:
                    st.markdown("#### Grafik Fluktuasi Jarak vs Waktu Simulasi")
                    
                    with st.expander("ℹ️ Cara Membaca Grafik Fluktuasi"):
                        st.markdown("""
                        **Sumbu X (Horizontal)**: Waktu simulasi dalam jam desimal (misalnya 4.0 = 04:00, 4.5 = 04:30).
                        
                        **Sumbu Y (Vertikal)**: Total jarak tempuh sementara seluruh armada dalam kilometer (km).
                        
                        **Pola Naik**: Terjadi saat pelanggan dinamis baru disisipkan ke rute (DYNAMIC_INSERTION), menyebabkan jarak bertambah.
                        
                        **Pola Turun**: Terjadi saat algoritma RVND melakukan re-optimasi (RE_OPTIMIZATION), memangkas jarak dengan menata ulang urutan kunjungan.
                        
                        **Interpretasi**: Grafik yang stabil atau menurun di akhir simulasi menunjukkan algoritma berhasil menjaga efisiensi rute meskipun ada gangguan dinamis.
                        """)
                    
                    cdf2 = pd.DataFrame(dists)
                    fig_flux = go.Figure()
                    fig_flux.add_trace(go.Scatter(
                        x=cdf2["t"], y=cdf2["d"],
                        mode="lines+markers",
                        line=dict(color="#1E40AF", width=3),
                        marker=dict(size=8, color="#3B82F6"),
                        name="Total Jarak",
                        fill="tozeroy",
                        fillcolor="rgba(37,99,235,0.08)",
                    ))
                    fig_flux.update_layout(
                        xaxis_title="Waktu Simulasi (jam)",
                        yaxis_title="Total Jarak Tempuh (km)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        height=380,
                        font=dict(family="Inter"),
                        showlegend=True,
                        legend=dict(
                            orientation="h", yanchor="bottom", y=1.02,
                            xanchor="center", x=0.5,
                            font=dict(size=13),
                        ),
                        hoverlabel=dict(font_size=12, font_family="Inter"),
                    )
                    st.plotly_chart(fig_flux, use_container_width=True)

            if res.get("init_log"):
                with st.expander(f"Catatan Perbaikan RVND ({len(res['init_log'])} iterasi)"):
                    st.dataframe(
                        pd.DataFrame(res["init_log"]),
                        hide_index=True, use_container_width=True,
                    )

        # ═══ TAB 5: ANALISIS KOMPARASI ═══
        with t_analisis:
            st.markdown("### Analisis Perbandingan: Statis Ideal vs Dinamis")
            
            with st.expander("ℹ️ Panduan Konsep & Cara Membaca Grafik Perbandingan", expanded=False):
                st.markdown("""
                ##### 📘 Konsep Dasar Analisis Perbandingan
                *   **Solusi Statis Ideal (Offline Benchmark)**: Skenario teoritis di mana seluruh pesanan pelanggan (statis + dinamis) diasumsikan sudah diketahui sejak awal hari (pukul 04:00 pagi). Ini merupakan solusi optimal terbaik yang bisa dicapai apabila tidak ada faktor ketidakpastian operasional (*upper bound* efisiensi).
                *   **Solusi Dinamis (Online DVRPTW)**: Skenario operasional riil di lapangan di mana pelanggan dinamis muncul mendadak secara bertahap saat armada sudah di perjalanan. Sistem harus merespon secara real-time dengan menyisipkan pesanan baru ke dalam rute yang sedang berjalan.
                *   **Dynamic Overhead Gap**: Selisih persentase jarak rute dinamis aktual terhadap rute statis ideal offline. Nilai ini melambangkan **"Harga Ketidakpastian Informasi"** (biaya tambahan akibat kedatangan pesanan mendadak). Semakin kecil nilai gap ini, semakin tangguh algoritma *Cheapest Insertion + RVND* dalam menekan dampak kedatangan pesanan mendadak.
                
                ##### 📊 Panduan Membaca Visualisasi Grafik
                *   **Grafik Jarak Total**: Membandingkan total jarak tempuh kumulatif. Batang biru muda (Statis Ideal) adalah baseline terbaik, sedangkan batang biru tua (Dinamis) adalah hasil aktual. Selisih yang tipis menunjukkan efisiensi tinggi dari penyisipan rute dinamis.
                *   **Grafik Jarak per Rute**: Menampilkan pembagian beban kerja jarak antar armada. Berguna untuk mengevaluasi pemerataan rute operasional agar beban antar kendaraan homogen tetap seimbang dan efisien.
                """)

            # Metrik utama dengan 5 kolom
            st.markdown("---")
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Jarak Statis Ideal", f"{m['ideal_static_distance']:.2f} km")
            c2.metric("Jarak Dinamis", f"{m['final_distance']:.2f} km")
            gap_km = m["final_distance"] - m["ideal_static_distance"]
            c3.metric("Selisih Jarak", f"{gap_km:.2f} km",
                       delta=f"{m['dynamic_gap_pct']:.2f}%",
                       delta_color="inverse")
            c4.metric("Kendaraan Terpakai", m["total_routes"])
            c5.metric("Pelanggan Terlayani", m["total_customers"])

            # Tabel perbandingan detail
            st.markdown("---")
            st.markdown("#### Tabel Perbandingan Detail")

            # Hitung metrik tambahan per rute
            ideal_routes = res.get("ideal_static_routes", [])
            final_routes = res["final_routes"]

            # Metrik statis ideal
            ideal_dist = m["ideal_static_distance"]
            ideal_n_routes = len(ideal_routes)
            ideal_loads = [
                sum(custs[n].demand for n in rt.customers_only if n in custs)
                for rt in ideal_routes
            ] if ideal_routes else []
            ideal_avg_load = np.mean(ideal_loads) if ideal_loads else 0

            # Metrik dinamis
            final_dist_val = m["final_distance"]
            final_n_routes = m["total_routes"]
            final_loads = [
                sum(custs[n].demand for n in rt.customers_only if n in custs)
                for rt in final_routes
            ]
            final_avg_load = np.mean(final_loads) if final_loads else 0

            ideal_time_val = total_time(ideal_routes, tmtx, custs) if ideal_routes else 0

            comp_df = pd.DataFrame({
                "Parameter": [
                    "Total Jarak Tempuh (km)",
                    "Jumlah Rute/Kendaraan",
                    "Total Pelanggan Terlayani",
                    "Rata-rata Muatan per Kendaraan (kg)",
                    "Total Waktu Operasional",
                    "Dynamic Overhead Gap (%)",
                ],
                "Statis Ideal (Offline)": [
                    f"{ideal_dist:.2f}",
                    ideal_n_routes,
                    m["total_customers"],
                    f"{ideal_avg_load:.0f}",
                    f"{ideal_time_val:.4f} jam ({format_hours_to_hms(ideal_time_val)})" if ideal_time_val > 0 else "-",
                    "-",
                ],
                "Dinamis (Online DVRPTW)": [
                    f"{final_dist_val:.2f}",
                    final_n_routes,
                    m["total_customers"],
                    f"{final_avg_load:.0f}",
                    f"{m['final_time']:.4f} jam ({format_hours_to_hms(m['final_time'])})",
                    f"{m['dynamic_gap_pct']:.2f}%",
                ],
            })
            st.dataframe(comp_df, hide_index=True, use_container_width=True)

            # Interpretasi hasil
            gap = m["dynamic_gap_pct"]
            if gap > 0:
                st.info(
                    f"**Dynamic Overhead Gap: {gap:.2f}%**\n\n"
                    f"Rute Dinamis memerlukan tambahan jarak {gap_km:.2f} km "
                    f"({gap:.2f}%) dibandingkan Solusi Statis Ideal. "
                    f"Ini merupakan *Value of Information* — biaya ketidakpastian "
                    f"akibat pesanan pelanggan yang muncul terlambat."
                )
            elif gap == 0:
                st.success(
                    "Rute Dinamis berhasil menyamai efisiensi Solusi Statis Ideal! "
                    "Tidak ada tambahan biaya jarak akibat elemen dinamis."
                )
            else:
                st.success(
                    f"**Dynamic Gap: {gap:.2f}%** — "
                    f"Rute Dinamis lebih efisien dari Solusi Statis Ideal."
                )

            # Grafik perbandingan jarak (bar chart)
            st.markdown("---")
            st.markdown("#### Perbandingan Total Jarak Tempuh")
            st.caption("Membandingkan total jarak tempuh rute aktual (Dinamis) dengan batas teoritis terbaik (Statis Ideal).")
            
            fig_comp = go.Figure()
            fig_comp.add_trace(go.Bar(
                x=["Statis Ideal (Offline)"],
                y=[ideal_dist],
                name="Statis Ideal (Offline)",
                marker_color="#93C5FD",
                text=[f"{ideal_dist:.2f} km"],
                textposition="auto",
                textfont=dict(size=14, color="#0F172A", family="Inter"),
            ))
            fig_comp.add_trace(go.Bar(
                x=["Dinamis (Online)"],
                y=[final_dist_val],
                name="Dinamis (Online)",
                marker_color="#1E40AF",
                text=[f"{final_dist_val:.2f} km"],
                textposition="auto",
                textfont=dict(size=14, color="#FFFFFF", family="Inter"),
            ))
            fig_comp.update_layout(
                yaxis_title="Jarak Tempuh (km)",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                height=360,
                font=dict(family="Inter"),
                showlegend=True,
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02,
                    xanchor="center", x=0.5,
                    font=dict(size=13),
                ),
                hoverlabel=dict(font_size=12, font_family="Inter"),
            )
            st.plotly_chart(fig_comp, use_container_width=True)

            # Grafik perbandingan jarak per rute (grouped bar)
            if ideal_routes and final_routes:
                st.markdown("#### Perbandingan Jarak per Rute Kendaraan")
                st.caption("Membandingkan beban jarak tempuh masing-masing armada untuk memantau keseimbangan operasional.")
                
                max_routes = max(len(ideal_routes), len(final_routes))
                route_labels = [f"Kendaraan {i+1}" for i in range(max_routes)]
                ideal_dists = [
                    route_distance(rt.path, dist) for rt in ideal_routes
                ] + [0] * (max_routes - len(ideal_routes))
                final_dists = [
                    route_distance(rt.path, dist) for rt in final_routes
                ] + [0] * (max_routes - len(final_routes))

                fig_per_route = go.Figure()
                fig_per_route.add_trace(go.Bar(
                    x=route_labels, y=ideal_dists,
                    name="Statis Ideal",
                    marker_color="#93C5FD",
                    text=[f"{d:.1f}" for d in ideal_dists],
                    textposition="auto",
                    textfont=dict(size=14),
                ))
                fig_per_route.add_trace(go.Bar(
                    x=route_labels, y=final_dists,
                    name="Dinamis",
                    marker_color="#1E40AF",
                    text=[f"{d:.1f}" for d in final_dists],
                    textposition="auto",
                    textfont=dict(size=14),
                ))
                fig_per_route.update_layout(
                    barmode="group",
                    yaxis_title="Jarak Tempuh (km)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    height=350,
                    font=dict(family="Inter"),
                    legend=dict(
                        orientation="h", yanchor="bottom", y=1.02,
                        xanchor="center", x=0.5,
                        font=dict(size=13),
                    ),
                    hoverlabel=dict(font_size=12, font_family="Inter"),
                )
                st.plotly_chart(fig_per_route, use_container_width=True)

            # Grafik pie chart distribusi demand
            st.markdown("#### Distribusi Demand Pelanggan")
            pie_labels = []
            pie_values = []
            pie_colors = []
            for cid, c_obj in sorted(custs.items()):
                pie_labels.append(f"Plg {cid} ({'D' if c_obj.is_dynamic else 'S'})")
                pie_values.append(c_obj.demand)
                pie_colors.append("#EF4444" if c_obj.is_dynamic else "#2563EB")

            fig_pie = go.Figure(data=[go.Pie(
                labels=pie_labels,
                values=pie_values,
                marker=dict(colors=pie_colors),
                textinfo="label+percent",
                textfont=dict(size=14),
                hole=0.4,
            )])
            fig_pie.update_layout(
                height=400,
                font=dict(family="Inter"),
                paper_bgcolor="rgba(0,0,0,0)",
                legend=dict(font=dict(size=13)),
                annotations=[dict(
                    text=f"<b>{sum(pie_values):.0f} kg</b>",
                    x=0.5, y=0.5, font_size=20, showarrow=False,
                    font=dict(color="#1E3A5F", family="Inter"),
                )],
                hoverlabel=dict(font_size=12, font_family="Inter"),
            )
            st.plotly_chart(fig_pie, use_container_width=True)

            # Detail rute statis ideal
            if ideal_routes:
                with st.expander("Detail Rute Solusi Statis Ideal (Offline)"):
                    stbl = []
                    for i, rt in enumerate(ideal_routes):
                        rd = route_distance(rt.path, dist)
                        ld = sum(
                            custs[n].demand for n in rt.customers_only if n in custs
                        )
                        stbl.append({
                            "Kendaraan": f"Kendaraan {i + 1}",
                            "Rute": " → ".join(map(str, rt.path)),
                            "Muatan (kg)": f"{ld:.0f}",
                            "Jarak (km)": f"{rd:.2f}",
                        })
                    st.dataframe(
                        pd.DataFrame(stbl),
                        hide_index=True, use_container_width=True,
                    )
