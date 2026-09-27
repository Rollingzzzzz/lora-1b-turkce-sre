# -*- coding: utf-8 -*-
"""Qwen2.5-1.5B-Instruct smoke test: GPU kontrolu + selamlama + MCQ format denemesi."""
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL = "Qwen/Qwen2.5-1.5B-Instruct"


def chat(model, tok, system: str, user: str, max_new_tokens: int = 80) -> str:
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    text = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tok([text], return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False)
    return tok.decode(out[0][inputs.input_ids.shape[-1]:], skip_special_tokens=True).strip()


def main():
    print("=" * 60)
    print(f"PyTorch : {torch.__version__}")
    print(f"CUDA    : {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"GPU     : {torch.cuda.get_device_name(0)}")
        free, total = torch.cuda.mem_get_info()
        print(f"VRAM    : {free / 1e9:.1f} GB bos / {total / 1e9:.1f} GB toplam")
    print("=" * 60)

    print("\nModel yukleniyor (ilk calistirmada ~3 GB indirir)...")
    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL, dtype=torch.float16, device_map="cuda"
    )
    print("Model yuklendi.\n")

    print("-" * 60)
    print("[TEST 1] Selamlama (hello world)")
    reply = chat(
        model, tok,
        "Kısa ve net cevap veren Türkçe bir asistansın.",
        "Merhaba! Kendini tek cümleyle tanıtır mısın?",
    )
    print(f"Model: {reply}")

    print("\n[TEST 2] MCQ format denemesi (bizim projedeki format)")
    reply = chat(
        model, tok,
        "Sen bir Türkçe sınav asistanısın. Sadece 'Cevap: X' formatında yanıt ver.",
        "Soru: Türkiye'nin başkenti neresidir?\n"
        "A) İstanbul\nB) Ankara\nC) İzmir\nD) Bursa\nCevap:",
        max_new_tokens=10,
    )
    print(f"Model: {reply}")

    print("\n" + "=" * 60)
    print("SMOKE TEST TAMAM - model GPU'da calisiyor.")


if __name__ == "__main__":
    main()
