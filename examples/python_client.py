#!/usr/bin/env python3
"""Exemplu de client pentru API, doar cu biblioteca standard.

Porneste serverul intai:  python3 server.py
Apoi:                     python3 examples/python_client.py
"""

import json
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:8787"


def get(path: str) -> dict:
    with urllib.request.urlopen(f"{BASE}{path}", timeout=10) as r:
        return json.load(r)


def main():
    # un verset anume
    v = get("/api/verse/in/3/16")
    print(f"{v['referinta']}\n  {v['text']}\n")

    # un capitol intreg
    cap = get("/api/books/mt/5")
    print(f"{cap['carte']} {cap['capitol']} — {len(cap['versete'])} versete")
    print(f"  primul: {cap['versete']['1'][:70]}…\n")

    # cautare fara diacritice
    q = urllib.parse.quote("inima curata")
    rez = get(f"/api/search?q={q}&limit=3")
    print(f"„inima curata” — {rez['rezultate']} rezultate")
    for hit in rez["versete"]:
        print(f"  {hit['carte']} {hit['capitol']}, {hit['verset']}: {hit['text'][:60]}…")


if __name__ == "__main__":
    main()
