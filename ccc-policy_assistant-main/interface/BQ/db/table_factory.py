import os
import json
import logging
from typing import Dict
from google.cloud import storage
from google.api_core.exceptions import GoogleAPIError
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

class TableAgentFactory:
    def __init__(self, gcs_bucket_name: str, gcs_schemas_path: str, project_id: str):
        self.gcs_bucket_name = gcs_bucket_name
        self.gcs_schemas_path = gcs_schemas_path.rstrip('/')
        self.project_id = project_id
        self.schemas: Dict[str, dict] = {}
        logger.info(f"Initializing TableAgentFactory with GCS bucket: {gcs_bucket_name}, path: {gcs_schemas_path}")
        self._load_all_schemas()
    
    def _load_all_schemas(self):
        """Load all JSON schemas from the GCS bucket path."""
        try:
            storage_client = storage.Client(project=self.project_id)
            bucket = storage_client.bucket(self.gcs_bucket_name)
            
            # List all files in the schemas path
            blobs = bucket.list_blobs(prefix=self.gcs_schemas_path)
            
            schema_count = 0
            for blob in blobs:
                if blob.name.endswith('.json'):
                    try:
                        # Download the file content
                        content = blob.download_as_text()
                        schema = json.loads(content)
                        
                        # Extract table name from the blob path
                        table_name = os.path.splitext(os.path.basename(blob.name))[0]
                        
                        if "Overview description of file contents" not in schema or "Data dictionary" not in schema:
                            logger.warning(f"Invalid schema for {table_name}: Missing required fields")
                            continue
                            
                        self.schemas[table_name] = schema
                        schema_count += 1
                        logger.info(f"Loaded schema for table: {table_name}")
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse schema from {blob.name}: {str(e)}")
                    except GoogleAPIError as e:
                        logger.error(f"Failed to download schema from {blob.name}: {str(e)}")
            
            if schema_count == 0:
                logger.warning(f"No valid schemas found in gs://{self.gcs_bucket_name}/{self.gcs_schemas_path}")
            else:
                logger.info(f"Successfully loaded {schema_count} schemas from GCS")
                
        except Exception as e:
            logger.error(f"Error loading schemas from GCS: {str(e)}")
            raise
    
    def get_schema(self, table_name: str) -> dict:
        """Get the schema for a specific table."""
        schema = self.schemas.get(table_name)
        if not schema:
            raise ValueError(f"No schema found for table: {table_name}")
        return schema
    
    def get_all_table_names(self) -> list:
        """Get the list of all table names."""
        return list(self.schemas.keys())

# Initialize with GCS bucket and path
gcs_bucket_name =os.getenv("GOOGLE_BUCKET")
gcs_schemas_path = os.getenv("GOOGLE_SCHEMA_PATH")
project_id = os.getenv("BQ_PROJECT_ID")

table_factory = TableAgentFactory(
    gcs_bucket_name=gcs_bucket_name,
    gcs_schemas_path=gcs_schemas_path,
    project_id=project_id
)