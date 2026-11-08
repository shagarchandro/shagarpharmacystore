# v3.1 admin upgrades against the REAL server (fresh DB, port 8800)
import json, urllib.request
from playwright.sync_api import sync_playwright
B='http://127.0.0.1:8800/';res=[]
def ok(c,m): res.append(('PASS ' if c else 'FAIL ')+m)
CUST={'name':'Api Tester','phone':'01712345678','addr':'House 5, Road 3','thana':'Dhanmondi','district':'Dhaka','division':'Dhaka','post':'1205'}
def post(p,b):
    r=urllib.request.Request(B+'api/'+p,data=json.dumps(b).encode(),headers={'X-Requested-With':'XMLHttpRequest','Content-Type':'application/json'},method='POST');return json.load(urllib.request.urlopen(r))
post('orders',{'items':[{'id':'P1','qty':1}],'customer':CUST,'area':'dhaka','pay':'Cash on delivery'})
with sync_playwright() as p:
    b=p.chromium.launch();errs=[];c=b.new_context(viewport={'width':1280,'height':900});c.add_init_script("localStorage.setItem('mc_poll','1500');window.__notes=[];window.Notification=class{static get permission(){return 'granted'}static requestPermission(){return Promise.resolve('granted')}constructor(t){window.__notes.push(t)}};")
    pg=c.new_page();pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(B+'admin/login.html');pg.wait_for_selector('#lu');pg.fill('#lu','owner');pg.fill('#lp','Sunrise-Tea-4471');pg.click('button.btn');pg.wait_for_url('**/admin/index.html');pg.wait_for_selector('details.navgrp')
    ok(pg.locator('details.navgrp').count()==5 and pg.locator('#side nav button[data-t]').count()>=25,'grouped sidebar with the server (%d screens)'%pg.locator('#side nav button[data-t]').count())
    pg.click('#side nav button[data-t=dash]');pg.wait_for_selector('.attn');ok('Orders waiting' in pg.inner_text('.attn'),'attention strip sees the waiting order: '+pg.inner_text('.attn').replace('\n',' ')[:80])
    ok(pg.title().startswith('('),'tab title shows a count: '+pg.title())
    pg.click('button.alrt');post('orders',{'items':[{'id':'P2','qty':1}],'customer':CUST,'area':'dhaka','pay':'Cash on delivery'})
    pg.wait_for_timeout(5000)
    ok(len(pg.evaluate("window.__notes"))>=1 and pg.title().startswith('(2)'),'a new order is noticed (title %s, notifications %s)'%(pg.title(),pg.evaluate("window.__notes")))
    pg.keyboard.press('g');pg.keyboard.press('o');pg.wait_for_selector('#app h1');ok('Orders' in pg.inner_text('#app h1'),'"g o" opens Orders')
    ok(not errs,'no page errors '+str(errs[:2]));b.close()
print('\n'.join(res));print('SUMMARY pass=%d fail=%d'%(sum(r.startswith('PASS') for r in res),sum(r.startswith('FAIL') for r in res)))
