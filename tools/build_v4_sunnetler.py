#!/usr/bin/env python3
"""v4: sunnetler.json'u 365 gune tamamlar. Mevcut 180 kayit DEGISMEZ, 181-365 eklenir.
Yeni kayitlar sadece Buhari ve Muslim'den (Sahih); hadis_metni fawazahmed0/hadith-api tur-* ceviresinden birebir.
Ayrica her kayda ingilizce/fransizca metin ve almanca not eklenir (yeni alanlar).
Aufruf: python build_v4_sunnetler.py <hsrc> [--dry]
"""
import json, sys, os, re
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))
from sunnet_konular import KONULAR, EN_RX, REJECT, RENAME, EXPL

H = sys.argv[1]
DRY = '--dry' in sys.argv
NAME = {'bukhari': 'Buhârî', 'muslim': 'Müslim'}
DE_NOT = 'Deutsche Übersetzung folgt – englischer Text.'


def L(p):
    return json.load(open(p, encoding='utf-8'))


src = {}
for k in NAME:
    E = {l: L(os.path.join(H, f'{l}-{k}.min.json')) for l in ('tur', 'eng', 'fra')}
    meta = E['eng']['metadata']
    sec_of = {}
    for sk, sd in meta['section_details'].items():
        for n in range(int(sd['hadithnumber_first']), int(sd['hadithnumber_last']) + 1):
            sec_of[n] = meta['sections'][sk].strip()
    idx = {l: {h['hadithnumber']: h for h in E[l]['hadiths']} for l in E}
    src[k] = (idx, sec_of)

p = 'data/daily/sunnetler.json'
old = L(p)
assert len(old) == 180
used = {(x['kaynak_adi'], str(x['hadis_numarasi']).split('.')[0]) for x in old}
used_titles = {x['baslik'].lower() for x in old}
new, miss, picked = [], [], []
for baslik, uyg, rx in KONULAR:
    if baslik.lower() in used_titles:
        continue
    r = re.compile(rx)
    er = re.compile(EN_RX[baslik]) if baslik in EN_RX else None
    best = None
    for k in ('bukhari', 'muslim'):
        idx, sec_of = src[k]
        for n, ht in idx['tur'].items():
            t = ht['text'].strip()
            if not (60 <= len(t) <= 1100):
                continue
            ee = idx['eng'].get(n)
            if not (r.search(t) or (er and ee and er.search(ee['text']))):
                continue
            num = ht.get('arabicnumber') or n
            num = ('%g' % num) if isinstance(num, float) else str(num)
            if (NAME[k], num.split('.')[0]) in used:
                continue
            he = idx['eng'].get(n)
            if not he or not he['text'].strip():
                continue
            cand = (len(t) + (0 if k == 'bukhari' else 50), k, n, num)
            if best is None or cand < best:
                best = cand
        if best and best[1] == 'bukhari':
            break
    if not best:
        miss.append(baslik)
        continue
    _, k, n, num = best
    if baslik in REJECT:
        used.add((NAME[k], num.split('.')[0]))  # yanlis eslesen hadis de tekrar secilmesin
        continue
    if baslik in RENAME:
        baslik, uyg = RENAME[baslik]
    picked.append((baslik, uyg, k, n, num))
    used.add((NAME[k], num.split('.')[0]))
    used_titles.add(baslik.lower())

# Numara ile secilenler
for baslik, uyg, k, want in EXPL:
    idx, sec_of = src[k]
    hit = None
    for n, he in idx['eng'].items():
        a = he.get('arabicnumber') or n
        if (k == 'bukhari' and n == want) or (k == 'muslim' and int(float(a)) == want):
            hit = (n, a)
            break
    if not hit:
        miss.append('EXPL-yok:' + baslik); continue
    n, a = hit
    num = ('%g' % a) if isinstance(a, float) else str(a)
    if (NAME[k], num.split('.')[0]) in used or baslik.lower() in used_titles:
        miss.append('EXPL-kullanilmis:' + baslik); continue
    t = idx['tur'].get(n, {}).get('text', '').strip()
    if len(t) < 40 or 'önceki hadis' in t.lower():
        miss.append('EXPL-tr-yok:' + baslik); continue
    picked.append((baslik, uyg, k, n, num))
    used.add((NAME[k], num.split('.')[0]))
    used_titles.add(baslik.lower())

for baslik, uyg, k, n, num in picked:
    idx, sec_of = src[k]
    hf = idx['fra'].get(n)
    new.append({'baslik': baslik, 'sunnet_uygulamasi': uyg, 'hadis_metni': idx['tur'][n]['text'].strip(),
                'kaynak_adi': NAME[k], 'bolum': sec_of.get(n, ''), 'hadis_numarasi': num, 'derece': 'Sahih',
                'hadis_metni_en': idx['eng'][n]['text'].strip(),
                'hadis_metni_fr': hf['text'].strip() if hf and hf['text'].strip() else idx['eng'][n]['text'].strip(),
                'hadis_metni_de_not': DE_NOT,
                'kaynak_url': f'https://sunnah.com/{k}:{num.split(".")[0]}',
                'metin_kaynagi': f'fawazahmed0/hadith-api ({k}: tur/eng/fra)'})
print('yeni', len(new), 'bulunamayan', len(miss), miss)
if DRY:
    for i, x in enumerate(new, 181):
        en = re.sub(r'\s+', ' ', x['hadis_metni_en'])
        print(i, x['baslik'], '|', x['kaynak_adi'], x['hadis_numarasi'], '|', en[:200])
    sys.exit()
need = 365 - 180
assert len(new) >= need, len(new)
out = list(old) + [{'gun': 181 + i, **x} for i, x in enumerate(new[:need])]
with open(p, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print('ok', len(out))
