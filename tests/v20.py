# Real-browser tests: admin search, product filters/bulk price, sortable tables, ledger and recall, pick list, dashboard period, idle logout, permissions. Serve on port 8765 first.
from playwright.sync_api import sync_playwright
B='http://localhost:8765/';res=[]
def ok(c,m): res.append(('PASS ' if c else 'FAIL ')+m)
with sync_playwright() as p:
    b=p.chromium.launch(); errs=[]
    c=b.new_context(viewport={'width':1280,'height':900}); c.add_init_script("sessionStorage.setItem('mc_role','Owner')"); pg=c.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)[:120])); pg.on('dialog',lambda d:d.accept('x'))
    pg.goto(B+'index.html'); pg.evaluate("localStorage.setItem('mc_cart',JSON.stringify({P1:2}))"); pg.goto(B+'checkout.html')
    for n,v in [('name','Search Tester'),('phone','01712345678'),('addr','House 5, Road 3'),('thana','Dhanmondi'),('district','Dhaka')]: pg.fill(f'#app input[name={n}]',v)
    pg.click('#app button[type=submit]'); pg.wait_for_url('**#/success/*')
    pg.goto(B+'admin/pos.html'); pg.wait_for_selector('#pq'); pg.fill('#pq','890001000'); pg.press('#pq','Enter'); pg.wait_for_timeout(150); pg.fill('[aria-label="Cash received"]','100'); pg.click('button:text-is("Complete sale")'); pg.wait_for_selector('dialog[open]'); pg.evaluate("document.querySelector('dialog').remove()")
    # global search
    pg.goto(B+'admin/index.html'); pg.wait_for_selector('#gs'); pg.keyboard.press('Control+k'); ok(pg.evaluate("document.activeElement.id")=='gs','Ctrl+K focuses the admin search')
    pg.fill('#gs','Search Tes'); pg.wait_for_selector('.gitem'); ok('Order' in pg.inner_text('.gres'),'search finds orders by customer name'); pg.click('.gitem >> nth=0'); pg.wait_for_timeout(250)
    ok(pg.locator('#app tbody tr').count()==1 and 'INV-1001' in pg.inner_text('#app tbody'),'choosing an order opens Orders filtered to it')
    pg.fill('#gs','Napa'); pg.wait_for_selector('.gitem'); pg.click('.gitem:has-text("Product") >> nth=0'); pg.wait_for_timeout(250); ok(pg.input_value('input[aria-label="Search products"]')=='Napa 500mg' and pg.locator('#app tbody tr').count()==1,'choosing a product opens Products filtered to it')
    # product filters, bulk price, sorting
    pg.click('button:text-is("Clear filters")'); pg.wait_for_timeout(200); ok('Showing 12 of 12 products' in pg.inner_text('#app'),'clear filters shows every product')
    pg.fill('input[aria-label="Search products"]','sec'); pg.press('input[aria-label="Search products"]','Enter'); pg.wait_for_timeout(250); ok('Showing 1 of 12 products' in pg.inner_text('#app'),'product search narrows the list')
    pg.click('button:text-is("Clear filters")'); pg.wait_for_timeout(200); pg.select_option('select[aria-label="Filter category"]','Digestive'); pg.wait_for_timeout(250); ok('Showing 2 of 12 products' in pg.inner_text('#app'),'category filter works')
    pg.click('button:text-is("Clear filters")'); pg.wait_for_timeout(200); pg.click('summary:has-text("Bulk price change")'); pg.select_option('select[aria-label="Price change scope"]','cat:Digestive'); pg.fill('input[aria-label="Percent change"]','200'); pg.click('button:text-is("Apply price change")'); pg.wait_for_timeout(200); ok('Enter a change between' in pg.inner_text('#toasts'),'out-of-range price change is rejected')
    pg.fill('input[aria-label="Percent change"]','10'); pg.click('button:text-is("Apply price change")'); pg.wait_for_timeout(300)
    r=pg.evaluate("(()=>{const d=JSON.parse(localStorage.mc_db);return [d.products.find(p=>p.id==='P2').price,d.products.find(p=>p.id==='P5').price,d.products.find(p=>p.id==='P1').price,d.audit.at(-1).msg]})()"); ok(r[:3]==[77,108,12] and 'Bulk price change 10%' in r[3],f'bulk price change updates only the chosen category and is audited {r[:3]}')
    pg.click('th:has-text("Name")'); first=lambda: pg.inner_text('#app tbody tr >> nth=0 >> td >> nth=0'); a=first(); pg.click('th:has-text("Name")'); d=pg.inner_text('#app tbody tr >> nth=0 >> td >> nth=0'); ok(a=='Ace Plus' and d.startswith('Vitamin'),f'column headers sort ascending and descending ({a} / {d})')
    pg.evaluate("(()=>{const d=JSON.parse(localStorage.mc_db);for(let i=0;i<20;i++)d.products.push({...d.products[0],id:'PX'+i,name:'Extra '+i,sku:'SKX'+i,barcode:'89009'+i});localStorage.mc_db=JSON.stringify(d)})()"); pg.reload(); pg.click('#side nav button[data-t=products]'); pg.wait_for_selector('#app tbody tr')
    ok(pg.locator('#app tbody tr:visible').count()==25 and pg.locator('button.more:visible').count()==1,'long tables show 25 rows and a Show more button'); pg.click('button.more'); pg.wait_for_timeout(150); ok(pg.locator('#app tbody tr:visible').count()==32,'Show more reveals the rest')
    # ledger and recall
    pg.click('#side nav button[data-t=ledger]'); pg.wait_for_selector('button[role=tab]'); ok(pg.locator('#app tbody tr').count()>=2,'stock ledger lists movements')
    with pg.expect_download() as dl: pg.click('button:text-is("Export CSV")')
    ok(dl.value.suggested_filename=='stock-ledger.csv','ledger exports to CSV')
    pg.click('button[role=tab]:text-is("Audit trail")'); pg.wait_for_timeout(200); ok('Bulk price change' in pg.inner_text('#app'),'audit trail shows admin actions')
    pg.click('button[role=tab]:text-is("Batch recall")'); pg.fill('input[name=bq]','A0'); pg.click('button:text-is("Find batch")'); pg.wait_for_timeout(250); t=pg.inner_text('#app')
    ok('INV-1001' in t and 'Search Tester' in t and 'INV-POS-1' in t,'batch recall lists the online order and the POS sale that used the batch')
    pg.click('button:text-is("Print recall list")'); pg.wait_for_selector('dialog[open]'); ok('Recall list' in pg.inner_text('dialog[open]'),'recall list can be printed'); pg.evaluate("document.querySelector('dialog').remove()")
    # pick list
    pg.click('#side nav button[data-t=orders]'); pg.wait_for_selector('button:text-is("Pick list")'); pg.click('button:text-is("Pick list") >> nth=0'); pg.wait_for_selector('dialog[open]'); t=pg.inner_text('dialog[open]'); ok('Napa 500mg' in t and 'A0' in t,'pick list names the exact batch to pull'); pg.evaluate("document.querySelector('dialog').remove()")
    # dashboard, users, settings
    pg.click('#side nav button[data-t=dash]'); pg.wait_for_selector('select[aria-label="Dashboard period"]'); ok('Sales, last 7 days' in pg.inner_text('#app') and 'Average basket' in pg.inner_text('#app'),'dashboard shows period sales and average basket'); pg.select_option('select[aria-label="Dashboard period"]','30'); pg.wait_for_timeout(200); ok('Sales, last 30 days' in pg.inner_text('#app'),'dashboard period can be switched')
    pg.click('#side nav button[data-t=users]'); pg.wait_for_selector('text=Roles and permissions'); ok('Pending, Confirmed, Processing, Packed' in pg.inner_text('#app'),'users screen lists role permissions')
    pg.click('#side nav button[data-t=settings]'); pg.wait_for_selector('input[name=idleMin]'); ok(pg.input_value('input[name=idleMin]')=='30','settings has an auto-logout time (30 minutes by default)')
    pg.evaluate("D.settings.idleMin=0;IDLE_LAST=Date.now()-3600e3;idleCheck()"); pg.wait_for_timeout(400); ok('login.html' not in pg.url,'auto-logout off (0) keeps the session')
    pg.evaluate("D.settings.idleMin=30;IDLE_LAST=Date.now()-3600e3;idleCheck()"); pg.wait_for_url('**login.html'); ok('inactivity' in pg.inner_text('#lmsg'),'idle session is logged out with an explanation'); st=c.storage_state(); c.close()
    d=b.new_context(viewport={'width':1280,'height':900},storage_state=st); d.add_init_script("sessionStorage.setItem('mc_role','Delivery Staff')"); q=d.new_page(); q.goto(B+'admin/index.html'); q.wait_for_selector('#gs'); q.fill('#gs','Napa'); q.wait_for_timeout(250); ok('Product' not in q.inner_text('.gres'),'search only shows areas the role may open (Delivery Staff sees no products)')
    q.fill('#gs','INV-1001'); q.wait_for_selector('.gitem'); ok('Order' in q.inner_text('.gres'),'Delivery Staff can still find orders'); d.close()
    ok(not errs,'no page errors '+str(errs)); b.close()
print('\n'.join(res))
