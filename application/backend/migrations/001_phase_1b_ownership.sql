-- Phase 1B: durable application ownership for Supabase-authenticated users.
-- Target: PostgreSQL / Supabase.
-- Existing email/member_id fields are intentionally retained for compatibility.
-- owner_user_id is nullable only during deterministic legacy backfill.

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

-- Preflight identity-integrity check: the backfill matches emails
-- case-insensitively, so duplicate lower(email) identities would make the
-- mapping nondeterministic. Abort before changing any ownership data.
DO $$
DECLARE
    duplicate_count integer;
BEGIN
    SELECT count(*) INTO duplicate_count
    FROM (
        SELECT lower(email) AS normalized_email
        FROM users
        WHERE email IS NOT NULL
        GROUP BY lower(email)
        HAVING count(*) > 1
    ) AS duplicate_identities;

    IF duplicate_count > 0 THEN
        RAISE EXCEPTION
            'Phase 1B ownership preflight failed: duplicate case-insensitive user email identities detected (%)',
            duplicate_count;
    END IF;
END $$;

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

-- Explicit remediation/report path: do not silently assign ambiguous or
-- unmatched rows. Migration must stop before enforcing NOT NULL and FKs if
-- any user-owned row cannot be deterministically mapped.
DO $$
DECLARE
    unmatched_health integer;
    unmatched_appointments integer;
    unmatched_orders integer;
    unmatched_vitals integer;
BEGIN
    SELECT count(*) INTO unmatched_health
    FROM health_records
    WHERE owner_user_id IS NULL;

    SELECT count(*) INTO unmatched_appointments
    FROM appointments
    WHERE owner_user_id IS NULL;

    SELECT count(*) INTO unmatched_orders
    FROM orders
    WHERE owner_user_id IS NULL;

    SELECT count(*) INTO unmatched_vitals
    FROM vitals
    WHERE owner_user_id IS NULL;

    IF unmatched_health > 0 OR unmatched_appointments > 0 OR unmatched_orders > 0 OR unmatched_vitals > 0 THEN
        RAISE EXCEPTION
            'Phase 1B ownership backfill incomplete: health_records=%, appointments=%, orders=%, vitals=%',
            unmatched_health, unmatched_appointments, unmatched_orders, unmatched_vitals;
    END IF;
END $$;

ALTER TABLE health_records ALTER COLUMN owner_user_id SET NOT NULL;
ALTER TABLE appointments ALTER COLUMN owner_user_id SET NOT NULL;
ALTER TABLE orders ALTER COLUMN owner_user_id SET NOT NULL;
ALTER TABLE vitals ALTER COLUMN owner_user_id SET NOT NULL;

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
