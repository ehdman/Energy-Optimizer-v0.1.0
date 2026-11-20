# Mimari notları

## v0.4.0 veri akışı

1. Sayaç adaptörü CSV/XLSX dosyasını okur; zaman damgalarını, birimleri ve düzenli aralıkları doğrular.
2. Domain katmanı elektrik yüklerini ve üretim operasyonlarını aynı zaman ufkunda temsil eder.
3. Üretim bağımlılıkları DAG olarak doğrulanır; makine kimlikleri tek-kapasiteli kaynakları tanımlar.
4. MILP çözücüsü üretim önceliği, enerji maliyeti, gecikme, tesis güç sınırı, makine doluluğu ve operasyon sırasını birlikte ele alır.
5. Analiz/raporlama enerji maliyeti ile gecikme cezasını ayrı tutar.
6. Dashboard önerileri gösterir; fiziksel ekipmana komut göndermez.

## Katmanlar

- **Domain modelleri:** Enerji görevi/üretim operasyonu, kaynak kimliği, öncelik, teslim zamanı, optimizasyon isteği ve sonucu.
- **Ingestion:** CSV/XLSX okuma, ISO-8601 zaman damgası, saat dilimi, düzenli aralık ve sayısal veri doğrulaması.
- **Analytics:** Tüketim, maliyet, tepe güç ve üretim yoğunluğu göstergeleri.
- **Optimization:** SciPy/HiGHS MILP ve kısıtları koruyan greedy alternatif.
- **Reporting:** Model bazlı maliyet ve sayaçtan ölçülen dönem karşılaştırması.
- **Dashboard:** Yerel Streamlit pilot arayüzü; kullanıcı hesabı veya veritabanı içermez.

## Üretim ve enerji modeli

Her görev bir üretim operasyonu veya bağımsız esnek enerji yükü olabilir. Aynı machine_id değerini paylaşan işler aynı zaman aralığında çalışamaz. predecessors alanı, bir operasyonun başlayabilmesi için bitmiş olması gereken görevleri tanımlar. Bağımlılık grafiği döngüsüz olmalıdır.

MILP amaç sırası:
1. Çizelgelenen toplam priority_weight değerini maksimize et.
2. Aynı ağırlıklı tamamlanma düzeyinde elektrik maliyeti + açıkça tanımlanmış soft due-date gecikme cezasını minimize et.

Bütün öncelik ağırlıkları 1 ise ilk hedef mümkün olan görev sayısını maksimize eder. Gecikme cezası elektrik faturası maliyeti değildir; ayrı raporlanır. Ağırlıklar göreceli tercihlerdir ve müşteri operasyon sorumlusu tarafından onaylanmalıdır.

## Model kısıtları

- Her görev bir başlangıç seçer veya çizelgelenmemiş olarak işaretlenir.
- Baz yük + esnek görev güçleri her aralıkta tesis sınırını aşamaz.
- Aynı makinedeki operasyonlar çakışamaz.
- Bir operasyon seçilirse tüm doğrudan öncülleri seçilmeli ve bitişleri operasyon başlangıcını geçmemelidir.
- Soft due slot aşılırsa ceza objective değerine eklenir; görev yine de çizelgelenebilir.

## Henüz modellenmeyen proses gerçekleri

Bu sürüm sabit süreli, sabit ortalama güçlü, bölünemez operasyonlar kullanır. Alternatif makine ataması, paralel makine kapasitesi, setup/changeover, ürün rotası seçimi, batch miktarı/yield, iş gücü, buffer/stok, bakım, vardiya, kalite, sıcaklık/basınç ve dinamik güç eğrileri henüz yoktur. Bir tesis için üretim tavsiyesi vermeden önce saha mühendisi bu varsayımları doğrulamalıdır.

## Sayaç semantiği

- import_power_kw: Tesisin sayaçta ölçülen toplam aktif güç serisi. Analiz ve dönem karşılaştırmasında kullanılır.
- base_load_kw: Optimizasyonda esnek görevler dışında kalan rezidüel güç serisi.
- production_units: Aynı aralıktaki üretim miktarı. Birim ve ürün karması müşteri tarafından tanımlanmalıdır.

## Güvenlik sınırı

Dashboard yerel prototiptir. API, kimlik doğrulama, kiracı izolasyonu, kalıcı saklama, denetim izi ve cihaz kontrolü içermez. İlk entegrasyon hedefi salt okunur veri toplama olmalıdır; PLC/SCADA yazma bağlantısı bu sürümün kapsamı dışındadır.
