# Real-browser role tests. Serve the project on port 8765 first.
from playwright.sync_api import sync_playwright
B='http://localhost:8765/';res=[]
def ok(c,m): res.append(('PASS ' if c else 'FAIL ')+m)
EXPECT={'Owner':21,'Pharmacist':7,'Cashier':3,'Inventory Manager':10,'Delivery Staff':2}
FORBID={'Pharmacist':'users','Cashier':'users','Inventory Manager':'settings','Delivery Staff':'reports'}
with sync_playwright() as p:
    b=p.chromium.launch(); c0=b.new_context(); pg=c0.new_page(); pg.goto(B+'index.html'); pg.evaluate("localStorage.setItem('mc_cart',JSON.stringify({P3:1}))"); pg.goto(B+'checkout.html')
    for n,v in [('name','Role Tester'),('phone','01712345678'),('addr','House 5, Road 3'),('thana','Dhanmondi'),('district','Dhaka')]: pg.fill(f'#app input[name={n}]',v)
    pg.click('#app button[type=submit]'); pg.wait_for_url('**#/success/*'); state=c0.storage_state()
    def role_page(role,url='admin/index.html',st=None):
        c=b.new_context(storage_state=st or state); c.add_init_script(f"sessionStorage.setItem('mc_role','{role}')"); pp=c.new_page(); pp.on('dialog',lambda d:d.accept()); pp.goto(B+url); pp.wait_for_selector('#app h1'); return c,pp
    for role,n in EXPECT.items():
        c,pp=role_page(role); cnt=pp.locator('#side nav button').count(); ok(cnt==n,f'{role} sees {cnt} tabs (expected {n})')
        if role in FORBID:
            pp.goto(B+f'admin/index.html#{FORBID[role]}'); pp.wait_for_selector('#app h1'); h=pp.inner_text('#app h1').lower(); ok(FORBID[role] not in h,f'{role} deep link to #{FORBID[role]} falls back to an allowed screen ({h})')
        c.close()
    c,pp=role_page('Cashier','admin/index.html#orders'); pp.wait_for_selector('#app tbody select'); sel=pp.locator('#app tbody select').first
    sel.select_option('Shipped'); pp.wait_for_timeout(250); ok(pp.evaluate("db().orders[0].status")=='Pending','Cashier cannot set Shipped')
    pp.locator('#app tbody select').first.select_option('Packed'); pp.wait_for_timeout(250); ok(pp.evaluate("db().orders[0].status")=='Packed','Cashier can set Packed'); st2=c.storage_state(); c.close()
    c,pp=role_page('Delivery Staff','admin/index.html#orders',st2); pp.wait_for_selector('#app tbody select'); pp.locator('#app tbody select').first.select_option('Cancelled'); pp.wait_for_timeout(250); ok(pp.evaluate("db().orders[0].status")=='Packed','Delivery Staff cannot cancel orders')
    pp.locator('#app tbody select').first.select_option('Shipped'); pp.wait_for_timeout(250); ok(pp.evaluate("db().orders[0].status")=='Shipped','Delivery Staff can set Shipped'); c.close()
    b.close()
print('\n'.join(res))
