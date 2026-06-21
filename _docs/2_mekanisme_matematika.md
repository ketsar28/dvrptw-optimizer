# Panduan Mekanisme Matematika DVRPTW

Dokumen ini menjelaskan dasar pemodelan matematis dari **Dynamic Vehicle Routing Problem with Time Windows (DVRPTW)** yang digunakan dalam proyek tesis Nuha. Dokumen ini dapat digunakan sebagai referensi utama penulisan Bab III (Metodologi Penelitian / Pemodelan Matematika) di draf skripsi Nuha.

---

## 📐 1. Formulasi Model Matematika DVRPTW
Permasalahan DVRPTW dimodelkan menggunakan graf terarah $G = (V, A)$, dengan:
*   $V = \{0, 1, 2, ..., n\}$ sebagai himpunan seluruh titik (*nodes*), di mana titik $0$ mewakili **Depot Pusat**, dan $V \setminus \{0\}$ mewakili himpunan **Pelanggan**.
*   $A = \{(i, j) : i, j \in V, i \neq j\}$ sebagai himpunan busur (*arcs*) yang menghubungkan antar titik.
*   $d_{ij}$ sebagai jarak tempuh dari titik $i$ ke titik $j$.
*   $t_{ij}$ sebagai waktu perjalanan dari titik $i$ ke titik $j$.
*   $q_i$ sebagai jumlah permintaan (*demand*) dari pelanggan $i$ (dengan $q_0 = 0$).
*   $s_i$ sebagai durasi pelayanan (*service time*) di pelanggan $i$ (dengan $s_0 = 0$).
*   $[e_i, l_i]$ sebagai jendela waktu (*time window*) pelanggan $i$. Di mana $e_i$ adalah batas awal pelayanan (paling cepat) dan $l_i$ adalah batas akhir pelayanan (paling lambat). Untuk depot pusat, jendela waktu $[e_0, l_0]$ menyatakan jam operasional depot (jam buka $e_0 = 4.0$ dan jam tutup $l_0 = 7.0$).
*   $K$ sebagai himpunan kendaraan homogen yang tersedia (maksimal $2$ kendaraan), dengan kapasitas muat masing-masing sebesar $Q = 2500\text{ kg}$.

### Variabel Keputusan
1.  $x_{ijk} = \begin{cases} 1, & \text{jika kendaraan } k \text{ berjalan langsung dari titik } i \text{ ke } j \\ 0, & \text{lainnya} \end{cases}$
2.  $w_{ik} = \text{Waktu mulai pelayanan kendaraan } k \text{ di titik } i$ (jika dikunjungi).

---

## 🎯 2. Fungsi Tujuan (Objective Function)
Tujuan dari model ini adalah meminimalkan total jarak perjalanan yang ditempuh oleh seluruh armada kendaraan:
$$\min \sum_{k \in K} \sum_{i \in V} \sum_{j \in V} d_{ij} x_{ijk}$$

---

## 🔒 3. Batasan-Batasan Model (Constraints)

### A. Alur Kunjungan
1.  **Setiap pelanggan dilayani tepat satu kali** oleh satu kendaraan:
    $$\sum_{k \in K} \sum_{j \in V, j \neq i} x_{ijk} = 1, \quad \forall i \in V \setminus \{0\}$$
2.  **Keseimbangan Aliran**: Kendaraan yang masuk ke suatu node pelanggan harus keluar dari node tersebut:
    $$\sum_{i \in V, i \neq p} x_{ipk} - \sum_{j \in V, j \neq p} x_{pjk} = 0, \quad \forall p \in V \setminus \{0\}, \forall k \in K$$
3.  **Awal dan Akhir Rute**: Setiap kendaraan $k$ harus memulai rute dari depot (0) dan mengakhiri perjalanan di depot (0):
    $$\sum_{j \in V \setminus \{0\}} x_{0jk} \le 1, \quad \forall k \in K$$
    $$\sum_{i \in V \setminus \{0\}} x_{i0k} \le 1, \quad \forall k \in K$$

### B. Kapasitas Kendaraan (Capacity Constraints)
Akumulasi total barang yang dikirimkan oleh kendaraan $k$ tidak boleh melebihi kapasitas maksimal kendaraan $Q = 2500\text{ kg}$:
$$\sum_{i \in V \setminus \{0\}} q_i \left( \sum_{j \in V, j \neq i} x_{ijk} \right) \le Q, \quad \forall k \in K$$

### C. Jendela Waktu (Time Windows Constraints)
1.  **Hubungan Waktu Antar Node**: Jika kendaraan $k$ berjalan dari $i$ ke $j$, pelayanan di node $j$ baru bisa dimulai setelah pelayanan di $i$ selesai ditambah waktu tempuh perjalanan $t_{ij}$:
    $$x_{ijk} = 1 \implies w_{ik} + s_i + t_{ij} \le w_{jk}$$
    *(Dalam program, formula ini disimulasikan secara deterministik untuk melacak durasi perjalanan secara presisi).*
2.  **Kelayakan Jendela Waktu**: Waktu pelayanan di setiap node harus berada dalam batas jendela waktu pelanggan:
    $$e_i \le w_{ik} \le l_i, \quad \forall i \in V, \forall k \in K$$
    Untuk depot, kendaraan harus kembali sebelum jam tutup depot ($l_0 = 7.0$ atau pukul 07:00):
    $$w_{0k} \le l_0, \quad \forall k \in K$$

---

## ⚡ 4. Aturan Dinamis & Batasan Non-Preemption
Kunci utama dari aspek dinamis (DVRPTW) pada proyek ini adalah penanganan pesanan baru yang muncul saat kendaraan sudah berada di perjalanan.

### Variabel Waktu Pemunculan ($T_{\text{reveal}}$)
Setiap pelanggan dinamis $u$ memiliki waktu muncul $T_{\text{reveal}}$ ke sistem. Pelanggan $u$ hanya boleh disisipkan ke rute kendaraan jika jam virtual saat ini $t \ge T_{\text{reveal}}$.

### Aturan Non-Preemption
Ketika pesanan dinamis $u$ masuk pada jam virtual $t$, kendaraan sedang bergerak. Program harus mendeteksi node mana saja yang **sudah dikunjungi** atau **sedang dituju** (disebut sebagai **Committed Nodes**). Node-node ini tidak boleh diubah urutannya atau disisipkan pelanggan baru di antaranya.

*   **Langkah Pelacakan**:
    Program menghitung akumulasi waktu kedatangan di setiap node pada rute saat ini:
    $$\text{Arrival Time}(path[m]) = w_{path[m], k}$$
*   **Batas Committed**:
    Indeks batas committed dihitung sebagai:
    $$\text{committed\_idx} = \max \{ m : w_{path[m], k} \le t \}$$
*   **Penyisipan Layak**:
    Pelanggan dinamis $u$ hanya boleh disisipkan pada indeks pos:
    $$\text{pos} \ge \text{committed\_idx} + 1$$
    Hal ini mencegah kendaraan berbalik arah (*non-preemption*) dan memastikan kendaraan menyelesaikan tujuannya saat ini terlebih dahulu sebelum menuju ke lokasi pelanggan dinamis baru.
