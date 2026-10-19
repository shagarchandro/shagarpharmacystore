// sw.js: network-first service worker. Online you always get the latest files; offline you get the last copy you visited.
const C='mc-v2';
const CORE=['index.html','admin/index.html','admin/login.html','assets/css/styles.css','assets/css/admin.css','assets/css/responsive.css','assets/js/utils.js','assets/js/i18n.js','assets/js/storage.js','assets/js/store.js','assets/js/admin.js','assets/icons/favicon.svg','assets/images/logo.svg','manifest.webmanifest'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(C).then(c=>c.addAll(CORE)).then(()=>self.skipWaiting()))});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x!==C).map(x=>caches.delete(x)))).then(()=>self.clients.claim()))});
self.addEventListener('fetch',e=>{const r=e.request;if(r.method!=='GET'||new URL(r.url).origin!==location.origin)return;
e.respondWith(fetch(r).then(res=>{if(res.ok){const cp=res.clone();caches.open(C).then(c=>c.put(r,cp))}return res}).catch(()=>caches.match(r,{ignoreSearch:true}).then(m=>m||caches.match(r.mode==='navigate'?(new URL(r.url).pathname.includes('/admin/')?'admin/index.html':'index.html'):r))))});
