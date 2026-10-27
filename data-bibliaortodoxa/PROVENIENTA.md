# Proveniența textului

Textul din `books/` a fost extras automat de pe **[bibliaortodoxa.ro](https://bibliaortodoxa.ro/)**
în octombrie 2026, cu scriptul `scrape_bibliaortodoxa.py` din acest repo.

## Ce e

Biblia sau Sfânta Scriptură în ediția sinodală a Bisericii Ortodoxe Române,
în ortografia ediției tipărite (`prooroc`, `mîna`, `cît`) — nu în ortografia
modernizată din alte digitizări.

- 80 de cărți, 1.347 de capitole, canonul ortodox complet
- Psalmii după numerotarea Septuagintei, cu Psalmul 151
- cărțile pe care edițiile protestante nu le au: Tobit, Iudita, Baruh,
  Epistola lui Ieremia, Cântarea celor trei tineri, III Ezdra, Înțelepciunea
  lui Solomon, Sirah, Susana, Bel, 1–2–3 Macabei, Rugăciunea regelui Manase

## Cine a făcut textul

Digitizarea aparține echipei de la bibliaortodoxa.ro, care a tehnoredactat,
scanat și corectat textul pe cont propriu, ca inițiativă privată. Aici e
redistribuit pentru uz de studiu și pentru ca API-ul să funcționeze.

**Dacă ești din echipa bibliaortodoxa.ro** și nu vrei ca textul să stea aici,
deschide un issue sau scrie-mi — îl scot imediat, fără discuții.

## Calitatea textului

E o digitizare, nu un facsimil. Am comparat cu datasetul public
[AndreiGam/bibliaortodoxa](https://github.com/AndreiGam/bibliaortodoxa):
diferențele sunt de două feluri — ortografie veche (`cît` vs `cât`, corect
aici) și typo-uri OCR (`maţ mult` în loc de `mai mult`, `1-a` în loc de
`l-a`). Astea din urmă sunt greșeli ale sursei, păstrate ca atare ca să nu
inventez text.

Nu folosi acest fișier ca ediție critică. Pentru citat academic, tipăritura.

## Numerotarea versetelor

17 capitole au numerotarea stricată în sursă. Am tratat două cazuri diferit:

- **Numere duplicate** (14 capitole) — pagina are, de exemplu, două versete
  cu numărul 11 și niciunul cu 12. Rândurile sunt însă complete și în ordine,
  așa că am renumerotat 1..N. Fără asta, scrierea într-un dict ar fi pierdut
  un verset. Capitolul are un câmp `nota` cu numerele originale.
- **Verset chiar lipsă** (2 capitole) — Deuteronom 2 nu are versetul 18, iar
  Iosua 22 nu are 30 și are o etichetă greșită „80" pe ultimul rând. Aici am
  păstrat numerotarea originală și am pus o notă, ca să nu deplasez toate
  versetele următoare.

Două diferențe față de datasetul GitHub care nu sunt erori ale sursei:

- **Psalmul 111** are 10 versete în tipar; pagina le afișează pe ultimele
  două într-un singur rând, cu „10." în text.
- **Galateni 4** are 31 de versete (corect aici); datasetul GitHub are 30.

## Licență

Textul **nu** e acoperit de licența MIT a codului. Nu are o licență de
reutilizare declarată de autorii digitizării.
