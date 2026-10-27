# Biblia ortodoxă română — API local

API minimal peste textul Bibliei ortodoxe (ediția sinodală), ca să poți construi
o aplicație fără să scrapezi un site la fiecare cerere.

**Conținut:** 80 de cărți, 1.347 de capitole, 36.310 versete — canonul ortodox
complet, inclusiv Tobit, Iudita, Baruh, Ecclesiasticul, Macabeii, III Ezdra,
Rugăciunea regelui Manase și Psalmul 151.

Textul e în repo, în `data-bibliaortodoxa/books/`, și e sursa implicită a
serverului. Ortografia e cea din tipar (`prooroc`, `mîna`, `cît`), nu cea
modernizată.

## Două surse de text

| Folder | Ce e | Ortografie | În repo |
|---|---|---|---|
| `data-bibliaortodoxa/books` | extras de pe bibliaortodoxa.ro | veche (`prooroc`, `mîna`) | **da** — sursa implicită |
| `data/books` | dataset GitHub (AndreiGam) | modernizată (`proroc`, `mâna`) | nu, se aduce local |

Datasetul GitHub are 36.311 versete față de 36.310 aici. Diferența e
documentată în [PROVENIENTA.md](data-bibliaortodoxa/PROVENIENTA.md).

Serverul alege sursa așa:

```bash
python3 server.py                                   # data-bibliaortodoxa/books
python3 server.py --data data/books                 # datasetul modernizat
BIBLE_DATA=data/books python3 server.py 9000
```

## Cum se extrage textul de pe site

`scrape_bibliaortodoxa.py` descarcă toate cele 1.347 de capitole, cu pauze între
cereri și reîncercări. Merge lent, intenționat — site-ul e mic și nu are API.

```bash
python3 scrape_bibliaortodoxa.py            # ~25 min, scrie în data-bibliaortodoxa/
python3 compare_sources.py                  # diferențe între cele două surse
```

Se poate relua oricând: sări peste cărțile deja descărcate.

## Pornire

```bash
python3 server.py          # http://127.0.0.1:8787
python3 server.py 9000     # alt port
```

Fără dependențe — doar biblioteca standard Python 3.9+.

## Rute

| Rută | Ce întoarce |
|---|---|
| `GET /` | documentație + totaluri |
| `GET /api/books` | lista cărților, cu id, titlu, testament, număr de capitole |
| `GET /api/books/{id}` | o carte: capitolele și câte versete are fiecare |
| `GET /api/books/{id}/{capitol}` | versetele capitolului |
| `GET /api/verse/{id}/{capitol}/{verset}` | un singur verset |
| `GET /api/search?q=text&limit=20` | căutare, ignoră diacriticele |
| `GET /api/random` | un verset la întâmplare |

`id` este abrevierea cărții, cu minuscule: `fc`, `ies`, `ps`, `mt`, `mc`, `lc`,
`in`, `fa`, `rm`, `ap` etc. Lista completă: `GET /api/books`.

## Exemple

```bash
curl http://127.0.0.1:8787/api/books/in/3
curl http://127.0.0.1:8787/api/verse/in/3/16
curl "http://127.0.0.1:8787/api/search?q=fericiti&limit=5"
curl "http://127.0.0.1:8787/api/search?q=inima%20curata"   # merge și fără diacritice
```

```json
{
  "carte": "Ioan",
  "capitol": 3,
  "verset": 16,
  "text": "Căci Dumnezeu aşa a iubit lumea, încât pe Fiul Său Cel Unul-Născut L-a dat ca oricine crede în El să nu piară, ci să aibă viaţă veşnică.",
  "referinta": "Ioan 3, 16"
}
```

CORS este deschis (`Access-Control-Allow-Origin: *`), deci merge direct din
browser. Serverul ține totul în memorie și răspunde în ~2–5 ms.

## Date

`data-bibliaortodoxa/books/*.json`, câte un fișier pe carte, plus
`cuprins.json` cu ordinea canonică. Structura unui fișier:

```json
{
  "n": 8,
  "abr": "Rut",
  "titlu": "Cartea Rut",
  "capitole": [
    { "n": 1, "nume": "Rut Capitolul 1", "versuri": { "1": "În zilele acelea..." } }
  ]
}
```

Sursa textului din repo: [bibliaortodoxa.ro](https://bibliaortodoxa.ro/),
prin `scrape_bibliaortodoxa.py`. Detalii în
[PROVENIENTA.md](data-bibliaortodoxa/PROVENIENTA.md).

## De știut înainte de producție

- **Textul de bază** este ediția sinodală a BOR (1914, revizuită 1982/1994).
  Datasetul are licență Unlicense, dar ediția tipărită a BOR are propria
  situație de drepturi. Pentru o aplicație publică, verifică asta sau cere
  binecuvântarea editurii bisericești.
- **Nu există un API public** cu textul ortodox. Agregatorii liberi
  (bolls.life, getbible, helloao, wldeh) au doar traduceri protestante:
  Cornilescu, NTR, BTF, LSB.
- Dacă vrei găzduit, codul ăsta se poate muta ușor într-un Cloudflare Worker
  sau pe un VPS mic, cu datele servite din JSON.

## Textul biblic

Textul e inclus în repo, în `data-bibliaortodoxa/books/` — extras de pe
[bibliaortodoxa.ro](https://bibliaortodoxa.ro/), 80 de cărți, 1.347 de
capitole, canonul ortodox complet.

Proveniența, calitatea textului și ce se întâmplă dacă ownerul site-ului
cere retragerea: **[PROVENIENTA.md](data-bibliaortodoxa/PROVENIENTA.md)**.

Pe scurt: digitizarea aparține echipei de la bibliaortodoxa.ro, nu are o
licență de reutilizare declarată, și e redistribuită aici pentru studiu.
Codul e MIT; textul **nu** e acoperit de MIT.

Datasetul alternativ (ortografie modernizată) e în `.gitignore` — se aduce
local cu `scrape_bibliaortodoxa.py` sau de la
[AndreiGam/bibliaortodoxa](https://github.com/AndreiGam/bibliaortodoxa).

## Licență

Cod: [MIT](LICENSE). Textul biblic: vezi mai sus.


