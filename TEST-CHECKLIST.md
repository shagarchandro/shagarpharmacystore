# Test checklist
Automated jsdom smoke test (not a real browser) PASSED: catalog render, expired batch excluded from stock, add to cart, checkout, stock deduction, Rx order blocked without prescription details and sent to review, all 15 Owner admin tabs render, monthly report renders, FEFO drain order, oversell blocked.
Also passed in the jsdom run: product page, discount maths, contact form notification, order-success page, dashboard chart, invoice buttons, stock adjustment and negative-stock rejection.
Also passed in the jsdom run: saved details prefill, loyalty points, order again, Rx approve/reject (reject restocks and stores the reason), product edit validation and audit, reorder PO, POS quick add, order filter.
Also passed in the jsdom run (v7): featured/essentials sections, header search, brand and Rx filters, store pickup, admin sidebar, category rename, dashboard quick actions, new settings and logo text on the storefront.
Also passed in the jsdom run (v8): address validation, Rx rule at POS (cashier blocked, pharmacist allowed), sale-linked stock log, POS refund restock, product-sales report, backup validation, error state, asset files.
Real-browser (Playwright/Chromium) sweep and end-to-end flows also PASSED, see README "Testing done".
Everything below is still NOT RUN manually (Firefox, Safari, real phone, print preview, screen reader). is still NOT RUN manually (no real-browser, visual, mobile or print testing).
- [ ] Shop: search, category, sort, max price, pagination, details dialog
- [ ] Cart: qty > stock rejected, SAVE10 needs ৳500+, totals
- [ ] Checkout: bad phone rejected; Rx item requires doctor + confirmation; stock deducted FEFO
- [ ] Orders: login, timeline, cancel restores stock, return request
- [ ] Admin roles: only Owner/Pharmacist approve Rx orders
- [ ] Inventory: expired batch not sellable; write-off; receive batch
- [ ] POS: barcode (e.g. 890001000), cash < total blocked, receipt, suspend/resume
- [ ] Reports CSV; JSON export/import/reset; theme + language persist; mobile layout
- [ ] Purchases: PO receive needs batch + future expiry; stock rises only after receive; purchase return limits
- [ ] Returns: accept (restock/discard) then refund creates refund record
- [ ] Suppliers: balance and payment; Expenses: cashbook and shift close; Delivery queue; Settings and coupon validation
- [ ] Users: add/deactivate (last Owner protected); login lists active users; image upload (3 MB limit); notifications; Bangla toggle on every page; redirect pages open correct views
- [ ] Home chips/offers/testimonials/footer layout on phone; product page; invoice print; chart; skip link
- [ ] Rx queue approve/reject on phone; product edit dialog layout; order search; reorder PO; quick-add; audit trail; return reason prompt; order again with low stock
- [ ] VISUAL: header/hero/cards at 360, 768, 1024, 1440 px; sidebar menu on phone; dark mode contrast; print receipt; Bangla font rendering
- [ ] Checkout address fields on phone; POS Rx prompt flow; POS refund; import of a hand-edited bad backup; error state via Reset button
- [x] Real browser (Chromium): partial receive, supplier edit/delete guard, full product form with image, report date range, orders CSV, guest tracking (tests/e2e2.py)
- [ ] Not run: Firefox, Safari, real phone, print preview, screen reader
