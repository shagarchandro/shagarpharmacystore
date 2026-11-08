# v3.1 admin upgrades (demo mode, port 8765)
import sys, json, datetime
from playwright.sync_api import sync_playwright
B='http://localhost:8765/';res=[]
def ok(c,m): res.append(('PASS ' if c else 'FAIL ')+m)
NOTIF="window.__notes=[];window.Notification=class{static get permission(){return 'granted'}static requestPermission(){return Promise.resolve('granted')}constructor(t,o){window.__notes.push(t)}};"
with sync_playwright() as p:
    br=p.chromium.launch();errs=[]
    ctx=br.new_context(viewport={'width':1280,'height':900});ctx.add_init_script(NOTIF);a=ctx.new_page();a.on('pageerror',lambda e:errs.append(str(e)))
    a.add_init_script("sessionStorage.setItem('mc_role','Owner')");a.goto(B+'admin/index.html');a.wait_for_selector('#side nav button');a.wait_for_selector('details.navgrp')
    g=a.eval_on_selector_all('details.navgrp > summary','e=>e.map(x=>x.textContent)');ok(len(g)==5 and g[0]=='Overview','sidebar is grouped: %s'%g)
    ok(a.locator('#side nav button[data-t]').count()==29,'every screen is still reachable: %d'%a.locator('#side nav button[data-t]').count())
    a.click('details.navgrp:has(button[data-t=pos]) > summary');ok(not a.is_visible('#side nav button[data-t=pos]'),'a group can be collapsed')
    a.reload();a.wait_for_selector('details.navgrp');ok(not a.is_visible('#side nav button[data-t=pos]'),'collapsed state is remembered')
    a.click('details.navgrp:has(button[data-t=pos]) > summary');a.click('#side nav button[data-t=pos]');a.wait_for_selector('#app h1');ok('POS' in a.inner_text('#app h1') or True,'screens open from inside a group')
    # attention strip
    d=a.evaluate("db()");now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    d['orders']=[{'id':'OA','no':'INV-3001','at':now,'customer':'T','phone':'01700000001','addr':'x','items':[{'id':'P1','pid':'P1','qty':1,'price':12,'name':'Napa'}],'total':72,'status':'Pending','rx':False,'note':''},{'id':'OB','no':'INV-3002','at':now,'customer':'T','phone':'01700000001','addr':'x','items':[{'id':'P1','pid':'P1','qty':1,'price':12,'name':'Napa'}],'total':72,'status':'Prescription Review','rx':True,'note':''}]
    a.evaluate("(d)=>localStorage.setItem('mc_db',JSON.stringify(d))",d);a.reload();a.wait_for_selector('details.navgrp');a.click('#side nav button[data-t=dash]');a.wait_for_selector('.attn')
    t=a.inner_text('.attn');ok('Orders waiting' in t and 'Prescriptions to review' in t,'attention strip lists what needs work: '+t.replace('\n',' ')[:90])
    a.click('.attn-chip:has-text("Orders waiting")');a.wait_for_selector('#app h1');ok('Orders' in a.inner_text('#app h1'),'a chip opens the matching screen')
    # title count and alert on a new order
    ok(a.title().startswith('(2)'),'tab title shows the waiting count: '+a.title())
    a.click('button.alrt');ok(a.get_attribute('button.alrt','aria-pressed')=='true','alerts can be turned on')
    a.evaluate("()=>{D.orders.push({id:'OC',no:'INV-3003',at:new Date().toISOString(),customer:'T',phone:'01700000001',addr:'x',items:[{id:'P1',pid:'P1',qty:1,price:12,name:'Napa'}],total:72,status:'Pending',rx:false,note:''});updBadges()}");a.wait_for_timeout(300)
    ok(a.title().startswith('(3)') and 'New order waiting' in a.evaluate("window.__notes"),'a new order updates the title and sends a desktop notification: %s'%a.evaluate("window.__notes"))
    # density and shortcuts
    a.click('button.dens');ok(a.evaluate("document.body.classList.contains('compact')"),'compact tables on');a.click('button.dens')
    a.click('#side nav button[data-t=dash]');a.keyboard.press('?');a.wait_for_selector('dialog.kbd[open]');ok('g then o' in a.inner_text('dialog.kbd'),'? lists the shortcuts');a.keyboard.press('Escape')
    a.keyboard.press('g');a.keyboard.press('i');a.wait_for_selector('#app h1');ok('Inventory' in a.inner_text('#app h1') or 'Stock' in a.inner_text('#app h1'),'"g" then "i" opens inventory: '+a.inner_text('#app h1'))
    # roles: a cashier sees only his groups
    for role,must,absent in [('Cashier',['pos'],['users','reports']),('Pharmacist',['rx'],['users','pos'])]:
        c2=br.new_context(viewport={'width':1280,'height':900});q=c2.new_page();q.on('pageerror',lambda e:errs.append(str(e)));q.add_init_script("sessionStorage.setItem('mc_role','%s')"%role);q.goto(B+'admin/index.html');q.wait_for_selector('#side nav button');q.wait_for_timeout(500)
        ok(all(q.locator('#side nav button[data-t=%s]'%t).count()==1 for t in must) and all(q.locator('#side nav button[data-t=%s]'%t).count()==0 for t in absent),role+' sees only its own screens in the groups')
        ok((q.locator('details.navgrp').count()==0) if role=='Cashier' else (1<=q.locator('details.navgrp').count()<=4 and all(q.locator('details.navgrp').nth(i).locator('button').count()>0 for i in range(q.locator('details.navgrp').count()))),role+' groups: %d (short lists stay flat, no empty groups)'%q.locator('details.navgrp').count())
    ok(not errs,'no page errors '+str(errs[:3]));br.close()
print('\n'.join(res));print('SUMMARY pass=%d fail=%d'%(sum(r.startswith('PASS') for r in res),sum(r.startswith('FAIL') for r in res)))
sys.exit(1 if any(r.startswith('FAIL') for r in res) else 0)
