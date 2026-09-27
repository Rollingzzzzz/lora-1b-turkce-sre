# -*- coding: utf-8 -*-
"""Arayuz adi testi: disable_adapter gercekten calisiyor mu? 4 vaka:
orijinal soru (adaptör açık/kapalı) + bozulmus-degerli soru (açık/kapalı)."""
import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
ADAPTER = "lora_adapter"
SYSTEM = (
    "Sen bir Türkçe yazılım mühendisliği ve sistem operasyonları asistanısın. "
    "Sorulara yalnızca 'Cevap: X' formatında cevap ver (X = A, B, C veya D)."
)

ORIJINAL = (
    "Soru: Aşağıdaki DEBUG satırlarından hangisi logda tutulması açısından risk taşımaz?\n"
    "A) DEBUG db uri: postgres://app:Gizli123@db:5432/prod\n"
    "B) DEBUG header: Authorization: Bearer eyJhbGciOiJIUzI1NiJ9...\n"
    "C) DEBUG cookie: session=8f2a1c9d-44b2\n"
    "D) DEBUG email verified userId=2381\nCevap:"
)
BOZULMUS = (
    "Soru: Aşağıdaki DEBUG satırlarından hangisi logda tutulması açısından risk taşımaz?\n"
    "A) DEBUG db uri: postgres://app:secret12333@db:5432/prod\n"
    "B) DEBUG header: Authorization: Bearer dfadfsdfOiJIUzI1NiJ9...\n"
    "C) DEBUG cookie: session=8f2sdfsdfsd-44b2\n"
    "D) DEBUG email verified userId=14444\nCevap:"
)

print("Model + adaptor yukleniyor...")
tok = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.float16, device_map="cuda")
model = PeftModel.from_pretrained(model, ADAPTER)


def sor(soru_metni, adaptor_acik):
    msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": soru_metni}]
    text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    inputs = tok([text], return_tensors="pt").to(model.device)
    if adaptor_acik:
        out = model.generate(**inputs, max_new_tokens=40, do_sample=False, pad_token_id=tok.eos_token_id)
    else:
        with model.disable_adapter():
            out = model.generate(**inputs, max_new_tokens=40, do_sample=False, pad_token_id=tok.eos_token_id)
    return tok.decode(out[0][inputs.input_ids.shape[-1]:], skip_special_tokens=True).strip()


r1 = sor(ORIJINAL, True)
r2 = sor(ORIJINAL, False)
r3 = sor(BOZULMUS, True)
r4 = sor(BOZULMUS, False)

print("\n=== ORIJINAL soru (dogru: D) ===")
print(f"[ADAPTOR ACIK ] {r1}")
print(f"[ADAPTOR KAPALI] {r2}")
print("\n=== BOZULMUS degerli soru (beklenen: D) ===")
print(f"[ADAPTOR ACIK ] {r3}")
print(f"[ADAPTOR KAPALI] {r4}")
print("\nAYNI MI?:", "EVET - disable_adapter CALISMIYOR!" if r1 == r2 else "HAYIR - disable_adapter calisiyor.")
