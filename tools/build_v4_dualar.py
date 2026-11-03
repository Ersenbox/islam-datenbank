#!/usr/bin/env python3
"""v4: data/daily/dualar_v2.json - 365 gunluk, kaynagi dogrulanmis dualar.
Kaynaklar:
  - Kur'an dualari: alquran.cloud (quran-uthmani, tr.diyanet, en.sahih, de.bubenheim, fr.hamidullah)
  - Hadis dualari: fawazahmed0/hadith-api (ara/tur/eng/fra), sadece dua bolumleri,
    Buhari/Muslim (Sahih) veya tum muhaddis derecelendirmeleri Sahih/Hasan olanlar. Daif YOK.
Eski dualar.json'a dokunulmaz.
Aufruf: python build_v4_dualar.py <hsrc> <qsrc>
"""
import json, sys, os, re, unicodedata
sys.stdout.reconfigure(encoding="utf-8")

H, Q = sys.argv[1], sys.argv[2]
DE_NOT = 'Deutsche Übersetzung folgt – englischer Text.'
FR_NOT = 'Traduction française non disponible – texte anglais.'


def L(p):
    return json.load(open(p, encoding='utf-8'))


def strip_ar(s):
    s = unicodedata.normalize('NFKD', s)
    s = re.sub('[ؐ-ًؚ-ٰٟۖ-ۭـ]', '', s)
    for a, b in (('ٱ', 'ا'), ('أ', 'ا'), ('إ', 'ا'), ('آ', 'ا')):
        s = s.replace(a, b)
    return s


# ---------- Kur'an ----------
QREFS = ['1:6', '2:127', '2:128', '2:201', '2:250', '2:286', '3:8', '3:9', '3:16', '3:38', '3:53', '3:147',
         '3:191', '3:192', '3:193', '3:194', '5:83', '7:23', '7:47', '7:89', '7:126', '7:151', '10:85', '10:86',
         '12:101', '14:40', '14:41', '17:24', '17:80', '18:10', '20:25', '20:114', '21:83', '21:87', '21:89',
         '23:29', '23:97', '23:109', '23:118', '25:65', '25:74', '26:83', '26:85', '27:19', '28:16', '28:21',
         '28:24', '37:100', '40:7', '40:8', '46:15', '59:10', '60:4', '60:5', '66:8', '66:11', '71:28', '44:12',
         '2:285']
QREFS = list(dict.fromkeys(QREFS))
QE = {'arapca': 'quran-uthmani', 'turkce': 'tr.diyanet', 'ingilizce': 'en.sahih', 'almanca': 'de.bubenheim',
      'fransizca': 'fr.hamidullah'}
qt = {}
for f, e in QE.items():
    d = L(os.path.join(Q, e + '.json'))['data']
    for s in d['surahs']:
        for a in s['ayahs']:
            r = f'{s["number"]}:{a["numberInSurah"]}'
            qt.setdefault(r, {})[f] = a['text'].strip()
            qt[r]['sure'] = s['englishName']
quran = []
for r in QREFS:
    t = qt[r]
    quran.append({'tur': 'kuran', 'arapca': t['arapca'], 'turkce': t['turkce'], 'ingilizce': t['ingilizce'],
                  'almanca': t['almanca'], 'fransizca': t['fransizca'], 'kaynak_adi': "Kur'ân-ı Kerîm",
                  'bolum': t['sure'], 'numara': r, 'derece': "Kur'ân",
                  'kaynak_url': 'https://quran.com/' + r.replace(':', '/'),
                  'metin_kaynagi': 'alquran.cloud: ' + ', '.join(QE.values())})

# ---------- Hadis ----------
ORDER = ['Buhârî', 'Müslim', 'Tirmizî', 'İbn Mâce', 'Ebû Dâvûd', 'Nesâî']
BOOKS = [('bukhari', 'Buhârî', ['80']), ('muslim', 'Müslim', ['48']), ('tirmidhi', 'Tirmizî', ['48']),
         ('ibnmajah', 'İbn Mâce', ['34']), ('abudawud', 'Ebû Dâvûd', None), ('nasai', 'Nesâî', ['50'])]
BAD = re.compile(r"da.?if|munkar|maudu|mawdu|shadh|batil|fabricat|weak", re.I)
DUA = re.compile('اللهم|ربنا|رب اغفر|اعوذ ب|لا اله الا الله|سبحان الله|استغفر الله|حسبنا الله|يا حي يا قيوم')
STRICT = re.compile('اللهم')
hadis, seen = [], set()
for key, tr_name, secs in BOOKS:
    E = {}
    for l in ('ara', 'eng', 'tur', 'fra'):
        p = os.path.join(H, f'{l}-{key}.min.json')
        if os.path.exists(p):
            E[l] = L(p)
    meta = E['eng']['metadata']
    if secs is None:
        secs = [k for k, v in meta['sections'].items() if 'witr' in v.lower()]
    dua_secs = set(secs)
    secs = list(secs) + [k for k in meta['sections'] if k not in dua_secs and k in meta['section_details']]
    idx = {l: {h['hadithnumber']: h for h in E[l]['hadiths']} for l in E}
    for sk in secs:
        sd = meta['section_details'][sk]
        for n, he in idx['eng'].items():
            if not (sd['hadithnumber_first'] <= n <= sd['hadithnumber_last']):
                continue
            ha, ht = idx['ara'].get(n), idx['tur'].get(n)
            hf = idx.get('fra', {}).get(n)
            if not (ha and ht and he['text'].strip() and ha['text'].strip() and ht['text'].strip()):
                continue
            grades = he.get('grades') or []
            if key in ('bukhari', 'muslim'):
                derece = 'Sahih'
            else:
                if not grades or any(BAD.search(g['grade']) for g in grades):
                    continue
                derece = ' / '.join(sorted({g['grade'].strip() for g in grades}))
            ar = strip_ar(ha['text'])
            m = DUA.search(ar) if sk in dua_secs else STRICT.search(ar)
            if not m:
                continue
            sig = re.sub(r'\W', '', ar[m.start():m.start() + 70])
            if sig in seen or len(ht['text']) > 1500:
                continue
            seen.add(sig)
            num = he.get('arabicnumber') or n
            num = ('%g' % num) if isinstance(num, float) else str(num)
            has_fr = bool(hf and hf['text'].strip())
            e = {'tur': 'hadis', 'arapca': ha['text'].strip(), 'turkce': ht['text'].strip(),
                 'ingilizce': he['text'].strip(), 'almanca': he['text'].strip(), 'almanca_not': DE_NOT,
                 'fransizca': hf['text'].strip() if has_fr else he['text'].strip()}
            if not has_fr:
                e['fransizca_not'] = FR_NOT
            e.update({'kaynak_adi': tr_name, 'bolum': meta['sections'][sk].strip(), 'numara': num,
                      'derece': derece, 'kaynak_url': f'https://sunnah.com/{key}:{num.split(".")[0]}',
                      'metin_kaynagi': f'fawazahmed0/hadith-api ({key}: ara/tur/eng/fra)'})
            e['_prio'] = 0 if sk in dua_secs else 1
            hadis.append(e)
print('kuran', len(quran), 'hadis aday', len(hadis))
need = 365
hadis.sort(key=lambda x: (x['_prio'], len(x['turkce']) > 600, ORDER.index(x['kaynak_adi'])))
hadis = hadis[:need - len(quran)]
assert len(quran) + len(hadis) == need, (len(quran), len(hadis))
out, qi, hi = [], 0, 0
step = need / len(quran)
for g in range(need):
    if qi < len(quran) and g >= int(qi * step):
        out.append(quran[qi]); qi += 1
    else:
        out.append(hadis[hi]); hi += 1
out = [{'gun': i + 1, **{k: v for k, v in x.items() if k != '_prio'}} for i, x in enumerate(out)]
doc = {'aciklama': "365 günlük dualar (v2). Sadece doğrulanmış kaynaklar: Kur'ân ve Sahih/Hasan hadisler, daif yok. "
                   "Almanca hadis metni yoktur: İngilizce metin + not gösterilir.",
       'adet': len(out), 'dualar': out}
with open('data/daily/dualar_v2.json', 'w', encoding='utf-8', newline='\n') as f:
    json.dump(doc, f, ensure_ascii=False, indent=1)
from collections import Counter
print('ok', len(out), Counter(x['kaynak_adi'] for x in out))
