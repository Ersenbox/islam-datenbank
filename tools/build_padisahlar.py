#!/usr/bin/env python3
"""36 Osmanlı padişahı - kaynaklı detay bilgisi.
 - Özet: Türkçe Wikipedia giriş bölümü (düz metin)
 - Seferler/Savaşlar/Fetihler: Türkçe Wikipedia makalesinin bölüm başlıkları (yıl veya sefer/savaş/fetih içerenler)
 - Yaptırdığı eserler: Wikidata P88 ("yaptıran / commissioned by")
Çıktı: data/osmanli_padisahlar.json
"""
import json, re, sys, time, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding='utf-8')
UA = 'IslamTakvimi26-datenbank/1.0 (https://github.com/Ersenbox/islam-datenbank)'
TITLES = ['I. Osman', 'Orhan Gazi', 'I. Murad', 'I. Bayezid', 'I. Mehmed', 'II. Murad', 'II. Mehmed', 'II. Bayezid',
          'I. Selim', 'I. Süleyman', 'II. Selim', 'III. Murad', 'III. Mehmed', 'I. Ahmed', 'I. Mustafa', 'II. Osman',
          'IV. Murad', 'İbrahim (Osmanlı padişahı)', 'IV. Mehmed', 'II. Süleyman', 'II. Ahmed', 'II. Mustafa',
          'III. Ahmed', 'I. Mahmud', 'III. Osman', 'III. Mustafa', 'I. Abdülhamid', 'III. Selim', 'IV. Mustafa',
          'II. Mahmud', 'Abdülmecid', 'Abdülaziz', 'V. Murad', 'II. Abdülhamid', 'V. Mehmed', 'VI. Mehmed']
CAMPAIGN = re.compile(r'sefer|fetih|fethi|savaş|kuşatma|muharebe|zafer|harb|isyan|antlaşma|ilhak|teslim|\(1[2-9]\d\d', re.I)
LINKRX = re.compile(r'muharebesi|kuşatması|seferi|savaşı|fethi|antlaşması|zaferi|harbi', re.I)
SKIP = re.compile(r'kaynakça|notlar|dış bağlantılar|ayrıca bakınız|popüler kültür|ailesi|eşleri|çocukları|kaynak|galeri', re.I)


def http(url):
    for i in range(5):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'application/json'})
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.load(r)
        except Exception:
            time.sleep(5 * (i + 1))
    raise RuntimeError(url)


def api(params):
    time.sleep(0.3)
    q = urllib.parse.urlencode({**params, 'format': 'json', 'formatversion': 2})
    return http('https://tr.wikipedia.org/w/api.php?' + q)


def sparql(q):
    time.sleep(1)
    return http('https://query.wikidata.org/sparql?format=json&query=' + urllib.parse.quote(q))['results']['bindings']


# saltanat yılları (uygulamadaki listeden) - yılı yazılı olup dönem dışında kalan olaylar çıkarılır
APP = r'C:/Users/mckin/AndroidStudioProjects/IslamTakvimi26/app/src/main/java/com/example/data/provider/OttomanHistoryData.kt'
REIGN = {}
for mm in re.finditer(r'number = (\d+),\s*name = "[^"]*",\s*reignYears = "(\d{4})\s*-\s*(\d{4})"', open(APP, encoding='utf-8').read()):
    REIGN[int(mm.group(1))] = (int(mm.group(2)), int(mm.group(3)))


def in_reign(no, text):
    yrs = [int(y) for y in re.findall(r'(1[2-9]\d\d)', text)]
    if not yrs or no not in REIGN:
        return True
    a, b = REIGN[no]
    return any(a - 1 <= y <= b + 1 for y in yrs)


out = []
for no, t in enumerate(TITLES, 1):
    r = api({'action': 'query', 'prop': 'extracts|pageprops|info', 'exintro': 1, 'explaintext': 1, 'redirects': 1,
             'inprop': 'url', 'titles': t})
    p = r['query']['pages'][0]
    title = p['title']
    qid = p.get('pageprops', {}).get('wikibase_item', '')
    ozet = re.sub(r'\n{2,}', '\n\n', p.get('extract', '').strip())
    parsed = api({'action': 'parse', 'page': title, 'prop': 'sections|wikitext'})['parse']
    secs = parsed['sections']
    seferler = []
    # metindeki bağlantılı savaş/kuşatma/sefer/fetih makaleleri (metindeki sırayla)
    wt = parsed.get('wikitext', '')
    wt = wt.split('== Kaynakça')[0].split('==Kaynakça')[0]
    for mm in re.finditer(r'\[\[([^\]|#]+)(?:\|[^\]]*)?\]\]', wt):
        link = mm.group(1).strip()
        if LINKRX.search(link) and link not in seferler and in_reign(no, link):
            seferler.append(link)
    # yılı olmayan bağlantılar: Wikidata tarihi (P585/P580/P582) ile saltanat kontrolü; tarihi yoksa çıkar
    noyear = [l for l in seferler if not re.search(r'\b1[2-9]\d\d\b', l)]
    if noyear and no in REIGN:
        qmap = {}
        for i in range(0, len(noyear), 50):
            rr = api({'action': 'query', 'prop': 'pageprops', 'redirects': 1, 'titles': '|'.join(noyear[i:i + 50])})
            norm = {n['from']: n['to'] for n in rr['query'].get('normalized', []) + rr['query'].get('redirects', [])}
            byt = {pg['title']: pg.get('pageprops', {}).get('wikibase_item') for pg in rr['query']['pages']}
            for l in noyear[i:i + 50]:
                t2 = norm.get(norm.get(l, l), norm.get(l, l))
                if byt.get(t2):
                    qmap[l] = byt[t2]
        years = {}
        if qmap:
            vals = ' '.join('wd:' + q for q in set(qmap.values()))
            rows = sparql('SELECT ?x (MIN(YEAR(?d)) AS ?y) (MAX(YEAR(?d)) AS ?z) WHERE { VALUES ?x { %s } '
                          '?x wdt:P585|wdt:P580|wdt:P582 ?d } GROUP BY ?x' % vals)
            for b in rows:
                years[b['x']['value'].rsplit('/', 1)[1]] = (int(b['y']['value']), int(b['z']['value']))
        a, b2 = REIGN[no]
        keep = []
        for l in seferler:
            if l in noyear:
                yz = years.get(qmap.get(l, ''), None)
                if not yz or yz[1] < a - 1 or yz[0] > b2 + 1:
                    continue
            keep.append(l)
        seferler = keep
    for s in secs:
        line = re.sub(r'<[^>]+>', '', s['line']).strip()
        if SKIP.search(line):
            continue
        if CAMPAIGN.search(line) and line not in seferler and in_reign(no, line):
            seferler.append(line)
    eserler = []
    if qid:
        rows = sparql(f'SELECT DISTINCT ?x ?xLabel WHERE {{ ?x wdt:P88 wd:{qid} . '
                      f'SERVICE wikibase:label {{ bd:serviceParam wikibase:language "tr,en". }} }}')
        for b in rows:
            lab = b['xLabel']['value']
            if re.fullmatch(r'Q\d+', lab) or re.search(r'ferman|decree|charter|waqfiyya|tiem|ssm |\(', lab, re.I):
                continue
            if lab not in eserler:
                eserler.append(lab)
    url = 'https://tr.m.wikipedia.org/wiki/' + urllib.parse.quote(title.replace(' ', '_'))
    out.append({'no': no, 'saltanat': '%d - %d' % REIGN[no] if no in REIGN else '', 'wiki_baslik': title, 'wikidata': qid, 'ozet': ozet, 'seferler': seferler[:30],
                'eserler': sorted(eserler), 'kaynak_url': url,
                'kaynak': 'Türkçe Vikipedi (özet, bölüm başlıkları) + Wikidata P88 (eserler)'})
    print(no, title, qid, 'özet', len(ozet), 'sefer', len(seferler), 'eser', len(eserler), flush=True)

with open('data/osmanli_padisahlar.json', 'w', encoding='utf-8', newline='\n') as f:
    json.dump({'aciklama': '36 Osmanlı padişahı - Vikipedi/Wikidata kaynaklı detaylar', 'padisahlar': out}, f,
              ensure_ascii=False, indent=1)
print('ok', len(out))
