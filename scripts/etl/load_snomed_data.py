#!/usr/bin/env python3
"""
SNOMED CT Indian Drug Database ETL Pipeline
Production-grade data loader with error handling, validation, and monitoring
"""

import csv
import sys
import time
import logging
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
from dataclasses import dataclass

import psycopg2
from psycopg2.extras import execute_batch
from psycopg2 import sql

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/snomed_etl.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ETLStats:
    """Track ETL statistics"""
    table_name: str
    total_records: int = 0
    loaded_records: int = 0
    failed_records: int = 0
    execution_time_ms: int = 0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []

class SnomedETL:
    """Production-grade SNOMED ETL pipeline"""
    
    BATCH_SIZE = 5000
    DATA_DIR = Path("CommonDrugCodesForIndia_FlatFilePackage")
    
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.conn = None
        self.stats: Dict[str, ETLStats] = {}
        
    def connect(self):
        """Establish database connection with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.conn = psycopg2.connect(**self.db_config)
                self.conn.autocommit = False
                logger.info("Database connection established")
                return
            except psycopg2.Error as e:
                logger.error(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def parse_date(self, date_str: str) -> str:
        """Parse date from YYYYMMDD format"""
        if not date_str or date_str.strip() == '':
            return None
        try:
            return datetime.strptime(date_str.strip(), '%Y%m%d').date()
        except ValueError:
            return None
    
    def load_substances(self) -> ETLStats:
        """Load SNOMED substances (28,913 records)"""
        stats = ETLStats(table_name='snomed_substances')
        start_time = time.time()
        
        file_path = self.DATA_DIR / "SubstanceMaster.txt"
        logger.info(f"Loading substances from {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter='\t')
                
                cursor = self.conn.cursor()
                batch = []
                
                for row in reader:
                    stats.total_records += 1
                    try:
                        batch.append((
                            int(row['Identifier']),
                            row['Substance Name'].strip(),
                            row.get('CAS Number', '').strip() or None,
                            row.get('UNII', '').strip() or None,
                            row.get('Substance Description', '').strip() or None,
                            row.get('Molecular Weight', '').strip() or None,
                            row.get('Toxicity', '').strip() or None,
                            row.get('SMILE', '').strip() or None,
                            row.get('InChI', '').strip() or None,
                            row.get('IUPAC Name', '').strip() or None,
                            row.get('Molecular Formula', '').strip() or None,
                            self.parse_date(row.get('last_updated_on', ''))
                        ))
                        
                        if len(batch) >= self.BATCH_SIZE:
                            self._execute_batch(cursor, 'snomed_substances', batch, stats)
                            batch = []
                            
                    except Exception as e:
                        stats.failed_records += 1
                        stats.errors.append(f"Row {stats.total_records}: {str(e)}")
                        logger.warning(f"Failed to process substance row {stats.total_records}: {e}")
                
                # Load remaining batch
                if batch:
                    self._execute_batch(cursor, 'snomed_substances', batch, stats)
                
                self.conn.commit()
                cursor.close()
                
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to load substances: {e}")
            raise
        
        stats.execution_time_ms = int((time.time() - start_time) * 1000)
        logger.info(f"Substances loaded: {stats.loaded_records}/{stats.total_records} "
                   f"in {stats.execution_time_ms}ms")
        return stats
    
    def load_generics(self) -> ETLStats:
        """Load SNOMED generics (9,870 records)"""
        stats = ETLStats(table_name='snomed_generics')
        start_time = time.time()
        
        file_path = self.DATA_DIR / "GenericMaster.txt"
        logger.info(f"Loading generics from {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter='\t')
                
                cursor = self.conn.cursor()
                batch = []
                
                for row in reader:
                    stats.total_records += 1
                    try:
                        batch.append((
                            int(row['Identifier']),
                            row['Generic Name'].strip(),
                            row.get('Substance Identifier', '').strip() or None,
                            row.get('Route of Administration', '').strip() or None,
                            row.get('Dose Form', '').strip() or None,
                            row.get('Therapeutic Role', '').strip() or None,
                            row.get('Indication', '').strip() or None,
                            row.get('Contra Indication', '').strip() or None,
                            row.get('Interaction with Drugs', '').strip() or None,
                            row.get('Classification of Drugs', '').strip() or None,
                            row.get('Source/ Regulatory', '').strip() or None,
                            self.parse_date(row.get('last_updated_on', ''))
                        ))
                        
                        if len(batch) >= self.BATCH_SIZE:
                            self._execute_batch(cursor, 'snomed_generics', batch, stats)
                            batch = []
                            
                    except Exception as e:
                        stats.failed_records += 1
                        stats.errors.append(f"Row {stats.total_records}: {str(e)}")
                        logger.warning(f"Failed to process generic row {stats.total_records}: {e}")
                
                if batch:
                    self._execute_batch(cursor, 'snomed_generics', batch, stats)
                
                self.conn.commit()
                cursor.close()
                
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to load generics: {e}")
            raise
        
        stats.execution_time_ms = int((time.time() - start_time) * 1000)
        logger.info(f"Generics loaded: {stats.loaded_records}/{stats.total_records} "
                   f"in {stats.execution_time_ms}ms")
        return stats
    
    def load_brands(self) -> ETLStats:
        """Load SNOMED brands (89,447 records) - MAIN TABLE"""
        stats = ETLStats(table_name='snomed_brands')
        start_time = time.time()
        
        file_path = self.DATA_DIR / "BrandMaster.txt"
        logger.info(f"Loading brands from {file_path}")
        
        # Temporarily disable foreign key checks
        cursor = self.conn.cursor()
        cursor.execute("SET session_replication_role = 'replica';")
        self.conn.commit()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter='\t')
                
                cursor = self.conn.cursor()
                batch = []
                
                for row in reader:
                    stats.total_records += 1
                    try:
                        generic_id = row.get('Generic Identifier', '').strip()
                        product_id = row.get('Product Identifier', '').strip()
                        supplier_id = row.get('Supplier Identifier', '').strip()
                        
                        # Skip if generic_id doesn't exist (allow NULL)
                        generic_id_val = int(generic_id) if generic_id else None
                        
                        batch.append((
                            int(row['Identifier']),
                            row['Brand Name'].strip(),
                            int(product_id) if product_id else None,
                            int(supplier_id) if supplier_id else None,
                            generic_id_val,
                            row.get('License Number', '').strip() or None,
                            row.get('License Status', 'UNKNOWN').strip(),
                            row.get('Excipient', '').strip() or None,
                            self.parse_date(row.get('last_updated_on', '')),
                            True  # active
                        ))
                        
                        if len(batch) >= self.BATCH_SIZE:
                            self._execute_batch(cursor, 'snomed_brands', batch, stats)
                            batch = []
                            
                    except Exception as e:
                        stats.failed_records += 1
                        stats.errors.append(f"Row {stats.total_records}: {str(e)}")
                        logger.warning(f"Failed to process brand row {stats.total_records}: {e}")
                
                if batch:
                    self._execute_batch(cursor, 'snomed_brands', batch, stats)
                
                # Re-enable foreign key checks
                cursor.execute("SET session_replication_role = 'origin';")
                self.conn.commit()
                cursor.close()
                
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to load brands: {e}")
            raise
        
        stats.execution_time_ms = int((time.time() - start_time) * 1000)
        logger.info(f"Brands loaded: {stats.loaded_records}/{stats.total_records} "
                   f"in {stats.execution_time_ms}ms")
        return stats
    
    def load_products(self) -> ETLStats:
        """Load SNOMED products (68,517 records)"""
        stats = ETLStats(table_name='snomed_products')
        start_time = time.time()
        
        file_path = self.DATA_DIR / "ProductMaster.txt"
        logger.info(f"Loading products from {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter='\t')
                
                cursor = self.conn.cursor()
                batch = []
                
                for row in reader:
                    stats.total_records += 1
                    try:
                        batch.append((
                            int(row['Identifier']),
                            row['Product Name'].strip()
                        ))
                        
                        if len(batch) >= self.BATCH_SIZE:
                            self._execute_batch(cursor, 'snomed_products', batch, stats)
                            batch = []
                            
                    except Exception as e:
                        stats.failed_records += 1
                        stats.errors.append(f"Row {stats.total_records}: {str(e)}")
                        logger.warning(f"Failed to process product row {stats.total_records}: {e}")
                
                if batch:
                    self._execute_batch(cursor, 'snomed_products', batch, stats)
                
                self.conn.commit()
                cursor.close()
                
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to load products: {e}")
            raise
        
        stats.execution_time_ms = int((time.time() - start_time) * 1000)
        logger.info(f"Products loaded: {stats.loaded_records}/{stats.total_records} "
                   f"in {stats.execution_time_ms}ms")
        return stats
    
    def load_suppliers(self) -> ETLStats:
        """Load SNOMED suppliers (7,935 records)"""
        stats = ETLStats(table_name='snomed_suppliers')
        start_time = time.time()
        
        file_path = self.DATA_DIR / "SupplierMaster.txt"
        logger.info(f"Loading suppliers from {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter='\t')
                
                cursor = self.conn.cursor()
                batch = []
                
                for row in reader:
                    stats.total_records += 1
                    try:
                        batch.append((
                            int(row['Identifier']),
                            row['Supplier Name'].strip(),
                            row.get('Country', '').strip() or None,
                            True  # active
                        ))
                        
                        if len(batch) >= self.BATCH_SIZE:
                            self._execute_batch(cursor, 'snomed_suppliers', batch, stats)
                            batch = []
                            
                    except Exception as e:
                        stats.failed_records += 1
                        stats.errors.append(f"Row {stats.total_records}: {str(e)}")
                        logger.warning(f"Failed to process supplier row {stats.total_records}: {e}")
                
                if batch:
                    self._execute_batch(cursor, 'snomed_suppliers', batch, stats)
                
                self.conn.commit()
                cursor.close()
                
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to load suppliers: {e}")
            raise
        
        stats.execution_time_ms = int((time.time() - start_time) * 1000)
        logger.info(f"Suppliers loaded: {stats.loaded_records}/{stats.total_records} "
                   f"in {stats.execution_time_ms}ms")
        return stats
    
    def load_drug_forms(self) -> ETLStats:
        """Load SNOMED drug forms (423 records)"""
        stats = ETLStats(table_name='snomed_drug_forms')
        start_time = time.time()
        
        file_path = self.DATA_DIR / "DrugFormMaster.txt"
        logger.info(f"Loading drug forms from {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter='\t')
                
                cursor = self.conn.cursor()
                batch = []
                
                for row in reader:
                    stats.total_records += 1
                    try:
                        # Assuming columns: Identifier, Form Name, Description
                        identifier = row.get('Identifier', '').strip()
                        if not identifier:
                            continue
                            
                        batch.append((
                            int(identifier),
                            list(row.values())[1].strip() if len(row.values()) > 1 else 'Unknown',
                            list(row.values())[2].strip() if len(row.values()) > 2 else None
                        ))
                        
                        if len(batch) >= self.BATCH_SIZE:
                            self._execute_batch(cursor, 'snomed_drug_forms', batch, stats)
                            batch = []
                            
                    except Exception as e:
                        stats.failed_records += 1
                        logger.warning(f"Failed to process drug form row {stats.total_records}: {e}")
                
                if batch:
                    self._execute_batch(cursor, 'snomed_drug_forms', batch, stats)
                
                self.conn.commit()
                cursor.close()
                
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to load drug forms: {e}")
            raise
        
        stats.execution_time_ms = int((time.time() - start_time) * 1000)
        logger.info(f"Drug forms loaded: {stats.loaded_records}/{stats.total_records} "
                   f"in {stats.execution_time_ms}ms")
        return stats
    
    def load_routes(self) -> ETLStats:
        """Load SNOMED routes of administration (161 records)"""
        stats = ETLStats(table_name='snomed_routes')
        start_time = time.time()
        
        file_path = self.DATA_DIR / "RouteOfAdministrationMaster.txt"
        logger.info(f"Loading routes from {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter='\t')
                
                cursor = self.conn.cursor()
                batch = []
                
                for row in reader:
                    stats.total_records += 1
                    try:
                        identifier = row.get('Identifier', '').strip()
                        if not identifier:
                            continue
                            
                        batch.append((
                            int(identifier),
                            list(row.values())[1].strip() if len(row.values()) > 1 else 'Unknown',
                            list(row.values())[2].strip() if len(row.values()) > 2 else None
                        ))
                        
                        if len(batch) >= self.BATCH_SIZE:
                            self._execute_batch(cursor, 'snomed_routes', batch, stats)
                            batch = []
                            
                    except Exception as e:
                        stats.failed_records += 1
                        logger.warning(f"Failed to process route row {stats.total_records}: {e}")
                
                if batch:
                    self._execute_batch(cursor, 'snomed_routes', batch, stats)
                
                self.conn.commit()
                cursor.close()
                
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to load routes: {e}")
            raise
        
        stats.execution_time_ms = int((time.time() - start_time) * 1000)
        logger.info(f"Routes loaded: {stats.loaded_records}/{stats.total_records} "
                   f"in {stats.execution_time_ms}ms")
        return stats
    
    def _execute_batch(self, cursor, table_name: str, batch: List[Tuple], stats: ETLStats):
        """Execute batch insert with error handling"""
        if not batch:
            return
        
        queries = {
            'snomed_substances': """
                INSERT INTO snomed_substances 
                (snomed_id, substance_name, cas_number, unii, substance_description,
                 molecular_weight, toxicity, smile, inchi, iupac_name, molecular_formula, last_updated)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (snomed_id) DO UPDATE SET
                    substance_name = EXCLUDED.substance_name,
                    last_updated = EXCLUDED.last_updated
            """,
            'snomed_generics': """
                INSERT INTO snomed_generics 
                (snomed_id, generic_name, substance_ids, route_of_admin, dose_form,
                 therapeutic_role, indication, contra_indication, drug_interactions,
                 drug_classification, source_regulatory, last_updated)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (snomed_id) DO UPDATE SET
                    generic_name = EXCLUDED.generic_name,
                    last_updated = EXCLUDED.last_updated
            """,
            'snomed_brands': """
                INSERT INTO snomed_brands 
                (snomed_id, brand_name, product_id, supplier_id, generic_id,
                 license_number, license_status, excipient, last_updated, active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (snomed_id) DO UPDATE SET
                    brand_name = EXCLUDED.brand_name,
                    last_updated = EXCLUDED.last_updated
            """,
            'snomed_products': """
                INSERT INTO snomed_products (snomed_id, product_name)
                VALUES (%s, %s)
                ON CONFLICT (snomed_id) DO UPDATE SET
                    product_name = EXCLUDED.product_name
            """,
            'snomed_suppliers': """
                INSERT INTO snomed_suppliers (snomed_id, supplier_name, country, active)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (snomed_id) DO UPDATE SET
                    supplier_name = EXCLUDED.supplier_name
            """,
            'snomed_drug_forms': """
                INSERT INTO snomed_drug_forms (snomed_id, form_name, form_description)
                VALUES (%s, %s, %s)
                ON CONFLICT (snomed_id) DO UPDATE SET
                    form_name = EXCLUDED.form_name
            """,
            'snomed_routes': """
                INSERT INTO snomed_routes (snomed_id, route_name, route_description)
                VALUES (%s, %s, %s)
                ON CONFLICT (snomed_id) DO UPDATE SET
                    route_name = EXCLUDED.route_name
            """
        }
        
        try:
            execute_batch(cursor, queries[table_name], batch, page_size=1000)
            stats.loaded_records += len(batch)
        except Exception as e:
            logger.error(f"Batch insert failed for {table_name}: {e}")
            stats.failed_records += len(batch)
            raise
    
    def refresh_materialized_view(self):
        """Refresh the complete drugs materialized view"""
        logger.info("Refreshing materialized view...")
        start_time = time.time()
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT refresh_snomed_complete_view()")
            self.conn.commit()
            cursor.close()
            
            elapsed = int((time.time() - start_time) * 1000)
            logger.info(f"Materialized view refreshed in {elapsed}ms")
        except Exception as e:
            logger.error(f"Failed to refresh materialized view: {e}")
            raise
    
    def log_stats(self):
        """Log ETL statistics to database"""
        cursor = self.conn.cursor()
        
        for table_name, stats in self.stats.items():
            try:
                cursor.execute("""
                    INSERT INTO snomed_etl_log 
                    (table_name, records_loaded, records_failed, execution_time_ms, status, error_message)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    stats.table_name,
                    stats.loaded_records,
                    stats.failed_records,
                    stats.execution_time_ms,
                    'SUCCESS' if stats.failed_records == 0 else 'PARTIAL',
                    '\n'.join(stats.errors[:10]) if stats.errors else None
                ))
            except Exception as e:
                logger.error(f"Failed to log stats for {table_name}: {e}")
        
        self.conn.commit()
        cursor.close()
    
    def run(self):
        """Execute complete ETL pipeline"""
        total_start = time.time()
        logger.info("=" * 80)
        logger.info("Starting SNOMED CT Indian Drug Database ETL Pipeline")
        logger.info("=" * 80)
        
        try:
            self.connect()
            
            # Load in dependency order
            self.stats['substances'] = self.load_substances()
            self.stats['generics'] = self.load_generics()
            self.stats['products'] = self.load_products()
            self.stats['suppliers'] = self.load_suppliers()
            self.stats['brands'] = self.load_brands()
            self.stats['drug_forms'] = self.load_drug_forms()
            self.stats['routes'] = self.load_routes()
            
            # Refresh materialized view
            self.refresh_materialized_view()
            
            # Log statistics
            self.log_stats()
            
            total_time = int((time.time() - total_start) * 1000)
            total_loaded = sum(s.loaded_records for s in self.stats.values())
            total_failed = sum(s.failed_records for s in self.stats.values())
            
            logger.info("=" * 80)
            logger.info("ETL Pipeline Completed Successfully")
            logger.info(f"Total records loaded: {total_loaded:,}")
            logger.info(f"Total records failed: {total_failed:,}")
            logger.info(f"Total execution time: {total_time:,}ms ({total_time/1000:.2f}s)")
            logger.info("=" * 80)
            
            # Print summary table
            print("\n" + "=" * 80)
            print(f"{'Table':<25} {'Total':<12} {'Loaded':<12} {'Failed':<12} {'Time (ms)':<12}")
            print("=" * 80)
            for stats in self.stats.values():
                print(f"{stats.table_name:<25} {stats.total_records:<12,} "
                      f"{stats.loaded_records:<12,} {stats.failed_records:<12,} "
                      f"{stats.execution_time_ms:<12,}")
            print("=" * 80)
            
        except Exception as e:
            logger.error(f"ETL pipeline failed: {e}")
            raise
        finally:
            self.close()


def main():
    """Main entry point"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'database': os.getenv('DB_NAME', 'medical_library'),
        'user': os.getenv('DB_USER', 'samirkolhe'),
        'password': os.getenv('DB_PASSWORD', '')
    }
    
    etl = SnomedETL(db_config)
    etl.run()


if __name__ == '__main__':
    main()
