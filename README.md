# MediCare Pharmacy Management System (demo)
Vanilla HTML/CSS/JS storefront + admin panel for a fictional Bangladesh pharmacy. No build step.

## Run
Open this folder in VS Code → right-click `index.html` → **Open with Live Server** (or `python3 -m http.server`).
Admin: `/admin/login.html`, pick a role, demo code `demo` (not real security).

## Structure
`index.html` (storefront SPA: shop, cart, checkout, orders, wishlist, help) · `admin/` (login + panel) · `assets/js/core.js` (storage, seed data, i18n, FEFO stock) · `store.js` · `admin.js` · `assets/css/styles.css`.

## Implemented
Search/filter/sort/pagination, product details, Rx flagging + pharmacist-review gate, cart with stock validation and coupon `SAVE10`, checkout with BD phone validation, order tracking/cancel/return request, wishlist, dark mode, EN/বাংলা (core labels), ৳ and Asia/Dhaka dates.
Admin: role-based tabs, KPIs, product add/price edit/delete, batch inventory with FEFO + expiry blocking + write-off + receiving, POS with receipt/suspend/resume, order statuses, reports + CSV (formula-safe), JSON export/import (validated, preview) and reset.

## Data
Everything is in LocalStorage key `mc_db` (schema v1). Reset: Admin → Data → Reset.

## Added in v2
Purchase orders with receive-to-stock (stock counts only after receiving) and purchase returns, order returns/refunds with optional restock, suppliers with balances and payments, customers with loyalty points, expenses and cashbook with shift closing, delivery queue, settings, coupons, activity log.

## Added in v3
Alerts tab (low stock, near expiry, expired, Rx reviews, return requests), full report set with daily/weekly/monthly periods and CSV export per table, product edit (name, reorder level, Rx flag), generated placeholder product images (no external files), more Bangla labels. Fixed a bug where the admin panel failed to load because of a duplicate `V` identifier.

## Added in v4
Per-feature entry pages (`products.html`, `cart.html`, `checkout.html`, `orders.html`, `wishlist.html`, `faq.html`, `privacy.html`, `terms.html`, `contact.html`, `admin/pos.html`, `admin/inventory.html`, etc.) that open the matching view of the single-page app; user management (Owner only, no passwords, login picks a demo user); in-app notifications (new orders, return requests); product image upload (resized to a small JPEG stored in LocalStorage); broader Bangla translation of labels, buttons, tables and messages.

## Added in v5
Home page category chips, offers strip, testimonials (fictional) and footer; real product detail page (`#/product/ID`); contact form (saved as an in-app notification); order-success page; per-product discount % (shown with strike-through, used in cart, orders and POS); manual stock adjustment with reasons (damaged stock is logged as an expense); 7-day sales chart on the dashboard; printable order invoices; skip-to-content links.

## Added in v6
Customer: saved details (checkout is prefilled), loyalty points, "Order again" (respects current stock), mandatory reason for return requests, pharmacy note shown on rejected prescriptions.
Admin: Prescription review queue (approve, or reject with a reason that restocks the order and tells the customer), full product edit dialog (all fields, SKU/barcode uniqueness, discount limits), order search and status filter, reorder suggestions that create purchase orders (no duplicate open PO), POS quick-add buttons, admin audit trail in Settings.

## Added in v7 (prompt gap audit + premium redesign)
Design: new teal/mint/amber system with serif headlines, glass header with search, capsule hero, product cards with images and discount badges, admin sidebar shell with icons, active-item highlight, mobile off-canvas menu, dark mode, print styles, reduced-motion support.
Storefront: header search, featured products and health essentials sections, brand and prescription-type filters, store pickup (free, no address needed), FAQ accordion help center, store name/address/phone from Settings, coupons honour the disable switch.
Admin: Categories & brands management (rename/merge), dashboard quick actions and expiry alerts, FEFO "sell first" marker per batch, delivery rider assignment, coupon enable/disable/delete, full business settings (logo text, address, phone, receipt footer, default reorder level, theme and language for this browser).

## Added in v8
Prescription control at the POS (Rx items need a pharmacist or owner plus a prescription reference, saved on the sale), POS sale refunds with optional restock and linked refund records, stock-log entries linked to the sale number, strict backup validation (schema version, unique ids, batch/order/sale checks) before the restore preview, Bangladesh address fields (division, district, thana/upazila, postcode), friendly error state instead of a blank page, product-sales report, batch number on product pages, favicon/logo/placeholder assets, more Bangla labels.

## Added in v9
Customer management in admin (search, rename, internal note, block/unblock; blocked numbers cannot place orders; per-customer order list). Bangla product names, categories and order statuses. Real standalone pages: every storefront page (`cart.html`, `checkout.html`, `orders.html`, `wishlist.html`, `contact.html`, `faq.html`, `privacy.html`, `terms.html`, `products.html`, `product-details.html?id=P1`, `order-success.html?no=INV-1001`) and every admin page (`admin/pos.html`, `admin/inventory.html`, ...) now loads the app directly on that screen instead of redirecting. Fixes found in real-browser testing: admin deep links such as `admin/index.html#rx` opened the wrong tab; long generic names overflowed cards on phones; sidebar order and empty states tidied; clicking outside the mobile menu closes it.

## Added in v10
Add-product full form (all fields, image upload, discount, validation) alongside the quick form; supplier edit and guarded delete; partial purchase receiving (each delivery becomes its own batch; supplier balance follows what was actually received); guest order tracking by order number plus mobile number; report date range (From/To) applied to sales, profit and product sales; CSV export for orders and customers.

## Testing done
Playwright with Chromium (served by `python3 -m http.server`): all store pages and all 19 admin tabs at 360, 768 and 1280 px had no console errors and no horizontal overflow; end-to-end flows passed (order, Rx order, pharmacist approval, POS barcode sale and receipt, bad-backup rejection, Bangla mode). A jsdom logic suite also passes. Scripts are in `tests/` (optional dev tools: `pip install playwright`, serve the folder on port 8765, run `python3 tests/e2e.py` and `python3 tests/e2e2.py`).
Not tested: Firefox, Safari, a real phone, print preview, screen readers, VS Code Live Server itself.

## Prompt coverage (honest)
Implemented: everything in the original brief that a browser-only demo can do. Still demo-only or not real: login (demo code, no passwords), payments (selection only), SMS/email (in-app notifications only), barcode hardware (keyboard entry only), prescription documents (deliberately not stored), delivery tracking (manual statuses).
Not done: loyalty point redemption (points are displayed only); free-text content (notes, addresses, user-entered names) is not translated; Bangla product names exist only for the 12 demo products.

## Limitations (honest)
Demo only; not secure for real pharmacy use. Real use needs a backend, database, auth, audit trail and protected prescription handling.
