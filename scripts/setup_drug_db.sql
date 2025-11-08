-- Setup Drug Database Schema
-- Run this first before ETL pipeline

-- 1. Generic Ingredients (Master)
CREATE TABLE IF NOT EXISTS generic_ingredients (
    ingredient_id SERIAL PRIMARY KEY,
    rxnorm_cui VARCHAR(20) UNIQUE,
    ingredient_name VARCHAR(200) NOT NULL,
    atc_code VARCHAR(20),
    cas_number VARCHAR(50),
    therapeutic_class VARCHAR(100),
    pharmacological_class VARCHAR(100),
    drug_category VARCHAR(50),
    indications TEXT,
    symptoms TEXT,
    conditions TEXT,
    ingredient_name_hindi TEXT,
    ingredient_name_tamil TEXT,
    ingredient_name_telugu TEXT,
    search_vector TSVECTOR,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_rxnorm_cui ON generic_ingredients(rxnorm_cui);
CREATE INDEX idx_atc_code ON generic_ingredients(atc_code);
CREATE INDEX idx_ingredient_name ON generic_ingredients(ingredient_name);
CREATE INDEX idx_ingredient_search ON generic_ingredients USING gin(search_vector);

-- 2. Indian Brand Drugs
CREATE TABLE IF NOT EXISTS indian_brand_drugs (
    brand_id SERIAL PRIMARY KEY,
    brand_name VARCHAR(200) NOT NULL,
    manufacturer VARCHAR(200),
    ingredient_id INTEGER REFERENCES generic_ingredients(ingredient_id),
    rxnorm_cui VARCHAR(20),
    strength VARCHAR(50),
    dosage_form VARCHAR(50),
    route VARCHAR(50),
    schedule VARCHAR(10),
    cdsco_approval VARCHAR(50),
    mrp DECIMAL(10,2),
    pack_size VARCHAR(50),
    prescription_required BOOLEAN DEFAULT TRUE,
    otc_available BOOLEAN DEFAULT FALSE,
    brand_name_hindi TEXT,
    brand_name_tamil TEXT,
    search_vector TSVECTOR,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(brand_name, strength, dosage_form)
);

CREATE INDEX idx_brand_ingredient ON indian_brand_drugs(ingredient_id);
CREATE INDEX idx_brand_rxnorm ON indian_brand_drugs(rxnorm_cui);
CREATE INDEX idx_brand_name ON indian_brand_drugs(brand_name);
CREATE INDEX idx_brand_manufacturer ON indian_brand_drugs(manufacturer);
CREATE INDEX idx_brand_search ON indian_brand_drugs USING gin(search_vector);

-- 3. Combination Drugs
CREATE TABLE IF NOT EXISTS combination_drugs (
    combination_id SERIAL PRIMARY KEY,
    brand_name VARCHAR(200) NOT NULL,
    manufacturer VARCHAR(200),
    ingredients JSONB,
    dosage_form VARCHAR(50),
    mrp DECIMAL(10,2),
    pack_size VARCHAR(50),
    search_vector TSVECTOR,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_combination_ingredients ON combination_drugs USING gin(ingredients);
CREATE INDEX idx_combination_search ON combination_drugs USING gin(search_vector);

-- 4. Drug Interactions
CREATE TABLE IF NOT EXISTS drug_interactions (
    interaction_id SERIAL PRIMARY KEY,
    drug_a_id INTEGER REFERENCES generic_ingredients(ingredient_id),
    drug_b_id INTEGER REFERENCES generic_ingredients(ingredient_id),
    severity VARCHAR(20),
    interaction_type VARCHAR(50),
    description TEXT,
    clinical_effect TEXT,
    management TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_interaction_drug_a ON drug_interactions(drug_a_id);
CREATE INDEX idx_interaction_drug_b ON drug_interactions(drug_b_id);

-- 5. Drug Contraindications
CREATE TABLE IF NOT EXISTS drug_contraindications (
    contraindication_id SERIAL PRIMARY KEY,
    drug_id INTEGER REFERENCES generic_ingredients(ingredient_id),
    icd10_code VARCHAR(20),
    contraindication_type VARCHAR(20),
    reason TEXT,
    alternative_drugs JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_contraindication_drug ON drug_contraindications(drug_id);
CREATE INDEX idx_contraindication_icd10 ON drug_contraindications(icd10_code);

-- Enable full-text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Update search vectors (trigger function)
CREATE OR REPLACE FUNCTION update_drug_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.brand_name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.manufacturer, '')), 'B');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_generic_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.ingredient_name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.indications, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.symptoms, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.conditions, '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER brand_search_vector_update
    BEFORE INSERT OR UPDATE ON indian_brand_drugs
    FOR EACH ROW EXECUTE FUNCTION update_drug_search_vector();

CREATE TRIGGER generic_search_vector_update
    BEFORE INSERT OR UPDATE ON generic_ingredients
    FOR EACH ROW EXECUTE FUNCTION update_generic_search_vector();

-- 6. Ayushman Bharat HBP Procedures
CREATE TABLE IF NOT EXISTS abhbp_procedures (
    procedure_id SERIAL PRIMARY KEY,
    package_code VARCHAR(20) UNIQUE NOT NULL,
    package_name TEXT NOT NULL,
    specialty VARCHAR(100),
    procedure_type TEXT,
    base_rate DECIMAL(10,2),
    icd10_codes JSONB DEFAULT '[]',
    cpt_equivalent VARCHAR(20),
    hbp_category VARCHAR(50),
    empanelment_required BOOLEAN DEFAULT TRUE,
    preauth_required BOOLEAN DEFAULT FALSE,
    search_vector TSVECTOR,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_abhbp_package_code ON abhbp_procedures(package_code);
CREATE INDEX idx_abhbp_specialty ON abhbp_procedures(specialty);
CREATE INDEX idx_abhbp_search ON abhbp_procedures USING gin(search_vector);
CREATE INDEX idx_abhbp_icd10 ON abhbp_procedures USING gin(icd10_codes);

-- Update search vector for AB-HBP
CREATE OR REPLACE FUNCTION update_abhbp_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.package_code, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.package_name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.specialty, '')), 'B');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER abhbp_search_vector_update
    BEFORE INSERT OR UPDATE ON abhbp_procedures
    FOR EACH ROW EXECUTE FUNCTION update_abhbp_search_vector();

-- Sample data
INSERT INTO generic_ingredients (rxnorm_cui, ingredient_name, atc_code, therapeutic_class) VALUES
('202433', 'Acetaminophen', 'N02BE01', 'Analgesic/Antipyretic'),
('6809', 'Metformin', 'A10BA02', 'Antidiabetic'),
('36567', 'Simvastatin', 'C10AA01', 'Lipid Lowering Agent'),
('3521', 'Amlodipine', 'C08CA01', 'Calcium Channel Blocker'),
('8640', 'Omeprazole', 'A02BC01', 'Proton Pump Inhibitor')
ON CONFLICT (rxnorm_cui) DO NOTHING;
