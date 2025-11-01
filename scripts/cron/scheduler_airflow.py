"""
Airflow DAG for scheduled drug data updates
Alternative: Use simple cron if Airflow not available
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from etl_drug_pipeline import DrugETL
import os

# Default args
default_args = {
    'owner': 'hms',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# DAG definition
dag = DAG(
    'drug_data_etl',
    default_args=default_args,
    description='ETL pipeline for drug database updates',
    schedule_interval='0 2 * * 0',  # Weekly on Sunday 2 AM
    catchup=False,
)

def run_etl():
    """Run ETL pipeline"""
    DATABASE_URL = os.getenv('DATABASE_URL')
    etl = DrugETL(DATABASE_URL)
    
    try:
        etl.run(
            nrces_file="data/nrces_drugs.tsv",
            kaggle_file="data/kaggle_drugs.csv",
            enrich_rxnorm=True
        )
    finally:
        etl.close()

# Tasks
etl_task = PythonOperator(
    task_id='run_drug_etl',
    python_callable=run_etl,
    dag=dag,
)


# ============================================
# SIMPLE CRON ALTERNATIVE (No Airflow needed)
# ============================================
"""
Add to crontab:

# Run drug ETL every Sunday at 2 AM
0 2 * * 0 cd /path/to/data-machine && python etl_drug_pipeline.py >> logs/etl.log 2>&1

# Or use systemd timer (Linux)
"""
