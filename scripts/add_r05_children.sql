-- Add R05 child codes
INSERT INTO icd10_codes (code, term, chapter, parent_code, active) VALUES
('R051', 'Acute cough', 'Cough', 'R05', true),
('R052', 'Subacute cough', 'Cough', 'R05', true),
('R053', 'Chronic cough', 'Cough', 'R05', true),
('R054', 'Cough syncope', 'Cough', 'R05', true),
('R058', 'Other specified cough', 'Cough', 'R05', true),
('R059', 'Cough, unspecified', 'Cough', 'R05', true)
ON CONFLICT (code) DO NOTHING;
