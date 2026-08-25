-- Phase 1B: durable application ownership for Supabase-authenticated users.
-- Target: PostgreSQL / Supabase.
-- Existing email/member_id fields are intentionally retained for compatibility.
-- owner_user_id is nullable during migration so legacy rows can be backfilled safely.

ALTER TABLE health_records
    ADD COLUMN IF NOT EXISTS owner_user_id TEXT;
ALTER TABLE appointments
    ADD COLUMN IF NOT EXISTS owner_user_id TEXT;
ALTER TABLE orders
    ADD COLUMN IF NOT EXISTS owner_user_id TEXT;
ALTER TABLE vitals
    ADD COLUMN IF NOT EXISTS owner_user_id TEXT;

CREATE INDEX IF NOT EXISTS ix_health_records_owner_user_id
    ON health_records (owner_user_id);
CREATE INDEX IF NOT EXISTS ix_appointments_owner_user_id
    ON appointments (owner_user_id);
CREATE INDEX IF NOT EXISTS ix_orders_owner_user_id
    ON orders (owner_user_id);
CREATE INDEX IF NOT EXISTS ix_vitals_owner_user_id
    ON vitals (owner_user_id);

-- Deterministic legacy backfill: only rows whose stored email matches an
-- existing application profile are associated. No request-supplied identity
-- participates in this migration.
UPDATE health_records AS r
SET owner_user_id = u.id
FROM users AS u
WHERE r.owner_user_id IS NULL
  AND r.user_email IS NOT NULL
  AND lower(r.user_email) = lower(u.email);

UPDATE appointments AS a
SET owner_user_id = u.id
FROM users AS u
WHERE a.owner_user_id IS NULL
  AND a.user_email IS NOT NULL
  AND lower(a.user_email) = lower(u.email);

UPDATE orders AS o
SET owner_user_id = u.id
FROM users AS u
WHERE o.owner_user_id IS NULL
  AND o.user_email IS NOT NULL
  AND lower(o.user_email) = lower(u.email);

UPDATE vitals AS v
SET owner_user_id = u.id
FROM users AS u
WHERE v.owner_user_id IS NULL
  AND v.user_email IS NOT NULL
  AND lower(v.user_email) = lower(u.email);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_health_records_owner_user'
    ) THEN
        ALTER TABLE health_records
            ADD CONSTRAINT fk_health_records_owner_user
            FOREIGN KEY (owner_user_id) REFERENCES users(id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_appointments_owner_user'
    ) THEN
        ALTER TABLE appointments
            ADD CONSTRAINT fk_appointments_owner_user
            FOREIGN KEY (owner_user_id) REFERENCES users(id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_orders_owner_user'
    ) THEN
        ALTER TABLE orders
            ADD CONSTRAINT fk_orders_owner_user
            FOREIGN KEY (owner_user_id) REFERENCES users(id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_vitals_owner_user'
    ) THEN
        ALTER TABLE vitals
            ADD CONSTRAINT fk_vitals_owner_user
            FOREIGN KEY (owner_user_id) REFERENCES users(id);
    END IF;
END $$;
