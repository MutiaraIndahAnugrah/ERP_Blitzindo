# Cetak invoice dinamis

Template final berada pada `invoice_print/items.html`. Format Builder membaca ulang Sales Invoice asli, sehingga penggabungan item oleh before_print tidak menghilangkan tautan sumber.

## Hubungan sumber

1. Sales Invoice Item.detail_order -> Detail Order.details.
2. Jika detail_order kosong: Sales Order Item yang ditunjuk so_detail hanya dipakai bila parent cocok dengan sales_order pada item invoice.
3. Identitas menggunakan nama, nama asing, paspor dan durasi rincian sumber; Tenaga Kerja yang boleh dibaca menjadi fallback identitas.
4. Visa hanya dari Result Document dengan TKA dan WO sumber yang cocok, bukan visa terbaru dari sumber lain.

Item digabung untuk tampilan jika item_code, rate, UOM dan kumpulan durasinya sama. Tidak ada deduplikasi atau pemilihan orang berdasarkan kemiripan nama, qty, atau harga.

## Harga dan total

Kolom `Harga / <UOM>` membaca rate item invoice. `Total tagihan` membaca amount item invoice. Jika qty tagihan 13 sementara sumber berisi 32 rincian, semua 32 rincian sumber ditampilkan dengan tarif unit invoice; jumlah orang sumber bukan pengali total tagihan. Template tidak menentukan 13 orang mana yang ditagih.

Kolom paspor, visa, durasi dan harga mengikuti data yang tersedia. Item tanpa tautan tetap tercetak dengan pesan bahwa rincian belum tertaut. Style memakai kelas tabel existing Frappe. Tidak ada tabel lampiran terpisah, tombol baru, atau validasi transaksi tambahan.

## Batasan

Hasil mengikuti data ERP saat dicetak, sehingga perubahan master dapat mengubah cetakan ulang. Tidak membuat snapshot historis atau menambahkan kurs, fee USD, PO, dan alokasi TKA dengan tebakan. Pengguna memerlukan izin baca sumber yang relevan. Format lain tidak ikut berubah hanya karena template ini dipasang pada satu Print Format.

Teruji lokal: 24 tes template, HTML/PDF dua invoice contoh, dan rendering tiga invoice tambahan. Hash transaksi sebelum/sesudah pemasangan lokal sama. Belum ada klaim pengujian atau deployment production.
