# Kaynaklar ve yeniden kullanılan bileşenler

## A+V-att uygulaması

Yapeng Tian ve diğerlerinin [AVE-ECCV18 deposu](https://github.com/YapengTian/AVE-ECCV18), `93f843fed72fb17394df76330df958b0c2dbde76` revizyonu kullanıldı. `AV_att.pt`, `models.py`, özgün bölüm listeleri ve etiketler çalışma sırasında bu depodan alınır. Dosyalar bu depoda yeniden dağıtılmaz. İncelenen revizyonda ayrı bir LICENSE dosyası bulunamadı. Kullanıcılar özgün kod, model ve verinin kullanım koşullarını kaynak sahiplerinden doğrulamalıdır.

`scripts/ave_smoke.py`, kaydedilmiş ağırlıkları hash ve izin verilen nesne sınıflarıyla kontrol ederek yükler. Özgün `models.py` bellekte çalıştırılırken dört CUDA sıfır durumu girdi cihazına taşınır ve eski Xavier başlatıcısı güncel adına çevrilir. Model parametreleri değişmez. Özgün eğitim betiğindeki kayıp ile makaledeki açıklama farkı, bu projenin checkpoint çıkarımını etkilemez. Yeniden eğitim yapılmadı.

Atıf, Tian, Y., Shi, J., Li, B., Duan, Z. ve Xu, C. (2018). *Audio-Visual Event Localization in Unconstrained Videos*. ECCV. [Makale](https://arxiv.org/abs/1803.08842).

## AVE özellikleri

Görüntü özellikleri özgün yazar bağlantısındaki HDF5 dosyasından HTTP bayt aralıklarıyla alınır. Ses için Google Drive kota sorunu nedeniyle [LECOO/AVE aynası](https://huggingface.co/datasets/LECOO/AVE/tree/main) kullanıldı. Aynanın tam dosya SHA-256 değeri `6765e445a5a66853282964576222c7aaf895b563100b2d99f29ecfd413c7d8fc`. Bu özet kullanılan sürümü tanımlar. Özgün ses dosyasıyla tam dosya özeti karşılaştırması henüz yapılamadı.

Veri, ham videolar, özellikler ve büyük checkpoint'ler Git'e eklenmez. Kaynak bağlantısının herkese açık olması yeniden dağıtım izni anlamına gelmez. Erişim ve kullanımda yazarların ve veri sağlayıcının koşulları geçerlidir. Bu projedeki hazırlama komutu, okuyucunun bu erişim koşullarını kendi kullanımı için değerlendirdiğini varsayar.

## Ders materyalleri

Ekrem Çetinkaya'nın YZM5110 ders slaytları ve ödev PDF'si yerel `kaynaklar/` klasöründe incelendi. Bu PDF'ler herkese açık depoya yüklenmez. Hafta 4'ün zamansal hizalama ve Hafta 5'in kaynak bazında bölme konuları deney tasarımına bağlandı. Öğrenciye özgü kod, çıktı, rapor ve sunum ders yönergesinin bireysel çalışma koşuluna tabidir.

## Yazılım

Çıkarımda Python 3.12.14, NumPy 2.5.4, h5py 3.16.0 ve PyTorch 2.15.0 kullanıldı. Grafikler Matplotlib 3.10.8, rapor ReportLab, düzenlenebilir sunum OpenAI Artifact Tool ile üretildi. Yazılımlar kendi lisanslarına tabidir. Yapay zekâ katkıları [AI_USAGE.md](AI_USAGE.md) dosyasında açıklanır.
