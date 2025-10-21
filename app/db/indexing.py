from sqlalchemy import text
from app.db.database import async_engine
import logging

logger = logging.getLogger(__name__)

class IndexManager:
    """Advanced indexing strategy for optimal query performance"""
    
    async def create_performance_indexes(self):
        """Create comprehensive indexing strategy"""
        
        async with async_engine.begin() as conn:
            
            # 1. Composite indexes for common query patterns
            indexes = [
                # Multi-column indexes for search patterns
                {
                    'name': 'idx_icd10_active_chapter_code',
                    'table': 'icd10_codes',
                    'columns': '(active, chapter, code)',
                    'condition': 'WHERE active = true'
                },
                {
                    'name': 'idx_icd10_term_active_billable',
                    'table': 'icd10_codes', 
                    'columns': '(term, active, billable)',
                    'condition': 'WHERE active = true AND billable = true'
                },
                
                # Partial indexes for performance
                {
                    'name': 'idx_icd10_code_prefix_active',
                    'table': 'icd10_codes',
                    'columns': '(substring(code, 1, 3), active)',
                    'condition': 'WHERE active = true'
                },
                
                # Full-text search indexes
                {
                    'name': 'idx_icd10_term_fulltext',
                    'table': 'icd10_codes',
                    'columns': 'USING GIN(to_tsvector(\'english\', term || \' \' || COALESCE(short_desc, \'\')))',
                    'condition': ''
                },
                
                # Similarity search indexes (requires pg_trgm extension)
                {
                    'name': 'idx_icd10_term_trigram',
                    'table': 'icd10_codes',
                    'columns': 'USING GIN(term gin_trgm_ops)',
                    'condition': ''
                },
                {
                    'name': 'idx_icd10_code_trigram',
                    'table': 'icd10_codes',
                    'columns': 'USING GIN(code gin_trgm_ops)',
                    'condition': ''
                },
                
                # Hierarchy navigation indexes
                {
                    'name': 'idx_icd10_parent_code_active',
                    'table': 'icd10_codes',
                    'columns': '(parent_code, active)',
                    'condition': 'WHERE parent_code IS NOT NULL AND active = true'
                },
                
                # Performance monitoring indexes
                {
                    'name': 'idx_search_logs_user_time',
                    'table': 'search_logs',
                    'columns': '(user_id, created_at DESC)',
                    'condition': ''
                },
                {
                    'name': 'idx_search_logs_query_hash',
                    'table': 'search_logs',
                    'columns': '(md5(query), created_at DESC)',
                    'condition': ''
                }
            ]
            
            # Create required extensions
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS btree_gin"))
            
            # Create all indexes
            for idx in indexes:
                try:
                    sql = f"""
                        CREATE INDEX CONCURRENTLY IF NOT EXISTS {idx['name']} 
                        ON {idx['table']} {idx['columns']} {idx['condition']}
                    """
                    await conn.execute(text(sql))
                    logger.info(f"Created index: {idx['name']}")
                except Exception as e:
                    logger.error(f"Failed to create index {idx['name']}: {e}")
    
    async def create_materialized_views(self):
        """Create materialized views for complex queries"""
        
        async with async_engine.begin() as conn:
            
            # Chapter statistics view
            await conn.execute(text("""
                CREATE MATERIALIZED VIEW IF NOT EXISTS mv_chapter_stats AS
                SELECT 
                    chapter,
                    COUNT(*) as total_codes,
                    COUNT(*) FILTER (WHERE active = true) as active_codes,
                    COUNT(*) FILTER (WHERE billable = true) as billable_codes,
                    MIN(code) as first_code,
                    MAX(code) as last_code
                FROM icd10_codes 
                GROUP BY chapter
                WITH DATA
            """))
            
            # Popular searches view
            await conn.execute(text("""
                CREATE MATERIALIZED VIEW IF NOT EXISTS mv_popular_searches AS
                SELECT 
                    query,
                    COUNT(*) as search_count,
                    AVG(response_time_ms) as avg_response_time,
                    AVG(results_count) as avg_results,
                    MAX(created_at) as last_searched
                FROM search_logs 
                WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY query
                HAVING COUNT(*) >= 5
                ORDER BY search_count DESC
                LIMIT 1000
                WITH DATA
            """))
            
            # Create indexes on materialized views
            await conn.execute(text("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_chapter_stats_chapter 
                ON mv_chapter_stats (chapter)
            """))
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_mv_popular_searches_count 
                ON mv_popular_searches (search_count DESC)
            """))
            
            logger.info("Created materialized views with indexes")
    
    async def setup_query_optimization(self):
        """Configure PostgreSQL for optimal query performance"""
        
        async with async_engine.begin() as conn:
            
            # Optimize PostgreSQL settings for search workload
            optimizations = [
                "SET shared_preload_libraries = 'pg_stat_statements'",
                "SET track_activity_query_size = 2048",
                "SET log_min_duration_statement = 1000",  # Log slow queries
                "SET log_checkpoints = on",
                "SET log_connections = on",
                "SET log_disconnections = on",
                "SET log_lock_waits = on",
                "SET deadlock_timeout = '1s'",
                "SET statement_timeout = '30s'",  # 30 second query timeout
                "SET idle_in_transaction_session_timeout = '10min'"
            ]
            
            for optimization in optimizations:
                try:
                    await conn.execute(text(optimization))
                    logger.info(f"Applied optimization: {optimization}")
                except Exception as e:
                    logger.warning(f"Could not apply optimization {optimization}: {e}")
    
    async def analyze_and_vacuum(self):
        """Maintain table statistics and cleanup"""
        
        async with async_engine.begin() as conn:
            
            tables = ['icd10_codes', 'icd11_codes', 'search_logs']
            
            for table in tables:
                # Update table statistics
                await conn.execute(text(f"ANALYZE {table}"))
                
                # Vacuum to reclaim space (non-blocking)
                await conn.execute(text(f"VACUUM (ANALYZE) {table}"))
                
                logger.info(f"Analyzed and vacuumed table: {table}")
            
            # Refresh materialized views
            await conn.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_chapter_stats"))
            await conn.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_popular_searches"))
            
            logger.info("Refreshed materialized views")

index_manager = IndexManager()