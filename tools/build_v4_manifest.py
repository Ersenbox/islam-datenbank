#!/usr/bin/env python3
"""v4: manifest.json guncelle - mevcut kayitlar korunur, degisen dosyalarin sha256/bytes/count degerleri yenilenir,
yeni dosyalar eklenir."""
import json, hashlib, os, sys
sys.stdout.reconfigure(encoding='utf-8')
m = json.load(open('manifest.json', encoding='utf-8'))
m['version'] = 4
m['updated'] = '2026-11-03'


def info(rel):
    b = open(rel, 'rb').read().replace(b'\r\n', b'\n')  # git LF olarak saklar
    return len(b), hashlib.sha256(b).hexdigest()


def count(rel):
    d = json.load(open(rel, encoding='utf-8'))
    if isinstance(d, list):
        return len(d)
    for k in ('ayetler', 'dualar'):
        if k in d:
            return len(d[k])
    return d.get('total')


byp = {f['path']: f for f in m['files']}
want = ['data/daily/ayetler.json', 'data/daily/dualar.json', 'data/daily/dualar_v2.json', 'data/daily/sunnetler.json']
for b in ['bukhari', 'muslim', 'abudawud', 'tirmidhi', 'nasai', 'ibnmajah']:
    for d in ('hadith', 'hadith_tr', 'hadith_fr'):
        p = f'data/{d}/{b}/index.json'
        if os.path.exists(p):
            want.append(p)
for p in want:
    e = byp.get(p) or {'path': p}
    e['count'] = count(p)
    e['bytes'], e['sha256'] = info(p)
    if p.endswith('sunnetler.json'):
        e['expected'] = 365
        e['complete'] = e['count'] == 365
    if '/hadith' in p:
        idx = json.load(open(p, encoding='utf-8'))
        e['books'] = len(idx['books'])
        e['download_bytes'] = sum(x['bytes'] for x in idx['books'])
        e['language'] = idx.get('language', 'en')
    if p not in byp:
        m['files'].append(e)
        byp[p] = e
m['notes'] = {
    'dualar_v2': "365 gun, sadece Kur'an + Sahih/Hasan hadis, daif yok. Eski dualar.json degistirilmedi (360 gun, bazi kaynaklari hatali).",
    'almanca': 'Almanca hadis cevirisi yok: uygulama Ingilizce metin + not gosterir. Ayetlerde almanca_meal = de.bubenheim.',
    'fransizca': 'Tirmizi icin Fransizca ceviri yok: Ingilizce metin + not.',
}
with open('manifest.json', 'w', encoding='utf-8', newline='\n') as f:
    json.dump(m, f, ensure_ascii=False, indent=1)
print('manifest v4', len(m['files']), 'dosya')
