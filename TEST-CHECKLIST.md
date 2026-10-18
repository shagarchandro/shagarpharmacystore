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
