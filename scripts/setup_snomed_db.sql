-- ============================================================================
-- SNOMED CT Indian Drug Database Schema
-- Production-grade schema for 89K+ Indian drugs with SNOMED codes
-- ============================================================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- ============================================================================
-- 1. SNOMED Substances (28,913 records)
-- ============================================================================
CREATE TABLE IF NOT EXISTS snomed_substances (
    snomed_id BIGINT PRIMARY KEY,
    substance_name TEXT NOT NULL,
    cas_number VARCHAR(50),
    unii VARCHAR(20),
    substance_description TEXT,
    molecular_weight VARCHAR(50),
    toxicity TEXT,
    smile TEXT,
    inchi TEXT,
    iupac_name TEXT,
    molecular_formula VARCHAR(200),
    last_updated DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_snomed_substance_name ON snomed_substances USING gin(substance_name gin_trgm_ops);
CREATE INDEX idx_snomed_cas ON snomed_substances(cas_number) WHERE cas_number IS NOT NULL;
CREATE INDEX idx_snomed_unii ON snomed_substances(unii) WHERE unii IS NOT NULL;

-- ============================================================================
-- 2. SNOMED Generics (9,870 records)
-- ============================================================================
CREATE TABLE IF NOT EXISTS snomed_generics (
    snomed_id BIGINT PRIMARY KEY,
    generic_name TEXT NOT NULL,
    substance_ids TEXT,  -- Comma-separated SNOMED IDs
    route_of_admin TEXT, -- Comma-separated route codes
    dose_form TEXT,
    therapeutic_role TEXT,
    indication TEXT,
    contra_indication TEXT,
    drug_interactions TEXT,
    drug_classification TEXT,
    source_regulatory TEXT,
    last_updated DATE,
    search_vector TSVECTOR,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_snomed_generic_name ON snomed_generics USING gin(generic_name gin_trgm_ops);
CREATE INDEX idx_snomed_generic_search ON snomed_generics USING gin(search_vector);
CREATE INDEX idx_snomed_generic_indication ON snomed_generics USING gin(indication gin_trgm_ops) WHERE indication IS NOT NULL;

-- ============================================================================
-- 3. SNOMED Brands (89,447 records) - MAIN TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS snomed_brands (
    snomed_id BIGINT PRIMARY KEY,
    brand_name TEXT NOT NULL,
    product_id BIGINT,
    supplier_id BIGINT,
    generic_id BIGINT REFERENCES snomed_generics(snomed_id),
    license_number VARCHAR(100),
    license_status VARCHAR(20),
    excipient TEXT,
    last_updated DATE,
    search_vector TSVECTOR,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_snomed_brand_name ON snomed_brands USING gin(brand_name gin_trgm_ops);
CREATE INDEX idx_snomed_brand_search ON snomed_brands USING gin(search_vector);
CREATE INDEX idx_snomed_brand_generic ON snomed_brands(generic_id);
CREATE INDEX idx_snomed_brand_supplier ON snomed_brands(supplier_id);
CREATE INDEX idx_snomed_brand_product ON snomed_brands(product_id);
CREATE INDEX idx_snomed_brand_active ON snomed_brands(active) WHERE active = TRUE;

-- ============================================================================
-- 4. SNOMED Products (68,517 records)
-- ============================================================================
CREATE TABLE IF NOT EXISTS snomed_products (
    snomed_id BIGINT PRIMARY KEY,
    product_name TEXT NOT NULL,
    search_vector TSVECTOR,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_snomed_product_name ON snomed_products USING gin(product_name gin_trgm_ops);
CREATE INDEX idx_snomed_product_search ON snomed_products USING gin(search_vector);

-- ============================================================================
-- 5. SNOMED Suppliers/Manufacturers (7,935 records)
-- ============================================================================
CREATE TABLE IF NOT EXISTS snomed_suppliers (
    snomed_id BIGINT PRIMARY KEY,
    supplier_name TEXT NOT NULL,
    country VARCHAR(100),
    search_vector TSVECTOR,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_snomed_supplier_name ON snomed_suppliers USING gin(supplier_name gin_trgm_ops);
CREATE INDEX idx_snomed_supplier_search ON snomed_suppliers USING gin(search_vector);
CREATE INDEX idx_snomed_supplier_active ON snomed_suppliers(active) WHERE active = TRUE;

-- ============================================================================
-- 6. SNOMED Drug Forms (423 records)
-- ============================================================================
CREATE TABLE IF NOT EXISTS snomed_drug_forms (
    snomed_id BIGINT PRIMARY KEY,
    form_name TEXT NOT NULL,
    form_description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_snomed_form_name ON snomed_drug_forms(form_name);

-- ============================================================================
-- 7. SNOMED Routes of Administration (161 records)
-- ============================================================================
CREATE TABLE IF NOT EXISTS snomed_routes (
    snomed_id BIGINT PRIMARY KEY,
    route_name TEXT NOT NULL,
    route_description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_snomed_route_name ON snomed_routes(route_name);

-- ============================================================================
-- 8. Materialized View: Complete Drug Information (Performance Optimization)
-- ============================================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS snomed_drugs_complete AS
SELECT 
    b.snomed_id as brand_snomed_id,
    b.brand_name,
    b.license_status,
    b.active,
    g.snomed_id as generic_snomed_id,
    g.generic_name,
    g.indication,
    g.contra_indication,
    g.therapeutic_role,
    g.dose_form,
    p.product_name,
    s.supplier_name,
    s.country as manufacturer_country,
    b.search_vector as brand_search,
    g.search_vector as generic_search
FROM snomed_brands b
LEFT JOIN snomed_generics g ON b.generic_id = g.snomed_id
LEFT JOIN snomed_products p ON b.product_id = p.snomed_id
LEFT JOIN snomed_suppliers s ON b.supplier_id = s.snomed_id
WHERE b.active = TRUE;

CREATE UNIQUE INDEX idx_snomed_complete_brand_id ON snomed_drugs_complete(brand_snomed_id);
CREATE INDEX idx_snomed_complete_brand_name ON snomed_drugs_complete USING gin(brand_name gin_trgm_ops);
CREATE INDEX idx_snomed_complete_generic_name ON snomed_drugs_complete USING gin(generic_name gin_trgm_ops);
CREATE INDEX idx_snomed_complete_supplier ON snomed_drugs_complete USING gin(supplier_name gin_trgm_ops);

-- ============================================================================
-- Triggers: Auto-update search vectors
-- ============================================================================

CREATE OR REPLACE FUNCTION update_snomed_brand_search()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.brand_name, '')), 'A');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_snomed_generic_search()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.generic_name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.indication, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.therapeutic_role, '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_snomed_product_search()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.product_name, '')), 'A');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_snomed_supplier_search()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.supplier_name, '')), 'A');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop existing triggers if they exist
DROP TRIGGER IF EXISTS snomed_brand_search_update ON snomed_brands;
DROP TRIGGER IF EXISTS snomed_generic_search_update ON snomed_generics;
DROP TRIGGER IF EXISTS snomed_product_search_update ON snomed_products;
DROP TRIGGER IF EXISTS snomed_supplier_search_update ON snomed_suppliers;

-- Create triggers
CREATE TRIGGER snomed_brand_search_update
    BEFORE INSERT OR UPDATE ON snomed_brands
    FOR EACH ROW EXECUTE FUNCTION update_snomed_brand_search();

CREATE TRIGGER snomed_generic_search_update
    BEFORE INSERT OR UPDATE ON snomed_generics
    FOR EACH ROW EXECUTE FUNCTION update_snomed_generic_search();

CREATE TRIGGER snomed_product_search_update
    BEFORE INSERT OR UPDATE ON snomed_products
    FOR EACH ROW EXECUTE FUNCTION update_snomed_product_search();

CREATE TRIGGER snomed_supplier_search_update
    BEFORE INSERT OR UPDATE ON snomed_suppliers
    FOR EACH ROW EXECUTE FUNCTION update_snomed_supplier_search();

-- ============================================================================
-- Function: Refresh materialized view
-- ============================================================================
CREATE OR REPLACE FUNCTION refresh_snomed_complete_view()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY snomed_drugs_complete;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Statistics and Monitoring
-- ============================================================================
CREATE TABLE IF NOT EXISTS snomed_etl_log (
    log_id SERIAL PRIMARY KEY,
    table_name VARCHAR(50),
    records_loaded INTEGER,
    records_failed INTEGER,
    execution_time_ms INTEGER,
    status VARCHAR(20),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_snomed_etl_log_created ON snomed_etl_log(created_at DESC);

-- ============================================================================
-- Grant permissions (adjust as needed)
-- ============================================================================
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;
-- GRANT ALL ON ALL TABLES IN SCHEMA public TO app_user;

-- ============================================================================
-- Vacuum and Analyze
-- ============================================================================
VACUUM ANALYZE snomed_brands;
VACUUM ANALYZE snomed_generics;
VACUUM ANALYZE snomed_products;
VACUUM ANALYZE snomed_suppliers;
VACUUM ANALYZE snomed_substances;
