#!/usr/bin/env python3
"""Tarihte Bugün - sadece KANITLI olaylar.
Kaynak: Wikimedia "On this day" (selected + events). Her olay için olayın bağlı makalelerinden biri
indirilir ve metninde tam tarih (ör. "3 Kasım 1957") geçiyorsa olay kabul edilir. Link = o makale.
Kanıtı bulunamayan olay YAZILMAZ.
Çıktı: data/tarihte_bugun/<dil>.json  {"MM-DD": [{"year","text","cat","src","url"}]}
Aufruf: python build_tarihte_bugun.py tr [en de fr]
"""
import json, os, re, sys, time, urllib.parse, urllib.request
from datetime import date, timedelta
sys.stdout.reconfigure(encoding='utf-8')
UA = 'IslamTakvimi26-datenbank/1.0 (https://github.com/Ersenbox/islam-datenbank)'
MAX_LEN = 250000  # bundan büyük (genel) makaleler kanıt için kullanılmaz
MAX_OUT = 7

MON = {
 'tr': ['Ocak','Şubat','Mart','Nisan','Mayıs','Haziran','Temmuz','Ağustos','Eylül','Ekim','Kasım','Aralık'],
 'en': ['January','February','March','April','May','June','July','August','September','October','November','December'],
 'de': ['Januar','Februar','März','April','Mai','Juni','Juli','August','September','Oktober','November','Dezember'],
 'fr': ['janvier','février','mars','avril','mai','juin','juillet','août','septembre','octobre','novembre','décembre'],
}
def rx(p): return re.compile(p, re.I)
RULES = {
 'tr': (rx(r"türkiye|\btürk|osmanlı|istanbul|ankara|izmir|atatürk|selçuklu|tbmm|anadolu|kıbrıs|tanzimat|padişah|hümayun|\bsultan|sadrazam|beylik|chp|inönü|menderes|ecevit|demirel|özal|türkiye cumhuriyeti|cumhuriyetin ilanı|kurtuluş savaşı|milli mücadele|millî mücadele|çanakkale|malazgirt|viyana kuşatma|mohaç|preveze|kosova savaşı|niğbolu|ankara savaşı|lozan|sevr"),
        rx(r"\bislam|müslüman|\bcami|halife|mekke|medine|\bhac\b|kur'an|emevi|abbasi|endülüs|kudüs|hicri|peygamber|selahaddin|memlük|fatımi|\barap"),
        rx(r"futbol|\bmaç|olimpiyat|şampiyona|fifa|uefa|\bfilm|albüm|şarkı|\bdizi|oscar|grammy|eurovision|\bkupa|turnuva|\boyun|konsol|basketbol|voleybol|tenis|formula|yarış|müzik|\bgrup|tiyatro|sinema|televizyon")),
 'en': (rx(r"turkey|turkish|ottoman|istanbul|constantinople|ankara|atatürk|seljuk|anatolia|cyprus|sultan|gallipoli|manzikert|mohács|lausanne"),
        rx(r"\bislam|muslim|mosque|caliph|mecca|medina|\bhajj|qur'?an|umayyad|abbasid|al-andalus|jerusalem|saladin|mamluk|fatimid|\barab"),
        rx(r"football|soccer|olympic|championship|fifa|uefa|\bfilm|album|\bsong|television|oscar|grammy|eurovision|\bcup\b|tournament|video game|basketball|tennis|formula|\brace\b|music|\bband\b|singer|actor|theatre|cinema")),
 'de': (rx(r"türkei|türkisch|osmani|istanbul|konstantinopel|ankara|atatürk|seldschuk|anatolien|zypern|sultan|gallipoli|mohács|lausanne"),
        rx(r"\bislam|muslim|moschee|kalif|mekka|medina|\bhadsch|koran|umayyad|omaijad|abbasid|al-andalus|jerusalem|saladin|mamluk|fatimid|\baraber|arabisch"),
        rx(r"fußball|olympi|meisterschaft|fifa|uefa|\bfilm|album|\blied|\bsong|fernseh|oscar|grammy|eurovision|pokal|turnier|videospiel|basketball|tennis|formel|rennen|musik|\bband\b|sänger|schauspiel|theater|kino")),
 'fr': (rx(r"turquie|\bturc|ottoman|istanbul|constantinople|ankara|atatürk|seldjoukide|anatolie|chypre|sultan|gallipoli|mohács|lausanne"),
        rx(r"\bislam|musulman|mosquée|calife|la mecque|médine|\bhajj|coran|omeyyade|abbasside|al-andalus|jérusalem|saladin|mamelouk|fatimide|\barabe"),
        rx(r"football|olympi|championnat|fifa|uefa|\bfilm|album|chanson|télévis|oscar|grammy|eurovision|\bcoupe|tournoi|jeu vidéo|basket|tennis|formule|course|musique|groupe|chanteu|acteur|théâtre|cinéma")),
}

def http(url, tries=6):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'application/json'})
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and i < tries - 1:
                time.sleep(10 * (i + 1)); continue
            if e.code == 404:
                return {}
            raise
        except Exception:
            if i < tries - 1:
                time.sleep(5 * (i + 1)); continue
            raise
    return {}

def phrases(lang, d, m, y):
    M = MON[lang][m - 1]
    if lang == 'tr': return [f'{d} {M} {y}']
    if lang == 'en': return [f'{M} {d}, {y}', f'{d} {M} {y}']
    if lang == 'de': return [f'{d}. {M} {y}']
    if lang == 'fr': return [f'{"1er" if d == 1 else d} {M} {y}', f'{d} {M} {y}']

LINK = re.compile(r'\[\[(?:[^|\]]*\|)?([^\]]*)\]\]')
def norm(t):
    t = t.replace('&nbsp;', ' ').replace(' ', ' ').replace('{{0}}', '')
    t = LINK.sub(r'\1', t)
    t = re.sub(r"'''?", '', t)
    return re.sub(r'[ \t]+', ' ', t)

def api(lang, params):
    q = urllib.parse.urlencode({**params, 'format': 'json', 'formatversion': 2})
    time.sleep(0.25)
    return http(f'https://{lang}.wikipedia.org/w/api.php?{q}')

def page_info(lang, titles):
    out = {}
    for i in range(0, len(titles), 50):
        r = api(lang, {'action': 'query', 'prop': 'info', 'titles': '|'.join(titles[i:i + 50])})
        for p in r.get('query', {}).get('pages', []):
            if 'missing' not in p: out[p['title']] = p.get('length', 0)
    return out

def page_text(lang, titles):
    out = {}
    for i in range(0, len(titles), 10):
        r = api(lang, {'action': 'query', 'prop': 'revisions', 'rvprop': 'content', 'rvslots': 'main', 'titles': '|'.join(titles[i:i + 10])})
        for p in r.get('query', {}).get('pages', []):
            try: out[p['title']] = norm(p['revisions'][0]['slots']['main']['content'])
            except Exception: pass
    return out

def build_day(lang, m, d):
    tr_rx, is_rx, ex_rx = RULES[lang]
    base = f'https://api.wikimedia.org/feed/v1/wikipedia/{lang}/onthisday/%s/{m:02d}/{d:02d}'
    time.sleep(0.25); sel = http(base % 'selected').get('selected', [])
    time.sleep(0.25); evs = http(base % 'events').get('events', [])
    cands, seen = [], set()
    for is_sel, arr in ((True, sel), (False, evs)):
        for x in arr:
            text = (x.get('text') or '').strip(); y = x.get('year')
            if not text or y is None or text in seen: continue
            seen.add(text)
            pages = [p['titles']['normalized'] for p in x.get('pages', []) if p.get('titles')]
            hay = text + ' ' + ' '.join(pages[:3])
            if ex_rx.search(hay): continue
            cat = 'TR' if tr_rx.search(hay) else 'ISLAM' if is_rx.search(hay) else ('WORLD' if is_sel or (isinstance(y, int) and y < 1950) else None)
            if cat: cands.append({'year': y, 'text': text, 'cat': cat, 'pages': pages})
    order = {'TR': 0, 'ISLAM': 1, 'WORLD': 2}
    cands.sort(key=lambda c: order[c['cat']])
    cands = cands[:30]
    titles = sorted({p for c in cands for p in c['pages']})
    lens = page_info(lang, titles)
    small = {t for t in titles if 0 < lens.get(t, 0) <= MAX_LEN}
    texts = {}
    out, counts = [], {'TR': 0, 'ISLAM': 0, 'WORLD': 0}
    for c in cands:
        lim = 3 if c['cat'] != 'WORLD' else MAX_OUT
        if counts[c['cat']] >= lim or len(out) >= MAX_OUT: continue
        # makaleleri sadece gerektiğinde indir (küçükten büyüğe)
        need = sorted([p for p in c['pages'] if p in small and p not in texts], key=lambda t: lens.get(t, 0))[:4]
        if need:
            texts.update(page_text(lang, need))
            for p in need: texts.setdefault(p, '')
        ph = phrases(lang, d, m, abs(c['year']) if isinstance(c['year'], int) else c['year'])
        src = next((p for p in c['pages'] if p in texts and any(f in texts[p] for f in ph)), None)
        if not src: continue  # kanıt yok -> gösterilmez
        if any(o['year'] == str(c['year']) and o['src'] == src for o in out): continue  # aynı olay iki kez
        out.append({'year': str(c['year']), 'text': c['text'], 'cat': c['cat'], 'src': src,
                    'url': f'https://{lang}.m.wikipedia.org/wiki/' + urllib.parse.quote(src.replace(' ', '_'))})
        counts[c['cat']] += 1
    out.sort(key=lambda e: (order[e['cat']], -(int(e['year']) if e['year'].lstrip('-').isdigit() else 0)))
    return out

def main_part(lang, sm, em):
    # paralel parça: aylar sm..em -> data/tarihte_bugun/parts/<dil>_<sm>_<em>.json
    os.makedirs('data/tarihte_bugun/parts', exist_ok=True)
    path = f'data/tarihte_bugun/parts/{lang}_{sm}_{em}.json'
    res = json.load(open(path, encoding='utf-8')) if os.path.exists(path) else {}
    full = f'data/tarihte_bugun/{lang}.json'
    if os.path.exists(full):
        try:
            for k, v in json.load(open(full, encoding='utf-8')).items():
                if sm <= int(k[:2]) <= em: res.setdefault(k, v)
        except Exception:
            pass
    day = date(2024, sm, 1)
    while day.year == 2024 and day.month <= em:
        k = f'{day.month:02d}-{day.day:02d}'
        if k not in res:
            try:
                res[k] = build_day(lang, day.month, day.day)
            except Exception as e:
                print('HATA', lang, k, e, flush=True)
            with open(path, 'w', encoding='utf-8', newline=chr(10)) as f:
                json.dump(dict(sorted(res.items())), f, ensure_ascii=False, separators=(',', ':'))
            print(lang, k, len(res.get(k, [])), flush=True)
        day += timedelta(days=1)
    print('FERTIG-PART', lang, sm, em, len(res), flush=True)


def merge(lang):
    res = {}
    full = f'data/tarihte_bugun/{lang}.json'
    if os.path.exists(full): res.update(json.load(open(full, encoding='utf-8')))
    d = 'data/tarihte_bugun/parts'
    for fn in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if fn.startswith(lang + '_'): res.update(json.load(open(os.path.join(d, fn), encoding='utf-8')))
    with open(full, 'w', encoding='utf-8', newline=chr(10)) as f:
        json.dump(dict(sorted(res.items())), f, ensure_ascii=False, separators=(',', ':'))
    print('merge', lang, len(res), 'gün, boş:', sum(1 for v in res.values() if not v))


def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--part':
        return main_part(sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))
    if len(sys.argv) > 1 and sys.argv[1] == '--merge':
        for l in sys.argv[2:]: merge(l)
        return
    langs = sys.argv[1:] or ['tr']
    os.makedirs('data/tarihte_bugun', exist_ok=True)
    for lang in langs:
        path = f'data/tarihte_bugun/{lang}.json'
        res = json.load(open(path, encoding='utf-8')) if os.path.exists(path) else {}
        day = date(2024, 1, 1)
        while day.year == 2024:
            k = f'{day.month:02d}-{day.day:02d}'
            if k not in res:
                try:
                    res[k] = build_day(lang, day.month, day.day)
                except Exception as e:
                    print('HATA', lang, k, e, flush=True)
                if True:  # her gün kaydet
                    with open(path, 'w', encoding='utf-8', newline='\n') as f:
                        json.dump(dict(sorted(res.items())), f, ensure_ascii=False, separators=(',', ':'))
                print(lang, k, len(res.get(k, [])), flush=True)
            day += timedelta(days=1)
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(dict(sorted(res.items())), f, ensure_ascii=False, separators=(',', ':'))
        empty = sum(1 for v in res.values() if not v)
        print('FERTIG', lang, len(res), 'gün, boş:', empty, 'ort:', round(sum(len(v) for v in res.values()) / max(1, len(res)), 1), flush=True)

if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[1] == '--day':
        lang, md = sys.argv[2], sys.argv[3]
        m, d = map(int, md.split('-'))
        for e in build_day(lang, m, d): print(e['cat'], e['year'], e['text'][:80], '| kanıt:', e['src'])
    else:
        main()
