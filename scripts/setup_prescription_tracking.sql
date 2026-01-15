-- ============================================================================
-- Prescription Tracking & Outbreak Detection Schema
-- ============================================================================

-- 1. Prescription Records
CREATE TABLE IF NOT EXISTS prescriptions (
    prescription_id BIGSERIAL PRIMARY KEY,
    hospital_id VARCHAR(50),
    doctor_id VARCHAR(50),
    patient_age INT,
    patient_gender CHAR(1),
    location VARCHAR(100),
    icd10_code VARCHAR(20),
    diagnosis TEXT,
    prescribed_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_prescriptions_icd10 ON prescriptions(icd10_code);
CREATE INDEX idx_prescriptions_location ON prescriptions(location);
CREATE INDEX idx_prescriptions_date ON prescriptions(prescribed_date);
CREATE INDEX idx_prescriptions_hospital ON prescriptions(hospital_id);

-- 2. Prescription Drugs (many-to-many)
CREATE TABLE IF NOT EXISTS prescription_drugs (
    id BIGSERIAL PRIMARY KEY,
    prescription_id BIGINT REFERENCES prescriptions(prescription_id),
    snomed_id BIGINT,
    brand_name TEXT,
    generic_name TEXT,
    dosage TEXT,
    duration TEXT,
    quantity INT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_prescription_drugs_prescription ON prescription_drugs(prescription_id);
CREATE INDEX idx_prescription_drugs_snomed ON prescription_drugs(snomed_id);
CREATE INDEX idx_prescription_drugs_generic ON prescription_drugs USING gin(generic_name gin_trgm_ops);

-- 3. Outbreak Tracking (Materialized View)
CREATE MATERIALIZED VIEW IF NOT EXISTS outbreak_trends AS
SELECT 
    location,
    icd10_code,
    diagnosis,
    DATE_TRUNC('week', prescribed_date) as week,
    COUNT(*) as case_count,
    AVG(patient_age) as avg_age,
    COUNT(CASE WHEN patient_gender = 'M' THEN 1 END) as male_count,
    COUNT(CASE WHEN patient_gender = 'F' THEN 1 END) as female_count
FROM prescriptions
WHERE prescribed_date >= CURRENT_DATE - INTERVAL '8 weeks'
GROUP BY location, icd10_code, diagnosis, DATE_TRUNC('week', prescribed_date);

CREATE UNIQUE INDEX idx_outbreak_trends_unique 
    ON outbreak_trends(location, icd10_code, week);

-- 4. Drug Popularity (Materialized View)
CREATE MATERIALIZED VIEW IF NOT EXISTS drug_popularity AS
SELECT 
    pd.snomed_id,
    pd.generic_name,
    p.icd10_code,
    p.location,
    COUNT(*) as prescription_count,
    COUNT(DISTINCT p.hospital_id) as hospital_count,
    DATE_TRUNC('month', p.prescribed_date) as month
FROM prescription_drugs pd
JOIN prescriptions p ON pd.prescription_id = p.prescription_id
WHERE p.prescribed_date >= CURRENT_DATE - INTERVAL '6 months'
GROUP BY pd.snomed_id, pd.generic_name, p.icd10_code, p.location, 
         DATE_TRUNC('month', p.prescribed_date);

CREATE INDEX idx_drug_popularity_icd10 ON drug_popularity(icd10_code);
CREATE INDEX idx_drug_popularity_location ON drug_popularity(location);

-- 5. Function: Refresh outbreak data
CREATE OR REPLACE FUNCTION refresh_outbreak_data()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY outbreak_trends;
    REFRESH MATERIALIZED VIEW CONCURRENTLY drug_popularity;
END;
$$ LANGUAGE plpgsql;

-- 6. Sample data for testing
INSERT INTO prescriptions (hospital_id, doctor_id, patient_age, patient_gender, location, icd10_code, diagnosis, prescribed_date)
VALUES 
    ('H001', 'D001', 35, 'M', 'Mumbai', 'R50.9', 'Viral Fever', CURRENT_DATE - INTERVAL '1 day'),
    ('H001', 'D002', 28, 'F', 'Mumbai', 'R50.9', 'Viral Fever', CURRENT_DATE - INTERVAL '2 days'),
    ('H002', 'D003', 42, 'M', 'Mumbai', 'J00', 'Common Cold', CURRENT_DATE - INTERVAL '1 day'),
    ('H001', 'D001', 55, 'M', 'Delhi', 'E11.9', 'Type 2 Diabetes', CURRENT_DATE - INTERVAL '3 days'),
    ('H003', 'D004', 30, 'F', 'Bangalore', 'R50.9', 'Viral Fever', CURRENT_DATE);

-- Refresh views
SELECT refresh_outbreak_data();

-- 7. Grant permissions
-- GRANT SELECT ON prescriptions TO app_user;
-- GRANT SELECT ON prescription_drugs TO app_user;
-- GRANT SELECT ON outbreak_trends TO app_user;
-- GRANT SELECT ON drug_popularity TO app_user;
