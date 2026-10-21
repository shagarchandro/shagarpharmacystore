# API-level tests for the real server. Start it first:
#   python3 server/server.py --port 8800 --data /tmp/shagar_t --owner-password 'Sunrise-Tea-4471'
import json, sys, threading, urllib.request, urllib.error, copy
B = 'http://127.0.0.1:8800'; res = []
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
def login(u, p):
    s, j, h = call('POST', '/api/login', {'username': u, 'password': p}); return s, j, (h.get('Set-Cookie') or '').split(';')[0]
def state(ck): s, j, _ = call('GET', '/api/state', cookie=ck); return j
def stock(pid): return next(p['stock'] for p in call('GET', '/api/catalog')[1]['products'] if p['id'] == pid)
CUST = {'name': 'Api Tester', 'phone': '01712345678', 'addr': 'House 5, Road 3', 'thana': 'Dhanmondi', 'district': 'Dhaka', 'division': 'Dhaka', 'post': '1205'}
def order(items, **kw):
    body = {'items': items, 'customer': CUST, 'area': 'dhaka', 'pay': 'Cash on delivery'}; body.update(kw); return call('POST', '/api/orders', body)

s, j, ck = login('owner', 'Sunrise-Tea-4471'); ok(s == 200 and ck.startswith('sid='), 'owner logs in with the real password')
ok(call('POST', '/api/login', {'username': 'owner', 'password': 'wrong'})[0] == 401, 'wrong password is rejected')
ok(call('GET', '/api/state')[0] == 401 and call('GET', '/api/staff')[0] == 401, 'private endpoints need a session')
s, j, h = call('POST', '/api/login', {'username': 'owner', 'password': 'Sunrise-Tea-4471'}); c = h['Set-Cookie']; ok('HttpOnly' in c and 'SameSite=Strict' in c, 'session cookie is HttpOnly and SameSite=Strict')
ok(call('POST', '/api/coupon', {'code': 'SAVE10'}, headers={'X-Requested-With': ''})[0] == 403, 'POST without the request header is refused (CSRF guard)')
cat = call('GET', '/api/catalog')[1]; ok(all('cost' not in p and 'sku' not in p for p in cat['products']), 'public catalog never exposes cost or SKU')

# orders priced by the server
s0 = stock('P1'); s, j, _ = order([{'id': 'P1', 'qty': 2, 'price': 1, 'total': 1}], total=1, fee=0)
o = j.get('order', {}); ok(s == 200 and o.get('sub') == 24 and o.get('fee') == 60 and o.get('total') == 84, f'server computes the price and ignores client numbers {o.get("total")}')
ok(stock('P1') == s0 - 2, 'stock is deducted at once'); no = o['no']
lg = state(ck)['data']['log']; ok(any(l['ref'] == no and l['delta'] == -2 for l in lg), 'stock log is linked to the order number')
ok(call('POST', '/api/orders', {'items': [{'id': 'P1', 'qty': 9999}], 'customer': CUST, 'area': 'dhaka', 'pay': 'Cash on delivery'})[0] in (400, 409), 'cannot order more than the stock')
ok(order([{'id': 'P5', 'qty': 1}])[0] == 400, 'prescription items need doctor details')
s, j, _ = order([{'id': 'P5', 'qty': 1}], doc='Dr A BMDC 1', rxConfirmed=True); ok(s == 200 and j['order']['status'] == 'Prescription Review', 'prescription order goes to review')
ok(order([{'id': 'P3', 'qty': 1}], coupon='NOPE')[0] == 400, 'unknown coupon is rejected')
s, j, _ = order([{'id': 'P9', 'qty': 2}], coupon='SAVE10'); ok(s == 200 and j['order']['disc'] == 70 and j['order']['total'] == 700 - 70 + 60, 'coupon discount applied by the server')
ok(order([{'id': 'P3', 'qty': 1}], area='moon')[0] == 400 and order([{'id': 'P3', 'qty': 1}], pay='gold')[0] == 400, 'delivery and payment options are validated')
bad = dict(CUST, phone='123'); ok(call('POST', '/api/orders', {'items': [{'id': 'P3', 'qty': 1}], 'customer': bad, 'area': 'dhaka', 'pay': 'Cash on delivery'})[0] == 400, 'invalid mobile number is rejected')

# concurrency: two customers want 40 of a 51-unit product
st8 = stock('P8'); out = []
def go(): out.append(order([{'id': 'P8', 'qty': 40}])[0])
t = [threading.Thread(target=go) for _ in range(2)]; [x.start() for x in t]; [x.join() for x in t]
ok(sorted(out) == [200, 409] and stock('P8') == st8 - 40, f'two simultaneous orders cannot oversell the stock {sorted(out)}')

# lookup / cancel / return
ok(call('POST', '/api/orders/lookup', {'no': no, 'phone': '01999999999'})[0] == 404, 'order lookup needs the right mobile number')
ok(call('POST', '/api/orders/lookup', {'no': no, 'phone': '+8801712345678'})[0] == 200, 'lookup accepts the +88 form of the number')
s0 = stock('P1'); ok(call('POST', '/api/orders/cancel', {'no': no, 'phone': '01712345678'})[0] == 200 and stock('P1') == s0 + 2, 'customer cancel restocks the same batches')
ok(call('POST', '/api/orders/cancel', {'no': no, 'phone': '01712345678'})[0] == 409, 'an order cannot be cancelled twice')
ok(call('POST', '/api/orders/return', {'no': no, 'phone': '01712345678', 'reason': 'x'})[0] in (400, 409), 'returns only for delivered orders')
ok(call('POST', '/api/contact', {'n': 'Sara', 'ph': '01912345678', 't': 'Feedback', 'o': '', 'm': 'Hello there'})[1].get('ref', '').startswith('CT-'), 'contact form returns a reference')

# staff management
ok(call('POST', '/api/staff', {'username': 'cash1', 'name': 'Cash One', 'role': 'Cashier', 'password': 'short'}, cookie=ck)[0] == 400, 'weak staff passwords are refused')
for u, r in (('cash1', 'Cashier'), ('deliv1', 'Delivery Staff'), ('pharma1', 'Pharmacist'), ('inv1', 'Inventory Manager')):
    ok(call('POST', '/api/staff', {'username': u, 'name': u, 'role': r, 'password': 'Temp-Password-1'}, cookie=ck)[0] == 200, f'owner creates {r}')
s, j, cc = login('cash1', 'Temp-Password-1'); ok(j['user']['must_change'] is True, 'new staff must change the temporary password')
ok(call('POST', '/api/state', {'base': {}, 'changes': {'notes': []}}, cookie=cc)[0] == 403, 'blocked from working until the password is changed')
ok(call('POST', '/api/password', {'old': 'Temp-Password-1', 'new': 'short'}, cookie=cc)[0] == 400, 'new password must be 10+ characters')
ok(call('POST', '/api/password', {'old': 'Temp-Password-1', 'new': 'Cashier-New-Pass-1'}, cookie=cc)[0] == 200, 'staff can change their password')
for u in ('deliv1', 'pharma1', 'inv1'):
    s, j, k = login(u, 'Temp-Password-1'); call('POST', '/api/password', {'old': 'Temp-Password-1', 'new': 'Fresh-Pass-7788'}, cookie=k)
_, _, cc = login('cash1', 'Cashier-New-Pass-1'); _, _, cd = login('deliv1', 'Fresh-Pass-7788'); _, _, cp = login('pharma1', 'Fresh-Pass-7788'); _, _, ci = login('inv1', 'Fresh-Pass-7788')
ok(call('GET', '/api/staff', cookie=cc)[0] == 403, 'only the owner can list staff')

# role and integrity checks on /api/state
st = state(cc); V = st['versions']; D = copy.deepcopy(st['data'])
prods = copy.deepcopy(D['products']); prods[0]['price'] = 1
ok(call('POST', '/api/state', {'base': {'products': V['products']}, 'changes': {'products': prods}}, cookie=cc)[0] == 403, 'cashier cannot change product prices (403)')
ords = copy.deepcopy(D['orders']); ords[0]['status'] = 'Shipped'
ok(call('POST', '/api/state', {'base': {'orders': V['orders']}, 'changes': {'orders': ords}}, cookie=cc)[0] == 403, 'cashier cannot set Shipped')
ords = copy.deepcopy(D['orders']); ords[0]['total'] = 1
ok(call('POST', '/api/state', {'base': {'orders': V['orders']}, 'changes': {'orders': ords}}, cookie=ci)[0] == 422, 'order totals cannot be edited by anyone')
rx = next(o for o in D['orders'] if o['status'] == 'Prescription Review'); ords = copy.deepcopy(D['orders']); next(o for o in ords if o['id'] == rx['id'])['status'] = 'Processing'
ok(call('POST', '/api/state', {'base': {'orders': V['orders']}, 'changes': {'orders': ords}}, cookie=ci)[0] == 403, 'only a pharmacist can release a prescription order')
s, j, _ = call('POST', '/api/state', {'base': {'orders': V['orders']}, 'changes': {'orders': ords}}, cookie=cp); ok(s == 200 and j['data']['orders'][[o['id'] for o in D['orders']].index(rx['id'])]['hist'][-1]['by'] == 'Pharmacist', 'pharmacist approves; the server records who and when')
st = state(cc); V = st['versions']; D = copy.deepcopy(st['data'])
bt = copy.deepcopy(D['batches']); bt[0]['qty'] += 50
ok(call('POST', '/api/state', {'base': {'batches': V['batches']}, 'changes': {'batches': bt}}, cookie=cc)[0] == 422, 'stock cannot change without a matching stock-log entry')
bt = copy.deepcopy(D['batches']); lg = copy.deepcopy(D['log']); bt[0]['qty'] -= 1; lg.append({'at': 'x', 'pid': bt[0]['pid'], 'batch': bt[0]['id'], 'delta': -1, 'ref': 'INV-POS-1', 'why': 'sale'})
sale = {'id': 'S-1', 'no': 'INV-POS-1', 'at': 'x', 'items': [{'pid': bt[0]['pid'], 'name': 'x', 'qty': 1, 'price': 999, 'cost': 1}], 'total': 999, 'disc': 0, 'pay': 'Cash', 'change': 0, 'by': 'Cashier'}
sales = copy.deepcopy(D['sales']) + [sale]
ok(call('POST', '/api/state', {'base': {'sales': V['sales'], 'batches': V['batches'], 'log': V['log']}, 'changes': {'sales': sales, 'batches': bt, 'log': lg}}, cookie=cc)[0] == 422, 'POS sale with a wrong price is rejected')
p = next(x for x in D['products'] if x['id'] == bt[0]['pid']); import math
eff = int(p['price'] * (100 - (p.get('disc') or 0)) / 100 + 0.5); sale['items'][0].update(price=eff, cost=p['cost'], name=p['name']); sale['total'] = eff
s, j, _ = call('POST', '/api/state', {'base': {'sales': V['sales'], 'batches': V['batches'], 'log': V['log']}, 'changes': {'sales': sales, 'batches': bt, 'log': lg}}, cookie=cc); ok(s == 200 and j['data']['sales'][-1]['by'] == 'Cashier', f'valid POS sale is accepted and stamped by the server {s} {j.get("error","")}')
ok(call('POST', '/api/state', {'base': {'sales': V['sales']}, 'changes': {'sales': sales}}, cookie=cc)[0] == 409, 'stale data from another device is refused (409)')
st = state(cc); V = st['versions']; sl = copy.deepcopy(st['data']['sales']); sl.pop()
ok(call('POST', '/api/state', {'base': {'sales': V['sales']}, 'changes': {'sales': sl}}, cookie=cc)[0] == 422, 'sales cannot be deleted')
D = state(ck); V = D['versions']; prods = copy.deepcopy(D['data']['products']); prods[0]['price'] = 13
ok(call('POST', '/api/state', {'base': {'products': V['products']}, 'changes': {'products': prods}}, cookie=ck)[0] == 200, 'owner can change a price')
prods[0]['price'] = -5; V = state(ck)['versions']
ok(call('POST', '/api/state', {'base': {'products': V['products']}, 'changes': {'products': prods}}, cookie=ck)[0] == 422, 'invalid prices are refused even for the owner')
ok(call('POST', '/api/state', {'base': {'orders': V['orders']}, 'changes': {'orders': [{'id': 'x'}]}}, cookie=ck)[0] == 422, 'orders cannot be created through the state API')

# lockout
for _ in range(5): call('POST', '/api/login', {'username': 'deliv1', 'password': 'bad'})
ok(call('POST', '/api/login', {'username': 'deliv1', 'password': 'Fresh-Pass-7788'})[0] == 429, 'account locks after 5 wrong passwords')

# logout and deactivate
call('POST', '/api/logout', {}, cookie=cp); ok(call('GET', '/api/state', cookie=cp)[0] == 401, 'logout ends the session on the server')
sid = next(u['id'] for u in call('GET', '/api/staff', cookie=ck)[1]['staff'] if u['username'] == 'inv1')
call('POST', f'/api/staff/{sid}/update', {'active': False}, cookie=ck); ok(call('GET', '/api/state', cookie=ci)[0] == 401, 'deactivating a staff member ends their session')
oid = next(u['id'] for u in call('GET', '/api/staff', cookie=ck)[1]['staff'] if u['username'] == 'owner')
ok(call('POST', f'/api/staff/{oid}/update', {'active': False}, cookie=ck)[0] == 409, 'the last active owner cannot be deactivated')


# ---- two-step login, sessions, security log, staff management, recovery
import hmac, hashlib, base64, struct, time, subprocess, os
def totp(secret, counter=None):
    counter = int(time.time() // 30) if counter is None else counter
    key = base64.b32decode(secret + '=' * ((8 - len(secret) % 8) % 8)); h = hmac.new(key, struct.pack('>Q', counter), hashlib.sha1).digest(); o = h[-1] & 15
    return str((struct.unpack('>I', h[o:o + 4])[0] & 0x7fffffff) % 10 ** 6).zfill(6)
ok(call('POST', '/api/staff', {'username': 'weak1', 'name': 'Weak One', 'role': 'Cashier', 'password': 'weak1-password'}, cookie=ck)[0] == 400, 'a password containing the username is refused')
ok(call('POST', '/api/staff', {'username': 'weak2', 'name': 'Weak Two', 'role': 'Cashier', 'password': 'aaaaaaaaaaaa'}, cookie=ck)[0] == 400 and call('POST', '/api/staff', {'username': 'weak3', 'name': 'Weak Three', 'role': 'Cashier', 'password': 'alllowercaseletters'}, cookie=ck)[0] == 400, 'repetitive and single-type passwords are refused')
call('POST', '/api/staff', {'username': 'secu1', 'name': 'Secu One', 'role': 'Pharmacist', 'password': 'Temp-Secu-5521'}, cookie=ck)
_, j, k = login('secu1', 'Temp-Secu-5521'); call('POST', '/api/password', {'old': 'Temp-Secu-5521', 'new': 'Moon-River-3090'}, cookie=k); _, _, k = login('secu1', 'Moon-River-3090')
acc = call('GET', '/api/account', cookie=k)[1]; ok(acc['user']['totp_enabled'] is False and any(x['current'] for x in acc['sessions']), 'account page data: sessions and 2FA state')
s2, j2, _ = call('POST', '/api/account/2fa/start', {}, cookie=k); secret = j2['secret']; ok(s2 == 200 and j2['uri'].startswith('otpauth://totp/'), 'two-step setup returns a secret and an authenticator link')
ok(call('POST', '/api/account/2fa/enable', {'password': 'Moon-River-3090', 'code': '000000'}, cookie=k)[0] == 400, 'wrong setup code is refused')
ok(call('POST', '/api/account/2fa/enable', {'password': 'bad', 'code': totp(secret)}, cookie=k)[0] == 401, 'enabling two-step needs the password')
s3, j3, _ = call('POST', '/api/account/2fa/enable', {'password': 'Moon-River-3090', 'code': totp(secret)}, cookie=k); codes = j3.get('recovery_codes', []); ok(s3 == 200 and len(codes) == 10, 'two-step enabled with 10 recovery codes')
s4, j4, _ = call('POST', '/api/login', {'username': 'secu1', 'password': 'Moon-River-3090'}); ok(s4 == 401 and j4.get('needs_code') is True, 'password alone no longer logs in')
ok(call('POST', '/api/login', {'username': 'secu1', 'password': 'Moon-River-3090', 'code': '123456'})[0] == 401, 'wrong code is refused')
ok(call('POST', '/api/login', {'username': 'secu1', 'password': 'Moon-River-3090', 'code': totp(secret)})[0] == 401, 'the code used during setup cannot be replayed')
nxt = int(time.time() // 30) + 1; s5, j5, h5 = call('POST', '/api/login', {'username': 'secu1', 'password': 'Moon-River-3090', 'code': totp(secret, nxt)}); ok(s5 == 200, 'password + a fresh code logs in')
ok(call('POST', '/api/login', {'username': 'secu1', 'password': 'Moon-River-3090', 'code': totp(secret, nxt)})[0] == 401, 'a code cannot be used twice')
s6, _, h6 = call('POST', '/api/login', {'username': 'secu1', 'password': 'Moon-River-3090', 'code': codes[0].lower()}); ok(s6 == 200, 'a recovery code logs in')
ok(call('POST', '/api/login', {'username': 'secu1', 'password': 'Moon-River-3090', 'code': codes[0]})[0] == 401, 'a recovery code works only once')
c1 = h5['Set-Cookie'].split(';')[0]; c2 = h6['Set-Cookie'].split(';')[0]
sess = call('GET', '/api/account', cookie=c1)[1]['sessions']; ok(len(sess) >= 3, f'the account page lists signed-in devices ({len(sess)})')
other = next(x for x in sess if not x['current'])
ok(call('POST', '/api/account/sessions/revoke', {'id': other['id']}, cookie=c1)[1].get('revoked') == 1, 'one device can be signed out')
ok(call('POST', '/api/account/sessions/revoke', {'others': True}, cookie=c1)[0] == 200 and call('GET', '/api/state', cookie=c2)[0] == 401 and call('GET', '/api/state', cookie=c1)[0] == 200, 'sign out all other devices keeps only this one')
ok(call('POST', '/api/account/2fa/disable', {'password': 'Moon-River-3090', 'code': '111111'}, cookie=c1)[0] == 400, 'turning two-step off needs a valid code')
ok(call('GET', '/api/security-log', cookie=c1)[0] == 403, 'only the owner can read the security log')
ev = call('GET', '/api/security-log?limit=200', cookie=ck)[1]['events']; kinds = {e['event'] for e in ev}
ok({'login_ok', 'login_failed', '2fa_enabled', 'staff_created', 'password_changed', 'recovery_code_used'} <= kinds, f'the security log records sign-ins, failures and account changes ({len(ev)} events)')
ok(all('password' not in (e['detail'] or '').lower() for e in ev), 'the security log never stores passwords')
sid_secu = next(u['id'] for u in call('GET', '/api/staff', cookie=ck)[1]['staff'] if u['username'] == 'secu1')
st = next(u for u in call('GET', '/api/staff', cookie=ck)[1]['staff'] if u['username'] == 'secu1'); ok(st['totp_enabled'] == 1 and st['last_login'], 'staff list shows 2FA state and last sign-in')
ok(call('POST', f'/api/staff/{sid_secu}/update', {'reset_2fa': True}, cookie=ck)[0] == 200 and call('POST', '/api/login', {'username': 'secu1', 'password': 'Moon-River-3090'})[0] == 200, 'the owner can reset a staff 2FA (lost phone)')
for _ in range(5): call('POST', '/api/login', {'username': 'secu1', 'password': 'bad'})
st = next(u for u in call('GET', '/api/staff', cookie=ck)[1]['staff'] if u['username'] == 'secu1'); ok(st['locked'] is True, 'a locked account is shown as locked')
ok(call('POST', f'/api/staff/{sid_secu}/update', {'unlock': True}, cookie=ck)[0] == 200 and call('POST', '/api/login', {'username': 'secu1', 'password': 'Moon-River-3090'})[0] == 200, 'the owner can unlock an account')
s7, _, k7 = login('secu1', 'Moon-River-3090')
call('POST', f'/api/staff/{sid_secu}/update', {'name': 'Secu Renamed', 'role': 'Cashier'}, cookie=ck); ok(call('GET', '/api/state', cookie=k7)[0] == 401, 'changing a role ends that person\'s sessions')
oid2 = next(u['id'] for u in call('GET', '/api/staff', cookie=ck)[1]['staff'] if u['username'] == 'owner'); ok(call('POST', f'/api/staff/{oid2}/update', {'role': 'Cashier'}, cookie=ck)[0] == 409, 'the last owner cannot be demoted')
here = os.path.dirname(os.path.abspath(__file__)) + '/../server/server.py'
out = subprocess.run([sys.executable, here, '--data', '/tmp/shagar_t', '--reset-password', 'cash1'], capture_output=True, text=True).stdout
newpw = out.split(': ', 1)[1].split('\n')[0].strip() if 'temporary password' in out else ''
s8, j8, _ = call('POST', '/api/login', {'username': 'cash1', 'password': newpw}); ok(s8 == 200 and j8['user']['must_change'] is True, 'server-console password reset works and forces a new password')
ok(call('GET', '/api/state', cookie=cc)[0] == 401, 'a console reset ends the old sessions')

# static files
for path in ('/server/server.py', '/server/data/shop.db', '/server/seed.json', '/tests/server_api.py', '/README.md', '/%2e%2e/etc/passwd', '/.git/config'):
    ok(call('GET', path)[0] == 404, f'not served: {path}')
s, body, h = call('GET', '/index.html'); ok(s == 200 and b'shagar-server' in body, 'pages are served with the server marker')
ok('Content-Security-Policy' in h and h.get('X-Frame-Options') == 'DENY' and h.get('X-Content-Type-Options') == 'nosniff', 'security headers are sent')
print('\n'.join(res)); print('SUMMARY pass=%d fail=%d' % (sum(r.startswith('PASS') for r in res), sum(r.startswith('FAIL') for r in res)))
