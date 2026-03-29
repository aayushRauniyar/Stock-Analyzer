import requests

KEY    = 'PKK4HFWNTHQ6EVWNKEAEFSST5A'
SECRET = 'Adrwo9qSgrzuHaPLyjVD551jRz84nRyZXUmQcQkA1sFw'
URL    = 'https://paper-api.alpaca.markets/v2'

headers = {'APCA-API-KEY-ID': KEY, 'APCA-API-SECRET-KEY': SECRET}

print('=' * 50)
print('  ALPACA PAPER TRADING — CONNECTION TEST')
print('=' * 50)

# ── Account check ─────────────────────────────────
print('\n[1] Testing /v2/account endpoint...')
r = requests.get(f'{URL}/account', headers=headers, timeout=10)
print(f'    HTTP Status: {r.status_code}')

if r.status_code == 200:
    a = r.json()
    acct_num = a.get('account_number', 'N/A')
    status   = a.get('status', 'N/A')
    equity   = float(a.get('equity', 0))
    cash     = float(a.get('cash', 0))
    buying   = float(a.get('buying_power', 0))
    print(f'    Account # : {acct_num}')
    print(f'    Status    : {status}')
    print(f'    Equity    : ${equity:,.2f}')
    print(f'    Cash      : ${cash:,.2f}')
    print(f'    Buying Pwr: ${buying:,.2f}')
    print('\n    [OK] ALPACA CONNECTED SUCCESSFULLY')
    alpaca_ok = True
else:
    print(f'    [FAIL] Response: {r.text[:300]}')
    alpaca_ok = False

# ── Positions check ───────────────────────────────
if alpaca_ok:
    print('\n[2] Testing /v2/positions endpoint...')
    r2 = requests.get(f'{URL}/positions', headers=headers, timeout=10)
    print(f'    HTTP Status: {r2.status_code}')
    if r2.status_code == 200:
        positions = r2.json()
        print(f'    Open positions: {len(positions)}')
        for p in positions:
            sym = p.get('symbol')
            qty = p.get('qty')
            av  = float(p.get('avg_entry_price', 0))
            cur = float(p.get('current_price', 0))
            upl = float(p.get('unrealized_pl', 0))
            print(f'      {sym}: {qty} shares @ ${av:.2f} | now ${cur:.2f} | P&L ${upl:+.2f}')
        print('    [OK] Positions retrieved')
    else:
        print(f'    [FAIL] {r2.text[:200]}')

# ── Clock check ───────────────────────────────────
if alpaca_ok:
    print('\n[3] Testing /v2/clock endpoint...')
    r3 = requests.get(f'{URL}/clock', headers=headers, timeout=10)
    print(f'    HTTP Status: {r3.status_code}')
    if r3.status_code == 200:
        clk = r3.json()
        is_open = clk.get('is_open', False)
        nxt_open = clk.get('next_open', 'N/A')
        nxt_close = clk.get('next_close', 'N/A')
        print(f'    Market Open : {is_open}')
        print(f'    Next Open   : {nxt_open}')
        print(f'    Next Close  : {nxt_close}')
        print('    [OK] Clock endpoint working')

print('\n' + '=' * 50)
if alpaca_ok:
    print('  ALL ALPACA CHECKS PASSED')
else:
    print('  ALPACA CONNECTION FAILED')
print('=' * 50 + '\n')
