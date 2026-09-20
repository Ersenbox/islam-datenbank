#!/usr/bin/env python3
"""Baut die islam-datenbank aus den Original-JSON-Dateien.
Aufruf:  python3 build.py <ordner_mit_originalen> <ausgabe_ordner>
"""
import json, re, sys, glob, os, hashlib, unicodedata
from datetime import date

src, out = sys.argv[1], sys.argv[2]
VERSION = 3

def find(prefix):
    for f in glob.glob(os.path.join(src, '*.json')):
        n = unicodedata.normalize('NFC', os.path.basename(f))
        if n.startswith(prefix):
            return f
    raise SystemExit('Datei nicht gefunden: ' + prefix)

def load(path):
    return json.loads(open(path, encoding='utf-8-sig').read())

def dump(path, data, pretty=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        if pretty:
            json.dump(data, f, ensure_ascii=False, indent=1)
        else:
            json.dump(data, f, ensure_ascii=False, separators=(',', ':'))

def clean(s):
    return s.replace('\ufeff', '').strip() if isinstance(s, str) else s

files = []
def register(rel, count, extra=None):
    p = os.path.join(out, rel)
    b = open(p, 'rb').read()
    e = {'path': rel, 'count': count, 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()}
    if extra: e.update(extra)
    files.append(e)

# ---------- Ayetler ----------
a = load(find('365'))
ay = []
for x in a['ayetler']:
    x = {k: clean(v) for k, v in x.items() if k != 'tarih'}
    ay.append(x)
dump(os.path.join(out, 'data/daily/ayetler.json'), {'aciklama': a['aciklama'], 'ayetler': ay}, True)
register('data/daily/ayetler.json', len(ay))

# ---------- Dualar ----------
d = [{k: clean(v) for k, v in x.items()} for x in load(find('360'))]
dump(os.path.join(out, 'data/daily/dualar.json'), d, True)
register('data/daily/dualar.json', len(d))

# ---------- Sünnetler (Datei ist abgeschnitten -> vollständige Einträge retten) ----------
raw = open(find('180'), encoding='utf-8-sig').read()
try:
    s = json.loads(raw)
except json.JSONDecodeError:
    s = []
    dec = json.JSONDecoder()
    i = raw.index('[') + 1
    while True:
        m = re.compile(r'\s*,?\s*').match(raw, i); i = m.end()
        if i >= len(raw) or raw[i] != '{': break
        try:
            obj, i = dec.raw_decode(raw, i)
            s.append(obj)
        except json.JSONDecodeError:
            break
s = [{k: clean(v) for k, v in x.items()} for x in s]
dump(os.path.join(out, 'data/daily/sunnetler.json'), s, True)
register('data/daily/sunnetler.json', len(s), {'expected': 180, 'complete': len(s) == 180})

# ---------- Hadis-Kitaplari ----------
COLL = {'bukhari': 'Sahih al-Bukhari', 'muslim': 'Sahih Muslim', 'abudawud': 'Sunan Abu Dawud',
        'tirmidhi': 'Jami at-Tirmidhi', 'nasai': "Sunan an-Nasa'i", 'ibnmajah': 'Sunan Ibn Majah'}
for key, title in COLL.items():
    h = load(os.path.join(src, f'eng-{key}.min.json'))
    secs = h['metadata']['sections']
    books = {}
    skipped = 0
    for x in h['hadiths']:
        if not x['text'].strip():
            skipped += 1; continue
        b = str(x['reference']['book'])
        item = {'n': x['hadithnumber'], 'text': x['text'].strip()}
        if 'arabicnumber' in x: item['ar'] = x['arabicnumber']
        if x.get('grades'): item['grades'] = x['grades']
        item['book'] = x['reference']['book']; item['h'] = x['reference']['hadith']
        books.setdefault(b, []).append(item)
    idx = []
    for b, items in sorted(books.items(), key=lambda t: int(t[0])):
        rel = f'data/hadith/{key}/books/{b}.json'
        dump(os.path.join(out, rel), items)
        idx.append({'id': int(b), 'name': secs.get(b, '').strip() or f'Book {b}', 'count': len(items),
                    'file': f'books/{b}.json', 'bytes': os.path.getsize(os.path.join(out, rel))})
    total = sum(i['count'] for i in idx)
    rel = f'data/hadith/{key}/index.json'
    dump(os.path.join(out, rel), {'id': key, 'name': title, 'language': 'en', 'total': total,
                                  'skipped_empty': skipped, 'books': idx}, True)
    register(rel, total, {'books': len(idx), 'download_bytes': sum(i['bytes'] for i in idx)})
    print(key, total, 'hadith,', len(idx), 'books,', skipped, 'leer uebersprungen')

manifest = {'name': 'islam-datenbank', 'version': VERSION, 'updated': date.today().isoformat(), 'files': files}
dump(os.path.join(out, 'manifest.json'), manifest, True)
print('sunnetler:', len(s), '/ 180')
