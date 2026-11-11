"""Build the YZM5110 report from saved results and the literature matrix."""

import argparse
import json
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, NextPageTemplate, PageBreak, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
)
import matplotlib


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
FONT_DIR = Path(matplotlib.get_data_path()) / "fonts/ttf"
pdfmetrics.registerFont(TTFont("Body", str(FONT_DIR / "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("BodyBold", str(FONT_DIR / "DejaVuSans-Bold.ttf")))
pdfmetrics.registerFontFamily("Body", normal="Body", bold="BodyBold", italic="Body", boldItalic="BodyBold")
INK = colors.HexColor("#162333")
MUTED = colors.HexColor("#4b5d70")
TEAL = colors.HexColor("#087b68")
STYLES = {
    "title": ParagraphStyle("title", fontName="BodyBold", fontSize=23, leading=29, spaceAfter=16, textColor=INK),
    "h1": ParagraphStyle("h1", fontName="BodyBold", fontSize=16, leading=21, spaceAfter=14, textColor=INK),
    "h2": ParagraphStyle("h2", fontName="BodyBold", fontSize=11, leading=16, spaceBefore=8, spaceAfter=7, textColor=INK),
    "body": ParagraphStyle("body", fontName="Body", fontSize=10.2, leading=14.9, spaceAfter=10, textColor=INK),
    "small": ParagraphStyle("small", fontName="Body", fontSize=8.4, leading=11.5, spaceAfter=7, textColor=MUTED),
    "cell": ParagraphStyle("cell", fontName="Body", fontSize=8.3, leading=11.2, textColor=INK),
    "matrix": ParagraphStyle("matrix", fontName="Body", fontSize=8.2, leading=11.2, textColor=INK),
}


def p(text, style="body"):
    # Normalize dash characters to ASCII for portable PDF text rendering.
    text = text.replace("−", "-").replace("–", "-").replace("—", "-")
    return Paragraph(text, STYLES[style])


def number(value, precision=2):
    return f"{value:.{precision}f}".replace(".", ",").replace("-0,00", "0,00")


def measured(value):
    return f"{number(value['estimate'])} [{number(value['ci95'][0])}, {number(value['ci95'][1])}]"


def table(rows, widths, style="cell"):
    values = [[p(escape(str(value)).replace("\n", "<br/>"), style) for value in row] for row in rows]
    tab = Table(values, colWidths=widths, hAlign="LEFT", repeatRows=1)
    tab.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eaf0f5")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("LINEBELOW", (0, 0), (-1, 0), 0.7, MUTED),
        ("LINEBELOW", (0, 1), (-1, -1), 0.25, colors.HexColor("#d5dee6")),
    ]))
    return tab


def footer(canvas, doc):
    width, height = canvas._pagesize
    canvas.saveState()
    canvas.setFont("Body", 7.4)
    canvas.setFillColor(MUTED)
    canvas.drawString(46, height - 28, "Eren Kahraman  |  YZM5110  |  AVE ve ses kayması")
    canvas.drawString(46, 25, "Araştırma projesi  |  11 Kasım 2026")
    canvas.drawRightString(width - 46, 25, str(doc.page))
    canvas.restoreState()


def build(repo_url, published):
    test = json.loads((RESULTS / "ave_test.json").read_text())
    ref = json.loads((RESULTS / "ave_reference.json").read_text())
    validation = json.loads((RESULTS / "ave_improvement_validation.json").read_text())
    lit = json.loads((ROOT / "report/literature.json").read_text())
    methods = ("reference", "local_average", "norm_matched")
    labels = {"reference": "A+V-att", "local_average": "Yerel ortalama", "norm_matched": "Norm eşlemeli"}
    destination = ROOT / "output/pdf/Kahraman_YZM5110_Research.pdf"
    destination.parent.mkdir(parents=True, exist_ok=True)
    doc = BaseDocTemplate(str(destination), pagesize=A4, title="AVE üzerinde ses ve görüntü arasındaki zaman kaymasının etkisi",
                          author="Eren Kahraman", leftMargin=46, rightMargin=46, topMargin=49, bottomMargin=44)
    templates = []
    for name, size in (("portrait", A4), ("landscape", landscape(A4))):
        width, height = size
        frame = Frame(46, 44, width - 92, height - 96, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        templates.append(PageTemplate(id=name, frames=[frame], pagesize=size, onPage=footer))
    doc.addPageTemplates(templates)
    story = []

    def prose(text):
        for paragraph in text.strip().split("\n\n"):
            story.append(p(paragraph.replace("\n", " ")))

    def page(title):
        if story:
            story.append(PageBreak())
        story.append(p(title, "h1"))

    story.append(p("AVE üzerinde ses ve görüntü arasındaki zaman kaymasının etkisi", "title"))
    story.append(p("Eren Kahraman<br/>Yıldız Teknik Üniversitesi<br/>YZM5110 Multimodal Learning<br/>Araştırma projesi · 11 Kasım 2026", "small"))
    story.append(p(f'<b>GitHub deposu</b><br/><link href="{escape(repo_url)}" color="#087b68">{escape(repo_url)}</link>', "small"))
    if not published:
        story.append(p("Depo bağlantısı planlanan hedeftir. Herkese açık yayımlama onayı bekleniyor.", "small"))
    story.append(p("Özet", "h2"))
    prose("""Bu çalışma, yayımlanmış A+V-att modelinde ses ile görüntü arasındaki saat kaymasının olay konumlandırmaya etkisini inceler. Ses özellikleri 0, ±1 ve ±2 saniye kaydırılır. Her koşul, aynı sınır bölümleri sıfırlanmış kaydırmasız kontrolle karşılaştırılır. Model ağırlıkları ve özgün etiketler sabittir.

Özgün AVE testindeki 402 klipte iki saniyelik kayma, referansı ortalama 1,89 yüzde puanı düşürdü (%95 güven aralığı [1,06, 2,74]). Tek müdahale olan yerel ses ortalaması, kaydırılmış örneklerde referansa göre 0,83 puan kazandırdı [0,29, 1,35]. Kayma kaybındaki azalma 0,58 puan oldu ve aralığı sıfırı içerdi [-0,04, 1,18]. Sonuçlar, küçük bir ses ön işlemesinin faydasını ve temiz girdideki maliyetini birlikte gösterir.""")
    story.append(p("1 Araştırma sorusu ve kapsam", "h2"))
    prose("""Araştırma sorusu, ses akışı görüntüye göre öne veya arkaya kaydırıldığında A+V-att'nin özgün olay sınıfını ve zamanını ne ölçüde geri kazanabildiğidir. Saat kayması, çok kipli kanıtın aynı zaman damgasında güvenilir biçimde birleştiği varsayımını sınar.

Katkılar; beş makalenin eleştirel karşılaştırması, yayımlanmış checkpoint'in özgün testte yeniden üretimi, iki yönlü ve eş maskeli kayma protokolü, yerel ses ortalaması ile norm eşlemeli ablasyon ve kaynak video düzeyinde belirsizlik analizidir. Çalışma bir saniyelik hazır özelliklerle, tek checkpoint ve CPU çıkarımıyla sınırlıdır. [1, 6]""")

    page("2 Literatür araması ve eleştirel sentez")
    prose("""İlk tarama 9 Kasım 2026'da “audio-visual event localization AVE temporal misalignment”, “temporal inconsistent audio-visual event localization” ve “audio-visual event localization AVE cross-temporal alignment” sorgularıyla yapıldı. Yayıncı kayıtları, tam metinler ve yazar depoları kullanıldı. Seçim, AVE bölüm doğruluğunu raporlayan ve farklı bir kipler arası etkileşim mekanizması sunan beş çalışmaya odaklandı. Bu proje odaklı taramanın kapsamlı bir sistematik derleme iddiası yoktur.

Tian vd. aynı saniyedeki sesle görsel bölgeleri ağırlıklandırır. CMAN, ne zaman ve hangi kipe güvenileceğini kapılarla seçer. PSP, eşzamanlı olmayı gerektirmeyen pozitif çiftler arasında özellik taşır. CMBS, karşı kipteki ilgisiz kanıtı bastırır. AVSGN, sınıf metinlerinin ortak anlamından ve zamanlar arası alt graflardan yararlanır. [1-5]

Yayınlardaki ablasyonlar, mekanizmaları kendi sistemleri içinde değerlendirir. CMAN'da sentinel çıkarılması %77,1'i %76,1'e; PSP çıkarılması %77,8'i %73,7'ye; CMBS zaman bastırmasının çıkarılması %79,3'ü %77,93'e indirir. AVSGN ses-görüntü alt grafı çıkarılınca %83,1'den %80,3'e iner. Bunlar yayınlardan alınan değerlerdir. [2-5]""")
    story.append(table([["Çalışma", "Tam / zayıf denetimli yayın skoru", "Ana mekanizma"],
                        ["AVEL 2018", "%72,7 / %66,7", "Sesle yönlendirilen görsel dikkat"],
                        ["CMAN 2020", "%77,1 / %75,7", "Uyarlamalı kip ve zaman seçimi"],
                        ["PSP 2021", "%77,8 / %73,5", "Pozitif bölüm çiftlerinden yayılım"],
                        ["CMBS 2022", "%79,3 / %74,2", "Zaman ve olay düzeyinde bastırma"],
                        ["AVSGN 2025", "%83,1 / %78,8", "Metin destekli anlamsal alt graflar"]], [105, 169, 229]))
    story.append(Spacer(1, 12))
    prose("""Skorlar arasındaki artış tek bir bileşene bağlanamaz. Kodlayıcılar, eğitim sinyalleri ve uygulama ayrıntıları farklıdır. Örneğin AVSGN, Tian'ın VGG özellikleri yerine CLIP/CLAP kullanır. Projenin yaklaşımı bu sistemleri yeniden eğitmek yerine, tek checkpoint'te kontrollü kaymayı ve sınır kaybını ölçmektir. Ek A, yönergedeki yedi alanı her makale için karşılaştırır.

Zamansal kaydırmanın kendisi yeni bir fikir olarak ileri sürülmez. AV-AND deposunda AVE üzerinde kayma denemeleri vardır. Buradaki katkı, seçilen ağırlıklarda iki yönü, eş sınır maskesini ve eşlenmiş belirsizliği birlikte raporlayan sınırlı bir deneydir. [10]""")

    page("3 Seçilen yöntemin teknik açıklaması")
    prose("""AVE görevinde her 10 saniyelik klip, birer saniyelik on bölüme ayrılır. Her bölümün hedefi 28 olay sınıfından biri veya arka plandır. Hazır ses vektörü a(t), 128 boyutludur. Görsel özellik V(t), 7 × 7 konumda 512 boyutlu vektör taşır. [1, 6]

A+V-att önce görsel ve işitsel özellikleri doğrusal dönüşüm ve ReLU ile işler. Ses temsili, aynı saniyedeki bütün görsel konumlara yayınlanır. Öğrenilmiş dönüşümler ve tanh, her görsel konumun dikkat skorunu üretir. Konumlar üzerinde softmax ile normalize edilen dikkat, özgün görsel vektörlerin ağırlıklı toplamını verir.

Bu özet görsel dizi ve özgün ses dizisi iki ayrı çift yönlü LSTM'ye girer. Her LSTM'nin yön başına gizli boyutu 128'dir. İki dizinin 256 boyutlu çıktıları birleştirilir. ReLU, 512'den 64'e doğrusal katman, ReLU ve 29 sınıflı çıktı katmanı ardından softmax bölüm olasılıklarını verir. Tahmin en yüksek olasılıklı sınıftır. [6]""")
    story.append(p("Görsel dikkat ve karar", "h2"))
    prose("""Her saniyede görsel özet, c(t) = toplam_j alpha(t,j) V(t,j) biçimindedir. alpha(t,j), konumlar üzerinde toplamı 1 olan öğrenilmiş ses koşullu ağırlıklardır. Son karar p(y(t) | A,V), iki BiLSTM'nin bütün klipten aldığı bağlama dayanır. Bu yüzden yalnız puanlanan orta saniyelere bakmak, sınırdaki ses kaybının model içindeki etkisini ortadan kaldırmaz.

Ses kayması önce aynı saniyedeki görsel dikkati, ardından ses BiLSTM bağlamını etkileyebilir. Bu bağlantı deneyin hipotezini kurar. Ana ölçüm bu iki etkinin birleşik sonucudur. Dikkat haritaları veya gizli durumlara yönelik nedensel bir ayrıştırma yapılmadı.

Makale tam denetimli sınıflandırmayı çapraz entropiyle açıklar. İncelenen eğitim betiği MultiLabelSoftMarginLoss kullanır. Proje hazır ağırlıklarla yalnız çıkarım yaptığı için bu fark kaydedildi. Aynı kodun yeniden eğitim sonucu, bu rapordaki checkpoint değerlendirmesinden farklı bir yeniden üretim hedefi olur. [1, 6]""")
    story.append(p("Dersle bağlantı", "h2"))
    prose("""Hafta 3'teki füzyon ve bozuk kip kontrolleri, tek bileşenin eş koşullarda sınanmasına karşılık gelir. Hafta 4'teki zaman birimi, saat kayması ve hizalama tartışması bir saniyelik ofsetleri motive eder. Hafta 5'teki kaynak ailesine göre bölme ilkesi, eğitim/doğrulama ile kaynak video örtüşmesini ayrıca incelemeyi gerektirir. [9]""")

    page("4 Yeniden üretim hedefi ve uyarlamalar")
    prose("""Hedef, Tian vd.'nin Tablo 1'inde A+V-att için yayımlanan %72,7 bölüm doğruluğunu özgün test bölümünde yeniden üretmektir. Başlangıç beklentisi, aynı hazır özellikler ve checkpoint ile makalenin bir ondalık basamakta verdiği skora yaklaşmaktır. Aynı kaynaklar ve doğrulanmış veri sırası altında belirgin bir fark, veri veya uygulama uyumsuzluğunu araştırmayı gerektirir. [1]

Özgün model kaynağı ve ağırlık SHA-256 özetleri denetlenir. Eski PyTorch pickle'ı yalnız beklenen sınıflar için izin veren yükleyiciyle okunur. Modern ağ kurulduktan sonra bütün checkpoint parametreleri strict=True ile yüklenir. Dört CUDA sıfır gizli durumu, girdi cihazında oluşturulacak şekilde bellekte değiştirilir. Eski Xavier başlatıcısının adı güncellenir. Öğrenilmiş parametreler korunur. [6]""")
    story.append(table([["Ölçüm", "Doğru bölüm / toplam", "Doğruluk"],
                       ["Yayımlanmış A+V-att", "Makale Tablo 1", "%72,7"],
                       ["Bu proje, maskesiz 0 sn", "2.924 / 4.020", f"%{number(ref['accuracy_percent'], 4)}"]], [205, 180, 118]))
    story.append(Spacer(1, 12))
    prose("""Yuvarlanmış yayın değerine fark +0,0363 yüzde puanı. İki değer bir ondalık basamakta %72,7'dir. Bu sonuç yayımlanmış ağırlıkların çıkarım yeniden üretimidir.

Özgün ortam Python 3.6/PyTorch 0.3.0 iken çalışma Python 3.12.14/PyTorch 2.15.0, NumPy 2.5.4 ve h5py 3.16.0 ile macOS arm64 CPU'da yapıldı. Doğruluk çıkarımında 16 kliplik gruplar ve 4 CPU iş parçacığı kullanıldı.

Google Drive ses bağlantısı kota hatası verdiği için aynı beklenen şekil ve boyuttaki LECOO/AVE aynası kullanıldı. Görüntü özellikleri yazarların HDF5 dosyasından, doğru HTTP 206 Content-Range başlığı ve bayt uzunluğu zorunlu tutularak alındı. Ses aynasının özgün dosyayla tam dosya özeti karşılaştırması yapılamadı. Bu sınır bütün sonuçların yorumuna dahildir. [7, 8]

İlk veri denemesinde tamamen sıfır ses döndüren aralık okuması tespit edildi ve o koşu elendi. Sonraki üç kliplik kontrolde özellikler sonlu ve sıfırdan farklıydı, etiketler aynı veri satırından alındı ve model (3,10,29) çıktı verdi. Yayımlanmış tablolarda kullanılan deneyler bu doğrulanmış veri yolundan üretildi.""")
    story.append(p("Kaynak revizyonu", "h2"))
    story.append(p("93f843fed72fb17394df76330df958b0c2dbde76", "small"))

    page("5 Önerilen iyileştirme ve gerekçesi")
    prose("""Doğrulama bölümünde iki saniyelik kaymada eş maskeli kontrole göre net 77 doğru bölüm kaybı görüldü. Sesin kaynak saniyesi ile hedef saniyenin olay varlığı ayrıştığında kayıp yoğunlaştı. Örneğin çan başlangıcından sonraki sesin erken bir arka plan bölümüne gelmesi, modeli olayı erken tahmin etmeye yöneltebilir.

Bu gözlemden sonra, iyileştirme koşusu görülmeden önce tek müdahale seçildi. Her merkez ses vektörü, yarıçapı iki saniye olan pencerenin geçerli komşularıyla harmanlandı. Merkez %50, komşu ortalaması %50 ağırlık taşır. Merkez ortalamaya ikinci kez katılmaz. Yapay sınır boşlukları ortalamaya girmez ve sıfır kalır. Geçerli komşu yoksa merkez korunur. Sıfır merkez vektörü iki kolda da sıfır kalır.""")
    story.append(p("İşlem", "h2"))
    prose("""N(t), 0 &lt; |s-t| ≤ 2 koşulunu ve geçerli ses maskesini sağlayan komşular olsun. m(t), N(t) içindeki a(s) vektörlerinin ortalamasıdır. Müdahale b(t) = 0,5 a(t) + 0,5 m(t) uygular. Girdi, A+V-att'nin hem görsel dikkat hem ses LSTM yoluna bu biçimde verilir.

Beklenti, kaymış başlangıç veya bitiş yakınındaki komşuların doğru olaya ait bilgiyi hedef saniyeye kısmen taşımasıdır. Yöntem kayma yönünü veya büyüklüğünü tahmin etmez. Yalnız verilen geçerlilik maskesini kullanır. Özgün görüntü ve etiketler sabittir. Doğru hizalanmış örneklerde komşu karışımı geçişi bulanıklaştırabilir.""")
    story.append(p("Norm eşlemeli ablasyon", "h2"))
    prose("""Ablasyon u(t) = a(t) ||b(t)||₂ / ||a(t)||₂ uygular. Sesin merkezdeki özellik yönünü koruyup büyüklüğünü müdahaleninkiyle eşler. Bu, komşu özellik yönlerinin katkısını yalnız norm değişiminden ayırmaya yardımcı olur. Ablasyonun norm hedefi de komşulardan geldiği için bu kontrolün kendisi zaman bağlamı kullanır.

Doğrulama tamamlandığında ±2 saniyede ortalama doğruluk referansta %71,56, müdahalede %72,16, ablasyonda %71,27 bulundu. Kaydırmasız doğruluk %73,42'den %73,34'e indi. Yarıçap veya karışım ağırlığı için test üzerinde arama yapılmadı. Bu tek aday ve bütün gözlenen olumsuz sonuçlar kayıt altına alındı.

Yapılandırma ve yöntem dosyası SHA-256 özetleri testten önce doğrulama çıktısına yazıldı. Test betiği bu özetler uyuşmazsa durur. Böylece aşağıdaki test sonuçları aynı müdahalenin değerlendirmesidir.""")

    page("6 Deney tasarımı ve ölçüler")
    story.append(table([["Bileşen", "Sabitlenen protokol"],
                       ["Veri bölümleri", "3.339 eğitim / 402 doğrulama / 402 özgün test"],
                       ["Girdiler ve hedef", "10 × 128 ses, 10 × 7 × 7 × 512 görüntü; 29 sınıflı özgün etiket"],
                       ["Ofsetler", "-2, -1, 0, +1, +2 saniye; pozitif ofset sesi geciktirir"],
                       ["Sınırlar", "Taşıma yok; boş ses sıfır; eş kontrolde aynı sınır sıfır"],
                       ["Puanlama", "Her yöntemde ve koşulda 2-7 indisleri, 2.412 bölüm"],
                       ["Belirsizlik", "10.000 kaynak video bootstrap tekrarı, seed 2026"],
                       ["Gecikme", "CPU 4 iş parçacığı; tek klip; 5 ısınma; her ofsette ilk 32 klip"]], [132, 371]))
    story.append(Spacer(1, 12))
    prose("""Ofset k için kaydırılmış ses a_k(t) = a(t-k) olur. Klip dışına çıkan kaynaklar sıfırdır. Örneğin +2'de ilk iki ses bölümü sıfırlanır. Kontrolde ses kaydırılmaz ve aynı ilk iki bölüm sıfırlanır. -2'de son iki bölüm iki kolda da sıfırdır. Klip uçları birbirine sarılmaz. BiLSTM bütün klibi gördüğü için bu eşleme çıkarımdan önce uygulanır.

Birincil kayma ölçüsü D₂, ±2 yönlerinin eş maskeli kontrol eksi kaydırılmış doğruluk farkının ortalamasıdır. Beklenti D₂ &gt; 0. İkincil beklenti D₂ &gt; D₁'dir. Müdahale için birincil karşılaştırma ±2 kaydırılmış doğrulukta yerel ortalama eksi referans farkıdır. Aynı fark ablasyona karşı da ölçülür. Kaydırmasız maliyet ve yöntem başına D₂ ayrıca raporlanır.

Bootstrap, kaynak video kimliklerini bütün yöntem ve ofsetlerle birlikte yeniden örnekler. Yüzdelik %2,5 ve %97,5 sınırları %95 aralığı verir. Mutlak skor aralıkları ile eşlenmiş fark aralıkları ayrı hesaplanır. Ofset bazındaki aralıklar çoklu karşılaştırma düzeltmesi içermez. Testteki 402 klibin kaynak kimlikleri farklıdır. Eğitim/doğrulamayla ortak sekiz kimlik çıkarılarak 394 klipte duyarlılık analizi yapılır.

Gecikme, bellekteki özelliklerden ön işleme, model ve argmax sonuna kadar ölçülür. Disk/ağ erişimi ve ham kiplerden özellik çıkarımı bu süreye dahil değildir. Yöntem çağrı sırası klipler arasında döndürülür. Zamanlama başına 160 gözlemden medyan ve p95 raporlanır.""")

    page("7 Sonuçlar ve eşlenmiş kontroller")
    story.append(p("Kaydırılmış bölüm doğruluğu", "h2"))
    rows = [["Kayma", "A+V-att", "Yerel ortalama", "Norm eşlemeli"]]
    for condition in test["conditions"]:
        line = [f"{condition['offset_seconds']:+d} sn"]
        for method in methods:
            value = condition["methods"][method]
            bounds = value["accuracy_ci95_percent"]["shifted"]
            line.append(f"%{number(value['accuracy_percent']['shifted'])}\n[{number(bounds[0])}, {number(bounds[1])}]")
        rows.append(line)
    story.append(table(rows, [62, 147, 147, 147]))
    story.append(Spacer(1, 12))
    story.append(p("İki yönün ortalamasında kayma kaybı", "h2"))
    rows = [["Yöntem", "D₁ (yüzde puanı)", "D₂ (yüzde puanı)"]]
    for method in methods:
        rows.append([labels[method], measured(test["overall"][method]["d1_pp"]), measured(test["overall"][method]["d2_pp"])])
    story.append(table(rows, [145, 179, 179]))
    story.append(Spacer(1, 12))
    prose("""Referansın D₂ aralığı sıfırın üstünde olduğu için birincil kayma hipotezi desteklenir. D₂ - D₁ farkı 1,49 [0,68, 2,34] yüzde puanıdır. Bir saniyelik kaymada toplam yön ortalaması belirsizken iki saniyede düşüş daha belirgindir. İleri ve geri yönün büyüklüğü aynı değildir.

Yerel ortalama ±2 saniyede ortalama %70,52, referans %69,69 ve ablasyon %69,96 verdi. Müdahale referansı 0,83 [0,29, 1,35], ablasyonu 0,56 [0,02, 1,10] yüzde puanı geçti. Ablasyon farkının alt sınırı sıfıra yakındır. Referansa göre kayma kaybındaki azalma 0,58 [-0,04, 1,18] puandır. Kaydırılmış doğruluk kazanımı, kayma kaybının azaldığı iddiasından daha kesin görünmektedir.""")

    page("7 Sonuçlar için doğruluk grafiği")
    story.append(Image(str(RESULTS / "ave_test_accuracy.png"), width=503, height=398))
    story.append(p("Şekil 1. Üst panel kaydırılmış örneklerin bölüm doğruluğunu, alt panel yerel ortalama ile iki karşılaştırmanın eşlenmiş farklarını gösterir. Çubuklar kaynak video düzeyinde %95 bootstrap güven aralıklarıdır.", "small"))
    story.append(p("Sınır maskesinin etkisi", "h2"))
    rows = [["Kaymanın kontrolü", "A+V-att (%)", "Yerel ortalama (%)", "Norm eşlemeli (%)"]]
    for condition in test["conditions"]:
        rows.append([f"{condition['offset_seconds']:+d} sn", *[
            number(condition["methods"][m]["accuracy_percent"]["aligned"]) for m in methods]])
    story.append(table(rows, [122, 127, 127, 127]))
    story.append(Spacer(1, 10))
    prose("""Her kaymanın kontrolü farklı sınırı maskelediği için ayrı bir skor üretir. Örneğin +2 referansı kendi %71,89 kontrolüyle, -2 referansı kendi %71,27 kontrolüyle karşılaştırılır. Tablonun 0 saniyesi %72,60'tır ve altı saniyelik puanlamaya aittir. Makaleyle karşılaştırılan tam klip skoru %72,7363'tür.""")

    page("7 Kaynak ölçümü ve hata analizi")
    rows = [["Yöntem", "Medyan ms/klip", "p95 ms/klip", "Çağrı"]]
    for method in methods:
        value = test["latency"]["methods"][method]
        rows.append([labels[method], number(value["median_ms"], 3), number(value["p95_ms"], 3), value["samples"]])
    story.append(table(rows, [167, 124, 124, 88]))
    story.append(Spacer(1, 12))
    prose("""Yerel ortalama medyana yaklaşık 0,020 ms/klip, yani %2,9 ekledi. Bu değer kısa CPU çağrılarının ölçümüdür ve makine yükünden etkilenebilir.

İki saniyelik kaymada olay varlığının hedef ve kaynak saniyeler arasında ayrıştığı 508 bölüm, 4.824 bölüm koşulunun %10,5'idir. Referansın eş maskeli kontrollere göre net 91 kaybının 76'sı (%83,5) bu gruptadır. Bu gruplama özgün zaman etiketlerine dayanır.

Yerel ortalama iki yönde 86 hatayı düzeltti ve 46 yeni hata yaptı. Ayrışan olay varlığı grubunda bu sayılar 21 ve 8'dir. 0 saniyede 27 hata düzeldi ve 29 doğru bölüm bozuldu. Yöntemin temiz girdi üzerindeki ortalama farkı -0,08 [-0,70, 0,54] puandır.""")
    story.append(table([["Örnek", "Hedef ve referans", "Yerel ortalama"],
                       ["Satır 27, +2 sn, t=5. Çan 5-10 sn. Kaynak ses t=3.", "Hedef çan. Referans arka plan.", "Çan. Başlangıç geri kazanıldı."],
                       ["Satır 421, +2 sn, t=2. Havlama 1-10 sn. Kaynak ses t=0.", "Hedef havlama. Referans havlama.", "Arka plan. Yeni kaçırma."],
                       ["Satır 68, 0 sn, t=6. Çan 6-10 sn.", "Hedef çan. Referans çan.", "Arka plan. Temiz başlangıç bulanıklaştı."]], [210, 155, 138]))
    story.append(Spacer(1, 12))
    prose("""Eğitim veya doğrulamayla kaynak kimliği ortak sekiz klip çıkarıldığında 394 klip kalır. Referans D₂ = 1,92 [1,10, 2,81] puandır. Müdahalenin referansa kazancı 0,85 [0,32, 1,40], ablasyona kazancı 0,57 [0,02, 1,12] puandır. D₂ azalması 0,59 [-0,04, 1,23] puanla belirsizliğini korur. Ana yorum bu filtreye duyarlı görünmemektedir.""")

    page("8 Sınırlılıklar ve sonuç")
    prose("""Özgün AVE testinde iki saniyelik ses kayması, A+V-att'nin özgün olayları geri kazanma başarısını düşürdü. Aynı sınır maskesiyle hesaplanan D₂'nin aralığı sıfırın üstünde. Yerel ses ortalaması, küçük bir gecikme maliyetiyle kaydırılmış doğruluğu artırdı. Kayma kaybını azalttığına ilişkin aralık ise sıfırı içeriyor.

Etiketler özgün zaman çizgisinde sabit tutuldu. Bu kurgu, sensör saat hatası altında özgün olayın geri kazanılmasını sınar. Yapay kaymadan sonra “aynı anda duyulan ve görülen olay” tanımına göre yeni etiket üretmek farklı bir değerlendirme kurar. Sonuçların kapsamı bu hedef seçimine bağlıdır.

Tek checkpoint ve tek veri kümesi kullanıldı. Bir saniyelik hazır özellikler, alt saniyelik kaymayı ve ham kodlayıcının davranışını örter. Sentetik sıfır dolgu ve geçerlilik maskesi deney kurulumu tarafından bilinir. Sonuçlar doğal sensör gecikmelerinin bütün çeşitlerini kapsamaz. Yöntem çevrimdışıdır, komşular gelecek saniyeleri ve referans çift yönlü bağlamı kullanır.

Ses aynası özgün dosyayla tam olarak karşılaştırılamadı. Kaynak video örtüşmesi ayrıca sınandı, ön eğitim kaynaklarıyla olası örtüşme ölçülmedi. Bootstrap aralıkları test örneklemesine ilişkindir. Yeniden eğitim veya checkpoint değişkenliğini kapsamaz. Gecikme yalnız hazır özelliklerden CPU çıkarımını kapsar.

Açık sorular, alt saniyelik veya değişken gecikme, doğal uyumsuzluk, farklı checkpoint'ler ve komşu harmanının olay sınırlarını koruyan sürümleridir. Bunlar yeni doğrulama tasarımı gerektirir. Bu rapordaki nihai test sonuçlarıyla ayar değiştirilmedi.""")
    story.append(p("Yapay zekâ kullanımı beyanı", "h2"))
    prose("""OpenAI Codex; kaynak arama, karşılaştırma matrisi ve sentez taslağı, yazar kodunun CPU uyarlaması, veri doğrulama, deney betikleri, yerel deney yürütme, bootstrap ve hata analizi, grafikler ve rapor/sunum düzenlemesinde kullanıldı. Konu, hipotez, eş maskeli karşılaştırma ve yerel ortalama/ablasyon tasarımı görüşme içinde Codex önerileriyle geliştirildi. Sayısal sonuçlar yerel betik çıktılarından alındı.

Ödev yönergesinin 7. bölümü beyan edilen desteğe izin verir. Kaynakları okuma, uygulamayı anlama, deney tasarımını değerlendirme, iddiaları ve atıfları doğrulama, sonuçları savunma sorumluluğu Eren Kahraman'a aittir. Somut katkılar depodaki AI_USAGE.md içinde açıklanır.""")

    story.append(NextPageTemplate("landscape"))
    page("Ek A  Beş makalenin karşılaştırma matrisi")
    story.append(p("A1  Soru ve katkı, kipler ve varsayımlar, mekanizma ve amaç. T/Z, tam ve zayıf denetimli eğitimi gösterir. Yayın sonuçları bu projenin ölçümlerinden ayrıdır.", "small"))
    story.append(table([["Makale", "Soru ve katkı", "Kipler ve varsayımlar", "Mekanizma ve amaç"], *[
        [item["name"], item["question"], item["modalities"], item["mechanism"]] for item in lit]], [100, 218, 204, 228], "matrix"))

    page("Ek A  Veri, kanıt ve yeniden üretim")
    story.append(p("A2  Aynı beş satırın devamı. Böylece her çalışma yönergedeki yedi değerlendirme alanını kapsar. Tam metin kaynakları [1-5].", "small"))
    story.append(table([["Makale", "Veri ve protokol", "Referans ve kanıt", "Kaynak ve yeniden üretim", "Sınırlılıklar ve bağlantılar"], *[
        [item["name"], item["data"], item["evidence"], item["resources"], item["limits"]] for item in lit]],
        [92, 163, 170, 162, 163], "matrix"))

    story.append(NextPageTemplate("portrait"))
    page("Kaynakça ve yeniden üretim kaydı")
    refs = [
        ("[1] Tian, Y., Shi, J., Li, B., Duan, Z. ve Xu, C. (2018). Audio-Visual Event Localization in Unconstrained Videos. ECCV.", lit[0]["url"]),
        ("[2] Xuan, H., Zhang, Z., Chen, S., Yang, J. ve Yan, Y. (2020). Cross-Modal Attention Network for Temporal Inconsistent Audio-Visual Event Localization. AAAI.", lit[1]["url"]),
        ("[3] Zhou, J., Zheng, L., Zhong, Y., Hao, S. ve Wang, M. (2021). Positive Sample Propagation Along the Audio-Visual Event Line. CVPR.", lit[2]["url"]),
        ("[4] Xia ve Zhao (2022). Cross-Modal Background Suppression for Audio-Visual Event Localization. CVPR.", lit[3]["url"]),
        ("[5] Liu vd. (2025). Audio-Visual Semantic Graph Network for Audio-Visual Event Localization. CVPR.", lit[4]["url"]),
        ("[6] Tian vd. AVE-ECCV18 kaynak kodu ve checkpoint. Sabit revizyon 93f843fed72fb17394df76330df958b0c2dbde76.", "https://github.com/YapengTian/AVE-ECCV18"),
        ("[7] AVE yazarlarının ses ve görüntü özellik bağlantıları.", "https://github.com/YapengTian/AVE-ECCV18#ave-dataset--features"),
        ("[8] LECOO/AVE ses özelliği aynası. Erişim 10 Kasım 2026.", "https://huggingface.co/datasets/LECOO/AVE/tree/main"),
        ("[9] Çetinkaya, E. YZM5110 Multimodal Learning, Hafta 1-5 slaytları ve Research Project yönergesi. 2026. Kullanıcı tarafından sağlanan ders materyalleri.", None),
        ("[10] AV-AND deposu. Kontrollü temporal misalignment örnekleri.", "https://github.com/cataug/AV-AND#temporal-misalignment"),
    ]
    for description, url in refs:
        text = escape(description)
        if url:
            text += f' <link href="{escape(url)}" color="#087b68">Kaynak bağlantısı</link>'
        story.append(p(text, "small"))
    story.append(p("Çalıştırılabilir kayıt", "h2"))
    prose("""Kod, yapılandırma, JSON/CSV çıktıları, komutlar ve yapay zekâ beyanı teslim deposunda yer alır. Nihai teslim submission-v1, önceki yerel aday submission-v1-rc1 etiketiyle tanımlanır. Kod ve deneyler için README.md içindeki sıralı komutlar, tablolar için scripts/export_tables.py ve grafik için scripts/plot_ave_test.py kullanılır.

9-10 Kasım deneyleri 11 Kasım'da teslim için paketlendi. Deneyler sırasında ayrı commit'ler oluşturulmadı. Araştırma planı aşama kayıtlarını korur. Yazar kodu, ders PDF'leri ve veri/özellik dosyaları depoda yeniden dağıtılmaz.""")
    story.append(p("Yapılandırma SHA-256", "h2"))
    digest = test["config_sha256"]
    story.append(p(digest[:32] + "<br/>" + digest[32:], "small"))
    doc.build(story)
    print(destination)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-url", required=True)
    parser.add_argument("--published", action="store_true", help="The named repository has been published and verified")
    args = parser.parse_args()
    build(args.repo_url, args.published)
