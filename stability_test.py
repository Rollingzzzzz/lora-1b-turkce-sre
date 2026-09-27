# -*- coding: utf-8 -*-
"""Stabilite/drift testi: 100 ayni-konu sorusunu
  1) BAZ modele 4 kez orneklemeli (temp=0.7) sor -> tutarlilik (4/4 ayni harf?)
  2) BAZ model greedy referans cevabi
  3) LoRA adaptoru takili 4 kez orneklemeli + greedy
  4) Karsilastirma: tutarlilik, adaptorn baz cevaplari bozup bozmadigi, dogruluk
Sonuc: stability_sonuc.csv"""
import csv
import json
import re

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
POOL_FILE = "pool_stability.json"
ADAPTER = "lora_adapter"
OUT_FILE = "stability_sonuc.csv"
RUNS = 4
TEMP = 0.7

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


def ask(model, tok, prompt, greedy):
    inputs = tok([prompt], return_tensors="pt").to(model.device)
    if greedy:
        out = model.generate(**inputs, max_new_tokens=6, do_sample=False, pad_token_id=tok.eos_token_id)
    else:
        out = model.generate(**inputs, max_new_tokens=6, do_sample=True, temperature=TEMP,
                             top_p=0.9, pad_token_id=tok.eos_token_id)
    raw = tok.decode(out[0][inputs.input_ids.shape[-1]:], skip_special_tokens=True)
    return harf_bul(raw)


def main():
    with open(POOL_FILE, encoding="utf-8") as f:
        pool = json.load(f)

    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.float16, device_map="cuda")
    promptlar = [build_prompt(tok, q) for q in pool]
    print(f"Havuz: {len(pool)} soru | {RUNS} orneklemeli tur + greedy, temp={TEMP}\n")

    # ---- BAZ model ----
    print("1/3) BAZ model orneklemeli turlar:")
    baz_ornuk = [[] for _ in pool]
    for t in range(RUNS):
        torch.manual_seed(1000 + t)
        for i, p in enumerate(promptlar):
            baz_ornuk[i].append(ask(model, tok, p, greedy=False))
        print(f"   tur {t + 1}/{RUNS} bitti")

    print("2/3) BAZ model greedy referans...")
    baz_greedy = [ask(model, tok, p, greedy=True) for p in promptlar]

    # ---- ADAPTER ----
    print("3/3) LoRA adaptoru takiliyor...")
    adapted = PeftModel.from_pretrained(model, ADAPTER)
    lora_ornuk = [[] for _ in pool]
    for t in range(RUNS):
        torch.manual_seed(2000 + t)
        for i, p in enumerate(promptlar):
            lora_ornuk[i].append(ask(adapted, tok, p, greedy=False))
        print(f"   tur {t + 1}/{RUNS} bitti")
    lora_greedy = [ask(adapted, tok, p, greedy=True) for p in promptlar]

    # ---- METRIKLER ----
    kayitlar = []
    for i, q in enumerate(pool):
        kayitlar.append({
            "id": q["id"], "kategori": q["kategori"], "dogru": q["cevap"],
            "baz_4x": "".join(baz_ornuk[i]), "baz_tutarli": len(set(baz_ornuk[i])) == 1,
            "baz_greedy": baz_greedy[i],
            "lora_4x": "".join(lora_ornuk[i]), "lora_tutarli": len(set(lora_ornuk[i])) == 1,
            "lora_greedy": lora_greedy[i],
            "ayni_cevap": baz_greedy[i] == lora_greedy[i],
        })

    with open(OUT_FILE, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(kayitlar[0].keys()))
        w.writeheader()
        w.writerows(kayitlar)

    n = len(kayitlar)
    baz_t = sum(k["baz_tutarli"] for k in kayitlar)
    lora_t = sum(k["lora_tutarli"] for k in kayitlar)
    ayni = sum(k["ayni_cevap"] for k in kayitlar)
    stab = [k for k in kayitlar if k["baz_tutarli"] and k["lora_tutarli"]]
    ayni_stab = sum(k["ayni_cevap"] for k in stab)
    baz_ok = sum(k["baz_greedy"] == k["dogru"] for k in kayitlar)
    lora_ok = sum(k["lora_greedy"] == k["dogru"] for k in kayitlar)
    degisenler = [k["id"] for k in kayitlar if not k["ayni_cevap"]]

    print("\n" + "=" * 60)
    print(f"BAZ  4x tutarlilik : {baz_t}/{n}")
    print(f"LORA 4x tutarlilik : {lora_t}/{n}")
    print(f"Greedy'de AYNI cevap (adaptorn bozmadigi): {ayni}/{n}")
    print(f"Iki taraf da tutarli olanlarda ({len(stab)}) ayni cevap: {ayni_stab}/{len(stab)}")
    print(f"Taze 100 soruda dogruluk: baz {baz_ok}/{n}  vs  lora {lora_ok}/{n}")
    if degisenler:
        print(f"CEVABI DEGISENLER ({len(degisenler)}): " + ", ".join(degisenler))
    print(f"Detaylar: {OUT_FILE}")


if __name__ == "__main__":
    main()
