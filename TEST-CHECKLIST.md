# Test checklist

Legend: **[auto]** passed in automated Chromium (Playwright) or jsdom runs during development; **[manual]** not run by me, please verify; **[not run]** could not be run in this environment (only Chromium was available; no real phone or printer).

## Navigation
- [auto] Every storefront page and all 19 admin tabs load at 360, 768 and 1280 px with no console errors and no horizontal overflow
- [auto] Admin deep links (`admin/index.html#rx`) and real pages (`admin/pos.html`) open the right screen
- [manual] Keyboard-only navigation through header, filters, cart and checkout
## CRUD
- [auto] Product add (full form with image), edit with SKU/barcode uniqueness, delete; supplier edit and guarded delete; category/brand rename; user add/deactivate; coupon add/disable/delete
## Search, filter, sort
- [auto] Search (header + suggestions with generic names), brand filter, Rx filter, price filter, category chips, sorting, pagination
## Cart, coupon, checkout
- [auto] Quantity above stock rejected; SAVE10 needs ৳500+; coupon survives moving to checkout.html; totals and order summary; store pickup (no fee/address); Bangladesh address validation; loyalty redemption limits
## POS
- [auto] Barcode entry, Rx rule (cashier blocked, pharmacist allowed), cash shortfall blocked, receipt, suspend/resume, refund, loyalty
## Inventory and FEFO
- [auto] Expired batch excluded from stock and sales; earliest expiry consumed first; oversell and negative stock blocked; adjustments and write-offs logged; low-stock and expiry alerts
## Purchasing
- [auto] Stock added only when received; partial receiving creates separate batches; purchase return limits; supplier balance follows received quantity
## Orders, returns, refunds
- [auto] Rx order → review → approve/reject (restock and reason); cancel restores stock and points; return request needs a reason; refund records linked to order or sale
## Reports and CSV
- [auto] All report tables render; date range filter; CSV downloads (orders)
- [manual] Open exported CSVs in Excel/Sheets and confirm formulas such as `=1+1` appear as text
## Theme, language, persistence
- [auto] Bangla mode shows Bangla labels and product names; payment values stay English
- [manual] Theme and language persist after closing and reopening the browser
## Import / export / reset
- [auto] Bad backups rejected (wrong version, missing lists, negative stock); valid backup accepted
- [manual] Export, reset, then import the exported file and compare data
## Accessibility and print
- [auto] axe-core (WCAG 2 A/AA and best practices): 0 violations, light and dark; receipt prints alone (PDF checked)
- [manual] Screen-reader pass; real printer
## Responsive and visual
- [auto] Screenshots reviewed at 390 px and 1280 px (store, admin, mobile menu, dark mode)
- [not run] Firefox, Safari, real phone, real tablet
## Roles
- [auto] Each role sees only its tabs; forbidden deep links fall back; Cashier and Delivery Staff cannot set statuses outside their list (tests/roles.py)
- [manual] Confirm the permissions match how your shop actually works
## Safety
- [auto] No `innerHTML`, `eval` or `document.write` in the source; full-storage and blocked-storage handled with a message
- [auto] After splitting core.js into utils/i18n/storage and styles.css into styles/admin/responsive: all browser suites (audit2, roles, loyalty, e2e, e2e2, sweep, axe) and the jsdom logic suite pass
- [auto] CSV import (valid rows only, duplicates and bad prices flagged), template download, backup reminder, day-end report, top sellers, POS F2/F9 (tests/v14.py); CSV export escapes leading = + - @
- [manual] Import a real product list from Excel saved as CSV (UTF-8) and check Bangla text
- [auto] Offline: storefront and admin open with the network switched off after one online visit; stocktake variance, shortage expense, negative count rejection; near-expiry markdown (tests/v15.py)
- [manual] Install the app from the browser menu on a phone or desktop and open it offline; run a real stocktake with a printed sheet
- [auto] Device-default theme/language, sidebar badges, per-notification read, status history with actor, PO print (tests/v16.py)
- [manual] Print a purchase order and an order history on paper
- [auto] Shop filters/chips/empty state/in-stock, wishlist count and bulk add, orders filters/details/invoice, help search, contact validation and reference, footer links and responsive stacking (tests/v17.py); axe 0 violations after the refresh
- [manual] Read the Help and Contact wording with a pharmacist; replace the fictional email, phone and hours with real ones in Settings/Help before any real use
- [auto] Palettes: default, cycle button, footer and admin pickers, persistence, invalid value fallback, theme-color meta and placeholder images follow the palette (tests/v18.py); axe contrast audit 0 violations for all four palettes in light and dark (tests/axe_palettes.py)
- [manual] Look at your brand colors and pick or edit a palette; check printed receipts in your chosen palette
- [auto] Shop name: page titles, header, footer, admin sidebar, login, receipts, manifest; no trace of the old name on storefront pages; older saved data migrates, an owner-chosen name is never overwritten; long name fits a 360 px phone (tests/v19.py)
- [manual] Check the Bangla spelling you want for the shop name if you need it on signs or receipts (the site shows the English name in both languages)
- [auto] Admin search (Ctrl+K, role-aware), product filters, bulk price change, sortable tables and Show more, stock ledger/audit CSV, batch recall, pick list, dashboard period, idle logout, permissions table (tests/v20.py); axe 0 violations on the admin tabs
- [manual] Try a real recall exercise with a batch number from your shelf; decide the right idle-logout time for your counter

## Real server mode
- [auto] 59 API checks (tests/server_api.py): server-side pricing, stock deduction and no overselling under concurrent orders, coupon and prescription rules, customer lookup/cancel, password hashing flow, forced password change, lockout, role permissions, tamper attempts (prices, order totals, stock without log, wrong sale prices), stale-data refusal, logout/deactivation, file protection, security headers
- [auto] 27 real-browser checks (tests/server_e2e.py): customer order reaches the admin on another device, prescription approval seen by the customer, status changes persist, two staff devices stay in sync, staff creation with forced password change, cashier POS sale accepted, tampering from the browser refused (403), tracking from any device, contact messages, logout
- [auto] 37 further browser checks (tests/server_admin_flows.py) push every other admin screen through the server's validation: purchase orders (receive, purchase return), suppliers, expired-stock write-off, damaged-stock adjustment, direct batch receiving, stocktake, POS sale and refund, a full order life-cycle (confirm, process, pack, rider, ship, deliver, return, restock, refund) with history, expenses, shift closing, product add/edit/delete, category rename, customer edit and block (blocked customers cannot order), settings, coupons, ledger, demo reset disabled, data intact after reload
- [auto] 29 further API checks inside tests/server_api.py for the login system: password rules, two-step setup/enable/login, replay and single-use protection, recovery codes, device list and sign-out, security log contents (no passwords), role-change and unlock/reset flows, lockout, last-owner protection, server-console password reset; 2 rate-limit checks (tests/server_ratelimit.py)
- [auto] 32 real-browser checks (tests/server_login_ui.py): redirect back after login, show/hide password, Caps Lock warning, forgot-password help, remembered username, strength meter, password change, two-step setup with recovery codes, login with code and with a recovery code, device list and "sign out all other devices", staff edit/unlock/reset two-step, security log and CSV, idle warning; axe contrast/accessibility audit of login, My account, Users and Security log in light and dark: 0 violations
- [auto] 25 further API checks (tests/server_api.py): role-limited data (delivery gets only orders and settings; cashier gets no supplier/purchase/note/audit data), costs hidden from cashier and pharmacist yet preserved on the server, server-filled sale costs, polling with limited views, backups (create, list, download as a real SQLite file, owner-only, no path tricks, automatic backup), health check, gzip, ETag/304, friendly 404, robots.txt, deploy files not served
- [auto] 14 real-browser checks (tests/server_roles_ui.py): delivery staff, pharmacist, cashier and inventory manager each still do their jobs with the limited data (shipping, Rx approval, POS sale, cashbook, purchasing), and cost/profit figures appear only where allowed
- [auto] 33 API checks (tests/server_features.py): delivery-time choice, minimum order, free-delivery threshold, pausing online orders and the public notice, invalid settings refused, waiting list (in-stock refused, duplicates merged, cashiers not sent it), prescription images (consent needed, real file-type check, size limit, ignored on non-prescription orders, only referenced on the order, owner/pharmacist only, never cached, view logged, not served as files) and automatic deletion after the retention period
- [auto] 22 real-browser checks (tests/server_features_ui.py) and 11 demo-mode checks (tests/v22.py): notice and paused banners, disabled checkout, free-delivery hints, delivery-time select, other-brands box, waiting-list form and staff list, prescription upload with consent and fake-image refusal, the pharmacist's image viewer, one-click purchase orders, bulk status change with prescription skipping, combined pick lists, Settings store controls; axe audit of 20 new/changed screens in light and dark: 0 violations
- [auto] 8 more API checks in tests/server_features.py (customer data export and erasure: owner only, needs the word ERASE, no trace of the number/name/waiting entry left, totals kept, old number cannot open the order, logged without the full number); 4 checks in tests/csp_sweep.py (strict policy header; no console or policy error on any of 19 storefront pages, 23 admin screens and the redirect); 8 checks in tests/load_check.py (see the README for the numbers)
- [manual] Upload a real phone photo as a prescription and open it as the pharmacist; confirm your retention period with your own legal advice
- [manual] Try two-step login with your own phone's authenticator app; test the server-console password reset on your real server
- [manual] Run behind HTTPS with --secure-cookies; test from a real phone on your network; try a failed power cut (restart the server and check orders are still there)
- [not run] Load testing, Windows/macOS server hosting, long-running (days) stability


## v1.3.0 add-ons (manual check)
- [ ] Shop: tick ⚖ on 2-3 cards, open Compare; the 4th product is refused; Clear empties it.
- [ ] Open two products, return to Shop: *Recently viewed* shows them; Clear removes them.
- [ ] Product page: Share copies/opens a link; WhatsApp link opens a chat with the product name.
- [ ] Health: BMI 170 cm / 70 kg gives 24.2; add a reminder one minute ahead and see the message; in Bangla the page title reads স্বাস্থ্য টুলস.
- [ ] Admin (Owner): Insights, Refill follow-ups, Shelf labels open; Pharmacist sees only Refill; Inventory Manager only Shelf labels; Cashier none.
- [ ] Print one shelf label and scan it with your real barcode scanner.

## v1.4.0 add-ons (manual check)
- [ ] Dashboard: set a daily target, see the progress bar, press Copy day summary and paste it somewhere.
- [ ] Expiry planner: change the window; expired batches are listed separately; CSV downloads.
- [ ] Margin analysis: a product priced below cost is flagged; Pharmacist and Cashier do not see this tab.
- [ ] Supplier orders: edit the text, Copy message, open WhatsApp for a supplier with a phone number.
- [ ] Price list: print preview groups products by category.
- [ ] Storefront: the header shows Open now / Closed now; Copy cart link opens the shared cart in a private window and adds the items.

## v1.5.0 login and staff (manual check)
- [ ] Log in with Remember unchecked, open the login page again: the username box is empty. Check it, log in, open again: pre-filled.
- [ ] Switch language on the login page: labels turn Bangla.
- [ ] Log in from a second device or network: the notice about a new address appears; the security log shows the new event.
- [ ] Owner > Users: the overview lists every account; lock, unlock and reset still work as before.
- [ ] My account: Suggest a password gives a 16-character password; Copy works.
- [ ] On the server: python3 server/server.py --list-staff prints the accounts.

## v1.6.0 (manual check)
- [ ] Admin: Ctrl+K still focuses the admin search box.
- [ ] Customer lookup: search a phone number, open the customer, check totals against Orders.
- [ ] Shop: press A+ twice, reload: size stays; open the admin: same size. Tap 🎤 and say a medicine name (Chrome/Android).

## v1.7.0 sign-in policy (manual check, on a test copy)
- [ ] Turn on your own two-step login, then Settings > Sign-in policy > require for Owner and Pharmacists. A Pharmacist without it sees only My account until set up.
- [ ] Set hours that exclude now: a Cashier cannot sign in (clear message), the Owner can. Restore the hours.
- [ ] Devices limit 1: sign in on a second device; the first one is signed out.
- [ ] Password max age 30: an account with an old password is asked to choose a new one at sign-in.
- [ ] Security log shows the new events.

## v1.8.0 login page (manual check)
- [ ] Phone-width login page: nothing is cut off, no sideways scrolling.
- [ ] Wrong password: message appears, password box is cleared and focused. Five wrong tries: the button counts down before it can be used again.
- [ ] Account with two-step: after the password, the code box appears; typing 6 digits signs in.
- [ ] Switch to Bangla: header, labels and tips are Bangla. Turn off Wi-Fi: the offline notice appears.

## v1.9.0 real login and navbar (manual check)
- [ ] Delete server/data (on a copy), start with start-server.bat/.sh: the window shows a setup code; the login page asks for it and creates the Owner.
- [ ] Open the login page from another computer before finishing setup: it needs the code; a wrong code is refused.
- [ ] Phone: the menu button opens and closes the links; the current page is highlighted; "/" focuses search on a computer.
- [ ] Admin top bar shows the screen name, the time and Online/Offline.

## v2.0.0 storefront sections (manual check)
- [ ] Shop: switch to List and back; open Quick view and add to cart; search a misspelled medicine and use a suggestion.
- [ ] Wishlist: save two items, press Share wishlist, open the link in a private window and save it there.
- [ ] Orders: press "Need help with this order": the contact form has the order number.
- [ ] Contact: the form remembers a half-written message after a reload and clears it after sending.
- [ ] Health: log a blood pressure of 150/95 (flagged), a normal one, see the chart; export the CSV; try the water tracker and the printed schedule.
- [ ] Have a pharmacist or doctor read the wording of the health ranges before showing them to real customers.

## v2.1.0 (manual check)
- [ ] Shop: search "napa", reload, tap the recent-search chip; on a phone with Chrome tap 📷 and scan a pack whose barcode is saved.
- [ ] Product page of a medicine that has another brand: the "Same ingredient, other brands" box shows the cheaper pack per unit.
- [ ] Wishlist: sort, add a note, reload; Copy list as text pastes a clean list.
- [ ] Orders (with an old delivered order): "Time to reorder?" and the spending bars appear.
- [ ] Open help.html or faq.html directly: the "Using this website" and "Know your medicine" groups are there and the section is highlighted.
- [ ] Health: dose planner (every 8 hours from 06:00) creates 06:00, 14:00 and 22:00 reminders; the calendar file opens in your calendar app.

## v2.2.0 (manual check)
- [ ] Real phone: open Shop, Wishlist, Orders, Help, Contact, Health and the admin Products screen; nothing is cut off and tables scroll sideways inside their box.
- [ ] Turn on a screen reader or keyboard-only use on the login page and the storefront header: every button has a clear name.
- [ ] Track an order by number and mobile: "Need help with this order?" appears and opens Contact with the number filled in.

## v3.0.0 design (manual check)
- [ ] Look at Shop, a product page, Cart, Checkout, Orders, Help, Contact, Health and the admin panel in light and dark mode, in English and Bangla, on a real phone and a laptop.
- [ ] Bangla text uses the same typeface (no fallback boxes) and the taka sign shows correctly.
- [ ] Switch the colour palette (🎨): every page stays readable in all four.
- [ ] Print an invoice or a shelf label: the colours do not get in the way.
- [ ] Offline test: after one visit, turn off the internet and reload the home page; fonts and styles still load.

## v3.0.1 (manual check)
- [ ] Press the colour button (🎨) four times: the header, buttons and strip change colour each time, in light and dark mode.
- [ ] Look at the pages in Bangla (the language button): headings and the taka sign use a clean Bengali typeface.

## v3.1.0 admin panel (manual check)
- [ ] The sidebar groups: collapse two, reload, they stay collapsed; open a screen inside a collapsed group through a shortcut and the group opens.
- [ ] Turn on 🔔, leave the panel in a background tab, place an order from another device: the tab title count rises (sound and notification if allowed).
- [ ] Press ? and try "g" then "o".
- [ ] Look at the Dashboard on a phone: the attention chips wrap and the sidebar opens with the menu button.
