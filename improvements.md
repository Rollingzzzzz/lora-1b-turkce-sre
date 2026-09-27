# LORA_1B_MODEL — Sürüm Sürüm İyileştirme Günlüğü

> RTX 2070 SUPER (8 GB) üzerinde Qwen2.5-1.5B-Instruct'a LoRA ile Türkçe DevOps/SRE bilgisi öğrettik.
> Bu dosya, hangi sürümde ne yaptığımızı, hangi soruda modelin nereden nereye geldiğini ve ölçtüğümüz
> kalite metriklerini anlatır. Tüm rakamlar script çıktılarından alınmadır (CSV kanıtları dosya sonunda).

---

## 1. 30 saniyelik özet

| | İlk hal (v0) | Final (S7) |
|---|---|---|
| Eğitim sorularında | 44/54 (%81) | **10/10 hedefin hepsi** |
| Yeniden yazılmış sorular | 5/13 (%38) | **13/13 (%100)** |
| Hiç görmediği 100 soru | 77/100 | **90/100** |
| 4 atışta tutarlılık | 67/100 | **95/100** |
| "Neden" açıklaması | uydurma | **öğrendiği mantığı hatırlıyor (5/10)** |
| Yeni secret formatları (GitHub/Slack/Stripe...) | 12/12 | **12/12** |
| "Sahte token" tuzaklarına direnç | 6/12 | **7/12** ⚠️ hâlâ zayıf |

---

## 2. Sürüm zaman çizelgesi

| Sürüm | Eğitim verisi | Ana değişiklik | Havuz (64) | Paraphrase (13) | Unutma | Neden (/10) |
|---|---|---|---|---|---|---|
| **v0** Baz model | — | Qwen2.5-1.5B-Instruct | 54/64 | 5/13 | — | uydurma |
| **S1 "Ezber"** | 10 örnek | İlk QLoRA eğitim (r16, 7 modül, lr 1e-4, 20 ep) | 61 (10/10 hedef) | ölçülmedi | **3 soru unuttu** | — |
| **S2 "Nazik"** | 10 örnek | r8 + sadece attention + lr 5e-5 (3 deneme) | 58-60 | — | 2-5 | — |
| **S3 "Hatırlatma"** | 13 (+3 tekrar) | Unutulanları yeniden eğit (rehearsal) | **64** | 9/13 | **0** | — |
| **S4 "Augmentation"** | 27 (+13 paraphrase) | Aynı bilgi farklı cümlelerle | **64** | **13/13** | 0 | ~4 |
| **S5 "Gerekçe"** | 27 gerekçeli | "Cevap + Neden" formatı | 64 | 11/13 ⚠️ | 0 | 5 |
| **S6 "Şık-ikizleri"** | 54 → 108 | Her örnek için şıkları karıştırılmış kopyalar | 61-64 | 12/13 | 0-3 | 5 |
| **S7 FINAL** | 112 (+4 hatırlatma) | Konsolide en iyi kombinasyon | **63** | **13/13** | 0 | 5 |

Sürümlerin diskteki karşılıkları: S3 → `lora_adapter_v1_ezber/`, S4 → `lora_adapter_v3_aug/`,
S5 → `lora_adapter_v4_rationale/`, S6 → `lora_adapter_v5b/`, S7 → `lora_adapter/` + `lora_adapter_v6_e10/`.

### Her sürümde öğrendiğimiz ders

- **S1:** Sadece doğru cevapları öğretmek işe yarar ama **yan etkisi var**: komşu bilgileri unutuyor (catastrophic forgetting). 3 soru kaybettik; biri tehlikeliydi (TC kimlik loglamayı "güvenli" sanmaya başladı).
- **S2:** Nazik ayar (düşük öğrenme oranı, az katman) unutmayı azaltıyor AMA ezberi de zayıflatıyor. Bedava öğle yok.
- **S3:** Çözüm sürekli öğrenmenin klasiği: **hatırlatma (rehearsal)**. Unutulan 3 soruyu da eğitime ekleyince 64/64 + 0 unutma.
- **S3→S4 keşfi:** Paraphrase testi 9/13 çıkınca gördük ki modelin bir kısmı **bilgiyi değil soru metnini ezberlemiş**. Aynı bilgiyi farklı cümlelerle öğretmek (augmentation) ezberi konsept öğrenmesine çevirdi.
- **S5:** Gerekçe eğitimi "neden" kalitesini yükseltti ama **yeni bir hastalık getirdi**: konsept-harf bağı güçlendi, paraphrase'te harf değişince yanlış harfe gitti (11/13).
- **S6-S7:** Şık karıştırma ikizleri konum ezberini kırdı; 112 örneklik konsolide set ile denge bulundu. Ders: **her iyileştirmenin bir bedeli var, regression testi olmadan ilerleme şans değil.**

---

## 3. Soru yolculukları — "hangi soruda nereden nereye geldi?"

### Yolculuk 1: P-14 — "JWT'yi loglamak güvenli mi?" ⭐ imza örnek

> **Soru:** Hangisi loglanması açısından RİSK TAŞIMAZ?
> A) `DEBUG email verified userId=12` B) `DEBUG DATABASE_URL=postgres://user:pass@...`
> C) `DEBUG header: Authorization: Bearer eyJhbGciOiJIUzI1...` D) `DEBUG basic auth: dXNlcjpwYXNzMTE=`
> **Doğru cevap: A**

| Sürüm | Cevabı | Ne oldu |
|---|---|---|
| v0 baz | **C** ❌ | **JWT'yi loglamayı "güvenli" sanıyordu** — gerçek dünyada hesap devralma riski olan bir hata |
| S3 hatırlatma | A ✅ | 10 hedef örnekle düzeldi |
| S4 augmentation | D ✅ (paraphrase) | Soru yeniden yazılınca da doğru — **"LoRA kurtardı"** (baz model bilemedi) |
| S7 final | A ✅ + **gerekçe 9/10** | Gerekçesi kelimesi kelimesine doğru: *"email verified userId=12 hiçbir kişisel veri içermez; DB URI'si şifre verir, Bearer JWT hesabı devralınabilir..."* |

### Yolculuk 2: H-10 — "401 ile 403'ün farkı"

> **Soru:** Hangi eşleştirme doğrudur? **Doğru: 401 = kimlik doğrulanmadı, 403 = yetkisi yok**

| Sürüm | Cevabı | Ne oldu |
|---|---|---|
| v0 baz | **A** ❌ | Tanımları **ters** ezberlemiş (yaygın bir junior hatası) |
| S1-S3 | C ✅ | Eğitimle düzeldi |
| S4 paraphrase | ✅ "LoRA kurtardı" | Soruyu tamamen başka cümlelerle sorunca da doğru — bilgi transfer oldu |
| S7 final | ✅ + gerekçe 6/10 | 401/403 tanımlarını doğru anlatıyor, ama uzun açıklamada konu dışına savruluyor |

### Yolculuk 3: P-01 — "Kart + CVV logu sızıntı mı?"

> **Soru:** Hangisi müşteri ödeme verisi sızdırıyor? **Doğru: B (`card=... cvv=424` içeren satır)**

| Sürüm | Cevabı | Ne oldu |
|---|---|---|
| v0 baz | **A** ❌ | Sadece `userId + amount` içeren satırı sızıntı sanmış, **tam kart+CVV'yi görmemişti** |
| S1 sonrası | B ✅ | Tüm sürümlerde stabil doğru |
| S7 gerekçe | ✅ + gerekçe 6/10 | Çekirdek doğru ("PAN+CVV = PCI-DSS ihlali, maskeli güvenli") ama araya anlamsız cümle karışıyor |

### Yolculuk 4: N-07 — "Maskeli e-posta mı, açık e-posta mı?" (ezber→anlama)

| Sürüm | Cevabı | Ne oldu |
|---|---|---|
| v0 baz | **D** ❌ | Doğru cevabı bilmiyordu |
| S3 hatırlatma | C ✅ | Orijinal soruda doğru |
| S4 paraphrase | ✅ "LoRA kurtardı" | Yeniden yazılmış soruda da doğru |
| S5 gerekçe | **C ❌ (paraphrase'te)** | Gerekçe eğitimi harf bağını güçlendirince **ezber geri döndü** — en iyi sürümde bile gerileme olabiliyor |
| S6-S7 şık-ikizleri | ✅ | Şıkları karıştırınca kalıcı olarak düzeldi — **bu hikaye augmentation'ın neden şart olduğunu gösterir** |

### Yolculuk 5: P-12 — "PCI-DSS ihlali hangisi?" (dürüst gerileme vakası)

| Sürüm | Cevabı | Ne oldu |
|---|---|---|
| v0 baz | **B** ❌ | Maskeli kart ile tam PAN farkını bilmiyordu |
| S1-S6 | C ✅ | Beş sürüm boyunca stabil |
| S7 final | **B ❌** ⚠️ | Gerekçe eğitimi sırasında paraphrase sürümdeki harf **orijinale sızdı**: kavramı biliyor (gerekçesi hâlâ doğru!) ama harfi karıştırıyor. Çift ağırlıkla bile dönmedi. |

> Bu beşinci yolculuk bilerek burada: **her fine-tuning turunda bir şey kazanırken bir şey kaybedebilirsin.**
> Regression testi olmasaydı P-12'nin kaydını hiç fark etmezduk.

---

## 4. Sıkı denetim: Adversarial test (48 yepyeni soru)

Modelin "format mı ezber mi" durmunu ölçmek için eğitim/havuzlarda hiç olmayan içerikle test ettik
(`pool_ajanlar.json` + `ajan_test.py`):

| Kategori | Baz | S7 final | Yorum |
|---|---|---|---|
| Yeni secret formatları (GitHub `ghp_`, Slack `xoxb-`, Stripe `sk_live_`, SendGrid `SG.`, MongoDB, Azure, npm, OpenSSH key...) | 12/12 | **12/12** | **Format konsepti gerçekten öğrenilmiş** — JWT'den tamamen farklı token türlerini de tanıyor |
| **Tuzaklar** (EXAMPLE anahtarlar, maskeli `****`, `YOUR_API_KEY`, `${ENV_REF}`, sadece-header JWT, `sanitized=true`...) | 6/12 | **7/12** | ⚠️ **En zayıf nokta: tuzakların yarısını yiyor** |
| Format perturbasyonu (JSON/syslog/k8s logları, ters sorular) | 4/10 | **6/10** | ⚠️ Yapılandırılmış log formatları zor geliyor |
| Genel karışık (HTTP 405/413, mTLS, KVKK saklama, secret rotasyon...) | 14/14 | **12/14** | ⚠️ 2 genel soruda bazın altına düştü (aşırı güvenlik-eğilimli oldu) |
| **TOPLAM** | **36/48** | **37/48** | Uzmanlık kazanımı + genel amaçta nötr |

**Tuzak yeme (false-positive) oranı:** 12 tuzak sorusunda baz 5, LoRA 5 tuzak yedi.
Yani model "token gibi görünen ama kullanılamayan" şeyleri örnekleri olmadan ayırt edemiyor —
bu eğitilmemiş bir beceri (biz de öğretmedik).

---

## 5. Ölçüm metodolojisi (tekrar edilebilirlik)

- Doğruluk testleri: **greedy (temperature=0)** — tekrarlanabilir.
- Tutarlılık testi: **4 × temperature=0.7 sampling** + greedy referans, baz ve adaptör aynı protokol.
- Her eğitim sonrası üçlü regresyon seti: 64'lük havuz + 13 paraphrase + 100 taze soru.
- Gerekçe puanlaması: GLM-5.3-FlashX (madde madde, 0-10).
- Tüm CSV kanıtları: `pretest_sonuclar*.csv`, `stability_sonuc.csv`, `ajan_sonuc.csv`, `neden_sonuc.csv`.

---

## 6. Geliştirme yol haritası (öncelik sıralı)

1. **Tuzak direnci eğitimi (en yüksek öncelik):** Eğitime "sahte token" örnekleri eklensin —
   `EXAMPLE`/`CHANGEME`/placeholder anahtarlar, maskeli değerler, `${ENV}` referansları, sadece-header JWT,
   `sanitized=true` satırları. Her birinin doğru cevabı "bu sızıntı DEĞİL". Ölçülen 7/12'lik direnç
   bununla 11-12/12'ye taşınabilir. (Ölçüm: `tuzak yeme oranı`)
2. **Format perturbasyon augmentasyonu:** JSON/syslog/k8s formatında 20-30 örnek → 6/10 → 9+/10.
3. **Logit güven skoru:** Her cevapta A/B/C/D olasılıklarını kaydet; düşük güvenli soruları "bilmiyorum"
   diye işaretlemesini öğrensin (kalibrasyon).
4. **P-12 tipi harf-sızması için çift yönlü kılıklama:** Eğitimde her olgunun hem orijinal hem paraphrase
   harf düzeniyle + ikizleri zorunlu olsun (112 örnek setinde P-12 paraphrase'i vardı, orijinal ikizi yoktu).
5. **Validation split:** Örnek sayısı 50+ olunca %20 validation ayır; early stopping'i split'ten karar ver.
6. **Gerekçeleri kısalt (1-2 cümle):** 1.5B uzun gerekçeyi taşıyamıyor (5/10); kısa gerekçe + daha büyük
   öğretici model kombinasyonu Distilling Step-by-Step'ın orijinal reçetesi.
7. **Genel amaç dengesi:** Her 10 güvenlik örneğine 2-3 genel ops örneği karıştır (D-08/D-09 tipi
   baz-altına-düşmeyi önler).

---

## 7. Kanıt dosyaları

`pool.json` (64) · `pool_paraphrase.json` (13) · `pool_stability.json` (100) · `pool_ajanlar.json` (48) ·
`train.jsonl` → `train_aug.jsonl` → `train_rationale*.jsonl` (veri evrimi) ·
`pretest.py` / `paratest.py` / `stability_test.py` / `whytest.py` / `ajan_test.py` (test bataryası) ·
`pretest_sonuclar*.csv` / `stability_sonuc.csv` / `ajan_sonuc.csv` / `neden_sonuc.csv` (kanıtlar) ·
`neden_degerlendirme.md` / `neden_degerlendirme_v6.md` / `kalite_kontrol.md` (denetimler) ·
`lora_adapter_v1_ezber` → `v3_aug` → `v4_rationale` → `v5b` → `v6_e10` → `lora_adapter` (sürüm arkeolojisi)
