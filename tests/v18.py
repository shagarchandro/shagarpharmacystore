# Real-browser tests: color palettes. Serve on port 8765 first.
from playwright.sync_api import sync_playwright
B='http://localhost:8765/';res=[]
def ok(c,m): res.append(('PASS ' if c else 'FAIL ')+m)
V=lambda pg,n: pg.evaluate(f"getComputedStyle(document.documentElement).getPropertyValue('{n}').trim()")
with sync_playwright() as p:
    b=p.chromium.launch(); errs=[]
    c=b.new_context(viewport={'width':1280,'height':900},color_scheme='light'); pg=c.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)[:100])); pg.goto(B+'index.html'); pg.wait_for_selector('#all article.card')
    ok(pg.evaluate("document.documentElement.dataset.palette")=='forest' and V(pg,'--pri')=='#13694b','default palette is Forest & Gold')
    pg.click('button[aria-label="Change color palette"]'); pg.wait_for_timeout(200); ok(V(pg,'--pri')=='#0f766e','header button switches to the next palette (Teal & Amber)')
    pg.reload(); pg.wait_for_selector('#all article.card'); ok(V(pg,'--pri')=='#0f766e','chosen palette persists after reload')
    pg.select_option('.foot select[aria-label="Color palette"]','ocean'); pg.wait_for_timeout(250); ok(V(pg,'--pri')=='#0b62a8','footer picker applies Ocean & Coral')
    src=pg.evaluate("decodeURIComponent(document.querySelector('#all article.card img').src)"); ok('#e1eefa' in src and '#0b62a8' in src,'product placeholder images follow the palette')
    ok(pg.get_attribute('meta[name=theme-color]','content')=='#0b62a8','browser theme-color follows the palette')
    c.close()
    c=b.new_context(viewport={'width':1280,'height':900}); c.add_init_script("localStorage.setItem('mc_palette','nonsense');localStorage.setItem('mc_theme','dark')"); pg=c.new_page(); pg.goto(B+'index.html'); pg.wait_for_selector('#all article.card'); ok(pg.evaluate("document.documentElement.dataset.palette")=='forest' and V(pg,'--pri')=='#4fcf93','invalid saved palette falls back to Forest, dark set applies'); c.close()
    c=b.new_context(viewport={'width':1280,'height':900}); c.add_init_script("sessionStorage.setItem('mc_role','Owner');localStorage.setItem('mc_theme','light')"); pg=c.new_page(); pg.goto(B+'admin/settings.html'); pg.wait_for_selector('select[aria-label="Color palette"]'); pg.select_option('select[aria-label="Color palette"]','plum'); pg.wait_for_timeout(300)
    ok(V(pg,'--pri')=='#7a2e8e' and 'rgb(59, 22, 71)' in pg.evaluate("getComputedStyle(document.getElementById('side')).backgroundImage"),'admin Settings picker recolors the sidebar and UI (Plum & Sage)')
    ok(not errs,'no page errors '+str(errs)); c.close()
    shots=[('forest_light',{'w':1280,'h':900,'t':'light','pal':'forest','u':'index.html'}),('forest_dark_m',{'w':390,'h':844,'t':'dark','pal':'forest','u':'index.html'}),('ocean_admin',{'w':1280,'h':800,'t':'light','pal':'ocean','u':'admin/index.html#dash','role':1}),('plum_store',{'w':1280,'h':900,'t':'light','pal':'plum','u':'index.html'})]
    for n,o in shots:
        c=b.new_context(viewport={'width':o['w'],'height':o['h']}); c.add_init_script(f"localStorage.setItem('mc_theme','{o['t']}');localStorage.setItem('mc_palette','{o['pal']}');"+("sessionStorage.setItem('mc_role','Owner');" if o.get('role') else "")); q=c.new_page(); q.goto(B+o['u']); q.wait_for_timeout(500); q.screenshot(path=f'/tmp/pal_{n}.png'); c.close()
    b.close()
print('\n'.join(res))
