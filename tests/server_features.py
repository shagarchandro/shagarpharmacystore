# Real-server tests for: store controls, free delivery, minimum order, delivery slot, waiting list, prescription images, retention, alternatives.
import base64, json, struct, subprocess, sys, os, time, zlib, urllib.request, urllib.error
from playwright.sync_api import sync_playwright
B = 'http://127.0.0.1:8800'; OWNER = 'Sunrise-Tea-4471'; res = []; PW = 'Fresh-Pass-7788'
def ok(c, m): res.append(('PASS ' if c else 'FAIL ') + m)
def call(m, p, body=None, cookie=None, headers=None):
    h = {'X-Requested-With': 'XMLHttpRequest', 'Content-Type': 'application/json'}
    if cookie: h['Cookie'] = cookie
    h.update(headers or {})
    r = urllib.request.Request(B + p, data=json.dumps(body).encode() if body is not None else None, headers=h, method=m)
    try:
        x = urllib.request.urlopen(r); raw = x.read(); return x.status, (json.loads(raw) if raw[:1] in b'{[' else raw), x.headers
    except urllib.error.HTTPError as e:
        raw = e.read(); return e.code, (json.loads(raw) if raw[:1] in b'{[' else raw), e.headers
def login(u, p): s, j, h = call('POST', '/api/login', {'username': u, 'password': p}); return (h.get('Set-Cookie') or '').split(';')[0]
def png(w=40, h=40):
    raw = b''.join(b'\x00' + os.urandom(3 * w) for _ in range(h))
    def ch(t, d): c = struct.pack('>I', len(d)) + t + d; return c + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + ch(b'IDAT', zlib.compress(raw)) + ch(b'IEND', b'')
CUST = {'name': 'Feature Tester', 'phone': '01755555555', 'addr': 'House 5, Road 3', 'thana': 'Dhanmondi', 'district': 'Dhaka', 'division': 'Dhaka', 'post': '1205'}
def order(items, **kw): body = {'items': items, 'customer': CUST, 'area': 'dhaka', 'pay': 'Cash on delivery'}; body.update(kw); return call('POST', '/api/orders', body)
ck = login('owner', OWNER)
def setsettings(**kw):
    st = call('GET', '/api/state', cookie=ck)[1]; s = dict(st['data']['settings']); s.update(kw); return call('POST', '/api/state', {'base': {'settings': st['versions']['settings']}, 'changes': {'settings': s}}, cookie=ck)
# store controls and rules
cat = call('GET', '/api/catalog')[1]; ok(cat['settings']['onlineOrders'] is True and cat['slots'][0] == 'As soon as possible', 'the public catalog tells the shop about order settings and delivery times')
s, j, _ = order([{'id': 'P3', 'qty': 1}], slot='Today 5-9 pm'); ok(s == 200 and j['order']['slot'] == 'Today 5-9 pm', 'a preferred delivery time is stored on the order')
ok(order([{'id': 'P3', 'qty': 1}], slot='Midnight')[0] == 400, 'unknown delivery times are refused')
s, j, _ = order([{'id': 'P3', 'qty': 1}], area='pickup', slot='Today 5-9 pm'); ok(j['order']['slot'] == '', 'pickup orders carry no delivery time')
ok(setsettings(minOrder=100, freeDeliveryMin=500)[0] == 200, 'the owner sets a minimum order and a free-delivery level')
s, j, _ = order([{'id': 'P3', 'qty': 1}]); ok(s == 400 and 'minimum order' in j['error'], 'orders below the minimum are refused')
s, j, _ = order([{'id': 'P9', 'qty': 2}]); ok(s == 200 and j['order']['fee'] == 0 and j['order']['total'] == 700, 'delivery is free above the threshold (server decides)')
s, j, _ = order([{'id': 'P4', 'qty': 2}]); ok(s == 200 and j['order']['fee'] == 60, 'below the threshold the normal fee applies')
ok(setsettings(minOrder=0, freeDeliveryMin=0, onlineOrders=False, notice='Eid hours: 10-6')[0] == 200 and call('GET', '/api/catalog')[1]['settings']['notice'] == 'Eid hours: 10-6', 'the notice reaches the public shop')
s, j, _ = order([{'id': 'P3', 'qty': 1}]); ok(s == 503 and 'paused' in j['error'], 'pausing online ordering is enforced by the server')
ok(setsettings(onlineOrders=True, notice='')[0] == 200 and order([{'id': 'P3', 'qty': 1}])[0] == 200, 'ordering resumes when switched on')
ok(setsettings(minOrder=-5)[0] == 422 and setsettings(notice='x' * 300)[0] == 422, 'invalid settings are refused')
# waiting list
st = call('GET', '/api/state', cookie=ck)[1]; bt = [b for b in st['data']['batches'] if b['pid'] == 'P8']; lg = list(st['data']['log'])
for b in bt: lg.append({'at': 'x', 'pid': 'P8', 'batch': b['id'], 'delta': -b['qty'], 'ref': 'test', 'why': 'adjust'}); b['qty'] = 0
ok(call('POST', '/api/state', {'base': {'batches': st['versions']['batches'], 'log': st['versions']['log']}, 'changes': {'batches': st['data']['batches'], 'log': lg}}, cookie=ck)[0] == 200, 'an out-of-stock product is created for the test')
ok(call('POST', '/api/waitlist', {'pid': 'P3', 'phone': '01755555555'})[0] == 409, 'cannot join the waiting list for something that is in stock')
ok(call('POST', '/api/waitlist', {'pid': 'P8', 'phone': '123'})[0] == 400, 'waiting list needs a valid mobile number')
ok(call('POST', '/api/waitlist', {'pid': 'P8', 'name': 'Waiting Person', 'phone': '01755555555'})[0] == 200 and call('POST', '/api/waitlist', {'pid': 'P8', 'phone': '01755555555'})[0] == 200, 'joining twice does not duplicate the entry')
wl = call('GET', '/api/state', cookie=ck)[1]['data']['waitlist']; ok(len(wl) == 1 and wl[0]['name'] == 'Waiting Person' and wl[0]['contacted'] is False, 'staff see who is waiting')
kc = None
call('POST', '/api/staff', {'username': 'cash5', 'name': 'cash5', 'role': 'Cashier', 'password': 'Temp-Password-1'}, cookie=ck); k0 = login('cash5', 'Temp-Password-1'); call('POST', '/api/password', {'old': 'Temp-Password-1', 'new': PW}, cookie=k0); kc = login('cash5', PW)
ok('waitlist' not in call('GET', '/api/state', cookie=kc)[1]['data'], 'cashiers are not sent the waiting list')
# prescription images
img = base64.b64encode(png()).decode()
s, j, _ = order([{'id': 'P5', 'qty': 1}], doc='Dr R BMDC 77', rxConfirmed=True, rxFile={'name': 'rx.png', 'data': img}); ok(s == 400 and 'tick' in j['error'], 'an image needs the customer\'s consent')
s, j, _ = order([{'id': 'P5', 'qty': 1}], doc='Dr R BMDC 77', rxConfirmed=True, rxConsent=True, rxFile={'name': 'rx.png', 'data': img}); o = j.get('order', {}); ok(s == 200 and o.get('rxFile', {}).get('type') == 'image/png', 'a prescription image is stored with the order')
ok('data' not in json.dumps(o['rxFile']) and len(o['rxFile']['id']) == 32, 'the order carries only a reference to the image, never the image')
ok(call('GET', '/api/prescriptions/download?no=' + o['no'])[0] == 401 and call('GET', '/api/prescriptions/download?no=' + o['no'], cookie=kc)[0] == 403, 'only a signed-in pharmacist or owner can open it')
s, body, h = call('GET', '/api/prescriptions/download?no=' + o['no'], cookie=ck); ok(s == 200 and body[:8] == b'\x89PNG\r\n\x1a\n' and h.get('Content-Type') == 'image/png' and h.get('Cache-Control') == 'no-store', 'the owner can view it (not cached)')
ev = call('GET', '/api/security-log?limit=100', cookie=ck)[1]['events']; ok(any(e['event'] == 'prescription_viewed' and e['detail'] == o['no'] for e in ev), 'each view is written to the security log')
ok(call('GET', '/prescriptions/' + o['rxFile']['id'] + '.png')[0] == 404 and call('GET', '/server/data/prescriptions/')[0] == 404, 'images are never served as normal files')
s, j, _ = order([{'id': 'P5', 'qty': 1}], doc='Dr R BMDC 77', rxConfirmed=True, rxConsent=True, rxFile={'name': 'x.png', 'data': base64.b64encode(b'GIF89a' + b'0' * 400).decode()}); ok(s == 400 and 'JPG, PNG' in j['error'], 'files that are not JPG/PNG/WebP are refused (checked by content, not name)')
s, j, _ = order([{'id': 'P5', 'qty': 1}], doc='Dr R BMDC 77', rxConfirmed=True, rxConsent=True, rxFile={'name': 'big.png', 'data': base64.b64encode(png() + b'0' * 3_100_000).decode()}); ok(s == 400, 'images over 3 MB are refused')
s, j, _ = order([{'id': 'P3', 'qty': 1}], rxConsent=True, rxFile={'name': 'rx.png', 'data': img}); ok(s == 200 and 'rxFile' not in j['order'], 'an image sent with a non-prescription order is ignored')
rxdir = '/tmp/shagar_t/prescriptions'; n_before = len(os.listdir(rxdir)); ok(n_before == 1, f'only the one valid image is on disk ({n_before})')
# retention
srv = os.path.dirname(os.path.abspath(__file__)) + '/../server/server.py'
out = subprocess.run([sys.executable, srv, '--data', '/tmp/shagar_t', '--purge-prescriptions', '--rx-days', '30'], capture_output=True, text=True).stdout; ok('0 prescription image' in out and len(os.listdir(rxdir)) == 1, 'recent images are kept')
import sqlite3
cn = sqlite3.connect('/tmp/shagar_t/shop.db'); row = cn.execute("select data from kv where coll='orders'").fetchone(); od = json.loads(row[0])
for x in od:
    if x.get('rxFile'): x['rxFile']['at'] = '2020-01-01T00:00:00.000Z'
cn.execute("update kv set data=? where coll='orders'", (json.dumps(od),)); cn.commit(); cn.close()
out = subprocess.run([sys.executable, srv, '--data', '/tmp/shagar_t', '--purge-prescriptions', '--rx-days', '30'], capture_output=True, text=True).stdout
ok('1 prescription image' in out and len(os.listdir(rxdir)) == 0, 'old images are deleted automatically after the retention period')
ok(call('GET', '/api/prescriptions/download?no=' + o['no'], cookie=ck)[0] == 404, 'a deleted image is gone for good')
ord2 = [x for x in call('GET', '/api/state', cookie=ck)[1]['data']['orders'] if x['no'] == o['no']][0]; ok(ord2['rxFile'].get('purged') is True, 'the order records that its image was deleted')
# privacy tools
call('POST', '/api/contact', {'n': 'Feature Tester', 'ph': '01755555555', 't': 'Feedback', 'o': '', 'm': 'Thank you for the quick delivery'})
tot_before = sum(x['total'] for x in call('GET', '/api/state', cookie=ck)[1]['data']['orders'])
ok(call('GET', '/api/privacy/export?phone=01755555555', cookie=kc)[0] == 403 and call('GET', '/api/privacy/export?phone=01755555555')[0] == 401, 'only the owner can export a customer\'s data')
ex = call('GET', '/api/privacy/export?phone=01755555555', cookie=ck)[1]; ok(len(ex['orders']) >= 4 and len(ex['messages']) == 1 and ex['waiting_list'], 'the export gathers orders, messages and waiting-list entries')
ok(call('POST', '/api/privacy/erase', {'phone': '01755555555'}, cookie=ck)[0] == 400 and call('POST', '/api/privacy/erase', {'phone': '01755555555', 'confirm': 'yes'}, cookie=ck)[0] == 400 and call('POST', '/api/privacy/erase', {'phone': '01755555555', 'confirm': 'ERASE'}, cookie=kc)[0] == 403, 'erasing needs the owner and the word ERASE')
s, j, _ = call('POST', '/api/privacy/erase', {'phone': '01755555555', 'confirm': 'ERASE'}, cookie=ck); ok(s == 200 and j['orders'] >= 4 and j['messages'] == 1, 'erasing removes the personal details from every order and message')
D2 = call('GET', '/api/state', cookie=ck)[1]['data']; txt = json.dumps(D2)
ok('01755555555' not in txt and 'Feature Tester' not in txt and 'Waiting Person' not in txt, 'no trace of the number, name or waiting-list entry is left anywhere in the data')
ok(sum(x['total'] for x in D2['orders']) == tot_before and any(x['customer'] == 'Erased customer' for x in D2['orders']), 'order totals stay for the accounts')
ok(call('POST', '/api/orders/lookup', {'no': o['no'], 'phone': '01755555555'})[0] == 404, 'the old number can no longer open the order')
ev = call('GET', '/api/security-log?limit=100', cookie=ck)[1]['events']; er = [e for e in ev if e['event'] == 'customer_erased']; ok(er and '01755555555' not in json.dumps(er) and '555' in er[0]['detail'], 'the erasure is logged without storing the full number')
print('\n'.join(res)); print('SUMMARY pass=%d fail=%d' % (sum(r.startswith('PASS') for r in res), sum(r.startswith('FAIL') for r in res)))
