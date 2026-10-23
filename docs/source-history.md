# Asal source dan batas perubahan

Repository dimulai dari snapshot aplikasi vendor kulkul_erp yang sudah ada pada bench lokal. Layout aplikasi dipertahankan agar kompatibel dengan Frappe. Identitas author dan lisensi vendor pada source dipertahankan.

Initial import tidak membawa riwayat Git lokal lama karena README historis berisi kredensial. README diganti dengan dokumentasi proyek yang tidak memuat rahasia. Konfigurasi nginx cadangan dan cache Python juga tidak diimpor. Kredensial lama yang pernah beredar perlu ditangani pemilik sistem secara terpisah; tidak dicantumkan ulang di sini.

Source aplikasi existing tidak direfaktor massal dalam penataan repo ini. Penambahan final berada di invoice_print, docs, scripts dan workflow pemeriksaan source. Tidak menyertakan eksperimen Blitz Invoice Attachment Row, historical attachment, hook/JS lampiran, atau skrip pembersihan lokal yang tidak menjadi bagian fitur cetak final.

Laporan audit rinci, PDF dan HTML preview, salinan database, serta data pekerja tetap di lingkungan lokal terbatas. Repo baru tidak mengganti folder app yang sedang dipakai bench dan tidak mengubah production.

Source vendor mencakup kode lama dan aset pihak ketiga; pemeriksaan syntax/metadata bukan audit keamanan menyeluruh atau validasi kompatibilitas upgrade. Perubahan aplikasi ke production tetap memerlukan review terpisah dari deployment template invoice.
