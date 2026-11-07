# Changelog

## 2.2.0 (quality pass: accessibility, phones, real-server checks)
- Accessibility audit with axe-core (light and dark, storefront and admin, WCAG 2.1 A/AA plus best practice): fixed the low-contrast "Admin" link in the header, three buttons whose accessible name did not contain their visible text (language toggle, Admin link, "+ 1 cup"). The audit now reports 0 problems.
- Phones (390 px): checked 11 storefront pages and 17 admin screens. Found and fixed one sideways-scroll problem that was already in the original project (the admin Products table); admin tables on phones now scroll inside themselves.
- Orders: the "Need help with this order?" button now also appears on an order found with "Track an order" (the normal case for customers without a saved name), not only on the saved-orders list.
- New tests: `tests/a11y_audit.py` (needs `npm i axe-core` in /tmp/axe), `tests/mobile_audit.py`, `tests/server_storefront.py` (the updated storefront sections against the real server: order, tracking, contact message, help, health, wishlist).
- Version 2.2.0, service worker mc-v12.

## 2.1.0 (storefront sections, second round)
- **Shop:** price per unit on cards (for example ৳2.50 / tab), recent-search chips, barcode scan (📷, only in browsers that support camera barcode reading; matches products that have a barcode or SKU saved), and "Same ingredient, other brands" on the product page with price per unit and the saving.
- **Wishlist:** sort (saved order, name, price, discount, in stock first), a private note per item, copy the list as text, and send it to the pharmacy on WhatsApp.
- **Orders:** "Time to reorder?" suggestions for items bought 25+ days ago and a six-month spending chart, both built from the customer's own orders.
- **Help:** new "Know your medicine" group (Rx, generic vs brand, reading a pack, forms, storage, leftovers, antibiotics); the FAQ search covers it.
- **Contact:** call-back time buttons and a picker for recent orders.
- **Health:** dose times planner (turns "every 8 hours" into reminders) and supply calculator (how long a supply lasts, with a calendar file to remind you to reorder).
- Fix: on a direct visit to Help or FAQ (`#/info`, `faq.html`) the 2.0.0 additions were not drawn because the page was not redrawn after the add-ons loaded; it is now redrawn and keeps the highlighted section.
- Global `[hidden]` rule so buttons hidden by the code are really hidden. Version 2.1.0, service worker mc-v11, new test `tests/sections2.py`.

## 2.0.0 (storefront sections)
- **Shop:** Grid / List view (remembered), Quick view (👁 on every card: details, quantity, add to cart), "Did you mean" suggestions and a WhatsApp question when a search finds nothing, back-to-top button.
- **Wishlist:** total for what is in stock, Share wishlist link (`#/sharewish/...`, opened by anyone and saved to their own list), price-drop / price-change notes since the item was saved, popular picks when the list is empty.
- **Orders:** "Need help with this order?" opens the contact form with the order number filled in; a guide to what each status means. (The existing totals, filters, search, invoices and returns are unchanged.)
- **Help:** emergency box (999), a new "Using this website" FAQ group that the FAQ search also filters, print button.
- **Contact:** open/closed status, WhatsApp, copy phone and map link next to the address; the form is prefilled from saved details, remembers an unsent message (cleared when sent) and receives the order number from Orders.
- **Health:** health log for blood pressure, blood sugar and weight with general-range notes, trend chart and CSV export; water tracker with a daily goal; printable medicine schedule; emergency number at the top. Everything stays on the device.
- The header "Open now" badge now follows the Friday 15:00 opening time shown on the Contact page (unless the shop sets its own hours).
- New `assets/js/extras2.js`; service worker mc-v10; version 2.0.0; new test `tests/sections.py`.

## 1.9.0 (real login, navbar)
- **Real login by default.** Starting the server on a fresh database no longer creates a default `owner` with a random password in the console. The login page shows a first-run form instead: you type a one-time **setup code** (printed in the server window, so only someone with access to the server can use it), your name, a username and a password (same strength rules as everywhere), and you are signed in as Owner. Setup closes for good once the Owner exists. Use `--owner-password` (or `SHAGAR_OWNER_PASSWORD`) or `--random-owner-password` for unattended installs.
- `start-server.bat` (Windows) and `start-server.sh` (Mac/Linux) start the real server and open the login page. The demo login (static files, demo code) now says clearly that it protects nothing.
- Storefront navbar: hamburger menu on phones (Esc and link-click close it), current page highlighted, shadow on scroll, "/" focuses search, one compact **Aa** text-size button, quieter "Admin" link; smaller search box so the header wraps less.
- Admin top bar: current screen name, Dhaka clock, online/offline indicator, signed-in name.
- Fix: the 1.3.0 Insights charts reused the CSS class `bars`, which the dashboard chart also uses, and could distort it; renamed to `hbars`.
- Version 1.9.0, service worker mc-v9, new tests `tests/server_setup.py` and `tests/navbar.py`.

## 1.8.0 (login page)
- Staff login page redesigned: brand header with a time-of-day greeting (Dhaka time), clearer layout on phones, "Signing in…" state that blocks double submits, 15-second cool-down after "too many attempts", wrong password clears and flags the field, two-step code field with a hint and automatic submit at 6 digits, "Not you? Use a different account" for a remembered username, offline notice, sign-in tips, and (demo mode) a short description of each role. English and Bangla.
- Correction to 1.6.0: the admin panel already had a global search on Ctrl+K. The extra "Quick find" added in 1.6.0 also grabbed Ctrl+K and duplicated it, so it was removed again. Customer lookup stays.
- Version 1.8.0, service worker mc-v8, new test `tests/server_login_page.py`.

## 1.7.0 (sign-in policy)
- Owner can turn on optional sign-in rules in Settings > Sign-in policy (server mode; **all off by default**): require two-step login for Owner / Owner and Pharmacists / everyone; allow non-Owner sign-in only within set hours (Dhaka time, overnight windows supported, Owner never blocked); limit devices signed in at once per person (older ones are signed out); ask for a new password after 30 to 365 days.
- Safety: two-step can only be required by an Owner who has already turned it on for themself. Staff who are required but not enrolled can open only My account (with a notice) until they finish; the server refuses their data requests until then. Blocked-by-hours attempts are logged and do not count as wrong passwords. The public shop never sees these settings.
- New security-log events: blocked outside hours, password expired by policy, older devices signed out. Version 1.7.0, service worker mc-v7, new test `tests/server_policy.py`.

## 1.6.0
- Admin: **Customer lookup** screen (Owner, Pharmacist, Cashier): one customer's whole history by phone or name (orders and counter sales, total spent, average basket, most-bought items, call link).
- Storefront: **voice search** (🎤, shown only in browsers that support it; Bangla or English) and **larger/smaller text** buttons (remembered; the admin panel uses the same size).
- Version 1.6.0, service worker cache mc-v6, new page `admin/customer360.html`, tests extended; cashier now sees 6 screens, Pharmacist 11, Owner 29 (roles tests updated).

## 1.5.0 (admin and staff login)
- Login page: Remember-my-username choice (unchecked removes it), display buttons (colors, theme, language) and Bangla labels, sensible autofocus; demo mode remembers the last user.
- Server: password age is tracked (`pw_changed`, added automatically to existing databases); sign-ins from a different address than last time are written to the security log (`login_new_address`) and reported to the person at sign-in; `/api/account` and `/api/staff` report password age and open sessions; new console command `python3 server/server.py --list-staff` (no password data shown).
- Admin: after signing in, dismissible notices for a new sign-in address and for a password 90+ days old; Users screen (Owner) gains a **Staff security overview** (two-step login coverage, old passwords, never signed in, locked, sessions, last address); My account gains a **strong password suggestion** made in the browser (never sent or saved).
- Nothing about passwords, lockout, two-step login or sessions was weakened or changed in behavior. Version 1.5.0, service worker cache mc-v5, new test `tests/server_login_v14.py`; the cashier tab count in `server_e2e.py` now includes Price list.

## 1.4.0
- Admin: **Expiry planner** (stock by expiry month, expired and expiring batches, CSV), **Margin analysis** (margin per product, below-cost and low-margin flags, stock value and potential profit, CSV; Owner and Inventory Manager), **Supplier orders** (ready-to-edit order messages for low-stock items per supplier, copy or open WhatsApp; sends nothing by itself) and a printable **Price list** (also CSV).
- Dashboard: "Today at a glance" card with a copy-able day summary and a daily sales target with progress bar (target saved in this browser).
- Storefront: open/closed badge (Dhaka time; hours default 9-22, or `openFrom` / `openTo` in settings) and **share your cart by link** (a shared link opens a list the visitor can add to their own cart, limited to stock).
- New pages `admin/pricelist|expiry|margins|reorder.html`; service worker cache `mc-v4`; server version 1.4.0; tests extended (`extras.py`, `server_extras.py`, `csp_sweep.py`, `roles.py`).

## 1.3.0
- Storefront: product compare (up to 3, price per unit, same-ingredient note), recently viewed products, share link and "ask the pharmacist on WhatsApp" on product pages, new Health tools page (BMI with Asian cut-offs, daily water guide, medicine reminders with browser notifications, healthy-habit tips).
- Admin: **Insights** (Owner: sales by hour and weekday, stock-cover forecast with suggested order quantity, dead stock, ABC analysis, top customers, near-expiry and expired stock value, CSV export), **Refill follow-ups** (Owner, Pharmacist: customers who may be due to buy again, with call links) and **Shelf labels** (Owner, Inventory Manager: printable labels with real Code 128 barcodes).
- New files: `assets/js/extras.js`, `assets/js/admin-extras.js`, `health.html`, `compare.html`, `admin/insights.html`, `admin/refill.html`, `admin/labels.html`. Existing screens and data are unchanged.
- Service worker cache bumped to `mc-v3`; server version 1.3.0; new tests `tests/extras.py` and `tests/server_extras.py`; roles test expectations updated for the new tabs.

## 1.2.0
- Strict Content-Security-Policy: no inline scripts anywhere (page settings moved to meta tags, the admin loader and login page are external files).
- Customer data export and erasure for privacy requests (Owner).
- Server version number (`--version`, `/api/health`); load and concurrency check script.

## 1.1.0
- Store controls (pause online orders, notice banner, minimum order, free-delivery level, delivery time choice).
- Other brands with the same ingredient on product pages; "tell me when it is back" waiting list.
- Prescription image upload with consent, private storage, pharmacist-only viewing and automatic deletion.
- Bulk order status change, combined pick lists, one-click purchase orders for low stock.
- Role-limited data (costs hidden from most roles), automatic and manual database backups, health check, gzip/ETag, 404 page, robots.txt, deployment templates.
- Staff login upgrades: two-step login (TOTP) with recovery codes, My account (devices, activity), security log, staff management, password rules, idle warning, server-console recovery commands.

## 1.0.0
- Real server mode (Python + SQLite): shared database, hashed-password staff accounts with sessions, server-side pricing and stock deduction, server-side role checks.
- Browser-only demo mode with the full storefront and admin panel (LocalStorage).
