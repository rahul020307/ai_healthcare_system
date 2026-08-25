-- CuraAssist CareHub: initial PostgreSQL/Supabase application schema
-- Phase 1B prerequisite. This creates the application tables represented by
-- the current SQLAlchemy models before 001_phase_1b_ownership.sql is run.
--
-- IMPORTANT:
-- - Supabase's auth.users is managed by Supabase Auth and is NOT recreated here.
-- - public.users is the application's profile table.
-- - This migration intentionally does not insert demo users or patient data.
-- - Run this only against the dedicated CuraAssist Supabase PostgreSQL project.

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT DEFAULT '+91 98765 43210',
    location TEXT DEFAULT 'Hyderabad, Telangana',
    age INTEGER DEFAULT 34,
    gender TEXT DEFAULT 'Male',
    blood_group TEXT DEFAULT 'O+',
    role TEXT DEFAULT 'Patient',
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_users_id ON users (id);
CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);

CREATE TABLE IF NOT EXISTS health_records (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    member_id TEXT DEFAULT 'fam1',
    user_email TEXT DEFAULT 'rahul.sharma@email.com',
    title TEXT NOT NULL,
    category TEXT DEFAULT 'Medical Reports',
    date TEXT DEFAULT CURRENT_DATE::TEXT,
    doctor TEXT DEFAULT 'Self Upload / Clinic',
    facility TEXT DEFAULT 'CuraAssist Digital Hub',
    summary TEXT DEFAULT '',
    tags TEXT DEFAULT 'Uploaded, Health Record',
    file_url TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_health_records_id ON health_records (id);
CREATE INDEX IF NOT EXISTS ix_health_records_owner_user_id ON health_records (owner_user_id);
CREATE INDEX IF NOT EXISTS ix_health_records_member_id ON health_records (member_id);
CREATE INDEX IF NOT EXISTS ix_health_records_user_email ON health_records (user_email);
CREATE INDEX IF NOT EXISTS ix_health_records_category ON health_records (category);

CREATE TABLE IF NOT EXISTS appointments (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    user_email TEXT DEFAULT 'rahul.sharma@email.com',
    doctor_id TEXT,
    doctor_name TEXT NOT NULL,
    specialty TEXT DEFAULT 'General Physician',
    patient_name TEXT NOT NULL,
    appointment_date TEXT NOT NULL,
    appointment_time TEXT NOT NULL,
    status TEXT DEFAULT 'Confirmed',
    consultation_type TEXT DEFAULT 'In-Person',
    hospital_name TEXT DEFAULT 'Apollo Hospitals',
    notes TEXT DEFAULT '',
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_appointments_id ON appointments (id);
CREATE INDEX IF NOT EXISTS ix_appointments_owner_user_id ON appointments (owner_user_id);
CREATE INDEX IF NOT EXISTS ix_appointments_user_email ON appointments (user_email);
CREATE INDEX IF NOT EXISTS ix_appointments_doctor_id ON appointments (doctor_id);

CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    user_email TEXT DEFAULT 'rahul.sharma@email.com',
    patient_name TEXT DEFAULT 'Rahul Sharma',
    items_json TEXT NOT NULL,
    total_amount DOUBLE PRECISION NOT NULL,
    delivery_address TEXT NOT NULL,
    payment_method TEXT DEFAULT 'UPI / Card',
    status TEXT DEFAULT 'Processing',
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_orders_id ON orders (id);
CREATE INDEX IF NOT EXISTS ix_orders_owner_user_id ON orders (owner_user_id);
CREATE INDEX IF NOT EXISTS ix_orders_user_email ON orders (user_email);

CREATE TABLE IF NOT EXISTS vitals (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    user_email TEXT DEFAULT 'rahul.sharma@email.com',
    systolic INTEGER DEFAULT 120,
    diastolic INTEGER DEFAULT 80,
    pulse INTEGER DEFAULT 72,
    temperature DOUBLE PRECISION DEFAULT 98.6,
    glucose DOUBLE PRECISION DEFAULT 95.0,
    recorded_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_vitals_id ON vitals (id);
CREATE INDEX IF NOT EXISTS ix_vitals_owner_user_id ON vitals (owner_user_id);
CREATE INDEX IF NOT EXISTS ix_vitals_user_email ON vitals (user_email);

CREATE TABLE IF NOT EXISTS medicines (
    medicine_id TEXT PRIMARY KEY,
    brand_name TEXT,
    generic_name TEXT,
    composition TEXT,
    category TEXT,
    price DOUBLE PRECISION,
    original_price DOUBLE PRECISION,
    dosage TEXT,
    prescription_required BOOLEAN DEFAULT FALSE,
    rating DOUBLE PRECISION DEFAULT 4.8,
    image_url TEXT DEFAULT ''
);

CREATE INDEX IF NOT EXISTS ix_medicines_medicine_id ON medicines (medicine_id);
CREATE INDEX IF NOT EXISTS ix_medicines_brand_name ON medicines (brand_name);
CREATE INDEX IF NOT EXISTS ix_medicines_generic_name ON medicines (generic_name);
CREATE INDEX IF NOT EXISTS ix_medicines_category ON medicines (category);

CREATE TABLE IF NOT EXISTS facilities (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT,
    address TEXT,
    phone TEXT,
    lat DOUBLE PRECISION NOT NULL,
    lng DOUBLE PRECISION NOT NULL,
    rating DOUBLE PRECISION DEFAULT 4.8,
    open_hours TEXT DEFAULT 'Open 24 Hours',
    emergency_available BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS ix_facilities_id ON facilities (id);
CREATE INDEX IF NOT EXISTS ix_facilities_type ON facilities (type);

-- Establish the application-level ownership foreign keys after all base tables
-- exist. Phase 1B migration 001 remains responsible for legacy backfill and
-- final NOT NULL enforcement when migrating an existing database.
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
