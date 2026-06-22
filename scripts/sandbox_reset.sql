-- Banco sandbox reset -- zero the Day-One demo back to an empty shop.
-- Run against the banco_sandbox DB only. Idempotent, sub-second, no restart.
--
-- Every Banco-touched table is named explicitly AND we CASCADE, so no child row
-- (a line item, a barcode alias, a stock movement, an OPEN cash shift) survives
-- to haunt the next take. RESTART IDENTITY resets the serial counters so the
-- first sale of every take is TXN ...0001 again.
--
-- Staff, store settings and login users are NOT here -- they must persist so
-- Pam can keep logging in and VAT stays correct between takes.

TRUNCATE TABLE
    line_items,
    promo_transactions,
    transactions,
    pos_stock_movements,
    product_barcodes,
    products,
    cash_movements,
    cash_shifts,
    shift_sessions,
    credit_transactions,
    customers
RESTART IDENTITY CASCADE;
