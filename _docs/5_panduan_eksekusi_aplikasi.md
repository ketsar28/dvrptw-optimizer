# Panduan Cara Menjalankan Aplikasi di Komputer Lokal

Dokumen ini menjelaskan langkah-langkah untuk mengunduh, menyiapkan lingkungan, dan menjalankan aplikasi dashboard DVRPTW secara lokal di sistem operasi Windows.

---

## 1. Mendapatkan Berkas Proyek

Terdapat dua opsi untuk mendapatkan berkas proyek, baik melalui GitHub maupun Google Drive.

### Opsi A: Melalui GitHub
- Buka tautan repositori GitHub: https://github.com/ketsar28/dvrptw-optimizer
- Pilih tombol Code yang berwarna hijau di bagian kanan atas halaman.
- Pilih opsi Download ZIP.
- Ekstrak berkas ZIP yang telah diunduh ke dalam direktori penyimpanan komputer (misalnya Documents atau Desktop).

### Opsi B: Melalui Google Drive
- Buka tautan folder Google Drive: https://drive.google.com/drive/folders/1uIFANk-9ww8SpLWHF_WQoJTA1sdLoRbk
- Masuk ke folder **PROGRAM** dan unduh folder tersebut (Google Drive akan otomatis mengompresnya menjadi berkas ZIP).
- Ekstrak berkas ZIP hasil unduhan ke komputer.
- **Penting**: Pastikan seluruh struktur berkas di dalam folder hasil ekstraksi tetap utuh dan berada dalam satu tingkat direktori yang sama, yaitu:
  - Folder: `_data`
  - Folder: `.streamlit`
  - Berkas: `.gitignore`
  - Berkas: `app.py`
  - Berkas: `README.md`
  - Berkas: `requirements.txt`
  - Berkas: `solver.py`
  - Berkas: `theme.py`

---

## 2. Buka Folder Melalui Command Prompt (CMD)

Langkah-langkah untuk membuka terminal langsung di direktori proyek:
- Buka Windows Explorer dan masuk ke dalam folder proyek hasil unduhan/ekstraksi (yang berisi berkas app.py dan solver.py).
- Klik pada address bar (kolom alamat folder di bagian atas Windows Explorer).
- Hapus seluruh teks alamat yang ada pada address bar tersebut, ketik cmd, kemudian tekan Enter.
- Jendela Command Prompt akan otomatis terbuka dan langsung mengarah pada direktori aktif folder tersebut.

---

## 3. Buka VS Code

Langkah-langkah untuk membuka teks editor VS Code melalui terminal:
- Pada jendela Command Prompt yang telah terbuka di direktori aktif, ketik perintah berikut:
  ```
  code .
  ```
- Tekan Enter. Aplikasi VS Code akan terbuka dan otomatis memuat seluruh berkas proyek.

---

## 4. Jalankan Aplikasi Streamlit

Langkah-langkah untuk menjalankan server lokal aplikasi:
- Di dalam VS Code, buka terminal baru dengan cara memilih menu Terminal di bar atas, kemudian pilih New Terminal.
- Sebelum menjalankan aplikasi, pastikan Python dan seluruh pustaka pendukung sudah terinstal. Pustaka dapat diinstal melalui terminal dengan mengetik perintah berikut:
  ```
  pip install -r requirements.txt
  ```
- Jalankan server Streamlit dengan memasukkan perintah berikut pada terminal:
  ```
  streamlit run app.py
  ```
- Tekan Enter. Peramban (browser) web akan otomatis terbuka dan menampilkan halaman dashboard optimasi DVRPTW secara lokal pada alamat http://localhost:8501.
