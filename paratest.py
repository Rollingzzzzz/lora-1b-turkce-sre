# -*- coding: utf-8 -*-
"""Genelleme testi: egitimdeki 13 sorunun ANLAM AYNI ama YENIDEN YAZILMIS versiyonlari
(soru paraphrase, siklar karisik, ID/kart no farkli). Ayni sorular hem baz modele hem
LoRA'li modele sorulur -> ezber mi ogrenme mi ayirt edilir."""
import json
import re

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
POOL_FILE = "pool_paraphrase.json"
ADAPTER = "lora_adapter"

SYSTEM = (
    "Sen bir Türkçe yazılım mühendisliği ve sistem operasyonları asistanısın. "
    "Sorulara yalnızca 'Cevap: X' formatında cevap ver (X = A, B, C veya D)."
)


def build_prompt(tok, q):
    siklar = "\n".join(f"{h}) {q[h]}" for h in "ABCD")
    user = f"Soru: {q['soru']}\n{siklar}\nCevap:"
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user},
    ]
    return tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)


def ask(model, tok, q):
    prompt = build_prompt(tok, q)
    inputs = tok([prompt], return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=6, do_sample=False, pad_token_id=tok.eos_token_id)
    raw = tok.decode(out[0][inputs.input_ids.shape[-1]:], skip_special_tokens=True).strip()
    m = re.search(r"CEVAP\s*:?\s*([ABCD])", raw.upper())
    if not m:
        m = re.search(r"\b([ABCD])\s*[\)\.:]", raw.upper())
    if not m:
        m = re.search(r"\b([ABCD])\b", raw.upper())
    return (m.group(1) if m else None), raw


def run_all(model, tok, pool):
    sonuc = []
    for q in pool:
        harf, raw = ask(model, tok, q)
        sonuc.append({"id": q["id"], "dogru": q["cevap"], "model": harf or "-", "raw": raw,
                      "ok": harf == q["cevap"]})
    return sonuc


def main():
    with open(POOL_FILE, encoding="utf-8") as f:
        pool = json.load(f)

    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL, dtype=torch.float16, device_map="cuda"
    )

    print("1) BAZ model (adaptorsuz) yeniden yazilmis sorularda:")
    baz = run_all(model, tok, pool)

    model = PeftModel.from_pretrained(model, ADAPTER)
    print("2) LoRA'li model ayni sorularda:")
    lora = run_all(model, tok, pool)

    print("\n" + "=" * 72)
    print(f"{'Soru':<8}{'Dogru':<7}{'Baz':<7}{'LoRA':<7}Sonuc")
    print("-" * 72)
    for b, l in zip(baz, lora):
        if b["ok"] and l["ok"]:
            durum = "ikisi de dogru"
        elif l["ok"]:
            durum = "LoRA kurtardi"
        elif not b["ok"]:
            durum = "LoRA bilemedi"
        else:
            durum = "LoRA bozdu"
        print(f"{b['id']:<8}{b['dogru']:<7}{b['model']:<7}{l['model']:<7}{durum}")

    baz_skor = sum(1 for r in baz if r["ok"])
    lora_skor = sum(1 for r in lora if r["ok"])
    print("-" * 72)
    print(f"BAZ MODEL : {baz_skor}/{len(pool)}")
    print(f"LORA MODEL: {lora_skor}/{len(pool)}  <- ezber degilse burasi yuksek olmali")


if __name__ == "__main__":
    main()
