import requests

BASE = 'http://localhost:5000/api'

print('=' * 60)
print('  BACKEND ENDPOINT VERIFICATION')
print('=' * 60)

endpoints = [
    ('GET',  '/market-data'),
    ('GET',  '/signals'),
    ('GET',  '/positions'),
    ('GET',  '/portfolio'),
    ('GET',  '/market-status'),
    ('GET',  '/tax-log'),
]

for method, path in endpoints:
    try:
        r = requests.get(BASE + path, timeout=5)
        body = r.json()
        code = r.status_code
        status = 'OK  ' if code == 200 else 'WARN' if code == 404 else 'FAIL'
        keys = list(body.keys())[:4]
        print(f'  [{status}] {code} {method} {path:20s} keys={keys}')
    except Exception as e:
        print(f'  [ERR ] {method} {path:20s} -> {e}')

print()
print('  Testing POST /refresh (fetches live data + AI signals)...')
try:
    r = requests.post(BASE + '/refresh', timeout=30)
    if r.status_code == 200:
        d = r.json()
        print('  [OK  ] Refresh successful!')
        if 'market_data' in d:
            print('  Market Data:')
            for ticker, v in d['market_data'].items():
                price = v.get('price', '?')
                chg   = v.get('chg', 0)
                sign  = '+' if float(chg or 0) >= 0 else ''
                print(f'    {ticker}: ${price} ({sign}{chg}%)')
        if 'signals' in d:
            print('  AI Signals:')
            for ticker, s in d['signals'].items():
                sig  = s.get('signal', '?')
                conf = s.get('conf', '?')
                print(f'    {ticker}: {sig} @ {conf}% confidence')
    else:
        print(f'  [WARN] Refresh returned HTTP {r.status_code}: {r.text[:300]}')
except Exception as e:
    print(f'  [ERR ] Refresh failed: {e}')

print()
print('=' * 60)
print('  VERIFICATION COMPLETE')
print('=' * 60)
