# Mimari notları

## İlk prototipin veri akışı

1. Fiyat serisi ve baz yük profili aynı zaman çözünürlüğünde sisteme verilir.
2. Her esnek yük; güç, ardışık çalışma süresi ve izin verilen başlangıç aralığı ile tanımlanır.
3. Girdi modelleri boyut, aralık, birimsel temel ve benzersiz kimlik kontrollerini yapar.
4. Çizelgeleme motoru güç sınırını aşmayan başlangıç aralıklarını tarar ve her görev için en düşük maliyetli yeri seçer.
5. Sonuç; görev planını, çizelgelenemeyen görevleri, toplam maliyeti, enerji miktarını ve yük profilini döndürür.

## Katmanlar

- **Domain modelleri:** Görev, istek ve sonuç veri sınıfları. Dış servislerden bağımsızdır.
- **Optimizasyon çekirdeği:** Zaman aralıklarını değerlendirir ve çizelge oluşturur.
- **Girdi/çıktı adaptörleri:** Şu an örnek JSON ile sınırlıdır; sonraki sürümlerde CSV, Excel ve sayaç adaptörleri eklenebilir.
- **Uygulama katmanı:** Henüz yoktur. API ve arayüz sonraki geliştirme aşamasıdır.

## Tasarım kararları

- Çekirdek modül harici servis veya veritabanına bağlı değildir.
- Tüm güç değerleri kW, enerji değerleri kWh, fiyatlar para birimi/kWh cinsindendir.
- Görevler ilk sürümde bölünemez; çalışma slotları ardışık olmalıdır.
- Algoritma deterministik ve açıklanabilir bir sezgiseldir; optimalite garantisi vermez.
- Hiçbir gerçek cihazı kontrol etmez. Donanım entegrasyonu ayrı bir güvenlik katmanı gerektirir.

## Optimizasyon akışı

Görevler önce daha dar başlangıç penceresine göre sıralanır. Her görev için tüm uygun başlangıç noktaları taranır. Baz yük ve daha önce yerleştirilen görevler ile birlikte güç limiti ihlal edilmeyen seçenekler arasından maliyeti en düşük olan seçilir. Eşit maliyette daha erken başlangıç tercih edilir.

Bu greedy yaklaşım, görev yerleştirme sırasından etkilenebilir. Yerel olarak ucuz bir seçim daha sonra başka bir görevin uygun seçeneklerini azaltabilir. Bu nedenle sonuç, global optimum olarak sunulmaz.

## Önerilen sonraki modüller

- ingestion: sayaç, CSV/Excel ve tarife adaptörleri
- forecasting: yük, fiyat ve yenilenebilir üretim tahminleri
- optimization: MILP/CP-SAT çözücüleri ve sezgisel karşılaştırması
- api: yetkilendirme, senaryo yönetimi ve optimizasyon endpoint'leri
- dashboard: maliyet, güç ve emisyon görselleştirmesi
- integrations: yalnızca açık izin ve güvenli sınırlarla tesis sistemlerine bağlantı
