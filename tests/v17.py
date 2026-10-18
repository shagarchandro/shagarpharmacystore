# Real-browser tests: Shop, Wishlist, Orders, Help, Contact, footer. Serve on port 8765 first.
from playwright.sync_api import sync_playwright
B='http://localhost:8765/';res=[]
def ok(c,m): res.append(('PASS ' if c else 'FAIL ')+m)
with sync_playwright() as p:
    b=p.chromium.launch(); ctx=b.new_context(viewport={'width':1280,'height':900}); pg=ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)[:120])); pg.on('dialog',lambda d:d.accept('Wrong size'))
    pg.goto(B+'index.html'); pg.wait_for_selector('#all article.card')
    ok('Showing 1–8 of 12 medicines' in pg.inner_text('#app'),'shop shows a result summary')
    pg.select_option('label:has-text("Brand") select','Square'); pg.wait_for_timeout(150); t=pg.inner_text('#app')
    ok('of 5 medicines' in t and pg.locator('button.chip:has-text("Brand: Square")').count()==1,'brand filter shows count and a removable chip')
    pg.click('button.chip:text-is("Clear all")'); pg.wait_for_timeout(150); ok('of 12 medicines' in pg.inner_text('#app'),'Clear all resets filters')
    pg.select_option('label:has-text("Sort") select','disc'); pg.fill('#app input[type=search]','zzzz'); pg.wait_for_timeout(200); ok('No medicines match' in pg.inner_text('#all'),'empty state when nothing matches')
    pg.click('#all button:text-is("Clear filters")'); pg.wait_for_timeout(150); ok('of 12 medicines' in pg.inner_text('#app'),'empty state offers Clear filters')
    pg.evaluate("(()=>{const d=JSON.parse(localStorage.mc_db);d.batches.filter(b=>b.pid==='P8').forEach(b=>b.qty=0);localStorage.mc_db=JSON.stringify(d)})()"); pg.reload(); pg.wait_for_selector('#all article.card')
    pg.check('label.check input'); pg.wait_for_timeout(150); t=pg.inner_text('#app'); ok('of 11 medicines' in t and 'Vitamin C' not in pg.inner_text('#all'),'In stock only hides out-of-stock products')
    pg.uncheck('label.check input')
    # wishlist
    hearts=pg.locator('#all article.card button[aria-label=Wishlist]'); hearts.nth(0).click(); pg.wait_for_timeout(100); pg.locator('#all article.card button[aria-label=Wishlist]').nth(1).click(); pg.wait_for_timeout(100)
    ok(pg.inner_text('header nav a[href="#/wishlist"]')=='Wishlist (2)','header shows wishlist count')
    pg.click('header nav a[href="#/wishlist"]'); pg.wait_for_selector('button:has-text("Add all in-stock")'); pg.click('button:has-text("Add all in-stock")'); pg.wait_for_timeout(150); ok(pg.inner_text('#cc')=='2','add all in-stock puts both items in the cart')
    pg.click('button:text-is("Clear wishlist")'); pg.wait_for_timeout(150); ok('Your wishlist is empty' in pg.inner_text('#app') and pg.locator('#app a.btn:has-text("Browse medicines")').count()==1,'clear wishlist shows an empty state with a link')
    # orders
    pg.goto(B+'checkout.html')
    for n,v in [('name','Shop Tester'),('phone','01712345678'),('addr','House 5, Road 3'),('thana','Dhanmondi'),('district','Dhaka')]: pg.fill(f'#app input[name={n}]',v)
    if pg.locator('#app input[name=doc]').count(): pg.fill('#app input[name=doc]','Dr A, BMDC 1234'); pg.check('#app input[name=ok]')
    pg.click('#app button[type=submit]'); pg.wait_for_url('**#/success/*'); pg.goto(B+'orders.html'); pg.wait_for_selector('#app article.card'); t=pg.inner_text('#app')
    ok('Total spent' in t and 'In progress' in t and 'Loyalty points' in t,'orders page shows summary cards and loyalty')
    ok(pg.locator('.timeline small').count()>=1,'timeline shows when the order reached each step')
    pg.click('#app summary:has-text("Order details")'); ok('Deliver to:' in pg.inner_text('#app details'),'order details expand with address, payment and totals')
    pg.select_option('select[aria-label="Order filter"]','delivered'); pg.wait_for_timeout(150); ok('No orders match this filter' in pg.inner_text('#app'),'status filter works')
    pg.select_option('select[aria-label="Order filter"]','all'); pg.wait_for_timeout(100); pg.click('button:text-is("Print invoice")'); pg.wait_for_selector('dialog[open]'); ok('INV-1001' in pg.inner_text('dialog[open]'),'customer can open a printable invoice'); pg.evaluate("document.querySelector('dialog').remove()")
    # help
    pg.goto(B+'faq.html'); pg.wait_for_selector('#sec-faq'); ok(pg.evaluate("document.getElementById('sec-faq').classList.contains('hl')"),'faq.html highlights the FAQ section')
    tot=pg.locator('#app details').count(); pg.fill('#app input[type=search]','prescription'); pg.wait_for_timeout(150); vis=pg.locator('#app details:visible').count(); ok(0<vis<tot,f'FAQ search narrows answers ({vis} of {tot})')
    pg.fill('#app input[type=search]','zzzz'); pg.wait_for_timeout(150); ok('No answers match' in pg.inner_text('#app'),'FAQ search shows a no-match message')
    # footer
    ok(pg.locator('.foot-grid > *').count()==4 and pg.locator('.foot a[href^="tel:"]').count()==1,'footer has four columns and a tel link')
    pg.click('.foot a:text-is("Returns and refunds")'); pg.wait_for_timeout(300); ok(pg.evaluate("document.getElementById('sec-returns').classList.contains('hl')") and '#/info' in pg.url,'footer help link opens Help at the right section')
    pg.evaluate("window.scrollTo(0,99999)"); pg.click('.foot button:text-is("Back to top")'); pg.wait_for_timeout(900); ok(pg.evaluate("window.scrollY")<5,'Back to top works')
    # contact
    pg.click('.foot a:text-is("Contact")'); pg.wait_for_selector('#app form'); pg.fill('#app input[name=n]','Z'); pg.fill('#app input[name=ph]','123'); pg.fill('#app textarea[name=m]','hi'); pg.click('#app button.btn:has-text("Send message")'); pg.wait_for_timeout(200)
    ok('valid Bangladesh mobile' in pg.inner_text('#ce-ph') and pg.get_attribute('#app input[name=ph]','aria-invalid')=='true','contact form shows inline errors')
    pg.fill('#app input[name=n]','Sara Akter'); pg.fill('#app input[name=ph]','01912345678'); pg.fill('#app input[name=o]','inv-1001'); pg.fill('#app textarea[name=m]','Do you stock ORS sachets?'); pg.click('#app button.btn:has-text("Send message")'); pg.wait_for_timeout(300)
    ok('CT-1001' in pg.inner_text('#app'),'valid message shows a reference number')
    r=pg.evaluate("(()=>{const d=JSON.parse(localStorage.mc_db);return [d.messages.length,d.messages[0].order,d.notes.some(n=>/CT-1001/.test(n.msg))]})()"); ok(r==[1,'INV-1001',True],f'message stored with order number and a staff notification {r}')
    b2=b.new_context(viewport={'width':360,'height':740}); m=b2.new_page(); m.goto(B+'index.html'); m.wait_for_selector('.foot-grid'); ok(len(m.evaluate("getComputedStyle(document.querySelector('.foot-grid')).gridTemplateColumns").split(' '))==1,'footer stacks to one column on phones')
    for name,url in [('shop','index.html'),('wishlist','wishlist.html'),('orders','orders.html'),('help','faq.html'),('contact','contact.html')]:
        m.goto(B+url); m.wait_for_selector('#app h1'); m.wait_for_timeout(250); m.screenshot(path=f'/tmp/m_{name}.png',full_page=True)
    pg.goto(B+'index.html'); pg.wait_for_selector('#all article.card'); pg.screenshot(path='/tmp/d_shop.png',full_page=False)
    ok(not errs,'no page errors '+str(errs)); b.close()
print('\n'.join(res))
