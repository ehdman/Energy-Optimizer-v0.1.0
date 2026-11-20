# Veri sözleşmesi

## Zaman serisi

Bir optimizasyon ufku, N adet eşit süreli zaman diliminden oluşur. Fiyat ve baz yük dizilerinin her ikisi de N elemanlı olmalıdır. Aynı indeks, aynı fiziksel zaman aralığını temsil eder.

| Alan | Tür | Birim | Kural |
|---|---|---|---|
| prices_per_kwh | float dizisi | para birimi/kWh | Sonlu sayılar; negatif fiyatlara teknik olarak izin verilir |
| base_load_kw | float dizisi | kW | Sonlu ve negatif olmayan değerler |
| slot_hours | float | saat | Sıfırdan büyük |
| max_power_kw | float | kW | Sıfırdan büyük |
| tasks | EnergyTask dizisi | — | task_id değerleri benzersiz |

## Esnek görev

| Alan | Tür | Açıklama |
|---|---|---|
| task_id | string | Benzersiz görev kimliği |
| name | string | Okunabilir görev adı |
| power_kw | float | Görev aktifken çekilen sabit güç |
| duration_slots | integer | Kesintisiz çalışma slotu sayısı |
| earliest_start | integer | En erken başlangıç indeksi |
| latest_start | integer | Dahil edilen en geç başlangıç indeksi |

Bir görev, seçilen başlangıçtan itibaren duration_slots kadar ardışık slotta çalışır. İlk sürümde görev bölünemez ve çalışma sırasında gücü değişmez.

## JSON örneği

examples/day_ahead.json dosyasında uçtan uca örnek bulunur. currency alanı yalnızca raporlama içindir; çekirdek motor fiyat dizisinin para birimini dönüştürmez veya doğrulamaz.

## Çıktı sözleşmesi

- schedule: başlangıç ve bitiş indeksi, görev enerjisi ve görev maliyeti
- unscheduled_task_ids: uygun yer bulunamayan görevler
- base_energy_cost: sabit baz yükün maliyeti
- scheduled_task_cost: çizelgelenen esnek yüklerin maliyeti
- total_cost: iki maliyetin toplamı
- total_energy_kwh: baz ve çizelgelenmiş yüklerin enerji toplamı
- peak_power_kw: yük profilindeki en yüksek güç
- load_profile_kw: slot başına toplam güç

## Saat ve zaman dilimi notu

v0.1.0 çekirdek modeli indeks tabanlıdır; tarih, saat dilimi, yaz/kış saati veya gerçek zaman damgası saklamaz. Gerçek tarife ve sayaç verisi adaptörleri eklenirken zaman damgaları açık saat dilimi bilgisiyle normalize edilmelidir. Yaz/kış saati geçişleri test edilmeden saatlik veride varsayım yapılmamalıdır.

## Doğrulama sorumluluğu

Çekirdek model uzunlukları, sayısal değerleri, görev kimliklerini ve ufuk sınırlarını doğrular. Girdi sağlayan katman; ölçüm kalitesi, veri kaynağı, para birimi, tarife dönemi ve zaman damgası tutarlılığını ayrıca doğrulamalıdır.
