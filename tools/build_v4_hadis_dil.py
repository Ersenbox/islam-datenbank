#!/usr/bin/env python3
"""v4: data/hadith_<dil>/<kitap>/ - mevcut data/hadith/<kitap> (Ingilizce) ile AYNI bolum yapisinda
Turkce (tr) ve Fransizca (fr) metinler. Kaynak: fawazahmed0/hadith-api (tur-*, fra-*).
Mevcut data/hadith klasorune dokunulmaz.
Aufruf: python build_v4_hadis_dil.py <hsrc>
"""
import json, os, sys
sys.stdout.reconfigure(encoding='utf-8')
H = sys.argv[1]
LANG = {'tr': 'tur', 'fr': 'fra'}
BOOKS = ['bukhari', 'muslim', 'abudawud', 'tirmidhi', 'nasai', 'ibnmajah']


def dump(p, d, pretty=False):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        if pretty:
            json.dump(d, f, ensure_ascii=False, indent=1)
        else:
            json.dump(d, f, ensure_ascii=False, separators=(',', ':'))


summary = []
for lang, pre in LANG.items():
    for b in BOOKS:
        src = os.path.join(H, f'{pre}-{b}.min.json')
        if not os.path.exists(src):
            summary.append((lang, b, 'kaynak yok'))
            continue
        tx = {h['hadithnumber']: h['text'].strip() for h in json.load(open(src, encoding='utf-8'))['hadiths']}
        idx = json.load(open(f'data/hadith/{b}/index.json', encoding='utf-8'))
        oidx = {k: v for k, v in idx.items() if k != 'books'}
        oidx['language'] = lang
        oidx['source'] = f'fawazahmed0/hadith-api {pre}-{b}'
        oidx['books'] = []
        total = 0
        for bk in idx['books']:
            eng = json.load(open(f'data/hadith/{b}/{bk["file"]}', encoding='utf-8'))
            out = []
            for h in eng:
                t = tx.get(h['n'], '')
                if t:
                    e = {k: v for k, v in h.items() if k != 'text'}
                    e['text'] = t
                    out.append(e)
            rel = f'data/hadith_{lang}/{b}/{bk["file"]}'
            dump(rel, out)
            total += len(out)
            oidx['books'].append({**bk, 'count': len(out), 'bytes': os.path.getsize(rel)})
        oidx['total'] = total
        dump(f'data/hadith_{lang}/{b}/index.json', oidx, True)
        summary.append((lang, b, total, idx['total']))
for s in summary:
    print(s)
