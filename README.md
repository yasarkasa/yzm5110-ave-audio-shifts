# AVE altında kontrollü ses kayması

Eren Kahraman · Yıldız Teknik Üniversitesi · YZM5110 Multimodal Learning · 2026

Bu araştırma projesi, Tian vd.'nin A+V-att modelinde ses akışını görüntüye göre 0, ±1 ve ±2 saniye kaydırır. Her kayma, aynı sınır saniyelerini sıfırlayan kaydırmasız bir kontrolle karşılaştırılır. Tek müdahale, ses özelliklerini yerel komşularla harmanlamaktır. Norm eşlemeli ablasyon, büyüklük değişimini özellik yönünden ayırmaya yardımcı olur.

## Teslim dosyaları

- [Araştırma raporu](output/pdf/Kahraman_YZM5110_Research.pdf)
- [Düzenlenebilir sunum](output/slides/Kahraman_YZM5110_Presentation.pptx)
- [Beş makalenin ayrıntılı karşılaştırması](MAKALE-KARSILASTIRMA.md)
- [Test tabloları, güven aralıkları ve hata analizi](results/ave_test_report.md)
- [Yapay zekâ kullanımı beyanı](AI_USAGE.md) ve [kaynak bileşenler](THIRD_PARTY.md)

## Ölçülen sonuçlar

Özgün test bölümünün 402 klibinde, her koşulda aynı altı saniye puanlandı. ±2 saniyede ortalama doğruluk referansta %69,69, yerel ortalamada %70,52 ve norm eşlemeli ablasyonda %69,96 oldu. Yerel ortalamanın referansa kazancı 0,83 yüzde puanı (%95 GA [0,29, 1,35]). Eş maskeli `D₂` düşüşü referansta 1,89 ve yerel ortalamada 1,31 yüzde puanı. `D₂` azalmasının aralığı sıfırı içerir. Kaydırmasız tam klip yeniden üretimi %72,7363 ve makalenin yayımladığı A+V-att değeri %72,7'dir.

![Kayma bazında doğruluk ve eşlenmiş yöntem farkı](results/ave_test_accuracy.png)

## Kurulum

Test edilen ortam Python 3.12.14, macOS arm64 ve CPU'dur. Git ve ağ erişimi gerekir. Paket sürümleri `requirements.txt` içinde sabittir. Paketlerin desteklediği platformda Python 3.12 kullanın.

```bash
python3.12 -m venv .ave-local/venv
.ave-local/venv/bin/python -m pip install -r requirements-figures.txt
```

Grafik gerekmiyorsa `requirements.txt` yeterlidir. Raporu yeniden oluşturmak için `requirements-report.txt` içindeki ek paketler gerekir.

## Veri ve model erişimi

Hazırlama betiği yazar deposunu `93f843fed72fb17394df76330df958b0c2dbde76` revizyonuna sabitler. Etiketler, bölüm listeleri ve ağırlıklar bu checkout'tan okunur. Görüntü özellikleri yazarların bağlantısından doğrulanmış HTTP aralıklarıyla indirilir. Ses, kayda alınmış SHA-256 özetiyle kontrol edilen LECOO/AVE aynasından gelir. Veriler `.ave-local/` içinde saklanır.

Özgün ses bağlantısı kota hatası verdiği için ayna kullanıldı. Ayna ile özgün dosyanın tam eşdeğerliği doğrulanamadı. Hazır özellikler üzerinde çıkarım yapılır. Ham ses/video kodlama ve yeniden eğitim aşamaları bu çalışmanın kapsamı dışındadır. Erişim bağlantıları ve kullanım koşulları [kaynak kaydında](THIRD_PARTY.md) açıklanır. Ders PDF'leri, veri dosyaları, ortam, büyük ağırlıklar ve kimlik bilgileri yayımlanmaz.

## Küçük çalıştırma kontrolü

Üç doğrulama klibiyle veri, etiket ve model çıktısını kontrol eder. İlk kurulumda yaklaşık 42,4 MB ses, 6 MB görüntü özelliği ve yazar deposu indirilir. İndirme Google Drive veya Hugging Face erişimine bağlıdır. Kota veya HTTP aralık hatasında komut durur. Hazır görüntü satırları korunduğu için aynı komut tekrar çalıştırılabilir.

```bash
.ave-local/venv/bin/python -B scripts/prepare_ave.py --split smoke
.ave-local/venv/bin/python -B scripts/ave_smoke.py
```

## Bildirilen deneylerin tekrar çalıştırılması

Özgün test görüntüleri yaklaşık 807 MB, doğrulama görüntüleri de yaklaşık 807 MB tutar. Her iki bölümün ham önbelleği yaklaşık 1,61 GB'dir. Kurulu PyTorch ve ortam ayrıca disk alanı kullanır. İndirme süresi ağ ve kotaya bağlıdır. Hazır önbellekle deneyler CPU üzerinde çalışır.

```bash
# Görüntü özelliklerini hazırla
.ave-local/venv/bin/python -B scripts/prepare_ave.py --split all

# Makalenin maskesiz tam klip A+V-att sonucunu yeniden üret
.ave-local/venv/bin/python -B scripts/ave_reference.py

# Beş kayma ve eş maskeli kontrolleri doğrula
.ave-local/venv/bin/python -B scripts/ave_shift.py

# Sabit müdahale ve ablasyonu doğrulamada çalıştır
.ave-local/venv/bin/python -B scripts/ave_improvement.py

# Aynı ayarlarla özgün test, bootstrap, gecikme ve hata analizi
.ave-local/venv/bin/python -B scripts/ave_test.py

# Sonuç JSON'undan tabloları ve grafiği oluştur
.ave-local/venv/bin/python -B scripts/export_tables.py
.ave-local/venv/bin/python -B scripts/plot_ave_test.py
```

Test betiği, yöntem ve yapılandırma özetlerini kaydedilen doğrulama koşusuyla karşılaştırır. Değişiklik varsa çalışmayı durdurur. Gecikme tekrarları makine yüküne göre değişebilir. CPU doğruluğu ve güven aralıkları için kullanılan seed 2026'dır. Bootstrap, kaynak video kimliklerini bütün yöntem ve koşullar için birlikte örnekler. Testte 402 farklı kaynak video vardır. Eğitim/doğrulamayla ortak sekiz video çıkarıldığında 394 kliplik duyarlılık analizi ayrıca raporlanır.

Kaydedilmiş JSON ve CSV dosyaları Git'te bulunur. Son iki komut veri indirmeden kaydedilmiş test sonuçlarından tabloları ve grafiği yeniden üretir. Komutlar `results/` altındaki ilgili çıktıları yeniler. Teslim çıktısını korumak için ayrı bir checkout kullanılabilir.

## Deney ayarları ve sürüm

[configs/ave_improvement.json](configs/ave_improvement.json), doğrulamadan önce kaydedilen 2 saniye yarıçap, 0,5 komşu ağırlığı, 2–7 puanlama indisleri, 16 klip doğruluk grubu ve tek klip gecikme protokolünü içerir. Özgün model ağırlıkları sabittir. Testte yöntem ayarı değiştirilmedi. Yapılandırma SHA-256 değeri `5adb3bbca7243ed4d56d9ab1488811b69b522e6bb8b12246a24f08a568d8b846`.

Nihai teslim sürümü `submission-v1`, önceki yerel teslim adayı `submission-v1-rc1` etiketiyle tanımlanır. Depo geçmişi, 9-10 Kasım deneylerini 11 Kasım'da paketleyen kayıtları içerir. Deneyler sırasında ayrı commit'ler oluşturulmadı. Tarihsel Git geçmişi sonradan üretilmedi. Aşamalar ve zamanında kaydedilmiş sonuçlar [araştırma planında](ARASTIRMA-PLANI.md) bulunur.

## Kaynak ve yapay zekâ beyanı

Ana kaynak Tian vd. (ECCV 2018), *Audio-Visual Event Localization in Unconstrained Videos*. [Makale](https://arxiv.org/abs/1803.08842) · [Yazar deposu](https://github.com/YapengTian/AVE-ECCV18)

OpenAI Codex, kaynak taraması, kod uyarlaması, deney yürütme, analiz ve rapor/sunum düzenleme desteğinde kullanıldı. Yöntem ve kontrol tasarımı da görüşme içinde Codex önerileriyle geliştirildi. Somut katkılar [AI_USAGE.md](AI_USAGE.md) içinde açıklandı. Kaynakları okuma, kodu anlama, iddiaları doğrulama ve sonuçları savunma sorumluluğu öğrenciye aittir.
