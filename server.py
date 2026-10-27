#!/usr/bin/env python3
"""API local pentru Biblia ortodoxa romaneasca (text sinodal).

Pornire:  python3 server.py [port]
Implicit: http://127.0.0.1:8787

Rute:
  GET /                                  documentatie scurta
  GET /api/books                         lista cartilor
  GET /api/books/{id}                    o carte (capitole + nr. versete)
  GET /api/books/{id}/{capitol}          versetele unui capitol
  GET /api/verse/{id}/{capitol}/{verset} un singur verset
  GET /api/search?q=text&limit=20        cautare (ignora diacriticele)
  GET /api/random                        un verset la intamplare
"""

import json
import os
import random
import re
import sys
import unicodedata
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# Sursa textului, in ordine: --data, variabila BIBLE_DATA, apoi implicit.
# data-bibliaortodoxa/books = textul din repo (ortografia tiparului)
# data/books                = datasetul GitHub, ortografie modernizata
_DEFAULT = Path(__file__).parent / "data-bibliaortodoxa" / "books"
if not (_DEFAULT / "cuprins.json").exists():
    _DEFAULT = Path(__file__).parent / "data" / "books"
if "--data" in sys.argv:
    DATA = Path(sys.argv[sys.argv.index("--data") + 1])
elif os.environ.get("BIBLE_DATA"):
    DATA = Path(os.environ["BIBLE_DATA"])
else:
    DATA = _DEFAULT

if not (DATA / "cuprins.json").exists():
    sys.exit(f"Nu gasesc cuprins.json in {DATA}")

# Diacriticele se taie prin NFD + eliminarea semnelor combinate,
# ca sa functioneze si cu virgula dedesubt, si cu cedila.


def fold(s: str) -> str:
    """Scoate diacriticele romanesti, ca sa cauti si fara ele."""
    decomposed = unicodedata.normalize("NFD", s)
    return "".join(c for c in decomposed if unicodedata.category(c) != "Mn").lower()


def load() -> tuple[list[dict], dict[str, dict], list[tuple]]:
    toc = json.loads((DATA / "cuprins.json").read_text(encoding="utf-8"))
    order, books = [], {}
    for testament, entries in toc.items():
        for _, meta in sorted(entries.items(), key=lambda kv: int(kv[0])):
            bid = meta["abr"].lower()
            raw = json.loads((DATA / f'{meta["abr"]}.json').read_text(encoding="utf-8"))
            book = {
                "id": bid,
                "titlu": meta["titlu"],
                "nume": meta["nume"],
                "testament": testament,
                "capitole": [
                    {"n": ch["n"], "versete": len(ch["versuri"]), "text": ch["versuri"]}
                    for ch in raw["capitole"]
                ],
            }
            books[bid] = book
            order.append(
                {
                    "id": bid,
                    "titlu": book["titlu"],
                    "nume": book["nume"],
                    "testament": testament,
                    "capitole": len(book["capitole"]),
                }
            )

    index = [
        (b["id"], b["titlu"], ch["n"], int(v), txt)
        for b in books.values()
        for ch in b["capitole"]
        for v, txt in ch["text"].items()
    ]
    return order, books, index


ORDER, BOOKS, INDEX = load()

# Index plat pentru cautare: text pliat (fara diacritice) + referinta.
FOLDED = []
for bid, titlu, chn, vn, txt in INDEX:
    FOLDED.append((fold(f"{titlu} {chn}:{vn} {txt}"), bid, chn, vn, txt))


class Handler(BaseHTTPRequestHandler):
    server_version = "BibliaOrtodoxaAPI/1.0"

    def log_message(self, fmt, *args):  # linistit in consola
        pass

    def send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlparse(self.path)
        parts = [p for p in url.path.split("/") if p]
        qs = parse_qs(url.query)

        try:
            if not parts:
                return self.send_json(
                    {
                        "api": "Biblia ortodoxa romana - API local",
                        "versiune": "1.1",
                        "sursa": str(DATA),
                        "total": {"carti": len(ORDER), "versete": len(INDEX)},
                        "rute": [
                            "/api/books",
                            "/api/books/{id}",
                            "/api/books/{id}/{capitol}",
                            "/api/verse/{id}/{capitol}/{verset}",
                            "/api/search?q=text&limit=20",
                            "/api/random",
                        ],
                    }
                )

            if parts[:2] == ["api", "books"]:
                if len(parts) == 2:
                    return self.send_json(ORDER)
                book = BOOKS.get(parts[2].lower())
                if not book:
                    return self.send_json({"error": "carte inexistenta", "id": parts[2]}, 404)
                if len(parts) == 3:
                    return self.send_json(
                        {
                            "id": book["id"],
                            "titlu": book["titlu"],
                            "testament": book["testament"],
                            "capitole": [
                                {"n": c["n"], "versete": c["versete"]} for c in book["capitole"]
                            ],
                        }
                    )
                ch = next((c for c in book["capitole"] if c["n"] == int(parts[3])), None)
                if not ch:
                    return self.send_json({"error": "capitol inexistent"}, 404)
                return self.send_json(
                    {
                        "carte": book["titlu"],
                        "id": book["id"],
                        "capitol": ch["n"],
                        "versete": ch["text"],
                    }
                )

            if parts[:2] == ["api", "verse"] and len(parts) == 5:
                book = BOOKS.get(parts[2].lower())
                if not book:
                    return self.send_json({"error": "carte inexistenta"}, 404)
                ch = next((c for c in book["capitole"] if c["n"] == int(parts[3])), None)
                txt = ch["text"].get(parts[4]) if ch else None
                if not txt:
                    return self.send_json({"error": "verset inexistent"}, 404)
                return self.send_json(
                    {"carte": book["titlu"], "capitol": int(parts[3]), "verset": int(parts[4]),
                     "text": txt, "referinta": f'{book["titlu"]} {parts[3]}, {parts[4]}'}
                )

            if parts[:2] == ["api", "search"]:
                q = fold((qs.get("q") or [""])[0].strip())
                limit = min(int((qs.get("limit") or ["20"])[0]), 200)
                if len(q) < 2:
                    return self.send_json({"error": "q trebuie sa aiba minim 2 caractere"}, 400)
                hits = []
                for folded, bid, chn, vn, txt in FOLDED:
                    if q in folded:
                        hits.append(
                            {"id": bid, "carte": BOOKS[bid]["titlu"], "capitol": chn,
                             "verset": vn, "text": txt}
                        )
                        if len(hits) >= limit:
                            break
                return self.send_json({"q": q, "rezultate": len(hits), "versete": hits})

            if parts[:2] == ["api", "random"]:
                bid, titlu, chn, vn, txt = random.choice(INDEX)
                return self.send_json(
                    {"id": bid, "carte": titlu, "capitol": chn, "verset": vn, "text": txt}
                )

            return self.send_json({"error": "ruta inexistenta", "path": url.path}, 404)

        except (ValueError, IndexError):
            return self.send_json({"error": "cerere invalida"}, 400)


def lan_ip() -> str | None:
    """IP-ul din reteaua locala, ca sa-l poti deschide de pe telefon."""
    import socket

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return None


def main():
    # portul e orice argument numeric ramas dupa ce scoatem "--data <cale>"
    # --host 0.0.0.0 expune serverul in reteaua locala (implicit doar localhost)
    port, host, skip_next = 8787, "127.0.0.1", False
    for i, arg in enumerate(sys.argv[1:]):
        if skip_next:
            skip_next = False
        elif arg in ("--data", "--host"):
            skip_next = True
        elif arg.isdigit():
            port = int(arg)
    if "--host" in sys.argv:
        host = sys.argv[sys.argv.index("--host") + 1]

    print(f"{len(ORDER)} carti, {len(INDEX)} versete", flush=True)
    print(f"sursa: {DATA}", flush=True)
    print(f"API pornit: http://{host if host != '0.0.0.0' else '127.0.0.1'}:{port}", flush=True)
    if host == "0.0.0.0":
        ip = lan_ip()
        print(f"din retea:  http://{ip}:{port}" if ip else "din retea:  (nu am gasit IP-ul)", flush=True)
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    main()
