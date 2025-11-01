"""
Minimal ETL Pipeline for Indian Drug Database
Ingests: NRCeS TSV, Kaggle CSV, RxNorm API → PostgreSQL
"""

import pandas as pd
import requests
import psycopg2
from psycopg2.extras import execute_batch
import logging
from typing import Dict, List, Optional
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RxNormAPI:
    """RxNorm REST API client"""
    BASE_URL = "https://rxnav.nlm.nih.gov/REST"
    
    @staticmethod
    def get_rxcui(drug_name: str) -> Optional[str]:
        """Get RxNorm CUI for drug name"""
        try:
            response = requests.get(
                f"{RxNormAPI.BASE_URL}/rxcui.json",
                params={"name": drug_name, "search": 2}
            )
            data = response.json()
            if 'idGroup' in data and 'rxnormId' in data['idGroup']:
                return data['idGroup']['rxnormId'][0]
        except Exception as e:
            logger.warning(f"RxNorm lookup failed for {drug_name}: {e}")
        return None
    
    @staticmethod
    def get_atc_code(rxcui: str) -> Optional[str]:
        """Get ATC code for RxNorm CUI"""
        try:
            response = requests.get(
                f"{RxNormAPI.BASE_URL}/rxclass/class/byRxcui.json",
                params={"rxcui": rxcui, "relaSource": "ATC"}
            )
            data = response.json()
            classes = data.get('rxclassMinConceptList', {}).get('rxclassMinConcept', [])
            if classes:
                return classes[0].get('classId')
        except Exception as e:
            logger.warning(f"ATC lookup failed for {rxcui}: {e}")
        return None


class DrugETL:
    """ETL Pipeline for drug data"""
    
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.conn = psycopg2.connect(db_url)
        self.cursor = self.conn.cursor()
    
    def extract_nrces_tsv(self, filepath: str) -> pd.DataFrame:
        """Extract from NRCeS TSV file"""
        logger.info(f"Extracting NRCeS data from {filepath}")
        df = pd.read_csv(filepath, sep='\t', encoding='utf-8')
        df['source'] = 'nrces'
        return df
    
    def extract_kaggle_csv(self, filepath: str) -> pd.DataFrame:
        """Extract from Kaggle CSV file"""
        logger.info(f"Extracting Kaggle data from {filepath}")
        df = pd.read_csv(filepath, encoding='utf-8')
        df['source'] = 'kaggle'
        return df
    
    def clean_drug_name(self, name: str) -> str:
        """Clean and normalize drug name"""
        if pd.isna(name):
            return ""
        name = str(name).strip()
        name = name.replace('  ', ' ')
        name = name.title()
        return name
    
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform and clean data"""
        logger.info(f"Transforming {len(df)} records")
        
        # Clean names
        df['drug_name'] = df['drug_name'].apply(self.clean_drug_name)
        df['generic_name'] = df['generic_name'].apply(self.clean_drug_name)
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['drug_name', 'generic_name'])
        
        # Remove empty names
        df = df[df['drug_name'] != ""]
        
        logger.info(f"After cleaning: {len(df)} records")
        return df
    
    def enrich_with_rxnorm(self, df: pd.DataFrame, batch_size: int = 100) -> pd.DataFrame:
        """Enrich with RxNorm CUI (batched to avoid rate limits)"""
        logger.info("Enriching with RxNorm data")
        
        rxcui_list = []
        atc_list = []
        
        for idx, row in df.iterrows():
            generic = row.get('generic_name', '')
            
            # Get RxNorm CUI
            rxcui = RxNormAPI.get_rxcui(generic)
            rxcui_list.append(rxcui)
            
            # Get ATC code
            atc = None
            if rxcui:
                atc = RxNormAPI.get_atc_code(rxcui)
            atc_list.append(atc)
            
            # Rate limiting
            if (idx + 1) % batch_size == 0:
                logger.info(f"Processed {idx + 1}/{len(df)} records")
                time.sleep(1)  # Avoid rate limits
        
        df['rxnorm_cui'] = rxcui_list
        df['atc_code'] = atc_list
        
        logger.info(f"RxNorm enrichment: {df['rxnorm_cui'].notna().sum()} matches")
        return df
    
    def load_generic_ingredients(self, df: pd.DataFrame):
        """Load generic ingredients to database"""
        logger.info("Loading generic ingredients")
        
        # Get unique generics
        generics = df[['generic_name', 'rxnorm_cui', 'atc_code']].drop_duplicates()
        generics = generics[generics['generic_name'] != ""]
        
        insert_query = """
            INSERT INTO generic_ingredients 
            (ingredient_name, rxnorm_cui, atc_code)
            VALUES (%s, %s, %s)
            ON CONFLICT (rxnorm_cui) DO UPDATE 
            SET ingredient_name = EXCLUDED.ingredient_name,
                atc_code = EXCLUDED.atc_code
            RETURNING ingredient_id, rxnorm_cui
        """
        
        rxcui_to_id = {}
        for _, row in generics.iterrows():
            try:
                self.cursor.execute(insert_query, (
                    row['generic_name'],
                    row['rxnorm_cui'],
                    row['atc_code']
                ))
                result = self.cursor.fetchone()
                if result:
                    rxcui_to_id[row['rxnorm_cui']] = result[0]
            except Exception as e:
                logger.error(f"Error inserting generic {row['generic_name']}: {e}")
        
        self.conn.commit()
        logger.info(f"Loaded {len(rxcui_to_id)} generic ingredients")
        return rxcui_to_id
    
    def load_brand_drugs(self, df: pd.DataFrame, rxcui_to_id: Dict):
        """Load brand drugs to database"""
        logger.info("Loading brand drugs")
        
        insert_query = """
            INSERT INTO indian_brand_drugs 
            (brand_name, manufacturer, ingredient_id, rxnorm_cui, 
             strength, dosage_form, mrp, pack_size, active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (brand_name, strength, dosage_form) DO UPDATE
            SET manufacturer = EXCLUDED.manufacturer,
                mrp = EXCLUDED.mrp,
                updated_at = NOW()
        """
        
        batch_data = []
        for _, row in df.iterrows():
            rxcui = row.get('rxnorm_cui')
            ingredient_id = rxcui_to_id.get(rxcui)
            
            if not ingredient_id:
                continue
            
            batch_data.append((
                row.get('drug_name', ''),
                row.get('manufacturer', ''),
                ingredient_id,
                rxcui,
                row.get('strength', ''),
                row.get('dosage_form', 'Tablet'),
                row.get('mrp', 0.0),
                row.get('pack_size', ''),
                True
            ))
        
        execute_batch(self.cursor, insert_query, batch_data, page_size=1000)
        self.conn.commit()
        logger.info(f"Loaded {len(batch_data)} brand drugs")
    
    def run(self, nrces_file: str = None, kaggle_file: str = None, 
            enrich_rxnorm: bool = True):
        """Run full ETL pipeline"""
        logger.info("Starting ETL pipeline")
        
        dfs = []
        
        # Extract
        if nrces_file:
            dfs.append(self.extract_nrces_tsv(nrces_file))
        if kaggle_file:
            dfs.append(self.extract_kaggle_csv(kaggle_file))
        
        if not dfs:
            logger.error("No data sources provided")
            return
        
        # Combine
        df = pd.concat(dfs, ignore_index=True)
        logger.info(f"Total records: {len(df)}")
        
        # Transform
        df = self.transform(df)
        
        # Enrich with RxNorm
        if enrich_rxnorm:
            df = self.enrich_with_rxnorm(df)
        
        # Load
        rxcui_to_id = self.load_generic_ingredients(df)
        self.load_brand_drugs(df, rxcui_to_id)
        
        logger.info("ETL pipeline completed")
    
    def close(self):
        """Close database connection"""
        self.cursor.close()
        self.conn.close()


# Sample data format expectations
SAMPLE_NRCES_FORMAT = """
drug_name	generic_name	manufacturer	strength	dosage_form	mrp	pack_size
Crocin	Acetaminophen	GSK	500mg	Tablet	15.00	10 tablets
Dolo 650	Acetaminophen	Micro Labs	650mg	Tablet	30.00	15 tablets
"""

SAMPLE_KAGGLE_FORMAT = """
drug_name,generic_name,manufacturer,strength,dosage_form,mrp,pack_size
Glycomet,Metformin,USV,500mg,Tablet,25.00,10 tablets
Glucophage,Metformin,Merck,500mg,Tablet,35.00,10 tablets
"""


if __name__ == "__main__":
    # Configuration
    DATABASE_URL = "postgresql://user:password@localhost:5432/hms_terminology"
    
    # Run ETL
    etl = DrugETL(DATABASE_URL)
    
    try:
        etl.run(
            nrces_file="data/nrces_drugs.tsv",
            kaggle_file="data/kaggle_drugs.csv",
            enrich_rxnorm=True
        )
    finally:
        etl.close()
