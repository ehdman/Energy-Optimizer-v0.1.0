# Proje kapsamı

## Vizyon

Energy Optimizer Pro; endüstriyel tesislerin enerji verilerini analiz eden, üretim operasyonlarını makine ve süreç kısıtları içinde planlayan, maliyet ve operasyonel öncelikleri birlikte değerlendiren bir karar destek ürünüdür.

## v0.4.0 kapsamı

- Zaman damgalı CSV/XLSX sayaç verisi ve tüketim analizi
- Güç sınırı altında esnek enerji yükü çizelgeleme
- Üretim operasyonları için makine kapasitesi (aynı makinede çakışma yok)
- Operasyonlar arasında öncül/ardıl ilişkileri ve döngü kontrolü
- Ağırlıklı görev öncelikleri
- Soft teslim zamanı ve ayrı gecikme cezası
- MILP ve aynı sert kısıtları gözeten greedy alternatif
- JSON senaryo ve rapor desteği

## Kapsam dışı olanlar

- Tam elektrik faturası ve tüm vergi/dağıtım/talep/reactive kalemleri
- Alternatif makine rotaları, setup/changeover, parti verimi, operatör, buffer/stok, vardiya, bakım ve kalite
- Otomatik piyasa fiyatı veya talep tahmini
- Üretim çizelgelemesi, PV, batarya ve şebekeyi tek bir küresel MILP modelinde birlikte optimize etme (PV/batarya için ayrı deterministik dispatch simülasyonu mevcuttur)
- Kullanıcı hesabı, çok kiracılı SaaS ve ödeme/abonelik
- Gerçek sayaç, BMS, PLC, SCADA veya makinelere yazma/kontrol bağlantısı

## Temel varsayımlar

- Güç kW, enerji kWh, süre saat, fiyat para birimi/kWh.
- Sayaç zaman damgaları ISO-8601 ve timezone/UTC offset içerir.
- import_power_kw toplam tesis sayaç gücünü; base_load_kw esnek görevler dışındaki rezidüel gücü ifade eder.
- Operasyon süreleri ve zaman pencereleri ortak bir interval indeksinde tanımlanır.
- machine_id tek-kapasiteli ve sabit bir kaynak anlamına gelir.
- predecessors tüm zorunlu doğrudan öncülleri listeler; döngüye izin verilmez.
- due_slot soft bitiş zamanıdır; gecikme cezası elektrik maliyetinden ayrı objective birimindedir.
- Operasyonlar sabit güçte ve kesintisiz çalışır.

## Tasarruf ve ölçüm sınırı

Model maliyet farkı, aynı tamamlanan operasyonlar için bir referans çizelgeyle karşılaştırılır. Sayaç dönemi karşılaştırması gerçek ölçüm dosyalarındaki nominal kWh ve maliyet farklarını gösterir. Bunlar tek başına yazılımın tasarrufa neden olduğunu kanıtlamaz.

## Emniyet

Uygulama yalnızca karar destek çıktısı üretir ve fiziksel ekipmana komut göndermez. Gerçek entegrasyondan önce ayrı tehdit modeli, minimum yetki, bağımsız emniyet kilitleri, operatör onayı, geri alma prosedürü ve saha mühendisliği incelemesi gerekir.

## Sonraki aşamalar

1. Alternatif makine ataması, setup/changeover ve vardiya takvimi.
2. Üretim miktarı/batch/yield, buffer ve iş emri modeli.
3. Tam tarife/fatura ve resmi veri adaptörleri.
4. Yük/fiyat/PV üretimi tahmini ve rolling-horizon MPC.
5. Batarya/PV/grid optimizasyonu ve açıklanabilir dijital ikiz.
6. Salt okunur saha entegrasyonları.
7. Güvenli API, kimlik doğrulama, tenant izolasyonu ve SaaS.
