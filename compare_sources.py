#!/usr/bin/env python3
"""Compara cele doua surse: datasetul GitHub vs textul de pe bibliaortodoxa.ro.

Utilizare: python3 compare_sources.py [--a data/books] [--b data-bibliaortodoxa/books]

Raporteaza cate versete sunt identice dupa normalizare (fara diacritice,
fara punctuatie), care e rata pe fiecare carte, si da exemple de diferente.
"""

import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent


def arg(flag, default):
    return Path(sys.argv[sys.argv.index(flag) + 1]) if flag in sys.argv else default


A = arg("--a", HERE / "data" / "books")
B = arg("--b", HERE / "data-bibliaortodoxa" / "books")


def norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-z0-9 ]", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def load(root: Path) -> dict:
    out = {}
    for f in root.glob("*.json"):
        if f.name == "cuprins.json":
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        out[d["abr"]] = d
    return out


def main():
    a, b = load(A), load(B)
    only_a = set(a) - set(b)
    only_b = set(b) - set(a)
    if only_a:
        print("doar in A:", sorted(only_a))
    if only_b:
        print("doar in B:", sorted(only_b))

    tot = same = diff = missing = 0
    per_book = []
    examples = []
    for abr in sorted(set(a) & set(b)):
        cha = {c["n"]: c["versuri"] for c in a[abr]["capitole"]}
        chb = {c["n"]: c["versuri"] for c in b[abr]["capitole"]}
        bs = bd = bm = 0
        for cap, va in cha.items():
            vb = chb.get(cap, {})
            for v, ta in va.items():
                if v not in vb:
                    bm += 1
                    continue
                if norm(ta) == norm(vb[v]):
                    bs += 1
                else:
                    bd += 1
                    if len(examples) < 12:
                        examples.append((a[abr]["titlu"], cap, v, ta, vb[v]))
        tot += bs + bd + bm
        same += bs
        diff += bd
        missing += bm
        per_book.append((abr, a[abr]["titlu"], bs + bd + bm, bs, bd, bm))

    print(f"\n{'carte':32} {'versete':>8} {'identice':>9} {'diferite':>9} {'lipsa':>6} {'%':>7}")
    print("-" * 78)
    for abr, titlu, n, s, d, m in sorted(per_book, key=lambda r: (r[3] / max(r[2], 1))):
        print(f"{titlu[:32]:32} {n:8} {s:9} {d:9} {m:6} {s/max(n,1)*100:6.1f}%")
    print("-" * 78)
    print(f"{'TOTAL':32} {tot:8} {same:9} {diff:9} {missing:6} {same/max(tot,1)*100:6.1f}%")

    print("\nEXEMPLE DE DIFERENTE (A = GitHub, B = bibliaortodoxa.ro)")
    for titlu, cap, v, ta, tb in examples:
        print(f"\n{titlu} {cap}:{v}")
        print("  A:", ta[:220])
        print("  B:", tb[:220])


if __name__ == "__main__":
    main()
