# Shagar Medical Store – Pharmacy Management System (demo)

A responsive pharmacy storefront plus admin panel for Shagar Medical Store (demo data is fictional), built with HTML5, CSS3 and vanilla JavaScript (no framework, no build step). Data lives in the browser's LocalStorage.

> **Two modes.** Open the pages from any static server for the browser-only demo, or run `python3 server/server.py` for the real server mode (shared database, real logins, server-side checks). See "Real server mode".

## Requirements
Any modern browser and a local static server (VS Code Live Server, `python3 -m http.server`, etc.). Pages must be served over HTTP, not opened as `file://`.

## Run with VS Code Live Server
1. Extract the ZIP and open the `MediCare-Pharmacy` folder in VS Code (the folder and ZIP names follow the original project brief; the shop name shown on the site is Shagar Medical Store).
2. Right-click `index.html` → **Open with Live Server**.
3. Admin panel: `/admin/login.html`. Pick a demo user and enter the demo code **`demo`** (it is a convenience, not security; no passwords are stored).

Demo users: Owner, Pharmacist, Cashier, Inventory Manager, Delivery Staff (manage them under Admin → Users).
Demo coupon: `SAVE10` (10% off orders of ৳500+). Demo barcodes: `890001000` … `890001011`.

## Folder structure
```
index.html                      storefront app (single-page, hash routes)
products.html product-details.html cart.html checkout.html order-success.html
orders.html wishlist.html contact.html faq.html shipping.html returns.html privacy.html terms.html
                                real pages that open the matching storefront screen
admin/login.html                demo login
admin/index.html                admin app (dashboard, products, inventory, POS ...)
admin/products|inventory|pos|orders|customers|suppliers|purchases|returns|reports|expenses|delivery|users|settings.html
                                real pages that open that admin screen
assets/css/styles.css           design tokens, base and storefront components
assets/css/admin.css            admin shell (sidebar, top bar)
assets/css/responsive.css       breakpoints, reduced motion, print rules (loaded last)
assets/js/utils.js              DOM helper, formatting, ids, CSV (formula-safe), toasts
assets/js/i18n.js               English/Bangla dictionary, theme and language helpers
assets/js/storage.js            LocalStorage helpers, schema version, seed data, FEFO stock logic, loyalty
assets/js/store.js              storefront: products, cart, checkout, orders, router
assets/js/admin.js              admin panel: shell, products, inventory, POS, orders, reports, data
assets/icons, assets/images     favicon, logo, placeholder (product images are generated or uploaded)
tests/                          optional developer tests (Playwright / jsdom)
README.md  TEST-CHECKLIST.md  .gitignore
```
The brief's suggested layout is followed for CSS (`styles/admin/responsive`) and for the shared JS (`storage/utils/i18n`). The storefront modules (`products/cart/checkout/app`) live together in `store.js`, and the admin modules (`admin/inventory/pos/reports`) in `admin.js`, because their views share state and are wrapped in a fixed order; splitting them further would add risk without changing behaviour.

## Features
**Storefront:** home (search, category chips, hero, featured, offers, health essentials, trust, testimonials, contact, footer), product list with search suggestions, category/brand/prescription filters, sorting, pagination, product pages (generic name, strength, manufacturer, form, pack, price, stock, batch/expiry, warning, prescription status), cart (quantity edit, stock validation, coupon, delivery fee, loyalty redemption), checkout (Bangladesh address fields, delivery or store pickup, demo payment choice, order summary), order confirmation, tracking timeline, guest tracking, profile with saved details, order history, cancel, return request, wishlist, contact form, FAQ, shipping, returns, privacy, terms. Light/dark mode, English/বাংলা, ৳ currency, Asia/Dhaka dates.
**Prescriptions:** Rx items are clearly marked. Online Rx orders go to *Prescription Review* and cannot be processed until a pharmacist or owner approves (or rejects with a reason). At the POS, Rx items can only be sold by a pharmacist or owner with a prescription reference. Prescription documents are deliberately not stored.
**Admin:** role-based tabs and permissions (Cashier may set Pending–Packed, Inventory Manager Processing/Packed, Delivery Staff Shipped/Delivered, Owner and Pharmacist everything; forbidden deep links fall back to an allowed screen; these checks run in the browser, so they are not real access control); dashboard (KPIs, quick actions, 7-day sales chart, low-stock and expiry alerts); product CRUD with images, discount, SKU/barcode, reorder level; categories and brands; batch inventory with FEFO, expiry blocking, adjustments and write-offs; POS (barcode, discounts, change, receipt, suspend/resume, refunds, loyalty); orders with all 11 statuses, filter and invoice; prescription queue; customers (notes, block); suppliers; purchase orders with partial receiving and purchase returns; returns and refunds; expenses, cashbook, shift closing; delivery with rider; coupons; notifications; audit trail; users; business settings; reports (daily/weekly/monthly sales, profit estimate, payment methods, product and category sales, purchases, supplier balances, inventory value, low stock, near expiry, expired loss, refunds, expenses) with date range and CSV export (formula-injection safe).
**Data:** JSON export/import with validation, restore preview, confirmation, schema version 1, reset to demo data.

## Extras beyond the brief
Products CSV import (template download, validation, preview, duplicate SKU/barcode detection, skips bad rows), day-end report you can print, dashboard top sellers (30 days) and POS profit estimate, a backup reminder when data exists and no export was made in 7 days, POS keyboard shortcuts (F2 focus search, F9 complete sale).

**Installable and offline (PWA):** `manifest.webmanifest` and `sw.js` let the app be installed from Chromium-based browsers and open without a network. The service worker is network-first, so while you are online (for example with Live Server) you always get your latest edits; offline you get the last copy of each page you visited. Data stays in LocalStorage either way. If you ever see a stale page during development, unregister the worker in your browser's developer tools (Application → Service Workers).
**Stocktake:** Admin → Stocktake: print a count sheet, enter counted quantities per batch, see live variances, apply corrections (shortages are logged as stock loss at cost; expired batches cannot be increased).
**Near-expiry markdown ideas:** Admin → Alerts lists products with batches expiring within 30 days and sets a 20% discount in one click.

**Traceability and daily use:** every order status change is recorded automatically (what, when, by whom: Customer, Owner, Pharmacist ...) and shown under Orders → History; sidebar badges count waiting prescriptions, pending orders, alerts and unread notifications; notifications can be marked read one by one; purchase orders have a print view; first-time visitors get the dark theme and Bangla if their device prefers them (saved choices always win).

**Storefront refresh (v17):** Shop has a result count, removable filter chips with Clear all, an In stock only switch, a Biggest-discount sort and a helpful empty state. Wishlist has a header count, Add all in-stock to cart, Clear wishlist and out-of-stock notes. Orders is newest-first with summary cards, status filter and search, timestamps on the timeline, expandable order details, Order again, Return request and a printable customer invoice. Help has a searchable FAQ in groups, section shortcuts and a Still need help card. Contact has topic, optional order number, inline validation with a character counter, a reference number on success (stored with a staff notification), and visit/hours details (fictional). The footer is a four-column layout with shop and help links (Help links jump to the right section), tel link, hours, Back to top and a staff login link.

**Color palettes:** four palettes, each with a light and a dark set: **Forest & Gold** (default; deep green, warm cream, gold), **Teal & Amber** (the earlier look), **Ocean & Coral** (blue with a coral accent) and **Plum & Sage**. Change them with the 🎨 button in the header (cycles), the *Colors* picker in the storefront footer, or Admin → Settings. The choice is remembered per browser; the browser's address-bar color and the generated product placeholder images follow it. All palettes are defined as CSS variables at the top of `assets/css/styles.css`, so a new palette is one block of ~20 variables. Every palette passed an axe-core contrast audit (WCAG 2 AA) in light and dark mode on the main storefront and admin pages.

**Shop name:** the site is branded *Shagar Medical Store* (header, footer, page titles, receipts, invoices, admin sidebar, manifest, logo). Change the name, logo text, address, phone and receipt footer any time in Admin → Settings; the demo email, phone and opening hours shown on the Contact page are fictional and should be replaced before real use.

**Admin power tools (v20):** a global search in the top bar (also Ctrl+K) that finds orders, products, customers and batches and opens the right screen already filtered (it only shows areas the signed-in role may open); a Products screen with search, category, type and low-stock filters plus a Bulk price change tool (±50–100%, previewed, confirmed and audited); every table has sortable column headers and a Show more button after 25 rows; **Ledger & recall** with a filterable stock ledger, the audit trail (both exportable to CSV) and a **batch recall** lookup that lists every online order and POS sale that received units from a batch, printable (online orders placed from now on carry their order number in the stock log; older ones show as "order"); a **Pick list** per order naming the exact batches to pull; dashboard period comparison (7 or 30 days, change vs the previous period, average basket); automatic logout after inactivity (Settings, default 30 minutes, 0 = off); and a Roles and permissions table in Users. Roles and logout are enforced in the browser only and are not real security.

## New in 1.3.0 (add-ons; nothing existing was removed)
**Storefront:** *Compare* (⚖ on every product card, up to 3 products side by side with price per unit; products with the same generic name get an "ask the pharmacist" note), *Recently viewed* (home and product pages), *Share* and *Ask the pharmacist on WhatsApp* on product pages (uses the shop phone number from Settings), and a **Health** page (`#/health`, `health.html`): BMI calculator (Asian cut-offs), a rule-of-thumb daily water guide, medicine reminders (time, note, "taken" tick; they fire as an on-screen message and, if allowed, a browser notification, **only while the site is open**) and general habit tips. All of this is saved in the browser only (`mc_cmp`, `mc_recent`, `mc_rem`) and is general information, not medical advice.
**Admin:** *Insights* (Owner): sales by hour (Dhaka time) and weekday, stock cover and suggested order for 30 days from recent sales speed, dead stock, ABC analysis, top customers, near-expiry/expired stock value at cost. *Refill follow-ups* (Owner, Pharmacist): customers who bought an item 25-45 days ago (adjustable) and have not bought it again; call links; "contacted" marks are saved in this browser only; nothing is sent automatically. *Shelf labels* (Owner, Inventory Manager): print name, price, optional next expiry and a Code 128 barcode (product barcode, or SKU when empty); scan one printed label before printing a full sheet.
Implementation: `assets/js/extras.js` wraps the storefront views and cards; `assets/js/admin-extras.js` registers the three screens, and `admin-loader.js` loads it before `admin.js` (which gained one line to register them). Tests: `tests/extras.py` (demo mode, port 8765) and `tests/server_extras.py` (real server, in `run_server_tests.sh`).

## New in 1.4.0
**Admin:** *Expiry planner* (Owner, Pharmacist, Inventory Manager), *Margin analysis* and *Supplier orders* (Owner, Inventory Manager; margins need cost prices, which other roles never receive), *Price list* (all four roles that sell or stock: print or CSV). *Supplier orders* only prepares text per supplier (supplier = the supplier of the product's latest batch; quantity aims for twice the reorder level). The Dashboard gains *Today at a glance* with a copy-able summary and a daily sales target (saved in this browser only).
**Storefront:** an *Open now / Closed now* badge in the header (default hours 9:00-22:00 Dhaka time; add `openFrom` and `openTo` to the settings to change them) and **Copy cart link**: the link `#/sharecart/P1.2~P2.1` lists the items for whoever opens it and lets them add them to their own cart (never above stock; prescription items are still reviewed at checkout).

## New in 1.5.0 (admin and staff login)
Login page: remember-username option, display buttons, Bangla labels. After sign-in, staff see a notice if this sign-in came from a different address than the last one (it is also logged as *Sign-in from a new address* in the security log) or if the password is 90 or more days old. The Owner's Users screen shows a staff security overview, and My account can suggest a strong password (made in the browser). Server console: `python3 server/server.py --list-staff` lists accounts, roles, two-step status, lock status and password age. Notices are advice only: nothing is blocked or forced, and the "different address" check compares the last sign-in address, so phones moving between Wi-Fi and mobile data will trigger it harmlessly.

## New in 1.6.0
**Admin:** *Customer lookup* (personal data: shown only to Owner, Pharmacist and Cashier; use it only to serve the customer). **Storefront:** voice search (needs microphone permission; the browser's speech service may process the audio, so it is optional and only appears where the browser offers it) and text size buttons (A+ / A−, saved in the browser).

## New in 1.7.0: sign-in policy (Owner, server mode)
Settings > *Sign-in policy*: (1) require two-step login for Owner, Owner and Pharmacists, or everyone; (2) allow staff to sign in only between two hours of the day in Dhaka time (the Owner is exempt); (3) limit how many devices one person can be signed in on; (4) ask for a new password after a set number of days. Everything is off until you turn it on, and you must have two-step login on yourself before you can require it for others. Test every rule with a spare account first. If someone is locked out, the server console still works: `--reset-password`, `--disable-2fa`, `--unlock`, `--list-staff`. Existing sessions are not cut by the hours rule; it is checked when someone signs in.

## New in 1.8.0: login page
The staff login page now shows a greeting, a clearer layout on phones, a busy state while signing in, a short wait after too many attempts, helpful two-step code entry (automatic submit at 6 digits), a "Not you?" link for remembered usernames, an offline notice and sign-in tips; the demo login describes each role. All text is available in Bangla. The admin panel's own global search (Ctrl+K) is unchanged.

## Real login (1.9.0)
Real accounts, passwords, lockout, two-step login and sessions only exist when the **server** runs: double-click `start-server.bat` (Windows) or run `./start-server.sh` (Mac/Linux). It needs Python 3 and opens `http://localhost:8000/admin/login.html`. On the first run the page asks for the setup code shown in the server window, then your name, username and password. Static hosting (GitHub Pages, opening the files directly) can only offer the **demo** login, which anyone can use and which protects nothing. For a public shop, put the server behind HTTPS (see `deploy/`). Lost access: `--reset-password`, `--disable-2fa`, `--unlock`, `--list-staff` on the server.

## New in 2.0.0: Shop, Wishlist, Orders, Help, Contact, Health
See CHANGELOG. Health notes (blood pressure, sugar, water) are general information for adults and are not medical advice or a diagnosis; readings are stored only in the visitor's browser (`mc_hlog`, `mc_water`, `mc_rem`). The wishlist price-change note compares with the price seen when the item first appeared in the saved list on this device.

## Real server mode (works like a real site)

The project runs in **two modes** with the same pages:

| | Demo mode | **Real server mode** |
|---|---|---|
| Start with | any static server (Live Server) | `python3 server/server.py` |
| Data lives in | each browser's LocalStorage | a shared **SQLite database** on the server |
| Staff login | demo code `demo` (not security) | **real accounts**, hashed passwords, server sessions |
| Customer orders | stay in that browser | reach the pharmacy panel on any device |
| Prices, stock, totals | computed in the browser | **computed and checked on the server** |

### Start it
```
python3 server/server.py                      # http://127.0.0.1:8000/
python3 server/server.py --port 8080 --no-demo   # empty shop, no demo products
```
Python 3.9+ only; nothing to install. On the first run it creates `server/data/shop.db` and prints the first staff login (`owner` plus a random password, shown once). You must choose your own password at first login. Staff log in at `/admin/login.html`; the Owner creates other accounts under **Users** (each must change its temporary password).
Options: `--host`, `--port`, `--data DIR`, `--owner-password`, `--secure-cookies`, `--trust-proxy`, `--verbose` (or env `SHAGAR_HOST`, `SHAGAR_PORT`, `SHAGAR_DATA`, `SHAGAR_OWNER_PASSWORD`).

### What the server really does
- **Accounts and sessions:** PBKDF2-SHA256 hashed passwords, random session tokens stored hashed, HttpOnly + SameSite=Strict cookie, idle and absolute session timeouts (with a "Still there?" warning a minute before sign-out), account lock after 5 wrong attempts, rate limits, password rules (10+ characters, at least two kinds of characters, no common passwords, must not contain the username) with a strength meter, forced change of temporary passwords, deactivation ends sessions immediately.
- **Two-step login (TOTP):** each staff member can turn on a 6-digit authenticator code (Google/Microsoft Authenticator, Authy…) under **My account**. Codes cannot be replayed, wrong codes count toward the lockout, and 10 one-time recovery codes are issued. Setup uses the typed setup key (no QR code, so no extra library is needed).
- **My account:** change password, set up two-step login, see every signed-in device (browser, address, last active), sign out one or all other devices, and see recent activity on your own account (including your previous sign-in).
- **Staff management (Owner):** create staff, edit name/role, reset a password, unlock, reset a lost two-step, sign someone out everywhere, deactivate; the last active Owner is protected.
- **Security log (Owner):** sign-ins, failures, lockouts, password and role changes, two-step changes, recovery-code use and console resets, with filters and CSV export. Passwords and codes are never written to it.
- **Lost access:** on the server run `python3 server/server.py --reset-password owner` (new temporary password), `--disable-2fa USER` or `--unlock USER`.
- **Login page:** remembers where you were going, shows/hides the password, warns about Caps Lock, asks for the authenticator code only when needed, and never says whether the username or the password was wrong.
- **Customers:** the catalog never exposes cost prices; checkout sends only item ids and quantities; the server recomputes prices, discounts, coupon, delivery fee, deducts stock by first-expiry-first-out inside a database transaction (two shoppers cannot oversell the last units), enforces the prescription rules and numbers the order. Orders are looked up only with order number + mobile number; customers can cancel (stock returns) or request a return.
- **Staff changes are validated on the server:** each role may write only its own data sets; order totals/items/addresses cannot be edited by anyone; prescription orders can only be released by a pharmacist or owner; stock may change only together with a matching stock-log entry; POS sales must use the real current prices and deduct stock; sales, logs, audit and refunds are append-only; invalid prices/dates/quantities are refused; stale edits from another device are refused (409) instead of overwriting.
- **Each role is sent only the data it needs:** delivery staff receive just orders; a cashier gets products, stock, orders, sales and the cashbook but no supplier, purchase, customer-note, audit or message data; a pharmacist does not get messages or customer notes. **Purchase costs are hidden** from everyone except the Owner and the Inventory Manager (the server fills in the cost of each sold item itself, so cashiers and pharmacists never need to see or send it).
- **Backups and monitoring:** the server makes a consistent copy of the database every day by itself (the latest 14 are kept in `server/data/backups`), the Owner can back up now (latest 30 kept) and download copies from Admin -> Data; every backup is integrity-checked. `GET /api/health` is a simple check for monitoring tools; errors go to `server/data/server.log` (rotated).
- **Speed and hygiene:** pages and scripts are compressed (gzip) and revalidated with ETags, unknown addresses show a friendly 404 page, `robots.txt` keeps search engines out of `/admin/` and `/api/`, admin pages are marked noindex, and the `deploy/` folder is never served.
- **Shared and live:** the admin panel refreshes from the server every 15 seconds, so an order placed on a customer's phone appears on the counter computer.
- **Files:** the server serves only the website files (never `server/`, `tests/`, the database or `.md/.py` files) and sends security headers (CSP, nosniff, frame denial).
- **Backups:** Admin -> Data -> Export JSON downloads everything; Import restores it (the server first keeps a copy of the old database). You can also copy `server/data/shop.db` while the server is stopped.

### Put it on the internet safely
1. Run the server on a small VPS or office PC, bound to `127.0.0.1`.
2. Put **HTTPS** in front (Caddy or Nginx reverse proxy with a free Let's Encrypt certificate), and start the server with `--secure-cookies --trust-proxy`.
3. Open only ports 80/443; keep the operating system updated; make regular copies of `server/data/shop.db`.
4. Replace the demo address, phone, email and opening hours with the real ones (Admin -> Settings and the Contact page text).

### Store controls and customer features (both modes unless noted)
- **Store controls (Admin → Settings):** pause online ordering (for holidays; the server refuses orders and the shop shows a banner), a notice banner (e.g. Eid hours), a minimum order, and free home delivery above an amount. The server applies these rules itself in real server mode.
- **Delivery time preference:** customers choose a time window; it is saved on the order and printed on pick lists.
- **Other brands with the same ingredient:** product pages list products with the same generic name (price, strength, availability) with a reminder to ask the pharmacist before switching. This is information, not a substitution recommendation.
- **"Tell me when it is back":** for out-of-stock items customers leave a mobile number; staff see the list on the Alerts screen ("Back in stock - call them") and mark people as contacted. There is **no automatic SMS**: a person phones them.
- **Prescription image upload (real server mode only):** customers may attach a JPG/PNG/WebP (max 3 MB) with a consent tick box. The server checks the real file type, stores it outside the website folder under a random name, shows it only to a signed-in Pharmacist or Owner (every view is written to the security log, never cached), and **deletes it automatically after the retention period** (default 30 days, set under Store controls; `python3 server/server.py --purge-prescriptions` runs the clean-up by hand). Images are not virus-scanned. Check your local rules on storing prescription data and keep the privacy text accurate.
- **Admin time-savers:** select several orders and set their status together (prescription orders and closed orders are skipped and you are told), print pick lists for the selected orders in one go, and create purchase orders for every low-stock product with one click.

### Privacy tools, security policy and load check
- **Customer data requests (Owner):** under Customers, *Export data* downloads everything the shop holds for a mobile number (orders, messages, waiting-list entries, counter sales, loyalty, notes); *Erase data* (type ERASE) replaces the name, phone, address, doctor details and messages with placeholders, deletes any prescription image, removes waiting-list and loyalty entries and scrubs notification text. Order totals and items stay for the accounts. Both actions are written to the security log without storing the full number. Check with your own legal advice what you must keep and for how long.
- **Strict Content-Security-Policy:** pages contain no inline scripts any more, so the server sends `script-src 'self'`. A test visits every page and screen and fails on any policy violation.
- **Load check** (`tests/load_check.py`, one machine, localhost, Python's built-in threaded server): 400 catalog requests with 20 shoppers at once took 1.3 s (95% under 25 ms); 300 compressed home-page requests, 1.2 s; 60 orders for one product from 12 customers at once, all accepted in 1.1 s while the staff panel kept refreshing, with stock falling by exactly 60 and every order's stock-log entries present; 90 customers racing for the last 51 units: exactly 51 won, 39 were told it is out of stock, stock ended at 0. These numbers show the logic holds under simultaneous use; they do not say how fast the site is for visitors over the internet or how it behaves for days on end.

### Deployment files (not tested on a real server)
`deploy/` contains a systemd unit, a Caddyfile and an Nginx config plus short step-by-step notes (`deploy/README.txt`). They are templates: change the domain and paths, and test them on your own server.

### What is still NOT real (needs outside services or your decisions)
- **Payments:** only cash on delivery works; the bKash choice is a label. A real gateway needs a merchant account and its API.
- **SMS / email / push notifications:** not connected (staff see in-app notifications only).
- **Password-reset by email/SMS:** not available (no mail/SMS service); the Owner resets staff passwords, and the server console resets the Owner.
- **Customer accounts and phone verification:** customers are identified by order number + mobile number. Because the phone is not verified (no SMS OTP), **loyalty-point redemption is switched off online** and works only at the counter.
- **Single-machine database:** SQLite on one server is fine for a shop; it is not a clustered system.
- **Read access follows screens, not individual fields:** a role that can open the Orders screen sees all orders (including customer names and addresses); customer notes, messages, suppliers and costs are withheld as described above.
- The pages use one blocking request at start-up (kept for simplicity). Scripts may only come from the site itself (strict Content-Security-Policy, no inline scripts); inline styles are still allowed.
- Legal/regulatory duties for selling medicines (licences, prescription records, controlled drugs) are yours to confirm.

## Data, backup and reset
Everything is stored under the LocalStorage key `mc_db`. Admin → Data: **Export JSON** (backup), **Import JSON** (validated, with a preview and confirmation), **Reset to demo data** (confirmation). Clearing browser data also removes the demo data.

## Deploy as a static site
Upload the whole folder to any static host (GitHub Pages, Netlify, Cloudflare Pages, an Nginx/Apache folder). There is nothing to build; keep the folder structure. Remember that each visitor gets their own browser-local data and the admin "login" offers no real protection, so only deploy it as a demo.

## Limitations
- Demo-only login (shared code, role kept in sessionStorage); anyone can open the admin pages.
- LocalStorage: single browser, no multi-user sync, size limit (uploaded product images are shrunk to ~240 px), data can be cleared by the user.
- Payments, SMS/email, shipping and barcode hardware are **not** integrated (payment choice is a label; barcodes are typed or pasted; notifications are in-app only).
- Product data and free text are not translated into Bangla; only interface text and the 12 demo product names are.
- Only Chromium was available for browser testing; see TEST-CHECKLIST.md.

## Future backend recommendations
Use a server and database (e.g. PostgreSQL) with: real authentication (hashed credentials, MFA for staff), server-side role checks, transactional inventory (batch locks, FEFO in a transaction), a payment gateway (bKash/Nagad/cards via tokenised flow), SMS/email providers, protected prescription storage with access logs and retention rules, audit logs, scheduled backups, and a regulator-aware workflow for controlled medicines.

## Tests (optional developer tools)
`tests/` contains Playwright scripts (`server_api.py`, `server_e2e.py` and `server_admin_flows.py`, `server_login_ui.py`, `server_roles_ui.py`, `server_features.py`, `server_features_ui.py`, `csp_sweep.py`, `load_check.py` and `server_ratelimit.py` for the real server, run with `sh tests/run_server_tests.sh`; `e2e.py`, `e2e2.py`, `loyalty.py`, `audit2.py`, `roles.py`, `v14.py`, `v15.py`, `v16.py`, `v17.py`, `v18.py`, `v19.py`, `v20.py`, `axe_palettes.py`, `sweep.py`, `axe_audit.py`, `print_receipt.py`) and a jsdom logic suite (`logic-jsdom.js`). Serve the folder on port 8765 and run them with Python (`pip install playwright`) or Node. They are not needed to run the app.
