# Panduan Cara Menjalankan Aplikasi di Komputer Lokal

Dokumen ini menjelaskan langkah-langkah untuk mengunduh, menyiapkan lingkungan, dan menjalankan aplikasi dashboard DVRPTW secara lokal di sistem operasi Windows.

---

## 1. Unduh Berkas dari GitHub

Langkah-langkah untuk mendapatkan salinan kode program:

- Buka tautan repositori GitHub: https://github.com/ketsar28/dvrptw-optimizer
- Pilih tombol Code yang berwarna hijau di bagian kanan atas halaman.
- Pilih opsi Download ZIP.
- Ekstrak berkas ZIP yang telah diunduh ke dalam direktori penyimpanan komputer (misalnya Documents atau Desktop).

---

## 2. Buka Folder Melalui Command Prompt (CMD)

Langkah-langkah untuk membuka terminal langsung di direktori proyek:

- Buka Windows Explorer dan masuk ke dalam folder hasil ekstraksi yang berisi berkas app.py dan solver.py.
- Klik pada address bar (kolom alamat folder di bagian atas Windows Explorer).
- Hapus seluruh teks alamat yang ada pada address bar tersebut, ketik cmd, kemudian tekan Enter.
- Jendela Command Prompt akan otomatis terbuka dan langsung mengarah pada direktori aktif folder tersebut.

---

## 3. Buka VS Code

Langkah-langkah untuk membuka teks editor VS Code melalui terminal:

- Pada jendela Command Prompt yang telah terbuka di direktori aktif, ketik perintah berikut:
  ```Python
  code .
  ```
- Tekan Enter. Aplikasi VS Code akan terbuka dan otomatis memuat seluruh berkas proyek.

---

## 4. Jalankan Aplikasi Streamlit

Langkah-langkah untuk menjalankan server lokal aplikasi:

- Di dalam VS Code, buka terminal baru dengan cara memilih menu Terminal di bar atas, kemudian pilih New Terminal.
- Sebelum menjalankan aplikasi, pastikan Python dan seluruh pustaka pendukung sudah terinstal. Pustaka dapat diinstal melalui terminal dengan mengetik perintah berikut:
  ```Python
  pip install -r requirements.txt
  ```
- Jalankan server Streamlit dengan memasukkan perintah berikut pada terminal:
  ```Python
  streamlit run app.py
  ```
- Tekan Enter. Peramban (browser) web akan otomatis terbuka dan menampilkan halaman dashboard optimasi DVRPTW secara lokal pada alamat http://localhost:8501.
