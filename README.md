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
