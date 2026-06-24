# DVRPTW Optimizer — Dynamic Vehicle Routing Problem with Time Windows

### Sistem Pendukung Keputusan (DSS) untuk Optimasi Rute Logistik Dinamis Berbasis Heuristik dan Pencarian Lokal

---

## Deskripsi

Aplikasi ini dikembangkan untuk menjawab tantangan manajemen logistik modern yang dinamis. Dalam operasional logistik dunia nyata, efisiensi rute perjalanan sangat krusial untuk menekan biaya operasional. Tantangan terbesar muncul ketika pesanan pelanggan baru masuk secara mendadak saat armada kendaraan sudah di perjalanan. Sistem ini memodelkan dan menyelesaikan Dynamic Vehicle Routing Problem with Time Windows (DVRPTW) menggunakan kombinasi metaheuristik modern Iterated Local Search (ILS) yang mengintegrasikan Sequential Insertion Heuristic, Cheapest Insertion, Deterministic Local Search, dan Randomized Variable Neighborhood Descent (RVND) dengan mekanisme Perturbasi.

Sistem Pendukung Keputusan (SPK) ini membantu mengoptimalkan dan mengalihkan rute secara otomatis dan presisi secara matematis, dengan tetap menjaga kelayakan rute terhadap berbagai batasan operasional real-time.

---

## Urgensi dan Latar Belakang Proyek

Perencanaan rute secara manual memiliki celah kelemahan yang besar ketika menghadapi perubahan informasi yang cepat (elemen dinamis). Sangat sulit menghitung puluhan variabel pengiriman secara serentak di bawah tekanan waktu, yang meliputi:

- **Jam Buka-Tutup Depot (Time Windows)**: Kendaraan harus kembali ke depot sebelum batas waktu operasional berakhir.
- **Kapasitas Muat Terbatas (Capacity Constraint)**: Setiap armada memiliki batas muatan homogen (maksimal 2500 kg) yang tidak boleh dilanggar.
- **Asumsi Non-Preemption**: Kendaraan yang sedang menuju ke suatu lokasi tidak boleh mendadak putar balik di tengah jalan; mereka harus menyelesaikan pengantaran ke node yang dituju (committed) sebelum beralih ke pesanan dinamis baru.
- **Overhead Jarak**: Munculnya pesanan dinamis secara mendadak memicu pembengkakan jarak tempuh (Dynamic Overhead Gap) yang harus ditekan seminimal mungkin.

### Dampak Perencanaan Rute Manual:

1. **Pembengkakan Jarak dan Biaya**: Rute tanpa perencanaan matematis memicu rute memutar, konsumsi BBM boros, dan waktu tempuh lama.
2. **Pelanggaran Batasan Jendela Waktu**: Keterlambatan akibat urutan pengiriman yang salah menurunkan kepuasan pelanggan dan reputasi pelayanan.
3. **Ketimpangan Utilitas Kendaraan**: Salah satu armada terbeban penuh sedangkan armada lainnya menganggur dengan sisa kapasitas yang besar.

---

## Solusi yang Ditawarkan

Fokus utama aplikasi ini adalah menghasilkan rute logistik dinamis yang layak (feasible) dan paling efisien dengan meminimalkan total jarak tempuh seluruh armada. Sistem mengombinasikan tiga metode utama:

1. **Sequential Insertion Heuristic**: Membangun rute awal secara sekuensial dari daftar pelanggan statis (pesanan yang diketahui sejak awal hari) dengan menyisipkan node pelanggan secara bertahap pada posisi dengan biaya minimum dengan tetap menjaga feasibility kapasitas dan jendela waktu.
2. **Cheapest Insertion**: Ketika pesanan dinamis baru muncul di tengah hari, sistem menyisipkannya ke posisi rute berjalan yang menghasilkan tambahan jarak (insertion cost) paling minimal, dengan tetap menaati batas non-preemption.
3. **Iterated Local Search (ILS) dan RVND**: Melakukan pencarian metaheuristik secara iteratif pada rute uncommitted (sisa rute yang belum ditempuh) dengan alur:
   - **Local Search (Intra-Route)**: Mengoptimalkan rute secara deterministik dengan operator 2-Opt, Or-Opt, Reinsertion, dan Exchange.
   - **RVND (Randomized Variable Neighborhood Descent)**: Mengacak penggunaan 10 operator neighborhood secara inter-route (NL) dan intra-route (NL') untuk mereduksi jarak tempuh global secara optimal:
     - **Intra-Route (NL')**: 2-Opt, Or-Opt, Reinsertion, dan Exchange.
     - **Inter-Route (NL)**: Shift(1,0), Shift(2,0), Swap(1,1), Swap(2,1), Swap(2,2), dan Cross.
   - **Perturbasi (Perturbation)**: Melakukan pengacakan layak terkontrol untuk melepaskan solusi dari jebakan optimum lokal (local optima) sebelum dievaluasi ulang oleh mesin pencarian lokal.

---

## Fitur Utama Aplikasi

- **Interactive Dashboard Web**: Antarmuka web interaktif yang modern dan premium menggunakan Streamlit dengan navigasi bersih beraksen biru profesional.
- **Otomatisasi Sistem File dan Caching Dinamis**: Membaca dataset logistik lengkap secara otomatis melalui unggahan file JSON dengan sistem path caching yang dinamis dan portabel untuk berbagai sistem operasi.
- **Penegakan Dinamis Kapasitas Armada**: Menjamin kelayakan operasional secara ketat dengan membatasi jumlah rute agar tidak melebihi kapasitas armada maksimal homogen yang dikonfigurasi oleh pengguna.
- **Reproduksibilitas Akademis (Fixed Seed)**: Dilengkapi dengan fitur Kunci Acakan (Fixed Seed) menggunakan parameter acuan acak matematis interaktif untuk menghasilkan hasil optimasi rute metaheuristik ILS dan RVND yang konsisten 100% saat dijalankan ulang.
- **Desain Antarmuka Premium dan Navigasi Sidebar**:
  - **Seamless Charts**: Seluruh kanvas visualisasi grafik memiliki latar belakang transparan (rgba(0,0,0,0)) yang menyatu langsung dengan halaman utama.
  - **Dark Navy Sidebar**: Navigasi sidebar gelap berhiaskan badge inisial N (Network/Navigation) mewah, menu interaktif yang rapi, tombol sekunder yang terintegrasi, dan kartu identitas formal yang sangat informatif.
- **MDS Spasial dan Segment Pills Kontras Tinggi**: Memproyeksikan matriks jarak multi-dimensi menjadi peta jaringan koordinat 2D (MDS) rute dinamis dengan label jarak antar segmen rute berupa mini-badge/pill berlatar belakang putih solid (#FFFFFF) dan border biru agar tidak tertutup garis rute atau panah arah.
- **Komparasi Sebelum vs Setelah Optimasi (RVND)**: Panel khusus yang membandingkan performa rute heuristik dasar vs rute yang telah disempurnakan oleh RVND secara real-time, lengkap dengan persentase efisiensi jarak dan waktu kerja secara interaktif.
- **Format Waktu Otomatis (Jam, Menit, Detik)**: Mengonversi representasi matematis jam desimal (seperti 0.9005 jam) menjadi waktu operasional lapangan yang intuitif (54 menit 2 detik) di seluruh tabel rute dan kedatangan.
- **Analisis Celah Dinamis (Dynamic Gap) dan Log Kejadian**: Menganalisis fluktuasi jarak tempuh armada secara kronologis setiap kali ada kejadian dinamis baru yang masuk ke dalam sistem.
- **Dokumentasi Terintegrasi dan Expander Konsolidasian**: Seluruh penjelasan konsep akademik (Statis Ideal vs Dinamis, Dynamic Overhead Gap) telah disatukan secara rapi menjadi satu expander panduan terpadu tanpa duplikasi teks yang membingungkan.

---

## Panduan Instalasi dan Eksekusi

### 1. Clone / Unduh Repositori

```bash
git clone https://github.com/ketsar28/dvrptw-optimizer.git
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

Aplikasi akan berjalan di http://localhost:8501

---

## Struktur Repositori

```
├── app.py              # Dashboard Streamlit Utama (UI dan Visualisasi)
├── solver.py           # Mesin Optimasi DVRPTW (Sequential Insertion, Cheapest Insertion, ILS, dan RVND)
├── theme.py            # Desain Sistem dan Gaya CSS Kustom (Professional Blue)
├── requirements.txt    # Daftar Pustaka Dependensi Python
├── README.md           # Dokumentasi Proyek
├── _data/              # Sampel Berkas JSON untuk Pengujian
└── _docs/              # Dokumen Pendukung dan Panduan Laporan Skripsi
```

---

## Alur Kerja Sistem

```
┌─────────────────────────────────────────────────────────────────┐
│                    INPUT DATA LOGISTIK                          │
│  (JSON/CSV/Excel: Depot, Pelanggan, Matriks Jarak dan Waktu)    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              FASE 1: KONSTRUKSI RUTE AWAL                       │
│  Sequential Insertion Heuristic -> Rute layak pelanggan statis   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              FASE 2: SIMULASI DINAMIS                           │
│  Time-Stepping -> Pelanggan dinamis muncul berdasarkan          │
│  Reveal Time -> Cheapest Insertion ke rute berjalan             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              FASE 3: METAHEURISTIK ILS DAN RVND                 │
│  Penyempurnaan Rute uncommitted -> Deterministic Local Search    │
│  dan RVND (10 operators: NL dan NL') -> Perturbasi              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              OUTPUT DAN VISUALISASI                             │
│  Rute Optimal, Peta Jaringan, Event Log, Analisis Gap          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Parameter Model DVRPTW

| Parameter        | Deskripsi                   | Nilai Default |
| ---------------- | --------------------------- | ------------- |
| `tw_open`        | Jam buka depot (e0)         | 4.0 (04:00)   |
| `tw_close`       | Jam tutup depot (l0)        | 7.0 (07:00)   |
| `capacity`       | Kapasitas per kendaraan (Q) | 2500 kg       |
| `speed`          | Kecepatan rata-rata         | 60 km/jam     |
| `max_vehicles`   | Jumlah kendaraan tersedia   | 2 kendaraan   |
| `time_step`      | Interval simulasi           | 0.05 jam      |

---

## Referensi Algoritma

1. **Sequential Insertion Heuristic** — Konstruksi solusi rute awal yang layak dan kokoh.
2. **Cheapest Insertion** — Penyisipan pelanggan dinamis dengan biaya tambahan minimal.
3. **Iterated Local Search (ILS) dan RVND Metaheuristic** — Optimasi pencarian lokal metaheuristik iteratif dengan perturbasi sekuensial dan 10 operator neighborhood acak (NL dan NL').

---

*Departemen Matematika - Universitas Negeri Malang*
