from sqlalchemy import text, MetaData, Table
from app.db.database import engine, async_engine
import logging

logger = logging.getLogger(__name__)

class DatabasePartitionManager:
    """Manage database partitioning for large datasets"""
    
    def __init__(self):
        self.metadata = MetaData()
    
    async def create_icd10_partitions(self):
        """Create partitions for ICD-10 codes by chapter"""
        
        partitions = [
            ('A00', 'B99', 'infectious_parasitic'),
            ('C00', 'D89', 'neoplasms_blood'),
            ('E00', 'E89', 'endocrine_metabolic'),
            ('F01', 'F99', 'mental_behavioral'),
            ('G00', 'G99', 'nervous_system'),
            ('H00', 'H95', 'eye_ear'),
            ('I00', 'I99', 'circulatory'),
            ('J00', 'J99', 'respiratory'),
            ('K00', 'K95', 'digestive'),
            ('L00', 'L99', 'skin_subcutaneous'),
            ('M00', 'M99', 'musculoskeletal'),
            ('N00', 'N99', 'genitourinary'),
            ('O00', 'O9A', 'pregnancy_childbirth'),
            ('P00', 'P96', 'perinatal'),
            ('Q00', 'Q99', 'congenital'),
            ('R00', 'R99', 'symptoms_signs'),
            ('S00', 'T88', 'injury_poisoning'),
            ('V01', 'Y99', 'external_causes'),
            ('Z00', 'Z99', 'health_factors')
        ]
        
        async with async_engine.begin() as conn:
            # Create master table if not exists
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS icd10_master (
                    id SERIAL,
                    code VARCHAR(20) NOT NULL,
                    term TEXT NOT NULL,
                    short_desc TEXT,
                    chapter TEXT,
                    category VARCHAR(10),
                    parent_code VARCHAR(20),
                    active BOOLEAN DEFAULT TRUE,
                    billable BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) PARTITION BY RANGE (code)
            """))
            
            # Create partitions
            for start_code, end_code, partition_name in partitions:
                partition_table = f"icd10_{partition_name}"
                
                await conn.execute(text(f"""
                    CREATE TABLE IF NOT EXISTS {partition_table} 
                    PARTITION OF icd10_master 
                    FOR VALUES FROM ('{start_code}') TO ('{end_code}Z')
                """))
                
                # Create indexes on each partition
                await conn.execute(text(f"""
                    CREATE INDEX IF NOT EXISTS idx_{partition_name}_code 
                    ON {partition_table} (code)
                """))
                
                await conn.execute(text(f"""
                    CREATE INDEX IF NOT EXISTS idx_{partition_name}_term_gin 
                    ON {partition_table} USING GIN(to_tsvector('english', term))
                """))
                
                await conn.execute(text(f"""
                    CREATE INDEX IF NOT EXISTS idx_{partition_name}_active 
                    ON {partition_table} (active) WHERE active = true
                """))
                
                logger.info(f"Created partition {partition_table} for codes {start_code}-{end_code}")
    
    async def create_search_log_partitions(self):
        """Create time-based partitions for search logs"""
        
        async with async_engine.begin() as conn:
            # Create master search log table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS search_logs_master (
                    id BIGSERIAL,
                    user_id VARCHAR(50),
                    query TEXT NOT NULL,
                    results_count INTEGER,
                    response_time_ms FLOAT,
                    cache_hit BOOLEAN,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) PARTITION BY RANGE (created_at)
            """))
            
            # Create monthly partitions for current and next 6 months
            import datetime
            current_date = datetime.datetime.now()
            
            for i in range(7):  # Current month + 6 future months
                partition_date = current_date.replace(day=1) + datetime.timedelta(days=32*i)
                partition_date = partition_date.replace(day=1)
                next_month = (partition_date.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
                
                partition_name = f"search_logs_{partition_date.strftime('%Y_%m')}"
                
                await conn.execute(text(f"""
                    CREATE TABLE IF NOT EXISTS {partition_name}
                    PARTITION OF search_logs_master
                    FOR VALUES FROM ('{partition_date.strftime('%Y-%m-%d')}') 
                    TO ('{next_month.strftime('%Y-%m-%d')}')
                """))
                
                # Create indexes
                await conn.execute(text(f"""
                    CREATE INDEX IF NOT EXISTS idx_{partition_name}_created_at 
                    ON {partition_name} (created_at)
                """))
                
                await conn.execute(text(f"""
                    CREATE INDEX IF NOT EXISTS idx_{partition_name}_user_query 
                    ON {partition_name} (user_id, query)
                """))
    
    async def setup_read_replicas(self):
        """Configure read replica routing"""
        
        # Create read replica connection strings
        read_replicas = [
            "postgresql+asyncpg://readonly_user:password@replica1:5432/hms_terminology",
            "postgresql+asyncpg://readonly_user:password@replica2:5432/hms_terminology"
        ]
        
        return {
            'master': async_engine,
            'replicas': read_replicas,
            'routing_strategy': 'round_robin'
        }

partition_manager = DatabasePartitionManager()