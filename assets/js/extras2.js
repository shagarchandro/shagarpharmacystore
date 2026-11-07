// extras2.js (v2.0): updates to the Shop, Wishlist, Orders, Help, Contact and Health sections.
// Loaded after store.js and extras.js. It wraps the existing views and adds to them; nothing is removed.
// Everything stored here stays in this browser (mc_view, mc_wishp, mc_cdraft, mc_hlog, mc_water).
(()=>{
'use strict';
if(typeof views==='undefined'||typeof h!=='function'||typeof render!=='function')return;
const LS=(k,d)=>{try{const v=JSON.parse(localStorage.getItem(k));return v==null?d:v}catch(e){return d}};
const SVv=(k,v)=>{try{localStorage.setItem(k,JSON.stringify(v))}catch(e){}};
const tr=s=>typeof T==='function'?T(s):s;
const ldate=()=>new Date().toLocaleDateString('en-CA');
if(typeof I18!=='undefined')Object.assign(I18.bn,{Grid:'গ্রিড',List:'তালিকা',View:'দেখার ধরন','Quick view':'দ্রুত দেখুন','Did you mean':'আপনি কি বোঝাতে চেয়েছেন','Back to top':'উপরে যান','Share':'শেয়ার','Price dropped':'দাম কমেছে','Price changed':'দাম বদলেছে','Popular picks':'জনপ্রিয় পছন্দ','Share wishlist':'উইশলিস্ট শেয়ার করুন','Shared wishlist':'শেয়ার করা উইশলিস্ট','Save all to my wishlist':'সব আমার উইশলিস্টে রাখুন',
 'Need help with this order?':'এই অর্ডারে সাহায্য লাগবে?','Print receipt':'রসিদ প্রিন্ট','What do the statuses mean?':'স্ট্যাটাসের অর্থ কী?','All':'সব','Active':'চলমান','Delivered':'ডেলিভারি হয়েছে','Cancelled':'বাতিল','Using this website':'এই ওয়েবসাইট ব্যবহার','Medical emergency?':'জরুরি চিকিৎসা সমস্যা?','Print this page':'এই পেজ প্রিন্ট করুন',
 'Call us':'কল করুন','Copy phone':'ফোন কপি করুন','Show on map':'মানচিত্রে দেখুন','Message on WhatsApp':'হোয়াটসঅ্যাপে মেসেজ','Open now':'এখন খোলা','Closed now':'এখন বন্ধ','Health log':'স্বাস্থ্য লগ','Blood pressure':'রক্তচাপ','Blood sugar':'রক্তে শর্করা','Weight':'ওজন','Save reading':'রিডিং সংরক্ষণ','Water today':'আজকের পানি','Print my schedule':'আমার সূচি প্রিন্ট করুন','Emergency':'জরুরি','Export CSV':'CSV এক্সপোর্ট'});

// ---------------------------------------------------------------- Shop
const VK='mc_view',viewMode=()=>localStorage.getItem(VK)==='list'?'list':'grid';
const lev=(a,b)=>{const m=a.length,n=b.length;if(!m)return n;if(!n)return m;let p=Array.from({length:n+1},(_,i)=>i);for(let i=1;i<=m;i++){const c=[i];for(let j=1;j<=n;j++)c[j]=Math.min(p[j]+1,c[j-1]+1,p[j-1]+(a[i-1]===b[j-1]?0:1));p=c}return p[n]};
const waNum=()=>{const d=String((db().settings||{}).phone||'').replace(/\D/g,'');return d?(d.startsWith('88')?d:d.startsWith('0')?'88'+d:d):''};
const qv=p=>{const st=stock(db(),p.id);let q=1;const qty=h('output',{'aria-live':'polite'},'1');
 const close=()=>{w.close();w.remove()};
 const w=h('dialog',{class:'qv','aria-label':p.name},h('button',{type:'button',class:'qv-x','aria-label':tr('Close'),onclick:close},'✕'),
  h('img',{src:p.img||ph(p.name),alt:'',width:160}),h('h2',{},PN(p)),
  h('p',{class:'muted'},[p.generic,p.strength&&p.strength!=='—'?p.strength:'',p.form,p.pack].filter(Boolean).join(' · ')),h('p',{},p.maker),
  p.rx?h('p',{class:'warn'},tr('Prescription required')):null,
  h('p',{class:'price'},money(eff(p)),p.disc>0?h('s',{class:'muted'},' '+money(p.price)):null),
  h('p',{class:st?'ok':'bad'},st?'In stock ('+st+')':'Out of stock'),
  st?h('div',{class:'row'},h('button',{type:'button','aria-label':'Less',onclick(){q=Math.max(1,q-1);qty.textContent=q}},'−'),qty,h('button',{type:'button','aria-label':'More',onclick(){q=Math.min(st,q+1);qty.textContent=q}},'+'),
   h('button',{class:'btn',type:'button',onclick(){const c=cart();if((c[p.id]||0)+q>st)return toast('Only '+st+' available',1);c[p.id]=(c[p.id]||0)+q;setCart(c);toast('Added to cart');close()}},tr('Add to cart'))):null,
  h('p',{},h('a',{class:'btn2',href:'#/product/'+p.id,onclick:close},tr('Details'))));
 w.addEventListener('close',()=>w.remove());w.addEventListener('click',e=>{if(e.target===w)close()});document.body.append(w);w.showModal()};
const card1=card;card=function(p){const a=card1.apply(this,arguments),row=a.querySelector('.row');
 if(row)row.append(h('button',{type:'button',class:'qvbtn',title:tr('Quick view'),'aria-label':tr('Quick view')+': '+p.name,onclick:()=>qv(p)},'👁'));return a};
const cat2=views.catalog;views.catalog=function(){const r=cat2.apply(this,arguments);
 const f=r.querySelector('.filters');
 if(f){const tog=h('div',{class:'row viewtog',role:'group','aria-label':tr('View')});
  const mk=(m,l)=>h('button',{type:'button',class:viewMode()===m?'btn':'','aria-pressed':String(viewMode()===m),onclick(){localStorage.setItem(VK,m);const a=document.getElementById('all');if(a)a.classList.toggle('listview',m==='list');[...tog.children].forEach((b,i)=>{const on=(i===0?'grid':'list')===m;b.className=on?'btn':'';b.setAttribute('aria-pressed',String(on))})}},l);
  tog.append(mk('grid','▦ '+tr('Grid')),mk('list','☰ '+tr('List')));f.after(tog)}
 const all=r.querySelector('#all');if(all&&viewMode()==='list')all.classList.add('listview');
 const emp0=[...r.querySelectorAll('p')].find(p=>/^No medicines match/.test(p.textContent)),emp=emp0&&emp0.parentElement&&emp0.parentElement!==r?emp0.parentElement:emp0;
 if(emp&&S.q&&S.q.length>=2){const q=S.q.toLowerCase().trim(),lim=Math.max(2,Math.floor(q.length/3)),sc=p=>Math.min(...[p.name,p.generic,(p.bn||'')].filter(Boolean).flatMap(t=>{t=t.toLowerCase();return[lev(q,t),lev(q,t.split(/[\s,(]/)[0])]}));
  const sug=db().products.map(p=>({p,d:sc(p)})).filter(x=>x.d<=lim).sort((a,b)=>a.d-b.d).slice(0,4).map(x=>x.p),num=waNum();
  const box=h('div',{class:'card',role:'note'},sug.length?h('p',{},tr('Did you mean')+'?'):null,sug.length?h('div',{class:'row'},sug.map(p=>h('button',{type:'button',class:'btn2',onclick(){S.q=p.name;S.page=1;render()}},p.name))):null,
   num?h('p',{},h('a',{class:'btn2',href:'https://wa.me/'+num+'?text='+encodeURIComponent('Hello, do you have "'+S.q+'" in stock?'),target:'_blank',rel:'noopener noreferrer'},'💬 '+tr('Ask the pharmacist on WhatsApp'))):null);
  if(sug.length||num)emp.after(box)}
 return r};
{const b=h('button',{type:'button',class:'totop',hidden:true,'aria-label':tr('Back to top'),title:tr('Back to top'),onclick(){scrollTo({top:0,behavior:matchMedia('(prefers-reduced-motion:reduce)').matches?'auto':'smooth'})}},'↑');document.body.append(b);
 const t=()=>{b.hidden=scrollY<600};addEventListener('scroll',t,{passive:true});t()}

// ---------------------------------------------------------------- Wishlist
const wl0=views.wishlist;
views.wishlist=function(){const d=db(),w=wish(),L=d.products.filter(p=>w.includes(p.id)),wp=LS('mc_wishp',{});let ch=false;
 L.forEach(p=>{if(wp[p.id]==null){wp[p.id]=eff(p);ch=true}});Object.keys(wp).forEach(id=>{if(!w.includes(id)){delete wp[id];ch=true}});if(ch)SVv('mc_wishp',wp);
 const r=wl0.apply(this,arguments);
 [...r.querySelectorAll('.grid article.card')].forEach((c,i)=>{const p=L[i];if(!p)return;const was=wp[p.id],now=eff(p);
  if(was!=null&&now!==was)c.append(h('p',{class:now<was?'ok':'warn',role:'note'},(now<was?'⬇ '+tr('Price dropped'):'⬆ '+tr('Price changed'))+': ৳'+was+' → ৳'+now))});
 if(L.length){const inS=L.filter(p=>stock(d,p.id)>0),tot=inS.reduce((a,p)=>a+eff(p),0);
  const sum=h('div',{class:'row'},h('span',{class:'muted'},L.length+' saved · '+money(tot)+' for the '+inS.length+' in stock'),
   h('button',{type:'button',class:'btn2',onclick:async()=>{const u=location.href.split('#')[0]+'#/sharewish/'+L.map(p=>p.id).join('~');
    try{if(navigator.share){await navigator.share({title:tr('Wishlist'),url:u})}else{await navigator.clipboard.writeText(u);toast('Link copied')}}catch(e){if(e&&e.name!=='AbortError')toast('Could not share the link',1)}}},'↗ '+tr('Share wishlist')));
  const h1=r.querySelector('h1');h1?h1.after(sum):r.prepend(sum)}
 else{const pop=d.products.filter(p=>!p.rx&&stock(d,p.id)).sort((a,b)=>(b.disc||0)-(a.disc||0)).slice(0,4);
  if(pop.length)r.append(h('section',{},h('h2',{},tr('Popular picks')),h('div',{class:'grid'},pop.map(card))))}
 return r};
views.sharewish=()=>{const ids=(location.hash.split('/')[2]||'').split('~').filter(x=>/^[A-Za-z0-9_-]{1,20}$/.test(x)).slice(0,40),d=db(),L=ids.map(id=>d.products.find(p=>p.id===id)).filter(Boolean);
 if(!L.length)return h('section',{},h('h1',{},tr('Shared wishlist')),h('p',{class:'empty'},'This link is empty or no longer valid.'),h('a',{class:'btn',href:'#/'},tr('Shop')));
 return h('section',{},h('h1',{},tr('Shared wishlist')+' ('+L.length+')'),
  h('div',{class:'row'},h('button',{class:'btn',type:'button',onclick(){const w=wish();L.forEach(p=>{if(!w.includes(p.id))w.push(p.id)});localStorage.setItem('mc_wish',JSON.stringify(w));toast('Saved to your wishlist');location.hash='#/wishlist'}},tr('Save all to my wishlist')),
   h('button',{class:'btn2',type:'button',onclick(){const c=cart();let n=0;L.forEach(p=>{const st=stock(d,p.id);if(st>(c[p.id]||0)){c[p.id]=(c[p.id]||0)+1;n++}});setCart(c);toast(n?n+' item(s) added to cart':'Nothing could be added',!n)}},tr('Add to cart'))),
  h('div',{class:'grid'},L.map(card)))};

// ---------------------------------------------------------------- Orders
// The orders view already has totals, filters, search, receipts and return requests. This only adds a shortcut to the
// contact form with the order number filled in, and a plain-language guide to the statuses.
const DESC={Pending:'We received your order and the pharmacy has not looked at it yet.','Prescription Review':'A pharmacist is checking your prescription details.',Confirmed:'The pharmacy accepted your order.',Processing:'Your items are being prepared.',Packed:'Your order is packed and waiting for delivery.',Shipped:'Your order is on its way.',Delivered:'Your order arrived.',Cancelled:'The order was cancelled.','Return Requested':'You asked to return this order; the pharmacy will review it.',Returned:'The return was accepted.',Refunded:'The pharmacy refunded the order.'};
const orderNo=a=>(a.textContent.match(/\b[A-Z]{2,4}-\d{3,6}\b/)||[])[0]||'';
const helpBtn=a=>{const no=orderNo(a);if(!no||a.dataset.helped||!a.querySelector('.timeline'))return;a.dataset.helped='1';a.append(h('div',{class:'row'},h('button',{type:'button',class:'btn2',onclick(){try{sessionStorage.setItem('mc_cpre',no)}catch(e){}location.hash='#/contact'}},'💬 '+tr('Need help with this order?'))))};
const or0=views.orders;
views.orders=function(){const r=or0.apply(this,arguments);
 try{const run=()=>r.querySelectorAll('.timeline').forEach(t=>{let a=t.parentElement;for(let k=0;k<4&&a&&!orderNo(a);k++)a=a.parentElement;if(a&&a!==r)helpBtn(a)});run();
  new MutationObserver(run).observe(r,{childList:true,subtree:true});   // orders found later with "Track an order" get the button too
  if(r.querySelector('article.card .timeline')&&typeof STATUS!=='undefined')r.append(h('details',{class:'card'},h('summary',{},tr('What do the statuses mean?')),h('dl',{},STATUS.filter(s=>DESC[s]).flatMap(s=>[h('dt',{},s),h('dd',{},DESC[s])]))))
 }catch(e){console.error(e)}
 return r};

// ---------------------------------------------------------------- Help
const info0=views.info;
views.info=function(){const r=info0.apply(this,arguments);
 try{const h1=r.querySelector('h1');
  const emer=h('div',{class:'card warn',role:'note'},h('b',{},tr('Medical emergency?')+' '),'Call 999 (Bangladesh national emergency service) or go to the nearest hospital. Do not use this website for emergencies.');
  const pr=h('button',{type:'button',class:'btn2',onclick:()=>print()},'🖨 '+tr('Print this page'));
  h1?h1.after(emer,h('p',{},pr)):r.prepend(emer);
  const items=[['How do I compare medicines?','Tap ⚖ on up to 3 product cards, then open Compare. You see price per unit and details side by side. This compares packs and prices only; ask the pharmacist before switching any medicine.'],
   ['Can I share my cart or wishlist?','Yes. Use Copy cart link in the cart or Share wishlist on the wishlist. Whoever opens the link can add the items to their own cart, limited to what is in stock.'],
   ['How do medicine reminders work?','Open Health, add a medicine name and time. While this site is open in your browser it shows a message (and a browser notification if you allow it). Reminders are saved on this device only and do not replace your prescription instructions.'],
   ['Can I search by voice?','If your browser supports it, a 🎤 button appears next to the search box. Allow the microphone when asked, then say the medicine name.'],
   ['How do I make the text bigger?','Press the Aa button in the header to cycle through text sizes. Your choice is remembered on this device.'],
   ['How do I get help with an order?','Open Orders, find the order and choose Need help with this order. The contact form opens with the order number filled in.']];
  const det=items.map(([q,a])=>h('details',{},h('summary',{},q),h('p',{},a))),grp=h('div',{},h('h3',{},tr('Using this website')),...det);
  const none=r.querySelector('p.empty[role=status]');none?none.before(grp):r.append(grp);
  const si=r.querySelector('input[type=search]');if(si)si.addEventListener('input',e=>{const q=e.target.value.trim().toLowerCase();det.forEach((d,i)=>{d.hidden=!!q&&!(items[i].join(' ').toLowerCase().includes(q))});grp.hidden=!!q&&det.every(d=>d.hidden)})
 }catch(e){console.error(e)}
 return r};

// ---------------------------------------------------------------- Contact
const dhakaOpen=()=>{const s=db().settings||{},p=new Intl.DateTimeFormat('en-GB',{timeZone:'Asia/Dhaka',weekday:'short',hour:'2-digit',minute:'2-digit',hour12:false}).formatToParts(new Date()),
 g=t=>p.find(x=>x.type===t).value,hr=(+g('hour')%24)+(+g('minute'))/60,fri=g('weekday')==='Fri',a=s.openFrom!=null&&!isNaN(+s.openFrom)?+s.openFrom:(fri?15:9),b=s.openTo!=null&&!isNaN(+s.openTo)?+s.openTo:22;return hr>=a&&hr<b};
const ct0=views.contact;
views.contact=function(){const r=ct0.apply(this,arguments);
 try{const f=r.querySelector('form');
  if(f&&f.elements.n){const t=f.elements,pf=typeof PROF==='function'?PROF():{},dr=LS('mc_cdraft',{});
   t.n.value=t.n.value||dr.n||pf.name||'';t.ph.value=t.ph.value||dr.ph||pf.phone||'';if(dr.m&&!t.m.value)t.m.value=dr.m;
   const cc=r.querySelector('#cc2');if(cc)cc.textContent=t.m.value.length+' / 500';
   let pre='';try{pre=sessionStorage.getItem('mc_cpre')||'';sessionStorage.removeItem('mc_cpre')}catch(e){}
   if(pre&&/^[A-Za-z]{2,4}-\d{3,6}$/.test(pre)){t.o.value=pre;if(t.t)t.t.value='Order or delivery';t.m.focus()}
   f.addEventListener('input',()=>SVv('mc_cdraft',{n:t.n.value,ph:t.ph.value,m:t.m.value}));f.addEventListener('reset',()=>{try{localStorage.removeItem('mc_cdraft')}catch(e){}})}
  const info=[...r.querySelectorAll('.card')].find(c=>c.querySelector('h2')&&/Visit or call/.test(c.querySelector('h2').textContent));
  if(info){const s=db().settings||{},num=waNum(),open=dhakaOpen();
   info.append(h('p',{},h('span',{class:'openb'+(open?' on':''),role:'status'},(open?'● ':'○ ')+tr(open?'Open now':'Closed now'))),
    h('div',{class:'row'},num?h('a',{class:'btn2',href:'https://wa.me/'+num,target:'_blank',rel:'noopener noreferrer'},'💬 '+tr('Message on WhatsApp')):null,
     s.phone?h('button',{type:'button',class:'btn2',onclick:async()=>{try{await navigator.clipboard.writeText(s.phone);toast('Phone number copied')}catch(e){toast('Could not copy',1)}}},tr('Copy phone')):null,
     h('a',{class:'btn2',href:'https://www.openstreetmap.org/search?query='+encodeURIComponent(s.address||'Dhanmondi, Dhaka'),target:'_blank',rel:'noopener noreferrer'},'📍 '+tr('Show on map'))))}
 }catch(e){console.error(e)}
 return r};

// ---------------------------------------------------------------- Health additions
const SEV=['ok','warn','bad'];
const bpClass=(s,d)=>s>180||d>120?[2,'Very high. If you also have chest pain, severe headache, weakness or trouble speaking, get emergency help now.']:s>=140||d>=90?[2,'High range. Please see a doctor.']:s>=130||d>=80?[1,'Above the normal range (stage 1). Talk to your doctor.']:s>=120?[1,'Slightly raised. Keep checking and talk to your doctor.']:s<90||d<60?[1,'Low reading. If you feel dizzy or faint, get medical help.']:[0,'Within the normal range.'];
const bgClass=(v,ctx)=>{if(v<3.9)return[2,'Low. If you feel shaky, sweaty or confused, take sugar and get help.'];
 if(ctx==='fasting')return v<=5.5?[0,'Within the usual fasting range.']:v<7?[1,'Above the usual fasting range. Talk to your doctor.']:[2,'In the range doctors treat as diabetes. Please see a doctor.'];
 if(ctx==='after')return v<7.8?[0,'Within the usual range two hours after a meal.']:v<11.1?[1,'Above the usual range after a meal. Talk to your doctor.']:[2,'High. Please see a doctor.'];
 return v>=11.1?[2,'High. Please see a doctor.']:[0,'No concern flagged for a random reading; ask your doctor how to read it.']};
const logs=()=>LS('mc_hlog',[]);
const spark=(series,labels)=>{const all=series.flat();if(all.length<2)return null;const W=300,H=80,mn=Math.min(...all),mx=Math.max(...all),span=mx-mn||1,ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');
 svg.setAttribute('viewBox','0 0 '+W+' '+H);svg.setAttribute('role','img');svg.setAttribute('aria-label',labels);svg.setAttribute('class','spark');
 series.forEach((s,k)=>{if(s.length<2)return;const pts=s.map((v,i)=>[(i/(s.length-1))*(W-10)+5,H-8-((v-mn)/span)*(H-16)].map(n=>n.toFixed(1)).join(',')).join(' '),pl=document.createElementNS(ns,'polyline');
  pl.setAttribute('points',pts);pl.setAttribute('fill','none');pl.setAttribute('stroke','currentColor');pl.setAttribute('stroke-width','2');if(k)pl.setAttribute('stroke-dasharray','5 3');svg.append(pl)});return svg};
const dl=(name,text)=>{const a=document.createElement('a'),u=URL.createObjectURL(new Blob([text],{type:'text/csv'}));a.href=u;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),2000)};
const health0=views.health;
views.health=function(){const r=health0.apply(this,arguments);
 try{
  const emer=h('div',{class:'card warn',role:'note'},h('b',{},tr('Emergency')+': '),'call 999 (Bangladesh national emergency service). Do not wait for a reminder, a reading or a website.');
  const dis=r.querySelector('p.muted');dis?dis.after(emer):r.prepend(emer);
  // health log
  let type='bp',showAll=false;const body=h('div',{});
  const fm=h('form',{novalidate:true}),draw=()=>{
   const L=logs().sort((a,b)=>a.at.localeCompare(b.at)),sel=L.filter(x=>x.t===type),rec=sel.slice(-10).reverse();
   const names={bp:'Blood pressure (mmHg)',bg:'Blood sugar (mmol/L)',wt:'Weight (kg)'};
   const val=x=>x.t==='bp'?x.a+'/'+x.b+(x.c?' · pulse '+x.c:''):x.t==='bg'?x.a+(x.c?' ('+({fasting:'fasting',after:'after meal',random:'random'}[x.c]||'')+')':''):String(x.a);
   const cl=x=>x.t==='bp'?bpClass(x.a,x.b):x.t==='bg'?bgClass(x.a,x.c):null;
   const last14=sel.slice(-14),ch=type==='bp'?spark([last14.map(x=>x.a),last14.map(x=>x.b)],'Blood pressure trend, solid line top number, dashed line bottom number'):spark([last14.map(x=>x.a)],names[type]+' trend');
   body.replaceChildren(
    sel.length?h('p',{class:'muted'},names[type]+': '+sel.length+' reading(s)'):h('p',{class:'muted'},'No readings yet.'),ch||null,
    rec.length?h('div',{class:'scroll'},h('table',{},h('thead',{},h('tr',{},['Date','Reading','Note',''].map(x=>h('th',{scope:'col'},x)))),h('tbody',{},rec.map(x=>{const c=cl(x);return h('tr',{},h('td',{},new Date(x.at).toLocaleString('en-GB',{dateStyle:'medium',timeStyle:'short'})),h('td',{},val(x)),h('td',{class:c?SEV[c[0]]:''},c?c[1]:''),
     h('td',{},h('button',{type:'button',class:'btn2','aria-label':tr('Remove')+' '+val(x),onclick(){SVv('mc_hlog',logs().filter(y=>y.id!==x.id));draw()}},tr('Remove'))))})))):null,
    h('div',{class:'row'},h('button',{type:'button',class:'btn2',onclick(){const L2=logs();if(!L2.length)return toast('Nothing to export',1);dl('health-log.csv',['Date,Type,Value 1,Value 2,Pulse or context',...L2.map(x=>[x.at,x.t,x.a,x.b??'',x.c??''].join(','))].join('\n'))}},tr('Export CSV')),
     h('button',{type:'button',class:'btn2',onclick(){if(confirm('Delete every saved reading on this device?')){SVv('mc_hlog',[]);draw()}}},'Clear all')))};
  const kind=h('select',{name:'k','aria-label':'Reading type',onchange(e){type=e.target.value;fields();draw()}},[['bp','Blood pressure'],['bg','Blood sugar'],['wt','Weight']].map(([v,l])=>h('option',{value:v},tr(l))));
  const a=h('input',{name:'a',type:'number',inputmode:'decimal',step:'any'}),b=h('input',{name:'b',type:'number',inputmode:'decimal',step:'any'}),c=h('input',{name:'c',type:'number',inputmode:'numeric'}),cx=h('select',{name:'x'},[['fasting','Fasting'],['after','2 hours after a meal'],['random','Random']].map(([v,l])=>h('option',{value:v},l)));
  const la=h('label',{}),lb=h('label',{}),lc=h('label',{}),lx=h('label',{},'When',cx);
  const fields=()=>{la.replaceChildren(type==='bp'?'Top number (systolic)':type==='bg'?'Reading (mmol/L)':'Weight (kg)',a);lb.replaceChildren('Bottom number (diastolic)',b);lb.hidden=type!=='bp';lc.replaceChildren('Pulse (optional)',c);lc.hidden=type!=='bp';lx.hidden=type!=='bg'};
  fm.append(h('label',{},'Type',kind),la,lb,lc,lx,h('button',{class:'btn'},tr('Save reading')));fields();
  fm.onsubmit=e=>{e.preventDefault();const A=+a.value,B=+b.value,C=+c.value;let ok=false,rec={id:uid('H'),t:type,at:new Date().toISOString(),a:A};
   if(type==='bp'){ok=A>=50&&A<=300&&B>=30&&B<=200&&A>B;rec.b=B;if(C)rec.c=Math.round(C)}else if(type==='bg'){ok=A>=1&&A<=40;rec.c=cx.value}else{ok=A>=2&&A<=400}
   if(!ok)return toast('Please check the numbers you typed',1);const L=logs();L.push(rec);SVv('mc_hlog',L.slice(-200));fm.reset();fields();draw();
   const cls=type==='bp'?bpClass(A,B):type==='bg'?bgClass(A,rec.c):null;toast(cls?cls[1]:'Reading saved',cls&&cls[0]===2)};
  draw();
  // water tracker
  const wk=()=>{const d=LS('mc_water',{});return d.d===ldate()?d:{d:ldate(),n:0,g:d.g||8}};const prog=h('progress',{max:8,value:0,'aria-label':tr('Water today')}),cnt=h('output',{'aria-live':'polite'});
  const wdraw=()=>{const d=wk();prog.max=d.g;prog.value=Math.min(d.n,d.g);cnt.textContent=d.n+' / '+d.g+' cups'};
  const wset=f=>{const d=wk();f(d);d.n=Math.max(0,Math.min(40,d.n));SVv('mc_water',d);wdraw()};wdraw();
  const goal=h('input',{type:'number',min:1,max:20,value:wk().g,'aria-label':'Daily goal in cups',onchange(e){const v=Math.max(1,Math.min(20,Math.round(+e.target.value)||8));wset(d=>{d.g=v})}});
  // print schedule
  const printSched=()=>{const R=LS('mc_rem',[]).slice().sort((x,y)=>String(x.time).localeCompare(String(y.time)));if(!R.length)return toast('Add a reminder first',1);
   const w=h('dialog',{class:'rcpt'},h('h2',{},'Medicine schedule'),h('table',{},h('thead',{},h('tr',{},['Time','Medicine','Note'].map(x=>h('th',{scope:'col'},x)))),h('tbody',{},R.map(x=>h('tr',{},h('td',{},x.time),h('td',{},x.name),h('td',{},x.note||''))))),
    h('p',{class:'muted'},'Printed '+new Date().toLocaleDateString('en-GB',{dateStyle:'medium'})+'. Follow your doctor and the label on the medicine.'),h('button',{type:'button',onclick:()=>print()},tr('Print')),h('button',{type:'button',onclick(){w.close();w.remove()}},tr('Close')));w.addEventListener('close',()=>w.remove());document.body.append(w);w.showModal()};
  const grid=h('div',{class:'hgrid'},
   h('article',{class:'card wide'},h('h2',{},tr('Health log')),h('p',{class:'muted'},'Keep your own readings and see the trend. General adult ranges only: this is not a diagnosis. Saved on this device only.'),fm,body),
   h('article',{class:'card'},h('h2',{},tr('Water today')),h('p',{class:'muted'},'One cup is about 250 ml. Needs differ with weather, activity and health conditions.'),prog,cnt,
    h('div',{class:'row'},h('button',{type:'button',class:'btn2','aria-label':'One cup less',onclick:()=>wset(d=>{d.n--})},'−'),h('button',{type:'button',class:'btn',onclick:()=>wset(d=>{d.n++})},'+ 1 cup'),h('label',{},'Goal ',goal)),
    h('h3',{},tr('Print my schedule')),h('button',{type:'button',class:'btn2',onclick:printSched},'🖨 '+tr('Print my schedule'))));
  const g1=r.querySelector('.hgrid');g1?g1.after(grid):r.append(grid)
 }catch(e){console.error(e)}
 return r};


// ================================================================ v2.1 additions
if(typeof I18!=='undefined')Object.assign(I18.bn,{'Recent searches':'সাম্প্রতিক সার্চ','Scan a barcode':'বারকোড স্ক্যান','Same ingredient, other brands':'একই উপাদান, অন্য ব্র্যান্ড','Sort':'সাজান','Copy list as text':'তালিকা টেক্সট হিসেবে কপি','Time to reorder?':'আবার অর্ডারের সময়?','Spending by month':'মাসভিত্তিক খরচ','Know your medicine':'আপনার ওষুধ জানুন','Call me back':'আমাকে কল করুন','Dose times planner':'ডোজের সময় পরিকল্পনা','Supply calculator':'ওষুধ কতদিন চলবে','Add to calendar':'ক্যালেন্ডারে যোগ করুন','Create reminders':'রিমাইন্ডার তৈরি করুন'});
const unitOf=p=>{const m=String(p.pack||'').match(/(\d+)\s*([A-Za-z]+)/);return m&&+m[1]>1?{n:+m[1],w:m[2].replace(/s$/i,'').toLowerCase()}:null};
// --- Shop: price per unit on cards
const card2=card;card=function(p){const a=card2.apply(this,arguments);try{const u=unitOf(p),pe=a.querySelector('.price');if(u&&pe&&!a.querySelector('.ppu'))pe.after(h('small',{class:'muted ppu'},'৳'+(eff(p)/u.n).toFixed(2)+' / '+u.w))}catch(e){}return a};
// --- Shop: recent searches + barcode scan
const RS='mc_rs',recentQ=()=>LS(RS,[]);
const SC=window.BarcodeDetector&&navigator.mediaDevices&&navigator.mediaDevices.getUserMedia;
const scan=async()=>{let stream=null,timer=0,lock=false;const vid=h('video',{playsinline:true,muted:true,autoplay:true,'aria-label':'Camera preview',style:'width:100%;max-height:50vh;background:#000'});
 const close=()=>{clearInterval(timer);if(stream)stream.getTracks().forEach(t=>t.stop());w.close();w.remove()};
 const w=h('dialog',{class:'qv','aria-label':tr('Scan a barcode')},h('h2',{},tr('Scan a barcode')),h('p',{class:'muted'},'Point the camera at the barcode on the pack. It works for products that have a barcode saved in the shop.'),vid,h('p',{},h('button',{type:'button',class:'btn2',onclick:close},tr('Close'))));
 w.addEventListener('close',()=>{clearInterval(timer);if(stream)stream.getTracks().forEach(t=>t.stop());w.remove()});document.body.append(w);w.showModal();
 try{stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:'environment'}});vid.srcObject=stream;try{const pl=vid.play();if(pl&&pl.catch)pl.catch(()=>{})}catch(e){}
  const det=new window.BarcodeDetector();timer=setInterval(async()=>{if(lock)return;try{const c=await det.detect(vid);if(!c.length)return;const v=String(c[0].rawValue||'').trim();lock=true;
   const p=db().products.find(x=>v&&(String(x.barcode||'')===v||String(x.sku||'')===v));if(p){close();location.hash='#/product/'+p.id}else{toast('No product with this barcode',1);setTimeout(()=>{lock=false},2000)}}catch(e){}},400)}
 catch(e){toast(e&&e.name==='NotAllowedError'?'Camera permission is blocked':'Could not start the camera',1);close()}};
const cat3=views.catalog;views.catalog=function(){const r=cat3.apply(this,arguments);
 try{const i=r.querySelector('.filters input[type=search]');
  if(i){i.addEventListener('change',e=>{const q=e.target.value.trim().toLowerCase();if(q.length>=2)SVv(RS,[q,...recentQ().filter(x=>x!==q)].slice(0,6))});
   if(SC&&!r.querySelector('.scanbtn')){const b=h('button',{type:'button',class:'scanbtn btn2','aria-label':tr('Scan a barcode'),title:tr('Scan a barcode'),onclick:scan},'📷');(r.querySelector('.mic')||i).after(b)}}
  const rq=recentQ();const tog=r.querySelector('.viewtog');
  if(rq.length&&tog)tog.after(h('div',{class:'row',role:'group','aria-label':tr('Recent searches')},h('small',{class:'muted'},tr('Recent searches')+':'),...rq.map(q=>h('button',{type:'button',class:'btn2',onclick(){S.q=q;S.page=1;render()}},q)),h('button',{type:'button',class:'linkbtn','aria-label':tr('Clear'),onclick(){SVv(RS,[]);render()}},'✕')))
 }catch(e){console.error(e)}return r};
// --- Shop: same ingredient, other brands on the product page
const prod2=views.product;views.product=function(){const r=prod2.apply(this,arguments);
 try{const id=(location.hash.split('/')[2]||new URLSearchParams(location.search).get('id')||'').split('?')[0],d=db(),p=d.products.find(x=>x.id===id);
  if(p&&p.generic){const g=p.generic.toLowerCase().trim(),per=x=>{const u=unitOf(x);return u?eff(x)/u.n:eff(x)},base=per(p);
   const alt=d.products.filter(x=>x.id!==p.id&&String(x.generic||'').toLowerCase().trim()===g&&stock(d,x.id)>0).sort((a,b)=>per(a)-per(b)).slice(0,4);
   if(alt.length)r.append(h('section',{class:'card',role:'region','aria-label':tr('Same ingredient, other brands')},h('h2',{},tr('Same ingredient, other brands')),
    h('p',{class:'muted'},'Same active ingredient and name of the medicine. Strength and pack size can differ: compare them first, and ask the pharmacist before switching. Prescription items still need a prescription.'),
    h('ul',{},alt.map(x=>{const pu=per(x),dif=Math.round((1-pu/base)*100),u=unitOf(x);return h('li',{},h('a',{href:'#/product/'+x.id},PN(x)),' · '+[x.strength&&x.strength!=='—'?x.strength:'',x.pack].filter(Boolean).join(' · ')+' · '+money(eff(x))+(u?' (৳'+pu.toFixed(2)+' / '+u.w+')':'')+(dif>=5?' · '+dif+'% cheaper per unit':dif<=-5?' · '+(-dif)+'% dearer per unit':''))}))))}
 }catch(e){console.error(e)}return r};

// --- Wishlist: sort, personal notes, copy as text
const wl2=views.wishlist;views.wishlist=function(){const r=wl2.apply(this,arguments);
 try{const d=db(),w=wish(),L=d.products.filter(p=>w.includes(p.id)),grid=r.querySelector('.grid'),cards=grid?[...grid.querySelectorAll(':scope>article.card')]:[];
  if(L.length&&cards.length===L.length){const notes=LS('mc_wnote',{}),pairs=cards.map((c,i)=>({c,p:L[i]}));
   pairs.forEach(({c,p})=>c.append(h('label',{class:'wnote'},tr('Note'),h('input',{value:notes[p.id]||'',maxlength:80,placeholder:'e.g. for Dad, ask the doctor','aria-label':'Note for '+p.name,onchange(e){const n=LS('mc_wnote',{});if(e.target.value.trim())n[p.id]=e.target.value.trim().slice(0,80);else delete n[p.id];SVv('mc_wnote',n)}}))));
   const keys={saved:null,name:(a,b)=>a.p.name.localeCompare(b.p.name),lo:(a,b)=>eff(a.p)-eff(b.p),hi:(a,b)=>eff(b.p)-eff(a.p),disc:(a,b)=>(b.p.disc||0)-(a.p.disc||0),stock:(a,b)=>(stock(d,b.p.id)>0)-(stock(d,a.p.id)>0)};
   const apply=k=>{const f=keys[k];const arr=f?pairs.slice().sort(f):pairs;grid.append(...arr.map(x=>x.c))};
   const cur=LS('mc_wsort','saved');const sel=h('select',{'aria-label':tr('Sort'),onchange(e){SVv('mc_wsort',e.target.value);apply(e.target.value)}},[['saved','Saved order'],['name','Name'],['lo','Price low–high'],['hi','Price high–low'],['disc','Biggest discount'],['stock','In stock first']].map(([v,l])=>h('option',{value:v,selected:v===cur},l)));
   apply(cur in keys?cur:'saved');
   const text=()=>{const n=LS('mc_wnote',{});return d.settings.store+' – wishlist\n'+L.map(p=>'• '+p.name+' ('+[p.strength&&p.strength!=='—'?p.strength:'',p.pack].filter(Boolean).join(', ')+') – '+money(eff(p))+(stock(d,p.id)>0?'':' (out of stock)')+(n[p.id]?' – '+n[p.id]:'')).join('\n')};
   const num=waNum(),row=h('div',{class:'row'},h('label',{},tr('Sort')+' ',sel),h('button',{type:'button',class:'btn2',onclick:async()=>{try{await navigator.clipboard.writeText(text());toast('List copied')}catch(e){toast('Could not copy',1)}}},tr('Copy list as text')),
    num?h('a',{class:'btn2',href:'https://wa.me/'+num+'?text='+encodeURIComponent('Hello, are these available?\n'+text()),target:'_blank',rel:'noopener noreferrer',onclick(e){e.currentTarget.href='https://wa.me/'+num+'?text='+encodeURIComponent('Hello, are these available?\n'+text())}},'💬 '+tr('Ask the pharmacist on WhatsApp')):null);
   grid.before(row)}
 }catch(e){console.error(e)}return r};

// --- Orders: reorder suggestions and spending by month (from this customer's own orders)
const myOrders=()=>{try{return(typeof SERVER!=='undefined'&&SERVER)?(typeof MYORD!=='undefined'?MYORD:[]):db().orders.filter(o=>o.customer===(typeof me==='function'?me():null))}catch(e){return[]}};
const or2=views.orders;views.orders=function(){const r=or2.apply(this,arguments);
 try{const O=myOrders().filter(o=>!['Cancelled','Returned','Refunded'].includes(o.status));if(!O.length)return r;const d=db(),now=Date.now(),last={};
  O.filter(o=>o.status==='Delivered').forEach(o=>(o.items||[]).forEach(i=>{const id=i.pid||i.id,t=new Date(o.at).getTime();if(id&&(!last[id]||t>last[id]))last[id]=t}));
  const sug=Object.entries(last).map(([id,t])=>({p:d.products.find(x=>x.id===id),days:Math.floor((now-t)/864e5)})).filter(x=>x.p&&x.days>=25&&stock(d,x.p.id)>0).sort((a,b)=>b.days-a.days).slice(0,5);
  const mon={};for(let k=5;k>=0;k--){const dt=new Date();dt.setDate(1);dt.setMonth(dt.getMonth()-k);mon[dt.getFullYear()+'-'+String(dt.getMonth()+1).padStart(2,'0')]=0}
  O.forEach(o=>{const k=new Date(o.at).toLocaleDateString('en-CA').slice(0,7);if(k in mon)mon[k]+=+o.total||0});const mx=Math.max(1,...Object.values(mon));
  const box=h('section',{class:'card'},
   sug.length?h('div',{},h('h2',{},tr('Time to reorder?')),h('p',{class:'muted'},'Things you bought a while ago. This is only a reminder: follow your doctor and your prescription for how much and how often.'),
    h('ul',{},sug.map(({p,days})=>h('li',{},PN(p)+' · '+days+' days ago · '+money(eff(p))+' ',h('button',{type:'button',class:'btn2',onclick(){const c=cart();if((c[p.id]||0)+1>stock(d,p.id))return toast('Only '+stock(d,p.id)+' available',1);c[p.id]=(c[p.id]||0)+1;setCart(c);toast('Added to cart')}},tr('Add to cart')))))):null,
   Object.values(mon).some(v=>v>0)?h('div',{},h('h2',{},tr('Spending by month')),h('div',{class:'hbars',role:'list'},Object.entries(mon).map(([k,v])=>h('div',{class:'br',role:'listitem'},h('span',{},k.slice(2)),h('i',{style:'width:'+Math.round(v/mx*100)+'%'}),h('span',{},money(v)))))):null);
  r.append(box)}catch(e){console.error(e)}return r};

// --- Help: know your medicine
const info2=views.info;views.info=function(){const r=info2.apply(this,arguments);
 try{const items=[['What does Rx or "prescription required" mean?','The medicine is sold only against a valid prescription from a registered doctor. At checkout the pharmacist reviews it before the order is sent.'],
  ['Brand and generic: what is the difference?','A generic name is the active ingredient (for example paracetamol). Brands are the same ingredient made by different companies, often at different prices. Strength and pack size can differ, so compare them and ask the pharmacist before switching.'],
  ['How do I read a medicine pack?','Look for the name and strength (for example 500 mg), the form (tablet, capsule, syrup), the batch number, the manufacturing and expiry dates, the storage advice, the maker and the printed price. Never use a medicine past its expiry date.'],
  ['Tablet, capsule, syrup, drops: what is the difference?','These are forms of medicine. Tablets and capsules are swallowed whole unless the label says otherwise. Syrups and drops are measured with the cup or dropper that comes with the pack, not a kitchen spoon.'],
  ['How should I store medicines?','Keep them in a cool, dry place away from sunlight, heat and children. Some need a fridge: check the label. Keep them in their original pack so the batch and expiry stay visible.'],
  ['What should I do with expired or leftover medicines?','Do not use expired medicine and do not share leftovers. Ask the pharmacy how to dispose of them safely.'],
  ['Why finish a full antibiotic course?','Stopping early can leave bacteria alive and make the infection return or resist treatment. Take antibiotics exactly as prescribed, and only when prescribed.']];
  const det=items.map(([q,a])=>h('details',{},h('summary',{},q),h('p',{},a))),grp=h('div',{},h('h3',{},tr('Know your medicine')),...det,h('p',{class:'muted'},'General information only. It does not replace your doctor or pharmacist.'));
  const first=[...r.querySelectorAll('h3')].find(x=>/Using this website/.test(x.textContent)),host=first?first.parentElement:null;host?host.after(grp):r.append(grp);
  const si=r.querySelector('input[type=search]');if(si)si.addEventListener('input',e=>{const q=e.target.value.trim().toLowerCase();det.forEach((d,i)=>{d.hidden=!!q&&!items[i].join(' ').toLowerCase().includes(q)});grp.hidden=!!q&&det.every(d=>d.hidden)})
 }catch(e){console.error(e)}return r};

// --- Contact: call-back time and pick a recent order
const ct2=views.contact;views.contact=function(){const r=ct2.apply(this,arguments);
 try{const f=r.querySelector('form');if(f&&f.elements.m){const t=f.elements,wrap=h('div',{role:'group','aria-label':tr('Call me back')},h('small',{class:'muted'},tr('Call me back')+': '),
   ...['Morning (9-12)','Afternoon (12-5)','Evening (5-9)'].map(sl=>h('button',{type:'button',class:'btn2',onclick(){const line='Please call me back: '+sl+'.';if(!t.m.value.includes('Please call me back:'))t.m.value=(t.m.value?t.m.value+'\n':'')+line;else t.m.value=t.m.value.replace(/Please call me back: [^\n]*/,line);t.m.dispatchEvent(new Event('input',{bubbles:true}));t.m.focus()}},sl)));
  t.m.closest('label')?t.m.closest('label').after(wrap):t.m.after(wrap);
  const O=myOrders().slice().sort((a,b)=>String(b.at).localeCompare(String(a.at))).slice(0,5);
  if(O.length&&t.o){const sel=h('select',{'aria-label':'Pick a recent order',onchange(e){if(e.target.value)t.o.value=e.target.value}},h('option',{value:''},'Pick a recent order'),O.map(o=>h('option',{value:o.no||o.id},(o.no||o.id)+' · '+money(o.total))));t.o.closest('label')?t.o.closest('label').after(sel):t.o.after(sel)}}
 }catch(e){console.error(e)}return r};

// --- Health: dose times planner and supply calculator
const health2=views.health;views.health=function(){const r=health2.apply(this,arguments);
 try{const out=h('p',{class:'hres',hidden:true,'aria-live':'polite'}),dn=h('input',{name:'dn',maxlength:60}),ds=h('input',{name:'ds',type:'time',value:'08:00'}),di=h('select',{name:'di'},[[24,'once a day'],[12,'every 12 hours'],[8,'every 8 hours'],[6,'every 6 hours'],[4,'every 4 hours']].map(([v,l])=>h('option',{value:v},l)));
  const times=()=>{const [hh,mm]=(ds.value||'08:00').split(':').map(Number),step=+di.value,n=Math.floor(24/step);return Array.from({length:n},(_,k)=>{const x=(hh*60+mm+k*step*60)%1440;return String(Math.floor(x/60)).padStart(2,'0')+':'+String(x%60).padStart(2,'0')}).sort()};
  const show=()=>{out.hidden=false;out.textContent='Dose times: '+times().join(', ')+'. Use the times your doctor or the label gives you.'};
  [ds,di].forEach(x=>x.addEventListener('change',show));
  const mk=h('button',{type:'button',class:'btn',onclick(){const nm=dn.value.trim().slice(0,60);if(nm.length<2)return toast('Enter the medicine name',1);const R=LS('mc_rem',[]),T2=times();if(R.length+T2.length>20)return toast('You can keep up to 20 reminders',1);
   T2.forEach(tm=>R.push({id:uid('R'),name:nm,time:tm,note:'dose planner'}));SVv('mc_rem',R);toast(T2.length+' reminder(s) added');render()}},tr('Create reminders'));
  const sn=h('input',{name:'sn',maxlength:60}),su=h('input',{name:'su',type:'number',min:1,max:1000,inputmode:'numeric'}),sp=h('input',{name:'sp',type:'number',min:0.5,max:24,step:'0.5',value:'1',inputmode:'decimal'}),so=h('p',{class:'hres',hidden:true,'aria-live':'polite'});let runout=null;
  const ics=h('button',{type:'button',class:'btn2',hidden:true,onclick(){if(!runout)return;const warn=new Date(runout);warn.setDate(warn.getDate()-3);const ymd=x=>x.getFullYear()+String(x.getMonth()+1).padStart(2,'0')+String(x.getDate()).padStart(2,'0'),nm=(sn.value.trim()||'medicine').replace(/[\r\n,;]/g,' ');
   const body=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//Shop//Reminder//EN','BEGIN:VEVENT','UID:'+uid('E')+'@shop','DTSTAMP:'+new Date().toISOString().replace(/[-:]/g,'').slice(0,15)+'Z','DTSTART;VALUE=DATE:'+ymd(warn),'SUMMARY:Reorder '+nm+' (about 3 days left)','END:VEVENT','END:VCALENDAR'].join('\r\n');
   const a=document.createElement('a'),u=URL.createObjectURL(new Blob([body],{type:'text/calendar'}));a.href=u;a.download='reorder.ics';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),2000)}},'📅 '+tr('Add to calendar'));
  const calc=h('button',{type:'button',class:'btn',onclick(){const u=+su.value,per=+sp.value;if(!(u>=1)||!(per>0))return toast('Enter how many units you have and how many you take a day',1);const days=Math.floor(u/per);runout=new Date();runout.setDate(runout.getDate()+days);
   so.hidden=false;so.textContent='About '+days+' day(s) of supply, until '+runout.toLocaleDateString('en-GB',{dateStyle:'medium'})+'. Reorder a few days before that, and only as your prescription allows.';ics.hidden=false}},'Calculate');
  const grid=h('div',{class:'hgrid'},
   h('article',{class:'card'},h('h2',{},tr('Dose times planner')),h('p',{class:'muted'},'Turns "every 8 hours" into clock times and creates reminders for them. Follow your doctor and the label for the real schedule.'),
    h('div',{class:'hform'},h('label',{},'Medicine name',dn),h('label',{},'First dose',ds),h('label',{},'How often',di),mk),out),
   h('article',{class:'card'},h('h2',{},tr('Supply calculator')),h('p',{class:'muted'},'How long will what you have last?'),
    h('div',{class:'hform'},h('label',{},'Medicine name',sn),h('label',{},'Units in hand (tablets, ml...)',su),h('label',{},'Units taken per day',sp),calc),so,ics));
  r.append(grid)}catch(e){console.error(e)}return r};

{const mr=document.querySelector('meta[name="shagar-route"]');if(mr&&mr.dataset.section&&!window.SECTION)window.SECTION=mr.dataset.section;render()}
})();
