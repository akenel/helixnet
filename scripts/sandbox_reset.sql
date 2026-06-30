-- Banco sandbox reset -- zero the Day-One demo back to a clean trading day.
-- Run against the banco_sandbox DB only. Idempotent, sub-second, no restart.
--
-- SOURCE-SCOPED BY SKU PREFIX. Each catalog source owns ONLY its own prefix and the
-- reset touches ONLY what a source owns:
--   * TAM-  = the Artemis import (the demo seed). The reset REFRESHES it: delete the
--             TAM- rows here, then sandbox_seed_catalog.sql re-inserts the clean 100,
--             so the demo catalog resets crisp every night.
--   * other = manually-created products (e.g. LZ-...) belong to NO sync, so the reset
--             NEVER deletes them -- they persist until a human deletes them. (This is
--             why a hand-made "grinder" used to vanish overnight: the old reset
--             truncated ALL products instead of just TAM-.)
--   * future sources (Mosey/FourTwenty -> MOS-/FTW-) each manage only their own prefix.
--
-- WHAT THIS CLEARS: the SALES / transactional tables (sales, line items, drawers,
-- shifts, cash movements, store credit, walk-in customers, stock-movement ledger).
-- Every such row is truncated WITH CASCADE + RESTART IDENTITY so no OPEN cash shift or
-- stray line item haunts the next take and the first sale is TXN ...0001 again.
--
-- WHAT THIS PRESERVES: every NON-TAM catalog row (products, their translations,
-- images, barcode aliases). A real till does not forget hand-made merchandise
-- overnight. TAM- catalog children (translations/images/barcodes) drop via the
-- products FK CASCADE when the TAM- products are deleted, then get re-seeded.
--
-- Each table is guarded by to_regclass(): the POS create_all() only builds the tables
-- whose models are registered, so the set varies by env. Truncate what exists, skip
-- what doesn't -- the reset never fails on a missing relation.
--
-- Staff, store settings and login users are NOT here -- they must persist so Pam can
-- keep logging in and VAT stays correct between takes.

DO $$
DECLARE
    t text;
BEGIN
    -- 1) Zero the transactional tables (a clean trading day). line_items must go
    --    before the TAM- product delete below (line_items -> products is NO ACTION).
    FOREACH t IN ARRAY ARRAY[
        'line_items',
        'promo_transactions',
        'transactions',
        'pos_stock_movements',
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

    -- 2) Refresh ONLY the TAM- demo catalog: delete its rows (product FK CASCADE drops
    --    their translations/images/barcodes); sandbox_seed_catalog.sql re-inserts the
    --    clean set right after. Non-TAM- products (manual LZ-, future MOS-/FTW-) are
    --    left completely untouched.
    IF to_regclass('products') IS NOT NULL THEN
        DELETE FROM products WHERE sku LIKE 'TAM-%';
    END IF;
END $$;
