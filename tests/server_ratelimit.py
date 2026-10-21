# Rate limits with the default (unscaled) settings. Run against: python3 server/server.py --port 8801 --data /tmp/shagar_rl --owner-password 'Sunrise-Tea-4471'
import json, urllib.request, urllib.error
B = 'http://127.0.0.1:8801'; res = []
def ok(c, m): res.append(('PASS ' if c else 'FAIL ') + m)
def post(p, body):
    r = urllib.request.Request(B + p, data=json.dumps(body).encode(), headers={'X-Requested-With': 'XMLHttpRequest', 'Content-Type': 'application/json'}, method='POST')
    try: return urllib.request.urlopen(r).status
    except urllib.error.HTTPError as e: return e.code
codes = [post('/api/contact', {'n': 'Rate Tester', 'ph': '01712345678', 't': 'Other', 'm': 'Hello there %d' % i}) for i in range(7)]
ok(codes[:5] == [200] * 5 and codes[5] == 429, f'the contact form allows 5 messages then answers 429 {codes}')
codes = [post('/api/login', {'username': 'nobody', 'password': 'wrong-password-%d' % i}) for i in range(22)]
ok(codes[0] == 401 and codes[-1] == 429, 'repeated logins from one address are throttled (429)')
print('\n'.join(res)); print('SUMMARY pass=%d fail=%d' % (sum(r.startswith('PASS') for r in res), sum(r.startswith('FAIL') for r in res)))
