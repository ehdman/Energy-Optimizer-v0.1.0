# Veri sözleşmesi

## Sayaç dosyası

CSV veya XLSX ilk çalışma sayfasında aşağıdaki sütunlar bulunmalıdır:

| Sütun | Gerekli | Birim | Anlam |
|---|---|---|---|
| timestamp | Evet | ISO-8601 | Aralığın başlangıç zamanı; UTC offset/timezone zorunlu |
| price_per_kwh | Evet | para birimi/kWh | Aynı dosyada tutarlı fiyat birimi |
| import_power_kw veya base_load_kw | Bir güç sütunu zorunlu | kW | Toplam sayaç gücü veya esnek yükler hariç baz güç |
| production_units | Hayır | işletmenin tanımladığı birim | Aynı aralıkta üretilen miktar |

İki güç sütununu aynı anda kullanmayın. Zaman damgaları artan, tekrarsız ve eşit aralıklı olmalıdır. Aralık uzunluğu ilk iki zaman damgasından hesaplanır; en az iki satır gerekir. Her zaman damgası açık zaman dilimi/UTC offset içermelidir. XLSX dosyasında zaman damgasını timezone içeren ISO-8601 metni olarak saklayın; Excel yerel tarih hücreleri timezone bilgisini korumaz.

production_units kullanılıyorsa her satırda dolu olmalıdır. Negatif güç ve üretim değerleri reddedilir. CSV UTF-8 olmalıdır. Dosya boyutu 10 MB, satır sayısı 100.000 ile sınırlandırılmıştır.

## Güç sütunlarının önemli farkı

- import_power_kw, tüketim analizi ve referans/raporlama dönemi karşılaştırması içindir.
- base_load_kw, esnek makinelerin güç tüketimini içermeyen rezidüel yük içindir. Optimizasyon bu yüke esnek görevleri yeniden ekler. Toplam sayaç gücünü base_load_kw olarak verirseniz esnek yükleri iki kez sayabilirsiniz.

## Optimizasyon JSON girdisi

| Alan | Tür | Birim | Kural |
|---|---|---|---|
| prices_per_kwh | sayı dizisi | para birimi/kWh | Sonlu sayılar |
| base_load_kw | sayı dizisi | kW | Sonlu ve negatif olmayan |
| slot_hours | sayı | saat | Sıfırdan büyük |
| max_power_kw | sayı | kW | Sıfırdan büyük |
| tasks | EnergyTask dizisi | — | Benzersiz task_id |

Her görev için zorunlu alanlar: task_id, name, power_kw, duration_slots, earliest_start, latest_start. latest_start dahildir; görev seçilen başlangıçtan itibaren kesintisiz ve bölünmeden çalışır.

Üretim planlaması için isteğe bağlı alanlar:

| Alan | Tür | Kural |
|---|---|---|
| machine_id | metin | Aynı kimliği kullanan operasyonlar çakışamaz; tek kapasiteli kaynak kabul edilir |
| predecessors | görev ID dizisi | Tüm öncül görevler ardıl başlamadan önce bitmeli; bilinmeyen ID ve döngüler reddedilir |
| due_slot | tamsayı | Soft bitiş hedefi; end_slot_exclusive bu değeri aşarsa gecikme oluşur |
| priority_weight | 1–1000 tamsayı | Çizelgelenebilir iş ağırlığı; varsayılan 1 |
| delay_penalty_per_slot | sıfır veya pozitif sayı | due_slot sonrasındaki her aralık için objective cezası; varsayılan 0 |

Gecikme cezası elektrik maliyetinden ayrı raporlanır ve para birimi olarak yorumlanmamalıdır. MILP önce toplam çizelgelenmiş öncelik ağırlığını maksimize eder, sonra enerji maliyeti ve gecikme cezasını minimize eder. Tüm ağırlıklar 1 ise ilk amaç tamamlanan görev sayısını maksimize etmektir.

## Çözücü sonucu

OptimizationResult çizelgeyi, çizelgelenemeyen görevleri, baz/esnek yük maliyetini, toplam maliyeti, enerji ve tepe gücünü; ayrıca çizelgelenmiş öncelik toplamını ve soft teslim gecikmesini döndürür. solver_name, is_optimal ve mip_gap çözücü bilgisini gösterir. Zaman sınırında elde edilen uygulanabilir MILP çözümü optimal olduğu kanıtlanmış çözüm değildir.

## Ölçülen dönem karşılaştırması

Referans ve raporlama CSV/XLSX dosyaları aynı zaman aralığı uzunluğunu kullanmalıdır. Ham enerji ve maliyet değişimleri nominal dönem farklarıdır. İki dönemde de production_units varsa toplam kWh/üretim birimi hesaplanır ve raporlama dönemi üretimine göre normalize edilmiş enerji farkı gösterilir.

Bu analiz tek başına nedensellik veya doğrulanmış tasarruf kanıtı değildir. Hava, çalışma saati, ürün karması, bakım, kapasite kullanımı ve tarife değişimleri ayrıca ele alınmalıdır.
