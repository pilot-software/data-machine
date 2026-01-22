# Implementation Plan

## 🎯 Goal
Transform keyword search → semantic search with learning capability

**Timeline:** 6 weeks  
**Cost:** $0 → $100/mo (gradual)  
**Team:** 1-2 developers

---

## 📅 Week-by-Week Plan

### Week 1: Quick Wins (8 hours)

#### Day 1-2: Add Confidence Scoring (4 hours)
```python
# app/services/therapeutic_search.py

def calculate_confidence(drug, diagnosis):
    score = 0.0
    
    # Exact indication match
    if diagnosis.lower() in (drug.get('indication') or '').lower():
        score += 0.5
    
    # First-line therapy
    if is_first_line(drug, diagnosis):
        score += 0.3
    
    # Safety score
    if no_contraindications(drug):
        score += 0.2
    
    return round(score, 2)

# Add to each drug
for drug in drugs:
    drug['confidence_score'] = calculate_confidence(drug, diagnosis)
    drug['match_reason'] = explain_match(drug, diagnosis)

# Sort by confidence
drugs = sorted(drugs, key=lambda x: x['confidence_score'], reverse=True)
```

**Test:**
```bash
curl -X POST "http://localhost:8001/api/v1/clinical-ai/diagnose-text" \
  -H "X-API-Key: dev-key-123" \
  -d '{"prompt": "medicine for sugar"}'

# Should see confidence_score in response
```

---

#### Day 3-4: Add Safety Endpoints (4 hours)
```python
# app/api/safety_endpoints.py

@router.post("/interactions/check")
async def check_interactions(drugs: List[str]):
    interactions = []
    
    # Basic checks
    if "aspirin" in drugs and "ibuprofen" in drugs:
        interactions.append({
            "drugs": ["aspirin", "ibuprofen"],
            "severity": "moderate",
            "description": "Increased bleeding risk"
        })
    
    return {"interactions": interactions}

@router.post("/prescriptions/validate")
async def validate_prescription(drugs: List[dict], patient: dict):
    errors = []
    
    # Check allergies
    for drug in drugs:
        if drug["name"] in patient.get("allergies", []):
            errors.append(f"Patient allergic to {drug['name']}")
    
    return {"valid": len(errors) == 0, "errors": errors}
```

**Deliverable:** 2 new safety endpoints

---

### Week 2: Vector DB Setup (12 hours)

#### Day 1: Setup Pinecone (2 hours)
```bash
# Sign up: https://app.pinecone.io/
# Get free tier API key

# Add to .env
PINECONE_API_KEY=your-key
PINECONE_ENVIRONMENT=gcp-starter
OPENAI_API_KEY=your-key

# Install
pip install pinecone-client==3.0.0 openai==1.0.0
```

```python
# scripts/setup_vector_db.py
from pinecone import Pinecone, ServerlessSpec
import os

pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))

pc.create_index(
    name="hms-drugs",
    dimension=1536,
    metric="cosine",
    spec=ServerlessSpec(cloud='aws', region='us-east-1')
)
```

---

#### Day 2-3: Create Embedding Service (6 hours)
```python
# app/services/embedding_service.py
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def embed_text(text: str):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

def embed_batch(texts: list):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=texts
    )
    return [item.embedding for item in response.data]
```

---

#### Day 4-5: Embed Drug Catalog (4 hours)
```python
# scripts/embed_drugs.py
from app.db.database import SessionLocal
from app.services.embedding_service import embed_batch
from pinecone import Pinecone
from sqlalchemy import text
import os

db = SessionLocal()
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index = pc.Index("hms-drugs")

# Fetch drugs
drugs = db.execute(text("""
    SELECT brand_snomed_id, brand_name, generic_name, indication
    FROM snomed_drugs_complete
    WHERE active = TRUE
    LIMIT 10000  -- Start with 10K
""")).fetchall()

# Embed in batches
batch_size = 100
for i in range(0, len(drugs), batch_size):
    batch = drugs[i:i+batch_size]
    
    texts = [
        f"{d.brand_name} - {d.generic_name}. Used for: {d.indication or 'general use'}"
        for d in batch
    ]
    
    embeddings = embed_batch(texts)
    
    vectors = [
        {
            "id": f"drug_{d.brand_snomed_id}",
            "values": embedding,
            "metadata": {
                "snomed_id": d.brand_snomed_id,
                "brand_name": d.brand_name,
                "generic_name": d.generic_name
            }
        }
        for d, embedding in zip(batch, embeddings)
    ]
    
    index.upsert(vectors=vectors)
    print(f"Embedded {i+len(batch)}/{len(drugs)}")
```

**Run:**
```bash
python scripts/embed_drugs.py
# Takes 30-60 minutes for 10K drugs
```

---

### Week 3: Semantic Search (8 hours)

#### Day 1-3: Add Semantic Search Endpoint (6 hours)
```python
# app/api/snomed_endpoints.py
from app.services.embedding_service import embed_text
from pinecone import Pinecone
import os

pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index = pc.Index("hms-drugs")

@router.get("/semantic-search")
async def semantic_search(
    q: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    # Generate embedding
    embedding = embed_text(q)
    
    # Search vector DB
    results = index.query(
        vector=embedding,
        top_k=limit,
        include_metadata=True
    )
    
    # Get full data from DB
    snomed_ids = [int(r.metadata['snomed_id']) for r in results.matches]
    
    drugs = db.execute(text("""
        SELECT * FROM snomed_drugs_complete
        WHERE brand_snomed_id = ANY(:ids)
    """), {"ids": snomed_ids}).fetchall()
    
    # Add similarity scores
    drug_map = {d.brand_snomed_id: dict(d._mapping) for d in drugs}
    
    enriched = []
    for match in results.matches:
        snomed_id = int(match.metadata['snomed_id'])
        if snomed_id in drug_map:
            drug = drug_map[snomed_id]
            drug['similarity_score'] = round(match.score, 3)
            enriched.append(drug)
    
    return {
        "query": q,
        "results": enriched
    }
```

---

#### Day 4-5: A/B Testing (2 hours)
```python
# app/middleware/ab_testing.py
import random

async def ab_test_middleware(request, call_next):
    variant = "A" if random.random() < 0.5 else "B"
    request.state.ab_variant = variant
    response = await call_next(request)
    response.headers["X-AB-Variant"] = variant
    return response

# In search endpoint
@router.get("/search")
async def search(q: str, request: Request):
    if request.state.ab_variant == "B":
        return semantic_search(q)  # New
    else:
        return keyword_search(q)   # Old
```

**Test:**
```bash
# Test semantic search
curl "http://localhost:8001/api/v1/snomed/semantic-search?q=medicine%20for%20sugar"

# Should return diabetes drugs even without keyword "sugar"
```

---

### Week 4: LangChain Agent (12 hours)

#### Day 1-3: Create Agent Tools (8 hours)
```python
# app/services/langchain_tools.py
from langchain.tools import Tool
from langchain.agents import initialize_agent
from langchain_openai import ChatOpenAI
import os

def search_drugs_tool(query: str) -> str:
    """Search drugs semantically"""
    embedding = embed_text(query)
    results = index.query(vector=embedding, top_k=5)
    return "\n".join([r.metadata['brand_name'] for r in results.matches])

def search_icd_tool(query: str) -> str:
    """Search ICD codes"""
    db = SessionLocal()
    results = db.execute(text("""
        SELECT code, term FROM icd10_codes
        WHERE term ILIKE :q LIMIT 3
    """), {"q": f"%{query}%"}).fetchall()
    return "\n".join([f"{r.code}: {r.term}" for r in results])

tools = [
    Tool(name="SearchDrugs", func=search_drugs_tool, 
         description="Search drugs by symptoms or condition"),
    Tool(name="SearchICD", func=search_icd_tool,
         description="Search ICD codes for diagnosis")
]

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3)
agent = initialize_agent(tools, llm, agent="conversational-react-description")
```

---

#### Day 4-5: Add Agent Endpoint (4 hours)
```python
# app/api/clinical_ai_endpoints.py
from app.services.langchain_tools import agent

@router.post("/agent-diagnose")
async def agent_diagnose(query: str):
    response = agent.run(query)
    return {
        "query": query,
        "response": response,
        "agent_type": "langchain"
    }
```

**Test:**
```bash
curl -X POST "http://localhost:8001/api/v1/clinical-ai/agent-diagnose" \
  -H "X-API-Key: dev-key-123" \
  -d '{"query": "35yo with fever and cough, suggest treatment"}'
```

---

### Week 5: Case Memory (8 hours)

#### Day 1-3: Implement Case Storage (6 hours)
```python
# app/services/case_memory.py
from app.services.embedding_service import embed_text
from pinecone import Pinecone
import json

pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index = pc.Index("hms-drugs")

def store_case(symptoms: str, diagnosis: str, drugs: list):
    case_text = f"Symptoms: {symptoms}. Diagnosis: {diagnosis}. Drugs: {', '.join(drugs)}"
    embedding = embed_text(case_text)
    
    index.upsert(vectors=[{
        "id": f"case_{hash(case_text)}",
        "values": embedding,
        "metadata": {
            "type": "case",
            "symptoms": symptoms,
            "diagnosis": diagnosis,
            "drugs": json.dumps(drugs)
        }
    }])

def retrieve_similar_cases(symptoms: str, limit: int = 3):
    embedding = embed_text(symptoms)
    results = index.query(
        vector=embedding,
        top_k=limit,
        filter={"type": "case"}
    )
    return [r.metadata for r in results.matches]
```

---

#### Day 4-5: Integrate with Agent (2 hours)
```python
# Update agent endpoint
@router.post("/agent-diagnose-with-memory")
async def agent_diagnose_with_memory(query: str):
    # Retrieve similar cases
    similar_cases = retrieve_similar_cases(query)
    
    # Add context
    context = f"Similar past cases: {similar_cases}\n\nCurrent: {query}"
    
    # Run agent
    response = agent.run(context)
    
    # Store this case
    store_case(query, "extracted_diagnosis", ["extracted_drugs"])
    
    return {
        "query": query,
        "response": response,
        "similar_cases": similar_cases
    }
```

---

### Week 6: Production (8 hours)

#### Day 1-2: Optimization (4 hours)
- Add Redis caching for embeddings
- Optimize vector search queries
- Load test (1000 req/min)

#### Day 3: Security Audit (2 hours)
- Review API key management
- Check data privacy
- Implement rate limiting

#### Day 4-5: Deploy (2 hours)
```bash
# Update .env in production
# Deploy
git push origin main
./deploy.sh

# Monitor
tail -f logs/app.log
```

---

## 📊 Success Metrics

| Week | Deliverable | Metric |
|------|-------------|--------|
| 1 | Confidence scoring | User satisfaction +10% |
| 2 | Vector DB setup | 10K drugs embedded |
| 3 | Semantic search | Accuracy 60% → 85% |
| 4 | LangChain agent | Complex queries working |
| 5 | Case memory | Learning from past cases |
| 6 | Production | 95% accuracy, <300ms response |

---

## 💰 Budget

| Week | Component | Cost |
|------|-----------|------|
| 1-2 | Development | $0 |
| 3 | Pinecone (free) | $0 |
| 4 | OpenAI Embeddings | $10 |
| 5 | Pinecone (paid) | $70 |
| 6 | Production | $20 |
| **Total** | | **$100/mo** |

---

## 🚀 Quick Start

### Today (1 hour)
```bash
# 1. Add confidence scoring
# Edit: app/services/therapeutic_search.py
# Add calculate_confidence() function

# 2. Test
curl -X POST "http://localhost:8001/api/v1/clinical-ai/diagnose-text" \
  -d '{"prompt": "medicine for sugar"}'
```

### This Week (8 hours)
```bash
# 1. Add safety endpoints
# 2. Setup Pinecone
# 3. Embed 10K drugs
```

### Next Month (40 hours)
```bash
# 1. Semantic search (Week 3)
# 2. LangChain agent (Week 4)
# 3. Case memory (Week 5)
# 4. Production (Week 6)
```

---

## ✅ Checklist

### Week 1
- [ ] Add confidence scoring
- [ ] Add drug interaction endpoint
- [ ] Add prescription validation endpoint

### Week 2
- [ ] Setup Pinecone account
- [ ] Create embedding service
- [ ] Embed 10K drugs

### Week 3
- [ ] Add semantic search endpoint
- [ ] Setup A/B testing
- [ ] Test accuracy improvement

### Week 4
- [ ] Create LangChain tools
- [ ] Add agent endpoint
- [ ] Test complex queries

### Week 5
- [ ] Implement case storage
- [ ] Add case retrieval
- [ ] Test learning capability

### Week 6
- [ ] Optimize performance
- [ ] Security audit
- [ ] Production deployment

---

## 🆘 Troubleshooting

**Issue:** Pinecone quota exceeded  
**Solution:** Use free tier (100K vectors) or local Qdrant

**Issue:** Slow embeddings  
**Solution:** Use `sentence-transformers` for local embeddings

**Issue:** High costs  
**Solution:** Cache embeddings in Redis, use free tier Ollama

---

**Start with Week 1 tasks today!**
