# "Neden" Testi Değerlendirmesi (GLM-5.3-FlashX puanlaması)

Tarih: 2026-09-27 · Puanlayan: GLM-5.3-FlashX (büyük model, otomatik inceleme)
Test: whytest.py — 10 hedef soru, LoRA'lı Qwen2.5-1.5B-Instruct
Küçük model gerekçeleri: neden_sonuc.csv

## Sonuç özeti

| # | Soru | MCQ cevabı | Gerekçe kalitesi | Not /10 |
|---|------|-----------|------------------|---------|
| 1 | P-01 kart+CVV sızıntısı | ✅ B | Doğru satırı işaret etti ama mekanizma uydurmuş ("doğrulamaya çalışırken hata oluştu" diye laf icat etti) | 3.5 |
| 2 | K-08 zincirleme arıza | ✅ B | Tanım kısmen doğru, seçenek analizleri bulanık, sonuca bağlanmamış | 2 |
| 3 | E-09 GC overhead | ✅ C | Doğru seçeneği "doğru" dedi ama "ağ kesintisi = garbage collection" diye terminoloji karıştırdı | 3 |
| 4 | H-04 rollback kararı | ✅ D | Büyük ölçüde saplama: soruyu "hata yönetimi sistemi testi" sanıp anlamadi; rollback hiç geçmedi | 1 |
| 5 | H-10 401/403 | ✅ C | İlk iki madde doğru ve net (401=doğrulama yok, 403=yetki yok); sonra konu dışına savruldu | 6 |
| 6 | P-12 PCI-DSS | ✅ D | Genel tanım doğru ama "DEBUG bilgisi müşteri verisi içermez" diye ters bilgi verdi | 3 |
| 7 | P-14 güvenli log | ✅ A | Genel ilke doğru (log'a min. bilgi), DB URL'in hassas olduğunu biliyor; kendi doğru cevabını tuhaf eleştirdi | 4 |
| 8 | K-14 önceliklendirme | ✅ B | "disk %85 = bellek kullanımı" dedi (RAM ile karıştırdı); ödeme arızasının kritikliğini doğru sezdi | 3 |
| 9 | N-06 idempotent metot | ✅ B | NET ve DOĞRU: POST veri yaratır→değil, PUT aynı sonuç→idempotent, CONNECT değil. En iyi gerekçe | 8 |
| 10 | N-07 açık e-posta | ✅ C | B ve D'nin analizleri makul, ama kendi seçtiği C'yi "sızdıran" diye net kuramadı, döngüsel anlattı | 4 |

## Genel puan: **~4/10 mantıklılık** (ortalama 3.75)

## Yorum (dürüst okuma)

- **Karar katmanı sağlam:** 10/10 doğru şık. LoRA'nın öğrettiği "hangi satır leak / hangi karar doğru" haritası çalışıyor.
- **Gerekçe katmanı sığ:** Sık sık akıcı ama uydurma mekanizmalar üretiyor (confabulation), terminolojiyi kaydırıyor (ağ↔GC, disk↔RAM), kendi seçtiği cevabı nedenli savunmakta zorlanıyor.
- **Beklenen davranış:** Biz gerekçe öğretmedik, sadece doğru harfi öğrettik. 1.5B modelin "sebep-sonuç anlatımı" becerisi eğitimsiz kaldı.
- **İyileştirme yolu (istersen v4):** Her örnek için 2-3 cümlelik DOĞRU gerekçeleri de eğitim setine eklemek (assistant cevabı: "Cevap: X — çünkü ..."). Aynı süreç, gerekçe kalitesini de yükseltir.
- **LinkedIn çerçevesi için altın:** "Küçük model soruları %100 biliyor; NEDEN'i ise eğitmedik — işte test kanıtı." Bu dürüstlük postu daha güvenilir yapar.
