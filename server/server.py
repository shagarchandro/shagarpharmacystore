#!/usr/bin/env python3
"""Shagar Medical Store server.

One process serves the website files and a JSON API backed by SQLite.
Python standard library only (Python 3.9+). Run:  python3 server/server.py

What is real here: a shared database, staff accounts with hashed passwords and
server-side sessions, server-side role checks, server-side order pricing and
stock deduction (FEFO) in a transaction, rate limiting, and input validation.
What is NOT included: payment gateways, SMS/email, HTTPS (put a reverse proxy
in front for HTTPS), phone-number verification for customers.
"""
import argparse, base64, hashlib, hmac, http.server, json, mimetypes, os, re, secrets, shutil, sqlite3
import gzip, logging, logging.handlers, sys, threading, time, traceback, urllib.parse
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

VERSION = '2.0.0'
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SEED = os.path.join(HERE, 'seed.json')

COLLS = ['products', 'batches', 'orders', 'sales', 'coupons', 'suppliers', 'log', 'expenses', 'notes', 'audit',
         'purchases', 'refunds', 'shifts', 'cust', 'messages', 'loyalty', 'waitlist', 'settings']
DICT_COLLS = {'cust', 'loyalty', 'settings'}
STATUS = ['Pending', 'Confirmed', 'Prescription Review', 'Processing', 'Packed', 'Shipped', 'Delivered',
          'Cancelled', 'Return Requested', 'Returned', 'Refunded']
STATUS_OK = {'Cashier': ['Pending', 'Confirmed', 'Processing', 'Packed'],
             'Inventory Manager': ['Processing', 'Packed'], 'Delivery Staff': ['Shipped', 'Delivered']}
ROLES = ['Owner', 'Pharmacist', 'Cashier', 'Inventory Manager', 'Delivery Staff']
WRITE = {
    'Owner': set(COLLS) - {'messages'},
    'Pharmacist': {'orders', 'batches', 'log', 'notes', 'audit', 'refunds', 'sales', 'loyalty', 'waitlist'},
    'Cashier': {'orders', 'batches', 'log', 'sales', 'loyalty', 'shifts', 'expenses'},
    'Inventory Manager': {'products', 'batches', 'log', 'purchases', 'suppliers', 'expenses', 'audit', 'notes', 'orders', 'waitlist'},
    'Delivery Staff': {'orders'},
}
# What each role may READ (a superset of what it may write). Anything else is simply not sent to that role.
READ = {
    'Owner': set(COLLS),
    'Pharmacist': {'products', 'batches', 'orders', 'sales', 'notes', 'log', 'audit', 'refunds', 'loyalty', 'suppliers', 'purchases', 'settings', 'waitlist'},
    'Cashier': {'products', 'batches', 'orders', 'sales', 'loyalty', 'shifts', 'expenses', 'refunds', 'log', 'settings'},
    'Inventory Manager': {'products', 'batches', 'orders', 'sales', 'log', 'audit', 'purchases', 'suppliers', 'expenses', 'notes', 'settings', 'waitlist'},
    'Delivery Staff': {'orders', 'settings'},
}
COST_ROLES = {'Owner', 'Inventory Manager'}  # only these see purchase/cost prices


def view_for(role, data, vers):
    keep = READ.get(role, set())
    out = {c: data[c] for c in COLLS if c in keep and c in data}
    v = {c: vers[c] for c in COLLS if c in keep and c in vers}
    if role not in COST_ROLES:
        if 'products' in out:
            out['products'] = [{k: x for k, x in p.items() if k != 'cost'} for p in out['products']]
        if 'batches' in out:
            out['batches'] = [{k: x for k, x in b.items() if k != 'cost'} for b in out['batches']]
        if 'sales' in out:
            out['sales'] = [dict(s, items=[{k: x for k, x in it.items() if k != 'cost'} for it in s.get('items', [])]) for s in out['sales']]
    return out, v
DEFAULT_SETTINGS = {'store': 'Shagar Medical Store', 'logoText': 'Shagar Medical Store', 'address': 'Dhanmondi, Dhaka',
                    'phone': '01700-000000', 'receiptFooter': 'Thank you. Keep this receipt for returns.',
                    'defReorder': 20, 'idleMin': 30, 'invoice': 'INV', 'feeDhaka': 60, 'feeOut': 120, 'expiryDays': 60,
                    'onlineOrders': True, 'notice': '', 'freeDeliveryMin': 0, 'minOrder': 0, 'rxRetentionDays': 30,
                    # sign-in policy (all off by default; only the Owner can change these)
                    'req2fa': '', 'hoursOn': False, 'hoursFrom': 8, 'hoursTo': 22, 'maxSessions': 0, 'pwMaxDays': 0}
SLOTS = ['As soon as possible', 'Today 5-9 pm', 'Tomorrow 9 am-1 pm', 'Tomorrow 5-9 pm']
MAX_RX = 3_000_000
RX_EXT = {'image/jpeg': '.jpg', 'image/png': '.png', 'image/webp': '.webp'}
RX_DIR = None
PAY_OK = ['Cash on delivery', 'bKash (demo, not connected)']
PHONE_RE = re.compile(r'^(\+?88)?01[3-9]\d{8}$')
LOCK = threading.RLock()
ARGS = None
DB_PATH = None
RL = defaultdict(deque)
RATE_SCALE = 1.0
BACKUP_DIR = None
LOG = logging.getLogger('shagar')


class ApiError(Exception):
    def __init__(self, code, msg, extra=None):
        super().__init__(msg)
        self.code, self.msg, self.extra = code, msg, extra or {}


def bad(msg, code=422):
    raise ApiError(code, msg)


def now_iso():
    d = datetime.now(timezone.utc)
    return d.strftime('%Y-%m-%dT%H:%M:%S.') + '%03dZ' % (d.microsecond // 1000)


def today_str():
    return datetime.now(timezone.utc).date().isoformat()


def isnum(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def isint(x):
    return isinstance(x, int) and not isinstance(x, bool)


def js_round(x):
    return int(x + 0.5) if x >= 0 else -int(-x + 0.5)


def eff(p):
    return js_round(p['price'] * (100 - (p.get('disc') or 0)) / 100)


def nph(x):
    return re.sub(r'^\+?88', '', str(x or ''))


# ---------------------------------------------------------------- database
SCHEMA = '''
CREATE TABLE IF NOT EXISTS kv(coll TEXT PRIMARY KEY, data TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT);
CREATE TABLE IF NOT EXISTS staff(id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
  role TEXT NOT NULL, salt TEXT NOT NULL, pw TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1,
  must_change INTEGER NOT NULL DEFAULT 0, failed INTEGER NOT NULL DEFAULT 0, locked_until REAL NOT NULL DEFAULT 0,
  created TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS sessions(th TEXT PRIMARY KEY, staff_id INTEGER NOT NULL, created REAL NOT NULL, last_seen REAL NOT NULL);
CREATE TABLE IF NOT EXISTS security_log(id INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT NOT NULL, user TEXT, event TEXT NOT NULL, ip TEXT, detail TEXT);
'''
MIGRATIONS = {'staff': [('totp_secret', 'TEXT'), ('totp_pending', 'TEXT'), ('totp_enabled', 'INTEGER NOT NULL DEFAULT 0'), ('recovery', 'TEXT'),
                        ('totp_last', 'INTEGER NOT NULL DEFAULT 0'), ('last_login', 'TEXT'), ('last_ip', 'TEXT'), ('prev_login', 'TEXT'), ('prev_ip', 'TEXT'), ('pw_changed', 'TEXT')],
              'sessions': [('ip', 'TEXT'), ('ua', 'TEXT')]}


def migrate(conn):
    for table, cols in MIGRATIONS.items():
        have = {r['name'] for r in conn.execute(f'PRAGMA table_info({table})')}
        for name, typ in cols:
            if name not in have:
                conn.execute(f'ALTER TABLE {table} ADD COLUMN {name} {typ}')


def seclog(conn, user, event, ip='', detail=''):
    conn.execute('INSERT INTO security_log(at,user,event,ip,detail) VALUES(?,?,?,?,?)', (now_iso(), user, event, ip, (detail or '')[:300]))
    conn.execute('DELETE FROM security_log WHERE id < (SELECT MAX(id) FROM security_log) - 5000')


def db():
    conn = sqlite3.connect(DB_PATH, timeout=30, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA synchronous=NORMAL')
    return conn


def kvload(conn, c):
    r = conn.execute('SELECT data, version FROM kv WHERE coll=?', (c,)).fetchone()
    if r is None:
        empty = {} if c in DICT_COLLS else []
        conn.execute('INSERT INTO kv(coll,data,version) VALUES(?,?,1)', (c, json.dumps(empty)))
        return empty, 1
    return json.loads(r['data']), r['version']


def kvstore(conn, c, data):
    conn.execute('UPDATE kv SET data=?, version=version+1 WHERE coll=?', (json.dumps(data, separators=(',', ':')), c))


def meta_get(conn, k, default=None):
    r = conn.execute('SELECT v FROM meta WHERE k=?', (k,)).fetchone()
    return r['v'] if r else default


def meta_set(conn, k, v):
    conn.execute('INSERT INTO meta(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v', (k, str(v)))


def hash_pw(pw, salt=None):
    salt = salt or secrets.token_bytes(16)
    h = hashlib.pbkdf2_hmac('sha256', pw.encode('utf-8'), salt, 240000)
    return base64.b64encode(salt).decode(), base64.b64encode(h).decode()


def check_pw(pw, salt_b64, h_b64):
    h = hashlib.pbkdf2_hmac('sha256', pw.encode('utf-8'), base64.b64decode(salt_b64), 240000)
    return hmac.compare_digest(base64.b64encode(h).decode(), h_b64)


SETUP = {'code': None}
RANDOM_OWNER = False


def init_db(demo, owner_pw):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = db()
    conn.executescript(SCHEMA)
    migrate(conn)
    created_pw = None
    with LOCK:
        conn.execute('BEGIN IMMEDIATE')
        try:
            if meta_get(conn, 'seeded') is None:
                data = {c: ({} if c in DICT_COLLS else []) for c in COLLS}
                data['settings'] = dict(DEFAULT_SETTINGS)
                if demo and os.path.exists(SEED):
                    seed = json.load(open(SEED, encoding='utf-8'))
                    t0 = datetime.now(timezone.utc).date()
                    for b in seed['batches']:
                        off = b.pop('expOffset')
                        b['exp'] = (t0 + __import__('datetime').timedelta(days=off)).isoformat()
                    data['products'], data['batches'] = seed['products'], seed['batches']
                    data['coupons'], data['suppliers'] = seed['coupons'], seed['suppliers']
                    data['settings'].update(seed.get('settings', {}))
                for c in COLLS:
                    conn.execute('INSERT OR REPLACE INTO kv(coll,data,version) VALUES(?,?,1)', (c, json.dumps(data[c])))
                meta_set(conn, 'seeded', '1')
                meta_set(conn, 'order_seq', '1000')
            if conn.execute('SELECT COUNT(*) AS n FROM staff').fetchone()['n'] == 0 and (owner_pw or RANDOM_OWNER):
                forced = owner_pw is None
                pw = owner_pw or secrets.token_urlsafe(10)
                salt, h = hash_pw(pw)
                conn.execute('INSERT INTO staff(username,name,role,salt,pw,active,must_change,created) VALUES(?,?,?,?,?,1,?,?)',
                             ('owner', 'Owner', 'Owner', salt, h, 1 if forced else 0, now_iso()))
                created_pw = pw if forced else '(the password you supplied)'
            conn.execute('COMMIT')
        except Exception:
            conn.execute('ROLLBACK')
            raise
    conn.close()
    return created_pw


# ---------------------------------------------------------------- helpers
def rate(ip, group, limit, window):
    now = time.time()
    q = RL[(ip, group)]
    while q and now - q[0] > window:
        q.popleft()
    if len(q) >= limit * RATE_SCALE:
        return False
    q.append(now)
    return True


def sanitize_str(x, mx, minimum=0, what='Text'):
    if not isinstance(x, str):
        bad(f'{what} is required', 400)
    x = x.strip()
    if len(x) < minimum or len(x) > mx:
        bad(f'{what} must be {minimum}-{mx} characters', 400)
    return x


def fefo_take(batches, log, pid, qty, ref, now):
    usable = sorted([b for b in batches if b['pid'] == pid and b['qty'] > 0 and b['exp'] >= today_str()],
                    key=lambda b: b['exp'])
    if sum(b['qty'] for b in usable) < qty:
        return False
    n = qty
    for b in usable:
        t = min(b['qty'], n)
        b['qty'] -= t
        n -= t
        log.append({'at': now, 'pid': pid, 'batch': b['id'], 'delta': -t, 'ref': ref, 'why': 'sale'})
        if not n:
            break
    return True


def stock_of(batches, pid):
    return sum(b['qty'] for b in batches if b['pid'] == pid and b['qty'] > 0 and b['exp'] >= today_str())


# ---------------------------------------------------------------- validation of staff changes
def v_products(lst):
    ids, skus, bcs = set(), set(), set()
    for p in lst:
        if not isinstance(p, dict):
            bad('Invalid product')
        pid = p.get('id')
        if not isinstance(pid, str) or not pid or len(pid) > 64 or pid in ids:
            bad('Product ids must be unique')
        ids.add(pid)
        if not isinstance(p.get('name'), str) or not 2 <= len(p['name'].strip()) <= 160:
            bad(f'Product {pid}: invalid name')
        if not isnum(p.get('price')) or not 0 < p['price'] <= 1e7:
            bad(f"Product {p['name']}: price must be above 0")
        if not isnum(p.get('cost')) or p['cost'] < 0:
            bad(f"Product {p['name']}: invalid cost")
        d = p.get('disc') or 0
        if not isnum(d) or not 0 <= d <= 90:
            bad(f"Product {p['name']}: discount must be 0-90")
        if not isint(p.get('reorder', 0)) or p.get('reorder', 0) < 0:
            bad(f"Product {p['name']}: invalid reorder level")
        if not isinstance(p.get('rx', False), bool):
            bad('Invalid prescription flag')
        for key, seen in (('sku', skus), ('barcode', bcs)):
            v = p.get(key)
            if v:
                if not isinstance(v, str) or v in seen:
                    bad(f'Duplicate {key}: {v}')
                seen.add(v)
        img = p.get('img')
        if img is not None and (not isinstance(img, str) or not img.startswith('data:image/') or len(img) > 700000):
            bad('Invalid product image')
    return ids


def v_batches_and_log(old, new, product_ids, changes):
    ob = {b['id']: b['qty'] for b in old['batches']}
    nb = new['batches']
    seen = set()
    for b in nb:
        if not isinstance(b, dict) or not isinstance(b.get('id'), str) or b['id'] in seen:
            bad('Batch ids must be unique')
        seen.add(b['id'])
        if b.get('pid') not in product_ids:
            bad(f"Batch {b.get('no')}: unknown product")
        if not isint(b.get('qty')) or b['qty'] < 0:
            bad(f"Batch {b.get('no')}: quantity must be a whole number, 0 or more")
        if not re.fullmatch(r'\d{4}-\d\d-\d\d', str(b.get('exp', ''))):
            bad(f"Batch {b.get('no')}: invalid expiry date")
    ol, nl = old['log'], new['log']
    if len(nl) < len(ol) or nl[:len(ol)] != ol:
        bad('The stock log is append-only')
    deltas = defaultdict(int)
    for e in nl[len(ol):]:
        if not isinstance(e, dict) or not isinstance(e.get('pid'), str) or not isint(e.get('delta')):
            bad('Invalid stock log entry')
        if e.get('batch'):
            deltas[e['batch']] += e['delta']
    for bid in set(deltas) | {b['id'] for b in nb}:
        b = next((x for x in nb if x['id'] == bid), None)
        if b is None:
            continue  # batch removed together with its product
        if b['qty'] - ob.get(bid, 0) != deltas.get(bid, 0):
            bad(f"Stock for batch {b['no']} changed by {b['qty'] - ob.get(bid, 0)} but the stock log records {deltas.get(bid, 0)}")


def v_orders(role, old, new_list):
    olds = {o['id']: o for o in old}
    if len(new_list) != len(old):
        bad('Orders cannot be added or removed here')
    mutable = {'status', 'note', 'reason', 'driver', 'hist', 'loy', 'loyBack'}
    out = []
    for o in new_list:
        oo = olds.get(o.get('id')) if isinstance(o, dict) else None
        if oo is None:
            bad('Orders cannot be created here')
        for k in set(o) | set(oo):
            if k not in mutable and o.get(k) != oo.get(k):
                bad(f"Order {oo['no']}: {k} cannot be changed")
        for k in ('note', 'reason', 'driver'):
            if o.get(k) is not None and (not isinstance(o[k], str) or len(o[k]) > 500):
                bad(f'Invalid {k}')
        st = o.get('status')
        if st not in STATUS:
            bad('Invalid order status')
        if o.get('loy') != oo.get('loy') and not (o.get('loy') == 0 and st == 'Cancelled'):
            bad(f"Order {oo['no']}: loyalty points can only be returned when the order is cancelled")
        res = dict(oo)
        for k in ('note', 'reason', 'driver', 'loy', 'loyBack'):
            if k in o:
                res[k] = o[k]
        if st != oo['status']:
            if role not in ('Owner', 'Pharmacist'):
                if st not in STATUS_OK.get(role, []):
                    bad(f'Your role ({role}) cannot set the status {st}', 403)
                if oo.get('status') == 'Prescription Review':
                    bad('Only a pharmacist or owner can release a prescription order', 403)
                if oo.get('rx') and STATUS.index(st) > STATUS.index('Prescription Review'):
                    bad('Only a pharmacist or owner can approve a prescription order', 403)
            res['status'] = st
            res['hist'] = list(oo.get('hist') or []) + [{'s': st, 'at': now_iso(), 'by': role}]
        out.append(res)
    return out


def v_sales(role, old_sales, new_sales, products, new_log, old_log):
    pm = {p['id']: p for p in products}
    if not isinstance(new_sales, list) or len(new_sales) < len(old_sales):
        bad('Sales cannot be deleted')
    appended = defaultdict(lambda: defaultdict(int))
    for e in new_log[len(old_log):]:
        if e.get('why') == 'sale' and e.get('ref'):
            appended[e['ref']][e['pid']] += e['delta']
    existing = {s.get('no') for s in old_sales}
    out = []
    for i, s in enumerate(new_sales):
        if not isinstance(s, dict):
            bad('Invalid sale')
        if i < len(old_sales):
            o = old_sales[i]
            if s == o:
                out.append(o)
                continue
            ch = {k for k in set(s) | set(o) if s.get(k) != o.get(k)}
            if ch <= {'refunded', 'loy', 'loyBack'} and s.get('refunded') is True and not o.get('refunded') \
                    and role in ('Owner', 'Pharmacist'):
                out.append({**o, 'refunded': True, 'loy': s.get('loy', o.get('loy')), 'loyBack': s.get('loyBack')})
                continue
            bad(f"Sale {o.get('no')} cannot be edited")
        no = s.get('no')
        if not isinstance(no, str) or not 3 <= len(no) <= 40 or no in existing:
            bad('Sale numbers must be unique')
        existing.add(no)
        items = s.get('items')
        if not isinstance(items, list) or not 1 <= len(items) <= 100:
            bad(f'Sale {no}: invalid items')
        total, per, rx = 0, defaultdict(int), False
        for it in items:
            p = pm.get(it.get('pid')) if isinstance(it, dict) else None
            if p is None:
                bad(f'Sale {no}: unknown product')
            if not isint(it.get('qty')) or not 1 <= it['qty'] <= 9999:
                bad(f'Sale {no}: invalid quantity')
            if it.get('price') != eff(p):
                bad(f"Sale {no}: the price of {p['name']} must be {eff(p)}")
            it['cost'] = p['cost']
            total += it['qty'] * it['price']
            per[p['id']] += it['qty']
            rx = rx or bool(p.get('rx'))
        d, loy = s.get('disc', 0), s.get('loy', 0)
        if not isnum(d) or d < 0 or d > total or not isint(loy) or loy < 0 or loy > (total - d) // 2:
            bad(f'Sale {no}: invalid discount or points')
        if abs(s.get('total', -1) - (total - d - loy)) > 0.01:
            bad(f'Sale {no}: the total does not match the items')
        if s.get('pay') not in ('Cash', 'bKash (demo)', 'Card (demo)'):
            bad(f'Sale {no}: invalid payment method')
        if rx:
            if role not in ('Owner', 'Pharmacist'):
                bad('Only a pharmacist or owner can sell prescription medicines', 403)
            if not isinstance(s.get('rx'), str) or len(s['rx'].strip()) < 6:
                bad(f'Sale {no}: a prescription reference is required')
        for pid, q in per.items():
            if appended[no].get(pid, 0) != -q:
                bad(f'Sale {no}: stock was not deducted correctly for one item')
        out.append({**s, 'at': now_iso(), 'by': role})
    return out


def v_append_only(name, old, new):
    if not isinstance(new, list) or len(new) < len(old) or new[:len(old)] != old:
        bad(f'{name} is append-only')
    for e in new[len(old):]:
        if not isinstance(e, dict):
            bad(f'Invalid {name} entry')
    return new


REQ2FA = {'': set(), 'owner': {'Owner'}, 'owner_pharmacist': {'Owner', 'Pharmacist'}, 'all': set(ROLES)}


def dhaka_hour():
    return (datetime.now(timezone.utc) + timedelta(hours=6)).hour


def hours_ok(st, role):
    """Staff sign-in window (Dhaka time). The Owner is never restricted. A window like 20 to 6 spans midnight."""
    if role == 'Owner' or not st.get('hoursOn'):
        return True
    a, b, hr = st.get('hoursFrom', 8), st.get('hoursTo', 22), dhaka_hour()
    return a <= hr < b if a < b else (hr >= a or hr < b)


def v_settings(s):
    if not isinstance(s, dict):
        bad('Invalid settings')
    out = dict(DEFAULT_SETTINGS)
    for k in ('store', 'logoText', 'address', 'phone', 'receiptFooter'):
        out[k] = sanitize_str(s.get(k, DEFAULT_SETTINGS[k]), 200, 1, k)
    if not re.fullmatch(r'[A-Za-z0-9-]{2,8}', str(s.get('invoice', 'INV'))):
        bad('Invoice prefix must be 2-8 letters, digits or dashes')
    out['invoice'] = s.get('invoice', 'INV')
    out['onlineOrders'] = bool(s.get('onlineOrders', True))
    notice = s.get('notice', '')
    if not isinstance(notice, str) or len(notice) > 200:
        bad('The notice must be at most 200 characters')
    out['notice'] = notice.strip()
    for k, lo, hi in (('feeDhaka', 0, 10000), ('feeOut', 0, 10000), ('expiryDays', 1, 3650), ('defReorder', 0, 100000), ('idleMin', 0, 240),
                      ('freeDeliveryMin', 0, 1000000), ('minOrder', 0, 1000000), ('rxRetentionDays', 0, 365),
                      ('hoursFrom', 0, 23), ('hoursTo', 1, 24), ('maxSessions', 0, 10), ('pwMaxDays', 0, 365)):
        v = s.get(k, DEFAULT_SETTINGS[k])
        if not isnum(v) or not lo <= v <= hi:
            bad(f'{k} must be between {lo} and {hi}')
        out[k] = v
    if s.get('req2fa', '') not in REQ2FA:
        bad('Invalid two-step policy')
    out['req2fa'] = s.get('req2fa', '')
    out['hoursOn'] = bool(s.get('hoursOn', False))
    if 0 < out['pwMaxDays'] < 30:
        bad('Password maximum age must be 0 (off) or at least 30 days')
    if out['hoursOn'] and out['hoursFrom'] == out['hoursTo']:
        bad('Sign-in hours must start and end at different times')
    return out


def validate(role, old, changes):
    for c in changes:
        if c not in WRITE.get(role, ()):
            raise ApiError(403, f'Your role ({role}) cannot change {c}.')
        want = dict if c in DICT_COLLS else list
        if not isinstance(changes[c], want):
            bad(f'{c} has the wrong type')
        if len(json.dumps(changes[c])) > 8_000_000:
            bad(f'{c} is too large')
    if role not in COST_ROLES:
        if isinstance(changes.get('batches'), list):
            ob = {b['id']: b for b in old['batches']}
            for b in changes['batches']:
                if isinstance(b, dict):
                    b.setdefault('cost', (ob.get(b.get('id')) or {}).get('cost', 0))
        if isinstance(changes.get('sales'), list):
            for i, sl in enumerate(changes['sales']):
                if isinstance(sl, dict) and i < len(old['sales']) and isinstance(sl.get('items'), list):
                    for j, it in enumerate(sl['items']):
                        oi = old['sales'][i].get('items', [])
                        if isinstance(it, dict) and j < len(oi):
                            it.setdefault('cost', oi[j].get('cost'))
    new = {c: changes.get(c, old[c]) for c in COLLS}
    out = dict(changes)
    product_ids = {p['id'] for p in old['products']}
    if 'products' in changes:
        product_ids = v_products(new['products'])
    if 'batches' in changes or 'log' in changes:
        v_batches_and_log(old, new, product_ids, changes)
    if 'orders' in changes:
        out['orders'] = v_orders(role, old['orders'], changes['orders'])
    if 'sales' in changes:
        out['sales'] = v_sales(role, old['sales'], changes['sales'], new['products'], new['log'], old['log'])
    for c in ('log', 'audit', 'expenses', 'shifts', 'refunds'):
        if c in changes:
            out[c] = v_append_only(c, old[c], changes[c])
    if 'notes' in changes and len(changes['notes']) > 5000:
        bad('Too many notifications')
    if 'coupons' in changes:
        codes = set()
        for k in changes['coupons']:
            if not isinstance(k, dict) or not isinstance(k.get('code'), str) or not k['code'] or k['code'] in codes \
                    or not isnum(k.get('pct')) or not 0 < k['pct'] <= 100 or not isnum(k.get('min', 0)) or k.get('min', 0) < 0:
                bad('Invalid coupon')
            codes.add(k['code'])
    if 'suppliers' in changes or 'purchases' in changes:
        for c in ('suppliers', 'purchases'):
            if c in changes:
                ids = set()
                for x in changes[c]:
                    if not isinstance(x, dict) or not isinstance(x.get('id'), str) or x['id'] in ids:
                        bad(f'Invalid {c} entry')
                    ids.add(x['id'])
                    if c == 'purchases' and (not isint(x.get('qty')) or x['qty'] < 1 or not isnum(x.get('cost')) or x['cost'] < 0):
                        bad('Invalid purchase order')
    if 'loyalty' in changes:
        for k, v in changes['loyalty'].items():
            if not isinstance(v, dict) or not isint(v.get('redeemed')) or v['redeemed'] < 0:
                bad('Invalid loyalty record')
    if 'cust' in changes:
        for k, v in changes['cust'].items():
            if not isinstance(v, dict):
                bad('Invalid customer record')
    if 'waitlist' in changes:
        ids = set()
        for w in changes['waitlist']:
            if not isinstance(w, dict) or not isinstance(w.get('id'), str) or w['id'] in ids or not isinstance(w.get('pid'), str) \
                    or not isinstance(w.get('phone'), str) or not isinstance(w.get('contacted', False), bool):
                bad('Invalid waiting-list entry')
            ids.add(w['id'])
        if len(changes['waitlist']) > 5000:
            bad('The waiting list is too long')
    if 'settings' in changes:
        out['settings'] = v_settings(changes['settings'])
    return out


# ---------------------------------------------------------------- request handler
class H(http.server.BaseHTTPRequestHandler):
    server_version = 'ShagarServer'
    sys_version = ''
    protocol_version = 'HTTP/1.1'

    def log_message(self, fmt, *a):
        if ARGS.verbose:
            sys.stderr.write('%s %s\n' % (self.address_string(), fmt % a))

    def ip(self):
        if ARGS.trust_proxy and self.headers.get('X-Forwarded-For'):
            return self.headers['X-Forwarded-For'].split(',')[0].strip()
        return self.client_address[0]

    def common_headers(self):
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Referrer-Policy', 'same-origin')
        self.send_header('Permissions-Policy', 'camera=(), microphone=(), geolocation=()')
        if ARGS.secure_cookies:
            self.send_header('Strict-Transport-Security', 'max-age=31536000')
        self.send_header('Content-Security-Policy',
                         "default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; "
                         "script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'")

    def send_bytes(self, code, body, ctype, headers=None, nocache=True, etag=None):
        headers = dict(headers or {})
        if len(body) > 1400 and 'gzip' in (self.headers.get('Accept-Encoding') or '') and \
                (ctype.startswith('text/') or 'json' in ctype or 'svg' in ctype or 'javascript' in ctype):
            body = gzip.compress(body, 5)
            headers['Content-Encoding'] = 'gzip'
        headers['Vary'] = 'Accept-Encoding'
        if etag:
            headers['ETag'] = etag
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store' if nocache else 'no-cache')
        self.common_headers()
        for k, v in headers.items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(body)

    def send_json(self, code, obj, headers=None):
        self.send_bytes(code, json.dumps(obj, separators=(',', ':')).encode('utf-8'), 'application/json; charset=utf-8', headers)

    def read_json(self):
        n = int(self.headers.get('Content-Length') or 0)
        if n > 12_000_000:
            raise ApiError(413, 'Request too large')
        raw = self.rfile.read(n) if n else b''
        if not raw:
            return {}
        try:
            return json.loads(raw.decode('utf-8'))
        except Exception:
            raise ApiError(400, 'Invalid JSON')

    def do_GET(self):
        self.route('GET')

    def do_HEAD(self):
        self.route('GET')

    def do_POST(self):
        self.route('POST')

    def route(self, method):
        try:
            u = urllib.parse.urlsplit(self.path)
            path = u.path
            if path.startswith('/api/'):
                if method == 'POST' and self.headers.get('X-Requested-With') != 'XMLHttpRequest':
                    raise ApiError(403, 'Missing request header')
                body = self.read_json() if method == 'POST' else None
                q = {k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()}
                if path == '/api/backups/download' and method == 'GET':
                    return self.download_backup(q)
                if path == '/api/prescriptions/download' and method == 'GET':
                    return self.download_rx(q)
                m = re.fullmatch(r'/api/staff/(\d+)/update', path)
                fn = ROUTES.get((method, path)) or ((lambda s, q, b: api_staff_update(s, q, b, int(m.group(1)))) if (m and method == 'POST') else None)
                if not fn:
                    raise ApiError(404, 'Not found')
                res = fn(self, q, body)
                headers = {}
                if isinstance(res, tuple):
                    res, headers = res
                self.send_json(200, res, headers)
            elif method == 'GET':
                self.static(path)
            else:
                raise ApiError(405, 'Method not allowed')
        except ApiError as e:
            if e.code == 404 and not self.path.startswith('/api/') and os.path.isfile(os.path.join(ROOT, '404.html')):
                page = open(os.path.join(ROOT, '404.html'), 'rb').read().replace(b'</head>', b'<meta name="shagar-server" content="1"></head>', 1)
                self.send_bytes(404, page, 'text/html; charset=utf-8')
            else:
                self.send_json(e.code, dict({'error': e.msg}, **e.extra))
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            traceback.print_exc()
            LOG.exception('Unhandled error for %s %s', method, self.path)
            try:
                self.send_json(500, {'error': 'Server error'})
            except Exception:
                pass

    def download_backup(self, q):
        u = self.session()
        need_role(u, 'Owner')
        name = q.get('name', '')
        if not re.fullmatch(r'(auto|manual)-\d{8}-\d{6}\.db', name) or not os.path.isfile(os.path.join(BACKUP_DIR, name)):
            raise ApiError(404, 'Backup not found')
        conn = db()
        try:
            seclog(conn, u['username'], 'backup_downloaded', self.ip(), name)
        finally:
            conn.close()
        data = open(os.path.join(BACKUP_DIR, name), 'rb').read()
        self.send_bytes(200, data, 'application/octet-stream', {'Content-Disposition': f'attachment; filename="{name}"'})

    def download_rx(self, q):
        u = self.session()
        need_role(u, 'Owner', 'Pharmacist')
        no = str(q.get('no') or '')
        conn = db()
        try:
            orders, _ = kvload(conn, 'orders')
            o = next((x for x in orders if x['no'] == no), None)
            rf = (o or {}).get('rxFile')
            if not rf or rf.get('purged'):
                raise ApiError(404, 'No prescription image for this order')
            path = os.path.join(RX_DIR, rf['id'] + RX_EXT.get(rf['type'], ''))
            if not os.path.isfile(path):
                raise ApiError(404, 'The image is no longer stored')
            seclog(conn, u['username'], 'prescription_viewed', self.ip(), no)
        finally:
            conn.close()
        self.send_bytes(200, open(path, 'rb').read(), rf['type'], {'Content-Disposition': 'inline'})

    # ---- static files
    def static(self, path):
        rel = urllib.parse.unquote(path).lstrip('/')
        parts = [p for p in rel.split('/') if p]
        if any(p.startswith('.') or p in ('server', 'tests', 'deploy', 'node_modules') for p in parts) or '\x00' in rel:
            raise ApiError(404, 'Not found')
        full = os.path.realpath(os.path.join(ROOT, *parts))
        if not (full == ROOT or full.startswith(ROOT + os.sep)):
            raise ApiError(404, 'Not found')
        if os.path.isdir(full):
            full = os.path.join(full, 'index.html')
        if not os.path.isfile(full) or full.lower().endswith(('.py', '.pyc', '.db', '.sqlite', '.md', '.sh', '.env', '.json')) \
                and not full.endswith('manifest.webmanifest'):
            raise ApiError(404, 'Not found')
        ctype = mimetypes.guess_type(full)[0] or 'application/octet-stream'
        if full.endswith('.webmanifest'):
            ctype = 'application/manifest+json'
        if full.endswith('.js'):
            ctype = 'text/javascript; charset=utf-8'
        st = os.stat(full)
        etag = '"%x-%x"' % (st.st_mtime_ns, st.st_size)
        if self.headers.get('If-None-Match') == etag:
            self.send_response(304)
            self.send_header('ETag', etag)
            self.send_header('Cache-Control', 'no-cache')
            self.common_headers()
            self.end_headers()
            return
        data = open(full, 'rb').read()
        if full.endswith('.html'):
            data = data.replace(b'</head>', b'<meta name="shagar-server" content="1"></head>', 1)
            ctype = 'text/html; charset=utf-8'
        self.send_bytes(200, data, ctype, nocache=False, etag=etag)

    # ---- auth
    def session(self, required=True):
        raw = self.headers.get('Cookie') or ''
        m = re.search(r'(?:^|;\s*)sid=([A-Za-z0-9_\-]+)', raw)
        user = None
        if m:
            th = hashlib.sha256(m.group(1).encode()).hexdigest()
            conn = db()
            try:
                r = conn.execute('SELECT s.created, s.last_seen, t.* FROM sessions s JOIN staff t ON t.id=s.staff_id WHERE s.th=?', (th,)).fetchone()
                if r and r['active']:
                    st, _ = kvload(conn, 'settings')
                    idle = (st.get('idleMin') or 0) * 60 or 8 * 3600
                    now = time.time()
                    if now - r['last_seen'] <= idle and now - r['created'] <= 12 * 3600:
                        user = {'id': r['id'], 'username': r['username'], 'name': r['name'], 'role': r['role'], 'must_change': bool(r['must_change']), 'totp_enabled': bool(r['totp_enabled']), 'th': th,
                                'must_2fa': r['role'] in REQ2FA.get(st.get('req2fa', ''), set()) and not r['totp_enabled']}
                        if now - r['last_seen'] > 20:
                            conn.execute('UPDATE sessions SET last_seen=? WHERE th=?', (now, th))
                    else:
                        conn.execute('DELETE FROM sessions WHERE th=?', (th,))
            finally:
                conn.close()
        if required and not user:
            raise ApiError(401, 'Please log in')
        if required and user and user.get('must_2fa'):
            p = self.path.split('?')[0]
            if not (p in ('/api/me', '/api/account', '/api/logout', '/api/password') or p.startswith('/api/account/')):
                raise ApiError(403, 'Your shop requires two-step login. Set it up in My account first.')
        return user


def need_role(user, *roles):
    if user['role'] not in roles:
        raise ApiError(403, 'Not allowed for your role')


# ---------------------------------------------------------------- API: public
def api_ping(h, q, b):
    return {'ok': True, 'mode': 'server'}


def api_me(h, q, b):
    u = h.session(False)
    return {'user': {k: u[k] for k in ('username', 'name', 'role', 'must_change', 'totp_enabled', 'must_2fa')} if u else None}


def api_catalog(h, q, b):
    conn = db()
    try:
        products, _ = kvload(conn, 'products')
        batches, _ = kvload(conn, 'batches')
        st, _ = kvload(conn, 'settings')
    finally:
        conn.close()
    t = today_str()
    out = []
    for p in products:
        use = sorted([x for x in batches if x['pid'] == p['id'] and x['qty'] > 0 and x['exp'] >= t], key=lambda x: x['exp'])
        pub = {k: p.get(k) for k in ('id', 'name', 'bn', 'generic', 'strength', 'maker', 'form', 'pack', 'price', 'disc', 'rx', 'cat', 'img', 'warn', 'reorder')}
        pub['stock'] = sum(x['qty'] for x in use)
        pub['nextExp'] = use[0]['exp'] if use else None
        pub['nextNo'] = use[0].get('no') if use else None
        out.append(pub)
    keep = ('store', 'logoText', 'address', 'phone', 'invoice', 'feeDhaka', 'feeOut', 'receiptFooter')
    pub = {k: st.get(k) for k in keep}
    for k in ('onlineOrders', 'notice', 'freeDeliveryMin', 'minOrder', 'rxRetentionDays'):
        pub[k] = st.get(k, DEFAULT_SETTINGS[k])
    return {'products': out, 'settings': pub, 'slots': SLOTS}


def api_coupon(h, q, b):
    if not rate(h.ip(), 'coupon', 60, 600):
        raise ApiError(429, 'Too many requests. Please wait a few minutes.')
    code = str((b or {}).get('code') or '').strip().upper()
    conn = db()
    try:
        coupons, _ = kvload(conn, 'coupons')
    finally:
        conn.close()
    k = next((x for x in coupons if x['code'].upper() == code and not x.get('off')), None)
    return {'valid': bool(k), 'code': k['code'] if k else None, 'pct': k['pct'] if k else 0, 'min': k.get('min', 0) if k else 0}


def api_order_create(h, q, b):
    if not rate(h.ip(), 'orders', 12, 600):
        raise ApiError(429, 'Too many orders from this connection. Please wait a few minutes.')
    if not isinstance(b, dict):
        bad('Invalid request', 400)
    items, cust = b.get('items'), b.get('customer')
    if not isinstance(items, list) or not 1 <= len(items) <= 50 or not isinstance(cust, dict):
        bad('Your cart is empty or invalid', 400)
    name = sanitize_str(cust.get('name'), 80, 2, 'Name')
    phone = sanitize_str(cust.get('phone'), 20, 1, 'Mobile number')
    if not PHONE_RE.match(phone):
        bad('Enter a valid Bangladesh mobile number', 400)
    area = b.get('area')
    if area not in ('dhaka', 'out', 'pickup'):
        bad('Choose a delivery option', 400)
    pay = b.get('pay')
    if pay not in PAY_OK:
        bad('Choose a payment option', 400)
    parts = {k: str(cust.get(k) or '').strip()[:120] for k in ('addr', 'thana', 'district', 'post', 'division')}
    if area != 'pickup':
        if len(parts['addr']) < 8 or len(parts['thana']) < 2 or len(parts['district']) < 2:
            bad('Enter your full address (house/road, thana and district)', 400)
        if parts['post'] and not re.fullmatch(r'\d{4}', parts['post']):
            bad('Postcode must be 4 digits', 400)
    want = {}
    for it in items:
        if not isinstance(it, dict) or not isinstance(it.get('id'), str) or not isint(it.get('qty')) or not 1 <= it['qty'] <= 99:
            bad('Invalid item in the cart', 400)
        want[it['id']] = want.get(it['id'], 0) + it['qty']
    couponc = str(b.get('coupon') or '').strip().upper()
    doc = str(b.get('doc') or '').strip()[:200]
    slot = str(b.get('slot') or SLOTS[0])
    if slot not in SLOTS:
        bad('Choose a delivery time', 400)
    rxf, rx_bytes, rx_mime, rx_path = b.get('rxFile'), None, None, None
    if rxf:
        if not b.get('rxConsent'):
            bad('Please tick the box that lets the pharmacy keep the prescription image', 400)
        rx_bytes, rx_mime = decode_rx_image(rxf)
    with LOCK:
        conn = db()
        conn.execute('BEGIN IMMEDIATE')
        try:
            products, _ = kvload(conn, 'products')
            batches, _ = kvload(conn, 'batches')
            settings, _ = kvload(conn, 'settings')
            coupons, _ = kvload(conn, 'coupons')
            if not settings.get('onlineOrders', True):
                raise ApiError(503, 'Online ordering is paused right now. Please call the pharmacy or try again later.')
            log, _ = kvload(conn, 'log')
            orders, _ = kvload(conn, 'orders')
            notes, _ = kvload(conn, 'notes')
            cust_rec, _ = kvload(conn, 'cust')
            for k, v in cust_rec.items():
                if nph(k) == nph(phone) and isinstance(v, dict) and v.get('blocked'):
                    raise ApiError(403, 'We cannot accept orders from this number. Please contact the pharmacy.')
            pm = {p['id']: p for p in products}
            rx = False
            for pid, qty in want.items():
                if pid not in pm:
                    raise ApiError(409, 'A product in your cart is no longer available')
                rx = rx or bool(pm[pid].get('rx'))
            if rx and (len(doc) < 3 or not b.get('rxConfirmed')):
                raise ApiError(400, 'Prescription medicines need the doctor name or registration number and your confirmation')
            seq = int(meta_get(conn, 'order_seq', '1000')) + 1
            meta_set(conn, 'order_seq', seq)
            no = f"{settings.get('invoice', 'INV')}-{seq}"
            now = now_iso()
            lines, sub = [], 0
            for pid, qty in want.items():
                p = pm[pid]
                have = stock_of(batches, pid)
                if have < qty:
                    raise ApiError(409, f"Only {have} left of {p['name']}" if have else f"{p['name']} is out of stock")
                if not fefo_take(batches, log, pid, qty, no, now):
                    raise ApiError(409, f"Not enough unexpired stock of {p['name']}")
                lines.append({'pid': pid, 'name': p['name'], 'qty': qty, 'price': eff(p), 'rx': bool(p.get('rx'))})
                sub += eff(p) * qty
            disc = 0
            if couponc:
                k = next((x for x in coupons if x['code'].upper() == couponc and not x.get('off')), None)
                if not k:
                    raise ApiError(400, 'Invalid coupon')
                if sub < k.get('min', 0):
                    raise ApiError(400, f"This coupon needs an order of at least ৳{k.get('min', 0)}")
                disc = js_round(sub * k['pct'] / 100)
            if sub < settings.get('minOrder', 0):
                raise ApiError(400, f"The minimum order is ৳{settings.get('minOrder', 0)}")
            fmin = settings.get('freeDeliveryMin', 0)
            fee = 0 if (area == 'pickup' or (fmin > 0 and sub - disc >= fmin)) else (settings.get('feeOut', 120) if area == 'out' else settings.get('feeDhaka', 60))
            status = 'Prescription Review' if rx else 'Pending'
            addr = 'Store pickup' if area == 'pickup' else ', '.join(x for x in (parts['addr'], parts['thana'], parts['district'], parts['division'], parts['post']) if x)
            order = {'id': 'O-' + secrets.token_hex(5), 'no': no, 'at': now, 'customer': name, 'phone': phone, 'addr': addr,
                     'items': lines, 'rx': rx, 'status': status, 'pay': pay, 'doc': doc if rx else '', 'sub': sub, 'disc': disc,
                     'fee': fee, 'loy': 0, 'total': sub - disc + fee,
                     'delivery': 'Store pickup' if area == 'pickup' else 'Home delivery',
                     'hist': [{'s': status, 'at': now, 'by': 'Customer'}]}
            order['slot'] = '' if area == 'pickup' else slot
            if rx and rx_bytes:
                fid = secrets.token_hex(16)
                rx_path = os.path.join(RX_DIR, fid + RX_EXT[rx_mime])
                with open(rx_path, 'wb') as fh:
                    fh.write(rx_bytes)
                os.chmod(rx_path, 0o600)
                order['rxFile'] = {'id': fid, 'type': rx_mime, 'size': len(rx_bytes), 'at': now}
            orders.append(order)
            notes.append({'id': 'N-' + secrets.token_hex(4), 'at': now, 'msg': f"New order {no}" + (' – prescription review needed' if rx else ''), 'read': False})
            for c, d in (('batches', batches), ('log', log), ('orders', orders), ('notes', notes)):
                kvstore(conn, c, d)
            conn.execute('COMMIT')
        except Exception:
            conn.execute('ROLLBACK')
            if rx_path and os.path.exists(rx_path):
                os.remove(rx_path)
            raise
        finally:
            conn.close()
    return {'order': order}


def decode_rx_image(rxf):
    if not isinstance(rxf, dict) or not isinstance(rxf.get('data'), str):
        bad('Invalid prescription image', 400)
    raw = rxf['data'].split(',', 1)[-1]
    if len(raw) > MAX_RX * 4 // 3 + 16:
        bad('The prescription image is too large (max 3 MB)', 400)
    try:
        data = base64.b64decode(raw, validate=True)
    except Exception:
        bad('Invalid prescription image', 400)
    if len(data) > MAX_RX or len(data) < 200:
        bad('The prescription image must be between 200 bytes and 3 MB', 400)
    if data[:3] == b'\xff\xd8\xff':
        return data, 'image/jpeg'
    if data[:8] == b'\x89PNG\r\n\x1a\n':
        return data, 'image/png'
    if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        return data, 'image/webp'
    bad('Only JPG, PNG or WebP images are accepted', 400)


def purge_prescriptions(days=None):
    """Delete prescription images older than the retention period (settings.rxRetentionDays, 0 = keep)."""
    with LOCK:
        conn = db()
        conn.execute('BEGIN IMMEDIATE')
        try:
            st, _ = kvload(conn, 'settings')
            d = st.get('rxRetentionDays', 30) if days is None else days
            n = 0
            if d:
                cutoff = (datetime.now(timezone.utc) - timedelta(days=d)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
                orders, _ = kvload(conn, 'orders')
                for o in orders:
                    rf = o.get('rxFile')
                    if rf and not rf.get('purged') and rf.get('at', '') < cutoff:
                        p = os.path.join(RX_DIR, rf['id'] + RX_EXT.get(rf.get('type'), ''))
                        if os.path.exists(p):
                            os.remove(p)
                        rf['purged'] = True
                        n += 1
                if n:
                    kvstore(conn, 'orders', orders)
                    seclog(conn, None, 'prescriptions_purged', 'system', f'{n} image(s) older than {d} days')
            conn.execute('COMMIT')
            return n
        except Exception:
            conn.execute('ROLLBACK')
            raise
        finally:
            conn.close()


def api_waitlist(h, q, b):
    if not rate(h.ip(), 'waitlist', 8, 600):
        raise ApiError(429, 'Too many requests. Please wait a few minutes.')
    b = b or {}
    pid = str(b.get('pid') or '')
    phone = sanitize_str(b.get('phone'), 20, 1, 'Mobile number')
    if not PHONE_RE.match(phone):
        bad('Enter a valid Bangladesh mobile number', 400)
    name = str(b.get('name') or '').strip()[:60]
    with LOCK:
        conn = db()
        conn.execute('BEGIN IMMEDIATE')
        try:
            products, _ = kvload(conn, 'products')
            batches, _ = kvload(conn, 'batches')
            wl, _ = kvload(conn, 'waitlist')
            p = next((x for x in products if x['id'] == pid), None)
            if not p:
                raise ApiError(404, 'Product not found')
            if stock_of(batches, pid) > 0:
                raise ApiError(409, 'This medicine is in stock now')
            if not any(w['pid'] == pid and nph(w['phone']) == nph(phone) and not w.get('contacted') for w in wl):
                if sum(1 for w in wl if nph(w['phone']) == nph(phone) and not w.get('contacted')) >= 10:
                    raise ApiError(429, 'Too many waiting-list requests for this number')
                wl.append({'id': 'W-' + secrets.token_hex(4), 'pid': pid, 'name': name, 'phone': phone, 'at': now_iso(), 'contacted': False})
                kvstore(conn, 'waitlist', wl)
            conn.execute('COMMIT')
        except Exception:
            conn.execute('ROLLBACK')
            raise
        finally:
            conn.close()
    return {'ok': True}


def phone_arg(b_or_q):
    ph = str((b_or_q or {}).get('phone') or '').strip()
    if not PHONE_RE.match(ph):
        bad('Enter a valid Bangladesh mobile number', 400)
    return ph


def api_privacy_export(h, q, b):
    u = h.session()
    need_role(u, 'Owner')
    ph = phone_arg(q)
    conn = db()
    try:
        data = {c: kvload(conn, c)[0] for c in ('orders', 'messages', 'waitlist', 'loyalty', 'cust', 'sales')}
        out = {'phone': ph, 'exported_at': now_iso(),
               'orders': [o for o in data['orders'] if nph(o.get('phone')) == nph(ph)],
               'messages': [m for m in data['messages'] if nph(m.get('phone')) == nph(ph)],
               'waiting_list': [w for w in data['waitlist'] if nph(w.get('phone')) == nph(ph)],
               'counter_sales_with_this_number': [s for s in data['sales'] if nph(s.get('phone')) == nph(ph)],
               'loyalty': {k: v for k, v in data['loyalty'].items() if nph(k) == nph(ph)},
               'customer_notes': {k: v for k, v in data['cust'].items() if nph(k) == nph(ph)}}
        seclog(conn, u['username'], 'customer_data_exported', h.ip(), '...' + nph(ph)[-3:])
        return out
    finally:
        conn.close()


def api_privacy_erase(h, q, b):
    u = h.session()
    need_role(u, 'Owner')
    ph = phone_arg(b)
    if (b or {}).get('confirm') != 'ERASE':
        bad('Type ERASE to confirm', 400)
    tag = 'erased-' + hashlib.sha256(nph(ph).encode()).hexdigest()[:8]
    with LOCK:
        conn = db()
        conn.execute('BEGIN IMMEDIATE')
        try:
            orders, _ = kvload(conn, 'orders')
            msgs, _ = kvload(conn, 'messages')
            wl, _ = kvload(conn, 'waitlist')
            loy, _ = kvload(conn, 'loyalty')
            cust, _ = kvload(conn, 'cust')
            sales, _ = kvload(conn, 'sales')
            notes, _ = kvload(conn, 'notes')
            n_o = n_m = n_img = 0
            for o in orders:
                if nph(o.get('phone')) == nph(ph):
                    o['customer'], o['phone'], o['addr'], o['doc'] = 'Erased customer', tag, '(removed)', ''
                    rf = o.get('rxFile')
                    if rf and not rf.get('purged'):
                        p = os.path.join(RX_DIR, rf['id'] + RX_EXT.get(rf.get('type'), ''))
                        if os.path.exists(p):
                            os.remove(p)
                        rf['purged'] = True
                        n_img += 1
                    n_o += 1
            refs = set()
            for m in msgs:
                if nph(m.get('phone')) == nph(ph):
                    refs.add(m.get('ref'))
                    m['name'], m['phone'], m['msg'], m['order'] = '(erased)', tag, '(erased)', ''
                    n_m += 1
            for n in notes:
                if any(r and (' ' + r + ' ') in (' ' + str(n.get('msg', '')) + ' ') for r in refs) or nph(ph) in str(n.get('msg', '')):
                    n['msg'] = 'Customer message (erased)'
            wl2 = [w for w in wl if nph(w.get('phone')) != nph(ph)]
            for k in [k for k in loy if nph(k) == nph(ph)]:
                del loy[k]
            for k in [k for k in cust if nph(k) == nph(ph)]:
                del cust[k]
            for s_ in sales:
                if nph(s_.get('phone')) == nph(ph):
                    s_['phone'] = ''
            for c, d in (('orders', orders), ('messages', msgs), ('waitlist', wl2), ('loyalty', loy), ('cust', cust), ('sales', sales), ('notes', notes)):
                kvstore(conn, c, d)
            seclog(conn, u['username'], 'customer_erased', h.ip(), f"...{nph(ph)[-3:]}: {n_o} order(s), {n_m} message(s), {n_img} image(s), {len(wl) - len(wl2)} waiting-list entr(y/ies)")
            conn.execute('COMMIT')
        except Exception:
            conn.execute('ROLLBACK')
            raise
        finally:
            conn.close()
    return {'ok': True, 'orders': n_o, 'messages': n_m, 'images': n_img}


def find_order(orders, no, phone):
    no = str(no or '').strip().lower()
    return next((o for o in orders if o['no'].lower() == no and nph(o['phone']) == nph(phone)), None)


def api_order_lookup(h, q, b):
    if not rate(h.ip(), 'lookup', 60, 600):
        raise ApiError(429, 'Too many lookups. Please wait a few minutes.')
    conn = db()
    try:
        orders, _ = kvload(conn, 'orders')
    finally:
        conn.close()
    o = find_order(orders, (b or {}).get('no'), (b or {}).get('phone'))
    if not o:
        raise ApiError(404, 'No order found with that number and mobile number.')
    return {'order': o}


def api_order_lookup_many(h, q, b):
    if not rate(h.ip(), 'lookup', 60, 600):
        raise ApiError(429, 'Too many lookups. Please wait a few minutes.')
    lst = (b or {}).get('orders')
    if not isinstance(lst, list):
        bad('Invalid request', 400)
    conn = db()
    try:
        orders, _ = kvload(conn, 'orders')
    finally:
        conn.close()
    out = []
    for x in lst[:30]:
        if isinstance(x, dict):
            o = find_order(orders, x.get('no'), x.get('phone'))
            if o:
                out.append(o)
    return {'orders': out}


def customer_change(b, expect_status, new_status, reason_needed=False, note_msg=''):
    if not rate(b['_ip'], 'lookup', 60, 600):
        raise ApiError(429, 'Too many requests. Please wait a few minutes.')
    reason = None
    if reason_needed:
        reason = str(b.get('reason') or '').strip()
        if not 3 <= len(reason) <= 200:
            bad('Please give a reason (3-200 characters)', 400)
    with LOCK:
        conn = db()
        conn.execute('BEGIN IMMEDIATE')
        try:
            orders, _ = kvload(conn, 'orders')
            o = find_order(orders, b.get('no'), b.get('phone'))
            if not o:
                raise ApiError(404, 'No order found with that number and mobile number.')
            if o['status'] not in expect_status:
                raise ApiError(409, f"This order is {o['status']} and cannot be changed now.")
            now = now_iso()
            if new_status == 'Cancelled':
                batches, _ = kvload(conn, 'batches')
                log, _ = kvload(conn, 'log')
                for l in [x for x in log if x.get('ref') == o['no'] and x.get('delta', 0) < 0 and x.get('why') == 'sale']:
                    bt = next((x for x in batches if x['id'] == l.get('batch')), None)
                    if bt:
                        bt['qty'] += -l['delta']
                        log.append({'at': now, 'pid': l['pid'], 'batch': bt['id'], 'delta': -l['delta'], 'ref': o['no'], 'why': 'restock'})
                kvstore(conn, 'batches', batches)
                kvstore(conn, 'log', log)
            o['status'] = new_status
            o['hist'].append({'s': new_status, 'at': now, 'by': 'Customer'})
            if reason:
                o['reason'] = reason
            notes, _ = kvload(conn, 'notes')
            notes.append({'id': 'N-' + secrets.token_hex(4), 'at': now, 'msg': note_msg.format(no=o['no']), 'read': False})
            kvstore(conn, 'orders', orders)
            kvstore(conn, 'notes', notes)
            conn.execute('COMMIT')
        except Exception:
            conn.execute('ROLLBACK')
            raise
        finally:
            conn.close()
    return {'order': o}


def api_order_cancel(h, q, b):
    b = dict(b or {}, _ip=h.ip())
    return customer_change(b, ['Pending', 'Confirmed', 'Prescription Review'], 'Cancelled', False, 'Order {no} was cancelled by the customer')


def api_order_return(h, q, b):
    b = dict(b or {}, _ip=h.ip())
    return customer_change(b, ['Delivered'], 'Return Requested', True, 'Return requested for {no}')


def api_contact(h, q, b):
    if not rate(h.ip(), 'contact', 5, 600):
        raise ApiError(429, 'Too many messages. Please wait a few minutes.')
    b = b or {}
    n = sanitize_str(b.get('n'), 80, 2, 'Name')
    ph = sanitize_str(b.get('ph'), 20, 1, 'Mobile number')
    if not PHONE_RE.match(ph):
        bad('Enter a valid Bangladesh mobile number', 400)
    t = sanitize_str(b.get('t') or 'Other', 40, 1, 'Topic')
    o = str(b.get('o') or '').strip().upper()[:20]
    if o and not re.fullmatch(r'[A-Z]{2,8}-\d+', o):
        bad('Order numbers look like INV-1001', 400)
    m = sanitize_str(b.get('m'), 500, 5, 'Message')
    with LOCK:
        conn = db()
        conn.execute('BEGIN IMMEDIATE')
        try:
            msgs, _ = kvload(conn, 'messages')
            notes, _ = kvload(conn, 'notes')
            ref = 'CT-%d' % (1001 + len(msgs))
            now = now_iso()
            msgs.append({'id': 'M-' + secrets.token_hex(4), 'ref': ref, 'at': now, 'name': n, 'phone': ph, 'topic': t, 'order': o, 'msg': m})
            notes.append({'id': 'N-' + secrets.token_hex(4), 'at': now, 'msg': f'Contact {ref} ({t}) from {n} ({ph}): {m[:300]}', 'read': False})
            kvstore(conn, 'messages', msgs)
            kvstore(conn, 'notes', notes)
            conn.execute('COMMIT')
        except Exception:
            conn.execute('ROLLBACK')
            raise
        finally:
            conn.close()
    return {'ref': ref}


# ---------------------------------------------------------------- API: staff
DUMMY = None


def dummy_check(pw):
    global DUMMY
    if DUMMY is None:
        DUMMY = hash_pw('dummy-password-for-timing')
    check_pw(pw, *DUMMY)


def norm_recovery(code):
    return hashlib.sha256(re.sub(r'[\s-]', '', str(code)).upper().encode()).hexdigest()


def pw_age_days(r):
    """Days since the password was last set (falls back to the account creation date)."""
    try:
        t = datetime.fromisoformat(str(r['pw_changed'] or r['created']).replace('Z', '+00:00'))
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
        return max(0, int((datetime.now(timezone.utc) - t).total_seconds() // 86400))
    except Exception:
        return 0


def needs_setup(conn=None):
    c = conn or db()
    try:
        return c.execute('SELECT COUNT(*) AS n FROM staff').fetchone()['n'] == 0
    finally:
        if conn is None:
            c.close()


def api_setup_status(h, q, b):
    return {'needed': needs_setup()}


def api_setup(h, q, b):
    """First-run Owner creation from the browser. Works only while there are no staff accounts, and needs the
    one-time setup code that the server prints in its own window (so a stranger who reaches the page first cannot take over)."""
    ip, b = h.ip(), b or {}
    if not rate(ip, 'setup', 10, 600):
        raise ApiError(429, 'Too many attempts. Please wait a few minutes.')
    username = str(b.get('username') or '').strip().lower()
    name = str(b.get('name') or '').strip()[:60]
    pw, code = str(b.get('password') or ''), str(b.get('code') or '').strip()
    with LOCK:
        conn = db()
        try:
            if not needs_setup(conn) or not SETUP['code']:
                raise ApiError(409, 'Setup is already done. Please log in.')
            if not hmac.compare_digest(code.encode(), SETUP['code'].encode()):
                seclog(conn, None, 'setup_wrong_code', ip)
                raise ApiError(403, 'The setup code is not correct. It is shown in the server window.')
            if not re.fullmatch(r'[a-z0-9_.-]{3,30}', username):
                bad('Username: 3 to 30 letters, digits, dot, dash or underscore', 400)
            if len(name) < 2:
                bad('Please enter your name', 400)
            check_new_password(pw, username)
            salt, hh = hash_pw(pw)
            conn.execute('INSERT INTO staff(username,name,role,salt,pw,active,must_change,created,pw_changed) VALUES(?,?,?,?,?,1,0,?,?)',
                         (username, name, 'Owner', salt, hh, now_iso(), now_iso()))
            seclog(conn, username, 'owner_created', ip, 'first-run setup')
            SETUP['code'] = None
        finally:
            conn.close()
    return {'ok': True}


def api_login(h, q, b):
    ip = h.ip()
    b = b or {}
    username = str(b.get('username') or '').strip().lower()[:60]
    pw, code = str(b.get('password') or ''), str(b.get('code') or '')
    conn = db()
    try:
        if not rate(ip, 'login', 20, 600):
            seclog(conn, username or None, 'login_rate_limited', ip)
            raise ApiError(429, 'Too many login attempts. Please wait a few minutes.')
        r = conn.execute('SELECT * FROM staff WHERE username=?', (username,)).fetchone()
        now = time.time()
        if r and r['locked_until'] > now:
            seclog(conn, username, 'login_blocked_locked', ip)
            raise ApiError(429, 'This account is temporarily locked after too many wrong attempts. Try again later or ask the Owner to unlock it.')

        def fail(event, msg):
            if r:
                failed = r['failed'] + 1
                lock = now + 900 if failed >= 5 else 0
                conn.execute('UPDATE staff SET failed=?, locked_until=? WHERE id=?', (0 if lock else failed, lock, r['id']))
                seclog(conn, username, 'account_locked' if lock else event, ip)
            else:
                seclog(conn, username or '(empty)', event, ip)
            raise ApiError(401, msg)
        if r and r['active']:
            pw_ok = check_pw(pw, r['salt'], r['pw'])
        else:
            dummy_check(pw)
            pw_ok = False
        if not pw_ok:
            fail('login_failed', 'Wrong username or password')
        if r['totp_enabled']:
            if not code.strip():
                raise ApiError(401, 'Enter the 6-digit code from your authenticator app (or a recovery code)', {'needs_code': True})
            ctr = totp_verify(r['totp_secret'], code, r['totp_last'])
            if ctr is not None:
                conn.execute('UPDATE staff SET totp_last=? WHERE id=?', (ctr, r['id']))
            else:
                rec = json.loads(r['recovery'] or '[]')
                hh = norm_recovery(code)
                if hh in rec:
                    rec.remove(hh)
                    conn.execute('UPDATE staff SET recovery=? WHERE id=?', (json.dumps(rec), r['id']))
                    seclog(conn, username, 'recovery_code_used', ip, f'{len(rec)} left')
                else:
                    fail('login_wrong_code', 'That code is not right')
        pol, _ = kvload(conn, 'settings')
        if not hours_ok(pol, r['role']):
            seclog(conn, username, 'login_outside_hours', ip)
            raise ApiError(403, f"Staff sign-in is allowed only between {pol.get('hoursFrom', 8)}:00 and {pol.get('hoursTo', 22)}:00 (Dhaka time). Ask the Owner if you need access now.")
        if pol.get('pwMaxDays', 0) and pw_age_days(r) >= pol['pwMaxDays'] and not r['must_change']:
            conn.execute('UPDATE staff SET must_change=1 WHERE id=?', (r['id'],))
            seclog(conn, username, 'password_expired', ip, f"older than {pol['pwMaxDays']} days")
            r = dict(r, must_change=1)
        new_address = bool(r['last_ip']) and r['last_ip'] != ip
        if new_address:
            seclog(conn, username, 'login_new_address', ip, 'previous address ' + str(r['last_ip']))
        conn.execute('UPDATE staff SET failed=0, locked_until=0, prev_login=last_login, prev_ip=last_ip, last_login=?, last_ip=? WHERE id=?', (now_iso(), ip, r['id']))
        conn.execute('DELETE FROM sessions WHERE created<?', (now - 12 * 3600,))
        token = secrets.token_urlsafe(32)
        conn.execute('INSERT INTO sessions(th,staff_id,created,last_seen,ip,ua) VALUES(?,?,?,?,?,?)',
                     (hashlib.sha256(token.encode()).hexdigest(), r['id'], now, now, ip, (h.headers.get('User-Agent') or '')[:200]))
        cap = pol.get('maxSessions', 0)
        if cap:
            old = conn.execute('SELECT th FROM sessions WHERE staff_id=? ORDER BY created DESC', (r['id'],)).fetchall()[cap:]
            for o in old:
                conn.execute('DELETE FROM sessions WHERE th=?', (o['th'],))
            if old:
                seclog(conn, username, 'older_sessions_closed', ip, f'{len(old)} older device(s) signed out (limit {cap})')
        seclog(conn, username, 'login_ok', ip)
        secure = '; Secure' if (ARGS.secure_cookies or h.headers.get('X-Forwarded-Proto') == 'https') else ''
        cookie = f'sid={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age={12 * 3600}{secure}'
        return {'user': {'username': r['username'], 'name': r['name'], 'role': r['role'], 'must_change': bool(r['must_change']), 'totp_enabled': bool(r['totp_enabled']),
                         'must_2fa': r['role'] in REQ2FA.get(pol.get('req2fa', ''), set()) and not r['totp_enabled'],
                         'pw_age_days': pw_age_days(r), 'new_address': new_address, 'prev_login': r['last_login'], 'prev_ip': r['last_ip']}}, {'Set-Cookie': cookie}
    finally:
        conn.close()


def api_logout(h, q, b):
    u = h.session(False)
    if u:
        conn = db()
        try:
            conn.execute('DELETE FROM sessions WHERE th=?', (u['th'],))
            seclog(conn, u['username'], 'logout', h.ip())
        finally:
            conn.close()
    return {'ok': True}, {'Set-Cookie': 'sid=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0'}


def totp_at(secret_b32, counter, digits=6):
    key = base64.b32decode(secret_b32 + '=' * ((8 - len(secret_b32) % 8) % 8))
    h = hmac.new(key, counter.to_bytes(8, 'big'), hashlib.sha1).digest()
    o = h[-1] & 15
    return str((int.from_bytes(h[o:o + 4], 'big') & 0x7fffffff) % 10 ** digits).zfill(digits)


def totp_verify(secret, code, last_counter=0):
    code = re.sub(r'\s', '', str(code or ''))
    if not re.fullmatch(r'\d{6}', code):
        return None
    now = int(time.time() // 30)
    for c in (now - 1, now, now + 1):
        if c > last_counter and hmac.compare_digest(totp_at(secret, c), code):
            return c
    return None


COMMON_PW = {'password123', '1234567890', 'qwertyuiop', 'iloveyou12', 'admin12345', 'letmein123', 'welcome123', 'password1234',
             'shagar12345', 'medical1234', 'pharmacy123', '0123456789', 'abcdefghij', 'qwerty12345'}


def check_new_password(pw, username=None):
    if not isinstance(pw, str) or len(pw) < 10 or len(pw) > 200:
        bad('The new password must be at least 10 characters', 400)
    low = pw.lower()
    if low in COMMON_PW or len(set(pw)) < 4:
        bad('That password is too easy to guess', 400)
    if username and len(username) >= 3 and username.lower() in low:
        bad('The password must not contain the username', 400)
    classes = sum(bool(re.search(p, pw)) for p in (r'[a-z]', r'[A-Z]', r'\d', r'[^A-Za-z0-9]'))
    if classes < 2:
        bad('Use at least two kinds of characters (letters, digits, symbols)', 400)


def api_password(h, q, b):
    u = h.session()
    b = b or {}
    check_new_password(b.get('new'), u['username'])
    conn = db()
    try:
        r = conn.execute('SELECT * FROM staff WHERE id=?', (u['id'],)).fetchone()
        if not check_pw(str(b.get('old') or ''), r['salt'], r['pw']):
            seclog(conn, u['username'], 'password_change_failed', h.ip())
            raise ApiError(401, 'The current password is wrong')
        salt, hh = hash_pw(b['new'])
        conn.execute('UPDATE staff SET salt=?, pw=?, must_change=0, pw_changed=? WHERE id=?', (salt, hh, now_iso(), u['id']))
        conn.execute('DELETE FROM sessions WHERE staff_id=? AND th<>?', (u['id'], u['th']))
        seclog(conn, u['username'], 'password_changed', h.ip(), 'other sessions ended')
    finally:
        conn.close()
    return {'ok': True}


def api_state_get(h, q, b):
    user = h.session()
    conn = db()
    try:
        data, vers = {}, {}
        for c in COLLS:
            data[c], vers[c] = kvload(conn, c)
    finally:
        conn.close()
    out, v = view_for(user['role'], data, vers)
    if q.get('since') is not None and str(sum(v.values())) == q.get('since'):
        return {'changed': False}
    return {'versions': v, 'data': out}


def api_state_post(h, q, b):
    user = h.session()
    if user['must_change']:
        raise ApiError(403, 'Please change your password first')
    b = b or {}
    cs = b.get('changes')
    if isinstance(cs, dict) and isinstance(cs.get('settings'), dict) and cs['settings'].get('req2fa') and not user['totp_enabled']:
        raise ApiError(400, 'Turn on your own two-step login first (My account), then require it for others.')
    base, changes = b.get('base') or {}, b.get('changes')
    if not isinstance(changes, dict) or not changes or not isinstance(base, dict):
        bad('Nothing to save', 400)
    if any(c not in COLLS for c in changes):
        bad('Unknown data set', 400)
    with LOCK:
        conn = db()
        conn.execute('BEGIN IMMEDIATE')
        try:
            old, vers = {}, {}
            for c in COLLS:
                old[c], vers[c] = kvload(conn, c)
            for c in changes:
                if base.get(c) != vers[c]:
                    raise ApiError(409, 'This data was changed on another device. It has been refreshed; please repeat your change.')
            clean = validate(user['role'], old, changes)
            for c, data in clean.items():
                kvstore(conn, c, data)
                vers[c] += 1
            conn.execute('COMMIT')
        except Exception:
            conn.execute('ROLLBACK')
            raise
        finally:
            conn.close()
    out, v = view_for(user['role'], clean, vers)
    return {'ok': True, 'versions': v, 'data': out}


def api_staff_list(h, q, b):
    u = h.session()
    need_role(u, 'Owner')
    conn = db()
    try:
        rows = conn.execute('SELECT id,username,name,role,active,must_change,totp_enabled,last_login,last_ip,locked_until,created,pw_changed,'
                            '(SELECT COUNT(*) FROM sessions WHERE sessions.staff_id=staff.id) AS sessions FROM staff ORDER BY id').fetchall()
    finally:
        conn.close()
    now = time.time()
    out = []
    for r in rows:
        d = dict(r)
        d['locked'] = d.pop('locked_until') > now
        d['pw_age_days'] = pw_age_days(d)
        out.append(d)
    return {'staff': out}


def api_staff_create(h, q, b):
    u = h.session()
    need_role(u, 'Owner')
    b = b or {}
    username = sanitize_str(b.get('username'), 30, 3, 'Username').lower()
    if not re.fullmatch(r'[a-z0-9._-]+', username):
        bad('Username may use letters, digits, dot, dash and underscore', 400)
    name = sanitize_str(b.get('name'), 80, 2, 'Name')
    if b.get('role') not in ROLES:
        bad('Choose a role', 400)
    check_new_password(b.get('password'), username)
    salt, hh = hash_pw(b['password'])
    conn = db()
    try:
        try:
            conn.execute('INSERT INTO staff(username,name,role,salt,pw,active,must_change,created) VALUES(?,?,?,?,?,1,1,?)',
                         (username, name, b['role'], salt, hh, now_iso()))
        except sqlite3.IntegrityError:
            raise ApiError(409, 'That username is already taken')
        seclog(conn, u['username'], 'staff_created', h.ip(), f"{username} ({b['role']})")
    finally:
        conn.close()
    return {'ok': True}


def api_staff_update(h, q, b, sid):
    u = h.session()
    need_role(u, 'Owner')
    b = b or {}
    with LOCK:
        conn = db()
        try:
            r = conn.execute('SELECT * FROM staff WHERE id=?', (sid,)).fetchone()
            if not r:
                raise ApiError(404, 'Staff member not found')
            other_owner = conn.execute("SELECT COUNT(*) n FROM staff WHERE role='Owner' AND active=1 AND id<>?", (sid,)).fetchone()['n'] > 0
            who = r['username']
            if 'active' in b:
                if not b['active'] and r['role'] == 'Owner' and not other_owner:
                    raise ApiError(409, 'Keep at least one active Owner')
                conn.execute('UPDATE staff SET active=? WHERE id=?', (1 if b['active'] else 0, sid))
                if not b['active']:
                    conn.execute('DELETE FROM sessions WHERE staff_id=?', (sid,))
                seclog(conn, u['username'], 'staff_activated' if b['active'] else 'staff_deactivated', h.ip(), who)
            if 'name' in b or 'role' in b:
                name = sanitize_str(b.get('name', r['name']), 80, 2, 'Name')
                role = b.get('role', r['role'])
                if role not in ROLES:
                    bad('Choose a role', 400)
                if r['role'] == 'Owner' and role != 'Owner' and not other_owner:
                    raise ApiError(409, 'Keep at least one active Owner')
                conn.execute('UPDATE staff SET name=?, role=? WHERE id=?', (name, role, sid))
                if role != r['role']:
                    conn.execute('DELETE FROM sessions WHERE staff_id=?', (sid,))
                    seclog(conn, u['username'], 'staff_role_changed', h.ip(), f"{who}: {r['role']} -> {role}")
            if b.get('unlock'):
                conn.execute('UPDATE staff SET failed=0, locked_until=0 WHERE id=?', (sid,))
                seclog(conn, u['username'], 'staff_unlocked', h.ip(), who)
            if b.get('reset_2fa'):
                conn.execute('UPDATE staff SET totp_enabled=0, totp_secret=NULL, totp_pending=NULL, recovery=NULL, totp_last=0 WHERE id=?', (sid,))
                conn.execute('DELETE FROM sessions WHERE staff_id=?', (sid,))
                seclog(conn, u['username'], 'staff_2fa_reset', h.ip(), who)
            if b.get('logout_all'):
                conn.execute('DELETE FROM sessions WHERE staff_id=?', (sid,))
                seclog(conn, u['username'], 'staff_signed_out', h.ip(), who)
            if b.get('password'):
                check_new_password(b['password'], who)
                salt, hh = hash_pw(b['password'])
                conn.execute('UPDATE staff SET salt=?, pw=?, must_change=1, failed=0, locked_until=0 WHERE id=?', (salt, hh, sid))
                conn.execute('DELETE FROM sessions WHERE staff_id=?', (sid,))
                seclog(conn, u['username'], 'staff_password_reset', h.ip(), who)
        finally:
            conn.close()
    return {'ok': True}


def api_restore(h, q, b):
    u = h.session()
    need_role(u, 'Owner')
    d = (b or {}).get('data')
    if not isinstance(d, dict):
        bad('Not a backup file', 400)
    new = {c: d.get(c, {} if c in DICT_COLLS else []) for c in COLLS}
    for c in COLLS:
        if not isinstance(new[c], dict if c in DICT_COLLS else list):
            bad(f'Backup: {c} has the wrong type')
    ids = v_products(new['products'])
    for bt in new['batches']:
        if not isinstance(bt, dict) or bt.get('pid') not in ids or not isint(bt.get('qty')) or bt['qty'] < 0 or not re.fullmatch(r'\d{4}-\d\d-\d\d', str(bt.get('exp', ''))):
            bad('Backup: invalid batch')
    for o in new['orders']:
        if not isinstance(o, dict) or o.get('status') not in STATUS or not isnum(o.get('total')) or not isinstance(o.get('items'), list) or not isinstance(o.get('id'), str):
            bad('Backup: invalid order')
    new['settings'] = v_settings(new['settings'] or {})
    with LOCK:
        shutil.copy(DB_PATH, DB_PATH + '.before-restore-' + str(int(time.time())))
        conn = db()
        conn.execute('BEGIN IMMEDIATE')
        try:
            for c in COLLS:
                kvload(conn, c)
                kvstore(conn, c, new[c])
            conn.execute('COMMIT')
        except Exception:
            conn.execute('ROLLBACK')
            raise
        finally:
            conn.close()
    return {'ok': True}


def public_user(r):
    return {'username': r['username'], 'name': r['name'], 'role': r['role'], 'totp_enabled': bool(r['totp_enabled']),
            'last_login': r['prev_login'], 'last_ip': r['prev_ip']}


def api_account(h, q, b):
    u = h.session()
    conn = db()
    try:
        r = conn.execute('SELECT * FROM staff WHERE id=?', (u['id'],)).fetchone()
        sess = [{'id': x['th'][:12], 'created': x['created'], 'last_seen': x['last_seen'], 'ip': x['ip'], 'ua': x['ua'], 'current': x['th'] == u['th']}
                for x in conn.execute('SELECT * FROM sessions WHERE staff_id=? ORDER BY last_seen DESC', (u['id'],))]
        recent = [dict(e) for e in conn.execute('SELECT at,event,ip,detail FROM security_log WHERE user=? ORDER BY id DESC LIMIT 15', (u['username'],))]
        return {'user': public_user(r), 'pw_age_days': pw_age_days(r), 'sessions': sess, 'recent': recent, 'recovery_left': len(json.loads(r['recovery'] or '[]'))}
    finally:
        conn.close()


def api_2fa_start(h, q, b):
    u = h.session()
    conn = db()
    try:
        r = conn.execute('SELECT * FROM staff WHERE id=?', (u['id'],)).fetchone()
        if r['totp_enabled']:
            raise ApiError(409, 'Two-step login is already on')
        secret = base64.b32encode(secrets.token_bytes(20)).decode().rstrip('=')
        conn.execute('UPDATE staff SET totp_pending=? WHERE id=?', (secret, u['id']))
        st, _ = kvload(conn, 'settings')
        issuer = urllib.parse.quote(st.get('store', 'Shagar Medical Store'))
        uri = f"otpauth://totp/{issuer}:{urllib.parse.quote(r['username'])}?secret={secret}&issuer={issuer}&algorithm=SHA1&digits=6&period=30"
        return {'secret': secret, 'uri': uri}
    finally:
        conn.close()


def api_2fa_enable(h, q, b):
    u = h.session()
    b = b or {}
    conn = db()
    try:
        r = conn.execute('SELECT * FROM staff WHERE id=?', (u['id'],)).fetchone()
        if not check_pw(str(b.get('password') or ''), r['salt'], r['pw']):
            raise ApiError(401, 'The password is wrong')
        if not r['totp_pending']:
            raise ApiError(409, 'Start the setup first')
        ctr = totp_verify(r['totp_pending'], b.get('code'), 0)
        if ctr is None:
            raise ApiError(400, 'That code is not right. Check the time on your phone and try again.')
        codes = [secrets.token_hex(5).upper() for _ in range(10)]
        conn.execute('UPDATE staff SET totp_secret=?, totp_pending=NULL, totp_enabled=1, totp_last=?, recovery=? WHERE id=?',
                     (r['totp_pending'], ctr, json.dumps([norm_recovery(c) for c in codes]), u['id']))
        seclog(conn, u['username'], '2fa_enabled', h.ip())
        return {'recovery_codes': [c[:5] + '-' + c[5:] for c in codes]}
    finally:
        conn.close()


def api_2fa_disable(h, q, b):
    u = h.session()
    b = b or {}
    conn = db()
    try:
        r = conn.execute('SELECT * FROM staff WHERE id=?', (u['id'],)).fetchone()
        if not check_pw(str(b.get('password') or ''), r['salt'], r['pw']):
            raise ApiError(401, 'The password is wrong')
        if not r['totp_enabled']:
            raise ApiError(409, 'Two-step login is not on')
        code = str(b.get('code') or '')
        rec = json.loads(r['recovery'] or '[]')
        if totp_verify(r['totp_secret'], code, r['totp_last']) is None and norm_recovery(code) not in rec:
            raise ApiError(400, 'That code is not right')
        conn.execute('UPDATE staff SET totp_enabled=0, totp_secret=NULL, totp_pending=NULL, recovery=NULL, totp_last=0 WHERE id=?', (u['id'],))
        seclog(conn, u['username'], '2fa_disabled', h.ip())
        return {'ok': True}
    finally:
        conn.close()


def api_sessions_revoke(h, q, b):
    u = h.session()
    b = b or {}
    conn = db()
    try:
        if b.get('others'):
            n = conn.execute('DELETE FROM sessions WHERE staff_id=? AND th<>?', (u['id'], u['th'])).rowcount
        else:
            sid = str(b.get('id') or '')
            if not re.fullmatch(r'[0-9a-f]{12}', sid):
                bad('Invalid session', 400)
            n = conn.execute('DELETE FROM sessions WHERE staff_id=? AND th<>? AND substr(th,1,12)=?', (u['id'], u['th'], sid)).rowcount
        seclog(conn, u['username'], 'sessions_revoked', h.ip(), f'{n} session(s)')
        return {'ok': True, 'revoked': n}
    finally:
        conn.close()


def api_security_log(h, q, b):
    u = h.session()
    need_role(u, 'Owner')
    lim = min(max(int(q.get('limit', 200) or 200), 1), 500) if str(q.get('limit', '200')).isdigit() else 200
    sql, args = 'SELECT at,user,event,ip,detail FROM security_log', []
    cond = []
    if q.get('user'):
        cond.append('user=?')
        args.append(q['user'].lower())
    if q.get('event'):
        cond.append('event=?')
        args.append(q['event'])
    if cond:
        sql += ' WHERE ' + ' AND '.join(cond)
    conn = db()
    try:
        return {'events': [dict(e) for e in conn.execute(sql + ' ORDER BY id DESC LIMIT ' + str(lim), args)]}
    finally:
        conn.close()


def cli_admin(args):
    """Offline recovery commands: run on the server while the web server is stopped or running."""
    if not os.path.exists(DB_PATH):
        sys.exit(f'No database found at {DB_PATH}')
    conn = db()
    migrate(conn)
    user = (args.reset_password or args.disable_2fa or args.unlock).lower()
    r = conn.execute('SELECT * FROM staff WHERE username=?', (user,)).fetchone()
    if not r:
        sys.exit(f'No staff account named {user}')
    if args.reset_password:
        pw = secrets.token_urlsafe(10)
        salt, hh = hash_pw(pw)
        conn.execute('UPDATE staff SET salt=?, pw=?, must_change=1, failed=0, locked_until=0, active=1 WHERE id=?', (salt, hh, r['id']))
        conn.execute('DELETE FROM sessions WHERE staff_id=?', (r['id'],))
        seclog(conn, user, 'cli_password_reset', 'server console')
        print(f'New temporary password for {user}: {pw}\nIt must be changed at the next login.')
    elif args.disable_2fa:
        conn.execute('UPDATE staff SET totp_enabled=0, totp_secret=NULL, totp_pending=NULL, recovery=NULL, totp_last=0 WHERE id=?', (r['id'],))
        conn.execute('DELETE FROM sessions WHERE staff_id=?', (r['id'],))
        seclog(conn, user, 'cli_2fa_reset', 'server console')
        print(f'Two-step login turned off for {user}.')
    else:
        conn.execute('UPDATE staff SET failed=0, locked_until=0 WHERE id=?', (r['id'],))
        seclog(conn, user, 'cli_unlock', 'server console')
        print(f'{user} unlocked.')
    conn.close()


def cli_list_staff():
    """Print every staff account (no secrets): useful when someone is locked out or to review who can sign in."""
    if not os.path.exists(DB_PATH):
        sys.exit(f'No database found at {DB_PATH}')
    conn = db()
    migrate(conn)
    rows = conn.execute('SELECT * FROM staff ORDER BY id').fetchall()
    print(f"{'username':<16}{'role':<19}{'active':<8}{'2-step':<8}{'locked':<8}{'pw age':<8}last sign-in")
    now = time.time()
    for r in rows:
        print(f"{r['username']:<16}{r['role']:<19}{'yes' if r['active'] else 'no':<8}{'yes' if r['totp_enabled'] else 'no':<8}{'yes' if r['locked_until'] > now else 'no':<8}{str(pw_age_days(r)) + 'd':<8}{r['last_login'] or 'never'}")
    conn.close()


def make_backup(kind):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    name = f"{kind}-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.db"
    path = os.path.join(BACKUP_DIR, name)
    src = db()
    dst = sqlite3.connect(path)
    try:
        src.backup(dst)
        check = dst.execute('PRAGMA integrity_check').fetchone()[0]
    finally:
        dst.close()
        src.close()
    if check != 'ok':
        os.remove(path)
        raise RuntimeError('Backup failed the integrity check: ' + str(check))
    os.chmod(path, 0o600)
    keep = {'auto': 14, 'manual': 30}[kind]
    files = sorted(f for f in os.listdir(BACKUP_DIR) if f.startswith(kind + '-') and f.endswith('.db'))
    for f in files[:-keep]:
        os.remove(os.path.join(BACKUP_DIR, f))
    LOG.info('Backup created: %s', name)
    return name


def list_backups():
    out = []
    if os.path.isdir(BACKUP_DIR):
        for f in sorted(os.listdir(BACKUP_DIR), reverse=True):
            if re.fullmatch(r'(auto|manual)-\d{8}-\d{6}\.db', f):
                st = os.stat(os.path.join(BACKUP_DIR, f))
                out.append({'name': f, 'size': st.st_size, 'at': datetime.fromtimestamp(st.st_mtime, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'kind': f.split('-')[0]})
    return out


def backup_loop():
    time.sleep(3)
    while True:
        try:
            recent = [b for b in list_backups() if b['kind'] == 'auto']
            if not recent or time.time() - os.stat(os.path.join(BACKUP_DIR, recent[0]['name'])).st_mtime > 23 * 3600:
                make_backup('auto')
            purge_prescriptions()
        except Exception:
            LOG.exception('Automatic backup failed')
        time.sleep(3600)


def api_backups(h, q, b):
    u = h.session()
    need_role(u, 'Owner')
    return {'backups': list_backups()}


def api_backup_run(h, q, b):
    u = h.session()
    need_role(u, 'Owner')
    name = make_backup('manual')
    conn = db()
    try:
        seclog(conn, u['username'], 'backup_created', h.ip(), name)
    finally:
        conn.close()
    return {'ok': True, 'name': name}


def api_health(h, q, b):
    conn = db()
    try:
        ok = conn.execute('SELECT 1').fetchone()[0] == 1
    finally:
        conn.close()
    last = next((x['at'] for x in list_backups()), None)
    return {'ok': ok, 'last_backup': last, 'version': VERSION}


ROUTES = {
    ('GET', '/api/ping'): api_ping, ('GET', '/api/me'): api_me, ('GET', '/api/catalog'): api_catalog,
    ('POST', '/api/coupon'): api_coupon, ('POST', '/api/orders'): api_order_create,
    ('POST', '/api/orders/lookup'): api_order_lookup, ('POST', '/api/orders/lookup-many'): api_order_lookup_many,
    ('POST', '/api/orders/cancel'): api_order_cancel, ('POST', '/api/orders/return'): api_order_return,
    ('GET', '/api/setup'): api_setup_status, ('POST', '/api/setup'): api_setup,
    ('POST', '/api/contact'): api_contact, ('POST', '/api/login'): api_login, ('POST', '/api/logout'): api_logout,
    ('POST', '/api/password'): api_password, ('GET', '/api/state'): api_state_get, ('POST', '/api/state'): api_state_post,
    ('GET', '/api/account'): api_account, ('POST', '/api/account/2fa/start'): api_2fa_start, ('POST', '/api/account/2fa/enable'): api_2fa_enable,
    ('POST', '/api/account/2fa/disable'): api_2fa_disable, ('POST', '/api/account/sessions/revoke'): api_sessions_revoke, ('GET', '/api/security-log'): api_security_log,
    ('GET', '/api/privacy/export'): api_privacy_export, ('POST', '/api/privacy/erase'): api_privacy_erase, ('POST', '/api/waitlist'): api_waitlist, ('GET', '/api/backups'): api_backups, ('POST', '/api/backups/run'): api_backup_run, ('GET', '/api/health'): api_health,
    ('GET', '/api/staff'): api_staff_list, ('POST', '/api/staff'): api_staff_create, ('POST', '/api/restore'): api_restore,
}


def main():
    global ARGS, DB_PATH, RATE_SCALE, BACKUP_DIR, RX_DIR
    ap = argparse.ArgumentParser(description='Shagar Medical Store server')
    ap.add_argument('--host', default=os.environ.get('SHAGAR_HOST', '127.0.0.1'))
    ap.add_argument('--port', type=int, default=int(os.environ.get('SHAGAR_PORT', '8000')))
    ap.add_argument('--data', default=os.environ.get('SHAGAR_DATA', os.path.join(HERE, 'data')))
    ap.add_argument('--no-demo', action='store_true', help='start with an empty shop instead of demo products')
    ap.add_argument('--owner-password', default=os.environ.get('SHAGAR_OWNER_PASSWORD'))
    ap.add_argument('--secure-cookies', action='store_true', help='mark the session cookie Secure (use behind HTTPS)')
    ap.add_argument('--trust-proxy', action='store_true', help='use X-Forwarded-For for rate limiting (behind a reverse proxy)')
    ap.add_argument('--reset-password', metavar='USER', help='set a new temporary password for a staff account, then exit')
    ap.add_argument('--disable-2fa', metavar='USER', help='turn two-step login off for a staff account (lost phone), then exit')
    ap.add_argument('--unlock', metavar='USER', help='unlock a locked staff account, then exit')
    ap.add_argument('--random-owner-password', action='store_true', help='first run without the browser setup page: create the Owner with a random password shown once in this window')
    ap.add_argument('--list-staff', action='store_true', help='list staff accounts (no passwords), then exit')
    ap.add_argument('--rate-scale', type=float, default=1.0, help=argparse.SUPPRESS)
    ap.add_argument('--purge-prescriptions', action='store_true', help='delete prescription images past the retention period, then exit')
    ap.add_argument('--rx-days', type=int, default=None, help=argparse.SUPPRESS)
    ap.add_argument('--version', action='version', version='Shagar Medical Store server ' + VERSION)
    ap.add_argument('--no-auto-backup', action='store_true', help='turn off the daily automatic database backup')
    ap.add_argument('--verbose', action='store_true')
    ARGS = ap.parse_args()
    DB_PATH = os.path.join(ARGS.data, 'shop.db')
    RATE_SCALE = ARGS.rate_scale
    BACKUP_DIR = os.path.join(ARGS.data, 'backups')
    RX_DIR = os.path.join(ARGS.data, 'prescriptions')
    os.makedirs(RX_DIR, mode=0o700, exist_ok=True)
    os.makedirs(ARGS.data, exist_ok=True)
    fh = logging.handlers.RotatingFileHandler(os.path.join(ARGS.data, 'server.log'), maxBytes=1_000_000, backupCount=5, encoding='utf-8')
    fh.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    LOG.addHandler(fh)
    LOG.setLevel(logging.INFO)
    if ARGS.purge_prescriptions:
        init_db(not ARGS.no_demo, ARGS.owner_password)
        print(f'{purge_prescriptions(ARGS.rx_days)} prescription image(s) deleted.')
        return
    if ARGS.list_staff:
        cli_list_staff()
        return
    if ARGS.reset_password or ARGS.disable_2fa or ARGS.unlock:
        cli_admin(ARGS)
        return
    if ARGS.owner_password:
        check_new_password(ARGS.owner_password, 'owner')
    global RANDOM_OWNER
    RANDOM_OWNER = ARGS.random_owner_password
    pw = init_db(not ARGS.no_demo, ARGS.owner_password)
    if needs_setup():
        SETUP['code'] = secrets.token_urlsafe(6)
    if not ARGS.no_auto_backup:
        threading.Thread(target=backup_loop, daemon=True).start()
    srv = http.server.ThreadingHTTPServer((ARGS.host, ARGS.port), H)
    LOG.info('Server started on %s:%s', ARGS.host, ARGS.port)
    srv.daemon_threads = True
    print(f'Shagar Medical Store server {VERSION}: http://{ARGS.host}:{ARGS.port}/   (database: {DB_PATH})')
    if SETUP['code']:
        print('FIRST RUN: open http://' + (ARGS.host if ARGS.host not in ('0.0.0.0', '') else 'localhost') + ':' + str(ARGS.port) + '/admin/login.html to create the Owner account.')
        print('Setup code (type it on that page; it works once and is not stored): ' + SETUP['code'])
    if pw:
        print('First run: staff login  username: owner   password: ' + pw)
        if ARGS.owner_password is None:
            print('You will be asked to change this password at first login. It is shown only once.')
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print('\nStopped.')


if __name__ == '__main__':
    main()
