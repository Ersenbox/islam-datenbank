# islam-datenbank

Zentrale JSON-Datenquelle für Islam-Apps. Inhalte werden von den Apps geladen, statt in die APK eingebettet zu werden.

## Struktur

```
manifest.json                 Version + Dateiliste (Größe, SHA-256, Anzahl)
data/daily/ayetler.json       365 Tage – Arapça + Türkçe meal (Feld "gun" = Tag 1–365)
data/daily/dualar.json        360 Tage – okunuş, anlam, kaynak
data/daily/sunnetler.json     180 Tage – Günün Sünneti (vollständig, geprüft; Feld "derece")
data/hadith/<kitap>/index.json        Buchliste (id, name, count, file, bytes)
data/hadith/<kitap>/books/<id>.json   Hadithe eines Kapitels
tools/build.py                baut alles aus den Original-Dateien neu
```

Hadis-Kitaplar: `bukhari`, `muslim`, `abudawud`, `tirmidhi`, `nasai`, `ibnmajah` (Englisch).

Hadis-Eintrag: `n` Nr., `ar` arabische Nr., `text`, `grades`, `book`, `h`.

## Abruf (jsDelivr)

```
https://cdn.jsdelivr.net/gh/Ersenbox/islam-datenbank@main/manifest.json
https://cdn.jsdelivr.net/gh/Ersenbox/islam-datenbank@main/data/daily/ayetler.json
https://cdn.jsdelivr.net/gh/Ersenbox/islam-datenbank@main/data/hadith/bukhari/index.json
```

Alternativ: `https://raw.githubusercontent.com/Ersenbox/islam-datenbank/main/<pfad>`

## Update-Ablauf in der App

1. `manifest.json` laden, `version` mit lokal gespeicherter vergleichen.
2. Bei neuer Version: `sha256` je Datei vergleichen und nur geänderte Dateien laden.
3. Bei Datenänderung `version` im Manifest erhöhen (`tools/build.py`, `VERSION`).
4. Hinweis: jsDelivr cached `@main` bis zu 12 h; für sofortige Updates ein Tag/Release (`@v1`) nutzen.

## Bekannter Stand

- `sunnetler.json`: 180 Tage, jeder Eintrag gegen die Hadith-Datenbank geprüft, keine schwachen Hadithe (siehe `DEGISIKLIKLER.md`).
- `dualar.json`: 24 Einträge sind schwach (Daif), ~20 nicht verifizierbar (siehe Bericht).
- Leere Hadis-Einträge (Titel/Einleitungen) wurden entfernt.

## Tageslogik in der App (Zyklus)

Jede Datei läuft unabhängig im Kreis:

```
dayOfYear = 1..366
sunnet = sunnetler[(dayOfYear-1) % 180]      // beginnt alle 180 Tage von vorn
dua    = dualar[(dayOfYear-1) % 360]
ayet   = ayetler[(dayOfYear-1) % 365]
```

## v4 (2026-11-03) – Neu / Yeni

| Datei | Inhalt | Quelle |
|---|---|---|
| `data/daily/ayetler.json` | 365 Verse, **neue Felder** `ingilizce_meal`, `almanca_meal`, `fransizca_meal` (+ `*_kaynagi`) | alquran.cloud: `en.sahih`, `de.bubenheim`, `fr.hamidullah` |
| `data/daily/sunnetler.json` | jetzt **365 Tage** (1–180 unverändert, 181–365 neu). Neue Einträge nur Buhârî/Müslim (Sahih), Text 1:1 aus türkischer Übersetzung, plus `hadis_metni_en`, `hadis_metni_fr`, `kaynak_url` | fawazahmed0/hadith-api (`tur-*`, `eng-*`, `fra-*`) |
| `data/daily/dualar_v2.json` | **neu**, 365 Tage: 59 Koran-Duas + 306 Hadith-Duas, nur Sahih/Hasan (kein Daif), mit Arabisch, TR, EN, DE, FR, Quelle + Link | alquran.cloud, fawazahmed0/hadith-api |
| `data/hadith_tr/<kitap>/` | türkische Hadith-Texte, gleiche Struktur wie `data/hadith/` | fawazahmed0/hadith-api `tur-*` (Nesâî nur 628 Hadithe) |
| `data/hadith_fr/<kitap>/` | französische Hadith-Texte, gleiche Struktur | fawazahmed0/hadith-api `fra-*` (Tirmizî fehlt) |

- `dualar.json` (alt) bleibt **unverändert**. Achtung: 62 Einträge nennen alle „İbn Mâce 925“, 20 Einträge verweisen auf schwache (daif) Hadithe, 100 Tage sind nur Esmâ-Namen, kein arabischer Text. Für Apps `dualar_v2.json` benutzen.
- **Deutsch bei Hadithen:** Es gibt keine offene deutsche Hadith-Übersetzung. Apps zeigen den englischen Text + Hinweis (`almanca_not` / `hadis_metni_de_not`).
- `dualar_v2.json`: Bei Hadith-Duas steht der **ganze Hadith** (inkl. Kontext), kein Lateinisch-Okunuş (Quelle hat keinen).
- Neu bauen: `tools/build_v4_ayetler.py`, `tools/build_v4_sunnetler.py` (+ `tools/sunnet_konular.py`), `tools/build_v4_dualar.py`, `tools/build_v4_hadis_dil.py`, `tools/build_v4_manifest.py`.

Tageslogik (v4): `ayet = ayetler[(dayOfYear-1) % 365]`, `sunnet = sunnetler[(dayOfYear-1) % 365]`, `dua = dualar_v2.dualar[(dayOfYear-1) % 365]` (Tag 366 → wieder Tag 1).
