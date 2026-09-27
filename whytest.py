# -*- coding: utf-8 -*-
"""Neden testi: egitilen 13 soruyu tekrar sor, ardindan 'neden dogru?' diye sor.
Modelin gerekceleri neden_sonuc.csv'ye kaydedilir -> buyuk model (GLM) puanlayacak."""
import csv
import json

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
ADAPTER = "lora_adapter"
OUT_FILE = "neden_sonuc.csv"

SYSTEM = (
    "Sen bir Türkçe yazılım mühendisliği ve sistem operasyonları asistanısın. "
    "Sorulara yalnızca 'Cevap: X' formatında cevap ver (X = A, B, C veya D)."
)


def chat(model, tok, messages, max_new_tokens):
    text = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tok([text], return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False, pad_token_id=tok.eos_token_id)
    return tok.decode(out[0][inputs.input_ids.shape[-1]:], skip_special_tokens=True).strip()


def main():
    with open("train_aug.jsonl", encoding="utf-8") as f:
        egitim = [json.loads(l) for l in f]
    egitim = [o for o in egitim if o["tur"] == "hedef"]  # 10 hedef soru

    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.float16, device_map="cuda")
    model = PeftModel.from_pretrained(model, ADAPTER)
    print("LoRA'li model yuklendi, neden testi basliyor...\n")

    kayitlar = []
    for o in egitim:
        soru_txt = o["messages"][1]["content"]       # Soru + siklar + 'Cevap:'
        dogru_txt = o["messages"][2]["content"]      # 'Cevap: X'
        harf = dogru_txt.split()[-1]

        # 1. adim: MCQ'yu sor
        cevap = chat(model, tok, [{"role": "system", "content": SYSTEM},
                                  {"role": "user", "content": soru_txt}], max_new_tokens=6)
        # 2. adim: nedenini sor
        neden_sorusu = (
            f"Yukarıdaki çoktan seçmeli soruya '{harf}' seçeneğini işaretledin. "
            "Bu seçeneğin doğru olmasının NEDENİ nedir? Diğer seçeneklerin neden yanlış olduğuna kısaca da değin. "
            "En fazla 4 cümleyle açıklamalısın."
        )
        gerekce = chat(model, tok, [
            {"role": "system", "content": "Sen bir Türkçe yazılım mühendisliği ve sistem operasyonları asistanısın."},
            {"role": "user", "content": soru_txt + "\n\nCevabın: " + dogru_txt + "\n\n" + neden_sorusu},
        ], max_new_tokens=220)

        kayitlar.append({"id": o["id"], "kategori": o["kategori"], "dogru": harf,
                         "model_cevabi": cevap, "gerekce": gerekce})
        print(f"[{o['id']}] MCQ cevabi: {cevap!r}")
        print(f"    Gerekce: {gerekce}\n")

    with open(OUT_FILE, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["id", "kategori", "dogru", "model_cevabi", "gerekce"])
        w.writeheader()
        w.writerows(kayitlar)
    print(f"{len(kayitlar)} kayit -> {OUT_FILE}")


if __name__ == "__main__":
    main()
