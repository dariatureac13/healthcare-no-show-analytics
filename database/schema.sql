-- Drop tables if they already exist to allow clean script re-execution
DROP TABLE IF EXISTS appointments CASCADE;
DROP TABLE IF EXISTS doctors CASCADE;
DROP TABLE IF EXISTS clinics CASCADE;
DROP TABLE IF EXISTS patients CASCADE;

-- 1. Patients lookup table
CREATE TABLE patients (
    patient_id BIGINT PRIMARY KEY,
    gender CHAR(1) NOT NULL,
    age INT CHECK (age >= 0),
    scholarship INT NOT NULL,     -- Health insurance (0/1)
    hypertension INT NOT NULL,    -- Hypertension (0/1)
    diabetes INT NOT NULL,        -- Diabetes (0/1)
    alcoholism INT NOT NULL,      -- Alcoholism (0/1)
    handicap INT NOT NULL         -- Disability level (0-4)
);

-- 2. Clinics / Neighbourhoods lookup table
CREATE TABLE clinics (
    clinic_id SERIAL PRIMARY KEY,
    neighbourhood VARCHAR(100) UNIQUE NOT NULL -- Patient neighborhood
);

-- 3. Doctors lookup table (Synthetic)
CREATE TABLE doctors (
    doctor_id SERIAL PRIMARY KEY,
    doctor_name VARCHAR(100) NOT NULL,
    specialization VARCHAR(50) NOT NULL,
    service_cost DECIMAL(10, 2) NOT NULL
);

-- 4. Appointments fact table
CREATE TABLE appointments (
    appointment_id BIGINT PRIMARY KEY,
    patient_id BIGINT NOT NULL REFERENCES patients(patient_id),
    clinic_id INT NOT NULL REFERENCES clinics(clinic_id),
    doctor_id INT NOT NULL REFERENCES doctors(doctor_id),
    scheduled_day TIMESTAMP NOT NULL,    -- Day of scheduling
    appointment_day TIMESTAMP NOT NULL,  -- Appointment day scheduled
    sms_received INT NOT NULL,           -- SMS reminder used (0/1)
    no_show VARCHAR(3) NOT NULL          -- Target variable ('Yes'/'No')
);