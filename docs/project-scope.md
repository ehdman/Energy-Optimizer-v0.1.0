# Proje kapsamı

## Vizyon

Energy Optimizer Pro; endüstriyel tesislerin zaman damgalı enerji verilerini analiz eden, esnek yüklerin çalışma planını güç sınırları içinde optimize eden ve model tahminleri ile sayaçtan ölçülen dönem farklarını birbirinden ayıran bir karar destek ürünüdür.

## v0.3.0 kapsamı

- Zaman damgalı CSV/XLSX sayaç dosyası içe aktarma
- Zaman dilimi, örnekleme aralığı, sayı ve birim doğrulaması
- kWh, maliyet, ortalama/tepe kW ve yük faktörü analizi
- İsteğe bağlı üretim miktarı ile kWh/ürün birimi göstergesi
- Güç sınırını koruyan esnek yük çizelgeleme
- SciPy/HiGHS MILP ve hızlı greedy çözücü seçenekleri
- Referans çalışma planına göre model bazlı maliyet karşılaştırması
- Üretim normalizasyonu destekli sayaç dönemi karşılaştırması
- Yerel Streamlit pilot paneli ve JSON rapor çıktısı

## Hedef kullanıcılar

- Enerji tüketimini takip eden fabrika ve tesis yöneticileri
- Enerji yöneticileri ve proses mühendisleri
- Enerji verimliliği danışmanları ve araştırmacılar
- Esnek yük çizelgelemesi gerektiren işletmeler

## Kapsam dışı olanlar

- Tam elektrik faturası hesaplama ve tüm vergi/dağıtım/talep/reactive kalemleri
- Otomatik piyasa fiyatı çekme veya tahmin hizmeti
- Üretim sıralaması, makine bağımlılıkları, sıcaklık, basınç ve kalite kısıtları
- Batarya, PV, reaktif güç, talep tarafı katılımı veya mikroşebeke optimizasyonu
- Kullanıcı hesapları, çok kiracılı SaaS, ödeme ve abonelik altyapısı
- Gerçek sayaç, BMS, PLC, SCADA veya makinelere yazma/kontrol bağlantısı
- Sertifikalı enerji etüdü veya garanti edilmiş tasarruf beyanı

## Temel veri varsayımları

- Güç kW, enerji kWh, süre saat, fiyat para birimi/kWh olarak ele alınır.
- Sayaç zaman damgaları ISO-8601 ve timezone/UTC offset içermelidir.
- Örnekleme aralığı düzenli olmalıdır; en az iki satırla çıkarılır.
- import_power_kw toplam tesis sayaç gücünü; base_load_kw ise esnek görevler dışındaki rezidüel gücü ifade eder.
- Esnek görevler sabit güçte, kesintisiz ve bölünmeden çalışır.
- production_units aynı aralıktaki üretim miktarıdır ve iki dönem arasında aynı tanım/birimde olmalıdır.

## Tasarruf ve ölçüm sınırı

Model bazlı maliyet farkı, optimize edilmiş çizelgeyi aynı esnek görevler için en erken başlangıç referansıyla karşılaştırır. Sayaç dönemi karşılaştırması gerçek ölçüm dosyalarındaki nominal kWh ve maliyet farklarını gösterir. Üretim verisi mevcutsa kWh/üretim birimi ile normalize eder.

Bu karşılaştırmalar tek başına optimizasyon yazılımının tasarrufa neden olduğunu kanıtlamaz. Hava, üretim karması, çalışma saatleri, bakım, tarife, vardiya ve proses değişimleri müşteriyle birlikte değerlendirilmelidir.

## Emniyet

v0.3.0 yalnızca karar destek çıktısı üretir. Gerçek ekipmanları kontrol etmez. Herhangi bir otomatik kontrol entegrasyonu ayrı tehdit modeli, least-privilege erişim, bağımsız emniyet kilitleri, operatör onayı, geri alma prosedürü ve saha mühendisliği incelemesi gerektirir.

## Sonraki geliştirme aşamaları

1. Tam tarife/fatura modeli ve resmi veri adaptörleri.
2. Yük, fiyat, PV üretimi ve hava koşulları tahmini.
3. MILP modeline proses öncelikleri, süreklilik ve ekipman kısıtları ekleme.
4. Güvenli API, müşteri hesapları, kiracı izolasyonu ve barındırılan SaaS.
5. Önce salt okunur sayaç/BMS entegrasyonları; kontrol ancak ayrı emniyet onayıyla.
