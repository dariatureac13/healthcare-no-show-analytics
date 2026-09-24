import os
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from faker import Faker
from sqlalchemy import create_engine, text

# STEP 1: Database Connection & Table Cleanup
load_dotenv()  # Reads environment variables from .env file

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "clinic_db")

# Build SQLAlchemy connection string (PostgreSQL driver: psycopg2)
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

# Clear existing data before running ETL
with engine.begin() as conn:
    conn.execute(text("TRUNCATE TABLE appointments, patients, doctors, clinics RESTART IDENTITY CASCADE;"))
print("Existing database tables cleared.")
print("Successfully connected to PostgreSQL!")


# STEP 2: Read Raw CSV Data

csv_path = 'data/Kaggle_noshow_dataset.csv'
df_raw = pd.read_csv(csv_path, sep=';')
df_raw.columns = df_raw.columns.str.strip()


# STEP 3: Populate Lookup Tables


# 3.1. Clinics (clinics)
clinics_df = pd.DataFrame(df_raw['Neighbourhood'].dropna().unique(), columns=['neighbourhood'])
clinics_df.to_sql('clinics', engine, if_exists='append', index=False)

clinics_db = pd.read_sql('SELECT clinic_id, neighbourhood FROM clinics', engine)
clinic_map = dict(zip(clinics_db['neighbourhood'], clinics_db['clinic_id']))


# 3.2. Doctors (doctors) - Synthetic Lookup via Faker
fake = Faker()
Faker.seed(42)
np.random.seed(42)

specs = ["General Practice", "Diagnostics", "Therapy", "Surgery", "Neurology", "Pediatrics", "Cardiology"]
doctors_data = []

# Doctors are generated based on the number of clinics, with 4 doctors per clinic
total_doctors = len(clinics_db) * 4
for _ in range(total_doctors):
    doctors_data.append({
        "doctor_name": f"Dr. {fake.name()}",
        "specialization": np.random.choice(specs),
        "service_cost": float(np.random.choice([50.0, 70.0, 100.0, 120.0, 150.0, 200.0]))
    })

doctors_df = pd.DataFrame(doctors_data)
doctors_df.to_sql('doctors', engine, if_exists='append', index=False)

doctor_ids = pd.read_sql('SELECT doctor_id FROM doctors', engine)['doctor_id'].tolist()


# 3.3. Patients (patients)
patients_df = df_raw[[
    'PatientId', 'Gender', 'Age', 'Scholarship', 
    'Hipertension', 'Diabetes', 'Alcoholism', 'Handcap'
]].copy()

patients_df.columns = [
    'patient_id', 'gender', 'age', 'scholarship', 
    'hypertension', 'diabetes', 'alcoholism', 'handicap'
]

# Fix scientific string format ('2,98725E+13') -> float -> int64
patients_df['patient_id'] = (
    patients_df['patient_id']
    .astype(str)
    .str.replace(',', '.')
    .astype(float)
    .astype(np.int64)
)
patients_df = patients_df.drop_duplicates(subset=['patient_id'])
patients_df = patients_df[patients_df['age'] >= 0]

patients_df.to_sql('patients', engine, if_exists='append', index=False)


# STEP 4: Populate Fact Table (appointments)

appointments_df = df_raw.copy()

appointments_df['clinic_id'] = appointments_df['Neighbourhood'].map(clinic_map)
appointments_df['doctor_id'] = np.random.choice(doctor_ids, size=len(appointments_df))

appointments_df = appointments_df.rename(columns={
    'AppointmentID': 'appointment_id',
    'PatientId': 'patient_id',
    'ScheduledDay': 'scheduled_day',
    'AppointmentDay': 'appointment_day',
    'SMS_received': 'sms_received',
    'No-show': 'no_show'
})

appointments_df['patient_id'] = (
    appointments_df['patient_id']
    .astype(str)
    .str.replace(',', '.')
    .astype(float)
    .astype(np.int64)
)


appointments_df = appointments_df[appointments_df['patient_id'].isin(patients_df['patient_id'])]


appointments_df['scheduled_day'] = pd.to_datetime(appointments_df['scheduled_day'], dayfirst=True)
appointments_df['appointment_day'] = pd.to_datetime(appointments_df['appointment_day'], dayfirst=True)

fact_columns = [
    'appointment_id', 'patient_id', 'clinic_id', 'doctor_id',
    'scheduled_day', 'appointment_day', 'sms_received', 'no_show'
]

appointments_df[fact_columns].to_sql('appointments', engine, if_exists='append', index=False)

print("ETL pipeline executed successfully! All tables populated.")