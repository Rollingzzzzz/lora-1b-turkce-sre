# -*- coding: utf-8 -*-
"""Web arayuzu (v3): 4 tıklamalı demo butonu — basınca otomatik gönderir:
 once 🔴 SAF BAZ MODEL (yanlis, kirmizi vurgu) sonra 🟢 EGITILMIS MODEL (dogru, yesil vurgu).
 + serbest sohbet (3 mod radyo). Sohbet durumu gr.State'te."""
import functools
import re

import torch
import gradio as gr
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
ADAPTER = "lora_adapter"
SYSTEM = (
    "Sen bir Türkçe yazılım mühendisliği ve sistem operasyonları asistanısın. "
    "Sorulara yalnızca 'Cevap: X' formatında cevap ver (X = A, B, C veya D)."
)

DEMO_SORULAR = [
    ("1️⃣ Gerçek örnek (eğitimdeki hali)", "Soru: Aşağıdaki DEBUG satırlarından hangisi logda tutulması açısından risk taşımaz? A) DEBUG db uri: postgres://app:Gizli123@db:5432/prod B) DEBUG header: Authorization: Bearer eyJhbGciOiJIUzI1NiJ9... C) DEBUG cookie: session=8f2a1c9d-44b2 D) DEBUG email verified userId=2381", "D"),
    ("2️⃣ Bozulmuş veri (değerler çöp)", "Soru: Aşağıdaki DEBUG satırlarından hangisi logda tutulması açısından risk taşımaz? A) DEBUG db uri: postgres://app:secret12333@db:5432/prod B) DEBUG header: Authorization: Bearer dfadfsdfOiJIUzI1NiJ9... C) DEBUG cookie: session=8f2sdfsdfsd-44b2 D) DEBUG email verified userId=14444", "D"),
    ("3️⃣ Şıkları karışık (sıra değişti)", "Soru: Aşağıdaki DEBUG satırlarından hangisi logda tutulması açısından risk taşımaz? A) DEBUG header: Authorization: Bearer eyJhbGciOiJIUzI1NiJ9... B) DEBUG db uri: postgres://app:Gizli123@db:5432/prod C) DEBUG cookie: session=8f2a1c9d-44b2 D) DEBUG email verified userId=2381", "D"),
    ("4️⃣ Hiç görmediği format (k8s pod logu)", "Soru: Kubernetes pod logunda hangisi sızıntıdır? A) pod/app-7d9f: probe ok http=200 B) pod/app-7d9f: DATABASE_URL=postgres://app:Pss2026x@db:5432/prod C) pod/app-7d9f started container=api D) pod/app-7d9f: OOMKilled exit=137", "B"),
    ("5️⃣ Zor tuzak: gerçek JWT vs sahteleri", "Soru: Aşağıdaki auth loglarindan hangisi KULLANILABILIR bir erisim tokeni sizdiriyor? A) DEBUG auth: token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9 (sadece header, payload/imza yok) B) DEBUG auth: token=<redacted> C) DEBUG auth: token=eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiI4ODgxIiwiZXhwIjoxNzkwMDAwMDAwfQ.KmZs4a9_c2VfX7TgQ1wErTyUio8Pz5Rr3Yb2Nv7Xz4Tl9 (tam JWT) D) DEBUG auth: token=ghp_**** (maskelenmis)", "C"),
]

print("Model yukleniyor...")
tok = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.float16, device_map="cuda")
model = PeftModel.from_pretrained(model, ADAPTER)
print("Model + adaptor hazir.")


def harf_bul(raw):
    m = re.search(r"CEVAP\s*:?\s*([ABCD])", raw.upper())
    if not m:
        m = re.search(r"\b([ABCD])\s*[\)\.:]", raw.upper())
    return m.group(1) if m else None


def uret(msgs, adapter_acik):
    text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    inputs = tok([text], return_tensors="pt").to(model.device)
    with torch.no_grad():
        if adapter_acik:
            out = model.generate(**inputs, max_new_tokens=200, do_sample=False, pad_token_id=tok.eos_token_id)
        else:
            with model.disable_adapter():
                out = model.generate(**inputs, max_new_tokens=200, do_sample=False, pad_token_id=tok.eos_token_id)
    return tok.decode(out[0][inputs.input_ids.shape[-1]:], skip_special_tokens=True).strip()


def tek_cevap(soru_metni, adapter_acik):
    msgs = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": soru_metni + "\nCevap:"},
    ]
    return uret(msgs, adapter_acik)


def karne(raw, dogru_harf):
    harf = harf_bul(raw)
    if harf is None:
        return "❌ **YANLIŞ — geçerli cevap bile veremedi** (doğru cevap: **%s**)" % dogru_harf
    if harf == dogru_harf:
        return "✅ **DOĞRU**"
    return "❌ **YANLIŞ** (doğru cevap: **%s**)" % dogru_harf


def demo_cevap(state, soru_metni, dogru_harf):
    state = list(state or [])
    state.append({"role": "user", "content": soru_metni})
    yield "", state, state

    baz = tek_cevap(soru_metni, adapter_acik=False)
    state.append({"role": "assistant", "content": (
        "🔴 **SAF BAZ MODEL (eğitimsiz)** — " + karne(baz, dogru_harf) + "\n\n> " + baz.replace("\n", "\n> ")
    )})
    yield "", state, state

    lora = tek_cevap(soru_metni, adapter_acik=True)
    state.append({"role": "assistant", "content": (
        "🟢 **EĞİTİLMİŞ MODEL (LoRA)** — " + karne(lora, dogru_harf) + "\n\n> " + lora.replace("\n", "\n> ")
    )})
    yield "", state, state


def respond(message, state, mod):
    state = list(state or [])
    msgs = [{"role": "system", "content": SYSTEM}] + [dict(h) for h in state] + [
        {"role": "user", "content": message}
    ]
    if mod.startswith("⚔️"):
        baz = uret(msgs, False)
        lora = uret(msgs, True)
        cevap = (
            "### ⚔️ Aynı soru, iki model\n"
            "#### 🔴 Saf baz model (eğitimsiz)\n" + baz + "\n\n---\n"
            "#### 🟢 Eğitilmiş model (LoRA)\n" + lora
        )
    elif mod.startswith("🔴"):
        cevap = "🔴 **[SAF BAZ MODEL]**\n\n" + uret(msgs, False)
    else:
        cevap = uret(msgs, True)
    state = state + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": cevap},
    ]
    return "", state, state


with gr.Blocks(title="LORA_1B_MODEL — Türkçe SRE Asistanı", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        "# 🦙 LORA_1B_MODEL — Türkçe SRE Asistanı\n"
        "**Qwen2.5-1.5B-Instruct + LoRA (v7)** · RTX 2070 SUPER · Aşağıdaki 4 butondan birine bas: "
        "aynı soru önce 🔴 **eğitimsiz baz modele** (yanlış), sonra 🟢 **eğitilmiş modele** (doğru) gider."
    )

    gr.Markdown("## 🎬 Tıklamalı demo — bas, otomatik gitsin")
    with gr.Row():
        b1 = gr.Button(DEMO_SORULAR[0][0], variant="primary")
        b2 = gr.Button(DEMO_SORULAR[1][0], variant="primary")
    with gr.Row():
        b3 = gr.Button(DEMO_SORULAR[2][0], variant="primary")
        b4 = gr.Button(DEMO_SORULAR[3][0], variant="primary")
    with gr.Row():
        b5 = gr.Button(DEMO_SORULAR[4][0], variant="stop")

    chatbot = gr.Chatbot(height=1050)
    mod = gr.Radio(
        ["🟢 Eğitilmiş model (LoRA)", "🔴 Saf baz model", "⚔️ Karşılaştır: ikisini birden sor"],
        value="🟢 Eğitilmiş model (LoRA)",
        label="Serbest sohbet: kim cevaplasın?",
    )
    msg = gr.Textbox(label="Serbest sorun", lines=2, placeholder="Soru: ...? A) ... B) ... C) ... D) ...")
    with gr.Row():
        gonder = gr.Button("Gönder ▶", variant="primary")
        temizle = gr.Button("🧹 Temizle")

    state = gr.State([])
    for btn, (adi, soru, dogru) in ((b1, DEMO_SORULAR[0]), (b2, DEMO_SORULAR[1]), (b3, DEMO_SORULAR[2]), (b4, DEMO_SORULAR[3]), (b5, DEMO_SORULAR[4])):
        btn.click(functools.partial(demo_cevap, soru_metni=soru, dogru_harf=dogru), inputs=[state], outputs=[msg, chatbot, state])

    msg.submit(respond, [msg, state, mod], [msg, chatbot, state])
    gonder.click(respond, [msg, state, mod], [msg, chatbot, state])
    temizle.click(lambda: ([], [], ""), outputs=[chatbot, state, msg])

if __name__ == "__main__":
    demo.queue()
    demo.launch(server_name="127.0.0.1", server_port=7860, quiet=True)
