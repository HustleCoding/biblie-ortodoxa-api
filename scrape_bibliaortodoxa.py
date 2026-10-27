#!/usr/bin/env python3
"""Scrape bibliaortodoxa.ro intr-un dataset JSON, in aceeasi schema ca data/.

Utilizare:
    python3 scrape_bibliaortodoxa.py [--out data-bibliaortodoxa] [--only Abr]

Rezultatul: <out>/books/*.json + <out>/books/cuprins.json
Site-ul e mic si fara API public, asa ca merge incet, cu pauze intre cereri
si cu reincercari. Dureaza ~15 minute pentru tot canonul.

Lista cartilor, numarul de capitole si id-urile din carte.php stau in
canon.json, ca sa nu depinda de folderul data/ (care nu e in repo).
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
CANON = json.loads((HERE / "canon.json").read_text(encoding="utf-8"))["carti"]


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


def scrape_book(out: Path, book_meta: dict) -> str:
    abr, chapters = book_meta["abr"], book_meta["capitole"]
    target = out / "books" / f"{abr}.json"
    if target.exists():
        return f"skip {abr}"
    book = {"n": book_meta["n"], "abr": abr, "titlu": book_meta["titlu"],
            "nume": book_meta["nume"], "capitole": []}
    reparate = 0
    for cap in range(1, chapters + 1):
        time.sleep(DELAY + random.uniform(0, 0.3))
        page = fetch(f"{BASE}/carte.php?id={book_meta['id_site']}&cap={cap}")
        cname, verses, nota = parse_chapter(page)
        if not verses:
            raise RuntimeError(f"{abr} {cap}: niciun verset gasit")
        entry = {"n": cap, "nume": cname or f"{book_meta['titlu']} - Capitolul {cap}",
                 "versuri": verses}
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
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    (out / "books").mkdir(parents=True, exist_ok=True)

    jobs = [b for b in CANON if only is None or b["abr"].lower() == only.lower()]
    if only and not jobs:
        sys.exit(f"Nu stiu cartea {only!r}. Abrevieri: {', '.join(b['abr'] for b in CANON)}")

    cuprins = {}
    for b in CANON:
        cuprins.setdefault(b["testament"], {})[str(b["n"])] = {
            "nume": b["nume"], "abr": b["abr"], "titlu": b["titlu"]
        }
    (out / "books" / "cuprins.json").write_text(
        json.dumps(cuprins, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    print(f"{len(jobs)} carti, {sum(b['capitole'] for b in jobs)} capitole de descarcat", flush=True)
    done = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = [pool.submit(scrape_book, out, b) for b in jobs]
        for fut in futures:
            done += 1
            print(f"[{done:3}/{len(jobs)}] {fut.result()}", flush=True)
    print("GATA", flush=True)


if __name__ == "__main__":
    main()
