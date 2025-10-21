"""
ICD-11 API endpoints for HMS Terminology Service
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Optional
import asyncpg
from app.database import get_db_connection

router = APIRouter(prefix="/api/v1", tags=["ICD-11"])

@router.get("/autocomplete/icd11")
async def autocomplete_icd11(
    query: str = Query(..., min_length=2),
    limit: int = Query(10, le=50)
) -> List[Dict]:
    """ICD-11 autocomplete search"""
    conn = await get_db_connection()
    
    results = await conn.fetch("""
        SELECT code, title, definition, chapter,
               ts_rank(search_vector, plainto_tsquery('english', $1)) as rank
        FROM icd11_codes 
        WHERE search_vector @@ plainto_tsquery('english', $1)
           OR title ILIKE $2
           OR code ILIKE $2
        ORDER BY rank DESC, title
        LIMIT $3
    """, query, f"%{query}%", limit)
    
    await conn.close()
    
    return [
        {
            "code": row["code"],
            "title": row["title"],
            "definition": row["definition"],
            "chapter": row["chapter"],
            "relevance_score": float(row["rank"]) if row["rank"] else 0.0
        }
        for row in results
    ]

@router.get("/icd11/{code}")
async def get_icd11_code(code: str) -> Dict:
    """Get specific ICD-11 code details"""
    conn = await get_db_connection()
    
    result = await conn.fetchrow("""
        SELECT * FROM icd11_codes WHERE code = $1
    """, code)
    
    await conn.close()
    
    if not result:
        raise HTTPException(status_code=404, detail="ICD-11 code not found")
    
    return {
        "code": result["code"],
        "title": result["title"],
        "definition": result["definition"],
        "chapter": result["chapter"],
        "url": result["url"]
    }

@router.get("/enterprise/search/icd11/advanced")
async def advanced_icd11_search(
    query: str = Query(..., min_length=2),
    chapter: Optional[str] = None,
    fuzzy_threshold: float = Query(0.3, ge=0.0, le=1.0),
    limit: int = Query(20, le=100)
) -> Dict:
    """Advanced ICD-11 search with multiple algorithms"""
    conn = await get_db_connection()
    
    # Build dynamic query
    where_clause = "WHERE search_vector @@ plainto_tsquery('english', $1)"
    params = [query]
    
    if chapter:
        where_clause += " AND chapter ILIKE $2"
        params.append(f"%{chapter}%")
    
    results = await conn.fetch(f"""
        SELECT code, title, definition, chapter,
               ts_rank(search_vector, plainto_tsquery('english', $1)) as rank,
               similarity(title, $1) as similarity_score
        FROM icd11_codes 
        {where_clause}
        ORDER BY rank DESC, similarity_score DESC
        LIMIT ${len(params) + 1}
    """, *params, limit)
    
    await conn.close()
    
    return {
        "query": query,
        "total_results": len(results),
        "search_algorithm": "full_text_with_similarity",
        "results": [
            {
                "code": row["code"],
                "title": row["title"],
                "definition": row["definition"],
                "chapter": row["chapter"],
                "confidence_score": float(row["rank"]) + float(row["similarity_score"] or 0)
            }
            for row in results
        ]
    }