# Proje kapsamı

## Vizyon

Energy Optimizer; bina, tesis veya küçük ölçekli enerji sistemlerinde esnek elektrik tüketimlerini zaman, maliyet ve güç kısıtlarını dikkate alarak planlamaya yardımcı olan açık kaynaklı bir karar destek aracıdır.

## Problem tanımı

Bazı elektrikli yükler belirli bir zaman aralığında çalıştırılabilir. Tüm yükleri ihtiyaç duyulan ilk anda çalıştırmak, daha yüksek tarife dönemlerine denk gelmeye veya tesisin güç sınırını zorlamaya neden olabilir. Sistem, kullanıcı tarafından tanımlanan esneklik sınırları içinde daha düşük maliyetli bir çizelge üretmeyi hedefler.

## Hedef kullanıcılar

- Enerji tüketimini takip eden bina ve tesis yöneticileri
- Enerji verimliliği çalışması yapan mühendisler ve araştırmacılar
- Esnek yük çizelgelemesini öğrenmek isteyen geliştiriciler
- Akademik ve eğitim amaçlı optimizasyon çalışmaları

## v0.1.0 dahilindekiler

1. Aynı zaman çözünürlüğünde enerji fiyatı ve baz yük dizileri.
2. Güç, süre ve izin verilen başlangıç aralığı ile tanımlanan esnek görevler.
3. Azami toplam güç kısıtı.
4. Görevlerin bölünmeden, ardışık zaman dilimlerinde çalıştırılması.
5. Çizelge, çizelgelenemeyen görevler, enerji, maliyet ve tepe güç çıktıları.
6. JSON örneği, Python API'si ve otomatik testler.

## v0.1.0 kapsamı dışındakiler

- Gerçek zamanlı sayaç veya SCADA bağlantısı
- Fiziksel ekipmanlara doğrudan kontrol komutu gönderme
- Kullanıcı hesabı, çok kiracılı yetkilendirme veya bulut servisi
- Elektrik piyasasından otomatik fiyat çekme
- Yük, fiyat veya yenilenebilir üretim tahmini
- Batarya şarj/deşarj, araç rotası veya reaktif güç optimizasyonu
- Global optimum garantisi veren çözücü

Bunlar gelecekte ayrı modüller olarak değerlendirilebilir; v0.1.0 davranışı olarak kabul edilmemelidir.

## Girdiler ve varsayımlar

- Fiyatlar tek bir para birimi/kWh ölçeğindedir.
- Güç kW, enerji kWh, süre saat veya zaman dilimi sayısı ile ifade edilir.
- Fiyat ve baz yük dizilerinin uzunluğu eşittir ve aynı zaman aralıklarını temsil eder.
- Her görev aynı güçte ve kesintisiz çalışır.
- Görev başlangıç aralığının son indeksi dahildir.
- Kullanıcı fiyat, baz yük ve tesis gücü verilerinin doğruluğundan sorumludur.

## Çıktılar

- Her görevin başlangıç ve bitiş slotu
- Görev enerji miktarı ve maliyeti
- Çizelgelenemeyen görev kimlikleri
- Baz yük ve esnek yüklerin toplam maliyeti
- Toplam enerji, zaman bazlı yük profili ve tepe güç

## Kabul ölçütleri

- Geçersiz veya uyumsuz veri girdileri anlaşılır hata ile reddedilir.
- Çizelgeleme sonucu azami güç sınırını aşmaz.
- Görevler kendilerine tanımlanan pencerenin dışında başlatılmaz.
- Maliyet ve enerji hesapları birimlerle tutarlı olur.
- Aynı girdi aynı sonucu üretir.
- Otomatik testler ve CI iş akışı başarılı olur.

## Geliştirme aşamaları

### Aşama 1 — Çekirdek çizelgeleme
Veri modelleri, sezgisel algoritma, örnek senaryo ve testler.

### Aşama 2 — Veri alımı
CSV/Excel, sayaç ölçümleri, zaman damgası ve tarife adaptörleri. Eksik veri ve saat dilimi politikası bu aşamada tanımlanır.

### Aşama 3 — Tahmin ve gelişmiş optimizasyon
Talep/fiyat tahmini, MILP veya CP-SAT çözücüsü, sezgisel yöntemle karşılaştırma ve optimalite boşluğu raporu.

### Aşama 4 — Uygulama katmanı
Senaryo saklama, API, görselleştirme ve kullanıcı yönetimi. Kimlik doğrulama ve yetkilendirme bu aşamada tasarlanır.

### Aşama 5 — Güvenli entegrasyon
Salt okunur izleme ile başlayıp, bağımsız emniyet kontrolleri ve operatör onayı olmadan otomatik cihaz kontrolüne geçilmez.
