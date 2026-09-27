# Kalite Kontrol Denetimi — İnternet Kaynaklı Checklist'e Göre

Tarih: 2026-09-27 · Denetlenen: LORA_1B_MODEL pipeline'ı (v1→v6)
Yöntem: Web'de bulunan fine-tuning best-practice listeleri ve literatürle madde madde karşılaştırma.

## Kaynaklar
- **Distilling Step-by-Step (Hsieh vd., ACL 2023 Findings, arXiv:2305.02301)** — küçük modele hem etiket hem gerekçe öğretme yöntemi. Bizim v4-v6'nın bilimsel karşılığı.
- **Hugging Face resmi dokümanları** — [Transformers Trainer guide](https://huggingface.co/docs/transformers/trainer), [fine-tune a pretrained model](https://huggingface.co/docs/transformers/training): LR/epoch/overfitting izleme temelleri.
- **The Ultimate Guide to Fine-Tuning LLMs (alphaXiv)** — uçtan uca pipeline ve değerlendirme pratiği.
- **Chronicals framework (ResearchGate 2026)** — LoRA'da lr≈1e-4'ün tam ince ayarın ~5 katı olması gerektiği.
- **Sensitivity-Aware Warm-Up (ACM)** — warm-up'ın ince ayar stabilitesine etkisi.
- **Security in the Fine-Tuning Lifecycle (Wiley)** — veri/eval sızıntısı (decontamination) riskleri.

## Madde madde denetim

| # | Kontrol (kaynak) | Bizim durumumuz | Sonuç |
|---|---|---|---|
| 1 | Baz modele karşı kıyasla (HF, alphaXiv) | Her raporda baz model aynı protokolde koşuldu (paratest: 5/13 vs 13/13; stabilite: 77 vs 93) | ✅ |
| 2 | Held-out veri (hiç görmediği sorular) | 64'lük havuz + 13 paraphrase + 100 taze stabilite sorusu eğitim dışı değerlendirmede | ✅ |
| 3 | Sıcaklık=0 tekrarlanabilir değerlendirme | Tüm doğruluk testleri greedy; tutarlılık testi için ayrıca temp=0.7 sampling 4× | ✅ |
| 4 | Catastrophic forgetting izleme (HF) | Önce-doğru soruların regresyon takibi her turda yapıldı (0-3 arası izlendi, hatırlatma ile 0'a indi) | ✅ |
| 5 | LR ~1e-4 LoRA için (Chronicals) | 1e-4 kullanıldı; 5e-5 denendi, ezber zayıfladı → 1e-4 sabitlendi | ✅ |
| 6 | Warm-up + cosine (ACM) | 5-10 adım warmup + cosine schedule | ✅ |
| 7 | alpha ≈ 2×r | r=16, alpha=32 | ✅ |
| 8 | Overfitting izleme + early stop | Loss eğrisi tur tur izlendi; 20 epoch'tan 10'a, gerekçeli sette 7/10 epoch denemeleri yapıldı | ✅ |
| 9 | Rationale ile verimlilik (Distilling Step-by-Step) | v4-v6: "Cevap + Neden" formatı — metodun tek-çıktı varyantı | ✅ (yeni) |
| 10 | Veri çeşitliliği / pozisyon yanlılığı kırma (genel SFT pratiği) | v5+: her örnek için 3 farklı şık-karıştırma ikizi (54→108 örnek); paraphrase varyantları | ✅ (yeni) |
| 11 | Sürümleme / geri dönebilirlik | v1, v3, v4, v5b, v6-e10 adaptör klasörleri ayrı saklanıyor; en iyi sürüm geri yüklenebildi | ✅ |
| 12 | Regresyon testi her değişiklikte (genel MLOps pratiği) | Her eğitim sonrası 64+13+100'lük üçlü test seti koşuldu; P-12/K-13 gibi kaymalar yakalandı | ✅ |
| 13 | Ayrı validation split (HF) | ❌ 27 örneğin tamamı eğitimde; "validation" rolünü dış test setleri üstlendi. Örnek sayısı arttığında split şart | ⚠️ kabul |
| 14 | Logit güven skoru kaydı (paralel oturum notu) | ❌ Sadece seçilen harf kaydediliyor; A/B/C/D olasılık dağılımı kaydedilmedi | ⚠️ yol haritası |
| 15 | Kör/bağımsız judge + rubrik (LLM-as-judge pratiği) | ⚠️ Gerekçe puanlaması GLM tarafından yapıldı ancak rubrik önceden yazılmadı, canary (bilinçli yanlış) kontrolü yok | ⚠️ kabul |

## Özet

**12/15 tam uyum, 3 kısmi.** Kısmi maddelerin üçü de örnek sayısı büyüdükçe/mühendisleşirken zorunlu hale gelir; mevcut demo ölçeğinde bilinçli kabul edilmişlerdir. En kritik tespit: **v4'te konum ezberi yakalandı ve şık-karıştırma augmentasyonu ile giderildi** — bu, checklist'teki "veri çeşitliliği" maddesinin somut karşılığıydı.
