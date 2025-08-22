import logging, inspect
import google.genai as genai
from google.cloud import bigquery
import json, datetime
import os
from google.cloud import storage
from dotenv import load_dotenv
load_dotenv()

GCS_BUCKET_NAME = os.getenv("GOOGLE_BUCKET")
GCS_SCHEMAS_PATH = os.getenv("GOOGLE_SCHEMA_PATH")
BQ_PROJECT_ID = os.getenv("BQ_PROJECT_ID")
BQ_DATASET_ID = os.getenv("BQ_DATASET_ID")
MODEL_NAME = os.getenv("MODEL_NAME")
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))


def execute_query(query: str, table_name: str = None):
    """Execute a BigQuery SQL query"""
    bq_client = bigquery.Client()
    job_config = bigquery.QueryJobConfig()
    
    if table_name:
        job_config.default_dataset = f"{BQ_PROJECT_ID}.{BQ_DATASET_ID}"
    
    job = bq_client.query(query, job_config=job_config)
    return job.result().to_dataframe()

def execute_sql(clean_sql: str, table_name: str = None) -> dict:
    """Execute SQL and return JSON results"""
    try:
        df = execute_query(clean_sql, table_name)
        return {
            "data": json.loads(df.to_json(orient="records", date_format="iso")),
            "status": "success"
        }
    except Exception as e:
        logging.error(f"Error executing SQL: {str(e)}")
        return {
            "error": str(e),
            "status": "error"
        }
    
def generate_sql(user_question: str) -> str:  # Changed return type to str
    module = "{}.{}".format(__name__, inspect.currentframe().f_code.co_name)
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=f"""
        Generate BigQuery SQL following these rules:
        1. Use SAFE_CAST for type conversions
        2. Handle NULL values with IFNULL/COALESCE
        3. All COALESCE arguments must be same type
        4. Optimize for performance
        
        {user_question}
        """
    )    
    generated_sql = response.text.strip()
    clean_sql_1 = generated_sql.strip("`").replace("sql\n", "").strip()
    clean_sql_2 = " ".join(clean_sql_1.split())
    return clean_sql_2

def date_converter(o):
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()
