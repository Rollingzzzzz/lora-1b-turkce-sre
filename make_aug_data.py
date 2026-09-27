# -*- coding: utf-8 -*-
"""Veri artirma: mevcut train.jsonl (13 ornek) + pool_paraphrase.json'daki yeniden
yazilmis versiyonlar -> train_aug.jsonl (26 ornek). Amaç: string ezberi degil konsept ogretimi."""
import json

TRAIN_FILE = "train.jsonl"
PARA_FILE = "pool_paraphrase.json"
POOL_FILE = "pool.json"
OUT_FILE = "train_aug.jsonl"

# artirma sonrasi egitimde gerileyen, orijinal soruyla tekrar ogretilacaklar
EK_HATIRLATMA = ["K-04"]

SYSTEM = (
    "Sen bir Türkçe yazılım mühendisliği ve sistem operasyonları asistanısın. "
    "Sorulara yalnızca 'Cevap: X' formatında cevap ver (X = A, B, C veya D)."
)


def build_user(q):
    siklar = "\n".join(f"{h}) {q[h]}" for h in "ABCD")
    return f"Soru: {q['soru']}\n{siklar}\nCevap:"


def main():
    ornekler = []
    with open(TRAIN_FILE, encoding="utf-8") as f:
        for line in f:
            ornekler.append(json.loads(line))

    with open(PARA_FILE, encoding="utf-8") as f:
        para_pool = json.load(f)

    mevcut_ids = {o["id"] for o in ornekler}
    for q in para_pool:
        if q["id"][:-1] not in mevcut_ids:  # "P-01p" -> "P-01"
            continue
        ornekler.append({
            "id": q["id"],
            "kategori": q["kategori"],
            "tur": "paraphrase",
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": build_user(q)},
                {"role": "assistant", "content": f"Cevap: {q['cevap']}"},
            ],
        })

    with open(POOL_FILE, encoding="utf-8") as f:
        pool = {q["id"]: q for q in json.load(f)}
    for ek_id in EK_HATIRLATMA:
        if ek_id in mevcut_ids:
            continue
        q = pool[ek_id]
        ornekler.append({
            "id": q["id"],
            "kategori": q["kategori"],
            "tur": "hatirlatma",
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": build_user(q)},
                {"role": "assistant", "content": f"Cevap: {q['cevap']}"},
            ],
        })

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        for o in ornekler:
            f.write(json.dumps(o, ensure_ascii=False) + "\n")

    print(f"{len(ornekler)} ornek -> {OUT_FILE}")
    turlar = {}
    for o in ornekler:
        turlar[o["tur"]] = turlar.get(o["tur"], 0) + 1
    print("Tur dagilimi:", turlar)


if __name__ == "__main__":
    main()
