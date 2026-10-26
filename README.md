# ERP Blitzindo Utama

Custom app `kulkul_erp` untuk ERPNext/Frappe dan template cetak Sales Invoice dengan rincian TKA dinamis.

## Struktur

```text
kulkul_erp/        Aplikasi Frappe existing, termasuk DocType, hook, aset, dan portal
invoice_print/    Template invoice final, installer lokal, dan tes template
scripts/          Pemeriksaan source repository
docs/             Panduan pengembangan dan deploy
.github/workflows/ Pemeriksaan source di GitHub Actions
setup.py          Metadata package Frappe (nama package tetap kulkul_erp)
```

Nama aplikasi dan direktori `kulkul_erp` dipertahankan agar import, hook, dan path DocType existing tetap kompatibel. Nama repository GitHub tidak mengganti nama aplikasi Frappe.

## Mulai dari sini

- [Pengembangan lokal](docs/development.md)
- [Perilaku cetak invoice](docs/invoice-print.md)
- [Deploy dan rollback cetakan](docs/deployment.md)
- [Asal source dan batas perubahan](docs/source-history.md)

Baseline yang digunakan: Frappe 13.22.2, ERPNext 13.24.0, Python 3.9. Upgrade framework bukan bagian dari perubahan cetak ini.

## Pemeriksaan

```bash
python3 scripts/check_repository.py
```

Untuk pengujian template yang memerlukan Frappe, gunakan langkah di [panduan lokal](docs/development.md). GitHub Actions hanya memeriksa source; tidak memiliki akses database ERP.

## Catatan deployment

Mengunggah source ke GitHub tidak melakukan deploy. Perubahan cetak hanya mengganti blok items pada Print Format Builder melalui prosedur review. Tidak memerlukan migrate/build atau perubahan invoice, jurnal, pajak, maupun pembayaran.

Database, site_config, kredensial, invoice PDF, backup, serta hasil audit berisi data pribadi tidak disimpan di repository ini. Pengaturan dan Print Format yang dibuat lewat UI Frappe berada di database; source repo bukan backup lengkap sebuah site.

Lisensi existing aplikasi: MIT, lihat [license.txt](license.txt). Aset pihak ketiga mempertahankan pemberitahuan lisensi masing-masing.

## Background asset compression

Implementasi opsional untuk upload baru: [flow dan hasil tes](docs/asset-compression.md), [konfigurasi/deploy/rollback](docs/asset-compression-deployment.md). Memakai antrean khusus, default OFF. Belum dideploy production.
