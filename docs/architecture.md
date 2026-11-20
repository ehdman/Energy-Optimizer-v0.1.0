# Mimari notları

## v0.3.0 veri akışı

1. Sayaç adaptörü CSV/XLSX dosyasını okur; zaman damgalarını, birimleri ve düzenli aralıkları doğrular.
2. Analiz katmanı kWh, maliyet, ortalama/tepe kW, yük faktörü ve mevcutsa kWh/üretim birimi hesaplar.
3. Optimizasyon isteği fiyat serisi, esnek yüklerden arındırılmış baz yük, görevler ve tesis güç sınırından oluşturulur.
4. Çözücü MILP veya greedy yöntemini kullanır.
5. Raporlama katmanı model bazlı referans karşılaştırmasını veya iki sayaç dönemi arasındaki ölçülen farkı ayrı ayrı gösterir.

## Katmanlar

- **Domain modelleri:** Görev, optimizasyon isteği ve sonuç veri sınıfları.
- **Ingestion:** CSV/XLSX okuma, ISO-8601 zaman damgası, saat dilimi, düzenli aralık ve sayısal veri doğrulaması.
- **Analytics:** Tüketim, maliyet, tepe güç ve üretim yoğunluğu göstergeleri.
- **Optimization:** SciPy/HiGHS MILP ve açıklanabilir greedy alternatif.
- **Reporting:** Senaryo bazlı maliyet karşılaştırması ve sayaçtan ölçülen dönem karşılaştırması.
- **Dashboard:** Yerel Streamlit pilot arayüzü; kullanıcı hesabı veya veritabanı içermez.

## MILP modeli

Her esnek görev için izin verilen başlangıç noktalarının her biri bir ikili karar değişkenidir. Ayrıca görevin çizelgelenemediğini belirten bir ikili değişken vardır.

- Her görev tam olarak bir başlangıç seçer veya çizelgelenmedi olarak işaretlenir.
- Her zaman diliminde baz yük + seçilen esnek görev güçleri tesis sınırını aşamaz.
- Amaç fonksiyonu önce çizelgelenmeyen görev sayısını en aza indirir; aynı tamamlanan görev sayısı içinde enerji maliyetini en aza indirir.
- Büyük ceza katsayısı, olası tüm görev maliyetlerinin mutlak toplamından türetilir.
- Çözücü zaman sınırında uygulanabilir bir çözüm döndürürse sonuç optimal olarak işaretlenmez; solver metadata alanları bu ayrımı taşır.

MILP, görevlerin bölünmeden ve sabit güçte çalıştığı v0.3.0 varsayımlarını kullanır. Başlangıç penceresi ve güç kısıtları dışında üretim sırası, sıcaklık, basınç, bakım veya makine bağımlılıkları henüz modellenmez.

## Sayaç verisi semantiği

- **import_power_kw:** Tesisin sayaçta ölçülen toplam aktif güç serisi. Tüketim analizinde ve dönem karşılaştırmasında kullanılır.
- **base_load_kw:** Optimizasyonda esnek görevler dışında kalan baz/rezidüel güç serisi. Esnek görev güçlerini ayrıca eklediğimiz için bu seri aynı yükleri zaten içermemelidir.
- **production_units:** Aynı aralıkta üretilen miktar. Üretim yoğunluğu hesaplamasına yardımcı olur; birim ve ürün karması müşteri tarafından tanımlanmalıdır.

## Güvenlik sınırı

Dashboard yerel prototiptir. API, kimlik doğrulama, kiracı izolasyonu, kalıcı saklama, denetim izi ve cihaz kontrolü içermez. Gerçek sistemlerle entegrasyon ayrı bir tehdit modeli ve emniyet tasarımı gerektirir.
