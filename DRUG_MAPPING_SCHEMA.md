# 💊 Drug Mapping Architecture: Indian Brand ↔ RxNorm ↔ Generic

## 🎯 Mapping Strategy

```
Indian Brand Name → RxNorm CUI → Generic Ingredient → International Standards
     ↓                  ↓              ↓                      ↓
  Crocin          RX:202433      Paracetamol           ATC: N02BE01
  Dolo 650        RX:202433      Paracetamol           ATC: N02BE01
  Calpol          RX:202433      Paracetamol           ATC: N02BE01
     ↓                  ↓              ↓                      ↓
  All map to same generic ingredient via RxNorm CUI
```

## 📊 Database Schema

### **1. Generic Ingredients (Master Table)**

```sql
CREATE TABLE generic_ingredients (
    ingredient_id SERIAL PRIMARY KEY,
    
    -- Standard identifiers
    rxnorm_cui VARCHAR(20) UNIQUE,  -- RxNorm Concept Unique Identifier
    ingredient_name VARCHAR(200) NOT NULL,
    
    -- International standards
    atc_code VARCHAR(20),  -- WHO Anatomical Therapeutic Chemical
    cas_number VARCHAR(50),  -- Chemical Abstracts Service
    unii VARCHAR(20),  -- FDA Unique Ingredient Identifier
    
    -- Classification
    therapeutic_class VARCHAR(100),
    pharmacological_class VARCHAR(100),
    drug_category VARCHAR(50),  -- 'antibiotic', 'analgesic', etc.
    
    -- Multi-language
    ingredient_name_hindi TEXT,
    ingredient_name_tamil TEXT,
    ingredient_name_telugu TEXT,
    
    -- Search
    search_vector TSVECTOR,
    
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_rxnorm_cui ON generic_ingredients(rxnorm_cui);
CREATE INDEX idx_atc_code ON generic_ingredients(atc_code);
CREATE INDEX idx_ingredient_search ON generic_ingredients USING gin(search_vector);

-- Sample data
INSERT INTO generic_ingredients (rxnorm_cui, ingredient_name, atc_code, therapeutic_class) VALUES
('202433', 'Acetaminophen', 'N02BE01', 'Analgesic/Antipyretic'),
('6809', 'Metformin', 'A10BA02', 'Antidiabetic'),
('36567', 'Simvastatin', 'C10AA01', 'Lipid Lowering Agent'),
('3521', 'Amlodipine', 'C08CA01', 'Calcium Channel Blocker'),
('8640', 'Omeprazole', 'A02BC01', 'Proton Pump Inhibitor');
```

### **2. Indian Brand Drugs**

```sql
CREATE TABLE indian_brand_drugs (
    brand_id SERIAL PRIMARY KEY,
    
    -- Brand information
    brand_name VARCHAR(200) NOT NULL,
    manufacturer VARCHAR(200),
    
    -- Link to generic ingredient
    ingredient_id INTEGER REFERENCES generic_ingredients(ingredient_id),
    rxnorm_cui VARCHAR(20),  -- Denormalized for quick lookup
    
    -- Formulation
    strength VARCHAR(50),  -- '500mg', '10mg/ml'
    dosage_form VARCHAR(50),  -- 'Tablet', 'Syrup', 'Injection'
    route VARCHAR(50),  -- 'Oral', 'IV', 'Topical'
    
    -- Indian-specific
    schedule VARCHAR(10),  -- 'H', 'H1', 'X' (narcotic control)
    cdsco_approval VARCHAR(50),
    
    -- Pricing
    mrp DECIMAL(10,2),
    pack_size VARCHAR(50),  -- '10 tablets', '100ml'
    
    -- Availability
    prescription_required BOOLEAN,
    otc_available BOOLEAN,
    
    -- Multi-language
    brand_name_hindi TEXT,
    brand_name_tamil TEXT,
    
    -- Search
    search_vector TSVECTOR,
    
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_brand_ingredient ON indian_brand_drugs(ingredient_id);
CREATE INDEX idx_brand_rxnorm ON indian_brand_drugs(rxnorm_cui);
CREATE INDEX idx_brand_name ON indian_brand_drugs(brand_name);
CREATE INDEX idx_brand_search ON indian_brand_drugs USING gin(search_vector);

-- Sample data: Multiple brands for same generic
INSERT INTO indian_brand_drugs (brand_name, manufacturer, ingredient_id, rxnorm_cui, strength, dosage_form, mrp, pack_size) VALUES
('Crocin', 'GSK', 1, '202433', '500mg', 'Tablet', 15.00, '10 tablets'),
('Dolo 650', 'Micro Labs', 1, '202433', '650mg', 'Tablet', 30.00, '15 tablets'),
('Calpol', 'GSK', 1, '202433', '250mg/5ml', 'Syrup', 45.00, '60ml'),
('Metacin', 'Cipla', 1, '202433', '500mg', 'Tablet', 12.00, '10 tablets'),

('Glycomet', 'USV', 2, '6809', '500mg', 'Tablet', 25.00, '10 tablets'),
('Glucophage', 'Merck', 2, '6809', '500mg', 'Tablet', 35.00, '10 tablets'),
('Metsmall', 'Ajanta', 2, '6809', '500mg', 'Tablet', 20.00, '10 tablets');
```

### **3. Combination Drugs**

```sql
CREATE TABLE combination_drugs (
    combination_id SERIAL PRIMARY KEY,
    brand_name VARCHAR(200) NOT NULL,
    manufacturer VARCHAR(200),
    
    -- Multiple ingredients
    ingredients JSONB,  -- Array of {ingredient_id, rxnorm_cui, strength}
    
    -- Formulation
    dosage_form VARCHAR(50),
    
    -- Pricing
    mrp DECIMAL(10,2),
    pack_size VARCHAR(50),
    
    -- Search
    search_vector TSVECTOR,
    
    active BOOLEAN DEFAULT TRUE
);

-- Sample: Combination drugs
INSERT INTO combination_drugs (brand_name, manufacturer, ingredients, dosage_form, mrp, pack_size) VALUES
(
    'Telma-AM',
    'Glenmark',
    '[
        {"ingredient_id": 4, "rxnorm_cui": "3521", "ingredient_name": "Amlodipine", "strength": "5mg"},
        {"ingredient_id": 5, "rxnorm_cui": "38413", "ingredient_name": "Telmisartan", "strength": "40mg"}
    ]'::jsonb,
    'Tablet',
    85.00,
    '10 tablets'
),
(
    'Glimestar-M',
    'Lupin',
    '[
        {"ingredient_id": 2, "rxnorm_cui": "6809", "ingredient_name": "Metformin", "strength": "500mg"},
        {"ingredient_id": 6, "rxnorm_cui": "25789", "ingredient_name": "Glimepiride", "strength": "2mg"}
    ]'::jsonb,
    'Tablet',
    95.00,
    '15 tablets'
);

-- Index for JSONB search
CREATE INDEX idx_combination_ingredients ON combination_drugs USING gin(ingredients);
```

### **4. RxNorm Mapping Table (for updates)**

```sql
CREATE TABLE rxnorm_mappings (
    mapping_id SERIAL PRIMARY KEY,
    
    -- RxNorm identifiers
    rxnorm_cui VARCHAR(20) NOT NULL,
    rxnorm_name VARCHAR(200),
    rxnorm_tty VARCHAR(20),  -- Term Type: IN (ingredient), BN (brand name), etc.
    
    -- Relationships
    ingredient_id INTEGER REFERENCES generic_ingredients(ingredient_id),
    
    -- Source tracking
    source VARCHAR(50),  -- 'rxnorm', 'manual', 'verified'
    last_updated TIMESTAMP DEFAULT NOW(),
    
    active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_rxnorm_mapping_cui ON rxnorm_mappings(rxnorm_cui);
```

---

## 🔍 API Endpoints

### **1. Search by Brand Name → Get Generic**

```python
GET /api/v1/drugs/brand/search?query=crocin

Response:
{
    "brand_name": "Crocin",
    "manufacturer": "GSK",
    "generic_ingredient": {
        "ingredient_id": 1,
        "ingredient_name": "Acetaminophen",
        "rxnorm_cui": "202433",
        "atc_code": "N02BE01",
        "therapeutic_class": "Analgesic/Antipyretic"
    },
    "strength": "500mg",
    "dosage_form": "Tablet",
    "mrp": 15.00,
    "alternatives": [
        {"brand_name": "Dolo 650", "mrp": 30.00},
        {"brand_name": "Calpol", "mrp": 45.00},
        {"brand_name": "Metacin", "mrp": 12.00}
    ]
}
```

### **2. Search by Generic → Get All Brands**

```python
GET /api/v1/drugs/generic/acetaminophen

Response:
{
    "ingredient_name": "Acetaminophen",
    "rxnorm_cui": "202433",
    "atc_code": "N02BE01",
    "therapeutic_class": "Analgesic/Antipyretic",
    "available_brands": [
        {
            "brand_name": "Crocin",
            "manufacturer": "GSK",
            "strength": "500mg",
            "dosage_form": "Tablet",
            "mrp": 15.00,
            "pack_size": "10 tablets"
        },
        {
            "brand_name": "Dolo 650",
            "manufacturer": "Micro Labs",
            "strength": "650mg",
            "dosage_form": "Tablet",
            "mrp": 30.00,
            "pack_size": "15 tablets"
        },
        {
            "brand_name": "Metacin",
            "manufacturer": "Cipla",
            "strength": "500mg",
            "dosage_form": "Tablet",
            "mrp": 12.00,
            "pack_size": "10 tablets"
        }
    ],
    "cheapest_option": {
        "brand_name": "Metacin",
        "mrp": 12.00,
        "savings": "20% cheaper than average"
    }
}
```

### **3. Search by RxNorm CUI**

```python
GET /api/v1/drugs/rxnorm/202433

Response:
{
    "rxnorm_cui": "202433",
    "ingredient_name": "Acetaminophen",
    "atc_code": "N02BE01",
    "indian_brands_count": 15,
    "indian_brands": [...],
    "international_names": [
        "Paracetamol (UK/India)",
        "Acetaminophen (US)",
        "Tylenol (Brand - US)"
    ]
}
```

### **4. Find Cheaper Alternatives**

```python
POST /api/v1/drugs/alternatives
{
    "brand_name": "Dolo 650",
    "max_price": 20.00
}

Response:
{
    "original_drug": {
        "brand_name": "Dolo 650",
        "generic": "Acetaminophen",
        "mrp": 30.00
    },
    "cheaper_alternatives": [
        {
            "brand_name": "Metacin",
            "manufacturer": "Cipla",
            "mrp": 12.00,
            "savings": 18.00,
            "savings_percent": 60,
            "same_strength": true,
            "same_form": true
        },
        {
            "brand_name": "Crocin",
            "manufacturer": "GSK",
            "mrp": 15.00,
            "savings": 15.00,
            "savings_percent": 50,
            "same_strength": true,
            "same_form": true
        }
    ]
}
```

### **5. Drug Substitution Check**

```python
POST /api/v1/drugs/substitution-check
{
    "prescribed_brand": "Crocin",
    "available_brand": "Dolo 650"
}

Response:
{
    "substitutable": true,
    "reason": "Same generic ingredient (Acetaminophen)",
    "rxnorm_cui": "202433",
    "differences": {
        "strength": "Dolo 650 has higher strength (650mg vs 500mg)",
        "dosage_adjustment": "Reduce frequency if substituting"
    },
    "pharmacist_note": "Bioequivalent - safe to substitute with dosage adjustment"
}
```

### **6. Multi-language Search**

```python
GET /api/v1/drugs/search?query=पेरासिटामोल&language=hi

Response:
{
    "detected_language": "hi",
    "search_term": "पेरासिटामोल",
    "english_term": "Paracetamol",
    "rxnorm_cui": "202433",
    "results": [
        {
            "brand_name": "Crocin",
            "brand_name_hindi": "क्रोसिन",
            "generic_name": "Acetaminophen",
            "generic_name_hindi": "पेरासिटामोल",
            "mrp": 15.00
        }
    ]
}
```

---

## 🔄 Data Population Strategy

### **Phase 1: Core Generic Ingredients (Week 1-2)**

```python
# Import RxNorm ingredient data
# Source: https://www.nlm.nih.gov/research/umls/rxnorm/

import requests
import psycopg2

def import_rxnorm_ingredients():
    """Import top 500 generic ingredients from RxNorm"""
    
    # RxNorm REST API
    base_url = "https://rxnav.nlm.nih.gov/REST"
    
    # Top generic ingredients
    common_ingredients = [
        'Acetaminophen', 'Metformin', 'Amlodipine', 'Simvastatin',
        'Omeprazole', 'Atorvastatin', 'Losartan', 'Levothyroxine',
        'Aspirin', 'Ibuprofen', 'Amoxicillin', 'Azithromycin'
        # ... 500 total
    ]
    
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    for ingredient in common_ingredients:
        # Get RxNorm CUI
        response = requests.get(
            f"{base_url}/rxcui.json?name={ingredient}&search=2"
        )
        data = response.json()
        
        if 'idGroup' in data and 'rxnormId' in data['idGroup']:
            rxnorm_cui = data['idGroup']['rxnormId'][0]
            
            # Get ATC code
            atc_response = requests.get(
                f"{base_url}/rxclass/class/byRxcui.json?rxcui={rxnorm_cui}&relaSource=ATC"
            )
            atc_data = atc_response.json()
            atc_code = atc_data.get('rxclassMinConceptList', {}).get('rxclassMinConcept', [{}])[0].get('classId')
            
            # Insert into database
            cursor.execute("""
                INSERT INTO generic_ingredients 
                (rxnorm_cui, ingredient_name, atc_code)
                VALUES (%s, %s, %s)
                ON CONFLICT (rxnorm_cui) DO NOTHING
            """, (rxnorm_cui, ingredient, atc_code))
    
    conn.commit()
    cursor.close()
    conn.close()

# Run import
import_rxnorm_ingredients()
```

### **Phase 2: Indian Brand Mapping (Week 3-4)**

```python
def import_indian_brands():
    """Import Indian brand drugs and map to RxNorm"""
    
    # Source: MIMS India, CIMS, or manual curation
    indian_brands = [
        {
            'brand_name': 'Crocin',
            'manufacturer': 'GSK',
            'generic_name': 'Acetaminophen',
            'strength': '500mg',
            'dosage_form': 'Tablet',
            'mrp': 15.00,
            'pack_size': '10 tablets'
        },
        # ... thousands more
    ]
    
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    for brand in indian_brands:
        # Find RxNorm CUI for generic
        cursor.execute("""
            SELECT ingredient_id, rxnorm_cui 
            FROM generic_ingredients 
            WHERE LOWER(ingredient_name) = LOWER(%s)
        """, (brand['generic_name'],))
        
        result = cursor.fetchone()
        if result:
            ingredient_id, rxnorm_cui = result
            
            # Insert brand
            cursor.execute("""
                INSERT INTO indian_brand_drugs 
                (brand_name, manufacturer, ingredient_id, rxnorm_cui, 
                 strength, dosage_form, mrp, pack_size)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                brand['brand_name'], brand['manufacturer'],
                ingredient_id, rxnorm_cui,
                brand['strength'], brand['dosage_form'],
                brand['mrp'], brand['pack_size']
            ))
    
    conn.commit()
    cursor.close()
    conn.close()
```

### **Phase 3: Multi-language Translation (Week 5-6)**

```python
def add_hindi_translations():
    """Add Hindi translations for common drugs"""
    
    translations = {
        'Acetaminophen': 'पेरासिटामोल',
        'Metformin': 'मेटफॉर्मिन',
        'Amlodipine': 'एम्लोडिपिन',
        # ... more
    }
    
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    for english, hindi in translations.items():
        cursor.execute("""
            UPDATE generic_ingredients 
            SET ingredient_name_hindi = %s
            WHERE ingredient_name = %s
        """, (hindi, english))
    
    conn.commit()
    cursor.close()
    conn.close()
```

---

## 📊 Sample Queries

### **Query 1: Find all brands for a generic**

```sql
SELECT 
    gi.ingredient_name,
    gi.rxnorm_cui,
    ibd.brand_name,
    ibd.manufacturer,
    ibd.strength,
    ibd.mrp,
    ibd.pack_size
FROM generic_ingredients gi
JOIN indian_brand_drugs ibd ON gi.ingredient_id = ibd.ingredient_id
WHERE gi.ingredient_name = 'Acetaminophen'
ORDER BY ibd.mrp ASC;
```

### **Query 2: Find cheapest alternative**

```sql
WITH brand_generic AS (
    SELECT ingredient_id, rxnorm_cui
    FROM indian_brand_drugs
    WHERE brand_name = 'Dolo 650'
)
SELECT 
    ibd.brand_name,
    ibd.manufacturer,
    ibd.strength,
    ibd.mrp,
    ibd.pack_size
FROM indian_brand_drugs ibd
JOIN brand_generic bg ON ibd.ingredient_id = bg.ingredient_id
WHERE ibd.active = true
ORDER BY ibd.mrp ASC
LIMIT 5;
```

### **Query 3: Check drug substitution**

```sql
SELECT 
    b1.brand_name as prescribed,
    b2.brand_name as available,
    gi.ingredient_name as generic,
    gi.rxnorm_cui,
    CASE 
        WHEN b1.ingredient_id = b2.ingredient_id THEN 'Substitutable'
        ELSE 'Not Substitutable'
    END as substitution_status
FROM indian_brand_drugs b1
CROSS JOIN indian_brand_drugs b2
JOIN generic_ingredients gi ON b1.ingredient_id = gi.ingredient_id
WHERE b1.brand_name = 'Crocin'
  AND b2.brand_name = 'Dolo 650';
```

---

## 🎯 Benefits of This Architecture

### ✅ **Advantages**

1. **Standardization**: RxNorm CUI provides global standard
2. **Interoperability**: Can map to international drug databases
3. **Cost Savings**: Easy to find cheaper alternatives
4. **Drug Safety**: Check substitutability accurately
5. **Multi-language**: Support regional languages
6. **Scalability**: Add new brands without changing structure
7. **Analytics**: Track generic vs brand prescribing patterns

### 📊 **Use Cases**

```
1. Doctor prescribes "Crocin"
   → System shows: Generic = Acetaminophen (RxNorm: 202433)
   → Suggests cheaper alternatives: Metacin (₹12 vs ₹15)

2. Pharmacy has "Dolo 650" but prescription says "Crocin"
   → System checks: Same RxNorm CUI (202433)
   → Confirms: Substitutable (with dosage note)

3. Patient searches in Hindi: "बुखार की दवा"
   → System translates: "fever medicine"
   → Returns: Acetaminophen brands with Hindi names

4. Insurance claim validation
   → Check if prescribed brand matches approved generic
   → Verify pricing against NPPA ceiling
```

---

## 🚀 Implementation Timeline

```
Week 1-2: Setup schema + Import 500 generic ingredients
Week 3-4: Import 5,000 Indian brands + Map to RxNorm
Week 5-6: Add Hindi translations for top 500 drugs
Week 7-8: Build API endpoints + Testing
Week 9-10: Add combination drugs + Drug interactions
Week 11-12: Production deployment + Monitoring

Total: 12 weeks to production-ready drug mapping system
```

---

## 💡 Key Insight

This architecture gives you:
- **Indian Brand** → Local market relevance
- **RxNorm CUI** → Global standardization
- **Generic Ingredient** → Clinical accuracy
- **Multi-language** → Market penetration

**Perfect for Indian market with international standards!**
