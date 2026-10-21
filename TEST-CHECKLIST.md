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
- [manual] Try two-step login with your own phone's authenticator app; test the server-console password reset on your real server
- [manual] Run behind HTTPS with --secure-cookies; test from a real phone on your network; try a failed power cut (restart the server and check orders are still there)
- [not run] Load testing, Windows/macOS server hosting, long-running (days) stability
