# Pengembangan lokal

Repository ini berisi satu custom app Frappe. Jangan memindahkan folder `kulkul_erp/` ke folder tambahan karena setup.py dan framework memakai layout package ini.

## Checkout

Utamakan filesystem Linux di WSL untuk development Frappe:

```bash
mkdir -p ~/projects
cd ~/projects
git clone https://github.com/MutiaraIndahAnugrah/ERP_Blitzindo.git
cd ERP_Blitzindo
python3 scripts/check_repository.py
```

ERP lokal yang sudah terpasang di `~/frappe-bench/apps/kulkul_erp` tidak otomatis berpindah karena repo baru ini. Jangan mengganti folder aplikasi bench yang sedang berjalan tanpa mencatat perubahan lokal dan prosedur pemulihannya. Untuk pekerjaan aplikasi selanjutnya gunakan checkout Git yang disepakati pada bench development, dengan nama app tetap kulkul_erp.

## Tes template pada bench lokal

Installer hanya dapat memakai `blitz.local`. Biarkan bench lokal berjalan. Skrip memeriksa mute_emails, scheduler nonaktif, webhook kosong, dan validator lampiran lama tidak aktif. Ini pengaturan site development, bukan instruksi mengubah pengaturan production.

Sesuaikan path checkout di perintah ini:

```bash
cd ~/frappe-bench/sites
../env/bin/python ~/projects/ERP_Blitzindo/invoice_print/install.py
```

Tanpa `--apply`: menjalankan 24 tes template memakai Jinja sandbox Frappe, mencoba format dalam transaksi, menghasilkan preview dua invoice contoh, memeriksa hash transaksi, lalu rollback perubahan Print Format. Invoice contoh harus ada pada database lokal; jika tidak tersedia, sesuaikan SAMPLES pada installer lokal dengan dokumen uji yang sah.

Setelah preview diperiksa:

```bash
../env/bin/python ~/projects/ERP_Blitzindo/invoice_print/install.py --apply
```

Hasil tersimpan di `invoice_print/previews/` (diabaikan Git), backup format di private/backups site. Preview mengandung data pribadi. Logo yang belum direstore hanya diganti placeholder pada PDF uji, bukan Letter Head. Installer tidak digunakan di production.

## Komit perubahan

Gunakan branch untuk perubahan berikutnya. Periksa `git diff --cached` dan jalankan pemeriksaan source sebelum commit. Jangan commit database, token, kredensial, PDF invoice, atau hasil audit berisi nama/paspor. File fixture dan JSON DocType harus berupa metadata, bukan salinan transaksi.
