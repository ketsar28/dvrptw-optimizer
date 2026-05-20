# 🚚 DVRPTW Optimizer — Dynamic Vehicle Routing Problem with Time Windows
### Sistem Pendukung Keputusan (DSS) untuk Optimasi Rute Logistik Dinamis Berbasis Heuristik & Pencarian Lokal

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit.io)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📋 Deskripsi

Aplikasi ini dikembangkan untuk menjawab tantangan manajemen logistik modern yang dinamis. Dalam operasional logistik dunia nyata, efisiensi bukan lagi sekadar pilihan, melainkan keharusan untuk bertahan. Namun, tantangan terbesar muncul ketika **pesanan pelanggan baru masuk secara mendadak** saat armada kendaraan sudah di perjalanan. Bagaimana menentukan rute terbaik secara real-time tanpa mengganggu pengiriman yang sedang berjalan?

Sistem Pendukung Keputusan (SPK) cerdas ini dibangun secara khusus untuk memodelkan dan menyelesaikan **Dynamic Vehicle Routing Problem with Time Windows (DVRPTW)** menggunakan kombinasi algoritma **Nearest Neighbor**, **Cheapest Insertion**, dan **Randomized Variable Neighborhood Descent (RVND)**. Proses penjadwalan dan pengalihan rute dinamis yang sebelumnya rawan *human error* kini dapat dioptimalkan secara otomatis dan presisi secara matematis.

---

## 📋 Mengapa Proyek Ini Penting?

Berdasarkan studi kasus logistik, perencanaan rute secara manual memiliki celah kelemahan yang sangat besar ketika menghadapi perubahan informasi yang cepat (elemen dinamis). Manusia sangat kesulitan menghitung puluhan variabel pengiriman secara serentak di bawah tekanan waktu, yang meliputi:

- **Jam Buka-Tutup Depot (Time Windows)**: Kendaraan harus kembali ke depot sebelum batas waktu operasional berakhir.
- **Kapasitas Muat Terbatas (Capacity Constraint)**: Setiap armada memiliki batas muatan homogen (maksimal 2.500 kg) yang tidak boleh dilanggar.
- **Asumsi Non-Preemption**: Kendaraan yang sedang menuju ke suatu lokasi tidak boleh mendadak putar balik di tengah jalan; mereka harus menyelesaikan pengantaran ke node yang dituju (*committed*) sebelum beralih ke pesanan dinamis baru.
- **Overhead Jarak**: Munculnya pesanan dinamis secara mendadak memicu pembengkakan jarak tempuh (*Dynamic Overhead Gap*) yang harus ditekan seminimal mungkin.

### Dampak Negatif Rute Manual (Dasar Perancangan Sistem):

1. **📈 Pembengkakan Biaya & Jarak**: Rute tanpa perencanaan matematis memicu rute memutar, konsumsi BBM boros, dan waktu tempuh lama.
2. **⏰ Pelanggaran Jendela Waktu**: Keterlambatan akibat salah urutan pengiriman menurunkan kepuasan pelanggan dan reputasi perusahaan.
3. **⚖️ Ketimpangan Utilitas Kendaraan**: Salah satu armada terbebani penuh sedangkan armada lainnya menganggur dengan sisa kapasitas yang besar.

---

## 🎯 Solusi yang Ditawarkan

Fokus utama aplikasi ini adalah menghasilkan rute logistik dinamis yang **layak (feasible)** dan **paling efisien** dengan meminimalkan total jarak tempuh seluruh armada. Sistem mengombinasikan tiga algoritma tangguh:

1. **Nearest Neighbor Heuristic**: Membangun rute awal secara cepat dari daftar pelanggan statis (pesanan yang sudah diketahui sejak awal hari) dengan mencari pelanggan terdekat yang masih layak dikunjungi.
2. **Cheapest Insertion**: Ketika pesanan dinamis baru muncul di tengah hari, sistem menyisipkannya ke posisi rute berjalan yang menghasilkan tambahan jarak (*insertion cost*) paling minimal, dengan tetap menaati batas non-preemption.
3. **Randomized Variable Neighborhood Descent (RVND)**: Melakukan optimasi lokal (*local search*) secara iteratif pada sisa rute yang belum ditempuh menggunakan **5 struktur lingkungan (neighborhood structures)** secara acak untuk menata ulang urutan pengiriman agar lebih pendek:
   - *Intra-Route Operators*: **2-Opt**, **Or-Opt**, **Exchange** (mengoptimalkan urutan dalam satu rute).
   - *Inter-Route Operators*: **Relocate**, **Swap(1,1)** (memindahkan atau menukar pelanggan antar rute untuk menyeimbangkan muatan).

---

## ⚙️ Fitur Utama Aplikasi

- **💻 Interactive Dashboard Web**: Antarmuka web interaktif yang modern dan premium menggunakan Streamlit dengan navigasi bersih beraksen biru profesional.
- **📥 File System Automation**: Membaca dataset logistik lengkap (informasi depot, daftar pelanggan statis & dinamis, matriks jarak, dan matriks waktu) secara otomatis melalui unggahan file JSON.
- **🗺️ Multidimensional Scaling (MDS) Map**: Memproyeksikan matriks jarak multi-dimensi menjadi peta jaringan koordinat 2D yang akurat secara spasial sehingga pengguna dapat melihat rute aktual kendaraan.
- **⚡ Sebelum vs Setelah Optimasi (RVND)**: Panel khusus yang membandingkan performa rute heuristik dasar vs rute yang telah disempurnakan oleh RVND secara real-time, lengkap dengan persentase efisiensi jarak dan waktu kerja.
- **🕒 Automatic HMS Time Formatter**: Mengonversi representasi matematis jam desimal (seperti `0.9005 jam`) menjadi waktu operasional lapangan yang intuitif (`54 menit 2 detik`) di seluruh tabel rute dan kedatangan.
- **📊 Dynamic Gap & Event Log Analyzer**: Menganalisis fluktuasi jarak tempuh armada secara kronologis setiap kali ada kejadian dinamis baru yang masuk ke dalam sistem.
- **📝 Inline Documentation**: Setiap metrik dan visualisasi dilengkapi expander penjelasan dinamis yang menampilkan nilai aktual dari hasil perhitungan.

---

## 🛠️ Instalasi & Eksekusi Cepat

### 1. Clone / Unduh Repositori

```bash
git clone https://github.com/username-anda/dvrptw-optimizer.git
cd dvrptw-optimizer
```

### 2. Instal Dependensi

Pastikan Python 3.9+ telah terinstal, kemudian jalankan:

```bash
pip install -r requirements.txt
```

### 3. Jalankan Dashboard Streamlit

```bash
streamlit run app.py
```

Aplikasi akan berjalan di `http://localhost:8501`

---

## 📁 Struktur Kode Proyek

```
├── app.py              # Dashboard Streamlit Utama (UI & Visualisasi)
├── solver.py           # Mesin Optimasi DVRPTW (NN, Insertion, & RVND)
├── theme.py            # Desain Sistem & Gaya CSS Kustom (Professional Blue)
├── requirements.txt    # Daftar Pustaka Dependensi Python
├── README.md           # Dokumentasi Proyek
└── _data/              # Sampel Berkas JSON untuk Pengujian
```

---

## 📊 Alur Kerja Sistem

```
┌─────────────────────────────────────────────────────────────────┐
│                    INPUT DATA LOGISTIK                          │
│  (JSON/CSV/Excel: Depot, Pelanggan, Matriks Jarak & Waktu)     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              FASE 1: KONSTRUKSI RUTE AWAL                       │
│  Nearest Neighbor Heuristic → Rute dari pelanggan statis       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              FASE 2: SIMULASI DINAMIS                           │
│  Time-Stepping → Pelanggan dinamis muncul berdasarkan          │
│  Reveal Time → Cheapest Insertion ke rute berjalan             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              FASE 3: OPTIMASI RVND                              │
│  Local Search pada uncommitted nodes → 5 neighborhood          │
│  structures (2-Opt, Or-Opt, Exchange, Relocate, Swap)          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              OUTPUT & VISUALISASI                               │
│  Rute Optimal, Peta Jaringan, Event Log, Analisis Gap          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔬 Parameter Model DVRPTW

| Parameter | Deskripsi | Nilai Default |
|-----------|-----------|---------------|
| `tw_open` | Jam buka depot (e₀) | 4.0 (04:00) |
| `tw_close` | Jam tutup depot (l₀) | 7.0 (07:00) |
| `capacity` | Kapasitas per kendaraan (Q) | 2.500 kg |
| `speed` | Kecepatan rata-rata | 60 km/jam |
| `max_vehicles` | Jumlah kendaraan tersedia | 2 kendaraan |
| `time_step` | Interval simulasi | 0.05 jam |

---

## 📚 Referensi Algoritma

1. **Nearest Neighbor Heuristic** — Konstruksi solusi awal dengan greedy approach
2. **Cheapest Insertion** — Penyisipan pelanggan dinamis dengan biaya tambahan minimal
3. **RVND (Randomized Variable Neighborhood Descent)** — Optimasi lokal dengan randomisasi urutan operator


---

*© 2026 — Farida Nuha · Program Studi Matematika - Universitas Negeri Malang*
