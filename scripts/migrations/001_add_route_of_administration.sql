-- Migration: Add route_of_administration to snomed_brands
-- Solves: Rectal cream showing for systemic conditions

BEGIN;

ALTER TABLE snomed_brands 
ADD COLUMN route_of_administration VARCHAR(50);

UPDATE snomed_brands
SET route_of_administration = CASE
    WHEN brand_name ILIKE '%oral tablet%' OR brand_name ILIKE '%oral capsule%' THEN 'oral'
    WHEN brand_name ILIKE '%tablet%' OR brand_name ILIKE '%capsule%' THEN 'oral'
    WHEN brand_name ILIKE '%syrup%' OR brand_name ILIKE '%suspension%' THEN 'oral'
    WHEN brand_name ILIKE '%injection%' OR brand_name ILIKE '%injectable%' THEN 'parenteral'
    WHEN brand_name ILIKE '%rectal%' THEN 'rectal'
    WHEN brand_name ILIKE '%topical%' OR brand_name ILIKE '%cream%' OR brand_name ILIKE '%ointment%' THEN 'topical'
    WHEN brand_name ILIKE '%eye drop%' OR brand_name ILIKE '%ophthalmic%' THEN 'ophthalmic'
    WHEN brand_name ILIKE '%inhaler%' OR brand_name ILIKE '%inhalation%' THEN 'inhalation'
    WHEN brand_name ILIKE '%nasal%' THEN 'nasal'
    WHEN brand_name ILIKE '%vaginal%' THEN 'vaginal'
    WHEN brand_name ILIKE '%transdermal%' OR brand_name ILIKE '%patch%' THEN 'transdermal'
    ELSE 'oral'
END;

CREATE INDEX idx_snomed_brand_route ON snomed_brands(route_of_administration);
CREATE INDEX idx_snomed_brand_generic_route ON snomed_brands(generic_id, route_of_administration) WHERE active = TRUE;

COMMIT;
