#!/usr/bin/env python3
"""v4: ayetler.json'a ingilizce/almanca/fransizca meal alanlari ekler (mevcut alanlara dokunmaz).
Aufruf: python build_v4_ayetler.py <qsrc_ordner>   (alquran.cloud /v1/quran/<edition> JSON'lari)
"""
import json, sys, os
q = sys.argv[1]
ED = {'ingilizce_meal': 'en.sahih', 'almanca_meal': 'de.bubenheim', 'fransizca_meal': 'fr.hamidullah'}
tx = {}
for f, e in ED.items():
    d = json.load(open(os.path.join(q, e + '.json'), encoding='utf-8'))['data']
    tx[f] = {a['number']: a['text'].strip() for s in d['surahs'] for a in s['ayahs']}
    tx[f]['_ref'] = {a['number']: (s['number'], a['numberInSurah']) for s in d['surahs'] for a in s['ayahs']}
p = 'data/daily/ayetler.json'
doc = json.load(open(p, encoding='utf-8'))
for x in doc['ayetler']:
    g = x['global_ayet_no']
    for f, e in ED.items():
        assert tx[f]['_ref'][g] == (x['sure_no'], x['ayet_no']), (x['referans'], tx[f]['_ref'][g])
        x[f] = tx[f][g]
        x[f + '_kaynagi'] = 'alquran.cloud/' + e
with open(p, 'w', encoding='utf-8', newline='\n') as fh:
    json.dump(doc, fh, ensure_ascii=False, indent=1)
print('ok', len(doc['ayetler']))
