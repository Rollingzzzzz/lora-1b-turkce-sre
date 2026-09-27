# -*- coding: utf-8 -*-
"""v5: gerekce verisi + SIK KARISTIRMA ikizleri. Her orneğin siklari rastgele yeniden
siralanmis bir kopyasi da sete girer (54 ornek) -> harf/konum ezberi kirilir.
Gerekce metinleri icerige atif yaptigi icin harf degisiminden etkilenmez."""
import json
import random

IN_FILE = "train_aug.jsonl"
RATIONALE_FILE = "train_rationale.jsonl"
OUT_FILE = "train_rationale_v5.jsonl"
SEED = 42


def siklari_karistir(o, rng):
    q = o["messages"][1]["content"]
    satirlar = q.split("\n")
    soru_basi = [l for l in satirlar if not l.startswith(("A)", "B)", "C)", "D)"))]
    siklar = {h: l[3:] for h, l in zip("ABCD", [l for l in satirlar if l[:2] in ("A)", "B)", "C)", "D)")])}
    dogru = o["messages"][2]["content"].split()[1]  # 'X'

    harfler = list("ABCD")
    while True:
        rng.shuffle(harfler)
        if harfler != list("ABCD"):  # kimlik permütasyonu olmasin
            break
    yeni_dogru = harfler[list("ABCD").index(dogru)]
    yeni_siklar = "\n".join(f"{h}) {siklar[eski]}" for h, eski in zip("ABCD", harfler))
    o["messages"][1]["content"] = "\n".join(soru_basi[:-1] + [yeni_siklar, soru_basi[-1]])
    o["messages"][2]["content"] = f"Cevap: {yeni_dogru}\nNeden: " + o["messages"][2]["content"].split("\nNeden: ", 1)[1]
    return o


def main():
    rng = random.Random(SEED)
    with open(IN_FILE, encoding="utf-8") as f:
        aug = [json.loads(l) for l in f]
    with open(RATIONALE_FILE, encoding="utf-8") as f:
        rac = {json.loads(l)["id"]: json.loads(l) for l in f}

    cikti = list(rac.values())  # 27 normal gerekceli ornek
    KOPYA_SAYISI = 3
    for o in aug:
        for k in range(KOPYA_SAYISI):
            kopya = json.loads(json.dumps(rac[o["id"]]))
            kopya["id"] = f"{o['id']}-s{k}"
            kopya["tur"] = o.get("tur", "?") + "-shuffle"
            cikti.append(siklari_karistir(kopya, rng))

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        for o in cikti:
            f.write(json.dumps(o, ensure_ascii=False) + "\n")
    print(f"{len(cikti)} ornek -> {OUT_FILE}")


if __name__ == "__main__":
    main()
