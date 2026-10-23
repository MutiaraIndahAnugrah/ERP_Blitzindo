# Deploy rincian Sales Invoice ke production

Paket ini hanya mengubah blok items pada Print Format Builder. Tidak perlu migrate, build, restore database lokal, atau mengunggah seluruh aplikasi. Eksekusi production dilakukan oleh lead/Kulkul setelah menyetujui perubahan.

## File yang dikirim

- invoice_print/items.html: template Jinja final; satu-satunya payload runtime. Upload file ini dengan nama items.html.
- deployment.md: panduan ini.

Jangan deploy install.py: skrip itu khusus blitz.local. Jangan upload previews, backup, site_config.json, hooks.py lokal, paket blitz-invoice-attachment, atau data invoice contoh. self_test.py opsional untuk pemeriksaan di staging, bukan dependensi runtime.

## Perilaku versi ini

Rincian diambil dinamis melalui Invoice Item -> Detail Order (atau exact Sales Order Item) -> rincian TKA. Harga / UOM menggunakan rate item invoice. Total tagihan menggunakan amount invoice. Seluruh rincian sumber tetap tampil walaupun jumlah sumber berbeda dari qty tagihan. Data master yang berubah dapat mengubah hasil cetak ulang. Kolom kosong disembunyikan; tidak ada pemilihan orang otomatis. Data dan flow transaksi tidak berubah.

## 1. Persiapan oleh operator production

1. Pastikan persetujuan lead/Kulkul dan akses operator yang sesuai.
2. Catat nama Print Format Sales Invoice yang sebenarnya dipakai di production. Contoh perintah memakai PPN TEST; ganti jika berbeda. Jangan menganggap default production sama dengan lokal.
3. Pastikan format tersebut Print Format Builder, bukan custom_format. Langkah di bawah akan berhenti jika tidak sesuai.
4. Pastikan field dan doctypes sumber tersedia seperti di staging/local: Sales Invoice Item.detail_order, so_detail, sales_order; Sales Order Item.detail_order; Detail Order.details dan wo_number; Detail Order Items.data_tka, nama_tka, foreign_name, no_passport_tka, jangka_waktu; Tenaga Kerja.full_name, nama_asing, no_passport; Result Document.tka, work_orders, visa, docstatus.
5. Jika paket lampiran lama pernah dipasang di production, periksa hooks validasi/JS dahulu. Paket cetak ini tidak memasang ataupun melepas integrasi lama. Jangan menyalin hooks.py lokal untuk membersihkannya.
6. Coba di staging dengan akun staf invoice, termasuk izin baca Detail Order, Tenaga Kerja, dan Result Document. Jangan membuka izin luas hanya supaya rincian muncul.
7. Backup database production sesuai prosedur yang ada. Tidak perlu mematikan scheduler/email/webhook production untuk mengganti Print Format. Jangan menyalin pengaturan pengaman lokal.

Contoh pada server, dari user pemilik bench:

```bash
cd ~/frappe-bench
bench --site NAMA_SITE_PRODUCTION backup
mkdir -p ~/invoice-print-release
```

Upload hanya items.html ke ~/invoice-print-release/items.html melalui SFTP/SCP yang biasa digunakan. Konfirmasi nama site production aktual di server; jangan menyalin nama site lokal.

## 2. Buat format uji tanpa mengganti cetakan aktif

```bash
cd ~/frappe-bench
bench --site NAMA_SITE_PRODUCTION console
```

Jalankan blok Python berikut di console. Nama preview harus belum ada. Bila ada, hentikan dan gunakan nama baru, jangan menimpa format yang belum diperiksa.

```python
import frappe, json
from pathlib import Path
from datetime import datetime
from frappe.utils.jinja import get_jenv

TARGET = 'PPN TEST'  # sesuaikan format production
PREVIEW = TARGET + ' - Rincian Review'
source = frappe.get_doc('Print Format', TARGET)
assert source.doc_type == 'Sales Invoice'
assert source.print_format_builder and not source.custom_format
assert not frappe.db.exists('Print Format', PREVIEW)
template = Path.home().joinpath('invoice-print-release/items.html').read_text(encoding='utf8')
assert 'blitz-dynamic-source-items-v1' in template
get_jenv().from_string(template)
fields = json.loads(source.format_data or '[]')
matches = [i for i, field in enumerate(fields) if field.get('fieldname') == 'items' or 'blitz-dynamic-source-items-v1' in (field.get('options') or '')]
assert len(matches) == 1, 'Blok items tidak tunggal: periksa manual, jangan lanjut.'
backup = Path(frappe.get_site_path('private', 'backups', 'invoice_print_' + datetime.now().strftime('%Y%m%d_%H%M%S')))
backup.mkdir(parents=True, exist_ok=False)
backup.joinpath('before.json').write_text(json.dumps(source.as_dict(), default=str, ensure_ascii=False, indent=2), encoding='utf8')
fields[matches[0]] = dict(fieldname='_custom_html', fieldtype='HTML', print_hide=0, label='', options=template)
review = frappe.copy_doc(source)
review.name = PREVIEW
review.standard = 'No'
review.disabled = 0
review.format_data = json.dumps(fields, ensure_ascii=False)
review.insert()
frappe.db.commit()
print('Format review:', PREVIEW)
print('Backup:', str(backup.resolve()))
```

Bila ada exception, jalankan `frappe.db.rollback()` dan berhenti. Catat path backup yang dicetak. Keluar console dengan `exit()`.

## 3. Uji melalui website

1. Buka Sales Invoice -> klik ikon printer -> pilih format review secara manual. Format default belum diganti.
2. Cek DPKK, CCEPC, dan beberapa invoice lain: sumber lengkap, sumber kosong, sumber lebih banyak dari qty, harga berbeda, dan invoice tanpa SO.
3. Cocokkan qty dan total dengan invoice asli. Untuk DPKK contoh: qty 13, rate 11.921.000, amount 154.973.000; kelompok 12 bulan qty 3, rate 20.580.000, amount 61.740.000. Data production mungkin berbeda; gunakan nilai dokumen production.
4. Pastikan grouping tidak menggabungkan harga/UOM/durasi berbeda. Harga pada semua rincian adalah tarif per unit invoice; bukan penjumlahan tagihan atas semua orang sumber.
5. Cek header, logo, pelanggan, pajak, diskon, grand total, rekening dan tanda tangan tetap mengikuti format production.
6. Uji PDF melalui tombol PDF, seluruh halaman, huruf Mandarin, pemotongan baris dan tabel panjang. Uji dengan akun staf sehari-hari, bukan hanya Administrator. Preview memuat data pribadi, simpan di tempat terbatas.

## 4. Aktifkan setelah review disetujui

Buka console lagi. Ganti path BACKUP dengan path absolut yang dicatat pada langkah 2. Pemeriksaan membatalkan langkah bila format aktif telah berubah sejak backup.

```python
import frappe, json
from pathlib import Path
TARGET = 'PPN TEST'
PREVIEW = TARGET + ' - Rincian Review'
BACKUP = '/PATH/ABSOLUT/DARI/LANGKAH/2/before.json'
before = json.loads(Path(BACKUP).read_text(encoding='utf8'))
active = frappe.get_doc('Print Format', TARGET)
assert before['name'] == TARGET
assert active.modified == frappe.utils.get_datetime(before['modified']) or str(active.modified) == str(before['modified']), 'Format aktif berubah; review ulang.'
assert active.format_data == before.get('format_data'), 'Format aktif berubah; review ulang.'
review = frappe.get_doc('Print Format', PREVIEW)
assert review.doc_type == 'Sales Invoice' and review.print_format_builder and not review.custom_format
assert 'blitz-dynamic-source-items-v1' in review.format_data
active.format_data = review.format_data
active.save()
frappe.db.commit()
frappe.clear_cache(doctype='Print Format')
```

Bila gagal, `frappe.db.rollback()` dan berhenti. Kemudian:

```bash
bench --site NAMA_SITE_PRODUCTION clear-cache
```

Refresh halaman print website dan pilih TARGET. Karena format aktif yang sama diperbarui, pengguna yang memakai format itu mendapat rincian dinamis pada semua invoice. Format lain tidak berubah. Jika TARGET belum default, atur default Sales Invoice melalui Customize Form hanya jika memang disepakati. Tidak perlu migrate, build, restart, atau perubahan akuntansi.

## 5. Rollback hanya Print Format

Jika hasil tidak sesuai, pulihkan format_data dari backup sebelum deploy. Backup harus milik site dan format yang sama. Jangan restore seluruh database untuk rollback cetakan.

```python
import frappe, json
from pathlib import Path
TARGET = 'PPN TEST'
BACKUP = '/PATH/ABSOLUT/DARI/LANGKAH/2/before.json'
before = json.loads(Path(BACKUP).read_text(encoding='utf8'))
assert before['name'] == TARGET and before['doc_type'] == 'Sales Invoice'
active = frappe.get_doc('Print Format', TARGET)
active.format_data = before['format_data']
active.save()
frappe.db.commit()
frappe.clear_cache(doctype='Print Format')
```

Lalu clear-cache dan refresh seperti langkah 4. Jika default pernah diubah, kembalikan default sebelumnya. Format review dapat dinonaktifkan setelah selesai, tanpa menghapus invoice.

## Status paket

Template ini sudah diuji di blitz.local: 24 pengujian template lulus, PDF dua contoh diperiksa, dan hash data transaksi tetap sama. Tiga invoice lain juga berhasil dirender. Production belum disentuh. Tidak ada pengujian production yang diklaim oleh paket ini.
