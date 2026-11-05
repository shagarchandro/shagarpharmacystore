# A modest load and concurrency check against the REAL server on one machine (localhost). Start it first:
#   python3 server/server.py --port 8802 --data /tmp/shagar_load --owner-password 'Sunrise-Tea-4471' --rate-scale 1000 --no-auto-backup
# It reports real timings and checks that stock stays exactly right under many simultaneous customers. It does NOT measure internet speed.
import json, statistics, threading, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
B = 'http://127.0.0.1:8802'; res = []
def ok(c, m): res.append(('PASS ' if c else 'FAIL ') + m)
def req(method, path, body=None, cookie=None, headers=None):
    h = {'X-Requested-With': 'XMLHttpRequest', 'Content-Type': 'application/json'}
    if cookie: h['Cookie'] = cookie
    h.update(headers or {})
    r = urllib.request.Request(B + path, data=json.dumps(body).encode() if body is not None else None, headers=h, method=method)
    t0 = time.perf_counter()
    try:
        x = urllib.request.urlopen(r, timeout=60); raw = x.read(); st = x.status
    except urllib.error.HTTPError as e: raw = e.read(); st = e.code
    return st, (time.perf_counter() - t0) * 1000, raw
def burst(n, workers, fn):
    t0 = time.perf_counter()
    with ThreadPoolExecutor(workers) as ex: out = list(ex.map(fn, range(n)))
    return out, time.perf_counter() - t0
def stats(label, out, secs):
    ms = sorted(o[1] for o in out); p95 = ms[int(len(ms) * .95) - 1]
    print(f'{label}: {len(out)} requests in {secs:.1f}s = {len(out) / secs:.0f}/s | median {statistics.median(ms):.0f} ms, 95th percentile {p95:.0f} ms, slowest {ms[-1]:.0f} ms'); return p95
CUST = {'name': 'Load Tester', 'phone': '01733330000', 'addr': 'House 5, Road 3', 'thana': 'Dhanmondi', 'district': 'Dhaka', 'division': 'Dhaka', 'post': '1205'}
def order(pid, i): return req('POST', '/api/orders', {'items': [{'id': pid, 'qty': 1}], 'customer': dict(CUST, name='Load %d' % i), 'area': 'dhaka', 'pay': 'Cash on delivery'})
def stock(pid): return next(p['stock'] for p in json.loads(req('GET', '/api/catalog')[2])['products'] if p['id'] == pid)
st, _, raw = req('POST', '/api/login', {'username': 'owner', 'password': 'Sunrise-Tea-4471'}); ck = None
r = urllib.request.Request(B + '/api/login', data=json.dumps({'username': 'owner', 'password': 'Sunrise-Tea-4471'}).encode(), headers={'X-Requested-With': 'XMLHttpRequest', 'Content-Type': 'application/json'}, method='POST'); ck = urllib.request.urlopen(r).headers['Set-Cookie'].split(';')[0]
out, secs = burst(400, 20, lambda i: req('GET', '/api/catalog')); p = stats('product catalog, 20 shoppers at once', out, secs); ok(all(o[0] == 200 for o in out) and p < 2000, 'all 400 catalog requests succeed, 95% under 2 seconds')
out, secs = burst(300, 20, lambda i: req('GET', '/index.html', headers={'Accept-Encoding': 'gzip'})); p = stats('home page (compressed)', out, secs); ok(all(o[0] == 200 for o in out) and p < 2000, 'all 300 page requests succeed, 95% under 2 seconds')
s_before = stock('P3'); polls = []
def poll(): 
    for _ in range(30): polls.append(req('GET', '/api/state', cookie=ck)[0]); time.sleep(0.05)
th = threading.Thread(target=poll); th.start()
out, secs = burst(60, 12, lambda i: order('P3', i)); th.join(); p = stats('60 orders for one product, 12 customers at once', out, secs)
ok(all(o[0] == 200 for o in out) and p < 5000, 'all 60 simultaneous orders succeed, 95% under 5 seconds')
ok(stock('P3') == s_before - 60, f'stock fell by exactly 60 ({s_before} -> {stock("P3")})'); ok(all(s == 200 for s in polls), 'the staff panel kept loading while orders arrived')
S = json.loads(req('GET', '/api/state', cookie=ck)[2])['data']; nos = {o['no'] for o in S['orders'] if o['customer'].startswith('Load ')}
ok(sum(l['delta'] for l in S['log'] if l.get('ref') in nos and l['pid'] == 'P3') == -60 and len(nos) == 60, 'every order has its matching stock-log entries (60 orders, -60 units)')
s8 = stock('P8'); out, secs = burst(90, 24, lambda i: order('P8', 100 + i)); p = stats('90 customers fight for the last %d units' % s8, out, secs); codes = [o[0] for o in out]
ok(codes.count(200) == s8 and codes.count(409) == 90 - s8 and stock('P8') == 0, f'exactly {s8} orders win and the rest are told it is out of stock; stock ends at 0, never negative')
B_ = json.loads(req('GET', '/api/state', cookie=ck)[2])['data']['batches']; ok(all(b['qty'] >= 0 for b in B_), 'no batch ever went below zero')
print('\n'.join(res)); print('SUMMARY pass=%d fail=%d' % (sum(r.startswith('PASS') for r in res), sum(r.startswith('FAIL') for r in res)))
