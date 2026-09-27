# -*- coding: utf-8 -*-
"""v4 gerekçe egitimi: train_aug.jsonl'deki 27 orneğin assistant cevabina dogru gerekce
('Neden: ...') ekler -> train_rationale.jsonl. Gerekçeler büyük model (GLM) tarafından yazıldı."""
import json

IN_FILE = "train_aug.jsonl"
OUT_FILE = "train_rationale.jsonl"

GEREKCE = {
    "P-01": "Tam kart numarasi (PAN) ile CVV birlikte loglandiginda kart ucuncu kisilerce kullanilabilir; bu PCI-DSS ihlalidir. Maskeli kart (****4444) veya token guvenlidir; userId ve tutar tek basina odeme araci degildir.",
    "P-12": "PCI-DSS, ham PAN'in (tam kart numarasi + son kullanma tarihi) acikca loglanmasini yasaklar. Maskeli kart (****8813) ve saglayici tokeni (tok_*) standarda uygundur. Ihlal, tam PAN + exp yazan DEBUG satiridir.",
    "P-14": "'email verified userId=12' sadece kimliksiz bir olay bilgisi tasir, kisisel veri sizdirmaz. DB baglanti URI'si sifre verir, Bearer JWT hesabi devralinabilir, session cookie oturumu calinabilir. Guvenli tek satir budur.",
    "K-08": "Zincirleme arizanin isareti, birden cok servisin devre kesicisinin ayni anda acilmasi ve upstream thread havuzlarinin tukenmesidir; hata bagimlilik zinciri boyunca yayilmistir. Tek servisteki WARN/INFO satirlari henuz yayilma gostermez.",
    "K-14": "Oncelik musteri etkisiyle belirlenir: odeme API'si %100 coktuysa tum gelir akisi durmustur; ic aracin yavasligi sadece verimlilik kaybidir. Yazim hatasinin etkisi sifirdir; surekli tekrarlayan ERROR tek seferlik WARN'dan oncelidir.",
    "E-09": "GC overhead limit exceeded, JVM zamaninin neredeyse tamamini cop toplayicida gecirip heap'ten yeterli alan geri alamadigi anlamina gelir: bellek tukenmektedir. Cozum heap'i buyutmek veya sizintiyi bulmaktir; ag, disk ve CPU ile ilgisizdir.",
    "H-04": "Yeni surumun 500 hatalarini normalin ucinde katina cikardigi goruluyorsa en hizli iyilesme bilinen iyi surume donmektir (en dusuk MTTR). Log seviyesi degistirmek sorunu gizler, beklemek musteri etkisini surdurur; rollback guvenli ve geri alinabilir adimdir.",
    "H-10": "401 Unauthorized 'kimligin dogrulanamadi' demektir (bilgi eksik/gecersiz); 403 Forbidden ise kimlik dogrulanmis ama yetkinin olmadigi anlamina gelir. Tanimlari ters cevirmek erisim kontrolu sorunlarini yanlis teshis ettirir.",
    "N-06": "Idempotent istek tekrarlandiginda sonuc degismez: PUT ayni kaynaga ayni icerigi yazar, tekrari zararsizdir. POST her cagrida yeni kaynak yaratir; CONNECT tunel acar; PATCH tekrari baglama gore farkli sonuc verebilir.",
    "N-07": "Gercek e-posta adresi dogrudan kisisel veridir (KVKK/GDPR) ve acik yazilmasi sizintidir. Maskeli gosterim (m.k***@), sadece domain veya hash'li form kimligin yeniden kurulamamasini sagladigi icin guvenlidir.",
    "P-05": "'INFO sorgu tamam rows=1 sure=8ms' hicbir kisisel veri icermez, loglanmasi serbesttir. TC kimlik ceken SQL, tam kart numarasi ve SMTP sifresi ele gecirildiginde kimlik/finansal zarar dogurur.",
    "H-09": "Yuk yuksek ama CPU %2 ve iowait %90 ise cekirdek zamani disk beklemekte harcaniyor demektir; sorun islemcide degil diskte/girdi-cikta zinciridir. Darbogazi analizi disk IOPS ve gecikmesiyle yapilmalidir.",
    "N-03": "499 Nginx'e ozgudur: istemci yanit gelmeden baglantiyi kendisi kapatti. Upstream yavas olsaydi 504, kimlik sorunu olsaydi 401/403 gorurduk. Genelde istemci tarafindaki kisa zaman asimlarinin isaretidir.",
    "K-04": "Tek bir cron isininin hatasi 1 saat icinde otomatik tekrarlanacak, musteri etkisi yok. DB erisilemezligi, cift tahsilat ve kimlik dogrulama kesintisi aktif geliren/musteri etkisidir ve hemen mudahale ister.",
}


def main():
    with open(IN_FILE, encoding="utf-8") as f:
        ornekler = [json.loads(l) for l in f]

    eksik = [o["id"] for o in ornekler if o["id"].rstrip("p") not in GEREKCE]
    if eksik:
        raise SystemExit(f"Gerekce eksik: {eksik}")

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        for o in ornekler:
            tmp = o["id"][:-1] if o["id"].endswith("p") else o["id"]
            eski = o["messages"][2]["content"]          # 'Cevap: X'
            yeni = eski + "\nNeden: " + GEREKCE[tmp]    # cevap + gerekce
            o["messages"][2]["content"] = yeni
            f.write(json.dumps(o, ensure_ascii=False) + "\n")

    print(f"{len(ornekler)} ornek (gerekceli) -> {OUT_FILE}")


if __name__ == "__main__":
    main()
