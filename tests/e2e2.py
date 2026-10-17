# Real-browser tests for v10 features. Serve the project on port 8765 first.
from playwright.sync_api import sync_playwright
B='http://localhost:8765/';res=[]
def ok(c,m): res.append(('PASS ' if c else 'FAIL ')+m)
def dlg(d):
    m=d.message
    d.accept('LOT9' if 'Batch number' in m else '2027-12-31' if 'Expiry' in m else '5' if 'Quantity received' in m else 'Renamed Supplier' if 'Supplier name' in m else '01700000001' if m.startswith('Phone') else 'x')
with sync_playwright() as p:
    b=p.chromium.launch(); ctx=b.new_context(viewport={'width':1280,'height':900}); ctx.add_init_script("sessionStorage.setItem('mc_role','Owner')")
    pg=ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)[:100])); pg.on('dialog',dlg)
    pg.goto(B+'admin/purchases.html'); pg.wait_for_selector('form.row')
    pg.fill('input[name=qty]','12'); pg.fill('input[name=cost]','10'); pg.click('text=Create PO'); pg.wait_for_timeout(200)
    pg.click('button:text-is("Receive") >> nth=0'); pg.wait_for_timeout(200); ok('Partially received' in pg.inner_text('#app'),'partial receive keeps PO open')
    pg.click('button:text-is("Receive") >> nth=0'); pg.wait_for_timeout(200)
    r=pg.evaluate("(()=>{const d=JSON.parse(localStorage.mc_db);return [d.purchases[0].recv,d.batches.filter(b=>b.no==='LOT9').length,d.purchases[0].status]})()"); ok(r==[10,2,'Partially received'],f'two partial batches stored {r}')
    pg.goto(B+'admin/suppliers.html'); pg.wait_for_selector('tbody tr'); pg.click('text=Edit >> nth=0'); pg.wait_for_timeout(200); ok('Renamed Supplier' in pg.inner_text('#app'),'supplier edit')
    pg.click('text=Delete >> nth=0'); pg.wait_for_timeout(200); ok('cannot be deleted' in pg.inner_text('#toasts'),'supplier with history cannot be deleted')
    pg.goto(B+'admin/products.html'); pg.click('text=Add product (full form)'); pg.wait_for_selector('dialog[open] form')
    for n,v in [('name','Test Syrup'),('price','55'),('cost','40'),('disc','5'),('sku','SKU-T1'),('barcode','8900777')]: pg.fill(f'dialog input[name={n}]',v)
    pg.set_input_files('dialog input[name=img]','/tmp/px.png'); pg.click('dialog button.btn'); pg.wait_for_timeout(500)
    r=pg.evaluate("(()=>{const p=JSON.parse(localStorage.mc_db).products.find(x=>x.name==='Test Syrup');return p&&[p.price,p.disc,(p.img||'').slice(0,15)]})()"); ok(r==[55,5,'data:image/jpeg'],f'new product with image saved {r}')
    pg.goto(B+'admin/reports.html'); pg.fill('input[type=date] >> nth=0','2099-01-01'); pg.wait_for_timeout(300); ok('Nothing here yet.' in pg.inner_text('#app'),'report date range filters rows')
    pg.goto(B+'admin/orders.html')
    with pg.expect_download() as dl: pg.click('text=Export orders CSV')
    ok(dl.value.suggested_filename=='orders.csv','orders CSV downloads')
    s=ctx.new_page(); s.on('dialog',dlg); s.goto(B+'index.html'); s.wait_for_selector('#all article.card'); s.click('#all article.card >> nth=0 >> button.btn'); s.goto(B+'checkout.html')
    for n,v in [('name','Guest One'),('phone','01712345678'),('addr','House 5, Road 3'),('thana','Dhanmondi'),('district','Dhaka')]: s.fill(f'#app input[name={n}]',v)
    s.click('#app button[type=submit]'); s.wait_for_url('**#/success/*'); s.evaluate("localStorage.removeItem('mc_user')"); s.goto(B+'orders.html')
    s.fill('input[name=no]','INV-1001'); s.fill('input[name=ph]','01712345678'); s.click('button:text-is("Track")'); ok('Status' in s.inner_text('#app') and 'Pending' in s.inner_text('#app'),'guest can track order by number and phone')
    s.fill('input[name=ph]','01999999999'); s.click('button:text-is("Track")'); ok('No order found' in s.inner_text('#app'),'wrong phone does not reveal order')
    ok(not errs,'no page errors '+str(errs)); b.close()
print('\n'.join(res))
