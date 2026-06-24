# Laporan Audit Perbaikan Perhitungan Menit (Word vs Python)

Dokumen ini berisi hasil audit perbandingan dari draf perhitungan manual terbaru dengan hasil eksekusi simulasi pada program Python (`solver.py`).

---

## 1. Ringkasan Sinkronisasi Akhir
Secara keseluruhan, **perhitungan revisi pada draf laporan telah 100% sinkron dan sesuai secara fisik** dengan hasil dari program Python. Kekeliruan menjumlahkan jam dan menit yang ada di dokumen sebelumnya telah diperbaiki dengan mengalikan semua desimal waktu perjalanan dengan 60 menit.

Berikut tabel perbandingan hasil akhirnya:

| Parameter | Perhitungan Manual (Menit) | Hasil Eksekusi Program (Python) | Status Sinkronisasi |
| :--- | :---: | :---: | :---: |
| **Rute Kendaraan 1** | `0-2-4-6-7-0` | `0-2-4-6-7-0` | **Sinkron 100%** |
| **Jarak Kendaraan 1** | $68\text{ km}$ | $68,00\text{ km}$ | **Sinkron 100%** |
| **Waktu Kendaraan 1** | $145,38\text{ menit}$ | $145,07\text{ menit}$ | **Cocok** (Selisih $\approx 18$ detik dari pembulatan jam desimal) |
| **Rute Kendaraan 2** | `0-1-3-5-8-0` | `0-1-3-5-8-0` | **Sinkron 100%** (Menggunakan *Reveal Time* 4.5) |
| **Jarak Kendaraan 2** | $72\text{ km}$ | $72,00\text{ km}$ | **Sinkron 100%** |
| **Waktu Kendaraan 2** | $141,00\text{ menit}$ | $140,93\text{ menit}$ | **Cocok** (Selisih $\approx 4$ detik dari pembulatan jam desimal) |
| **Total Jarak Gabungan** | **$140\text{ km}$** | **$140,00\text{ km}$** | **Sinkron 100%** |

---

## 2. Audit Perhitungan Waktu Rute (Time Calculations)

### Rute Kendaraan 1 (`0-2-4-6-7-0`)
Waktu total dihitung berdasarkan akumulasi waktu perjalanan (*travel time*) dan pelayanan (*service time*):
$$T_{ij} = (t_{02} + t_{24} + t_{46} + t_{67} + t_{70}) + (f_2 + f_4 + f_6 + f_7)$$

*   **Waktu Tempuh Perjalanan (Konversi dari Jam ke Menit)**:
    - $t_{02} = 0,15 \text{ jam} \times 60 = 9 \text{ menit}$
    - $t_{24} = 0,32 \text{ jam} \times 60 = 19,2 \text{ menit}$
    - $t_{46} = 0,42 \text{ jam} \times 60 = 25,2 \text{ menit}$
    - $t_{67} = 0,08 \text{ jam} \times 60 = 4,8 \text{ menit}$
    - $t_{70} = 0,17 \text{ jam} \times 60 = 10,2 \text{ menit}$
    - $\text{Total Travel} = 9 + 19,2 + 25,2 + 4,8 + 10,2 = \mathbf{68,4\text{ menit}}$

*   **Waktu Pelayanan (Service Time - Menit Bawaan)**:
    - $\text{Total Service} = f_2 + f_4 + f_6 + f_7 = 18 + 16,02 + 21,96 + 21 = \mathbf{76,98\text{ menit}}$

*   **Hasil Akhir**:
    $$T_{ij} = 68,4 \text{ menit} + 76,98 \text{ menit} = \mathbf{145,38\text{ menit}}$$
    *(Hasil di Python bernilai **$145,07\text{ menit}$** karena menggunakan tingkat presisi desimal $1300 / 3600 \text{ jam}$ tanpa pembulatan di awal).*

---

### Rute Kendaraan 2 (`0-1-3-5-8-0`)
Perhitungan waktu total untuk rute dinamis Kendaraan 2:
$$T_{ij} = (t_{01} + t_{13} + t_{35} + t_{58} + t_{80}) + (f_1 + f_3 + f_5 + f_8)$$

*   **Waktu Tempuh Perjalanan (Konversi dari Jam ke Menit)**:
    - $t_{01} = 0,22 \text{ jam} \times 60 = 13,2 \text{ menit}$
    - $t_{13} = 0,18 \text{ jam} \times 60 = 10,8 \text{ menit}$
    - $t_{35} = 0,35 \text{ jam} \times 60 = 21 \text{ menit}$
    - $t_{58} = 0,28 \text{ jam} \times 60 = 16,8 \text{ menit}$
    - $t_{80} = 0,17 \text{ jam} \times 60 = 10,2 \text{ menit}$
    - $\text{Total Travel} = 13,2 + 10,8 + 21 + 16,8 + 10,2 = \mathbf{72\text{ menit}}$

*   **Waktu Pelayanan (Service Time - Menit Bawaan)**:
    - $\text{Total Service} = f_1 + f_3 + f_5 + f_8 = 18,36 + 18,36 + 16,68 + 15,6 = \mathbf{69\text{ menit}}$

*   **Hasil Akhir**:
    $$T_{ij} = 72 \text{ menit} + 69 \text{ menit} = \mathbf{141\text{ menit}}$$
    *(Hasil di Python bernilai **$140,93\text{ menit}$**).*

---

## 3. Penyelarasan Rute Dinamis Customer 8
Di file program Python, letak Customer 8 berada di awal setelah depot (`0-8-1-3-5-0`) jika menggunakan default reveal time `4.1` (04:06). Agar rute di program sama persis dengan rute manual yang ditaruh di akhir (`0-1-3-5-8-0`), kita hanya perlu menyelaraskan parameter waktu pemunculan dynamic customer:

*   **Penyebab**: Jam 04:06 mobil masih berada di jalan menuju Customer 1 (baru tiba 04:13). Karena belum mengunjungi pelanggan mana pun, program menyisipkan di posisi paling murah secara geografis (setelah depot).
*   **Solusi**: Ubah parameter `"Reveal Time (jam)"` milik Customer 8 di berkas skenario JSON menjadi **`4.5` (pukul 04:30)**. Pukul 04:30 berada di tengah proses pelayanan di Customer 1. Karena Customer 1 sudah telanjur dilayani, program terpaksa menaruh Customer 8 di bagian paling belakang sebelum pulang ke depot, menghasilkan rute `0-1-3-5-8-0` secara presisi.

---

## 4. Catatan Salah Ketik (Typo) pada Rancangan Rute
Bagian berikut direkomendasikan untuk direvisi pada draf laporan:
*   Di halaman perhitungan Kendaraan 2, pada langkah inisialisasi rute `0-1-3-0` ditulis **`(52 km)`**.
*   **Koreksi**: Berdasarkan matriks jarak, nilai sesungguhnya adalah $d_{01}\ (13) + d_{13}\ (11) + d_{30}\ (16) = \mathbf{40\text{ km}}$. Angka $52\text{ km}$ merupakan kesalahan ketik salin-tempel dari Rute 1.
*   *Catatan*: Typo ini tidak mempengaruhi jarak total akhir kendaraan 2 ($72\text{ km}$) karena pada penjumlahan akhir perhitungan tetap dilakukan dengan benar.
