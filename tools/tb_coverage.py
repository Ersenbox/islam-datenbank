import glob, json, sys, os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
tot = {}
for l in ['tr', 'en', 'de', 'fr']:
    keys = set()
    for fn in glob.glob(f'data/tarihte_bugun/{l}.json') + glob.glob(f'data/tarihte_bugun/parts/{l}_*.json'):
        try:
            keys |= set(json.load(open(fn, encoding='utf-8')).keys())
        except Exception:
            pass
    tot[l] = len(keys)
print(' '.join(f'{k}={v}' for k, v in tot.items()))
sys.exit(0 if all(v >= 366 for v in tot.values()) else 1)
