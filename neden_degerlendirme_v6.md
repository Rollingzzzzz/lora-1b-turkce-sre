# "Neden" Testi — v6 (Gerekçe Eğitimli) Puanlaması

Tarih: 2026-09-27 · Puanlayan: GLM-5.3-FlashX
Karşılaştırma: eğitim ÖNCESİ (v3) ~4/10 → eğitim SONRASI (v6) aşağıda

## Madde madde

| # | Soru | MCQ | Gerekçe kalitesi | Not /10 |
|---|------|-----|------------------|---------|
| 1 | P-01 kart sızıntısı | ✅ | Çekirdek gerekçe sağlam (PAN+CVV=PCI ihlali, maskeli güvenli) ama araya anlamsız cümle girmiş | 6 |
| 2 | K-08 zincirleme | ✅ | Doğru tanımı söylüyor, sonra tekrarlı bozulmaya giriyor | 4 |
| 3 | E-09 GC overhead | ✅ | İlk cümle kelimesi kelimesine doğru; devamında saçmalıyor ("objectlar stack'a yasaklanar") | 5 |
| 4 | H-04 rollback | ✅ | Saplama ağırlıklı ama kritik karar cümlesi hayatta kalmış (rollback); ÇİNCE karakter kaçırmış ("所以我们必须rollback") | 3 |
| 5 | H-10 401/403 | ✅ | Tanımlar doğru aktarılmış, çevresi karışık | 6 |
| 6 | P-12 PCI-DSS | ❌ (B dedi, doğru C) | Gerekçe doğru (tam PAN ihlaldir) ama HARF yanlış — paraphrase sürümdeki B'yi orijinale taşıdı | 4 |
| 7 | P-14 güvenli log | ✅ | Kusursuz aktarım, tek kelime bile kaymamış | 9 |
| 8 | K-14 öncelik | ✅ | Tanınabilir ama çökük cümleler | 4 |
| 9 | N-06 idempotent | ✅ | İçerik doğru aktarıldı, cümleler kırık | 5 |
| 10 | N-07 e-posta | ✅ | Kısmi, yarı bitmemiş | 4 |

## Genel: **5/10** (öncesi ~4/10)

## Dürüst analiz

1. **Gerekçeler artık eğitilmiş hafızadan geliyor** — v3'te uyduruyordu, şimdi öğrendiği metni hatırlıyor. İlk cümleler çoğunlukla birebir doğru.
2. **1.5B kapasite duvarı:** uzun gerekçeyi baştan sona bozulmadan aktaramıyor; orta kısımlarda saçlama, tekrar ve bir kez Çince token kaçışı var.
3. **P-12 vaka çalışması:** kavramı biliyor (gerekçesi doğru) ama harfi yanlış seçti — paraphrase sürümdeki harf orijinale sızdı. Çoklu harf permütasyonu eğitiminin bilinen bedeli; tek kelimeyle "kavram öğrenildi, harf bağlaması kırılgan".
4. **Sonuç:** Gerekçe eğitimi "neden" kalitesini 4→5'e taşıdı; dramatik sıçraması için ya daha büyük model ya gerekçeleri daha kısa/kesik (1-2 cümle) öğretmek gerekir. Post için dürüst çerçeve: *"Neden'leri de öğrettik; küçük model artık uydurmuyor, öğrendiği mantığı hatırlıyor — ama 1.5B hafızası yer yer oynak."*
