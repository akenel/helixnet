-- Banco sandbox reset -- zero the Day-One demo back to an empty shop.
-- Run against the banco_sandbox DB only. Idempotent, sub-second, no restart.
--
-- Every Banco-touched table is truncated WITH CASCADE, so no child row (a line
-- item, a barcode alias, a stock movement, an OPEN cash shift) survives to haunt
-- the next take. RESTART IDENTITY resets serial counters so the first sale of
-- every take is TXN ...0001 again.
--
-- Each table is guarded by to_regclass(): the POS create_all() only builds the
-- tables whose models are registered, so the set varies by env. Truncate what
-- exists, skip what doesn't -- the reset never fails on a missing relation.
--
-- Staff, store settings and login users are NOT here -- they must persist so
-- Pam can keep logging in and VAT stays correct between takes.

DO $$
DECLARE
    t text;
BEGIN
    FOREACH t IN ARRAY ARRAY[
        'line_items',
        'promo_transactions',
        'transactions',
        'pos_stock_movements',
        'product_barcodes',
        'products',
        'cash_movements',
        'cash_shifts',
        'shift_sessions',
        'credit_transactions',
        'customers'
    ] LOOP
        IF to_regclass(t) IS NOT NULL THEN
            EXECUTE format('TRUNCATE TABLE %I RESTART IDENTITY CASCADE', t);
        END IF;
    END LOOP;
END $$;
