# Design QA: every palette x light/dark, English and Bangla; axe contrast + font checks (demo mode, port 8765; needs axe in /tmp/axe)
import sys
from playwright.sync_api import sync_playwright
B='http://localhost:8765/';AXE=open('/tmp/axe/node_modules/axe-core/axe.min.js').read();bad={}
PAGES=['index.html#/','index.html#/product/P1','index.html#/cart','index.html#/checkout','index.html#/info','index.html#/contact','index.html#/health','index.html#/wishlist']
def run(pg,name):
    pg.evaluate(AXE);r=pg.evaluate("axe.run(document,{runOnly:['wcag2a','wcag2aa','wcag21aa']})")
    for v in r['violations']:
        bad.setdefault(v['id']+' ['+v['impact']+']',[]).append(name+': '+', '.join(str(n['target'][-1])[:40] for n in v['nodes'][:2]))
with sync_playwright() as p:
    br=p.chromium.launch()
    for pal in ('forest','teal','ocean','plum'):
        for dark in (False,True):
            ctx=br.new_context(viewport={'width':1100,'height':800},color_scheme='dark' if dark else 'light');pg=ctx.new_page()
            pg.add_init_script("localStorage.setItem('mc_palette','%s');localStorage.setItem('mc_cart',JSON.stringify({P1:1}));localStorage.setItem('mc_wish',JSON.stringify(['P1']))"%pal)
            for u in PAGES:
                pg.goto(B+u);pg.reload();pg.wait_for_timeout(350);run(pg,('%s%s %s'%(pal,' dark' if dark else '',u.split('#')[-1])))
            ctx.close()
    # Bangla: fonts really used, no missing glyph fallback
    ctx=br.new_context(viewport={'width':1100,'height':800});pg=ctx.new_page();pg.add_init_script("localStorage.setItem('mc_lang','bn')")
    pg.goto(B+'index.html');pg.wait_for_selector('#all');pg.wait_for_timeout(800)
    fam=pg.evaluate("getComputedStyle(document.querySelector('h1')).fontFamily");ok1=pg.evaluate("document.fonts.check('400 17px \"Hind Siliguri\"','ওষুধ ৳')")
    loaded=pg.evaluate("[...document.fonts].filter(f=>f.status==='loaded').map(f=>f.family.replace(/\"/g,'')+' '+f.weight)")
    print('Bangla heading font stack:',fam[:70]);print('Hind Siliguri can draw Bengali + taka:',ok1);print('fonts loaded on the Bangla home page:',sorted(set(loaded)))
    for u in PAGES[:4]:
        pg.goto(B+u);pg.reload();pg.wait_for_timeout(300);run(pg,'bn '+u.split('#')[-1])
    br.close()
for k,v in sorted(bad.items()):print(k,'\n    ',' | '.join(sorted(set(v))[:8]))
print('RULES WITH PROBLEMS:',len(bad))
