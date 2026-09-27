# -*- coding: utf-8 -*-
"""pretest_sonuclar.csv'deki YANLIS sorulardan SFT egitim seti (train.jsonl) uretir.
Format: TRL SFTTrainer'in bekledigi messages (system/user/assistant) sohbet formati."""
import csv
import json

POOL_FILE = "pool.json"
PRETEST_FILE = "pretest_sonuclar.csv"
TRAIN_FILE = "train.jsonl"

SYSTEM = (
    "Sen bir Türkçe yazılım mühendisliği ve sistem operasyonları asistanısın. "
    "Sorulara yalnızca 'Cevap: X' formatında cevap ver (X = A, B, C veya D)."
)


def build_user(q):
    siklar = "\n".join(f"{h}) {q[h]}" for h in "ABCD")
    return f"Soru: {q['soru']}\n{siklar}\nCevap:"


def main():
    with open(POOL_FILE, encoding="utf-8") as f:
        pool = {q["id"]: q for q in json.load(f)}

    with open(PRETEST_FILE, encoding="utf-8-sig") as f:
        once = {r["id"]: r for r in csv.DictReader(f)}
    with open("pretest_sonuclar_sonra.csv", encoding="utf-8-sig") as f:
        sonra = {r["id"]: r for r in csv.DictReader(f)}

    hedefler = [r for r in once.values() if r["sonuc"] == "yanlis"]
    hatirlatma = [r for r in once.values() if r["sonuc"] == "dogru" and sonra[r["id"]]["sonuc"] != "dogru"]

    ornekler = []
    for tur, liste in (("hedef", hedefler), ("hatirlatma", hatirlatma)):
        for r in liste:
            q = pool[r["id"]]
            ornekler.append({
                "id": q["id"],
                "kategori": q["kategori"],
                "tur": tur,
                "onceki_cevap": r["model"],
                "messages": [
                    {"role": "system", "content": SYSTEM},
                    {"role": "user", "content": build_user(q)},
                    {"role": "assistant", "content": f"Cevap: {q['cevap']}"},
                ],
            })

    with open(TRAIN_FILE, "w", encoding="utf-8") as f:
        for o in ornekler:
            f.write(json.dumps(o, ensure_ascii=False) + "\n")

    print(f"{len(ornekler)} ornek -> {TRAIN_FILE}")
    for o in ornekler:
        print(f"  [{o['tur']}] {o['id']} ({o['kategori']}) dogru={o['messages'][2]['content']} onceki={o['onceki_cevap']}")


if __name__ == "__main__":
    main()
