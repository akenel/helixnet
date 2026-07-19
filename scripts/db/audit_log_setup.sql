-- ============================================================================
-- Banco AUDIT LOG — the generic change-log machine (who / when / what changed)
-- ----------------------------------------------------------------------------
-- Built once, attach to ANY table with one CREATE TRIGGER line. Captures a
-- field-level diff (old -> new) on every INSERT/UPDATE/DELETE, tagged with the
-- app user (via the `app.actor` session var) or 'system' for raw/background writes.
--
-- Idempotent — safe to re-run. Apply per environment (sandbox -> staging -> prod):
--   docker exec -i postgres psql -U helix_user -d banco_<env> -v ON_ERROR_STOP=1 < audit_log_setup.sql
--
-- The "who": the app must run, per request, inside its transaction:
--   SELECT set_config('app.actor', '<username>', true);   -- true = SET LOCAL (txn-scoped)
-- Until that plumbing lands, app writes log as 'system' (still captures what/when).
-- Motivated 2026-07-19 by a silent staging rename nobody could attribute
-- (memory: banco-master-data-vision). NOTE: `app.current_user` fails to parse —
-- current_user is a reserved word — so the var is `app.actor`.
-- ============================================================================

-- 1) the logbook: one table for every audited change, any entity
CREATE TABLE IF NOT EXISTS audit_log (
  id          BIGSERIAL PRIMARY KEY,
  entity_type TEXT NOT NULL,                       -- which table
  entity_id   TEXT NOT NULL,                       -- which row (PK as text)
  action      TEXT NOT NULL,                       -- INSERT / UPDATE / DELETE
  changed_by  TEXT,                                -- app.actor session var, else 'system'
  changed_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  changes     JSONB                                -- {field:{old,new}} on UPDATE; full row on INSERT/DELETE
);
CREATE INDEX IF NOT EXISTS ix_audit_entity ON audit_log (entity_type, entity_id, changed_at DESC);

-- 2) the tripwire: ONE table-agnostic function (diffs OLD vs NEW generically)
CREATE OR REPLACE FUNCTION audit_capture() RETURNS trigger AS $fn$
DECLARE
  who TEXT := coalesce(nullif(current_setting('app.actor', true), ''), 'system');
  eid TEXT;
  chg JSONB;
BEGIN
  IF TG_OP = 'DELETE' THEN
    eid := OLD.id::text; chg := to_jsonb(OLD);
  ELSIF TG_OP = 'INSERT' THEN
    eid := NEW.id::text; chg := to_jsonb(NEW);
  ELSE
    eid := NEW.id::text;
    SELECT jsonb_object_agg(o.key, jsonb_build_object('old', o.value, 'new', n.value))
      INTO chg
      FROM jsonb_each(to_jsonb(OLD)) o JOIN jsonb_each(to_jsonb(NEW)) n USING (key)
      WHERE o.value IS DISTINCT FROM n.value;
    IF chg IS NULL THEN RETURN NEW; END IF;           -- no real change -> no noise
  END IF;
  INSERT INTO audit_log (entity_type, entity_id, action, changed_by, changes)
    VALUES (TG_TABLE_NAME, eid, TG_OP, who, chg);
  RETURN CASE WHEN TG_OP='DELETE' THEN OLD ELSE NEW END;
END;
$fn$ LANGUAGE plpgsql;

-- 3) attach to the tables we want audited (one line each — this is the "universal" part)
DROP TRIGGER IF EXISTS audit_products ON products;
CREATE TRIGGER audit_products AFTER INSERT OR UPDATE OR DELETE ON products
  FOR EACH ROW EXECUTE FUNCTION audit_capture();

-- To add more later, uncomment (a sale, a closeout, supplier + settings edits):
-- DROP TRIGGER IF EXISTS audit_transactions ON transactions;
-- CREATE TRIGGER audit_transactions AFTER INSERT OR UPDATE OR DELETE ON transactions
--   FOR EACH ROW EXECUTE FUNCTION audit_capture();
-- DROP TRIGGER IF EXISTS audit_cash_shifts ON cash_shifts;
-- CREATE TRIGGER audit_cash_shifts AFTER INSERT OR UPDATE OR DELETE ON cash_shifts
--   FOR EACH ROW EXECUTE FUNCTION audit_capture();
-- (suppliers, store_settings, etc. — same one-liner)
