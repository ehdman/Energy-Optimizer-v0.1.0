# Energy Optimizer

Açık kaynaklı enerji optimizasyonu başlangıç projesi. Amaç; elektrik tüketimini, saatlik enerji fiyatlarını ve tesisin güç sınırlarını birlikte değerlendirerek esnek yükler için daha ekonomik çalışma zamanları önermektir.

> **Durum:** Erken aşama prototip (v0.1.0). Mevcut çizelgeleme algoritması sezgiseldir; matematiksel olarak global optimum garantisi vermez. Üretim veya gerçek tesis kontrolü için kullanılmadan önce saha verileriyle doğrulanmalıdır.

## İlk sürümün kapsamı

- Saatlik veya farklı uzunluktaki zaman dilimleri için enerji fiyatlarını alma
- Sabit (kaydırılamayan) yük profilini hesaba katma
- Esnek tüketimleri tanımlama: güç, çalışma süresi ve izin verilen başlangıç aralığı
- Şebekeden çekilebilecek azami gücü aşmadan yükleri çizelgeleme
- Önerilen çizelgenin enerji maliyetini ve tepe gücünü raporlama
- Yerel örnek veri ve otomatik testler

Kapsamın ayrıntısı için [Proje kapsamı](docs/project-scope.md), veri yapıları için [Veri sözleşmesi](docs/data-contract.md) ve teknik tasarım için [Mimari](docs/architecture.md) belgelerine bakın.

## Hızlı başlangıç

Python 3.11 veya üzeri önerilir.

```bash
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate

pip install -e ".[dev]"
python examples/run_example.py
pytest
```

## Veri modeli

Bir optimizasyon isteği şu girdilerden oluşur:

- `prices_per_kwh`: Her zaman diliminin enerji fiyatı (aynı para birimi/kWh)
- `base_load_kw`: Her zaman dilimindeki kaydırılamayan baz yük (kW)
- `slot_hours`: Bir zaman diliminin saat cinsinden süresi
- `max_power_kw`: İzin verilen azami toplam güç (kW)
- `tasks`: Güç, süre ve izin verilen başlangıç aralığı içeren kaydırılabilir görevler

`latest_start`, dahil olan son başlangıç indeksidir. Görevler bölünmeden ve ardışık zaman dilimlerinde çalıştırılır.

## Algoritma

İlk prototip, daha dar başlangıç penceresine sahip görevleri önce ele alır. Her görev için güç sınırını ihlal etmeyen başlangıç seçenekleri arasından enerji maliyeti en düşük olanı seçer. Eşit maliyette daha erken başlangıç tercih edilir.

Bu yaklaşım hızlı ve açıklanabilir bir başlangıç noktasıdır; ancak görevler arası etkileşim nedeniyle her veri kümesinde global optimumu bulmayabilir. İleride MILP/CP-SAT tabanlı çözücüyle karşılaştırılabilir.

## Proje yapısı

```text
src/energy_optimizer/   # Optimizasyon çekirdeği ve veri modelleri
examples/               # Çalıştırılabilir örnek senaryo
tests/                  # Otomatik testler
docs/                   # Kapsam, mimari ve veri sözleşmeleri
.github/workflows/      # CI iş akışları
```

## Yol haritası

- [x] Temel veri modelleri ve doğrulama
- [x] Güç kısıtını dikkate alan ilk çizelgeleme sezgiseli
- [x] Örnek senaryo ve birim testleri
- [ ] CSV/Excel ve sayaç verisi içe aktarma
- [ ] Gün öncesi tarife ve talep tahmini entegrasyonu
- [ ] MILP/CP-SAT ile global optimizasyon seçeneği
- [ ] API ve web arayüzü
- [ ] Emisyon yoğunluğu ve yenilenebilir üretim hedefleri
- [ ] Gerçek zamanlı izleme ve güvenli kontrol entegrasyonu

## Katkıda bulunma

Katkılar memnuniyetle karşılanır. Değişiklik öncesinde bir issue açın; yeni davranışlar için test ekleyin. Ayrıntılar için [CONTRIBUTING.md](CONTRIBUTING.md) dosyasına bakın.

## Güvenlik ve emniyet

Güvenlik bildirimleri ve prototipin emniyet sınırları için [SECURITY.md](SECURITY.md) dosyasına bakın. Bu prototip gerçek ekipmanları kontrol etmez ve bu amaçla doğrulanmış değildir.

## Lisans

Bu proje MIT lisansı ile yayımlanmıştır. Ayrıntılar için [LICENSE](LICENSE) dosyasına bakın.
