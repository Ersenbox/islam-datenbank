#!/usr/bin/env python3
"""v4.1: sunnetler.json 1-180 kayitlarina EN/FR hadis metni ekler (yeni alanlar; mevcut alanlar degismez).
Eslestirme: kaynak_adi + hadis_numarasi (Muslim: arabicnumber tam kismi). Kur'an kaydi atlanir.
Aufruf: python build_v4_1_sunnet_ceviri.py <hsrc> [--dry]
"""
import json, os, sys
sys.stdout.reconfigure(encoding='utf-8')
H = sys.argv[1]
DRY = '--dry' in sys.argv
MAP = {'Buhârî': 'bukhari', 'Müslim': 'muslim', 'Ebû Dâvûd': 'abudawud', 'Tirmizî': 'tirmidhi',
       'Nesâî': 'nasai', 'İbn Mâce': 'ibnmajah'}
DE_NOT = 'Deutsche Übersetzung folgt – englischer Text.'
idx = {}
for tr, k in MAP.items():
    for l in ('eng', 'fra'):
        p = os.path.join(H, f'{l}-{k}.min.json')
        if not os.path.exists(p):
            continue
        d = {}
        for h in json.load(open(p, encoding='utf-8'))['hadiths']:
            if k == 'muslim':
                a = h.get('arabicnumber')
                if a is None:
                    continue
                key = int(float(a))
            else:
                key = int(h['hadithnumber'])
            if h['text'].strip() and key not in d:
                d[key] = (h['text'].strip(), h['hadithnumber'])
        idx[(k, l)] = d
p = 'data/daily/sunnetler.json'
s = json.load(open(p, encoding='utf-8'))
done, miss = 0, []
for x in s[:180]:
    k = MAP.get(x['kaynak_adi'])
    try:
        n = int(str(x['hadis_numarasi']).split('.')[0])
    except ValueError:
        n = None
    if not k or n is None:
        miss.append((x['gun'], x['kaynak_adi'], x['hadis_numarasi'])); continue
    en = idx.get((k, 'eng'), {}).get(n)
    if not en:
        miss.append((x['gun'], x['kaynak_adi'], x['hadis_numarasi'])); continue
    fr = idx.get((k, 'fra'), {}).get(n)
    if DRY:
        if x['gun'] % 15 == 1:
            print(x['gun'], x['kaynak_adi'], n, '| TR:', x['hadis_metni'][:90], '| EN:', en[0][:110])
        continue
    x['hadis_metni_en'] = en[0]
    x['hadis_metni_fr'] = fr[0] if fr else en[0]
    x['hadis_metni_de_not'] = DE_NOT
    x['kaynak_url'] = f'https://sunnah.com/{k}:{n}'
    x['metin_kaynagi'] = f'fawazahmed0/hadith-api ({k}: eng/fra) – numara ile eslestirildi'
    done += 1
print('eklendi', done, 'eslesmeyen', len(miss), miss)
if not DRY:
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(s, f, ensure_ascii=False, indent=1)
