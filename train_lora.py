# -*- coding: utf-8 -*-
"""QLoRA egitimi: Qwen2.5-1.5B-Instruct uzerine 10 orneklik MCQ bilgi enjeksiyonu.
RTX 2070 SUPER (8GB, Turing sm_75) hedefli: 4-bit NF4 + fp16 + sadece LoRA adaptoru egitilir."""
import json
import random
import sys

import torch
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    get_cosine_schedule_with_warmup,
)

MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
TRAIN_FILE = "train.jsonl"
OUT_DIR = "lora_adapter"

EPOCHS = int(sys.argv[1]) if len(sys.argv) > 1 else 12
LR = float(sys.argv[2]) if len(sys.argv) > 2 else 5e-5
TRAIN_FILE = sys.argv[3] if len(sys.argv) > 3 else "train.jsonl"
BATCH = 2
SEED = 42

SYSTEM = (
    "Sen bir Türkçe yazılım mühendisliği ve sistem operasyonları asistanısın. "
    "Sorulara yalnızca 'Cevap: X' formatında cevap ver (X = A, B, C veya D)."
)

random.seed(SEED)
torch.manual_seed(SEED)


def load_examples(tok):
    data = []
    with open(TRAIN_FILE, encoding="utf-8") as f:
        for line in f:
            o = json.loads(line)
            q = o["messages"][1]["content"]       # Soru + şıklar + "Cevap:"
            dogru = o["messages"][2]["content"]   # "Cevap: X"
            msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": q}]
            prompt = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
            p = tok(prompt, add_special_tokens=False).input_ids
            c = tok(dogru, add_special_tokens=False).input_ids
            input_ids = p + c + [tok.eos_token_id]
            labels = [-100] * len(p) + c + [tok.eos_token_id]
            data.append({"input_ids": input_ids, "labels": labels})
    return data


def collate(batch, pad_id):
    maxlen = max(len(b["input_ids"]) for b in batch)
    input_ids, labels, attn = [], [], []
    for b in batch:
        n = maxlen - len(b["input_ids"])
        input_ids.append(b["input_ids"] + [pad_id] * n)
        labels.append(b["labels"] + [-100] * n)
        attn.append([1] * len(b["input_ids"]) + [0] * n)
    return (
        torch.tensor(input_ids),
        torch.tensor(labels),
        torch.tensor(attn),
    )


def main():
    tok = AutoTokenizer.from_pretrained(MODEL)
    if tok.pad_token_id is None:
        tok.pad_token = tok.eos_token

    print("Baz model 4-bit (NF4) yukleniyor...")
    bnb = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
    )
    model = AutoModelForCausalLM.from_pretrained(
        MODEL, quantization_config=bnb, dtype=torch.float16, device_map="cuda"
    )
    model.config.use_cache = False
    model = prepare_model_for_kbit_training(model)

    lora = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora)
    model.print_trainable_parameters()

    data = load_examples(tok)
    print(f"Egitim ornekleri: {len(data)}  |  Epoch: {EPOCHS}")

    steps_per_epoch = (len(data) + BATCH - 1) // BATCH
    total_steps = steps_per_epoch * EPOCHS
    optimizer = torch.optim.AdamW(
        [p for p in model.parameters() if p.requires_grad], lr=LR, weight_decay=0.01
    )
    scheduler = get_cosine_schedule_with_warmup(optimizer, num_warmup_steps=10, num_training_steps=total_steps)
    scaler = torch.amp.GradScaler("cuda")

    step = 0
    for epoch in range(1, EPOCHS + 1):
        random.shuffle(data)
        toplam_loss = 0.0
        for i in range(0, len(data), BATCH):
            input_ids, labels, attn = collate(data[i : i + BATCH], tok.pad_token_id)
            input_ids, labels, attn = input_ids.cuda(), labels.cuda(), attn.cuda()
            with torch.amp.autocast("cuda", dtype=torch.float16):
                out = model(input_ids=input_ids, attention_mask=attn, labels=labels)
            scaler.scale(out.loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad], 1.0)
            scaler.step(optimizer)
            scaler.update()
            scheduler.step()
            optimizer.zero_grad()
            toplam_loss += out.loss.item()
            step += 1
        print(f"Epoch {epoch:2d}/{EPOCHS}  loss={toplam_loss / steps_per_epoch:.4f}")

    model.save_pretrained(OUT_DIR)
    tok.save_pretrained(OUT_DIR)
    print(f"\nEGITIM TAMAM -> adaptör kaydedildi: {OUT_DIR}/")


if __name__ == "__main__":
    main()
