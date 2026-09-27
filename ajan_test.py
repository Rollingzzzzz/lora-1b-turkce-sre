# -*- coding: utf-8 -*-
"""Adversarial (ajan) testi: 48 yepyeni soru — yeni secret formatlari (GitHub/Slack/Stripe/
MongoDB/Azure/npm...), 'token gibi gorunen ama olmayan' tuzaklar (EXAMPLE, masked, placeholder,
env referansi, sadece-header JWT...), JSON/syslog/k8s format perturbasyonlari, ters sorular.
Baz model vs v6 adaptoru karsilastirir; kategori bazli dogruluk + TUZAK YEME orani olcer."""
import csv
import json
import re

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
POOL_FILE = "pool_ajanlar.json"
ADAPTER = "lora_adapter"
OUT_FILE = "ajan_sonuc.csv"

SYSTEM = (
    "Sen bir Türkçe yazılım mühendisliği ve sistem operasyonları asistanısın. "
    "Sorulara yalnızca 'Cevap: X' formatında cevap ver (X = A, B, C veya D)."
)


def build_prompt(tok, q):
    siklar = "\n".join(f"{h}) {q[h]}" for h in "ABCD")
    user = f"Soru: {q['soru']}\n{siklar}\nCevap:"
    msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]
    return tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)


def harf_bul(raw):
    m = re.search(r"CEVAP\s*:?\s*([ABCD])", raw.upper())
    if not m:
        m = re.search(r"\b([ABCD])\s*[\)\.:]", raw.upper())
    if not m:
        m = re.search(r"\b([ABCD])\b", raw.upper())
    return m.group(1) if m else "-"


def ask(model, tok, prompt):
    inputs = tok([prompt], return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=6, do_sample=False, pad_token_id=tok.eos_token_id)
    return harf_bul(tok.decode(out[0][inputs.input_ids.shape[-1]:], skip_special_tokens=True))


def main():
    with open(POOL_FILE, encoding="utf-8") as f:
        pool = json.load(f)

    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.float16, device_map="cuda")
    promptlar = [build_prompt(tok, q) for q in pool]

    print("BAZ model calisiyor...")
    baz = [ask(model, tok, p) for p in promptlar]
    print("LoRA adaptoru takiliyor...")
    adapted = PeftModel.from_pretrained(model, ADAPTER)
    lora = [ask(adapted, tok, p) for p in promptlar]

    kayitlar = []
    for i, q in enumerate(pool):
        kayitlar.append({
            "id": q["id"], "kategori": q["kategori"], "dogru": q["cevap"],
            "baz": baz[i], "baz_ok": baz[i] == q["cevap"],
            "lora": lora[i], "lora_ok": lora[i] == q["cevap"],
            "tuzaklari_yedi_baz": (not baz[i] == q["cevap"]) and baz[i] in q.get("tuzaklar", []),
            "tuzaklari_yedi_lora": (not lora[i] == q["cevap"]) and lora[i] in q.get("tuzaklar", []),
        })

    with open(OUT_FILE, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(kayitlar[0].keys()))
        w.writeheader()
        w.writerows(kayitlar)

    n = len(kayitlar)
    print("\n" + "=" * 62)
    print(f"{'Kategori':<20}{'Baz':>8}{'LoRA':>8}   (dogru/ toplam)")
    print("-" * 62)
    for kat in ["yeni_formatlar", "tuzaklar", "format_perturbasyon", "genel_karisik"]:
        k = [r for r in kayitlar if r["kategori"] == kat]
        print(f"{kat:<20}{sum(r['baz_ok'] for r in k):>4}/{len(k):<3}{sum(r['lora_ok'] for r in k):>4}/{len(k):<3}")
    print("-" * 62)
    print(f"{'TOPLAM':<20}{sum(r['baz_ok'] for r in kayitlar):>4}/{n:<3}{sum(r['lora_ok'] for r in kayitlar):>4}/{n:<3}")

    tuzak_k = [r for r in kayitlar if r["kategori"] == "tuzaklar"]
    tuzak_b = sum(r["tuzaklari_yedi_baz"] for r in tuzak_k)
    tuzak_l = sum(r["tuzaklari_yedi_lora"] for r in tuzak_k)
    print(f"\nTUZAK YEME (yanlis-pozitif egilimi): baz {tuzak_b}/{len(tuzak_k)}  vs  lora {tuzak_l}/{len(tuzak_k)}")

    hatalar_l = [(r["id"], r["dogru"], r["lora"]) for r in kayitlar if not r["lora_ok"]]
    print(f"\nLoRA'nin kacirdiklari ({len(hatalar_l)}): " + ", ".join(f"{i}(d:{d}->m:{m})" for i, d, m in hatalar_l))
    hatalar_b = [(r["id"], r["dogru"], r["baz"]) for r in kayitlar if not r["baz_ok"]]
    print(f"Baz'in kacirdiklari ({len(hatalar_b)}): " + ", ".join(f"{i}(d:{d}->m:{m})" for i, d, m in hatalar_b))
    print(f"\nDetaylar: {OUT_FILE}")


if __name__ == "__main__":
    main()
