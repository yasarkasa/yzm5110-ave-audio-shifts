# Özgün AVE test sonuçları

Yerel ses ortalaması, ±2 saniyelik kaymada A+V-att referansına göre **0,83 yüzde puanı** doğruluk kazandırdı (%95 GA [0,29, 1,35]). Norm eşlemeli ablasyona göre kazanç **0,56 yüzde puanı** (%95 GA [0,02, 1,10]). Kaydırılmış koşuldaki doğruluk arttı. Eş maskeli kontrolle ölçülen kayma kaybındaki azalma için aralık sıfırı içeriyor.

10 Kasım 2026'da özgün AVE test bölümünün 402 klibi kullanıldı. Yayımlanmış A+V-att ağırlıkları ve Adım 5'teki ±2 saniyelik pencere ile %50 merkez ağırlığı kullanıldı. Her kaymanın eş maskeli kontrolünde ses yerinde kaldı ve kaydırılmış koşulla aynı ses indisleri sıfırlandı. Doğruluk, her koşulda aynı 2–7 indislerindeki 2.412 bölüm üzerinden hesaplandı. Görüntü özellikleri ve test sırası yazarlardan, ses özellikleri Adım 3 ve 5'teki LECOO/AVE aynasından geldi. Ses aynasının özgün dosyayla tam eşdeğerliği açık kaldı. [Sabit ayarlar](../configs/ave_improvement.json) · [Veri ve koşu kaydı](ave_test.json)

## Doğruluk ve güven aralıkları

Her hücre yüzde doğruluğu ve köşeli parantez içinde %95 güven aralığını gösterir. Kaydırılmamış 0 saniye satırı da diğer ofsetler gibi ortadaki altı saniyeyi kullanır.

| Kayma | A+V-att referansı | Yerel ses ortalaması | Norm eşlemeli ablasyon |
| ---: | ---: | ---: | ---: |
| −2 sn | 69,98 [66,50, 73,51] | **70,81** [67,33, 74,34] | 70,40 [66,87, 73,88] |
| −1 sn | 72,64 [69,15, 76,12] | **72,72** [69,24, 76,20] | 72,47 [68,99, 75,91] |
| 0 sn | **72,60** [69,07, 76,08] | 72,51 [68,95, 76,04] | 72,39 [68,91, 75,83] |
| +1 sn | 71,52 [67,99, 74,96] | **72,10** [68,53, 75,58] | 71,43 [67,91, 74,88] |
| +2 sn | 69,40 [65,88, 72,93] | **70,23** [66,67, 73,80] | 69,53 [66,00, 73,05] |

Eş maskeli kaydırmasız kontroller aşağıdaki değerleri verdi.

| Kaydırılmış eşi | A+V-att referansı | Yerel ses ortalaması | Norm eşlemeli ablasyon |
| ---: | ---: | ---: | ---: |
| −2 sn | 71,27 [67,74, 74,75] | 71,81 [68,33, 75,33] | 71,06 [67,54, 74,54] |
| −1 sn | 72,26 [68,78, 75,66] | 72,55 [68,99, 76,04] | 72,31 [68,82, 75,70] |
| 0 sn | 72,60 [69,07, 76,08] | 72,51 [68,95, 76,04] | 72,39 [68,91, 75,83] |
| +1 sn | 72,68 [69,15, 76,12] | 72,31 [68,78, 75,83] | 72,47 [68,99, 75,91] |
| +2 sn | 71,89 [68,37, 75,37] | 71,85 [68,33, 75,33] | 71,81 [68,33, 75,29] |

Adım 3'ün kaydırmasız ve maskesiz tam klip referansı **%72,7363** (2.924/4.020). Bu koşunun 0 saniye referansında 4.020 tahmin birebir eşleşti. Tian vd.'nin Tablo 1'de bildirdiği değer **%72,7**. Altı saniyelik tabloların paydası ise 2.412. [Yeniden üretim kaydı](ave_reference.json) · [Tian vd., Tablo 1](https://arxiv.org/pdf/1803.08842#page=12)

## Eşlenmiş karşılaştırmalar

Aralıklar, kaynak video kimliklerini bütün koşullar için birlikte yeniden örnekleyen 10.000 bootstrap tekrarının %2,5 ve %97,5 yüzdeliklerinden hesaplandı (seed 2026). Bu eşleme, iki yöntemin aynı bölümlerde doğru veya yanlış tahmin yapmasını hesaba katıyor. Her ofset için aralıklar ayrı hesaplandı.

| Yöntem | ±2 sn kaydırılmış ortalama (%) | `D₁` (yüzde puanı) | `D₂` (yüzde puanı) | `D₂ − D₁` (yüzde puanı) |
| --- | ---: | ---: | ---: | ---: |
| A+V-att referansı | 69,69 | 0,39 [−0,19, 0,97] | **1,89 [1,06, 2,74]** | **1,49 [0,68, 2,34]** |
| Yerel ses ortalaması | 70,52 | 0,02 [−0,46, 0,52] | 1,31 [0,56, 2,07] | 1,29 [0,62, 1,99] |
| Norm eşlemeli ablasyon | 69,96 | 0,44 [−0,15, 1,02] | 1,47 [0,64, 2,30] | 1,04 [0,25, 1,82] |

`D₁` ve `D₂`, ilgili kayma büyüklüğünde eş maskeli kontrol ile kaydırılmış doğruluk arasındaki farkın iki yön ortalamasıdır. Referans için `D₂` ve `D₂ − D₁` aralıkları sıfırın üstünde. Bu, iki saniyelik kaymanın referansın doğruluğunu düşüreceği ve düşüşün bir saniyedekinden büyük olacağı beklentilerini destekliyor.

Yerel ortalama ile referans arasındaki eşlenmiş `D₂` azalması **0,58** yüzde puanı (%95 GA [−0,04, 1,18]). Kaydırmasız fark **−0,08** yüzde puanı (%95 GA [−0,70, 0,54]). Ablasyona göre ±2 saniyedeki farkın alt sınırı sıfıra yakın. Grafik, kaydırılmış doğruluğu ve yöntem farklarını ayrı panellerde gösterir. [Grafik (PNG)](ave_test_accuracy.png) · [Grafik (SVG)](ave_test_accuracy.svg)

Eğitim veya doğrulamada da bulunan sekiz kaynak video çıkarıldığında 394 klip kaldı. Bu alt kümede referans `D₂` değeri **1,92** [%95 GA 1,10, 2,81], yerel ortalamanın ±2 saniyede referansa kazancı **0,85** [0,32, 1,40] ve ablasyona kazancı **0,57** [0,02, 1,12] yüzde puanı oldu. `D₂` azalması **0,59** [−0,04, 1,23] yüzde puanıydı. [Duyarlılık analizi](ave_test.json)

## Çıkarım gecikmesi

Ölçüm bellekteki özelliklerden başladı ve ses ön işlemesini, model çalıştırmayı ve sınıf seçimini kapsadı. MacOS arm64 CPU üzerinde 4 iş parçacığı, tek kliplik grup, yöntem başına 5 ısınma çağrısı ve her ofsetin ilk 32 klibi kullanıldı. Üç yöntemin çağrı sırası klipler arasında döndürüldü.

| Yöntem | Ölçüm | Medyan (ms/klip) | p95 (ms/klip) |
| --- | ---: | ---: | ---: |
| A+V-att referansı | 160 | 0,696 | 0,757 |
| Yerel ses ortalaması | 160 | 0,717 | 0,787 |
| Norm eşlemeli ablasyon | 160 | 0,723 | 0,795 |

Yerel ortalama bu koşuda medyana yaklaşık **0,020 ms/klip (%2,9)** ekledi.

## Hata analizi

`±2` saniyede, sesin geldiği saniye ile hedef saniyenin özgün etiketlerinde olay varlığının ayrıştığı 508 bölüm, 4.824 bölüm koşulunun %10,5'ini oluşturdu. Referansın eş maskeli kontrollere göre kaybettiği net 91 doğru tahminin 76'sı (%83,5) bu gruptaydı. Yerel ortalama iki yönde toplam 86 hatayı düzeltti ve 46 yeni hata yaptı. Olay varlığının ayrıştığı grupta bu sayılar 21 ve 8 idi.

| Kayma | Olay varlığı ayrışan bölüm | Bu grupta referansın net kaybı | Yerel ortalamanın düzelttiği / bozduğu (tüm bölümler) |
| ---: | ---: | ---: | ---: |
| −2 sn | 254 | 28 | 42 / 22 |
| −1 sn | 133 | 14 | 25 / 23 |
| 0 sn | 0 | 0 | 27 / 29 |
| +1 sn | 130 | 15 | 33 / 19 |
| +2 sn | 254 | 48 | 44 / 24 |

- **Düzelen başlangıç.** AVE satırı 27, `+2` saniye. Çan 5. saniyede başlıyor ve bu hedefe özgün sesin 3. saniyesi geliyor. Referans arka plan, yerel ortalama çan tahmin etti.
- **Yeni kaçırılan olay.** AVE satırı 421, `+2` saniye. Havlama 1. saniyede başlıyor ve 2. saniyedeki hedefe özgün sesin 0. saniyesi geliyor. Referans havlamayı buldu, yerel ortalama arka plan tahmin etti.
- **Kaydırmasız başlangıç hatası.** AVE satırı 68, 0 saniye. Referans, çanın başladığı 6. saniyeyi doğru sınıflandırdı. Yerel ortalama arka plan tahmin etti.

Bu örnekler anotasyon aralıkları ve kaydedilen tahminlerden seçildi. [Tüm örnekler ve sayımlar](ave_test.json) · [Bölüm bazında tahminler](ave_test_predictions.csv)

Proje kökünden test ve grafik komutları aşağıdadır. Test için Adım 3'teki önbellek ve doğrulamada sabitlenen dosyalar gerekir. Grafik, ayrı yerel klasördeki Matplotlib 3.10.8 ile üretildi.

```bash
.ave-local/venv/bin/python -B scripts/ave_test.py
PYTHONPATH=.ave-local/plot-deps MPLCONFIGDIR=.ave-local/matplotlib .ave-local/venv/bin/python -B scripts/plot_ave_test.py
```
