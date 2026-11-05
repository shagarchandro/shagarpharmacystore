// extras.js (v1.3): storefront add-ons that sit on top of store.js without changing it.
// Product compare, recently viewed, share / WhatsApp question, health tools (BMI, water, reminders).
// Everything here is stored in this browser only (LocalStorage keys mc_cmp, mc_recent, mc_rem).
(()=>{
'use strict';
if(typeof views==='undefined'||typeof h!=='function')return;
const LS=(k,d)=>{try{const v=JSON.parse(localStorage.getItem(k));return v==null?d:v}catch(e){return d}};
const SVv=(k,v)=>{try{localStorage.setItem(k,JSON.stringify(v))}catch(e){}};
const bnx={Health:'স্বাস্থ্য','Health tools':'স্বাস্থ্য টুলস',Compare:'তুলনা','Compare products':'পণ্য তুলনা','Compare (':'তুলনা (','Clear':'মুছুন','Recently viewed':'সম্প্রতি দেখা','Share':'শেয়ার',
'Ask the pharmacist on WhatsApp':'হোয়াটসঅ্যাপে ফার্মাসিস্টকে জিজ্ঞাসা করুন','Height (cm)':'উচ্চতা (সেমি)','Weight (kg)':'ওজন (কেজি)','Calculate':'হিসাব করুন','BMI calculator':'বিএমআই ক্যালকুলেটর',
'Daily water guide':'দৈনিক পানির নির্দেশিকা','Medicine reminders':'ওষুধের রিমাইন্ডার','Add reminder':'রিমাইন্ডার যোগ করুন','Medicine name':'ওষুধের নাম','Time':'সময়','Taken':'খাওয়া হয়েছে',
'Remove':'মুছে ফেলুন','Open now':'এখন খোলা','Menu':'মেনু','Staff login':'স্টাফ লগইন','Voice search':'ভয়েস সার্চ','Text size':'লেখার আকার','Closed now':'এখন বন্ধ','Copy cart link':'কার্টের লিংক কপি করুন','Shared cart':'শেয়ার করা কার্ট','Add all to my cart':'সব কার্টে যোগ করুন','Allow notifications':'নোটিফিকেশন চালু করুন','Healthy habits':'স্বাস্থ্যকর অভ্যাস','Price per unit':'প্রতি ইউনিট দাম','Nothing to compare yet':'এখনো তুলনা করার কিছু নেই'};
if(typeof I18!=='undefined')Object.assign(I18.bn,bnx);
const tr=s=>typeof T==='function'?T(s):s;
const pidFromHash=()=>(location.hash.split('/')[2]||new URLSearchParams(location.search).get('id')||'').split('?')[0];

// ---------- recently viewed ----------
const recent=()=>LS('mc_recent',[]).filter(id=>db().products.some(p=>p.id===id));
const seen=id=>{const L=[id,...LS('mc_recent',[]).filter(x=>x!==id)].slice(0,8);SVv('mc_recent',L)};
const recentBox=excl=>{const L=recent().filter(id=>id!==excl).slice(0,4).map(id=>db().products.find(p=>p.id===id)).filter(Boolean);
 if(!L.length)return null;
 return h('section',{class:'recent','aria-label':tr('Recently viewed')},h('h2',{},tr('Recently viewed')),h('div',{class:'grid'},L.map(p=>card(p))),
  h('p',{},h('button',{class:'btn2',onclick(){SVv('mc_recent',[]);render()}},tr('Clear'))))};

// ---------- compare ----------
const cmp=()=>LS('mc_cmp',[]).filter(id=>db().products.some(p=>p.id===id)).slice(0,3);
let bar=null;
const drawBar=()=>{if(!bar){bar=h('div',{class:'cmpbar',role:'region','aria-label':tr('Compare products'),hidden:true});document.body.append(bar)}
 const L=cmp();bar.hidden=!L.length||location.hash==='#/compare'||window.ROUTE==='compare'&&!location.hash;
 bar.replaceChildren(h('b',{},tr('Compare')+' ('+L.length+'/3)'),h('a',{class:'btn',href:'#/compare'},tr('Compare products')),h('button',{class:'btn2',onclick(){SVv('mc_cmp',[]);syncBtns();drawBar()}},tr('Clear')))};
const syncBtns=()=>{const L=cmp();document.querySelectorAll('button[data-cmp]').forEach(b=>{const on=L.includes(b.dataset.cmp);b.classList.toggle('cmp-on',on);b.setAttribute('aria-pressed',on)})};
const cmpBtn=p=>h('button',{type:'button','data-cmp':p.id,'aria-pressed':cmp().includes(p.id),title:tr('Compare'),'aria-label':tr('Compare')+' '+p.name,onclick(){let L=cmp();
 if(L.includes(p.id))L=L.filter(x=>x!==p.id);else{if(L.length>=3)return toast('You can compare up to 3 products',1);L=[...L,p.id]}SVv('mc_cmp',L);syncBtns();drawBar()}},'⚖');
const card0=card;card=function(p){const a=card0.apply(this,arguments),row=a.querySelector('.row');if(row)row.append(cmpBtn(p));return a};
const units=p=>{const m=String(p.pack||'').match(/(\d+)/);return m?+m[1]:0};
views.compare=()=>{const L=cmp().map(id=>db().products.find(p=>p.id===id)).filter(Boolean);
 if(!L.length)return h('section',{},h('h1',{},tr('Compare products')),h('p',{class:'empty'},tr('Nothing to compare yet')),h('p',{},'Use the ⚖ button on any product card (up to 3).'),h('a',{class:'btn',href:'#/'},tr('Shop')));
 const per=p=>units(p)?eff(p)/units(p):null,pv=L.map(per).filter(x=>x!=null),best=pv.length>1?Math.min(...pv):null,lo=Math.min(...L.map(eff));
 const rows=[['Generic',p=>p.generic],['Strength',p=>p.strength||'—'],['Form',p=>p.form],['Pack size',p=>p.pack],['Manufacturer',p=>p.maker],['Prescription',p=>p.rx?'Required':'Not required'],
  ['Price',p=>h('span',{class:eff(p)===lo&&L.length>1?'cmp-best':''},money(eff(p))+(p.disc>0?' (-'+p.disc+'%)':''))],
  [tr('Price per unit'),p=>{const v=per(p);return v==null?'—':h('span',{class:v===best?'cmp-best':''},'৳'+v.toFixed(2))}],
  ['Availability',p=>{const s=stock(db(),p.id);return s?'In stock ('+s+')':'Out of stock'}]];
 const same=new Set(L.map(p=>(p.generic||'').toLowerCase())).size===1&&L.length>1;
 return h('section',{},h('a',{href:'#/'},'← '+tr('Shop')),h('h1',{},tr('Compare products')),
  same&&h('p',{class:'hres',role:'note'},'These products share the same active ingredient. Ask the pharmacist before switching; this is information, not a recommendation.'),
  h('div',{class:'scroll'},h('table',{class:'cmp-table'},h('thead',{},h('tr',{},h('th',{scope:'col'},''),...L.map(p=>h('th',{scope:'col'},h('a',{href:'#/product/'+p.id},PN(p)))))),
   h('tbody',{},...rows.map(([k,f])=>h('tr',{},h('th',{scope:'row'},tr(k)),...L.map(p=>h('td',{},f(p))))),
    h('tr',{},h('th',{scope:'row'},''),...L.map(p=>{const s=stock(db(),p.id);return h('td',{},h('div',{class:'row'},h('button',{class:'btn',disabled:!s,onclick(){const c=cart();if((c[p.id]||0)+1>s)return toast('Only '+s+' available',1);c[p.id]=(c[p.id]||0)+1;setCart(c);toast('Added to cart')}},tr('Add to cart')),
     h('button',{class:'btn2',onclick(){SVv('mc_cmp',cmp().filter(x=>x!==p.id));render()}},tr('Remove'))))}))))));};

// ---------- wrap catalog and product views ----------
const cat0=views.catalog;views.catalog=function(){const r=cat0.apply(this,arguments);const home=!S.q&&!S.cat&&!S.brand&&!S.rx;const b=home?recentBox():null;if(b)r.append(b);return r};
const waNum=()=>{const d=String(db().settings.phone||'').replace(/\D/g,'');return d?(d.startsWith('88')?d:d.startsWith('0')?'88'+d:d):''};
const prod0=views.product;views.product=function(){const r=prod0.apply(this,arguments),id=pidFromHash(),p=db().products.find(x=>x.id===id);if(!p)return r;
 seen(id);const num=waNum(),txt=encodeURIComponent('Hello, I would like to ask about '+p.name+' ('+p.generic+').');
 const ex=h('div',{class:'row',role:'group','aria-label':'More actions'},cmpBtn(p),
  h('button',{type:'button',class:'btn2',onclick:async()=>{const u=location.href.split('#')[0]+'#/product/'+p.id;
   try{if(navigator.share){await navigator.share({title:p.name,url:u})}else{await navigator.clipboard.writeText(u);toast('Link copied')}}catch(e){if(e&&e.name!=='AbortError')toast('Could not share the link',1)}}},'↗ '+tr('Share')),
  num&&h('a',{class:'btn2',href:'https://wa.me/'+num+'?text='+txt,target:'_blank',rel:'noopener noreferrer'},'💬 '+tr('Ask the pharmacist on WhatsApp')));
 const c=r.querySelector('.card');if(c)c.after(ex);else r.append(ex);
 const rb=recentBox(id);if(rb)r.append(rb);return r};

// ---------- health tools ----------
const rems=()=>LS('mc_rem',[]);
const hhmm=d=>String(d.getHours()).padStart(2,'0')+':'+String(d.getMinutes()).padStart(2,'0');
const tick=()=>{const now=new Date(),k=hhmm(now),day=now.toISOString().slice(0,10);let L=rems(),ch=false;
 L.forEach(r=>{if(r.time===k&&r.fired!==day+k){r.fired=day+k;ch=true;const msg=r.name+(r.note?' – '+r.note:'');toast('⏰ Time for '+msg);
  try{if('Notification' in window&&Notification.permission==='granted')new Notification('Medicine reminder',{body:msg})}catch(e){}}});
 if(ch)SVv('mc_rem',L)};
setInterval(tick,20000);
views.health=()=>{
 const out=(id)=>h('p',{class:'hres',id,'aria-live':'polite',hidden:true});
 const bmiOut=out('bmi-out'),wOut=out('w-out'),list=h('ul',{class:'rem-list'});
 const draw=()=>{const L=rems().sort((a,b)=>a.time.localeCompare(b.time)),td=new Date().toISOString().slice(0,10);
  list.replaceChildren(...(L.length?L.map(r=>h('li',{},h('span',{},h('b',{},r.time),' · '+r.name+(r.note?' ('+r.note+')':'')+(r.taken===td?' ✓':'')),
   h('span',{class:'row'},h('button',{class:'btn2',type:'button',onclick(){const A=rems(),x=A.find(y=>y.id===r.id);if(x){x.taken=x.taken===td?'':td;SVv('mc_rem',A);draw()}}},tr('Taken')),
   h('button',{class:'btn2',type:'button','aria-label':tr('Remove')+' '+r.name,onclick(){SVv('mc_rem',rems().filter(y=>y.id!==r.id));draw()}},tr('Remove'))))):[h('li',{},'No reminders yet.')]))};
 draw();
 const bmi=h('form',{novalidate:true,onsubmit(e){e.preventDefault();const t=e.target.elements,hc=+t.h.value,w=+t.w.value;
  if(!(hc>=50&&hc<=250)||!(w>=2&&w<=400)){bmiOut.hidden=false;bmiOut.textContent='Enter a height between 50 and 250 cm and a weight between 2 and 400 kg.';wOut.hidden=true;return}
  const b=w/((hc/100)**2),cat=b<18.5?'Below the healthy range':b<23?'Within the healthy range':b<25?'Above the healthy range (overweight)':b<30?'Obese range (class I)':'Obese range (class II or higher)';
  bmiOut.hidden=false;bmiOut.textContent='BMI '+b.toFixed(1)+' – '+cat+'. Uses the Asian cut-offs common in South Asia. BMI is a rough screen, not a diagnosis.';
  wOut.hidden=false;wOut.textContent='A common rule of thumb is about '+Math.round(w*30)+'–'+Math.round(w*35)+' ml of fluids a day for a healthy adult (roughly '+(w*30/1000).toFixed(1)+'–'+(w*35/1000).toFixed(1)+' litres). You may need more in hot weather or with activity, and some medical conditions need less. Ask your doctor if unsure.'}},
  h('label',{},tr('Height (cm)'),h('input',{name:'h',type:'number',inputmode:'decimal',min:50,max:250,step:'any'})),
  h('label',{},tr('Weight (kg)'),h('input',{name:'w',type:'number',inputmode:'decimal',min:2,max:400,step:'any'})),
  h('button',{class:'btn'},tr('Calculate')),bmiOut);
 const form=h('form',{novalidate:true,onsubmit(e){e.preventDefault();const t=e.target.elements,name=t.n.value.trim().slice(0,60);
  if(name.length<2||!/^\d{2}:\d{2}$/.test(t.t.value))return toast('Enter the medicine name and a time',1);
  const L=rems();if(L.length>=20)return toast('You can keep up to 20 reminders',1);L.push({id:uid('R'),name,time:t.t.value,note:t.d.value.trim().slice(0,60)});SVv('mc_rem',L);e.target.reset();draw();toast('Reminder added')}},
  h('label',{},tr('Medicine name'),h('input',{name:'n',maxlength:60})),h('label',{},tr('Time'),h('input',{name:'t',type:'time'})),
  h('label',{},'Note (optional)',h('input',{name:'d',maxlength:60,placeholder:'e.g. after meals'})),h('button',{class:'btn'},tr('Add reminder')));
 const perm=('Notification' in window&&Notification.permission==='default')?h('button',{class:'btn2',type:'button',onclick(){Notification.requestPermission().then(()=>render())}},tr('Allow notifications')):null;
 return h('section',{},h('h1',{},tr('Health tools')),h('p',{class:'muted'},'General information only. It is not medical advice and does not replace your doctor or pharmacist.'),
  h('div',{class:'hgrid'},h('article',{class:'card'},h('h2',{},tr('BMI calculator')),bmi,h('h3',{},tr('Daily water guide')),wOut),
   h('article',{class:'card'},h('h2',{},tr('Medicine reminders')),h('p',{class:'muted'},'Reminders work only while this site is open in your browser, and are saved on this device only. They are not a substitute for your prescription instructions.'),form,perm,list)),
  h('article',{class:'card'},h('h2',{},tr('Healthy habits')),h('ul',{},
   ['Take medicines exactly as prescribed, and finish the full course of an antibiotic unless your doctor says otherwise.','Check the expiry date before use and store medicines in a cool, dry place away from children.','Do not share prescription medicines or take leftovers from an earlier illness.','Tell your pharmacist about every medicine, vitamin and herbal product you take.','See a doctor quickly for high fever, trouble breathing, chest pain or a severe allergic reaction.'].map(x=>h('li',{},x)))))};

// ---------- open/closed badge (Dhaka time; hours from Settings openFrom/openTo, default 9-22) ----------
const hrsNow=()=>{const f=new Intl.DateTimeFormat('en-GB',{timeZone:'Asia/Dhaka',hour:'2-digit',minute:'2-digit',hour12:false}).formatToParts(new Date());return(+f.find(x=>x.type==='hour').value%24)+(+f.find(x=>x.type==='minute').value)/60};
const badge=h('span',{class:'openb',role:'status'});
const drawBadge=()=>{const a=+db().settings.openFrom,b=+db().settings.openTo,fri=new Intl.DateTimeFormat('en-GB',{timeZone:'Asia/Dhaka',weekday:'short'}).format(new Date())==='Fri',from=isNaN(a)||db().settings.openFrom==null?(fri?15:9):a,to=isNaN(b)||db().settings.openTo==null?22:b,n=hrsNow(),open=n>=from&&n<to;
 badge.textContent=(open?'● ':'○ ')+tr(open?'Open now':'Closed now');badge.classList.toggle('on',open);badge.title='Hours '+from+':00–'+to+':00 (Dhaka time)'};
{const tl=document.querySelector('header .tools');if(tl)tl.prepend(badge);drawBadge();setInterval(drawBadge,60000)}

// ---------- share a cart by link ----------
const enc=c=>Object.entries(c).filter(([id,q])=>q>0).map(([id,q])=>id+'.'+q).join('~');
const dec=t=>(t||'').split('~').map(x=>x.split('.')).filter(a=>a.length===2&&/^[A-Za-z0-9_-]+$/.test(a[0])&&/^\d{1,3}$/.test(a[1])).map(([id,q])=>({id,q:+q})).filter(x=>x.q>0).slice(0,40);
const cart0=views.cart;views.cart=function(){const r=cart0.apply(this,arguments),c=cart();
 if(Object.keys(c).length){r.append(h('p',{},h('button',{class:'btn2',type:'button',onclick:async()=>{const u=location.href.split('#')[0]+'#/sharecart/'+enc(c);
  try{await navigator.clipboard.writeText(u);toast('Link copied')}catch(e){toast('Could not copy the link',1)}}},'🔗 '+tr('Copy cart link'))))}return r};
views.sharecart=()=>{const L=dec(location.hash.split('/')[2]).map(x=>({p:db().products.find(p=>p.id===x.id),q:x.q})).filter(x=>x.p);
 if(!L.length)return h('section',{},h('h1',{},tr('Shared cart')),h('p',{class:'empty'},'This cart link is empty or no longer valid.'),h('a',{class:'btn',href:'#/'},tr('Shop')));
 return h('section',{},h('h1',{},tr('Shared cart')),h('p',{class:'muted'},'Quantities are limited to what is in stock. Prescription items are still reviewed by a pharmacist at checkout.'),
  h('ul',{},L.map(({p,q})=>h('li',{},PN(p)+' × '+q+' — '+money(eff(p)*q)+(stock(db(),p.id)<q?' (only '+stock(db(),p.id)+' in stock)':'')))),
  h('button',{class:'btn',onclick(){const c=cart();let n=0;L.forEach(({p,q})=>{const st=stock(db(),p.id),add=Math.min(q,Math.max(0,st-(c[p.id]||0)));if(add>0){c[p.id]=(c[p.id]||0)+add;n++}});setCart(c);toast(n?'Added to cart':'Nothing could be added',!n);if(n)location.hash='#/cart'}},tr('Add all to my cart')))};

// ---------- voice search (only where the browser supports it) and text size ----------
const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
const cat1=views.catalog;views.catalog=function(){const r=cat1.apply(this,arguments);
 if(SR){const i=r.querySelector('.filters input[type=search]');if(i&&!r.querySelector('.mic')){let on=false;
  const b=h('button',{type:'button',class:'mic btn2','aria-label':tr('Voice search'),title:tr('Voice search'),onclick(){if(on)return;
   try{const rec=new SR();rec.lang=(typeof lang==='function'&&lang()==='bn')?'bn-BD':'en-US';rec.interimResults=false;rec.maxAlternatives=1;on=true;b.textContent='🎙️…';
    rec.onresult=e=>{const t=(e.results[0]&&e.results[0][0]&&e.results[0][0].transcript||'').trim().slice(0,80);if(t){i.value=t;i.dispatchEvent(new Event('input',{bubbles:true}))}};
    rec.onerror=e=>{toast(e.error==='not-allowed'?'Microphone permission is blocked':'Could not hear that, please try again',1)};
    rec.onend=()=>{on=false;b.textContent='🎤'};rec.start()}catch(e){on=false;toast('Voice search is not available',1)}}},'🎤');
  i.after(b)}}return r};
const FS=[100,112,125,140],fsGet=()=>{const v=+localStorage.getItem('mc_fs');return FS.includes(v)?v:100};
const fsSet=v=>{document.documentElement.style.fontSize=v+'%';try{localStorage.setItem('mc_fs',String(v))}catch(e){}};fsSet(fsGet());
{const tl=document.querySelector('header .tools');if(tl){const bt=h('button',{type:'button',class:'fsbtn','aria-label':tr('Text size'),title:tr('Text size')+': '+fsGet()+'%',onclick(){const k=FS.indexOf(fsGet()),v=FS[(k+1)%FS.length];fsSet(v);bt.title=tr('Text size')+': '+v+'%';toast(tr('Text size')+': '+v+'%')}},'Aa');tl.prepend(bt)}}

// ---------- navbar: mobile menu, current-page highlight, shadow on scroll, "/" to search ----------
{const hd=document.querySelector('header.bar'),nv=hd&&hd.querySelector('nav');if(nv){
 nv.id='mainnav';const btn=h('button',{type:'button',class:'navtoggle','aria-expanded':'false','aria-controls':'mainnav','aria-label':tr('Menu'),onclick(){setNav(!hd.classList.contains('navopen'))}},'☰');
 const setNav=o=>{hd.classList.toggle('navopen',o);btn.setAttribute('aria-expanded',String(o))};hd.insertBefore(btn,nv);
 nv.addEventListener('click',e=>{if(e.target.closest('a'))setNav(false)});
 addEventListener('keydown',e=>{if(e.key==='Escape'&&hd.classList.contains('navopen')){setNav(false);btn.focus()}});
 addEventListener('hashchange',()=>setNav(false));
 const st=hd.querySelector('a[href="admin/login.html"]');if(st){st.classList.add('staff');st.setAttribute('aria-label',tr('Staff login'));st.title=tr('Staff login')}
 const mark=()=>{const r=(location.hash?location.hash.slice(2).split('/')[0]:window.ROUTE)||'catalog',alias={product:'catalog',compare:'catalog',sharecart:'catalog',success:'orders'},cur=alias[r]||r;
  nv.querySelectorAll('a').forEach(a=>{const k=(a.getAttribute('href')||'').slice(2).split('/')[0]||'catalog';if(k===cur)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current')});};
 const r1=render;render=function(){const x=r1.apply(this,arguments);mark();return x};mark();
 const sc=()=>hd.classList.toggle('scrolled',scrollY>6);addEventListener('scroll',sc,{passive:true});sc();
 addEventListener('keydown',e=>{if(e.key==='/'&&!e.ctrlKey&&!e.metaKey&&!e.altKey&&!/^(INPUT|TEXTAREA|SELECT)$/.test((e.target.tagName||''))&&!e.target.isContentEditable){const i=hd.querySelector('.hsearch input');if(i){e.preventDefault();i.focus();i.select()}}})}}

// ---------- header link, bar, first draw ----------
{const nav=document.querySelector('header nav');if(nav&&!nav.querySelector('a[href="#/health"]'))nav.append(h('a',{href:'#/health'},tr('Health')))}
addEventListener('hashchange',()=>{drawBar();syncBtns()});
const render0=render;render=function(){const r=render0.apply(this,arguments);drawBar();syncBtns();return r};
{const r0=(location.hash?location.hash.slice(2)||'catalog':(window.ROUTE||'catalog')).split('/')[0];if(r0!=='info')render();else{drawBar();syncBtns()}}
tick();
})();
