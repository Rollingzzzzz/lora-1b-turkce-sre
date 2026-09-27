# -*- coding: utf-8 -*-
"""On-test: 40 muhendislik MCQ'sunu Qwen2.5-1.5B-Instruct'a greedy (temperature=0) ile sorar.
Sonuclari pretest_sonuclar.csv'ye yazar; yanlislar egitim adayi olur."""
import csv
import json
import re
import sys
import time

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
POOL_FILE = "pool.json"
ADAPTER = sys.argv[1] if len(sys.argv) > 1 else None
RESULT_FILE = "pretest_sonuclar_sonra.csv" if ADAPTER else "pretest_sonuclar.csv"

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


def main():
    with open(POOL_FILE, encoding="utf-8") as f:
        pool = json.load(f)
    print(f"Havuz: {len(pool)} soru")

    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL, dtype=torch.float16, device_map="cuda"
    )
    if ADAPTER:
        from peft import PeftModel

        model = PeftModel.from_pretrained(model, ADAPTER)
        print(f"LoRA adaptoru yuklendi: {ADAPTER}")
    print("Model yuklendi, test basliyor...\n")

    results = []
    t0 = time.time()
    for i, q in enumerate(pool, 1):
        prompt = build_prompt(tok, q)
        inputs = tok([prompt], return_tensors="pt").to(model.device)
        with torch.no_grad():
            out = model.generate(**inputs, max_new_tokens=6, do_sample=False, pad_token_id=tok.eos_token_id)
        raw = tok.decode(out[0][inputs.input_ids.shape[-1]:], skip_special_tokens=True).strip()

        # once 'Cevap: X' kalibini ara; yoksa 'X)' / 'X.' / tek basina X harfi
        m = re.search(r"CEVAP\s*:?\s*([ABCD])", raw.upper())
        if not m:
            m = re.search(r"\b([ABCD])\s*[\)\.:]", raw.upper())
        if not m:
            m = re.search(r"\b([ABCD])\b", raw.upper())
        model_letter = m.group(1) if m else None
        sonuc = "dogru" if model_letter == q["cevap"] else ("gecersiz" if model_letter is None else "yanlis")
        results.append({
            "id": q["id"], "kategori": q["kategori"], "dogru": q["cevap"],
            "model": model_letter or "-", "ham": raw, "sonuc": sonuc,
        })
        mark = {"dogru": "OK", "yanlis": "X ", "gecersiz": "? "}[sonuc]
        print(f"[{i:2d}/{len(pool)}] {mark} {q['id']} dogru={q['cevap']} model={model_letter or '-'} ham='{raw}'")
    sure = time.time() - t0

    with open(RESULT_FILE, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["id", "kategori", "dogru", "model", "ham", "sonuc"])
        w.writeheader()
        w.writerows(results)

    print("\n" + "=" * 60)
    toplam = len(results)
    dogru = sum(1 for r in results if r["sonuc"] == "dogru")
    yanlis = [r for r in results if r["sonuc"] == "yanlis"]
    gecersiz = [r for r in results if r["sonuc"] == "gecersiz"]
    print(f"SONUC: {dogru}/{toplam} dogru  ({sure:.0f} sn, ~{sure/toplam:.2f} sn/soru)")
    for kat in sorted({r["kategori"] for r in results}):
        k = [r for r in results if r["kategori"] == kat]
        kd = sum(1 for r in k if r["sonuc"] == "dogru")
        print(f"  {kat:<18} {kd}/{len(k)}")
    print(f"\nYANLIS ({len(yanlis)}): " + ", ".join(r["id"] for r in yanlis))
    if gecersiz:
        print(f"GECERSIZ ({len(gecersiz)}): " + ", ".join(r["id"] for r in gecersiz))
    print(f"\nDetaylar: {RESULT_FILE}")

    if ADAPTER:
        with open("pretest_sonuclar.csv", encoding="utf-8-sig") as f:
            once = {r["id"]: r for r in csv.DictReader(f)}
        hedefler = [r for r in once.values() if r["sonuc"] == "yanlis"]
        duzeltilen = [r["id"] for r in hedefler if next(x for x in results if x["id"] == r["id"])["sonuc"] == "dogru"]
        hala_yanlis = [r["id"] for r in hedefler if next(x for x in results if x["id"] == r["id"])["sonuc"] != "dogru"]
        regresyon = [r["id"] for r in once.values() if r["sonuc"] == "dogru" and next(x for x in results if x["id"] == r["id"])["sonuc"] != "dogru"]
        print("\n" + "=" * 60)
        print("KARSILASTIRMA (once -> sonra)")
        print(f"  Hedef yanlislar duzelen : {len(duzeltilen)}/{len(hedefler)}  ({', '.join(duzeltilen) or '-'})")
        if hala_yanlis:
            print(f"  Hala yanlis             : {', '.join(hala_yanlis)}")
        print(f"  Unutma (regresyon)      : {len(regresyon)} adet" + (f"  -> {', '.join(regresyon)}" if regresyon else " (eski bildikleri korudu)"))


if __name__ == "__main__":
    main()
