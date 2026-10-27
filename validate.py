#!/usr/bin/env python3
"""Verifica integritatea datasetului din data-bibliaortodoxa/books.

Utilizare: python3 validate.py [--data data-bibliaortodoxa/books]

Verifica:
  - toate cele 80 de carti din canon.json exista si au numarul de capitole din canon
  - fiecare capitol are versete, cu chei numerice
  - numaratoarea versetelor e continua 1..N sau, daca are goluri, capitolul
    are o nota care explica de ce (sursa are un verset lipsa)

Cod de ieșire: 0 daca e totul in regula, 1 daca lipseste ceva structural.
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
CANON = json.loads((HERE / "canon.json").read_text(encoding="utf-8"))["carti"]
DATA = Path(sys.argv[sys.argv.index("--data") + 1]) if "--data" in sys.argv else HERE / "data-bibliaortodoxa" / "books"


def ranges(nums: list[int]) -> str:
    """[30, 35, 36, 37] -> '30, 35-37'."""
    out, start, prev = [], None, None
    for n in nums:
        if start is None:
            start = prev = n
        elif n == prev + 1:
            prev = n
        else:
            out.append(str(start) if start == prev else f"{start}-{prev}")
            start = prev = n
    if start is not None:
        out.append(str(start) if start == prev else f"{start}-{prev}")
    return ", ".join(out)


def main() -> int:
    erori, goluri, total_v, total_c = [], [], 0, 0

    for b in CANON:
        f = DATA / f"{b['abr']}.json"
        if not f.exists():
            erori.append(f"lipseste {f.name}")
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        if len(d["capitole"]) != b["capitole"]:
            erori.append(f"{b['abr']}: {len(d['capitole'])} capitole, canon zice {b['capitole']}")

        for c in d["capitole"]:
            total_c += 1
            if not c["versuri"]:
                erori.append(f"{b['abr']} {c['n']}: capitol fara versete")
                continue
            if not all(k.isdigit() for k in c["versuri"]):
                erori.append(f"{b['abr']} {c['n']}: chei de verset nenumerice")
                continue
            nums = sorted(int(k) for k in c["versuri"])
            total_v += len(nums)
            if nums != list(range(1, len(nums) + 1)):
                if "nota" in c:
                    lipsa = [n for n in range(1, max(nums) + 1) if n not in nums]
                    goluri.append(f"{b['abr']} {c['n']}: lipsa {ranges(lipsa)} (notat in fisier)")
                else:
                    erori.append(f"{b['abr']} {c['n']}: numerotare rupta fara nota")

    print(f"carti:    {len(CANON)}")
    print(f"capitole: {total_c}")
    print(f"versete:  {total_v}")

    if goluri:
        print(f"\ncapitole cu goluri asumate in sursa ({len(goluri)}):")
        for g in goluri:
            print("  " + g)

    if erori:
        print(f"\nPROBLEME ({len(erori)}):")
        for e in erori:
            print("  " + e)
        return 1

    print("\nOK — structura e coerenta.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
