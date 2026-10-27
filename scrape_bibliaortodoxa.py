#!/usr/bin/env python3
"""Scrape bibliaortodoxa.ro intr-un dataset JSON, in aceeasi schema ca data/.

Utilizare:  python3 scrape_bibliaortodoxa.py [--out data-bibliaortodoxa]

Rezultatul: <out>/books/*.json + <out>/books/cuprins.json
Site-ul e mic si fara API public, asa ca merge incet, cu pauze intre cereri
si cu reincercari. Dureaza ~8 minute pentru tot canonul.
"""

import html
import json
import random
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASE = "https://bibliaortodoxa.ro"
UA = "Mozilla/5.0 (compatible; cititor-biblie/1.0; uz personal)"
DELAY = 0.7          # secunde intre cereri, per worker
WORKERS = 2
RETRIES = 3

HERE = Path(__file__).parent
TOC = json.loads((HERE / "data" / "books" / "cuprins.json").read_text(encoding="utf-8"))

# id-ul din carte.php pentru fiecare abreviere
IDS = {
    "Fc": 25, "Ies": 32, "Lv": 47, "Num": 59, "Dt": 17, "Ios": 41, "Jd": 46, "Rut": 71,
    "1Rg": 66, "2Rg": 67, "3Rg": 68, "4Rg": 69, "1Par": 14, "2Par": 15, "1Ezr": 23,
    "Ne": 58, "Est": 21, "Iov": 42, "Ps": 65, "Pr": 63, "Ecc": 18, "Cant": 9,
    "Is": 43, "Ir": 31, "Plg": 64, "Iz": 33, "Dn": 16, "Os": 60, "Am": 3, "Mi": 56,
    "Ioil": 39, "Avd": 6, "Ion": 40, "Naum": 57, "Avc": 5, "Sof": 73, "Ag": 2, "Za": 82,
    "Mal": 52, "Tob": 81, "Idt": 45, "Bar": 8, "Epist": 20, "Tin": 1, "3Ezr": 24,
    "Sol": 74, "Sir": 72, "Sus": 75, "Bel": 7, "1Mac": 49, "2Mac": 50, "3Mac": 51,
    "Man": 54, "Mt": 55, "Mc": 53, "Lc": 48, "In": 35, "FA": 26, "Rm": 70, "1Co": 12,
    "2Co": 13, "Ga": 29, "Ef": 19, "Flp": 28, "Col": 10, "1Tes": 76, "2Tes": 77,
    "1Tim": 78, "2Tim": 79, "Tit": 80, "Flm": 27, "Evr": 22, "Iac": 30, "1Ptr": 61,
    "2Ptr": 62, "1In": 36, "2In": 37, "3In": 38, "Iuda": 44, "Ap": 4,
}


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt == RETRIES - 1:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError("unreachable")


def parse_chapter(page: str) -> tuple[str, dict[str, str], str | None]:
    """Intoarce (nume capitol, versete, nota).

    Site-ul are capitole unde numerele de verset sunt duplicate sau deplasate
    (ex. doua versete cu numarul 11, iar 1 lipseste). Randurile insa sunt
    complete si in ordinea corecta, asa ca renumerotam 1..N si trecem
    numerotarea originala intr-o nota, ca sa nu pierdem text.
    """
    title = re.search(r'<div class="css_cat">(.*?)</div>', page, re.S)
    nume = re.sub(r"<[^>]+>", "", title.group(1)).strip() if title else ""

    rows: list[tuple[int, str]] = []
    for m in re.finditer(r"<tr id=verset(\d+)>(.*?)</tr>", page, re.S):
        cells = re.findall(r"<td[^>]*>(.*?)</td>", m.group(2), re.S)
        if len(cells) < 2:
            continue
        text = html.unescape(re.sub(r"<[^>]+>", "", cells[-1]))
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            rows.append((int(m.group(1)), text))

    labels = [n for n, _ in rows]
    if labels == list(range(1, len(rows) + 1)):
        return nume, {str(n): t for n, t in rows}, None

    # Numere duplicate = etichete stricate, dar randurile sunt in ordine:
    # renumerotam 1..N, altfel am pierde versete la scrierea in dict.
    if len(set(labels)) < len(labels):
        nota = "numerele din sursa: " + ", ".join(str(n) for n in labels)
        return nume, {str(i): t for i, (_, t) in enumerate(rows, 1)}, nota

    # Doar goluri, fara duplicate = un verset chiar lipseste din sursa.
    # Pastram numerotarea originala ca sa nu deplasam versetele urmatoare.
    nota = "numerotare cu goluri in sursa: " + ", ".join(str(n) for n in labels)
    return nume, {str(n): t for n, t in rows}, nota


def scrape_book(out: Path, n: int, abr: str, titlu: str, nume: str, chapters: int) -> str:
    target = out / "books" / f"{abr}.json"
    if target.exists():
        return f"skip {abr}"
    book = {"n": n, "abr": abr, "titlu": titlu, "nume": nume, "capitole": []}
    reparate = 0
    for cap in range(1, chapters + 1):
        time.sleep(DELAY + random.uniform(0, 0.3))
        page = fetch(f"{BASE}/carte.php?id={IDS[abr]}&cap={cap}")
        cname, verses, nota = parse_chapter(page)
        if not verses:
            raise RuntimeError(f"{abr} {cap}: niciun verset gasit")
        entry = {"n": cap, "nume": cname or f"{titlu} - Capitolul {cap}", "versuri": verses}
        if nota:
            entry["nota"] = nota
            reparate += 1
        book["capitole"].append(entry)
    target.write_text(json.dumps(book, ensure_ascii=False, indent=1), encoding="utf-8")
    total = sum(len(c["versuri"]) for c in book["capitole"])
    extra = f" ({reparate} capitole renumerotate)" if reparate else ""
    return f"ok {abr:6} {chapters:3} cap. {total:5} versete{extra}"


def main():
    out = Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else HERE / "data-bibliaortodoxa"
    (out / "books").mkdir(parents=True, exist_ok=True)
    (out / "books" / "cuprins.json").write_text(
        json.dumps(TOC, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    jobs = []
    for testament, entries in TOC.items():
        for key, meta in sorted(entries.items(), key=lambda kv: int(kv[0])):
            jobs.append((int(key), meta["abr"], meta["titlu"], meta["nume"]))

    counts = {}
    for f in (HERE / "data" / "books").glob("*.json"):
        if f.name == "cuprins.json":
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        counts[d["abr"]] = len(d["capitole"])

    print(f"{len(jobs)} carti, {sum(counts.values())} capitole de descarcat", flush=True)
    done = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = [
            pool.submit(scrape_book, out, n, abr, titlu, nume, counts[abr])
            for n, abr, titlu, nume in jobs
        ]
        for fut in futures:
            done += 1
            print(f"[{done:3}/{len(jobs)}] {fut.result()}", flush=True)
    print("GATA", flush=True)


if __name__ == "__main__":
    main()
