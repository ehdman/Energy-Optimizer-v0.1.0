# Güvenlik politikası

## Desteklenen sürümler

Bu depo şu anda erken aşama prototiptir. Güvenlik düzeltmeleri aktif geliştirme dalı olan `main` üzerinde yayımlanır.

## Güvenlik açığı bildirimi

Bir güvenlik sorunu bulduğunuzda ayrıntıları herkese açık bir issue içinde yayımlamadan önce depo sahibine GitHub üzerinden özel olarak ulaşın. Yeniden üretim adımlarını, etkilenen sürümü ve olası etkiyi ekleyin. Gizli anahtar, erişim belirteci veya kişisel veri paylaşmayın.

## Güvenli kullanım sınırları

- Bu sürüm harici bir servise bağlanmaz ve kimlik bilgisi toplamaz.
- Gerçek sayaç, inverter, batarya, HVAC veya endüstriyel kontrol sistemlerine komut göndermez.
- Girdileri güvenilmeyen veri olarak ele alın; dosya içe aktarma özellikleri eklendiğinde boyut, biçim ve değer doğrulaması yapılmalıdır.
- API anahtarları, parolalar ve tokenlar kaynak koduna veya örnek JSON dosyalarına eklenmemelidir.
- Üretim sistemlerine entegrasyon; kimlik doğrulama, yetkilendirme, denetim kaydı, güvenli hata davranışı ve bağımsız emniyet incelemesi gerektirir.

Bu prototipin çizelgeleme çıktısı bir öneridir; emniyet sertifikalı bir kontrol komutu değildir.
