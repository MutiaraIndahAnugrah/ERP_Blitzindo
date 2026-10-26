# Deploy background asset compression

Belum dijalankan di production. Lakukan review dan UAT dahulu. Source berada di branch feature/background-asset-compression; app/package tetap kulkul_erp. Jangan mengganti seluruh app production dengan snapshot lain tanpa meninjau perubahan vendor yang mungkin lebih baru.

## Prasyarat

- Backup database, site_config, common_site_config, hooks dan source release sebelumnya; simpan backup di lokasi privat.
- Python/Pillow/PyPDF2 kompatibel dengan Frappe yang terpasang. Lokal teruji: Python 3.9, Pillow 9.0.1, PyPDF2 1.26.0, RQ 1.8.1. Ini versi existing yang diuji, bukan rekomendasi mempertahankan versi lama tanpa patch keamanan.
- Ghostscript dengan patch keamanan distro terpasang sebagai executable gs. Di staging/local Ubuntu: sudo apt-get install ghostscript. Jangan upload binary lokal ke production.
- Verifikasi layout storage fisik; symlink dan remote storage saat ini dilewati. Cocokkan dengan fungsi backup/storage vendor yang benar-benar aktif di production.
- Sediakan ruang sementara dan memori; satu worker kompresi awal. Tidak mengirim dokumen ke layanan kompresi eksternal.

## Pasang source dengan fitur OFF

Deploy hanya perubahan yang sudah direview: direktori kulkul_erp/asset_compression, DocType asset_compression_job baru, penambahan File.after_insert serta scheduler dispatcher pada hooks.py. Jika sudah ada hook File/scheduler vendor, gabungkan dan pertahankan handler existing. Jangan menimpa semua hooks dengan versi lokal.

```bash
cd ~/frappe-bench
bench --site NAMA_SITE set-config asset_compression_enabled 0
```

Tambahkan DocType secara terarah melalui console sebagai operator berwenang. Tidak harus migrate seluruh metadata aplikasi lama hanya untuk satu tabel tambahan:

```python
import frappe
frappe.reload_doc('kulkul_erp', 'doctype', 'asset_compression_job', force=True)
from frappe.core.doctype.scheduled_job_type.scheduled_job_type import sync_jobs
sync_jobs()
frappe.db.commit()
frappe.clear_cache()
```

Apabila tim memilih bench migrate sesuai SOP, uji staging dahulu: baseline pernah mempunyai masalah panjang data/sql_mode. Jangan mengubah SQL mode production hanya untuk memaksa migrasi.

## Konfigurasi antrean dan site

Gabungkan ke common_site_config.json, jangan mengganti konfigurasi lain:

```json
{"workers": {"asset_compression": {"timeout": 180, "background_workers": 1}}}
```

Atur site_config dengan nilai numerik:

```bash
bench --site NAMA_SITE set-config asset_compression_target_bytes 2097152
bench --site NAMA_SITE set-config asset_compression_max_input_bytes 104857600
```

Batas input processing 100 MiB tidak otomatis menaikkan batas HTTP upload. Bila disetujui kapasitasnya, sesuaikan max_file_size site menjadi 104857600 dan client_max_body_size proxy agar mengizinkan multipart 100 MiB beserta overhead. Cocokkan timeout, memory dan ruang temporary server. Ini batas operasional, bukan penolakan setiap file >2 MiB. Tidak menjanjikan upload tak terbatas. Jangan menurunkan batas existing production tanpa review.

Jalankan worker khusus dengan process manager yang sudah dipakai server:

```bash
bench worker --queue asset_compression
```

Supervisor/systemd harus menjalankan worker ini terus, restart ketika gagal, dengan user pemilik bench. Gunakan generator konfigurasi/process manager bench yang sesuai instalasi, review diff sebelum reload. `background_workers: 1` mendefinisikan queue tetapi tidak menjamin proses worker otomatis sudah hidup.

Scheduler production yang existing harus berjalan agar dispatcher cron tiap menit aktif. Jangan menyalin mute_emails atau menonaktifkan scheduler production seperti lingkungan uji lokal. Restart proses web/worker sesuai SOP agar Python/hook baru termuat; clear-cache saja tidak memuat ulang modul yang sudah diimport worker.

## Aktifkan setelah prasyarat lulus

```bash
bench --site NAMA_SITE clear-cache
bench --site NAMA_SITE set-config asset_compression_enabled 1
```

Cek satu upload sintetis lewat website: original langsung bisa dibuka, pengguna lanjut bekerja, job Pending -> Queued -> Done/Skipped, URL tetap dan file valid. Lanjutkan UAT dokumen nyata yang disimpan terbatas: paspor/MRZ, QR/barcode, visa, stempel, orientasi, transparansi, scan multipage, signed/encrypted/interactive PDF, public/private, penghapusan file dan referensi bersama. Pantau CPU/RAM, I/O, antrean, Failed, ukuran dan keterbacaan. Semua form standar memakai handler yang sama; form custom/portal tetap perlu smoke test.

## Operasional lokal yang sudah dipasang

Pada blitz.local, target 2 MiB dan batas intake/processing 100 MiB telah dikonfigurasi; Ghostscript terpasang. Backup pengaturan awal ada di private/backups/asset_compression_before_20261026, termasuk hooks dan konfigurasi. Jangan commit isi backup.

Scheduler umum lokal tidak perlu diaktifkan. Layanan development khusus polling tiap 15 detik dan menjalankan satu worker burst:

```bash
cd ~/frappe-bench
bench --site blitz.local execute kulkul_erp.asset_compression.local_service.run
```

Layanan ini hanya menerima blitz.local dan memiliki lock satu instance. PID disimpan di private/asset_compression/local-service.pid. Untuk menjalankan tes yang mengendalikan job secara manual, hentikan layanan lokal dahulu supaya tidak mengambil fixture tes. Setelah selesai, jalankan kembali. Layanan hanya hidup selama proses/WSL hidup; setelah reboot perlu dijalankan ulang. Production menggunakan scheduler dan supervised worker, bukan helper ini.

Tes lokal dari sites/ (sesuaikan path checkout):

```bash
../env/bin/python ~/projects/ERP_Blitzindo/tests/test_asset_compression.py
```

Tes memakai data sintetis dan membersihkannya. Tidak dijalankan di production.

## Rollback / hentikan fitur

1. Set asset_compression_enabled menjadi 0 (angka), kemudian restart worker atau biarkan job aktif menyelesaikan pemeriksaan sebelum swap. Proses berat yang sudah berlangsung tidak seketika dibatalkan oleh perubahan config; job membaca konfigurasi saat koneksi dibuat.
2. Hentikan worker kompresi melalui process manager. Hook pencatatan menjadi no-op dan dispatcher tidak mengirim tugas baru. Upload standar tetap berjalan.
3. Jika ada job Processing/Failed dengan jurnal atau .original, jangan hapus tabel/berkas sebelum replay atau pemulihan manual diperiksa. Restart pada kode recovery yang sama dahulu bila diperlukan.
4. Source hook dapat dilepas setelah tidak ada recovery tertunda. Tabel job boleh dipertahankan sebagai audit; tidak perlu menghapus File, invoice atau transaksi.
5. Restore batas max_file_size/proxy sebelumnya hanya jika perubahan batas upload memang perlu dibatalkan dan disepakati. Pertahankan perubahan konfigurasi lain yang terjadi setelah backup.

File yang sudah sukses diperkecil tidak kembali otomatis menjadi original ketika fitur dimatikan. Pemulihan penuh dokumen tersebut memerlukan backup eksternal. Karena itu UAT dan strategi backup harus disetujui sebelum production. Original tidak disimpan permanen dua kali di disk ERP.
