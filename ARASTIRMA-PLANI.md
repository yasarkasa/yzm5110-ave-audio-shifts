# YZM5110 araştırma projesi

Bireysel çalışma, ders notunun %30'u. Teslim 18 Kasım 2026, 7. hafta, sunum oturumundan önce. Yönergede saat ve sunum süresi belirtilmemiş. [Ödev yönergesi](kaynaklar/YZM5110_Research_Project.pdf)

## Sırayla çalışma planı

Konu sınıf tablosunda kayıtlı. [Beş makalenin karşılaştırması ve literatür sentezi](MAKALE-KARSILASTIRMA.md) hazır. Aşağıdaki tarihler çalışma hedefleri. Teslim dosyalarını 17 Kasım'da hazır edip 18 Kasım'daki sunum oturumundan önce yüklemeyi hedefliyoruz.

| Sıra | Hedef | İş | Aşama çıktısı |
| --- | --- | --- | --- |
| 1 | 10 Kasım | **Veri ve ortamı doğrula. Tamamlandı.** AVE'nin hazır özellikleri, etiketleri ve özgün bölümleri kontrol edildi. | Üç doğrulama klibinde ses, görüntü ve etiket eşleşmesi ile A+V-att çıktısı doğrulandı. |
| 2 | 11 Kasım | **Okumayı ve hipotezi netleştir. Tamamlandı.** Beş makalenin matrisi gözden geçirildi ve literatür sentezi yazıldı. | Birincil karşılaştırma ve karar ölçütü deneyden önce kayda alındı. |
| 3 | 12–13 Kasım | **A+V-att referansını çalıştır. Tamamlandı.** Yazarların yayımladığı ağırlıklarla özgün test bölümünün tamamını kaydırmasız değerlendir. | 402 klipte %72,7363 doğruluk. Makalenin hassasiyetinde %72,7. |
| 4 | 14 Kasım | **Zaman kayması deneyini kur. Tamamlandı.** Görüntü ve etiketler sabitken ses 0, ±1 ve ±2 saniye kaydırıldı. Her kayma, aynı sınır maskesini alan kaydırmasız kontrolle karşılaştırıldı. | 402 doğrulama klibinde beş koşul çalıştı. [Kaydırma betiği](scripts/ave_shift.py) ve [sonuç kaydı](results/ave_shift_validation.json) hazır. |
| 5 | 15 Kasım | **Bir iyileştirme ve kontrol seç. Tamamlandı.** Yerel ses ortalaması ve norm eşlemeli ablasyon doğrulama bölümünde ölçüldü. | ±2 saniyede referansa göre +0,60 yüzde puanı. Tekli CPU gecikmesi kaydedildi ve [deney ayarları](configs/ave_improvement.json) sabitlendi. |
| 6 | 16 Kasım | **Nihai testi çalıştır ve sonuçları yorumla. Tamamlandı.** Üç yöntem 402 özgün test klibinde beş kayma ve eş maskeli kontrollerle değerlendirildi. | [Test raporu](results/ave_test_report.md), [doğruluk grafiği](results/ave_test_accuracy.png), güven aralıkları, gecikme ve hata analizi. |
| 7 | 17 Kasım | **Yerel teslim adayı hazırlandı.** 13 sayfalık rapor, 15 slaytlık sunum, kurulum/veri hazırlama ve sonuç üretim komutları eklendi. | Rapor ve sunum `output/` altında. Herkese açık GitHub oluşturma, açık paylaşım onayı bekliyor. |
| 8 | 18 Kasım, sunumdan önce | **Teslim et.** Araştırma projesi sayfasına depo bağlantısını ve PDF'yi ekle. Kaydın tamamlandığını doğrula. | Ders sayfasında tamamlanmış teslim. |

Özgün veri veya kodla ilgili bir engel çıkarsa önce yazarların sunduğu hazır özellikler ve çalıştırma yolları kontrol edilir. Daha küçük bir yeniden üretim gerekirse hangi veri, model veya bütçenin değiştiği kaydedilir. Kayma etkisi ve iyileştirme aynı uyarlanmış referans üzerinde ölçülür.

### Adım 1 · Çalıştırma kaydı

10 Kasım 2026'da macOS arm64 üzerinde Python 3.12.14, PyTorch 2.15.0, h5py 3.16.0 ve NumPy 2.5.4 ile CPU doğrulaması yapıldı. Özgün kod revizyonu `93f843fed72fb17394df76330df958b0c2dbde76`. Yazarların `AV_att.pt` dosyasındaki parametreler, dosya özeti ve izinli nesne listesi kontrol edilerek yüklendi. CUDA'ya bağlı sıfır LSTM durumları girdiyle aynı cihazda oluşturuldu. Xavier başlatıcısının güncel adı kullanıldı ve tüm model parametreleri yazarların ağırlıklarıyla yüklendi. [Yazarların kodu ve özellik bağlantıları](https://github.com/YapengTian/AVE-ECCV18/tree/93f843fed72fb17394df76330df958b0c2dbde76)

Görüntü özellikleri, yazarların HDF5 dosyasından yalnızca gerekli HTTP aralıkları okunarak alındı. İlk aralık okuyucusunun döndürdüğü ses dizileri tamamen sıfır olduğu için ilk koşu elendi. Google Drive kota hatası verince son koşuda herkese açık ses aynası kullanıldı. Ayna dosyası beklenen byte boyutunda ve `(4143, 10, 128)` düzeninde. Özgün dosyayla tam dosya özeti karşılaştırması bekliyor. Kullanılan ayna ses dosyasının SHA-256 değeri `6765e445a5a66853282964576222c7aaf895b563100b2d99f29ecfd413c7d8fc`. [Ses özelliği aynası](https://huggingface.co/datasets/LECOO/AVE/tree/main)

Ses, görüntü ve etiketler aynı sıfır tabanlı veri satırından alındı. Her üç örnekte her iki kipin özellikleri sonlu ve sıfırdan farklı değerler içeriyor. Model her klibin 10 bölümü için 29 sınıf olasılığı üretti. Eşleşme hazır özelliklerin klip satırı ve bir saniyelik zaman bölümü düzeyinde kontrol edildi.

| AVE satırı | Klip kimliği | Özgün olay aralığı | Doğru tahmin edilen bölüm |
| --- | --- | --- | --- |
| 56 | `SiA-LmxRebg` | Çan sesi, 5–10 sn | 9/10 |
| 273 | `-C8lz1HKEuo` | Erkek konuşması, 1–6 sn | 5/10 |
| 465 | `Gor0hFplM-U` | Havlama, 5–10 sn | 8/10 |

4.143 açıklama satırının sınıf ve zaman etiketleri `labels.h5` ile eşleşti. Özgün bölümler satır bazında ayrık ve büyüklükleri 3.339 eğitim, 402 doğrulama ve 402 test. Kaynak video kimliği bazında 18 video birden fazla bölümde yer alıyor. Bu fark, özgün skorun yeniden üretimi ve genelleme yorumunda ayrı tutulmalı. [Özgün AVE bölümleri](https://github.com/YapengTian/AVE-ECCV18/tree/93f843fed72fb17394df76330df958b0c2dbde76/data)

Mevcut yerel örnekle ağ bağlantısı gerektirmeden tekrar doğrulamak için proje kökünde çalıştır.

```bash
.ave-local/venv/bin/python scripts/ave_smoke.py
```

Klip bazındaki hedef ve tahmin dizileri `.ave-local/smoke_result.json` dosyasında. İndirilen özellikler, ağırlıklar ve çalışma ortamı `.ave-local/` altında Git dışında tutuluyor. Üç klibin sonuçları çalışabilirlik kontrolüne ait.

### Adım 3 · Kaydırmasız A+V-att referansı

10 Kasım 2026'da yazarların `AV_att.pt` ağırlıklarıyla özgün `test_order.h5` dosyasındaki 402 klip değerlendirildi. Her klibin 10 bölümünde en yüksek model olasılığına sahip sınıf, `labels.h5` dosyasındaki özgün sınıfla karşılaştırıldı. Ses kayması 0 saniye ve sınır maskesi kapalı. [Makale, Tablo 1 ve §6.2](https://arxiv.org/pdf/1803.08842#page=12) · [Özgün değerlendirme betiği](https://github.com/YapengTian/AVE-ECCV18/blob/93f843fed72fb17394df76330df958b0c2dbde76/supervised_main.py)

| Ölçüm | Doğru bölüm | Bölüm doğruluğu |
| --- | ---: | ---: |
| Bizim koşumuz | 2.924 / 4.020 | **%72,7363** |
| Makale, Tablo 1 | — | **%72,7** |

Makalenin yuvarlanmış değerine göre fark **+0,0363 yüzde puanı**. Her iki sonuç bir ondalık basamakta **%72,7**. Bu ölçüm, yayımlanmış ağırlıkların özgün test bölümü üzerindeki yeniden üretimidir.

402 görüntü satırı yazarların HDF5 dosyasından doğrulanmış HTTP bayt aralıklarıyla alındı. Resmî ses bağlantısı kota hatası verdiği için Adım 1'deki ses aynası kullanıldı. Ayna dosyasının SHA-256 değeri kayda alındı. Özgün ses dosyasıyla tam dosya özeti karşılaştırması bekliyor. Çıkarım, Adım 1'deki CPU uyarlaması ve 16 kliplik gruplarla çalıştırıldı. [Yazarların özellik bağlantıları](https://github.com/YapengTian/AVE-ECCV18#ave-dataset--features) · [Ses dosyası aynası](https://huggingface.co/datasets/LECOO/AVE/tree/main)

Ortam sürümleri, veri ve checkpoint özetleri [sonuç JSON'unda](results/ave_reference.json). Her bölümün hedef ve tahmin sınıfı [tahmin CSV'sinde](results/ave_reference_predictions.csv). Proje kökünde aşağıdaki komutlar çalıştırılabilir. İlk komut eksik görüntü satırlarını tamamlar.

```bash
.ave-local/venv/bin/python -B scripts/ave_reference.py --fetch
.ave-local/venv/bin/python -B scripts/ave_reference.py
```

### Adım 4 · Ses kayması protokolünün doğrulanması

10 Kasım 2026'da A+V-att, özgün `val_order.h5` dosyasındaki 402 klibin tamamında çalıştırıldı. Adım 3'teki ağırlıklar ve ses aynası kullanıldı. Görüntü özellikleri yazarların HDF5 dosyasından alındı; görüntü, etiket ve model ağırlıkları koşullar arasında sabit kaldı.

Pozitif ofset sesi geciktirir; örneğin `+2` koşulunda görüntü bölümü 4, ses bölümü 2 ile eşleşir. Kaydırmayla boşalan ses bölümleri çıkarımdan önce sıfırlandı. Her kontrolde ses yerinde bırakıldı ve tam aynı sınır bölümleri sıfırlandı. Model 10 bölümün tamamını gördü; doğruluk her koşulda ortak **2–7** indislerinde (sıfır tabanlı) hesaplandı. Bu, koşul başına **2.412** bölüm demek.

| Ses kayması | İki koşulda sıfırlanan indisler | Kaydırılmış doğruluk | Kaydırmasız kontrol | Kontrol − kaydırılmış (yüzde puanı) |
| ---: | --- | ---: | ---: | ---: |
| −2 sn | 8, 9 | %71,27 | %72,97 | +1,70 |
| −1 sn | 9 | %72,80 | %72,76 | −0,04 |
| 0 sn | — | %73,42 | %73,42 | 0,00 |
| +1 sn | 0 | %73,22 | %73,67 | +0,46 |
| +2 sn | 0, 1 | %71,85 | %73,34 | +1,49 |

Numaralı bir ses dizisinde beş ofsetin yönü, sınır maskelerinin eşleşmesi ve klip uçlarından ses taşınmaması kontrol edildi. `0` koşulunda ses girdileri ve 4.020 bölüm tahmini birebir eşleşti. Kaydedilen tahminler özgün doğrulama sırası ve etiketleriyle karşılaştırıldı; puanlanan 2.412 bölümde doğruluklar yeniden hesaplanarak doğrulandı. Yön ortalamaları doğrulamada `D₁ = +0,21` ve `D₂ = +1,60` yüzde puanı. Bunlar protokol kontrolünde gözlenen değerler; hipotezin nihai değerlendirmesi Adım 6'da özgün test bölümünde yapılacak.

[Koşul ve kaynak kaydı](results/ave_shift_validation.json) · [Bölüm bazında tahminler](results/ave_shift_validation_predictions.csv). CSV, her klibin 10 bölümünü içerir; `scored` sütunu doğruluğa giren bölümleri işaretler. Proje kökünden tekrar çalıştırmak için:

```bash
.ave-local/venv/bin/python -B scripts/ave_shift.py --fetch
.ave-local/venv/bin/python -B scripts/ave_shift.py
```

### Adım 5 · Yerel ses ortalaması ve deney ayarları

Doğrulama bölümünde iki saniyelik kayma, eş maskeli kontrole göre `−2` yönünde 41 ve `+2` yönünde 36 net doğru bölüm kaybettirdi. Hedef saniye ile kaydırılmış sesin kaynak saniyesi arasında olay varlığı değiştiğinde bu kayıplar sırasıyla 33 ve 44 oldu. Bu ölçüm AVE'nin özgün olay aralıklarını kullanır. Örneğin 56. satırda çan 5. saniyede başlıyor. `−2` kaymasında model arka plan olan 4. saniyeyi çan, `+2` kaymasında çan olan 5. saniyeyi arka plan olarak etiketledi. İki eş maskeli kontrol de ilgili saniyeyi doğru sınıflandırdı.

**Müdahale.** Her saniyenin 128 boyutlu ses vektörü %50 ağırlıkla korunur. Kalan %50, iki saniye önceye ve iki saniye sonraya kadar olan geçerli komşu vektörlerin eşit ağırlıklı ortalamasından gelir. Yapay sınır boşlukları ortalamaya katılmaz ve sıfır kalır. Geçerli komşu yoksa merkez korunur. A+V-att ağırlıkları, görüntü ve hedefler sabittir. Gerekçe, kaymış olay başlangıcı veya bitişi yakınındaki komşulardan uygun ses bilgisinin hedef saniyeye kısmen ulaşabilmesidir. Aynı işlem, doğru hizalanmış örneklerde geçişleri bulanıklaştırabilir.

**Ablasyon.** Aynı komşu harmanından saniye başına L2 normu alınır ve merkezdeki özgün ses vektörü bu norma ölçeklenir. Böylece harmanın büyüklük değişimi kontrol edilir, özellik yönü merkezden gelir. Merkez vektörü sıfırsa iki yöntemde de sıfır kalır. Referans, harmanlama yapmadan aynı girdiyle çalışır. Üç yöntem de kaydırılmış ve eş maskeli kaydırmasız koşullarda, aynı 2–7 indislerinde değerlendirilir.

**Ölçüler.** Birincil iyileştirme karşılaştırması `−2` ve `+2` kaydırılmış doğruluklarında, yerel ortalama eksi referans farkının iki yön ortalamasıdır. Aynı fark norm eşlemeli ablasyona karşı da hesaplanacak. Ayrıca 0 saniyedeki doğruluk değişimi ve eş maskeli `D₂` ölçüsü her yöntem için raporlanacak. Nihai testte farkların %95 güven aralığı, eşlenmiş kaynak video kimlikleriyle 10.000 bootstrap tekrarından hesaplanacak (seed 2026). Kaynak ölçüsü 4 CPU iş parçacığıyla, klip başına tekli çıkarım gecikmesidir. Her yöntemde 5 ısınma çağrısından sonra her ofset için özgün sıradaki ilk 32 klip kullanılır. Zamanlama bellekteki ses ve görüntüden başlar, ön işleme, model çalıştırma ve sınıf seçimini kapsar. Medyan ve 95. yüzdelik milisaniye olarak raporlanır.

Yarıçap, ağırlık, değerlendirme indisleri ve zamanlama ayarları iyileştirme koşusu öncesinde [deney yapılandırmasına](configs/ave_improvement.json) kaydedildi. Doğrulama sonuçlarıyla birlikte yapılandırmanın SHA-256 değeri de kayda alındı. Adım 6'da aynı yapılandırma ve uygulama dosyası kullanıldı.

| Yöntem | ±2 sn kaydırılmış doğruluk ortalaması | 0 sn doğruluk | Eş maskeli `D₂` (yüzde puanı) | CPU medyan / p95 (ms/klip) |
| --- | ---: | ---: | ---: | ---: |
| A+V-att referansı | %71,56 | %73,42 | 1,60 | 0,692 / 0,736 |
| Yerel ses ortalaması | %72,16 | %73,34 | 1,08 | 0,711 / 0,763 |
| Norm eşlemeli ablasyon | %71,27 | %73,26 | 1,76 | 0,714 / 0,778 |

Yerel ortalama ±2 saniyede referansın **0,60** ve norm eşlemeli ablasyonun **0,89** yüzde puanı üstündeydi. 0 saniyede referansa göre **0,08** yüzde puanı kaybetti. Örneğin `+2` koşulunda 139. satırın 3. saniyesindeki çan sesi hatası düzeldi. Aynı koşulda 239. satırın 5. saniyesindeki arka plan, yerel ortalamayla erkek konuşması olarak etiketlendi. 402 doğrulama klibinde referans tahminleri Adım 4 ile birebir eşleşti. Maskeler ve ablasyonun vektör normları tüm doğrulama girdilerinde kontrol edildi. Gecikme değerleri macOS arm64 CPU üzerinde, yöntem başına 160 çağrıdan hesaplandı.

[Sonuç ve yapılandırma özeti](results/ave_improvement_validation.json) · [Bölüm bazında tahminler](results/ave_improvement_validation_predictions.csv). Önbellekteki doğrulama verisiyle yeniden çalıştırma komutu aşağıdadır.

```bash
.ave-local/venv/bin/python -B scripts/ave_improvement.py
```

### Adım 6 · Özgün test ve hata analizi

10 Kasım 2026'da sabitlenen ayarlarla özgün AVE test bölümündeki 402 klip, koşul başına 2.412 bölüm üzerinden değerlendirildi. Referansta iki saniyelik kayma, eş maskeli kontrole göre **1,89 yüzde puanı** düşüş yarattı (%95 GA [1,06, 2,74]). `D₂ − D₁` farkı **1,49** [0,68, 2,34] yüzde puanıydı. Kaydırmasız referansın 4.020 tahmini Adım 3 ile birebir eşleşti.

Yerel ses ortalaması ±2 saniyede referansı **0,83** [0,29, 1,35] ve norm eşlemeli ablasyonu **0,56** [0,02, 1,10] yüzde puanı geçti. `D₂` düşüşündeki azalma **0,58** [−0,04, 1,18] yüzde puanıydı ve aralık sıfırı içerdi. Yerel ortalamanın medyan CPU gecikmesi **0,717 ms/klip**, referansınki **0,696 ms/klip**. Eğitim veya doğrulamayla ortak kaynaklı sekiz klip çıkarıldığında referansa göre ±2 saniye kazanımı **0,85** [0,32, 1,40] yüzde puanı oldu.

Olay varlığı hedef ve ses kaynağı saniyeleri arasında değişen bölümler, ±2 saniyedeki 91 net referans kaybının 76'sını oluşturdu. Yerel ortalama iki yönde 86 hatayı düzeltti ve 46 yeni hataya yol açtı. [Doğruluk tabloları, yöntem ve örnekler](results/ave_test_report.md) · [Grafik](results/ave_test_accuracy.svg) · [Makine okunur sonuçlar](results/ave_test.json) · [Bölüm tahminleri](results/ave_test_predictions.csv)

### Adım 7 · Teslim paketinin hazırlanması

11 Kasım 2026'da rapor yönergedeki sekiz bölüm sırasıyla hazırlandı. Beş makalenin yedi alanlı matrisi iki yatay ek sayfasına yerleştirildi. Türkçe rapor 13 sayfa ve adı `Kahraman_YZM5110_Research.pdf`. Düzenlenebilir sunum 15 slayt, kaynaklar ve konuşmacı notları içeriyor.

`README.md`, sabit bağımlılıklar, `prepare_ave.py`, küçük çalıştırma kontrolü ve sonuç JSON'undan tablo üretimi eklendi. Mevcut önbellekle veri hazırlama ve üç kliplik model kontrolü çalıştırıldı. Temiz bir makinede sıfırdan bütün indirme ve kurulum henüz yeniden denenmedi. Veri, ortam, büyük checkpoint'ler ve ders PDF'leri Git dışında tutuluyor. Codex'in somut katkıları raporda, son slaytta ve `AI_USAGE.md` içinde açıklanıyor.

Planlanan depo `https://github.com/yasarkasa/yzm5110-ave-audio-shifts`. GitHub hesabına erişim doğrulandı. Herkese açık oluşturma otomatik onay incelemesinde, açık paylaşım için ayrı kullanıcı yetkisi gerektiği gerekçesiyle durduruldu. Yerel teslim adayı `submission-v1-rc1` etiketiyle korunacak. Son yayımlama ve nihai `submission-v1` etiketi açık paylaşım onayından sonra tamamlanacak.

Sunum süresi yönergede belirtilmedi. Konuşmacı notları teknik savunmayı destekleyecek biçimde yazıldı. Öğrencinin kaynakları okuyup uygulamayı anladığını doğrulaması ve sözlü prova yapması teslim öncesinde tamamlanmalıdır.

## Gereksinimler

| Aşama | Teslimde gösterilecek kanıt |
| --- | --- |
| Literatür (§2, s. 1) | Tek bir araştırma sorusuna bağlı **en az beş makale**. Temel, yeni ve rakip yaklaşımları kapsayan bir arama ve seçim yöntemi. Makale başına bir satırdan oluşan karşılaştırma matrisi. Bulguların nerede uyuştuğunu ve hangi varsayımlarda ayrıştığını açıklayan sentez. Makale bulgusu, öğrenci yorumu ve öğrenci ölçümü ayrı ayrı tanımlanır. |
| Yeniden üretim (§3, s. 1–2) | **En az iki kip** kullanan bir makaleden sınanabilir bir kavram veya sonuç. Deney öncesinde beklenen sonuç ve iddiayı sorgulatacak gözlem. Kendi uygulaman veya kaynak gösterdiğin, anladığın bir uygulamanın uyarlaması. Yayın skoru ve ölçtüğün referans skor ayrı raporlanır. Daha küçük veri, model veya hesaplama bütçesi kullanılabilir. Sapmalar, açıklanabilen farklar ve hâlâ geçerli karşılaştırmalar kaydedilir. |
| Hedefli iyileştirme (§4, s. 2) | Referans deneyini anladıktan sonra **tek bir zayıflık** seç ve sonuçları görmeden önce müdahaleyi gerekçelendir. Eş koşullarda ölçtüğün referansla karşılaştır. Etkiyi ayıran en az bir kontrol veya ablasyon ekle. Görev kalitesiyle birlikte gecikme, tepe bellek veya eğitim süresi gibi uygun bir kaynak ölçüsü raporla. Olumlu ve olumsuz örnekleri, belirsizliği ve başarısız denemeleri göster. Yöntem ayarını doğrulama verisinde yap ve nihai test bölümünü değerlendirme için ayır. |
| Rapor ve depo (§5, s. 2–3) | `<LastName>_YZM5110_Research.pdf`, ilk sayfada **herkese açık depo URL'si**. Kurulum, bağımlılık sürümleri, veri sürümü ve lisansa uygun erişim, checkpoint, kaynak revizyonu, ön işleme, seed, yapılandırma, tam komutlar, kaydedilmiş çıktılar ve tablo/şekil üretim betikleri. Teslim sürümünü commit veya tag ile sabitle. Tam koşu pahalıysa küçük bir çalıştırma testi ve tam koşunun kaynak gereksinimleri. |
| Sunum (§6, s. 3 ve Hafta 1, s. 4) | Literatür sentezini, mekanizmayı, varsayımları, deney tasarımını ve sonuçları savunabilmek. Hafta 1 ayrıca Hugging Face Spaces demosu veya çalıştırma yönergeleri içeren bir GitHub deposu istiyor. |

Raporun zorunlu sırası

1. Araştırma sorusu, kapsam, motivasyon ve katkılar
2. Literatür arama yöntemi ve eleştirel sentez
3. Seçilen yöntemin teknik açıklaması
4. Yeniden üretim hedefi, uygulama ve kaynaktan sapmalar
5. Önerilen iyileştirme ve gerekçesi
6. Deney tasarımı, veri kümeleri, bölümler, referanslar, ölçüler ve kaynaklar
7. Sonuçlar, kontroller, belirsizlik ve hata analizi
8. Sınırlılıklar, sonuç ve açık sorular

Değerlendirme altı boyutu birlikte ele alıyor. Bunlar literatürün derinliği ve sentezi, teknik anlayış, yeniden üretim, hedefli iyileştirme, deneysel titizlik ve yeniden üretilebilirlik ile iletişim.

## Slaytlarla eşleştirme

| Kaynak | Projede karşılığı |
| --- | --- |
| [Hafta 1, s. 4–7 ve 59–64](kaynaklar/MML%20-%20Week%201.pdf#page=4) | Proje ve yapay zekâ politikası. Modelin iki kipten nasıl yararlandığı iddiası için tek kipli referanslar ve kontrollü girdi değişimleri. |
| [Hafta 2, s. 33–46](kaynaklar/MML%20-%20Week%202.pdf#page=33) | Ses ve video temsilleri, örnekleme ve zaman çözünürlüğü. Hazır özelliklerin hangi zaman birimini temsil ettiğini açıklamak için. |
| [Hafta 3, s. 54–59](kaynaklar/MML%20-%20Week%203.pdf#page=54) | Aynı değerlendirme koşullarında referans, kontrol, ablasyon ve belirsizlik. Füzyon ve kip etkileşimi iddiası kurulacaksa bu iddiaya uygun ek kontroller. |
| [Hafta 4, s. 53–63](kaynaklar/MML%20-%20Week%204.pdf#page=53) | Zamansal dayanaklandırma. Özellikle s. 56'da bir akışın zamanını değiştirerek eşzamanlılığa duyarlılığı ölçme ve s. 57'de sabit ofset ile saat kaymasının ayrımı. |
| [Hafta 5, s. 21–24 ve 69–75](kaynaklar/MML%20-%20Week%205.pdf#page=21) | Veri bölümü, sızıntı, bağımsız test, kaynak ölçümü ve başkasının aynı deneyi çalıştırabilmesi için gereken kayıtlar. |

## Sınıf tablosuna kaydedilen konu

| Alan | Kayıt |
| --- | --- |
| Research Topic | Measuring Robustness to Audio–Video Desynchronization on AVE |
| Paper Title | Audio-Visual Event Localization in Unconstrained Videos |
| Paper URL | [Tian vd. (ECCV 2018)](https://arxiv.org/abs/1803.08842) |

9 Kasım'da sınıf tablosundaki 28 kayıt incelendi. CLIP tabanlı birkaç yakın çalışma bulundu. Seçilen AVE makalesi ve zamansal kayma konusu mevcut kayıtlarda yer almıyordu. Üç alan kaydedildi ve satır sınıf tablosunda doğrulandı. [Dersin araştırma projesi sayfası](https://lecture.studio/ekrcet/yzm5110-multimodal-learning/s/N0HZQCWas8ZS9Nh1)

**Yeniden üretim hedefi.** Tian vd. makalesinin Tablo 1'inde denetimli A+V-att modeli AVE'de %72,7 doğruluk bildiriyor. Model ses ve görüntü özelliklerini kullanarak bir olayın hangi video bölümlerinde gerçekleştiğini ve sınıfını tahmin ediyor. Aynı tabloda tek kipli A ve V referansları var. Yazarların deposu kod, veri bölümleri ve hazır özellik bağlantıları sağlıyor. Veri erişimi ve CPU uyarlaması Adım 1'de doğrulandı; özgün A+V-att test sonucu Adım 3'te yeniden üretildi. [Makale, Tablo 1](https://www.ecva.net/papers/eccv_2018/papers_ECCV/papers/Yapeng_Tian_Audio-Visual_Event_Localization_ECCV_2018_paper.pdf#page=12) · [Yazarların deposu](https://github.com/YapengTian/AVE-ECCV18)

İlk soru, aynı videonun ses akışı görüntüye göre kontrollü olarak kaydırıldığında olay konumlandırma doğruluğunun nasıl değiştiği. Özgün protokoldeki referans ölçüldükten sonra kaydırılmamış ve kaydırılmış örnekler karşılaştırılacak. Eş sınır maskesi, hizalama etkisini sınırdaki ses kaybından ayırır. Adım 5'te seçilen yerel ses ortalaması ve norm eşlemeli kontrol, bu protokolün içinde değerlendirilecek.

### Seçilen literatür

Tian vd. ana makale. Dört karşılaştırma makalesi **CMAN** (Xuan vd., 2020), **PSP** (Zhou vd., 2021), **CMBS** (Xia ve Zhao, 2022) ve **AVSGN** (Liu vd., 2025). Hepsi AVE'de bölüm düzeyinde sonuç bildiriyor. [Beş makalenin karşılaştırma matrisi](MAKALE-KARSILASTIRMA.md) seçim gerekçesini, kaynakları, yayın skorlarını ve deney protokollerinin farklarını içeriyor.

### Ses kayması deneyinin hipotezi

**Birincil hipotez.** Tian vd.'nin yayımladığı A+V-att ağırlıkları sabitken, ses özelliklerini görüntüye göre **iki saniye öne veya arkaya** kaydırmak, iki yönün ortalamasında, aynı sınır maskesini alan kaydırmasız kontrole göre bölüm doğruluğunu düşürür. Beklenti, sesin aynı saniyedeki görsel dikkati yönlendirmesine dayanır. Modelin iki yönlü LSTM'leri komşu saniyelerden bağlam aldığı için düşüşün büyüklüğü deneyle belirlenecek. [A+V-att uygulaması](https://github.com/YapengTian/AVE-ECCV18/blob/93f843fed72fb17394df76330df958b0c2dbde76/models.py)

**Koşullar.** Bir saniyelik hazır ses özellikleri üzerinde `−2, −1, 0, +1, +2` saniyeyi kullanacağız. Pozitif kayma sesi geciktirir. Örneğin `+2` koşulunda görüntünün 4–5 saniye aralığına özgün sesin 2–3 saniye aralığı girer. Ses klibin başından sonuna veya sonundan başına taşınmaz. Boş kalan ses bölümlerine sıfır vektörü konur. Her kaydırmanın kontrolünde, ses yerinde kalır ve tam aynı sınır bölümleri sıfırlanır. Görüntüler, özgün etiketler ve model ağırlıkları tüm koşullarda sabittir. İki yönü ve büyüklüğü aynı örneklerle karşılaştırmak için doğruluk, sıfır tabanlı **2–7** indislerindeki ortak altı bölümde hesaplanır. Maskesiz `0` koşulu, sınır maskesinin tek başına etkisini de görmemizi sağlar.

**Birincil ölçü.** `D₂`, `−2` ve `+2` için yüzde puan cinsinden `kontrol doğruluğu − kaydırılmış doğruluk` farklarının ortalamasıdır. Beklenti `D₂ > 0`. %95 güven aralığını kaynak video kimliklerini 10.000 kez yeniden örnekleyerek hesaplayacağız (seed 2026). Bir kaynak videonun bütün klip satırları ve koşulları birlikte örneklenir. Aralık bütünüyle sıfırın üstündeyse hipotez desteklenir. Sıfırı içerirse sonuç belirsizdir. Aralık bütünüyle sıfırın altındaysa etki beklenen yönün tersindedir.

**İkincil beklenti.** İki saniyedeki düşüşün bir saniyedekinden büyük olmasını bekliyoruz (`D₂ > D₁`). `D₁` aynı yöntemle `−1` ve `+1` üzerinden hesaplanır. Öne ve arkaya kaydırma skorları ayrı gösterilir. Bu iki yön arasında önceden bir sıralama öngörülmüyor.

Kaydırma ve maskeleme kodu Adım 4'te doğrulama bölümünde kontrol edildi. Sabitlenen protokol Adım 6'da özgün test bölümüne uygulandı. Eğitim veya doğrulamada geçen kaynak kimliklerini çıkaran duyarlılık analizi test raporunda yer alıyor. Makaledeki %72,7 yeniden üretim karşılaştırması, Adım 3'te özgün test bölümünün maskesiz ve kaydırılmamış **10 bölümünün tamamında** hesaplandı. [Adım 1 veri kaydı](#adım-1--çalıştırma-kaydı) · [Test raporu](results/ave_test_report.md)

## Yapay zekâ denetimi ve beyan kaydı

Ödev PDF'sinin üç görünür sayfası ile metin katmanı karşılaştırıldı. Beyaz, sayfa dışına taşınmış veya görünmez çizim kipindeki metin, gizli katman, yorum, gömülü dosya veya JavaScript saptanmadı. Ödevin §7'si beyan edilen arama, kodlama ve düzenleme desteğine izin veriyor. Kaynakları okuma, uygulamayı anlama, deneyleri tasarlayıp çalıştırma, atıfları ve iddiaları kontrol etme ve sonuçları savunma öğrenciye ait. Sınıf arkadaşlarıyla genel tartışma ve geri bildirim serbest. Projeye özgü kod, çıktılar, analiz, rapor ve slaytlar öğrenciler arasında paylaşılmaz. [Ödev yönergesi, s. 3](kaynaklar/YZM5110_Research_Project.pdf#page=3)

- **9 Kasım 2026 · Codex.** Yönergedeki koşulları çıkardı, ders slaytlarıyla eşleştirdi, PDF'yi gizli içerik açısından inceledi, kaynak aramasını başlattı ve bir yeniden üretim adayı için yayın sonucu ile başlangıç varlıklarını doğruladı.

- **9 Kasım 2026 · Codex.** Sınıf tablosunu çakışma açısından inceledi, AVE konusunu ve makale bağlantısını kaydetti, yeni konu için kaynakları ve slayt eşleştirmesini güncelledi.
- **9 Kasım 2026 · Codex.** Dört karşılaştırma makalesini seçti, birincil kaynaklardan yöntemleri ve deney tablolarını kontrol etti, literatür matrisinin ilk taslağını hazırladı.
- **10 Kasım 2026 · Codex.** Çalışma sırasını, hedef tarihleri ve her aşamanın beklenen çıktısını planladı.
- **10 Kasım 2026 · Codex.** Yazarların veri ve model kaynaklarını kontrol etti, yerel doğrulama ortamını kurdu ve üç AVE klibiyle çalıştırma testini uygulayıp belgeledi.
- **10 Kasım 2026 · Codex.** Beş makalenin matrisini kaynaklarla gözden geçirdi, literatür sentezini yazdı ve kayma hipoteziyle karar ölçütünü belgeledi.
- **10 Kasım 2026 · Codex.** Özgün AVE test görüntülerini aldı, kaydırmasız A+V-att değerlendirme betiğini hazırlayıp çalıştırdı ve sonucu makalenin Tablo 1'iyle karşılaştırarak kaydetti.
- **10 Kasım 2026 · Codex.** Ses kayması ve eş maskeli kontrol betiğini hazırladı, beş ofseti özgün doğrulama bölümünde çalıştırdı ve kaydedilen tahminlerden doğrulukları yeniden hesaplayarak kontrol etti.
- **10 Kasım 2026 · Codex.** Doğrulama hatalarını olay aralıklarına göre inceledi. Yerel ses ortalamasını, norm eşlemeli ablasyonu ve gecikme ölçümünü uyguladı. Deney ayarlarını kaydetti ve doğrulama sonuçlarını kontrol etti.
- **10 Kasım 2026 · Codex.** Sabit ayarlarla özgün test koşusunu, kaynak video düzeyinde bootstrap ve örtüşme analizini uyguladı. Tahminlerden doğrulukları yeniden hesapladı, grafiği üretti ve düzelen veya yeni oluşan hataları belgeledi.
- **11 Kasım 2026 · Codex.** Raporu, düzenlenebilir sunumu, kurulum/veri erişimi ve yeniden çalıştırma belgelerini hazırladı. Beyan edilen araç ve katkıları AI_USAGE.md dosyasına ekledi. Herkese açık GitHub oluşturma için otomatik onay engelini kaydetti.
